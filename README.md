# 🧠 AI Resume Matcher & Virtual Interview System

A high-precision AI recruitment platform that automates the screening process. It combines **LLM-based Resume Analysis** with an **Adaptive Virtual Interview** to rank candidates based on a 70/30 weighted performance score.

---

## 🌟 Key Features & Evaluation

### 1. Smart Resume Parsing & Matching
*   **Summary**: uses a hybrid approach (`PyPDF2` + `EasyOCR`) to extract text from both standard and scanned PDFs. It employs `SentenceTransformers` to detect duplicate resumes via vector embeddings (>90% similarity). The core matching logic uses a strict LLM prompt to identify "Present" vs "Missing" skills against the Job Description.
*   **Evaluation**: **High Precision**. The "No Hallucination" prompt engineering ensures that only explicitly stated skills are counted. The duplicate detection effectively prevents redundant processing.

### 2. Adaptive AI Interviewer
*   **Summary**: Conducts a real-time, 5-question logic interview. It includes **Role Deduction** (automatically identifying the persona from the JD) and **Chain-of-Thought Questioning**, where each question adapts to the candidate's previous answer using `LangChain`.
*   **Evaluation**: **Dynamic & Context-Aware**. Unlike static scripts, the system digs deeper into a candidate's specific responses, mimicking a real technical screener.

### 3. Real-Time Job Recommendations (New) 🌍
*   **Summary**: Integrates with the **Adzuna API** to fetch live, location-specific job listings that match the candidate's identified role.
*   **Evaluation**: **Actionable Value**. Transforms the tool from a passive analyzer into an active career assistant, connecting candidates with real-world opportunities immediately.

### 4. Hybrid Text-to-Speech (TTS)
*   **Summary**: Features a dual-layer TTS engine. It attempts to use **ElevenLabs** for ultra-realistic voice streaming and falls back to standard browser-based speech synthesis if API limits are reached.
*   **Evaluation**: **Robust & Accessible**. Ensures the voice interface is always functional, prioritizing quality when available but guaranteeing usability.

### 5. Candidate Leaderboard & Analytics
*   **Summary**: A persistent SQLite database tracks every candidate's journey. It stores match scores, interview transcripts, and final weighted rankings (70% Interview / 30% Resume).
*   **Evaluation**: **Reliable State Management**. clearly visualizes the hiring pipeline, making it easy to compare candidates objectively.

---

## 🏗️ System Architecture & Workflow

The system operates in a linear, two-stage pipeline:

### Stage 1: Resume Matching (30% Weightage)
1.  **Ingestion & OCR**: Accepts `PDF` or `TXT`. Falls back to OCR for images.
2.  **Full-Text Analysis**: Feeds the entire resume to the LLM to extract skills contextually.
3.  **Match Scoring**:
    $$ Match Score = \frac{\text{Count(Matched Skills)}}{\text{Count(Matched Skills)} + \text{Count(Missing Skills)}} \times 100 $$

### Stage 2: AI Virtual Interview (70% Weightage)
1.  **Role Deduction**: Automatically determines the interview persona (e.g., "Senior DevOps Engineer").
2.  **Adaptive Questioning**: Q1 verifies resume gaps; Q2-Q5 adapt to the user's answers.
3.  **Real-Time Grading**: Every answer is scored (0-10) on Technical Accuracy and Clarity.
4.  **Final Scoring**:
    $$ Final Score = (Match Score \times 0.3) + (Interview Average \times 10 \times 0.7) $$

---

## 🛠️ Technology Stack

| Component | Library / Tool | Purpose |
| :--- | :--- | :--- |
| **Backend** | `FastAPI` | Asynchronous Python web server. |
| **LLM Engine** | `LangChain` | Prompt management and chains. |
| **Intelligence** | `OpenAI` / `OpenRouter` | Reasoning and grading. |
| **Job Data** | `Adzuna API` | Real-time job market listings. |
| **OCR** | `EasyOCR`, `PyMuPDF` | Scanned PDF text extraction. |
| **Embeddings** | `SentenceTransformers` | Vector similarity for duplicates. |
| **Database** | `SQLite3` | Local persistence for leaderboard. |

---

## 🚀 Usage Guide

### 1. Interactive CLI (Recommended)
The easiest way to test the full flow without a frontend.

```bash
python start_interview.py
```
*   **Step 1**: Uploads `resume.pdf` & `jd.txt`.
*   **Step 2**: Match analysis & Score.
*   **Step 3**: "Do you want to start the interview? (y/n)".
*   **Step 4**: Conducts a text-based interview.
*   **Step 5**: Prints final Weighted Score.

### 2. Web Interface (API)

**Base URL**: `http://127.0.0.1:8000`

#### `POST /upload`
Matches a resume against a JD.
*   **Input**: `resume` (File), `jd_file` (File) OR `job_description` (Text).
*   **Output**: JSON with `match_score`, `missing_skills`, and `interview_context`.

#### `POST /interview/start`
Starts a new interview session.
*   **Input**: `resume_text`, `job_description`, `match_score`.
*   **Output**: `session_id`, `role`, `question`.

#### `GET /jobs/recommend`
Fetches relevant job openings.
*   **Input**: `role` (str).
*   **Output**: List of job objects (title, company, url).

---

## 🚀 How to Run

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Web Application**
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
   Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

3. **CLI Mode (Optional)**
   ```bash
   python start_interview.py
   ```

