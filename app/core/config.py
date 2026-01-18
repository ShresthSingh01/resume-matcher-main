import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    # Default to SQLite for fallback, but Production should set DATABASE_URL
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/valid_candidates.db")
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Sentry
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    
    # App
    TITLE = "AI Resume Matcher & Interviewer"
    VERSION = "2.0.0"
    
    # Security
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

settings = Settings()
