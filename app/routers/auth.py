from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from loguru import logger
from fastapi.security import APIKeyHeader
from fastapi import Security
import secrets
from app.db import get_recruiter, create_recruiter, set_user_session, get_user_by_token
from app.auth import hash_password, verify_password

router = APIRouter()

API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)

async def get_current_user(request: Request, api_key: str = Security(API_KEY_HEADER)):
    # 1. Check Session Cookie
    session_token = request.cookies.get("session_token")
    if session_token:
        username = get_user_by_token(session_token)
        if username:
            return username

    # 2. Check Header (for API usage)
    if api_key:
        # Simple token check or separate API key logic
        # For now, treat api_key as session_token
        username = get_user_by_token(api_key)
        if username:
            return username

    raise HTTPException(status_code=401, detail="Not authenticated")

@router.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    try:
        if get_recruiter(username):
             raise HTTPException(status_code=400, detail="Username already exists")
        
        hashed = hash_password(password)
        if create_recruiter(username, hashed):
            return {"message": "User registered successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to register user (DB Error)")
    except Exception as e:
        logger.error(f"Register Error: {e}")
        # import traceback
        # traceback.print_exc() # Loguru handles exceptions in logger.exception or similar but we kept simple error log for now
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    try:
        user = get_recruiter(username)
        if not user:
            # Prevent timing attacks (conceptually), but simple return for now
            raise HTTPException(status_code=401, detail="Invalid credentials user not found")
        
        if verify_password(password, user['password_hash']):
            token = secrets.token_hex(32)
            set_user_session(username, token)
            
            response = JSONResponse(content={"message": "Login successful", "token": token})
            response.set_cookie(key="session_token", value=token, httponly=True)
            return response
        
        raise HTTPException(status_code=401, detail="Invalid credentials pwd mismatch")
    except Exception as e:
        logger.error(f"Login Error: {e}")
        # import traceback
        # traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.api_route("/logout", methods=["GET", "POST"])
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_token")
    return response
