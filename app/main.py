# Resume Matcher Main App
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from app.db import init_db, add_candidate, get_leaderboard, get_candidate, update_candidate_interview, clear_db
from app.schemas import StartInterviewRequest, InterviewAnswerRequest, InterviewResultRequest
from app.resume_parser import parse_resume
from app.embeddings import check_duplicate, load_initial_embeddings
from app.matcher import extract_skills, calculate_match_score
from app.utils import clean_text
from app.interview_manager import interview_manager
from app.tts import TTSManager

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

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.post("/upload")
async def upload_resume(
    resumes: list[UploadFile] = File(...),
    job_description: str = Form(None),
    jd_file: UploadFile = File(None)
):
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

        # Loop through all uploaded resumes
        for resume in resumes:
            try:
                # 1. Parse Resume
                file_content = await resume.read()
                resume_text = parse_resume(file_content, resume.filename)
                
                if not resume_text:
                    continue # Skip empty
                    
                # 3. Duplicate Check
                is_duplicate = check_duplicate(resume_text)
                
                # 4. Match
                match_data = extract_skills(resume_text, jd_text)
                match_score = calculate_match_score(
                    match_data['matched_skills'], 
                    match_data['missing_skills'],
                    resume_text=resume_text,
                    jd_text=jd_text
                )
                
                # 5. Save to DB
                cid = add_candidate(
                    name=resume.filename, 
                    resume_text=resume_text, 
                    jd=jd_text, 
                    match_score=match_score
                )

                results.append({
                    "candidate_id": cid,
                    "filename": resume.filename,
                    "match_score": match_score,
                    "matched_skills": match_data['matched_skills'],
                    "missing_skills": match_data['missing_skills'],
                    "reasoning": match_data['reasoning'],
                    "is_duplicate": is_duplicate,
                    "interview_context": {
                        "can_interview": True,
                        "prompt": "Proceed to AI Interview?",
                        "payload": {
                            "resume_text": resume_text, 
                            "job_description": jd_text,
                            "match_score": match_score
                        }
                    }
                })
            except Exception as e:
                print(f"Error processing {resume.filename}: {e}")

        return results
        
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
        session = interview_manager.create_session(
            resume_text=request.resume_text,
            jd=request.job_description,
            match_score=request.match_score
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
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/leaderboard")
async def leaderboard():
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
