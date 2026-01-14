from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

class StartInterviewRequest(BaseModel):
    resume_text: str
    job_description: str
    match_score: float

class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str

class InterviewResultRequest(BaseModel):
    session_id: str

class InterviewMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: datetime = datetime.now()

class QuestionScore(BaseModel):
    question: str
    answer: str
    score: float  # 0 to 10
    feedback: str
    strength: str = ""
    gap: str = ""
    improvement: str = ""

class InterviewSession(BaseModel):
    session_id: str
    job_description: str
    resume_text: str
    initial_match_score: float
    detected_role: str = "Candidate"
    
    # State
    messages: List[InterviewMessage] = []
    question_scores: List[QuestionScore] = []
    current_question: Optional[str] = None
    is_active: bool = True
    
    # Metadata
    candidate_id: Optional[str] = None
    created_at: datetime = datetime.now()
