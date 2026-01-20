# 🧠 Virex AI - Intelligent Recruitment & Interview Platform

**Virex AI** is a comprehensive recruitment automation system that standardizes the hiring process. It replaces subjective resume screening with a deterministic, template-based evaluation engine and an adaptive AI interviewer.

## 🌟 Key Features

## 🌟 Key Features & Scoring Logic

### 1. 🔍 Structured "Virex" Resume Evaluation
Unlike simple keyword matching, Virex uses a **Deterministic Weighted Scoring Engine** enhanced by **Precision Skill Validation**.
*   **Exact-Match Extraction**: The system uses strict regex boundaries to validate skills, ensuring no false positives (e.g., correctly distinguishing "Java" from "JavaScript" or "C" from "C++").

#### **A. The Likert Scale (1-5)**
Every parameter (Education, Experience, Skills, Projects, Certifications) is evaluated on a strict 1-5 scale:
*   **1 (Poor)**: No evidence found or largely irrelevant.
*   **2 (Fair)**: Minimal match, potential gaps, or only adjacent skills present.
*   **3 (Good)**: Meets the core requirements of the Job Description.
*   **4 (Very Good)**: Exceeds requirements, strong evidence of expertise.
*   **5 (Exceptional)**: Perfect match, demonstrates leadership or elite achievements.

#### **B. Role-Specific Weighting**
A "3/5" in Experience matters more for a Senior dev than an Intern. We apply purely mathematical weights:

| Parameter | 🎓 Intern/Fresher | 👨‍💻 Junior/Mid | 🚀 Senior/Lead |
| :--- | :---: | :---: | :---: |
| **Education** | **35%** | 20% | 10% |
| **Experience** | 5% | **25%** | **45%** |
| **Skills** | **25%** | **30%** | 30% |
| **Projects** | **25%** | 15% | 5% |
| **Certs** | 10% | 10% | 10% |

**Resume Score Calculation**:
`Resume Score = (Sum(Parameter Score × Weight)) × 20` _(Normalized to 0-100)_

### 2. ⚡ Automated Decision Workflow
The system buckets candidates based on their Resume Score, dynamically updating the **"Action Button"** on the dashboard:
*   **🟢 Shortlisted (Score > 75%)**: High probability of hire. Button: **"Next Round"** (Triggers onboarding/final interview).
*   **🟠 Waitlisted (Score 45-75%)**: Good profile but missing signals. Button: **"Invite to Interview"** (Sends AI Interview link).
*   **🔴 Rejected (Score < 45%)**: Does not meet criteria. Button: **"Send Rejection"** (Triggers polite decline email).

### 3. 🤖 Adaptive AI Interviewer & Final Scoring
Candidates on the waitlist can "earn" a shortlist spot through the AI Interview.

#### **A. Interview Grading (0-10 Scale)**
The AI evaluates every answer in real-time based on:
1.  **Technical Correctness**: Is the answer factually right?
2.  **Depth**: Did they explain *how* and *why*, or just recite definitions?
3.  **Clarity**: Communication style and detailed examples.

#### **B. The "Promotion" Algorithm**
We calculate a **Final Score** to decide if a candidate should be upgraded from Waitlist to Shortlist.
*   **Formula**: `Final Score = (Resume Score × 0.4) + (Interview Score × 0.6)`
*   *Why?* We give **60% weight** to the interview. A candidate with a weak resume (e.g., non-traditional background) can still win the job if they perform exceptionally (9/10) in the technical interview.

**Threshold**: If `Final Score >= 70`, the candidate is **Automatically Promoted** to **🟢 Shortlisted**.

### 4. 🛡️ Anti-Cheating & Security Suite
Virex implements a robust **"3-Ring Defense"** strategy to ensure interview integrity:

#### **Ring 1: Browser Lockdown**
*   **Fullscreen Enforcement**: Candidates must remain in fullscreen. Exiting triggers a visible "Proctoring Alert".
*   **Focus Tracking**: Switching tabs or minimizing the window is detected as a violation.
*   **Input Blocking**: Right-click, Copy, Cut, and Paste actions are disabled to prevent copying questions.

#### **Ring 2: Secondary Device Countermeasures**
*   **Strict Tymer**: Questions have a tight **40-second limit** to minimize "lookup time".
*   **Unselectable Text**: Question text cannot be highlighted, preventing easy OCR scanning.

#### **Ring 3: Behavioral Monitoring & Backend Flagging**
*   **Webcam Presence**: Live "Self-Audit" webcam feed displayed on screen.
*   **Typing Heuristics**: Detects "Superhuman" typing speeds (instant text injection) and blocks the input.
*   **Persistent Flagging**: All violations are logged in the database.
*   **3-Strike Termination**: Upon the 3rd violation, the interview is **Terminated immediately**.

#### **🔒 Permanent Lockout**
To prevent gaming the system, candidates with the following statuses are **permanently blocked** from restarting or retaking the interview:
*   `Shortlisted`, `Rejected`, `Terminated`, `Completed`.

### 5. 🔐 Multi-User Secure Workspace
Designed for collaborative teams, Virex ensures data privacy and efficient workflow management:
*   **Data Isolation**: Every candidate profile is strictly tagged with the uploader's `recruiter_username`. Recruiters only access the talent pool they source.
*   **Private Leaderboards**: Your hiring funnel and candidate rankings are isolated, ensuring no data leakage between recruiter accounts.

## 📚 Documentation
For a comprehensive deep dive into the system logic, detailed verification workflows, and architectural diagrams, please refer to the **[Project Documentation](PROJECT_DOCUMENTATION.md)**.


---

## 📐 System Architecture & Process Flow

[![image](https://image2url.com/r2/default/images/1768766096030-15277cf5-622b-4e68-809c-a883386b0260.png)]({url})


---

## 🛠️ Technology Stack

| Component | Technology | Usage |
| :--- | :--- | :--- |
| **Backend** | `FastAPI` (Python) | Async web server, handling parallel LLM requests and WebSocket-like flows. |
| **Evaluation** | `LangChain` + `Pydantic` | Structured output parsing for strict JSON data enforcement. |
| **Frontend** | `Next.js` (React) + `TypeScript` | Responsive, component-based UI with Server Side Rendering. |
| **Database** | `SQLite` | Persistent storage for Candidates, Sessions, and Transcripts. |
| **AI Models** | `GPT-4o-mini` | Powers the reasoning, resume parsing, and interview generation. |
| **TTS (Voice)** | `ElevenLabs` / Browser | Text-to-Speech for realistic interview experience. |

---

## 🚀 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-repo/virex-ai.git
    cd virex-ai
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    Create a `.env` file:
    ```ini
    OPENAI_API_KEY=sk-your-key
    OPENROUTER_API_KEY=sk-your-openrouter-key
    # Optional for Email
    SMTP_USERNAME=your-email@gmail.com
    SMTP_PASSWORD=your-app-password
    ```

4.  **Run the Server**
    ```bash
    uvicorn app.main:app --reload
    ```

5.  **Access the Dashboard**
    *   Login: `admin` / `admin123`
    *   URL: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### 6. 🐳 Run with Docker

Easily spin up the entire stack (Frontend + Backend + Database) using Docker.

1.  **Ensure Docker is Installed**
    Make sure you have Docker Desktop (Windows/Mac) or Docker Engine (Linux) installed and running.

2.  **Build and Run**
    ```bash
    docker compose up --build
    ```

3.  **Access the App**
    *   **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)
    *   **Database**: Accessible on port `5432`

### 7. 🌍 Global Access (Mobile / Public Internet)
To access the interview session from a mobile device or a different network (Waitlisted Candidates), use the automated **Global Launcher**:

1.  **Prerequisites**:
    *   Download [ngrok](https://ngrok.com/download) and place `ngrok.exe` in the project root.
    *   Add your auth token: `.\ngrok config add-authtoken <YOUR_TOKEN>`

2.  **Run the One-Click Script**:
    ```powershell
    .\start_global.ps1
    ```
    *   This will automatically:
        *   Start secure tunnels for both Frontend & Backend.
        *   Update your `.env` file with the public URLs.
        *   Launch the Docker application.
    *   **Share the Public Frontend URL** with candidates to allow them to take the interview from anywhere.

