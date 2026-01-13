import uuid
from typing import Dict, List, Tuple
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.models import InterviewSession, InterviewMessage, QuestionScore

class InterviewManager:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.sessions: Dict[str, InterviewSession] = {}
        self.MAX_QUESTIONS = 5

    def create_session(self, resume_text: str, jd: str, match_score: float) -> InterviewSession:
        session_id = str(uuid.uuid4())
        
        # 1. Deduce Role from JD
        role = self._deduce_role(jd)
        
        session = InterviewSession(
            session_id=session_id,
            job_description=jd,
            resume_text=resume_text,
            initial_match_score=match_score,
            detected_role=role
        )
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> InterviewSession:
        return self.sessions.get(session_id)

    def start_interview(self, session_id: str) -> str:
        session = self.get_session(session_id)
        if not session:
            return "Session not found."
            
        # Generate first question
        question = self._generate_question(session, is_first=True)
        session.current_question = question
        session.messages.append(InterviewMessage(role="assistant", content=question))
        return question

    def process_answer(self, session_id: str, answer: str) -> Tuple[str, bool, dict, float]:
        """
        Returns (next_question_or_message, is_finished, feedback_dict, score)
        """
        session = self.get_session(session_id)
        if not session or not session.is_active:
            return "Interview is closed.", True, "", 0.0

        # 1. Archive Answer
        session.messages.append(InterviewMessage(role="user", content=answer))
        
        # 2. Grade Answer
        current_q = session.current_question
        score, feedback_data = self._grade_answer(session, current_q, answer)
        
        session.question_scores.append(QuestionScore(
            question=current_q,
            answer=answer,
            score=score,
            feedback=feedback_data.get('summary', ''),
            strength=feedback_data.get('strength', ''),
            gap=feedback_data.get('gap', ''),
            improvement=feedback_data.get('improvement', '')
        ))
        
        # 3. Check termination
        if len(session.question_scores) >= self.MAX_QUESTIONS:
            session.is_active = False
            final_msg = "Interview complete. Thank you."
            session.messages.append(InterviewMessage(role="assistant", content=final_msg))
            return final_msg, True, feedback_data, score
            
        # 4. Generate Next Question
        next_q = self._generate_question(session, is_first=False)
        session.current_question = next_q
        session.messages.append(InterviewMessage(role="assistant", content=next_q))
        return next_q, False, feedback_data, score

    def calculate_final_result(self, session_id: str):
        session = self.get_session(session_id)
        if not session:
            return None
            
        avg_interview_score = 0
        if session.question_scores:
            avg_interview_score = sum(s.score for s in session.question_scores) / len(session.question_scores)
            
        # Weightage: 30% Resume, 70% Interview (scaled to 100)
        # Interview score is 0-10, so * 10 to get 0-100
        interview_score_100 = avg_interview_score * 10
        resume_score = session.initial_match_score
        
        final_score = (resume_score * 0.3) + (interview_score_100 * 0.7)
        
        # New: Generate Career Report
        career_report = self._generate_career_report(session)

        return {
            "session_id": session_id,
            "role": session.detected_role,
            "resume_score": round(resume_score, 2),
            "interview_score": round(interview_score_100, 2),
            "final_score": round(final_score, 2),
            "breakdown": session.question_scores,
            "career_report": career_report
        }

    # ---------- Private LLM Helper Methods ----------

    def _deduce_role(self, jd: str) -> str:
        prompt = PromptTemplate.from_template(
            "Extract the primary Job Role (Title) from this description. Return ONLY the role name. \n\nJD:\n{jd}"
        )
        chain = prompt | self.llm
        try:
            res = chain.invoke({"jd": jd[:2000]}) # Limit text if needed
            return res.content.strip()
        except:
            return "Candidate"

    def _generate_question(self, session: InterviewSession, is_first: bool) -> str:
        # Construct context from history
        history_summary = ""
        if not is_first:
            last_q = session.question_scores[-1].question
            last_a = session.question_scores[-1].answer
            history_summary = f"Previuos Q: {last_q}\nPrevious A: {last_a}\n"

        template = """
        You are an AI Technical Interviewer for the role of {role}.
        
        RESUME CONTEXT:
        {resume_context}
        
        JOB DESCRIPTION:
        {job_description}
        
        INTERVIEW HISTORY:
        {history}
        
        TASK:
        Generate the next interview question. 
        - If {is_first} is True, verify a core skill or a gap from the resume.
        - If not first, adapt to the previous answer.
        - Questions should be conceptual or "mini-tasks" (e.g. "Write a function to...", "Explain how you would design...").
        - Keep it challenging but fair.
        - Return ONLY the question text.
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        try:
            res = chain.invoke({
                "role": session.detected_role,
                "resume_context": session.resume_text[:3000], # Limit context
                "job_description": session.job_description[:1000],
                "history": history_summary,
                "is_first": str(is_first)
            })
            content = res.content.strip()
            if not content:
                raise ValueError("Empty response from LLM")
            return content
        except Exception as e:
            print(f"Error generating question: {e}")
            return "Could you walk me through your background and your relevant experience for this role?"

    def _grade_answer(self, session: InterviewSession, question: str, answer: str) -> Tuple[float, dict]:
        template = """
        You are an Interview Grader.
        
        Question: {question}
        Candidate Answer: {answer}
        
        Role: {role}
        
        TASK:
        Evaluate the answer on a scale of 0 to 10.
        Provide structured feedback.
        
        OUTPUT FORMAT:
        Score: <number>
        Strength: <what went well>
        Gap: <what is missing>
        Improvement: <actionable tip>
        Summary: <short general comment>
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        res = chain.invoke({
            "question": question,
            "answer": answer,
            "role": session.detected_role
        })
        
        # Parse output
        text = res.content
        score = 0.0
        data = {"summary": "No feedback", "strength": "", "gap": "", "improvement": ""}
        
        try:
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith("Score:"):
                    score = float(line.split(":", 1)[1].strip())
                elif line.startswith("Strength:"):
                    data["strength"] = line.split(":", 1)[1].strip()
                elif line.startswith("Gap:"):
                    data["gap"] = line.split(":", 1)[1].strip()
                elif line.startswith("Improvement:"):
                    data["improvement"] = line.split(":", 1)[1].strip()
                elif line.startswith("Summary:"):
                    data["summary"] = line.split(":", 1)[1].strip()
        except:
            pass
            
        return score, data

    def _generate_career_report(self, session: InterviewSession) -> dict:
        template = """
        You are an Expert Career Coach.
        
        Candidate Role: {role}
        Resume Context: {resume}
        Interview Performance:
        {performance}
        
        TASK:
        Generate a JSON-like report.
        1. Top 3 Focus Areas (Technical skills to learn).
        2. Preferred Job Roles (3 roles that fit best).
        3. One-line motivation.
        
        OUTPUT FORMAT:
        Focus Areas: <skill1>, <skill2>, <skill3>
        Preferred Roles: <role1>, <role2>, <role3>
        Motivation: <text>
        """
        
        # Summarize performance
        perf = ""
        for q in session.question_scores:
            perf += f"Q: {q.question}\nA: {q.answer}\nScore: {q.score}\n\n"
            
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        try:
            res = chain.invoke({
                "role": session.detected_role,
                "resume": session.resume_text[:2000],
                "performance": perf
            })
            
            # Parse
            print(f"DEBUG: Career Report Raw Output:\n{res.content}") # Debug log

            lines = res.content.split('\n')
            report = {"focus_areas": [], "preferred_roles": [], "motivation": ""}
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                if "Focus Areas:" in line:
                    val = line.split(":", 1)[1].strip()
                    report["focus_areas"] = [x.strip() for x in val.split(",") if x.strip()]
                elif "Preferred Roles:" in line or "Preferred Job Roles:" in line:
                    val = line.split(":", 1)[1].strip()
                    report["preferred_roles"] = [x.strip() for x in val.split(",") if x.strip()]
                elif "Motivation:" in line:
                    report["motivation"] = line.split(":", 1)[1].strip()
            
            # Fallback if empty
            if not report["preferred_roles"]:
                report["preferred_roles"] = [session.detected_role, "Senior " + session.detected_role]
                    
            return report
        except Exception as e:
            print(f"Error generating report: {e}")
            return {"focus_areas": ["General Upskilling"], "preferred_roles": [session.detected_role], "motivation": "Keep learning!"}
