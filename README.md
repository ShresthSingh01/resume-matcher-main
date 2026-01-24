# 🧠 Virex AI: Next-Gen Intelligent Recruitment System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-teal?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **"Transforming Recruitment from a Manual Process into a Data-Driven Science."**

**Virex AI** is an enterprise-grade, autonomous recruitment platform designed to eliminate human bias and operational bottlenecks. By unifying **LLM-based Resume Parsing** with an **Autonomous Voice-AI Interviewer**, Virex creates a seamless, end-to-end hiring pipeline that operates with zero-trust integrity.

---

## 📑 Table of Contents
- [Executive Summary](#-executive-summary)
- [System Architecture](#-system-architecture)
- [Detailed Subsystems](#-detailed-subsystems)
  - [I. Intelligent Resume Matcher (IRM)](#i-intelligent-resume-matcher-irm)
  - [II. Adaptive Virtual Interviewer (AVI)](#ii-adaptive-virtual-interviewer-avi)
  - [III. Scalability & Core](#iii-scalability--core)
- [Technology Stack](#-technology-stack)
- [Security & Anti-Cheating](#-security--anti-cheating)
- [Installation & Setup](#-installation--setup)

---

## 🚀 Executive Summary

Traditional recruitment is plagued by high volumes, unconscious bias, and scheduling inefficiencies. Virex AI solves this by introducing a **"Digital Recruiter"** that handles the heavy lifting:

1.  **Smart Screening**: Instantly parses and scores thousands of resumes against a JD using a 5-point Likert scale.
2.  **Autonomous Interviewing**: Conducts real-time, voice-based technical interviews with shortlisted candidates.
3.  **Deterministic Scoring**: Calculates a final weighted score (40% Resume + 60% Interview) to rank candidates objectively.

---

## 📐 System Architecture

The system operates on a strictly defined **3-Phase Workflow**:

![image](https://image2url.com/r2/default/images/1769268298988-e1b269bd-1a43-4745-a756-1c6ae79ebc1b.png)
### Data Flow
1.  **Ingestion**: Resume PDF $\rightarrow$ Text Extraction $\rightarrow$ LLM Template Mapping $\rightarrow$ Initial Score.
2.  **Interview**: Voice Audio $\rightarrow$ STT $\rightarrow$ LLM Context Engine $\rightarrow$ TTS $\rightarrow$ Browser Audio.
3.  **State**: Redis manages active "Session State" for <10ms latency updates.

---

## 🔍 Detailed Subsystems

### I. Intelligent Resume Matcher (IRM)
The **IRM** goes beyond keyword matching. It uses Large Language Models to extract a **Structured Candidate Profile** and evaluates it on a strict **5-Point Likert Scale**.

#### Evaluation Dimensions:
*   **Education**: Quality and relevance of degree (1-5).
*   **Experience**: Years of experience vs. seniority required (1-5).
*   **Skills**: Semantic match of hard/soft skills (1-5).
*   **Projects**: Complexity and real-world applicability (1-5).
*   **Certifications**: Verified credentials (1-5).

> **Formula**: $\text{Resume Score} = \sum (\text{Dimension Score} \times \text{Role Weight})$
> *Weights are dynamic based on the Role Template (e.g., Senior dev roles weight Experience higher).*

### II. Adaptive Virtual Interviewer (AVI)
The **AVI** acts as a technical proxy, validating that candidates *actually* know what they claim.

#### The Cognitive Loop (Listen-Think-Speak):
1.  **Input**: Captures candidate audio via Web Speech API.
2.  **Reasoning**: LLM generates a context-aware question based on the **Resume + JD + Previous Answer**.
3.  **Grading**: A separate "Grader Agent" scores the answer (0-10) for technical accuracy.
4.  **Output**: Ultra-realistic voice response via **ElevenLabs**.

### III. Scalability & Core
Built for enterprise loads (500+ concurrent users):
*   **Asynchronous Workers**: Background threads handle heavy PDF parsing without blocking the UI.
*   **Redis Hot-State**: Manages live interview sessions to ensure context isn't lost during connection drops.
*   **Database**: SQLite (dev) / PostgreSQL (prod) with strict Foreign Key constraints for integrity.

---

## 💻 Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | **Next.js 14** (TypeScript) | App Router, Server Components, TailwindCSS. |
| **Backend** | **FastAPI** (Python 3.10) | Async REST API, WebSockets for audio streaming. |
| **AI Brain** | **LangChain + Gemini Pro** | Orchestration of reasoning chains and prompt management. |
| **Voice** | **ElevenLabs + Web Speech API** | Low-latency Text-to-Speech (TTS) and Speech-to-Text (STT). |
| **Database** | **SQLAlchemy + Redis** | Relational data persistence and in-memory caching. |

---

## 🛡 Security & Anti-Cheating

Virex implements a **Zero-Trust Exam Environment** during interviews:

*   **Fullscreen Enforcement**: Exiting fullscreen triggers an immediate flag.
*   **Tab Focus Monitoring**: Switching tabs or minimizing the browser is detected.
*   **3-Strike Policy**:
    *   **1 Flag**: Warning issued (Score Impact: -20%).
    *   **2 Flags**: **Session Terminated** (Score = 0).
*   **Device Lock**: Unique session cookies prevent sharing interview links.

---

## 🛠 Installation & Setup

### Prerequisites
*   **Python** 3.10+
*   **Node.js** 18+
*   **Redis** (Optional, falls back to memory)

### 1. Clone the Repository
```bash
git clone https://github.com/Start-Virex-AI/virex-core.git
cd virex-core
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup Environment Variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY and ELEVENLABS_API_KEY

# Run Server
uvicorn app.main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run Development Server
npm run dev
```

Visit the dashboard at `http://localhost:3000`.

---

## 🔮 Future Roadmap (v2.0)
- [ ] **Code Execution Sandbox**: Live coding environment for developer roles.
- [ ] **Multimodal Analysis**: Video-based emotion and confidence scoring.
- [ ] **ATS Integration**: Direct connect to Greenhouse/Workday.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
