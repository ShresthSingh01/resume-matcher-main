# Resume Matcher & AI Interviewer - Project Documentation

## 1. Project Overview
**Resume Matcher & AI Interviewer** is an advanced recruitment automation platform designed to streamline the hiring process. It uses Large Language Models (LLMs) to intelligently parse resumes, match them against job descriptions, and conduct automated, voice-enabled technical interviews.

### Core Capabilities
- **Intelligent Resume Parsing**: key details (Skills, Experience, Education) are extracted using a hybrid approach (Regex + LLM).
- **Context-Aware Scoring**: Candidates are scored based on role-specific templates (Intern vs Senior), not just keyword matching.
- **AI-Driven Interviews**: Candidates meeting a specific threshold are invited to a real-time, voice-enabled technical interview conducted by an AI agent.
- **Anti-Cheating System**: Fullscreen enforcement, tab-switch monitoring, and webcam integration for interview integrity.
- **Automated Communication**: The system handles the entire email lifecycle—sending invites, rejection letters, or shortlist notifications automatically.

---

## 2. System Architecture

The application is built on a **FastAPI** backend with a **Vanilla JS** frontend, using **SQLite** for persistence and **LangChain** for orchestration.

```mermaid
graph TD
    Client[Client Browser] <-->|REST API / JSON| API[FastAPI Backend]
    
    subgraph "Backend Services"
        API <--> Auth[Auth Middleware]
        API <--> Matcher[Resume Matcher Engine]
        API <--> Interview[Interview Manager]
        API <--> Email[Email Service]
        API <--> Jobs[Adzuna Job Search]
    end
    
    subgraph "Data & AI"
        Matcher <--> DB[(SQLite Database)]
        Interview <--> DB
        Matcher <--> LLM[OpenAI / LangChain]
        Interview <--> LLM
        Interview <--> TTS[ElevenLabs API]
    end
```

### Technology Stack
- **Backend**: Python 3.10+, FastAPI, Pydantic
- **AI & LLM**: LangChain, OpenAI GPT-4o / GPT-3.5-Turbo
- **Database**: SQLite (NoSQL-style JSON storage for complex objects)
- **Frontend**: HTML5, CSS3 (Modern Dark Mode), Vanilla JavaScript
- **Voice/Audio**: ElevenLabs (TTS), Web Speech API (STT)

---

## 3. Intelligent Scoring & Logic

The system uses a **multi-stage scoring algorithm** to ensure high-quality candidate filtering.

### Stage 1: The Match Score (Resume vs JD)
Upon upload, the resume is compared to the Job Description (JD).
**Formula:**
$$ Final\ Match\ Score = (Skill\ Score \times 60\%) + (Semantic\ Score \times 40\%) $$

- **Skill Score**: Calculated by extracting skills from both documents and finding the intersection.
- **Semantic Score**: Uses vector embeddings (Cosine Similarity) to understand the "vibe" and implicit context match.

### Stage 2: Role-Based Evaluation
The system detects the role type (Intern, Junior, Senior) and applies a specific **template** to weight different aspects of the resume.

| Parameter | Intern Weight | Junior Weight | Senior Weight |
| :--- | :--- | :--- | :--- |
| **Education** | 25% | 15% | 5% |
| **Experience** | 10% | 25% | 40% |
| **Skills** | 30% | 30% | 35% |
| **Projects** | 25% | 20% | 15% |
| **Certifications** | 10% | 10% | 5% |

*Rationale:* Interns are judged potential (Education/Projects), while Seniors are judged on track record (Experience).

### Stage 3: The AI Interview Score
During the interview, every answer is graded on a scale of 0-10 based on relevance, technical accuracy, and depth.
$$ Interview\ Score = Average(Question\ Scores) \times 10 $$

### Stage 4: Final Candidate Score
The leaderboard ranks candidates by a composite score that favors valid interview performance.
**Formula:**
$$ Final\ Score = (Resume\ Match\ Score \times 40\%) + (Interview\ Score \times 60\%) $$

---

## 4. Workflows

### A. Recruitment Funnel (Recruiter View)
The automated workflow moves candidates through statuses based on their scores.

```mermaid
stateDiagram-v2
    [*] --> Upload : Recruiter uploads PDF
    Upload --> Parsing : Hybrid Extraction
    Parsing --> Scoring : Role-Based Eval
    
    state "Decision Logic" as Decision
    Scoring --> Decision
    
    Decision --> Shortlist : Score > 75
    Decision --> Waitlist : Score 50-75
    Decision --> Reject : Score < 50
    
    Waitlist --> Invite : Auto-Email Sent
    Invite --> Interview : Candidate takes AI Interview
    
    state "Interview Result" as Result
    Interview --> Result
    
    Result --> Shortlist : Final Score > 70
    Result --> Reject : Final Score < 70
```

### B. The Interview Loop (Candidate View)
The candidate experience is designed to mimic a real technical screen.

```mermaid
sequenceDiagram
    participant C as Candidate (Browser)
    participant S as Server
    participant AI as LLM (Interviewer)
    
    C->>S: Start Interview (Session ID)
    S->>C: Check Permissions (Cam/Mic)
    
    loop Question Cycle
        S->>AI: Generate Question (Context: Resume + History)
        AI->>S: "Tell me about your experience with X"
        S->>C: Question Text + Audio (TTS)
        C->>S: Spoken Answer (STT Text)
        S->>AI: Grade Answer (0-10)
        AI->>S: Score + Feedback
    end
    
    S->>C: Interview Complete
```

---

## 5. Key Features Detailed

### 🗣️ Text-to-Speech (TTS) Engine
- **Provider**: ElevenLabs (Primary), Browser Native (Fallback).
- **Voice Selection**: Automatically selects professional voices ('Adam', 'Josh', 'Rachel') if available.
- **Optimization**: Streams audio chunks for low latency.

### 🛡️ Anti-Cheating Suite
- **Visibility Detection**: The interview auto-terminates if the user switches tabs or minimizes the window.
- **Fullscreen Enforcement**: Candidates must remain in fullscreen mode.
- **Device Checks**: Mandatory webcam and microphone checks before starting.

### 📧 Email Notification Service
Powered by SMTP (Gmail), the system sends transactional emails based on status changes:
1.  **"Invited"**: Contains a unique link with a session token for the AI interview.
2.  **"Shortlisted"**: A congratulatory next-steps email.
3.  **"Rejected"**: A polite "thank you" email.

---

## 6. Database Schema (Schema Reference)

The system uses a relational model with JSON fields for flexibility.

**Table: `candidates`**
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Primary Key |
| `name` | TEXT | Extracted filename/name |
| `match_score` | REAL | Initial Resume Score |
| `status` | TEXT | Current State (Matched, Invited, Shortlisted) |
| `matched_skills` | JSON | List of skills found in resume AND JD |
| `flags` | JSON | List of integrity violations (tab switches) |

**Table: `interview_sessions`**
| Column | Type | Description |
| :--- | :--- | :--- |
| `session_id` | UUID | Primary Key (Linked to Candidate) |
| `scores` | JSON | Array of question-by-question grades |
| `current_question` | TEXT | State recovery for page reloads |

---

## 7. API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/upload` | POST | Uploads resumes and JD. Returns initial scores. |
| `/interview/start` | POST | Initializes a session. Returns the first question. |
| `/interview/answer` | POST | Submits an answer. Returns grading and next question. |
| `/interview/speak` | POST | Streams TTS audio for the given text. |
| `/invite/candidate/{id}` | POST | Triggers the email invite workflow. |
| `/interview/terminate` | POST | Ends interview due to cheating/violation. |
