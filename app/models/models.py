from sqlalchemy import Column, String, Float, Boolean, Text, ForeignKey, Integer, DateTime
from sqlalchemy.sql import func
from app.database import Base
import json

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    resume_text = Column(String)
    job_description = Column(String)
    match_score = Column(Float)
    interview_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    status = Column(String, default="Matched")
    feedback_data = Column(Text, default="{}") # JSON string
    matched_skills = Column(Text, default="[]") # JSON string
    missing_skills = Column(Text, default="[]") # JSON string
    resume_evaluation_data = Column(Text, default="{}")
    flags = Column(Text, default="[]")
    interview_enabled = Column(Boolean, default=True) # New Flag
    recruiter_username = Column(String, ForeignKey("recruiters.username"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UploadJob(Base):
    __tablename__ = "upload_jobs"

    job_id = Column(String, primary_key=True, index=True)
    recruiter_username = Column(String, ForeignKey("recruiters.username"))
    total_files = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    status = Column(String, default="processing") # processing, completed, failed
    interview_enabled = Column(Boolean, default=True) # New Flag
    results = Column(Text, default="[]") # Store JSON list of candidate_ids or errors
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Recruiter(Base):
    __tablename__ = "recruiters"

    username = Column(String, primary_key=True, index=True)
    password_hash = Column(String)
    session_token = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    session_id = Column(String, primary_key=True, index=True)
    candidate_id = Column(String, ForeignKey("candidates.id"))
    role = Column(String)
    current_question = Column(String)
    scores = Column(Text, default="[]")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("interview_sessions.session_id"))
    role = Column(String) # user/assistant
    content = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
