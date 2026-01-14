# Resume Matcher Main App
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import numpy as np
import re
from sklearn.metrics.pairwise import cosine_similarity
from app.skills import extract_skills
from app.job_providers.adzuna import search_jobs
from app.job_rankers import rank_jobs



from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import SecretStr
from app.models import StartInterviewRequest, InterviewAnswerRequest, InterviewResultRequest
from app.interview import InterviewManager

import os
from typing import List
from dotenv import load_dotenv
from typing import List
from dotenv import load_dotenv
from app.db import init_db, add_candidate, get_leaderboard, get_candidate, update_candidate_interview, clear_db

# Optional OCR dependencies
try:
    import easyocr
    import fitz  # PyMuPDF
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR dependencies (easyocr, pymupdf) not found. Image-based PDFs will be skipped.")

# Force load .env file, overriding system variables
load_dotenv(override=True)
# Trigger reload for env update

app = FastAPI(
    title="AI Resume Parser & JD Matcher",
    version="1.0.0"
)

# Initialize DB
init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

# ---------- Embeddings ----------

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

class SentenceTransformerEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return embedding_model.encode(texts).tolist()

    def embed_query(self, text):
        return embedding_model.encode([text])[0].tolist()

embeddings = SentenceTransformerEmbeddings()

# ---------- OCR Setup ----------
ocr_reader = None

def get_ocr_reader():
    global ocr_reader
    if not OCR_AVAILABLE:
        raise ImportError("OCR dependencies not installed.")
    
    if ocr_reader is None:
        print("⏳ Loading OCR Model (this may take a moment)...")
        ocr_reader = easyocr.Reader(['en']) 
        print("✅ OCR Model Loaded")
    return ocr_reader

# ---------- LLM Setup (OpenAI / OpenRouter) ----------

api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")

if api_key:
    print(f"🔌 Connecting to LLM: {model_name} at {base_url}")
    print(f"🔑 Using API Key: {api_key[:8]}...{api_key[-4:]}")
else:
    print("❌ Error: No API Key found (OPENROUTER_API_KEY or OPENAI_API_KEY).")

llm = ChatOpenAI(
    model=model_name,
    temperature=0,
    api_key=SecretStr(api_key) if api_key else None,
    base_url=base_url
)

# ---------- Interview Manager ----------
interview_manager = InterviewManager(llm)


prompt = PromptTemplate(
    input_variables=["context", "job_description"],
    template="""
You are an AI resume evaluation assistant.

RULES (DO NOT BREAK):
- Use ONLY the provided resume context.
- If a skill or requirement is NOT explicitly mentioned, say "Not found".
- Do NOT infer, guess, or assume.
- Do NOT add external knowledge.
- Do NOT rewrite the resume.

TASK:
Compare the resume context with the job description and explain:
1. Which required skills are clearly present
2. Which required skills are missing
3. A short factual explanation

OUTPUT FORMAT:
Present Skills: <comma_separated_list>
Missing Skills: <comma_separated_list>
Explanation: <text_explanation>

Resume Context:
{context}

Job Description:
{job_description}
"""
)

# ---------- In-memory duplicate storage ----------

stored_resume_embeddings = []

# ---------- Utilities ----------

def extract_text_from_resume(file):
    # Reset cursor just in case
    file.file.seek(0)

    # 1. Explicit Text Check (MIME or Extension)
    if file.content_type == "text/plain" or (file.filename and file.filename.lower().endswith(".txt")):
        return file.file.read().decode("utf-8", errors="ignore")

    # 2. Try PDF
    try:
        reader = PdfReader(file.file)
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
        
        # If extraction yielded little to no text, try OCR
        if not text.strip() and OCR_AVAILABLE:
            print("⚠️ No extracted text, attempting OCR...")
            file.file.seek(0)
            pdf_bytes = file.file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc:
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                results = get_ocr_reader().readtext(img_bytes, detail=0)
                text += " ".join(results) + "\n"
        
        if not text.strip() and not OCR_AVAILABLE:
             print("⚠️ OCR unavailable and no text found.")

        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        # 3. Fallback: If PDF fails, try reading as plain text (handling edge cases like 'application/octet-stream')
        file.file.seek(0)
        return file.file.read().decode("utf-8", errors="ignore")


def clean_text(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def chunk_text(text, size=300, overlap=50):
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def check_duplicate(embedding, threshold=0.9):
    if not stored_resume_embeddings:
        stored_resume_embeddings.append(embedding)
        return False, 0.0

    sims = cosine_similarity(np.array([embedding]), np.array(stored_resume_embeddings, dtype=np.float32))[0]
    max_sim = float(np.max(sims))

    if max_sim >= threshold:
        return True, max_sim

    stored_resume_embeddings.append(embedding)
    return False, max_sim


# ---------- API ----------

@app.post("/upload")
async def upload_resume_and_jd(
    resume: UploadFile = File(...),
    job_description: str = Form(None),
    jd_file: UploadFile = File(None)
):
    try:
        # 1. Extract Resume Text
        raw_resume = extract_text_from_resume(resume)
        cleaned_resume = clean_text(raw_resume)

        if not cleaned_resume:
             return JSONResponse(
                 status_code=400,
                 content={
                     "message": "Could not extract text from resume. It may be empty, corrupted, or an image-based/scanned PDF without selectable text."
                 }
             )

        # 2. Extract JD Text (From File OR Text Input)
        if jd_file:
            raw_jd = extract_text_from_resume(jd_file)
            cleaned_jd = clean_text(raw_jd)
        elif job_description:
            cleaned_jd = clean_text(job_description)
        else:
            return JSONResponse(
                status_code=400, 
                content={"message": "Please provide either a Job Description text OR upload a JD file."}
            )

        # ---------- Duplicate check ----------
        resume_embedding = embedding_model.encode([cleaned_resume])[0]
        check_duplicate(resume_embedding)

        # ---------- Optimization: Use Full Text (Fixes Missing Skills) ----------
        # Skipped partial chunking/RAG because it was missing relevant skills.
        context = cleaned_resume

        # ---------- LLM reasoning ----------
        chain = prompt | llm
        llm_output = chain.invoke({
            "context": context,
            "job_description": cleaned_jd
        })

        matched_skills, missing_skills, explanation = parse_llm_output(llm_output.content)
        match_score = calculate_match_score(matched_skills, missing_skills)

        return {
            "match_score": match_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "explanation": explanation,
            "explanation": explanation,
            "message": "Resume-job match analysis completed",
            "interview_context": {
                "can_interview": True,
                "prompt": "Based on this match, we recommend an AI Interview to finalize your ranking (70% weightage).",
                "payload": {
                    "resume_text": cleaned_resume,
                    "job_description": cleaned_jd,
                    "match_score": match_score
                }
            }
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ADD THESE FUNCTIONS BELOW EXISTING CODE (do not delete previous logic)

def parse_llm_output(llm_text):
    """
    Extract matched and missing skills from LLM output
    """
    matched_skills = []
    missing_skills = []
    explanation = ""

    if not isinstance(llm_text, str):
        llm_text = str(llm_text)
    
    lines = llm_text.split("\n")

    for line in lines:
        if "present skills" in line.lower():
            if ":" in line:
                matched_skills = [
                    skill.strip()
                    for skill in line.split(":")[1].split(",")
                    if skill.strip() and skill.strip().lower() not in ["not found", "none", "n/a"]
                ]
        elif "missing skills" in line.lower():
            if ":" in line:
                missing_skills = [
                    skill.strip()
                    for skill in line.split(":")[1].split(",")
                    if skill.strip() and skill.strip().lower() not in ["not found", "none", "n/a"]
                ]
        elif "explanation" in line.lower():
            parts = line.split(":", 1)
            if len(parts) > 1:
                explanation = parts[1].strip()
            else:
                explanation = line.replace("explanation", "", 1).strip()

    return matched_skills, missing_skills, explanation


def calculate_match_score(matched, missing):
    total = len(matched) + len(missing)
    if total == 0:
        return 0
    return round((len(matched) / total) * 100, 2)
@app.post("/match-resume")
async def match_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        # ---------- Extract & clean ----------
        raw_text = extract_text_from_resume(resume)
        cleaned_resume = clean_text(raw_text)

        if not cleaned_resume:
             return JSONResponse(
                 status_code=400,
                 content={
                     "message": "Could not extract text from resume. It may be empty, corrupted, or an image-based/scanned PDF without selectable text."
                 }
             )

        cleaned_jd = clean_text(job_description)

        # ---------- Duplicate check ----------
        resume_embedding = embedding_model.encode([cleaned_resume])[0]
        check_duplicate(resume_embedding)  # non-blocking

        # ---------- Optimization: Use Full Text (Fixes Missing Skills) ----------
        # Skipped partial chunking/RAG because it was missing relevant skills.
        context = cleaned_resume

        # ---------- LLM reasoning ----------
        chain = prompt | llm
        llm_response = chain.invoke({
            "context": context,
            "job_description": job_description
        })
        
        # DEBUG LOGGING (Added to trace inconsistencies)
        print(f"DEBUG: Extracted text length: {len(cleaned_resume)}")
        print(f"DEBUG: Text snippet: {cleaned_resume[:100]}...")
        print("DEBUG: Raw LLM Response:")
        print(llm_response.content)
        
        # ---------- Parse & score ----------
        matched, missing, explanation = parse_llm_output(llm_response.content)
        match_score = calculate_match_score(matched, missing)

        return {
            "match_score": match_score,
            "matched_skills": matched,
            "missing_skills": missing,
            "explanation": explanation,
            "interview_context": {
                "can_interview": True,
                "prompt": "Based on this match, we recommend an AI Interview to finalize your ranking (70% weightage).",
                "payload": {
                    "resume_text": cleaned_resume,
                    "job_description": cleaned_jd,
                    "match_score": match_score
                }
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "message": "An error occurred during resume matching."}
        )

@app.post("/batch-upload")
async def batch_upload(
    resumes: List[UploadFile] = File(...),
    job_description: str = Form(None),
    jd_file: UploadFile = File(None)
):
    try:
        # 1. Get JD Text
        if jd_file:
            raw_jd = extract_text_from_resume(jd_file)
            cleaned_jd = clean_text(raw_jd)
        elif job_description:
            cleaned_jd = clean_text(job_description)
        else:
            return JSONResponse(status_code=400, content={"message": "No JD provided."})

        results = []
        
        for resume in resumes:
            try:
                # Extract & Clean
                raw_text = extract_text_from_resume(resume)
                cleaned_resume = clean_text(raw_text)
                
                if not cleaned_resume:
                    continue
                    
                # LLM Match
                chain = prompt | llm
                llm_response = chain.invoke({
                    "context": cleaned_resume,
                    "job_description": cleaned_jd
                })
                
                matched, missing, explanation = parse_llm_output(llm_response.content)
                match_score = calculate_match_score(matched, missing)
                
                # Save to DB
                name = resume.filename if resume.filename else "Unknown Candidate"
                cid = add_candidate(name, cleaned_resume, cleaned_jd, match_score)
                
                results.append({
                    "id": cid,
                    "name": name,
                    "match_score": match_score,
                    "matched_skills": matched,
                    "missing_skills": missing
                })
                
            except Exception as e:
                print(f"Error processing {resume.filename}: {e}")
                continue

        print(f"DEBUG: Batch processing complete. Results: {len(results)}")
        return {"candidates": results}
    except Exception as e:
        print(f"CRITICAL ERROR in batch_upload: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/leaderboard")
async def leaderboard():
    return get_leaderboard()

@app.delete("/candidates")
async def clear_candidates():
    try:
        clear_db()
        return {"message": "All candidates cleared."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/interview/start")
async def start_interview(request: StartInterviewRequest):
    try:
        session = None
        
        # Check if this is a DB-backed start (flag: match_score == -1)
        if request.match_score == -1:
             print(f"DEBUG: Starting interview for Candidate ID: {request.resume_text}")
             candidate = get_candidate(request.resume_text) # Resume text holds the ID
             
             if not candidate:
                 print("DEBUG: Candidate not found in DB")
                 return JSONResponse(status_code=404, content={"message": "Candidate not found"})
             
             session = interview_manager.create_session(
                resume_text=candidate['resume_text'],
                jd=candidate['job_description'],
                match_score=candidate['match_score']
             )
             session.candidate_id = candidate['id'] # Link session to DB
        else:
            # Legacy/Single upload flow
            print("DEBUG: Starting interview for Single Session")
            session = interview_manager.create_session(
                resume_text=request.resume_text,
                jd=request.job_description,
                match_score=request.match_score
            )
            
        first_question = interview_manager.start_interview(session.session_id)
        
        return {
            "session_id": session.session_id,
            "role": session.detected_role,
            "message": "Interview started.",
            "question": first_question
        }
    except Exception as e:
        print(f"ERROR in start_interview: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/interview/answer")
async def submit_answer(request: InterviewAnswerRequest):
    try:
        next_question, is_finished, feedback, score = interview_manager.process_answer(
            session_id=request.session_id,
            answer=request.answer
        )
        
        return {
            "message": "Answer recorded.",
            "next_question": next_question,
            "is_finished": is_finished,
            "feedback": feedback,
            "score": score
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/interview/result")
async def get_interview_result(request: InterviewResultRequest):
    try:
        # 1️⃣ Calculate result ONCE
        result = interview_manager.calculate_final_result(request.session_id)
        if not result:
            return JSONResponse(
                status_code=404,
                content={"message": "Session not found"}
            )

        # 2️⃣ Fetch session
        session = interview_manager.get_session(request.session_id)

        # 3️⃣ Update DB if linked
        if session and hasattr(session, "candidate_id") and session.candidate_id:
            update_candidate_interview(
                session.candidate_id,
                result["interview_score"],
                result["final_score"],
                result["career_report"]
            )

        # 4️⃣ 🔥 JOB RECOMMENDATION LOGIC (ONLY IF REJECTED)
        REJECTION_THRESHOLD = 90

        if result["final_score"] < REJECTION_THRESHOLD:
            # Extract skills using AI
            skills = extract_skills(
                llm,
                session.resume_text,
                session.question_scores
            )

            # Search jobs
            jobs = search_jobs(skills)

            # Rank jobs
            ranked_jobs = rank_jobs(jobs, skills)

            # Attach to response
            result["job_recommendations"] = ranked_jobs[:5]
            result["status"] = "Rejected"
            print("FINAL SCORE:", result["final_score"])
            print("Extracted Skills:", skills)
            print("Jobs Found:", len(jobs))

        else:
            result["job_recommendations"] = []
            result["status"] = "Selected"

        return result

    except Exception as e:
        print("ERROR in /interview/result:", e)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
