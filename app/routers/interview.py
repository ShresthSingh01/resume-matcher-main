from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger
from app.schemas import StartInterviewRequest, InterviewAnswerRequest, InterviewResultRequest, FlagRequest
from app.db import get_candidate, get_active_session_by_candidate, flag_candidate, update_candidate_status
from app.interview_manager import interview_manager
from app.tts import TTSManager

router = APIRouter()
tts_manager = TTSManager()

@router.post("/interview/start")
async def start_interview(payload: StartInterviewRequest, request: Request):
    try:
        # Check for ACTIVE session logic (Singleton Device - Strict Cookie Lock)
        
        # Resolve candidate data first
        resume_text = payload.resume_text
        jd_text = payload.job_description
        match_score = payload.match_score

        if payload.candidate_id and (not resume_text or not jd_text):
            candidate = get_candidate(payload.candidate_id)
            if not candidate:
                 raise HTTPException(status_code=404, detail="Candidate not found.")
            
            # BLOCK RESTART LOGIC
            current_status = (candidate.get('status') or "").lower()
            
            # 1. Permanent Final States
            forbidden_statuses = ['shortlisted', 'rejected', 'terminated', 'completed']
            if any(s in current_status for s in forbidden_statuses):
                raise HTTPException(status_code=403, detail="Interview already completed or terminated.")

            # 2. Active State (Interviewing)
            # If they are "Interviewing", we ONLY allow entry if it's a valid Resume (Cookie Match).
            if "interviewing" in current_status or "active" in current_status:
                existing_session = get_active_session_by_candidate(payload.candidate_id)
                
                # If DB says active, check cookie
                if existing_session:
                    sid = existing_session['session_id']
                    client_cookie = request.cookies.get("interview_session")
                    
                    if client_cookie == sid:
                         # Valid Resume: Log and Fall through to existing_session logic below
                         logger.info(f"Resuming authorized session {sid}")
                    else:
                         # Invalid Resume: Block
                         logger.warning(f"Blocked unauthorized restart attempt for {sid}")
                         raise HTTPException(status_code=403, detail="Interview is already in progress. You cannot restart.")
                else:
                    # Status is Interviewing but no session found? 
                    # This implies a data inconsistency or manual DB edit. 
                    # Block to be safe, or allow if we assume status is stale?
                    # For strict security: Block.
                    raise HTTPException(status_code=403, detail="Interview status mismatch. Please contact support.")

            resume_text = candidate['resume_text']
            jd_text = candidate['job_description']
            match_score = candidate['match_score']

            existing_session = get_active_session_by_candidate(payload.candidate_id)
            if existing_session:
                sid = existing_session['session_id']
                # Check Cookie again (Redundant but safe)
                client_cookie = request.cookies.get("interview_session")
                
                if client_cookie == sid:
                    logger.info(f"Resuming active session {sid} (Cookie Match)")
                    session_obj = interview_manager.get_session(sid)
                    current_q = session_obj.current_question or "Welcome back. Let's continue."
                    
                    return JSONResponse(content={
                        "session_id": session_obj.session_id,
                        "role": session_obj.detected_role,
                        "question": current_q
                    })
                else:
                    # This should have been caught above, but double check
                    return JSONResponse(
                        status_code=403, 
                        content={"detail": "Access Denied: Interview is currently active on another device."}
                    )

        # Create New Session
        session = interview_manager.create_session(
            candidate_id=payload.candidate_id, 
            resume_text=resume_text, 
            jd=jd_text,
            match_score=match_score
        )
        
        if payload.candidate_id:
            update_candidate_status(payload.candidate_id, "Interviewing")
        
        question = interview_manager.start_interview(session.session_id)
        
        response = JSONResponse(content={
            "session_id": session.session_id,
            "role": session.detected_role,
            "question": question
        })
        
        # Set Lock Cookie (httponly for security, strict samesite)
        response.set_cookie(
            key="interview_session", 
            value=session.session_id, 
            httponly=True,
            samesite="lax" # Allow normal navigation
        )
        
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/interview/answer")
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

@router.post("/interview/result")
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
        logger.error(f"ERROR in /interview/result: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/interview/speak")
async def speak_text(payload: dict):
    text = payload.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    try:
        # If API Key is present, use ElevenLabs
        logger.debug("DEBUG: /interview/speak called")
        if tts_manager.client:
            logger.debug("DEBUG: Streaming audio from ElevenLabs...")
            return StreamingResponse(
                tts_manager.stream_audio(text),
                media_type="audio/mpeg"
            )
        else:
             logger.warning("DEBUG: TTS Manager has no client. Sending 503.")
             # Fallback signal for frontend to use Browser TTS
             return JSONResponse(status_code=503, content={"error": "TTS_DISABLED"})
    except Exception as e:
        logger.error(f"DEBUG: TTS Route Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/interview/flag")
async def flag_violation(req: FlagRequest):
    session = interview_manager.get_session(req.session_id)
    if not session or not session.candidate_id:
         # Log even if session not found? Safe to ignore for now
         return {"status": "ignored"}
    
    flag_candidate(session.candidate_id, req.reason)
    return {"status": "flagged"}

@router.post("/interview/terminate")
async def terminate_interview(req: FlagRequest):
    session = interview_manager.get_session(req.session_id)
    if not session or not session.candidate_id:
         return {"status": "ignored"}
    
    # 1. Flag
    flag_candidate(session.candidate_id, "TERMINATED: " + req.reason)
    # 2. Update Status to Terminated
    update_candidate_status(session.candidate_id, "Terminated")
    
    return {"status": "terminated"}
