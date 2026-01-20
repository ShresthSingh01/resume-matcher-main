from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.models import Candidate, Recruiter, InterviewSession, InterviewMessage
import uuid
import json
from typing import List, Dict, Optional
from datetime import datetime

# Initialize tables (auto-create if not exist for Dev simplicity, ideally use alembic upgrade head)
# Base.metadata.create_all(bind=engine)

def get_db_session():
    return SessionLocal()

def run_migrations():
    """
    Lightweight auto-migration to add missing columns.
    """
    session = get_db_session()
    try:
        from sqlalchemy import text
        # Check Candidate table
        try:
            session.execute(text("SELECT interview_enabled FROM candidates LIMIT 1"))
        except Exception:
            print("⚠️ Migration: Adding 'interview_enabled' to candidates table...")
            session.rollback()
            session.execute(text("ALTER TABLE candidates ADD COLUMN interview_enabled BOOLEAN DEFAULT 1"))
            session.commit()
            
        # Check UploadJob table
        try:
            session.execute(text("SELECT interview_enabled FROM upload_jobs LIMIT 1"))
        except Exception:
            print("⚠️ Migration: Adding 'interview_enabled' to upload_jobs table...")
            session.rollback()
            session.execute(text("ALTER TABLE upload_jobs ADD COLUMN interview_enabled BOOLEAN DEFAULT 1"))
            session.commit()
            
    except Exception as e:
        print(f"Migration Error: {e}")
    finally:
        session.close()

def init_db():
    # In production, use Alembic. For now, we can ensure tables exist.
    Base.metadata.create_all(bind=engine)
    run_migrations() # Run auto-migration
    print("✅ Database initialized (SQLAlchemy)")

def clear_db():
    session = get_db_session()
    try:
        session.query(InterviewMessage).delete()
        session.query(InterviewSession).delete()
        session.query(Candidate).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error clearing DB: {e}")
    finally:
        session.close()

# --- Candidate Functions ---

def add_candidate(name: str, resume_text: str, jd: str, match_score: float, matched_skills: list, missing_skills: list, resume_evaluation: dict = {}, status: str = "Matched", recruiter_username: str = None, interview_enabled: bool = True, final_score: float = 0.0) -> str:
    session = get_db_session()
    try:
        cid = str(uuid.uuid4())
        new_candidate = Candidate(
            id=cid,
            name=name,
            resume_text=resume_text,
            job_description=jd,
            match_score=match_score,
            status=status,
            matched_skills=json.dumps(matched_skills),
            missing_skills=json.dumps(missing_skills),
            resume_evaluation_data=json.dumps(resume_evaluation),
            recruiter_username=recruiter_username,
            interview_enabled=interview_enabled,
            interview_score=0.0,
            final_score=final_score,
            feedback_data="{}"
        )
        session.add(new_candidate)
        session.commit()
        return cid
    except Exception as e:
        session.rollback()
        print(f"DB Error add_candidate: {e}")
        raise e
    finally:
        session.close()

def get_candidate(cid: str) -> Optional[Dict]:
    session = get_db_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == cid).first()
        if candidate:
             return {k: v for k, v in candidate.__dict__.items() if not k.startswith('_')}
        return None
    finally:
        session.close()

def get_leaderboard(recruiter_username: str = None) -> List[Dict]:
    session = get_db_session()
    try:
        query = session.query(Candidate).order_by(Candidate.final_score.desc(), Candidate.match_score.desc())
        
        if recruiter_username:
             query = query.filter(Candidate.recruiter_username == recruiter_username)
             
        candidates = query.all()
        return [{k: v for k, v in c.__dict__.items() if not k.startswith('_')} for c in candidates]
    finally:
        session.close()

def update_candidate_interview(cid: str, interview_score: float, final_score: float, feedback: dict, status: str = 'completed'):
    session = get_db_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == cid).first()
        if candidate:
            candidate.interview_score = interview_score
            candidate.final_score = final_score
            candidate.status = status
            candidate.feedback_data = json.dumps(feedback)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"DB Error update_candidate: {e}")
        return False
    finally:
        session.close()

def update_candidate_status(cid: str, status: str):
    session = get_db_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == cid).first()
        if candidate:
            candidate.status = status
            session.commit()
    finally:
        session.close()

def flag_candidate(cid: str, violation: str) -> int:
    session = get_db_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == cid).first()
        if candidate:
             flags = json.loads(candidate.flags) if candidate.flags else []
             flags.append({"violation": violation, "timestamp": str(datetime.now())})
             candidate.flags = json.dumps(flags)
             session.commit()
             return len(flags)
        return 0
    finally:
        session.close()


# --- Session Functions ---

def save_session_db(session_id: str, candidate_id: str, role: str, is_active: bool = True):
    session = get_db_session()
    try:
        # Check if exists (upsert)
        existing = session.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if existing:
            existing.candidate_id = candidate_id
            existing.role = role
            existing.is_active = is_active
        else:
            new_sess = InterviewSession(
                session_id=session_id,
                candidate_id=candidate_id,
                role=role,
                is_active=is_active,
                current_question="",
                scores="[]"
            )
            session.add(new_sess)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"DB Error save_session: {e}")
    finally:
        session.close()

def get_session_db(session_id: str):
    session = get_db_session()
    try:
        sess = session.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if sess:
            return {k: v for k, v in sess.__dict__.items() if not k.startswith('_')}
        return None
    finally:
        session.close()

def update_session_db(session_id: str, current_question: str, scores: list, is_active: bool):
    session = get_db_session()
    try:
        sess = session.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if sess:
            sess.current_question = current_question
            sess.scores = json.dumps(scores)
            sess.is_active = is_active
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"DB Error update_session: {e}")
    finally:
        session.close()

def log_message_db(session_id: str, role: str, content: str):
    session = get_db_session()
    try:
        msg = InterviewMessage(session_id=session_id, role=role, content=content)
        session.add(msg)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"DB Error log_message: {e}")
    finally:
        session.close()

def get_session_messages(session_id: str):
    session = get_db_session()
    try:
        msgs = session.query(InterviewMessage).filter(InterviewMessage.session_id == session_id).order_by(InterviewMessage.timestamp.asc()).all()
        return [{"role": m.role, "content": m.content} for m in msgs]
    finally:
        session.close()

def get_active_session_by_candidate(candidate_id: str):
    session = get_db_session()
    try:
        sess = session.query(InterviewSession).filter(
            InterviewSession.candidate_id == candidate_id, 
            InterviewSession.is_active == True # noqa
        ).order_by(InterviewSession.created_at.desc()).first()
        
        if sess:
            return {k: v for k, v in sess.__dict__.items() if not k.startswith('_')}
        return None
    finally:
        session.close()


# --- Recruiter Functions ---

def create_recruiter(username: str, password_hash: str) -> bool:
    session = get_db_session()
    try:
        # Check if exists
        if session.query(Recruiter).filter(Recruiter.username == username).first():
            return False
            
        new_user = Recruiter(username=username, password_hash=password_hash)
        session.add(new_user)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"DB Error create_recruiter: {e}")
        return False
    finally:
        session.close()

def get_recruiter(username: str) -> Optional[Dict]:
    session = get_db_session()
    try:
        user = session.query(Recruiter).filter(Recruiter.username == username).first()
        if user:
            return {k: v for k, v in user.__dict__.items() if not k.startswith('_')}
        return None
    except Exception as e:
        print(f"DB Error get_recruiter: {e}")
        return None
    finally:
        session.close()

def set_user_session(username: str, token: str):
    session = get_db_session()
    try:
        user = session.query(Recruiter).filter(Recruiter.username == username).first()
        if user:
            user.session_token = token
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"DB Error set_user_session: {e}")
    finally:
        session.close()

def get_user_by_token(token: str) -> Optional[str]:
    session = get_db_session()
    try:
        user = session.query(Recruiter).filter(Recruiter.session_token == token).first()
        if user:
            return user.username
        return None
    except Exception as e:
        print(f"DB Error get_user_by_token: {e}")
        return None
    finally:
        session.close()
