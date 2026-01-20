# Resume Matcher Main App
import sentry_sdk
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import log_requests_middleware
from app.db import init_db

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

# Include Routers
app.include_router(auth.router)
app.include_router(candidates.router)
app.include_router(interview.router)
app.include_router(jobs.router)

# --- Top Level Page Routes ---
from fastapi.responses import RedirectResponse

@app.get("/")
async def redirect_root():
    return RedirectResponse(f"{settings.FRONTEND_URL}/")

@app.get("/login")
async def redirect_login():
    return RedirectResponse(f"{settings.FRONTEND_URL}/login")

@app.get("/candidate")
async def redirect_candidate(request: Request):
    return RedirectResponse(f"{settings.FRONTEND_URL}/candidate?{request.query_params}")


