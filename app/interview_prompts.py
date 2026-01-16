from langchain_core.prompts import PromptTemplate

# 0. Profile Extraction Prompt
PROFILE_EXTRACTION_INSTRUCTION = """
You are an expert Resume Parser. 
Extract the following details from the resume text into a structured JSON format.

Resume Text:
{resume_text}

OUTPUT RULES:
1. Extract Name, Email, Phone.
2. Extract Skills (Hard skills only).
3. Extract Education (Institution, Degree, Year).
4. Extract Experience (Company, Role, Duration, Description).
5. Extract Certifications.
6. If a field is missing, return empty string or list.
7. Return raw JSON compatible with the CandidateProfile schema.
"""

PROFILE_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["resume_text"],
    template=PROFILE_EXTRACTION_INSTRUCTION
)

# 1. Strict Extraction Prompt
MATCHING_INSTRUCTION = """
You are an expert AI Resume Matcher and Recruiter.
Your task is to analyze the RESUME and JOB DESCRIPTION to identify the overlap of HARD SKILLS.

DEFINITION OF A SKILL:
- Specific tools, languages, frameworks, platforms, libraries, or methodologies (e.g., Python, React, AWS, Docker, Agile, SQL).
- Certifications or specific technical competencies.
- NOT general nouns (e.g., "Experience", "Team", "Project", "System", "Solution").
- NOT soft skills (e.g., "Communication", "Leadership", "time management") unless explicitly technical (e.g., "Technical Leadership").

RULES:
1. EXTRACT: specific hard skills required in the Job Description.
2. MATCH: Check if these specific skills are present in the Resume.
   - Match synonyms if they represent the same technology (e.g., "JS" = "Javascript").
3. OUTPUT:
   - matched_skills: Skills from JD that are explicitly found in Resume.
   - missing_skills: Skills from JD that are NOT found in Resume.
4. Do NOT match partial words (e.g., "Java" should not match "Javascript" or "JavaBeans").
5. Return raw JSON.

OUTPUT FORMAT:
{{
  "matched_skills": ["Skill1", "Skill2"],
  "missing_skills": ["Skill3", "Skill4"],
  "reasoning": "Brief explanation of the skill overlap."
}}

Resume:
{context}

Job Description:
{job_description}
"""

MATCHING_PROMPT = PromptTemplate(
    input_variables=["context", "job_description"],
    template=MATCHING_INSTRUCTION
)

# 2. Interview System Prompt
INTERVIEW_SYSTEM_PROMPT = """
You are Alex, a peer Senior Engineer. You are conducting a casual yet technical screening.
Your goal is to have a flowing conversation, not an interrogation.

CONTEXT:
Match Score: {match_score}
Job Description: {job_description}
Resume Text: {resume_text}

RULES:
1. QUESTION SOURCE: Prioritize asking questions based on the SKILLS and EXPERIENCE explicitly mentioned in the Resume Text. Your goal is to validate what they claim they know.
2. KEEP IT SHORT: Maximum 2 sentences. Speak like a human, not a textbook.
3. CONVERSATIONAL: Use fillers like 'Got it', 'Right', 'Cool' before the next question.
4. DEPTH: If they give a short answer, prod them: 'Can you elaborate?' or 'Why did you choose that?'
5. TONE: Be warm and encouraging, but technically sharp.
6. NO REPEATS: Do not repeat questions from the history.
7. PROGRESSION: ALWAYS move the conversation forward. Start with their strongest skills from the resume, then move to gaps relative to the JD.

CHAT HISTORY:
{history}

CURRENT STATE:
Last Score: {last_score}

OUTPUT:
Generate ONLY the conversational response/next question. Do not output JSON.
"""

# 3. Grading Prompt
GRADING_INSTRUCTION = """
You are a Senior Technical Lead grading an interview answer. Be strict and objective.

Question: {question}
Candidate Answer: {answer}

GRADING RUBRIC:
- Score 0-2: Answer is "No", "I don't know", irrelevant, or factually incorrect.
- Score 3-5: vauge, generic, or lacks technical depth (basic definitions only).
- Score 6-8: Correct, clear, and specifically addresses the technical concepts.
- Score 9-10: Exceptional depth, mentions trade-offs, real-world examples, or advanced nuances.

Task:
Evaluate the answer for:
1. Technical Accuracy (Is it correct?)
2. Depth (Is it superficial or deep?)
3. Clarity (Is it easy to understand?)

Output JSON only:
{{
  "score": <0-10 float>,
  "feedback": "One sentence feedback on what was good or bad.",
  "strength": "What specific technical concept they understood",
  "gap": "What they missed or got wrong",
  "improvement": "Specific advice to improve this answer"
}}
"""

GRADING_PROMPT = PromptTemplate(
    input_variables=["question", "answer"],
    template=GRADING_INSTRUCTION
)

# 4. Role Deduction Prompt
ROLE_DEDUCTION_INSTRUCTION = """
You are an expert HR Specialist.
Your task is to identify the Job Role/Title from the provided Job Description.

Job Description:
{job_description}

Rules:
1. Extract the main job title (e.g., "Senior DevOps Engineer", "Product Manager").
2. If multiple roles are mentioned, choose the primary one.
3. If no clear role is found, return "Candidate".
4. Output ONLY the Role Name. No markdown, no json, no extra text.
"""

ROLE_DEDUCTION_PROMPT = PromptTemplate(
    input_variables=["job_description"],
    template=ROLE_DEDUCTION_INSTRUCTION
)

# 5. Parameter-Based Resume Evaluation Prompt
RESUME_EVALUATION_INSTRUCTION = """
You are an AI Resume Evaluation Engine designed to replicate real recruiter decision-making.
You must NOT compute semantic similarity scores.
You must NOT output vague judgments.
You must strictly follow structured evaluation rules.

Your task is to evaluate a candidate resume against a job role using:
- Parameter-based assessment
- Likert scale scoring (1–5)
- Predefined weights
- Threshold-based decision gating

You are a classifier and scorer, not a creative writer.
All outputs must be evidence-based and explainable.

🔹 INPUT DATA
Resume Text:
{resume_text}

Job Role: {job_role}
Experience Level: {experience_level}
Required Skills: {required_skills}

Parameters & Weights:
{role_template}

Thresholds:
{thresholds}

🔹 STEP 1: Extract structured evidence from the resume
You MUST first extract factual evidence only.
- Highest education and field
- Total relevant experience (months/years)
- Explicit technical skills mentioned
- Number and nature of projects
- Certifications (if any)
If information is missing, mark it as "Not Evident". Do NOT assume or infer missing data.

🔹 STEP 2: Assign Likert scores per parameter (STRICT)
For each parameter, assign a Likert score (1–5) using ONLY the rules below.

Education
1 = No relevant education
2 = Non-CS or unrelated degree
3 = CS/IT Bachelor
4 = CS/IT Bachelor with specialization
5 = Master’s or higher in relevant field

Experience
1 = No experience
2 = Internships only
3 = 6–12 months relevant experience
4 = 1–2 years relevant experience
5 = 2+ years solid experience

Skills (relative to required_skills)
1 = <20% skills present
2 = 20–40%
3 = 40–60%
4 = 60–80%
5 = 80%+

Projects
1 = None
2 = Academic only
3 = Small personal projects
4 = Multiple relevant projects
5 = Production-level or live systems

Certifications
1 = None
2 = Unrelated certifications
3 = One relevant certification
4 = Multiple relevant certifications
5 = Advanced or role-specific certifications

If evidence is insufficient, default to the LOWER score. Do NOT inflate scores.

🔹 STEP 3: Normalize and calculate Resume Score
normalized_score = likert_score / 5
resume_score = Σ(normalized_score × parameter_weight) × 100
Resume score must be a number between 0 and 100.

🔹 STEP 4: Threshold-based decision logic
IF resume_score >= shortlist_threshold:
    decision = "Strong Resume – Direct Shortlist"
    interview_required = false
ELSE IF resume_score >= interview_threshold:
    decision = "Borderline Resume – Virtual Interview Required"
    interview_required = true
ELSE:
    decision = "Weak Resume – Reject"
    interview_required = false

🔹 STEP 5: Generate structured, explainable output ONLY
Output valid JSON matching the following structure exactly.
"""

RESUME_EVALUATION_PROMPT = PromptTemplate(
    input_variables=["resume_text", "job_role", "experience_level", "required_skills", "role_template", "thresholds"],
    template=RESUME_EVALUATION_INSTRUCTION
)
