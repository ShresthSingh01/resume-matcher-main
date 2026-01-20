import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    # Default to SQLite for fallback, but Production should set DATABASE_URL
    # Database
    # Default to SQLite for fallback, but Production should set DATABASE_URL
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/valid_candidates.db")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Sentry
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    
    # App
    TITLE = "AI Resume Matcher & Interviewer"
    VERSION = "2.0.0"
    
    # Security
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # Frontend URL (for redirects)
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

settings = Settings()
