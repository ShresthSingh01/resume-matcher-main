from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from loguru import logger
import asyncio
from app.db import (
    add_candidate, get_leaderboard, get_candidate, 
    update_candidate_status, clear_db
)
from app.schemas import StartInterviewRequest
from app.resume_parser import parse_resume, extract_email
from app.email_service import send_interview_invite, send_shortlist_email, send_rejection_email
from app.utils import clean_text
from app.matcher import extract_required_skills, detect_job_role, extract_skills_async, evaluate_resume_structured
from app.role_templates import get_role_template
from app.jobs_service import search_jobs
from app.routers.auth import get_current_user
import json

router = APIRouter()

@router.get("/candidates/{candidate_id}/status")
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

from app.models.models import UploadJob
from app.jobs import process_upload_job
import uuid

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, user: str = Depends(get_current_user)):
    if not user: raise HTTPException(status_code=401)
    
    # We ideally check if this job belongs to user, but for now open internally
    from app.db import get_db_session
    session = get_db_session()
    try:
        job = session.query(UploadJob).filter(UploadJob.job_id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "total": job.total_files,
            "processed": job.processed_count,
            "results": job.results, # JSON string
            "created_at": job.created_at
        }
    finally:
        session.close()

@router.post("/upload")
async def upload_resume(
    resumes: list[UploadFile] = File(...),
    job_description: str = Form(None),
    jd_file: UploadFile = File(None),
    template_mode: str = Form("auto"),
    enable_interview: bool = Form(True), # New Flag
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: str = Depends(get_current_user)
):
    if not user: raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # 1. Parse JD (Immediate)
        jd_text = ""
        if jd_file:
            jd_content = await jd_file.read()
            jd_text = parse_resume(jd_content, jd_file.filename)
        elif job_description:
            jd_text = clean_text(job_description)
            
        if not jd_text:
            raise HTTPException(status_code=400, detail="Job Description is required.")

        # 2. Create Job Record
        job_id = str(uuid.uuid4())
        
        from app.db import get_db_session
        session = get_db_session()
        try:
            new_job = UploadJob(
                job_id=job_id,
                recruiter_username=user,
                total_files=len(resumes),
                processed_count=0,
                status="queued",
                interview_enabled=enable_interview # Store flag
            )
            session.add(new_job)
            session.commit()
        finally:
            session.close()
            
        # 3. Read files into memory for background processing
        # Note: For massive scale (1000+), save to temp disk instead of RAM
        files_data = []
        filenames = []
        for r in resumes:
            content = await r.read()
            files_data.append(content)
            filenames.append(r.filename)
            
        # 4. Trigger Background Task
        background_tasks.add_task(
            process_upload_job,
            job_id,
            files_data,
            filenames,
            jd_text,
            template_mode,
            user
        )
        
        return {"job_id": job_id, "message": "Upload started in background", "total_files": len(resumes)}

    except Exception as e:
        logger.error(f"Error in /upload: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/leaderboard")
async def leaderboard(user: str = Depends(get_current_user)):
    if not user: raise HTTPException(status_code=401)
    return get_leaderboard(recruiter_username=user)

@router.delete("/candidates")
async def reset_db():
    clear_db()
    return {"message": "Database cleared."}

async def background_rejection_flow(email: str, name: str, resume_text: str):
    """
    Background task: Detect role -> Fetch Adzuna jobs -> Send Rejection Email with jobs.
    """
    try:
        # 1. Detect Role from Resume (or default to 'Software Engineer' if unclear)
        role = await detect_job_role(resume_text)
        if not role: role = "Software Engineer"
        
        with open("debug_rejections_v2.log", "a", encoding="utf-8") as f:
             f.write(f"--- Flow Started ---\n")
             f.write(f"Role: {role}\n")
        
        # 2. Search Jobs
        jobs = search_jobs(role, results_per_page=3)
        
        with open("debug_rejections_v2.log", "a", encoding="utf-8") as f:
             f.write(f"Jobs Found: {len(jobs)}\n")
             f.write(f"Jobs: {str(jobs)}\n")
        
        # 3. Send Email
        send_rejection_email(email, name, jobs)
    except Exception as e:
        with open("debug_rejections_v2.log", "a", encoding="utf-8") as f:
             f.write(f"ERROR: {e}\n")
        # Fallback: send without jobs
        send_rejection_email(email, name, [])

@router.post("/invite/candidate/{cid}")
async def invite_candidate(cid: str, action: str = None, background_tasks: BackgroundTasks = BackgroundTasks()):
    candidate = get_candidate(cid)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    email = extract_email(candidate['resume_text'])
    if not email:
        raise HTTPException(status_code=400, detail="No email found in resume")
        
    status = candidate.get('status', 'Pending')
    
    # If explicit action is requested, update status first
    if action:
        action = action.lower()
        if action == 'reject':
            if "reject" not in status.lower():
                update_candidate_status(cid, "Rejected")
                status = "Rejected" # Local update for logic below
        elif action == 'shortlist':
            if "shortlist" not in status.lower():
                update_candidate_status(cid, "Shortlisted")
                status = "Shortlisted"
        elif action == 'invite':
             # Force invite path if not already strictly rejected/shortlisted?
             # Or just let it fall through to else
             pass

    if "sent" in status.lower():
         return {"message": f"Action already taken for this candidate (Status: {status})"}

    # Handle 'Selected' (from Interview) OR 'Selected (Resume)' (from Resume Only)
    if "selected" in status.lower() and "sent" not in status.lower():
        # HR Decision: Select for Next Round (Hiring)
        # MANUAL TRIGGER: Send Email
        background_tasks.add_task(send_shortlist_email, email, candidate['name'])
        update_candidate_status(cid, "Selected (Email Sent)") 
        return {"message": "Candidate selected for Next Round. Email queued."}

    if status == 'Shortlisted':
        # New Flow: Shortlisted means "Passed Resume Screen" -> Send Interview Invite
        background_tasks.add_task(send_interview_invite, email, candidate['name'], cid)
        update_candidate_status(cid, "Invited")
        msg = "Interview invitation sent to Shortlisted candidate."
        
    elif status == 'Interviewed' or status == 'Completed':
        # HR Decision: Select for Next Round
        background_tasks.add_task(send_shortlist_email, email, candidate['name'])
        update_candidate_status(cid, "Selected (Email Sent)")
        msg = "Candidate selected for Next Round. Email queued."
        
    elif "reject" in status.lower():
        # MANUAL TRIGGER: Send Email
        background_tasks.add_task(background_rejection_flow, email, candidate['name'], candidate['resume_text'])
        update_candidate_status(cid, "Rejected (Email Sent)")
        msg = "Rejection email with job suggestions queued."
    else:
        # Fallback for any old "Waitlisted" or "Pending" - Default to Interview Invite if not Rejected
        background_tasks.add_task(send_interview_invite, email, candidate['name'], cid)
        update_candidate_status(cid, "Invited")
        msg = "Interview invitation queued (Fallback)."

    return {"message": msg}
