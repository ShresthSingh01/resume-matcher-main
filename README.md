# 🧠 Virex AI - Intelligent Recruitment & Interview Platform

**Virex AI** is an enterprise-grade recruitment automation system designed to eliminate human bias and inefficiency from the hiring process. It replaces subjective resume screening with a **Deterministic Weighted Scoring Engine** and an **Autonomous AI Interviewer**, providing a complete end-to-end hiring pipeline.

---

## 📐 System Architecture

The system is built on a modern, scalable event-driven architecture:

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | `Next.js 14` (React) | Responsive Dashboard, Real-time Interview Interface, Leaderboard. |
| **Backend** | `FastAPI` (Python) | High-performance Async API, WebSocket management for real-time audio. |
| **AI Core** | `Google Gemini Pro` | The "Brain" for Resume Parsing, Matching, and Interview Context. |
| **Voice Engine** | `ElevenLabs` | Ultra-realistic Text-to-Speech (TTS) for the AI Interviewer. |
| **Database** | `SQLite` (SQLAlchemy) | Relational storage for Candidates, Recruiters, and Interview Sessions. |
| **Orchestrator** | `LangChain` | Manages LLM chains, structured outputs, and prompt engineering. |

---

## 🔄 System Workflow (Step-by-Step)

### 1. 📤 Intelligent Ingestion
*   **Action**: Recruiter uploads bulk resumes (PDF/DOCX) and inputs a Job Description (JD).
*   **Process**: The system uses `pypdf` + **LLM Parsing** to extract structured entities (Skills, Education, Experience) from even the messiest resume formats.

### 2. 🧠 Smart Resume Evaluation (The "Initial Filter")
Unlike simple keyword matchers, Virex uses a **Structured Likert-Scale Evaluation**:
the AI rates every candidate on **5 Dimensions (1-5 Scale)**:
1.  **Education**: (e.g., 5 = Top Tier/Masters, 1 = No Degree)
2.  **Experience**: (e.g., 5 = Senior Expert, 1 = Junior/None)
3.  **Skills**: (Semantic match against JD)
4.  **Projects**: (Complexity and relevance)
5.  **Certifications**: (Verified credentials)

**The Formula:**
$$ \text{Resume Score} = \sum (\text{Dimension Score} \times \text{Weight}) $$
*(Weights are dynamic based on role, e.g., Senior roles weight Experience 45%, Junior roles weight Skills 30%).*

### 3. ⚖️ Automated Decision Logic
Based on the Resume Score, the system strictly categorizes candidates:
*   **🔴 Rejected (< 60%)**: Candidate is filtered out.
*   **🟢 Shortlisted (>= 60%)**: Candidate is **Invited to AI Interview**.

### 4. 🤖 The AI Interview (The "Deep Dive")
Shortlisted candidates undergo a rigorous technical interview:
*   **Context Aware**: The AI reads the specific resume and JD to generate unique, challenging questions.
*   **Real-time Voice**: Interaction happens via voice (Speech-to-Text -> LLM -> Text-to-Speech).
*   **Anti-Cheating**: Full-screen enforcement, tab-switch detection, and object detection.

### 5. 🏆 The Final Leaderboard
Recruiters see a final ranked list sorted by a **Composite Score**:
$$ \text{Final Score} = (\text{Resume Score} \times 40\%) + (\text{Interview Score} \times 60\%) $$

### 6. ✅ Final Decision (Human-in-the-Loop)
For top candidates (Status: "Interviewed"), the recruiter has two explicit actions:
*   **Green Button ("Send Invite")**: Triggers the "Next Round" offer email.
*   **Red Button ("Reject")**: Triggers a polite data-driven rejection email.

---

## 🛡️ Security & Integrity

*   **Session Isolation**: Candidates cannot restart or retry interviews once completed.
*   **Input Blocking**: Copy/Paste/Right-Click disabled during tests.
*   **Role-Based Access**: Recruiters data is isolated; they cannot see each other's candidates.

---

## 🚀 Installation & Setup

### Prerequisites
*   Python 3.10+
*   Node.js 18+
*   Google Gemini API Key

### 1. Clone & Install
```bash
git clone https://github.com/your-repo/virex-ai.git
cd virex-ai

# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 2. Configure Environment (.env)
Create a `.env` file in the root:
```ini
GOOGLE_API_KEY=your_gemini_key
ELEVENLABS_API_KEY=your_voice_key
# Email Config (Optional)
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_password
```

### 3. Run the System
```bash
# Terminal 1: Backend
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

Access the Dashboard at: `http://localhost:3000`
