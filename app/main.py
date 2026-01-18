# Resume Matcher Main App
import sentry_sdk
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import log_requests_middleware
from app.db import init_db, get_leaderboard, get_user_by_token
from app.embeddings import load_initial_embeddings
from fastapi.middleware.cors import CORSMiddleware

# Import Routers
from app.routers import auth, candidates, interview, jobs

# Sentry Initialization
if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=1.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Logic
    setup_logging()
    logger.info(f"System Startup: {settings.TITLE} v{settings.VERSION}")
    init_db()
    
    init_db()
    
    # Embeddings are now lazy loaded on first use
    logger.info("Embeddings will be loaded on demand.")

    yield
    # Shutdown Logic
    logger.info("System Shutdown")

app = FastAPI(
    title=settings.TITLE,
    version=settings.VERSION,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(log_requests_middleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
app.include_router(auth.router)
app.include_router(candidates.router)
app.include_router(interview.router)
app.include_router(jobs.router)

# --- Top Level Page Routes ---

async def get_current_user_optional(request: Request):
    # 1. Check Session Cookie
    session_token = request.cookies.get("session_token")
    if session_token:
        username = get_user_by_token(session_token)
        if username:
            return username
    return None

@app.get("/login")
async def login_page():
    return FileResponse("static/login.html")

@app.get("/")
async def read_root(request: Request):
    user = await get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse("static/index.html")

@app.get("/interview/start")
async def read_interview_start(candidate_id: str):
    """
    Serves the Candidate Interview Portal.
    """
    return FileResponse("static/candidate.html")

