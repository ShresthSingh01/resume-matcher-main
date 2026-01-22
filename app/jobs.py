import asyncio
import json
import logging
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.db import get_db_session, add_candidate
from app.models.models import UploadJob
from app.resume_parser import parse_resume
from app.matcher import evaluate_resume_structured, detect_job_role, extract_required_skills, evaluate_resumes_bulk
from app.role_templates import get_role_template
from app.utils import clean_text

logger = logging.getLogger(__name__)

async def process_upload_job(
    job_id: str, 
    files_data: List[bytes], 
    filenames: List[str], 
    jd_text: str, 
    template_mode: str, 
    recruiter_username: str,
    resume_threshold: int = 50
):
    """
    Background task to process resumes.
    Refactored to process each resume INDIVIDUALLY with FULL TEXT context.
    """
    session = get_db_session()
    job = session.query(UploadJob).filter(UploadJob.job_id == job_id).first()
    
    if not job:
        logger.error(f"Job {job_id} not found starting processing.")
        session.close()
        return

    try:
        # Update status to processing
        job.status = "processing"
        job.total_files = len(files_data)
        session.commit()
        
        # --- Pre-computation Context ---
        detected_role = template_mode
        if template_mode == "auto":
             try:
                 detected_role = await detect_job_role(jd_text)
             except Exception:
                 detected_role = "Software Engineer"
        
        role_template, thresholds = get_role_template(detected_role)
        required_skills = await extract_required_skills(jd_text)
        
        # Parse resumes first
        parsed_resumes = []
        errors = []
        
        logger.info(f"Parsing {len(files_data)} files...")
        
        for i, (f_bytes, fname) in enumerate(zip(files_data, filenames)):
            try:
                text = parse_resume(f_bytes, fname)
                if text:
                    parsed_resumes.append({
                        "index": i,
                        "text": text,
                        "filename": fname
                    })
                else:
                    errors.append({"filename": fname, "error": "Empty text"})
            except Exception as e:
                errors.append({"filename": fname, "error": str(e)})

        logger.info(f"Evaluating {len(parsed_resumes)} resumes (Full Text Mode)...")
        with open("jobs_debug.log", "a", encoding="utf-8") as f:
             f.write(f"Received {len(files_data)} files.\n")
             f.write(f"Parsed {len(parsed_resumes)} resumes successfully.\n")
             if len(errors) > 0:
                 f.write(f"Parse Errors: {json.dumps(errors)}\n")
        
        # Bulk Evaluation (Optimized)
        BATCH_SIZE = 10
        valid_results = []
        
        for i in range(0, len(parsed_resumes), BATCH_SIZE):
            batch = parsed_resumes[i : i + BATCH_SIZE]
            logger.info(f"Processing Batch {i//BATCH_SIZE + 1} ({len(batch)} resumes)...")
            
            try:
                # evaluate_resumes_bulk returns list of {"index": idx, "output": ResumeEvaluationOutput}
                batch_results = await evaluate_resumes_bulk(
                    resumes=batch,
                    job_role=detected_role,
                    required_skills=required_skills,
                    role_template=role_template,
                    thresholds=thresholds
                )
                if batch_results:
                    valid_results.extend(batch_results)
            except Exception as e:
                logger.error(f"Batch {i//BATCH_SIZE + 1} failed: {e}")
                with open("jobs_debug.log", "a", encoding="utf-8") as f: f.write(f"❌ Batch Error: {e}\n")
                # Continue process other batches even if one fails
        
        # Save to DB
        results_list = []
        
        # Map back via index
        idx_map = {r["index"]: r for r in parsed_resumes}
        
        with open("jobs_debug.log", "a", encoding="utf-8") as f: 
            f.write(f"Saving {len(valid_results)} valid candidates to DB...\n")

        for res in valid_results:
            idx = res.get("index")
            output = res.get("output")
            source = idx_map.get(idx)
            
            if not source or not output: continue
            
            # Extract lists
            r_skills = set(s.lower() for s in output.extracted_evidence.skills)
            matched_list = [s for s in required_skills if s.lower() in r_skills]
            missing_list = [s for s in required_skills if s.lower() not in r_skills]
            
            # SCORING LOGIC
            interview_enabled = job.interview_enabled
            final_score = 0.0
            status = "Pending"
            
            if interview_enabled:
                # Conventional Flow: Wait for interview
                # Threshold for Shortlist: User Defined
                if output.weighted_resume_score >= resume_threshold:
                    status = "Shortlisted"
                else:
                    status = "Rejected"
                final_score = 0.0 # Will be calc after interview
            else:
                # Resume Only Flow: 100% Resume Score
                final_score = output.weighted_resume_score
                # Threshold for Selection: User Defined
                if final_score >= resume_threshold:
                    status = "Selected (Resume)"
                else:
                    status = "Rejected (Resume)"

            try:
                cid = add_candidate(
                    name=source["filename"],
                    resume_text=source["text"],
                    jd=jd_text,
                    match_score=output.weighted_resume_score,
                    matched_skills=matched_list,
                    missing_skills=missing_list,
                    resume_evaluation=output.model_dump(),
                    status=status,
                    recruiter_username=recruiter_username,
                    interview_enabled=interview_enabled,
                    final_score=final_score
                )
                results_list.append({"candidate_id": cid, "status": "success", "filename": source["filename"]})
                with open("jobs_debug.log", "a", encoding="utf-8") as f: f.write(f"✅ Saved candidate {cid} ({source['filename']})\n")
            except Exception as e:
                with open("jobs_debug.log", "a", encoding="utf-8") as f: f.write(f"❌ DB Save Error: {e}\n")

        # Append errors
        results_list.extend(errors)
        
        # Finalize Job
        job.processed_count = len(files_data)
        job.status = "completed"
        job.results = json.dumps(results_list)
        session.commit()
        logger.info(f"Job {job_id} Completed. {len(valid_results)} successes.")
        with open("jobs_debug.log", "a", encoding="utf-8") as f: f.write(f"Job {job_id} Completed.\n")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        with open("jobs_debug.log", "a", encoding="utf-8") as f: f.write(f"❌ CRITICAL JOB FAILURE: {e}\n")
        job.status = "failed"
        job.results = json.dumps({"error": str(e)})
        session.commit()
    finally:
        session.close()
