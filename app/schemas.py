from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime


class Education(BaseModel):
    institution: str = Field(description="Name of the university or school")
    degree: str = Field(description="Degree obtained, e.g., B.Sc. Computer Science")
    year: str = Field(description="Year of graduation or duration")

class Experience(BaseModel):
    company: str = Field(description="Name of the company")
    role: str = Field(description="Job title")
    duration: str = Field(description="Duration of employment")
    description: str = Field(description="Brief summary of responsibilities")

class CandidateProfile(BaseModel):
    name: str = Field(description="Full name of the candidate")
    email: str = Field(description="Email address")
    phone: str = Field(description="Phone number")
    skills: List[str] = Field(description="List of technical skills")
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

class StartInterviewRequest(BaseModel):
    resume_text: Optional[str] = None
    job_description: Optional[str] = None
    match_score: Optional[float] = None
    candidate_id: Optional[str] = None

class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str

class InterviewResultRequest(BaseModel):
    session_id: str

class FlagRequest(BaseModel):
    session_id: str
    reason: str

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

class ExtractedEvidence(BaseModel):
    education: str
    experience: str
    skills: List[str]
    projects: str
    certifications: str

class LikertScores(BaseModel):
    education: int
    experience: int
    skills: int
    projects: int
    certifications: int

class ResumeFeedback(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]

class ResumeEvaluationOutput(BaseModel):
    extracted_evidence: ExtractedEvidence
    likert_scores: LikertScores
    weighted_resume_score: float
    decision: str
    interview_required: bool
    resume_feedback: ResumeFeedback

class UploadJobResponse(BaseModel):
    job_id: str
    status: str
    total_files: int
    processed_count: int
    results: Optional[str] = None # JSON string of results
    created_at: datetime
