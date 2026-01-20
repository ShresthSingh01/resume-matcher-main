import uuid
from typing import Optional
from langchain_core.prompts import PromptTemplate
from app.schemas import InterviewSession, QuestionScore, InterviewMessage
from app.grading import grade_answer
from app.llm import get_llm
from app.interview_prompts import INTERVIEW_SYSTEM_PROMPT
from app.core.redis import redis_client
from app.db import (
    save_session_db, get_session_db, update_session_db, log_message_db, 
    get_candidate, get_session_messages, update_candidate_interview
)
import json
from loguru import logger

class InterviewManager:
    def __init__(self):
        self.llm = get_llm(temperature=0.7, max_tokens=600)

    def deduce_role(self, jd_text: str) -> str:
        try:
             from app.interview_prompts import ROLE_DEDUCTION_PROMPT
             chain = ROLE_DEDUCTION_PROMPT | self.llm
             res = chain.invoke({"job_description": jd_text})
             role = res.content.strip()
             role = role.replace('"', '').replace("'", "")
             return role
        except Exception as e:
            logger.warning(f"⚠️ Role Deduction Failed: {e}")
            return "Candidate"

    def create_session(
        self, 
        resume_text: Optional[str] = None, 
        jd: Optional[str] = None, 
        match_score: Optional[float] = None,
        candidate_id: Optional[str] = None
    ) -> InterviewSession:
        sid = str(uuid.uuid4())
        
        # Resolve from DB if ID provided
        if candidate_id:
            db_candidate = get_candidate(candidate_id)
            if db_candidate:
                resume_text = db_candidate['resume_text']
                jd = db_candidate['job_description']
                match_score = db_candidate['match_score']

        # Legacy/Fallback Logic
        if not candidate_id and resume_text and len(resume_text) == 36:
             candidate_id = resume_text
             db_candidate = get_candidate(candidate_id)
             if db_candidate:
                 resume_text = db_candidate['resume_text']
                 jd = db_candidate['job_description']
                 match_score = db_candidate['match_score']

        role = self.deduce_role(jd if jd else "")

        session = InterviewSession(
            session_id=sid,
            resume_text=resume_text or "",
            job_description=jd or "",
            initial_match_score=match_score or 0.0,
            candidate_id=candidate_id or "unknown",
            detected_role=role
        )
        
        # 1. Save to Redis (Hot State)
        redis_client.set_session(sid, session.dict())
        
        # 2. Save to DB (Persistence)
        save_session_db(sid, session.candidate_id, session.detected_role, True)
        
        return session

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        # 1. Try Redis
        data = redis_client.get_session(session_id)
        if data:
            return InterviewSession(**data)
        
        # 2. Fallback to DB
        row = get_session_db(session_id)
        if not row:
            return None
        
        # Rehydrate from DB
        cid = row['candidate_id']
        candidate = get_candidate(cid)
        
        resume_text = candidate['resume_text'] if candidate else ""
        jd = candidate['job_description'] if candidate else ""
        match_score = candidate['match_score'] if candidate and candidate.get('match_score') is not None else 0.0
        
        session = InterviewSession(
            session_id=row['session_id'],
            resume_text=resume_text,
            job_description=jd,
            initial_match_score=match_score,
            detected_role=row['role'],
            is_active=bool(row['is_active']),
            candidate_id=cid
        )
        
        # Load messages & scores
        msgs = get_session_messages(session_id)
        for m in msgs:
            session.messages.append(InterviewMessage(role=m['role'], content=m['content']))
            
        if row['scores']:
            scores_data = json.loads(row['scores'])
            for s in scores_data:
                session.question_scores.append(QuestionScore(**s))
            
        session.current_question = row['current_question']
        
        # Populate Cache
        redis_client.set_session(session_id, session.dict())
        
        return session

    def start_interview(self, session_id: str) -> str:
        session = self.get_session(session_id)
        if not session:
            return "Error: Session not found."
            
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
                "history": "No history yet.",
                "last_score": "None"
            })
            question = res.content.strip()
        except Exception as e:
            logger.error(f"Interview Start Error: {e}")
            question = "Could you please introduce yourself?"

        # Update State
        session.current_question = question
        session.messages.append(InterviewMessage(role="assistant", content=question))

        # Sync
        redis_client.set_session(session_id, session.dict())
        log_message_db(session_id, "assistant", question)
        update_session_db(session_id, question, [s.dict() for s in session.question_scores], True)
        
        return question

    def process_answer(self, session_id: str, answer: str):
        session = self.get_session(session_id)
        if not session or not session.is_active:
            raise ValueError("Invalid or inactive session.")
            
        current_q = session.current_question
        
        # Log Answer
        session.messages.append(InterviewMessage(role="user", content=answer))
        log_message_db(session_id, "user", answer)
        
        # Grade
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
        
        # Check Termination
        if len(session.question_scores) >= 5:
            redis_client.delete_session(session_id) # Optional: Clear cache on finish
            update_session_db(session_id, current_q, [s.dict() for s in session.question_scores], False)
            return "Interview Complete.", True, grade_data['feedback'], score

        # Next Question
        try:
            history_str = ""
            for msg in session.messages:
                # Include local history including the just-added answer
                role_label = "Interviewer" if msg.role == "assistant" else "Candidate"
                history_str += f"{role_label}: {msg.content}\n"
            
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
        except Exception:
             # Simple fallback
             import random
             next_q = random.choice([
                 "Tell me about a challenging project?",
                 "How do you handle deadlines?"
             ])

        # Update Session
        session.current_question = next_q
        session.messages.append(InterviewMessage(role="assistant", content=next_q))
        
        # Sync
        redis_client.set_session(session_id, session.dict())
        log_message_db(session_id, "assistant", next_q)
        update_session_db(session_id, next_q, [s.dict() for s in session.question_scores], True)
        
        return next_q, False, grade_data['feedback'], score

    def calculate_final_result(self, session_id: str) -> dict:
        # Try DB source of truth for final result
        session = self.get_session(session_id) 
        if not session:
            return None
            
        scores = [q.score for q in session.question_scores]
        avg_interview_score = sum(scores) / len(scores) if scores else 0
        
        # New Weighted Logic: 40% Resume + 60% Interview
        match_part = session.initial_match_score * 0.40
        interview_part = (avg_interview_score * 10) * 0.60
        final_score = match_part + interview_part
        
        # New Threshold: 60% Total Score
        threshold = 60.0
        # MANUAL REVIEW MODE:
        # Instead of Auto-Reject/Select, lay them all as "Interviewed"
        # The recruiter will sort by score on the leaderboard and decide.
        new_status = "Interviewed"

        if session.candidate_id and session.candidate_id != "unknown":
             # Check for Anti-Cheating Flags
             db_cand = get_candidate(session.candidate_id)
             penalty_msg = ""
             if db_cand and db_cand.get('flags'):
                 flags = json.loads(db_cand['flags'])
                 flag_count = len(flags)
                 
                 if flag_count > 0:
                     logger.warning(f"⚠️ Candidate {session.candidate_id} has {flag_count} cheat flags.")
                     # Penalty Logic
                     if flag_count >= 2:
                         final_score = 0
                         new_status = "Rejected (Cheating)"
                         penalty_msg = f"Rejected due to {flag_count} anti-cheating violations."
                     else:
                         # 20% penalty for 1 flag
                         penalty = final_score * 0.2
                         final_score -= penalty
                         penalty_msg = f"Score reduced by 20% due to anti-cheating violation."

             update_candidate_interview(
                 session.candidate_id, 
                 round(avg_interview_score * 10, 2),
                 round(final_score, 2),
                 {
                     "transcript": [
                        {"q": q.question, "a": q.answer, "score": q.score, "feedback": q.feedback}
                        for q in session.question_scores
                     ],
                     "note": penalty_msg
                 },
                 status=new_status
             )
        
        return {
            "session_id": session_id,
            "resume_score": session.initial_match_score,
            "interview_score": round(avg_interview_score * 10, 2),
            "final_score": round(final_score, 2),
            "decision": new_status,
            "transcript": [
                {"q": q.question, "a": q.answer, "score": q.score}
                for q in session.question_scores
            ]
        }

interview_manager = InterviewManager()
