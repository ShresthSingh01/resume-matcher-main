import uuid
from typing import Dict, List, Optional
from langchain_core.prompts import PromptTemplate
from app.schemas import InterviewSession, QuestionScore, InterviewMessage
from app.grading import grade_answer
from app.llm import get_llm
from app.interview_prompts import INTERVIEW_SYSTEM_PROMPT
from app.llm_utils import safe_invoke
from app.db import (
    save_session_db, get_session_db, update_session_db, log_message_db, 
    get_candidate, get_session_messages, update_candidate_interview
)
import json

class InterviewManager:
    def __init__(self):
        # State is now in DB
        self.llm = get_llm(temperature=0.7, max_tokens=600)

    def deduce_role(self, jd_text: str) -> str:
        """
        Extracts the role from JD using LLM.
        """
        try:
             from app.interview_prompts import ROLE_DEDUCTION_PROMPT
             chain = ROLE_DEDUCTION_PROMPT | self.llm
             res = chain.invoke({"job_description": jd_text})
             role = res.content.strip()
             # Basic cleanup if LLM adds quotes
             role = role.replace('"', '').replace("'", "")
             return role
        except Exception as e:
            print(f"⚠️ Role Deduction Failed: {e}")
            return "Candidate"

    def create_session(
        self, 
        resume_text: Optional[str] = None, 
        jd: Optional[str] = None, 
        match_score: Optional[float] = None,
        candidate_id: Optional[str] = None
    ) -> InterviewSession:
        sid = str(uuid.uuid4())
        
        # 1. Resolve from DB if ID provided
        if candidate_id:
            db_candidate = get_candidate(candidate_id)
            if db_candidate:
                resume_text = db_candidate['resume_text']
                jd = db_candidate['job_description']
                match_score = db_candidate['match_score']
            else:
                # Fallback or error? For now proceed if texts are passed
                if not resume_text:
                    raise ValueError("Candidate not found and no resume text provided.")

        # Legacy fallback if resume_text looks like UUID (Backwards compat logic removal/cleanup?)
        # Keeping it safe: if candidate_id was NOT passed but resume_text IS 36 chars, treat as ID
        if not candidate_id and resume_text and len(resume_text) == 36:
            candidate_id = resume_text
            db_candidate = get_candidate(candidate_id)
            if db_candidate:
                 resume_text = db_candidate['resume_text']
                 jd = db_candidate['job_description']
                 match_score = db_candidate['match_score']

        if not resume_text or not jd:
             # Just ensures we don't crash, but deduction might fail
             pass

        # Deduce Role
        role = self.deduce_role(jd if jd else "")

        # Create session object
        session = InterviewSession(
            session_id=sid,
            resume_text=resume_text or "",
            job_description=jd or "",
            initial_match_score=match_score or 0.0,
            candidate_id=candidate_id or "unknown",
            detected_role=role
        )
        
        # Save to DB
        save_session_db(sid, session.candidate_id, session.detected_role, True)
        
        return session

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        row = get_session_db(session_id)
        if not row:
            return None
        
        # Rehydrate session
        cid = row['candidate_id']
        candidate = get_candidate(cid)
        
        resume_text = ""
        jd = ""
        match_score = 0.0
        
        if candidate:
             resume_text = candidate['resume_text']
             jd = candidate['job_description']
             match_score = candidate['match_score']
        
        session = InterviewSession(
            session_id=row['session_id'],
            resume_text=resume_text,
            job_description=jd,
            initial_match_score=match_score,
            detected_role=row['role'],
            is_active=bool(row['is_active']),
            candidate_id=cid
        )
        
        # Load messages
        msgs = get_session_messages(session_id)
        for m in msgs:
            session.messages.append(InterviewMessage(role=m['role'], content=m['content']))
            
        # Load scores
        session.question_scores = []
        if row['scores']:
            scores_data = json.loads(row['scores'])
            for s in scores_data:
                session.question_scores.append(QuestionScore(**s))
            
        session.current_question = row['current_question']
        
        return session

    def start_interview(self, session_id: str) -> str:
        session = self.get_session(session_id)
        if not session:
            return "Error: Session not found."
            
        # Initial Question Generation
        try:
            prompt = PromptTemplate(
                input_variables=["resume_text", "job_description", "match_score", "role", "history", "last_score"],
                template=INTERVIEW_SYSTEM_PROMPT
            )
            chain = prompt | self.llm
            res = chain.invoke({
                "role": session.detected_role,
                "resume_text": session.resume_text,
                "job_description": session.job_description,
                "match_score": session.initial_match_score,
                "history": "No history yet (Start of interview).",
                "last_score": "None"
            })
            question = res.content.strip()
        except Exception as e:
            print(f"⚠️ Interview Start Error: {e}")
            question = "Could you please introduce yourself and your background?"

        # DB Update
        log_message_db(session_id, "assistant", question)
        scores_json = [s.dict() for s in session.question_scores]
        update_session_db(session_id, question, scores_json, True)
        
        return question

    def process_answer(self, session_id: str, answer: str):
        session = self.get_session(session_id)
        if not session or not session.is_active:
            raise ValueError("Invalid or inactive session.")
            
        current_q = session.current_question
        
        # Log User Answer
        log_message_db(session_id, "user", answer)
        
        # 1. Grade Answer
        grade_data = grade_answer(current_q, answer)
        score = grade_data['score']
        
        new_score = QuestionScore(
            question=current_q,
            answer=answer,
            score=score,
            feedback=grade_data['feedback'],
            strength=grade_data['strength'],
            gap=grade_data['gap'],
            improvement=grade_data['improvement']
        )
        session.question_scores.append(new_score)
        
        # 2. Check Termination (e.g., 5 questions)
        scores_json = [s.dict() for s in session.question_scores]
        if len(session.question_scores) >= 5:
            update_session_db(session_id, current_q, scores_json, False)
            return "Interview Complete.", True, grade_data['feedback'], score

        # 3. Generate Next Question
        try:
            # Build History
            history_str = ""
            # session.messages is populated in get_session
            # We want to show the recent exchange
            for msg in session.messages:
                role_label = "Interviewer" if msg.role == "assistant" else "Candidate"
                history_str += f"{role_label}: {msg.content}\n"
            
            # The session.messages list includes the LAST question (assistant) because it was saved 
            # in the previous turn (start_interview or process_answer).
            # It DOES NOT include the current 'answer' (user) because we just logged it 
            # but haven't re-fetched or appended it to the local session object.
            
            # So we only need to append the Candidate's answer to the history passed to LLM.
            history_str += f"Candidate: {answer}\n"

            prompt = PromptTemplate(
                input_variables=["resume_text", "job_description", "match_score", "role", "history", "last_score"],
                template=INTERVIEW_SYSTEM_PROMPT
            )
            chain = prompt | self.llm
            res = chain.invoke({
                "role": session.detected_role,
                "resume_text": session.resume_text,
                "job_description": session.job_description,
                "match_score": session.initial_match_score,
                "history": history_str,
                "last_score": str(score)
            })
            next_q = res.content.strip()
        except Exception as e:
             import traceback
             print(f"⚠️ QP Error: {e}")
             traceback.print_exc()
             # Improved fallback to avoid loops
             import random
             fallbacks = [
                 "That's interesting. Can you tell me about a challenging project you've worked on?",
                 "How do you handle tight deadlines?",
                 "Do you have any experience with cloud technologies?",
                 "What would you say is your biggest technical achievement?"
             ]
             next_q = random.choice(fallbacks)

        # Log & Update
        log_message_db(session_id, "assistant", next_q)
        update_session_db(session_id, next_q, scores_json, True)
        
        return next_q, False, grade_data['feedback'], score

    def calculate_final_result(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return None
            
        scores = [q.score for q in session.question_scores]
        avg_interview_score = sum(scores) / len(scores) if scores else 0
        
        # Weighted Score Calculation
        # Resume: 40% (Background)
        # Interview: 60% (Performance - Higher weight to give Waitlisted candidates a chance)
        match_part = session.initial_match_score * 0.4
        interview_part = (avg_interview_score * 10) * 0.6
        final_score = match_part + interview_part
        
        # Determine Final Status
        # Threshold: 70/100 to be upgrades to Shortlisted
        new_status = "Interviewed" # Default state (completed but not necessarily shortlisted)
        if final_score >= 70:
            new_status = "Shortlisted"
        else:
            new_status = "Rejected"

        if session.candidate_id and session.candidate_id != "unknown":
             update_candidate_interview(
                 session.candidate_id, 
                 round(avg_interview_score * 10, 2),
                 round(final_score, 2),
                 {"transcript": [
                    {"q": q.question, "a": q.answer, "score": q.score, "feedback": q.feedback}
                    for q in session.question_scores
                 ]},
                 status=new_status
             )
        
        return {
            "session_id": session_id,
            "resume_score": session.initial_match_score,
            "interview_score": round(avg_interview_score * 10, 2),
            "final_score": round(final_score, 2),
            "total_questions": len(scores),
            "transcript": [
                {"q": q.question, "a": q.answer, "score": q.score, "feedback": q.feedback}
                for q in session.question_scores
            ]
        }

# Singleton instance
interview_manager = InterviewManager()
