# 🧠 AI Resume Matcher & Virtual Interview System

A high-precision AI recruitment platform that automates the screening process. It combines **LLM-based Resume Analysis** with an **Adaptive Virtual Interview** to rank candidates based on a 70/30 weighted performance score.

---

## 🏗️ System Architecture & Workflow

The system operates in a linear, two-stage pipeline:

### Stage 1: Resume Matching (30% Weightage)
1.  **Ingestion & OCR**:
    *   Accepts `PDF` (Text/Scanned) or `TXT`.
    *   **Logic**: First tries `PyPDF2` for text layers. If empty/scanned, falls back to `PyMuPDF` + `EasyOCR` to read text from images.
    *   **Duplicate Check**: Uses `SentenceTransformers` (`all-MiniLM-L6-v2`) to generate a vector embedding of the resume. If this embedding has >90% cosine similarity with a previously processed resume, it flags a duplicate.
2.  **Full-Text Analysis**:
    *   Unlike traditional RAG systems that slice documents, we feed the **entire** resume text to the LLM.
    *   **Prompt Engineering**: A strict prompt enforces "No Hallucination" rules. It explicitly extracts "Present Skills" and "Missing Skills" based strictly on the provided Job Description (JD).
3.  **Match Scoring**:
    *   The system calculates a deterministic score:
        $$ Match Score = \frac{\text{Count(Matched Skills)}}{\text{Count(Matched Skills)} + \text{Count(Missing Skills)}} \times 100 $$

### Stage 2: AI Virtual Interview (70% Weightage)
1.  **Role Deduction**:
    *   The system analyzes the JD to automatically determine the interview persona (e.g., "Senior DevOps Engineer").
2.  **Adaptive Questioning**:
    *   **Q1**: Starts with a core role-based question or verifying a specific gap found in the resume.
    *   **Q2-Q5**: Adapts to the candidate's previous answers using a "Conversational Chain".
3.  **Real-Time Grading**:
    *   Every answer is evaluated by the LLM on a scale of 0-10 based on Technical Accuracy, Depth, and Clarity.
4.  **Final Scoring**:
    *   The system computes a weighted average for the final ranking:
        $$ Final Score = (Match Score \times 0.3) + (Interview Average \times 10 \times 0.7) $$

---

## 🛠️ Technology Stack

| Component | Library / Tool | Purpose |
| :--- | :--- | :--- |
| **Backend** | `FastAPI` | Asynchronous Python web server for high-throughput API handling. |
| **LLM Engine** | `LangChain` | Framework for managing prompt templates and LLM chains. |
| **Intelligence** | `OpenAI` / `OpenRouter` | GPT-4o-mini implies high reasoning capabilities for grading. |
| **OCR** | `EasyOCR`, `PyMuPDF` (fitz) | Extracts text from image-based/scanned PDFs. |
| **Embeddings** | `SentenceTransformers` | Generates vectors for duplicate detection. |
| **Vector Ops** | `scikit-learn` | Calculates Cosine Similarity for duplicates. |
| **Validation** | `Pydantic` | Data validation for API requests (Session models). |

---

## 🚀 Usage Guide

### 1. Interactive CLI (Recommended)
The easiest way to test the full flow without a frontend.

```bash
python start_interview.py
```
*   **Step 1**: Uploads `resume.pdf` & `jd.txt`.
*   **Step 2**: specific match score is shown.
*   **Step 3**: "Do you want to start the interview? (y/n)".
*   **Step 4**: Conducts a text-based interview in the terminal.
*   **Step 5**: Prints the final Weighted Score.

### 2. API Endpoints

**Base URL**: `http://127.0.0.1:8000`

#### `POST /upload`
Matches a resume against a JD.
*   **Input**: `resume` (File), `jd_file` (File) OR `job_description` (Text).
*   **Output**: JSON with `match_score`, `missing_skills`, and `interview_context`.

#### `POST /interview/start`
Starts a new interview session.
*   **Input**: `resume_text`, `job_description`, `match_score`.
*   **Output**: `session_id`, `role`, `question`.

## ✨ Core Features & Technical Workflow

### 1. Batch Resume Analysis (Rank & Match)
**User Workflow:**
1. Upload multiple PDF/TXT resumes + Job Description.
2. System processes all files and displays a **Leaderboard**.

**Technical Workflow:**
1.  **Extraction**: `PyPDF2` or `EasyOCR` extracts text from uploaded PDFs.
2.  **Vector Embedding**: `SentenceTransformer` converts text to vector embeddings for duplicate detection.
3.  **LLM Analysis**: Each resume is sent to the LLM (OpenAI/OpenRouter) with the JD.
    *   **Prompt**: Asks for direct skill comparison (Match/Missing).
4.  **Scoring**: Python logic calculates a match percentage based on matched vs total required skills.
5.  **Persistence**: Results are saved to a localized SQLite database (`candidates.db`).

### 2. Candidate Leaderboard (Database)
**User Workflow:**
1. View all past and current candidates ranked by score.
2. Filter status (Matched vs Interviewed).
3. "Clear All" to reset the database.

**Technical Workflow:**
1.  **Storage**: `app/db.py` manages a SQLite3 database with a `candidates` table.
2.  **Retrieval**: `GET /leaderboard` fetches structured data sorted by descending match score.
3.  **Action**: "Start Interview" button triggers the interview session linked to that specific candidate ID.

### 3. AI Interview Engine (TTS & STT)
**User Workflow:**
1.  Select a candidate > "Start Interview".
2.  Answer 5 technical/behavioral questions spoken by the AI.
3.  Receive a final "Interview Score".

**Technical Workflow:**
1.  **Session Init**: `InterviewManager` creates a session object, linking it to the candidate's Resume & JD context.
2.  **Question Generation**:
    *   **Round 1**: Validates core skills from the resume.
    *   **Round 2-5**: Adaptive questions based on previous answers (Chain-of-Thought).
3.  **Voice Interaction**:
    *   **Output**: Browser `SpeechSynthesis` (TTS) speaks the question.
    *   **Input**: Browser `webkitSpeechRecognition` (STT) converts user audio to text.
4.  **Grading**: After each answer, the LLM grades it (0-10) and checks for technical accuracy.

### 4. Comprehensive Career Report
**User Workflow:**
1.  After the interview, download a detailed `.txt` report.
2.  View specific "Focus Areas" and "Preferred Roles".

**Technical Workflow:**
1.  **Aggregation**: System compiles all Q&A pairs, scores, and feedback.
2.  **Final Analysis**: LLM reads the entire session transcript to generate high-level career advice.
3.  **Updates**: The final score is written back to the SQLite DB, updating the Leaderboard status.

---

## 🚀 How to Run

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup API Key**
   Create a `.env` file:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-...
   # or OPENAI_API_KEY=sk-...
   ```

3. **Run Server**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access UI**
   Open http://127.0.0.1:8000 in your browser.
