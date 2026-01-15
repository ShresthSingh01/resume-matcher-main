# 🧠 Virex AI - Intelligent Recruitment Platform

**Virex AI** is a next-generation recruitment platform designed to automate and enhance the hiring process. It bridges the gap between resume screening and technical interviewing using a powerful combination of LLM-based analysis and an adaptive AI interviewer.

---

## 🌟 Key Features

### 1. 🛡️ Secure Recruiter Dashboard
*   **Authentication**: Secure, cookie-based login for recruiters to protect sensitive candidate data.
*   **Batch Upload**: Drag-and-drop interface to process multiple PDF resumes simultaneously against a specific Job Description (JD).
*   **Leaderboard**: Real-time ranking of candidates based on a weighted "Final Score" (30% Resume Match + 70% Interview Performance).
*   **Detailed Analytics**: Interactive modal providing a deep dive into each candidate:
    *   **Skill Gap Analysis**: Visualizes "Matched" vs "Missing" skills.
    *   **Interview Transcript**: Full Q&A log with AI-generated feedback and scoring for every answer.
    *   **Downloadable Reports**: Generate offline text reports for team sharing.

### 2. 🤖 Adaptive AI Interviewer
*   **Context-Aware**: The AI reads the candidate's resume and the JD before the interview starts to tailor questions specifically to their background and the role.
*   **Dynamic Questioning**: Unlike static forms, the AI asks follow-up questions based on the candidate's actual responses, mimicking a real technical screener.
*   **Scoring Engine**: Evaluates every answer on a 0-10 scale for technical accuracy, clarity, and depth.

### 3. 📄 Smart Resume Parsing
*   **Hybrid OCR**: Uses `EasyOCR` and `PyMuPDF` to extract text from both digital and scanned PDFs.
*   **No-Hallucination Matching**: Strict prompt engineering ensures the AI only credits skills explicitly present in the resume.

### 4. 📊 Candidate Reporting
*   **Instant Feedback**: Candidates receive a summary of their performance immediately after the interview.
*   **Status Tracking**: Prevents candidates from re-taking completed interviews to ensure data integrity.

---

## 🛠️ Technology Stack

| Component | Technology | Usage |
| :--- | :--- | :--- |
| **Backend** | `FastAPI` (Python) | High-performance async web server handling API requests and business logic. |
| **Frontend** | `Vanilla JS` + `HTML5` | Lightweight, responsive UI with no build steps required. |
| **Styling** | `CSS3` (Neo-Brutalism) | Distinctive, high-contrast design system for a modern aesthetic. |
| **Database** | `SQLite` | Zero-configuration SQL engine for persisting candidate data and transcripts. |
| **AI / LLM** | `OpenAI GPT-4o-mini` | Powers the reasoning, resume analysis, and dynamic interviewing. |
| **Voice (TTS)** | `ElevenLabs` | (Optional) specialized text-to-speech for realistic voice interaction. |
| **Parsing** | `PyPDF2`, `EasyOCR` | Robust text extraction from diverse document formats. |

---

## 🚀 Workflow & Step-by-Step Guide

### 🧑‍💼 Recruiter Workflow

1.  **Login**: Access the dashboard at `/login` (Default credentials: `admin` / `admin123`).
2.  **Define Role**: Paste the Job Description (JD) into the text area.
3.  **Upload Resumes**: Select one or more PDF resumes and click **"Batch Analyze"**.
    *   *System Action*: Parses text, calculates "Match Score", and saves basic profiles to the database.
4.  **View Leaderboard**: Automatically redirects to the leaderboard showing all candidates ranked by score.
5.  **Invite Candidate**: Click **"Invite"** to generate a unique interview link for a candidate.
6.  **Review Performance**: Click **"View"** on a completed candidate to see:
    *   Final Score.
    *   Full Interview Transcript.
    *   Matched/Missing Skills.
7.  **Export**: Click **"Download Report"** inside the modal to save the full dossier as a `.txt` file.

### 🧑‍💻 Candidate Workflow

1.  **Start Interview**: Access the unique interview link provided by the recruiter.
2.  **System Check**: The AI introduces itself and confirms the candidate's readiness.
3.  **The Interview**:
    *   **Stage 1 (Introduction)**: Introduction and background check.
    *   **Stage 2 (Technical)**: Role-specific technical questions generated from the JD.
    *   **Stage 3 (Behavioral/Scenario)**: Problem-solving scenarios based on resume experience.
4.  **Completion**: The system calculates the final score and marks the profile as `Completed`.
5.  **Feedback**: The candidate sees a thank-you message and a partial summary (if enabled).

---

## ⚙️ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-repo/resume-matcher.git
    cd resume-matcher
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```ini
    OPENAI_API_KEY=sk-your-key-here
    ADMIN_USER=admin
    ADMIN_PASS=admin123
    # Optional
    ELEVENLABS_API_KEY=your-key-here
    ```

4.  **Run the Server**
    ```bash
    uvicorn app.main:app --reload
    ```

5.  **Access the App**
    *   **Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
    *   **API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)


