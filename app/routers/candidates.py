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

@router.post("/upload")
async def upload_resume(
    resumes: list[UploadFile] = File(...),
    job_description: str = Form(None),
    jd_file: UploadFile = File(None),
    template_mode: str = Form("auto"),
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
        
        # Pre-calculate JD context ONCE
        # A. Detect Role (or use Manual)
        if template_mode and template_mode != "auto":
             detected_role = template_mode 
        else:
             try:
                 detected_role = await detect_job_role(jd_text)
             except Exception as e:
                 logger.error(f"Role Detection Failed (Quota/Error): {e}")
                 # Fallback so we don't crash the entire upload
                 detected_role = "Software Engineer" # Default fallback
             
        logger.info(f"Role Mode: {template_mode}, Active Role: {detected_role}")
        
        # B. Get Template
        role_template, thresholds = get_role_template(detected_role)
        
        # C. Extract JD Skills (for required_skills param)
        required_skills = await extract_required_skills(jd_text)
        
        async def process_single_resume(resume):
            try:
                # A. Parse
                file_content = await resume.read()
                resume_text = parse_resume(file_content, resume.filename)
                
                if not resume_text:
                    return None
                
                # B. Async Evaluation (with rate limit)
                async with sem:
                    evaluation_result = await evaluate_resume_structured(
                        resume_text=resume_text,
                        job_role=detected_role,
                        experience_level="Mid", # Defaulting to Mid if unknown, or we could infer from role name
                        required_skills=required_skills,
                        role_template=role_template,
                        thresholds=thresholds
                    )

                # C. Extract Data for response/DB
                match_score = evaluation_result.weighted_resume_score
                matched_skills = evaluation_result.extracted_evidence.skills # This is technically resume skills, not intersection.
                # For compatibility with frontend "matched_skills" display:
                # We should compute intersection or just use resume skills?
                # The frontend likely expects 'matched' (intersection) and 'missing'.
                # The new schema output has 'extracted_evidence.skills'.
                # Let's do a quick set intersection here for UI compatibility
                r_skills = set(s.lower() for s in evaluation_result.extracted_evidence.skills)
                jd_skills = set(s.lower() for s in required_skills)
                
                # Simple set math for compatibility
                found_list = [s for s in required_skills if s.lower() in r_skills]
                missing_list = [s for s in required_skills if s.lower() not in r_skills]
                
                # D. Determine Status
                # "Strong Match (Shortlist)" -> "Shortlisted"
                # "Borderline (Interview Required)" -> "Interview"
                # "Weak Match (Reject)" -> "Rejected"
                status = "Reviewed"
                d = evaluation_result.decision.lower()
                if "reject" in d: status = "Rejected"
                elif "shortlist" in d: status = "Shortlisted"
                elif "interview" in d: status = "Waitlist"
                
                # E. DB Save
                cid = add_candidate(
                    name=resume.filename, 
                    resume_text=resume_text, 
                    jd=jd_text, 
                    match_score=match_score,
                    matched_skills=found_list,
                    missing_skills=missing_list,
                    resume_evaluation=evaluation_result.model_dump(),
                    status=status,
                    recruiter_username=user
                )
                
                # E. Result Structure
                return {
                    "candidate_id": cid,
                    "filename": resume.filename,
                    "name": resume.filename,
                    "email": evaluation_result.extracted_evidence.education, # Using education field as proxy for 'summary' or N/A
                    "phone": "N/A",
                    "match_score": match_score,
                    "matched_skills": found_list,
                    "missing_skills": missing_list,
                    "reasoning": f"Decision: {evaluation_result.decision}",
                    "profile": evaluation_result.extracted_evidence.model_dump(),
                    "is_duplicate": False, # Skipped duplicate check for speed/simplicity in this refactor
                    "interview_context": {
                        "can_interview": evaluation_result.interview_required,
                        "prompt": f"Decision: {evaluation_result.decision}",
                        "payload": {
                            "resume_text": resume_text, 
                            "job_description": jd_text,
                            "match_score": match_score
                        }
                    }
                }
            except Exception as e:
                logger.error(f"Error processing {resume.filename}: {e}")
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

    if status == 'Shortlisted':
        background_tasks.add_task(send_shortlist_email, email, candidate['name'])
        update_candidate_status(cid, "Shortlist Sent")
        msg = "Shortlist 'Next Round' email queued."
    elif status == 'Rejected':
        background_tasks.add_task(send_rejection_email, email, candidate['name'])
        update_candidate_status(cid, "Reject Sent")
        msg = "Rejection email queued."
    else:
        # Waitlist or Default -> Send AI Interview Invite
        background_tasks.add_task(send_interview_invite, email, candidate['name'], cid)
        update_candidate_status(cid, "Invited")
        msg = "Interview invitation queued (Waitlist/Standard)."

    return {"message": msg}
