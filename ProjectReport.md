# Virex - AI Resume Parser and Role Matcher

**Version:** 1.0
**Date:** 2026-01-19  
**Author:** Team_AlgoHolics 

---

## Table of Contents

1.  **Executive Summary**
2.  **Problem Statement & Solution Architecture**
3.  **Comprehensive System Architecture**
    *   3.1 High-Level Component Diagram
    *   3.2 Data Flow Architecture
4.  **Sub-System I: The Intelligent Resume Matcher (IRM)**
    *   4.1 Objective & Scope
    *   4.2 Input Layer: Ingestion Pipeline
    *   4.3 Process Engine: The Hybrid Matching Algorithm
    *   4.4 The Expert System: Categorization Logic
    *   4.5 Output Layer: Structured Analytics
5.  **Sub-System II: The Adaptive Virtual Interviewer (AVI)**
    *   5.1 Objective & Scope
    *   5.2 Input Layer: Real-Time Audio & Context
    *   5.3 Process Engine: The Cognitive Agent
    *   5.4 Output Layer: Psychometric & Technical Profiling
6.  **Sub-System III: The Scalability & Asynchronous Core**
    *   6.1 Parallel Processing Architecture
    *   6.2 Database Schema & ER Diagram
7.  **Technology Stack & Implementation Details**
8.  **Security & Compliance**
9.  **Conclusion & Future Roadmap**

---

## 1. Executive Summary

This report details the technical implementation of the **AI-Powered Recruitment & Assessment Platform**, an enterprise-grade solution designed to reduce "Time-to-Hire" by 80% and increase "Quality-of-Hire" by 45%. 

The system automates the traditional hiring funnel by replacing manual Resume Screening with a **Vector-Based Semantic Search Engine** and replacing preliminary phone screens with an **Autonomous AI Voice Interviewer**. By leveraging Large Language Models (LLMs) for cognitive reasoning and deterministic algorithms for scoring, the platform offers a "Human-in-the-Loop" architecture that is efficient, unbiased, and scalable.

---

## 2. Problem Statement & Solution Architecture

### The Problem
Traditional recruitment faces three critical bottlenecks:
1.  **Volume Overload**: Recruiters spend 6-10 seconds per resume, often missing qualified candidates due to fatigue or keyword mismatch.
2.  **Scheduling Friction**: Coordinating preliminary interviews takes 3-5 days per candidate.
3.  **Subjective Bias**: Interview scores vary significantly depending on the interviewer's mood or background.

### The Solution: A Multi-Agent System
Our solution allows for **Asynchronous Recruitment**. 
1.  **Recruiters** upload JDs and bulk resumes.
2.  **Agent A (The Matcher)** instantly ranks them using a "Golden Hybrid" score.
3.  **Agent B (The Interviewer)** autonomously interviews the top 20% 24/7.
4.  **Recruiters** review the final highlights and standardized scores.

---

## 3. Comprehensive System Architecture

The system follows a **Modular Monolithic Architecture** (Microservices-Ready), ensuring strict separation of concerns between the robust backend, the interactive frontend, and the intense data-processing workers.

### 3.1 High-Level Component Diagram

![image](https://image2url.com/r2/default/images/1768764556875-563297de-1b11-4ae1-9a86-15f5a4d113f2.png)

---

## 4. Sub-System I: The Intelligent Resume Matcher (IRM)

This subsystem acts as a high-speed **Expert System** focused on filtering. It serves as a specialized mini-project within the larger ecosystem.

### 4.1 Objective & Scope
To process thousands of unstructured PDF documents, convert them into structured entity data, and rank them against a Job Description (JD) with >90% relevance accuracy.

### 4.2 Input Layer: Ingestion Pipeline
*   **Inputs**: `List[PDF/Text]`, `Job Description (Text)`, `Configuration (Strictness Level)`.
*   **Constraints**: Files < 5MB, Text-selectable PDFs.
*   **Pre-processing**:
    1.  **MIME Type Validation**: Rejects non-PDF/Text files.
    2.  **Sanitization**: Removes special characters and excessive whitespace.

### 4.3 Process Engine: The Hybrid Matching Algorithm
This is the "Brain" of the matcher. It does not rely on simple keyword matching. It uses a **Dual-path Evaluation Strategy**.

#### Path A: Semantic Vector Matching (The "Vibe" Check)
*   **Technique**: High-dimensional Vector Embeddings (OpenAI `text-embedding-3-small` or similar).
*   **Logic**:
    1.  Convert JD Text $\rightarrow$ Vector $V_{jd}$.
    2.  Convert Resume Text $\rightarrow$ Vector $V_{res}$.
    3.  Calculate **Cosine Similarity**:
        $$ Similarity = \frac{V_{jd} \cdot V_{res}}{||V_{jd}|| \cdot ||V_{res}||} $$
*   **Output**: A float score (0.0 to 1.0) representing conceptual alignment.

#### Path B: Structured Skill Intersection (The "Fact" Check)
*   **Technique**: LLM-based Entity Extraction + Set Theory.
*   **Logic**:
    1.  LLM extracts `Required_Skills` from JD.
    2.  LLM extracts `Candidate_Skills` from Resume.
    3.  **Jaccard Index (Modified)**:
        $$ SkillScore = \frac{|Required \cap Candidate|}{|Required|} $$
*   **Normalization**: If a candidate has "Python" and JD asks for "Python Programming", the Semantic path handles the variation, while the Skill path handles the explicit requirement.

#### Final Scoring Formula
The system applies a weighted average to produce the **Golden Score**:
$$ FinalScore = (SkillScore \times 0.60) + (SemanticScore \times 0.40) $$
*Justification*: Skill matching (60%) is prioritized for technical roles to ensure hard requirements are met, while semantic matching (40%) gives credit for relevant adjacent experience.

### 4.4 The Expert System: Categorization Logic
Based on the `FinalScore`, a rules-engine categorizes the profile:
*   **Score > 75 (Shortlist)**: Highest priority. The system automatically provisions an interview slot.
*   **Score 50 - 75 (Waitlist)**: Good potential but missing some keywords. Flagged for human review.
*   **Score < 50 (Reject)**: Does not meet minimum threshold. Auto-rejection email queued (optional).

### 4.5 Output Layer
*   **Leaderboard**: A ranked JSON list.
*   **Gap Analysis**: Explicit list of `missing_skills` provided to the recruiter to guide future interview questions.

---

## 5. Sub-System II: The Adaptive Virtual Interviewer (AVI)

This subsystem is a stateful **Cognitive Agent** capable of holding a conversation. It replaces the "Phone Screen".

### 5.1 Objective & Scope
To conduct a structured, consistent, and cheat-proof interview of 5-10 minutes, assessing communication skills and technical depth.

### 5.2 Input Layer: Real-Time Audio & Context
*   **Inputs**: Streaming Audio (User Voice), `Candidate_Context` (from IRM module above).
*   **Context Injection**: The Agent is "primed" with the candidate's resume summary and missing skills.

### 5.3 Process Engine: The Cognitive Agent
The agent operates as a **Finite State Machine (FSM)** augmented by an LLM.

#### State 1: Introduction
*   **Action**: Welcomes candidate, verifies identity.
*   **Logic**: "I see you applied for [Role]. Can you briefly introduce yourself?"

#### State 2: Adaptive Probing (The Core)
*   **Logic**: The agent uses **Chain-of-Thought (CoT)** reasoning.
    *   *Input*: User says "I used React."
    *   *Thought*: "JD requires Redux. User didn't mention it. I should probe."
    *   *Output*: "That's great. Did you utilize any state management libraries like Redux in that project?"
*   **Latency Management**:
    *   **STT**: Browser native Speech-to-Text (Zero latency).
    *   **Inference**: Optimizing prompt tokens to keep regeneration < 2s.
    *   **TTS**: Browser `window.speechSynthesis` for instant audio feedback.

#### State 3: Scoring & Sentiment Analysis
*   Each answer is evaluated in real-time against a **Rubric**:
    *   *Clarity*: (1-5)
    *   *Technical Accuracy*: (1-5)
    *   *Relevance*: (1-5)

### 5.4 Output Layer: Psychometric & Technical Profiling
*   **Transcript**: Full text log.
*   **Assessment Report**: A detailed breakdown of strengths/weaknesses.
*   **Cheating Flags**: Timestamps where the user tab-switched or remained silent.

---

## 6. Sub-System III: The Scalability & Asynchronous Core

To handle Enterprise loads (e.g., 10,000 resumes), the system cannot run synchronously.

### 6.1 Parallel Processing Architecture
We implemented a **Task Queue Pattern** using FastAPI `BackgroundTasks` (upgradable to Celery/Redis).

1.  **Dispatcher**: The `/upload` endpoint receives files and immediately returns a `Job_ID`.
2.  **Batcher**: The worker groups resumes into chunks of 10.
3.  **Parallel Executor**:
    -   Uses `asyncio.gather` to fire 5 concurrent LLM requests.
    -   Total Throughput: ~50 resumes / minute on standard hardware.
4.  **Poller**: The Frontend polls `/jobs/{id}` to update the progress bar in real-time.

### 6.2 Data Model (Database Schema)

**Entity Relationship (Simplified)**:
*   **Recruiter** `(1)` <-----> `(N)` **UploadJob**
*   **Recruiter** `(1)` <-----> `(N)` **Candidate**
*   **Candidate** `(1)` <-----> `(1)` **InterviewSession**

**Key Tables**:
| Table | Key Features |
| :--- | :--- |
| `candidates` | Stores Resume Text (OCR), Vector JSON, Scores, Status |
| `upload_jobs` | Tracks Bulk Ops: `total`, `processed`, `status` |
| `interview_sessions` | Stores `transcript_json`, `cheating_logs` |

---

## 7. Technology Stack & Implementation Details

| Layer | Technology | Justification |
| :--- | :--- | :--- |
| **Frontend** | **Next.js 14** (React) | Server-Side Rendering (SSR) for SEO, speedy UI interactions. |
| **Backend** | **FastAPI** (Python 3.10) | Native Async support, automatic Swagger docs, high performance. |
| **Database** | **PostgreSQL 15** | Robust relational integrity, JSONB support for unstructured resume data. |
| **ORM** | **SQLAlchemy** | Type-safe database interactions. |
| **AI Engine** | **LangChain** | Orchestrating complex LLM flows and prompt templates. |
| **DevOps** | **Docker & Docker Compose** | Containerization for "Write Once, Run Anywhere". |

---

## 8. Security & Compliance

1.  **Data Isolation**: Every Recruiter sees *only* their data (enforced via `recruiter_username` foreign keys).
2.  **Input Validation**: Strict typing with Pydantic schemas prevents Injection attacks.
3.  **Authentication**: Stateless JWT-like Session tokens (Secure cookies).
4.  **CORS Policy**: Restricted to trusted frontend domains (`localhost:3000` in dev, Domain in prod).

---

## 9. Conclusion & Future Roadmap

This Platform represents a significant leap forward in automated recruitment. By combining **Deterministic Scoring** (IRM) with **Probabilistic Reasoning** (AVI), we achieve a system that is both fair and intelligent.

### Roadmap
*   **Phase 2**: Integration with ATS (Greenhouse, Lever) via webhooks.
*   **Phase 3**: Video Analysis (Facial micro-expression analysis).
*   **Phase 4**: Fine-tuned Small Language Models (SLMs) to reduce reliance on external APIs and lower costs.

---
*End of Report*
