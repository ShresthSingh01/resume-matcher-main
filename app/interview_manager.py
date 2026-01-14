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
        self.llm = get_llm(temperature=0.7)

    def create_session(self, resume_text: str, jd: str, match_score: float) -> InterviewSession:
        sid = str(uuid.uuid4())
        
        # Try to find existing candidate context
        candidate_id = "unknown"
        if len(resume_text) == 36: # Likely a candidate ID passed from frontend
             candidate_id = resume_text

        # Create session object
        session = InterviewSession(
            session_id=sid,
            resume_text=resume_text,
            job_description=jd,
            initial_match_score=match_score,
            candidate_id=candidate_id
        )
        
        # Save to DB
        save_session_db(sid, candidate_id, session.detected_role, True)
        
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
                input_variables=["resume_text", "job_description", "match_score", "role", "last_question", "last_answer", "last_score"],
                template=INTERVIEW_SYSTEM_PROMPT
            )
            chain = prompt | self.llm
            res = chain.invoke({
                "role": session.detected_role,
                "resume_text": session.resume_text,
                "job_description": session.job_description,
                "match_score": session.initial_match_score,
                "last_question": "None (Start of Interview)",
                "last_answer": "None",
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
            prompt = PromptTemplate(
                input_variables=["resume_text", "job_description", "match_score", "role", "last_question", "last_answer", "last_score"],
                template=INTERVIEW_SYSTEM_PROMPT
            )
            chain = prompt | self.llm
            res = chain.invoke({
                "role": session.detected_role,
                "resume_text": session.resume_text,
                "job_description": session.job_description,
                "match_score": session.initial_match_score,
                "last_question": current_q,
                "last_answer": answer,
                "last_score": str(score)
            })
            next_q = res.content.strip()
        except Exception as e:
             print(f"⚠️ QP Error: {e}")
             next_q = "Thank you. Let's move to the next topic. What are your key strengths?"

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
        
        match_part = session.initial_match_score * 0.3
        interview_part = (avg_interview_score * 10) * 0.7
        final_score = match_part + interview_part
        
        if session.candidate_id and session.candidate_id != "unknown":
             update_candidate_interview(
                 session.candidate_id, 
                 round(avg_interview_score * 10, 2),
                 round(final_score, 2),
                 {"transcript_len": len(scores)}
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
