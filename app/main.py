# Resume Matcher Main App
import os
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from app.db import init_db, add_candidate, get_leaderboard, get_candidate, update_candidate_interview, clear_db
from app.schemas import StartInterviewRequest, InterviewAnswerRequest, InterviewResultRequest
from app.resume_parser import parse_resume, extract_email
from app.embeddings import check_duplicate, load_initial_embeddings
# Auth Imports
from fastapi import Request, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
import secrets

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")
# Generate a random token on server start. 
# This invalidates all previous sessions every time the server restarts.
CURRENT_SESSION_TOKEN = secrets.token_hex(16)

from app.matcher import extract_skills, calculate_match_score, extract_skills_async, extract_profile_async

from app.utils import clean_text
from app.interview_manager import interview_manager
from app.tts import TTSManager
from app.email_service import send_interview_invite
import asyncio

tts_manager = TTSManager()

app = FastAPI(
    title="AI Resume Matcher & Interviewer",
    version="2.0.0"
)

# Initialize DB and Embeddings
@app.on_event("startup")
async def startup_event():
    init_db()
    # Optional: Load existing resumes for duplicate check
    candidates = get_leaderboard()
    texts = [c['resume_text'] for c in candidates if c.get('resume_text')]
    load_initial_embeddings(texts)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/login")
async def login_page():
    return FileResponse("static/login.html")

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    print(f"Login Attempt: Input user='{username}', pass='{password}'")
    print(f"Comparing against: Admin user='{ADMIN_USER}', pass='{ADMIN_PASS}'")
    
    if username.strip() == ADMIN_USER and password.strip() == ADMIN_PASS:
        resp = JSONResponse(content={"message": "Logged In"})
        resp.set_cookie(key="session_token", value=CURRENT_SESSION_TOKEN, httponly=True)
        return resp
    raise HTTPException(status_code=401, detail="Invalid Credentials")

@app.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("session_token")
    return resp

# Middleware / Dependency for Recruiter Routes
async def get_current_user(request: Request):
    token = request.cookies.get("session_token")
    if token != CURRENT_SESSION_TOKEN:
        return None
    return token

@app.get("/")
async def read_root(user: str = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    return FileResponse("static/index.html")

@app.get("/interview/start")
async def read_interview_start(candidate_id: str):
    """
    Serves the Candidate Interview Portal.
    """
    return FileResponse("static/candidate.html")

@app.get("/candidates/{candidate_id}/status")
async def get_candidate_status(candidate_id: str):
    data = get_candidate(candidate_id)
    if not data:
        return {"status": "not_found"}
    
    # Check if feedback/transcript exists to confirm completion
    is_complete = False
    if data.get('status') == 'completed':
        is_complete = True
    elif data.get('feedback_data'):
         # Fallback if status wasn't explicitly set but feedback exists
         try:
             fb = json.loads(data['feedback_data'])
             if fb and len(fb) > 0: is_complete = True
         except: pass

    return {
        "status": "completed" if is_complete else "pending",
        "interview_score": data.get("interview_score"),
        "final_score": data.get("final_score")
    }

@app.post("/upload")
async def upload_resume(
    resumes: list[UploadFile] = File(...),
    job_description: str = Form(None),
    jd_file: UploadFile = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: str = Depends(get_current_user)
):
    if not user: raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # 2. Parse JD (Once for all)
        jd_text = ""
        if jd_file:
            jd_content = await jd_file.read()
            jd_text = parse_resume(jd_content, jd_file.filename)
        elif job_description:
            jd_text = clean_text(job_description)
            
        if not jd_text:
            raise HTTPException(status_code=400, detail="Job Description is required.")

        results = []

       
        # 3. Process Resumes in Parallel (with Semaphore)
        sem = asyncio.Semaphore(5) # Limit to 5 concurrent LLM calls
        
        async def process_single_resume(resume):
            try:
                # A. Parse
                file_content = await resume.read()
                resume_text = parse_resume(file_content, resume.filename)
                
                if not resume_text:
                    return None
                
                # B. Async Extraction (with rate limit)
                async with sem:
                    # Only Skills now
                    skills_task = extract_skills_async(resume_text, jd_text)
                    match_data = await skills_task

                
                # C. Match Score
                match_score = calculate_match_score(
                    match_data['matched_skills'], 
                    match_data['missing_skills'],
                    resume_text=resume_text,
                    jd_text=jd_text
                )
                
                # D. DB Save
                # Fallback Profile
                cid = add_candidate(
                    name=resume.filename, 
                    resume_text=resume_text, 
                    jd=jd_text, 
                    match_score=match_score,
                    matched_skills=match_data['matched_skills'],
                    missing_skills=match_data['missing_skills']
                )
                
                # E. Result Structure
                return {
                    "candidate_id": cid,
                    "filename": resume.filename,
                    "name": resume.filename,
                    "email": "N/A",
                    "phone": "N/A",
                    "match_score": match_score,
                    "matched_skills": match_data['matched_skills'],
                    "missing_skills": match_data['missing_skills'],
                    "reasoning": match_data['reasoning'],
                    "profile": {}, # Empty profile
                    "is_duplicate": check_duplicate(resume_text),
                    "interview_context": {
                        "can_interview": True,
                        "prompt": "Proceed to AI Interview?",
                        "payload": {
                            "resume_text": resume_text, 
                            "job_description": jd_text,
                            "match_score": match_score
                        }
                    }
                }
            except Exception as e:
                print(f"Error processing {resume.filename}: {e}")
                return {"filename": resume.filename, "error": str(e)}

        # Run all tasks
        tasks = [process_single_resume(r) for r in resumes]
        results = await asyncio.gather(*tasks)
        
        # Filter None
        return [r for r in results if r]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        with open("error.log", "w") as f:
            f.write(traceback.format_exc())
        print(f"Error in /upload: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/interview/start")
async def start_interview(request: StartInterviewRequest):
    try:
        # Create session
        
        # If candidate_id provided but no context, fetch from DB
        resume_text = request.resume_text
        jd_text = request.job_description
        match_score = request.match_score

        if request.candidate_id and (not resume_text or not jd_text):
            candidate = get_candidate(request.candidate_id)
            if not candidate:
                 raise HTTPException(status_code=404, detail="Candidate not found.")
            resume_text = candidate['resume_text']
            jd_text = candidate['job_description']
            match_score = candidate['match_score']

        session = interview_manager.create_session(
            candidate_id=request.candidate_id, 
            resume_text=resume_text, 
            jd=jd_text,
            match_score=match_score
        )
        
        # Generate first question
        question = interview_manager.start_interview(session.session_id)
        
        return {
            "session_id": session.session_id,
            "role": session.detected_role,
            "question": question
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/interview/answer")
async def submit_answer(request: InterviewAnswerRequest):
    try:
        next_q, is_finished, feedback, score = interview_manager.process_answer(
            session_id=request.session_id,
            answer=request.answer
        )
        
        return {
            "next_question": next_q,
            "is_finished": is_finished,
            "feedback": feedback,
            "score": score
        }
    except ValueError as ve:
         return JSONResponse(status_code=400, content={"error": str(ve)})
    except Exception as e:
        import traceback
        with open("error.log", "w") as f:
            f.write(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/interview/result")
async def get_result(request: InterviewResultRequest):
    try:
        # 1️⃣ Calculate result ONCE
        result = interview_manager.calculate_final_result(request.session_id)
        if not result:
             raise HTTPException(status_code=404, detail="Session not found.")
             
        # Optional: Update DB if we had candidate_id logic wired through session
        # But for now, we return valid result
        
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR in /interview/result: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/leaderboard")
async def leaderboard(user: str = Depends(get_current_user)):
    if not user: raise HTTPException(status_code=401)
    return get_leaderboard()

@app.delete("/candidates")
async def reset_db():
    clear_db()
    return {"message": "Database cleared."}

@app.post("/interview/speak")
async def speak_text(payload: dict):
    text = payload.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    try:
        # If API Key is present, use ElevenLabs
        print("DEBUG: /interview/speak called")
        if tts_manager.client:
            print("DEBUG: Streaming audio from ElevenLabs...")
            return StreamingResponse(
                tts_manager.stream_audio(text),
                media_type="audio/mpeg"
            )
        else:
             print("DEBUG: TTS Manager has no client. Sending 503.")
             # Fallback signal for frontend to use Browser TTS
             return JSONResponse(status_code=503, content={"error": "TTS_DISABLED"})
    except Exception as e:
        print(f"DEBUG: TTS Route Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/invite/candidate/{cid}")
async def invite_candidate(cid: str, background_tasks: BackgroundTasks):
    candidate = get_candidate(cid)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    email = extract_email(candidate['resume_text'])
    if not email:
        raise HTTPException(status_code=400, detail="No email found in resume")
        
    background_tasks.add_task(send_interview_invite, email, candidate['name'], cid)
    return {"message": f"Invitation queued for {email}"}

# 5. Adzuna Job Search Endpoint
@app.get("/jobs/recommend")
async def get_job_recommendations(role: str):
    """
    Fetches job recommendations from Adzuna based on the role.
    """
    from app.jobs_service import search_jobs
    
    # Basic cleaning of role text
    clean_role = role.split(',')[0].strip() # Take first part if comma separated
    
    jobs = search_jobs(clean_role)
    return {"role": clean_role, "jobs": jobs}
