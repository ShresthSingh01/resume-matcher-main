import json
import re
from app.llm import get_llm
from app.interview_prompts import MATCHING_PROMPT, PROFILE_EXTRACTION_PROMPT, RESUME_EVALUATION_PROMPT, ROLE_DEDUCTION_PROMPT
from app.schemas import CandidateProfile, ResumeEvaluationOutput
import asyncio

def extract_skills(resume_text: str, jd_text: str) -> dict:
    """
    Extract skills and reasoning using LLM.
    Returns dict with matched_skills, missing_skills, reasoning.
    """
    llm = get_llm(temperature=0, max_tokens=1000)
    if not llm:
        raise ValueError("LLM not configured")
        
    chain = MATCHING_PROMPT | llm
    
    try:
        response = chain.invoke({
            "context": resume_text,
            "job_description": jd_text
        })
        content = response.content.strip()
    except Exception as e:
        print(f"⚠️ LLM Error: {e}. Switching to Regex Fallback.")
        # Regex Fallback
        jd_words = set(re.findall(r'\b\w+\b', jd_text.lower()))
        resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
        
        # Simple intersection (naive but works for fallback)
        # Filter for "skill-like" words (len > 3) to reduce noise
        stopwords = {
            "with", "experience", "knowledge", "working", "good", "strong", "skills", 
            "ability", "work", "team", "environment", "years", "plus", "have", "from", 
            "that", "this", "will", "your", "development", "using", "used", "proficient",
            "understanding", "excellent", "must", "should", "requirements", "project", 
            "projects", "code", "coding", "software", "engineer", "engineering", "user",
            "required", "preferred", "role", "candidate", "responsibilities", "include",
            "ensure", "collaborate", "support", "design", "build", "maintain", "create",
            "perform", "manage", "across", "within", "tools", "systems", "processes",
            "best", "practices", "technical", "technologies", "application", "applications",
            "solution", "solutions", "business", "functional", "specifications", "needs",
            "issues", "problems", "quality", "performance", "high", "scalable", "secure",
            "reliable", "efficient", "effective", "effectively", "communicate", "communication",
            "written", "verbal", "degree", "bachelor", "master", "computer", "science",
            "related", "field", "equivalent", "complex", "large", "scale", "modern",
            "frameworks", "libraries", "platforms", "services", "cloud", "infrastructure",
            "deployment", "continuous", "integration", "delivery", "agile", "scrum",
            "methodologies", "participate", "reviews", "testing", "debugging", "troubleshooting",
            "optimization", "security", "compliance", "standards", "documentation",
            "mentor", "junior", "members", "stakeholders", "product", "owners", "managers",
            "customers", "clients", "partners", "vendors", "internal", "external",
            "teams", "cross-functional", "initiatives", "goals", "objectives", "tasks",
            "assignments", "deadline", "driven", "detail", "oriented", "analytical",
            "problem", "solving", "interpersonal", "organizational", "time", "management",
            "prioritize", "multiple", "concurrent", "activities", "under", "pressure",
            "fast", "paced", "dynamic", "startup", "culture", "passion", "learning",
            "technologies", "innovative", "creative", "thinking", "adapt", "change",
            "willingness", "travel", "location", "remote", "hybrid", "office", "salary",
            "benefits", "package", "health", "dental", "vision", "insurance", "paid",
            "vacation", "holidays", "sick", "leave", "retirement", "plan", "match",
            "equity", "stock", "options", "bonus", "performance", "review", "annual",
            "quarterly", "monthly", "weekly", "daily", "hours", "schedule", "shift",
            "monday", "friday", "weekend", "evenings", "nights", "time", "full", "part",
            "contract", "temporary", "permanent", "internship", "co-op", "entry",
            "level", "mid", "senior", "lead", "principal", "architect", "manager",
            "director", "executive", "officer", "chief", "head", "president", "founder",
            "cofounder", "partner", "associate", "analyst", "consultant", "specialist",
            "coordinator", "administrator", "generalist", "recruiter", "sourcer",
            "coordinator", "business", "operations", "sales", "marketing", "finance",
            "accounting", "legal", "compliance", "regulatory", "affairs", "government",
            "public", "relations", "media", "communications", "content", "strategy",
            "planning", "analytics", "data", "science", "research", "development",
            "product", "project", "program", "portfolio", "management", "customer",
            "success", "support", "service", "account", "management", "business",
            "development", "partnerships", "alliances", "channels", "distribution",
            "logistics", "supply", "chain", "procurement", "purchasing", "sourcing",
            "inventory", "warehouse", "transportation", "shipping", "receiving",
            "facilities", "maintenance", "security", "safety", "environmental",
            "health", "quality", "assurance", "control", "manufacturing", "production",
            "assembly", "fabrication", "machining", "welding", "construction",
            "installation", "repair", "service", "technician", "mechanic", "electrician"
        }
        meaningful_jd = {w for w in jd_words if len(w) > 3 and w not in stopwords}
        matched = list(meaningful_jd.intersection(resume_words))
        missing = list(meaningful_jd - resume_words)
        
        return {
            "matched_skills": matched[:10], # Limit to top 10
            "missing_skills": missing[:10],
            "reasoning": "LLM unavailable. Fallback to keyword matching."
        }

    # Cleaning JSON code blocks if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    try:
        data = json.loads(content)
        
        # Post-process: Verify skills are actually in the resume text (Case Insensitive)
        # This solves the issue of "hallucinated" matches or loose matching.
        real_matched = []
        real_missing = data.get("missing_skills", [])
        
        r_text_lower = resume_text.lower()
        
        for skill in data.get("matched_skills", []):
            # Check if skill is in resume using STRICT word boundaries
            # This prevents "Java" matching "Javascript" or "OS" matching "Cost"
            s_clean = re.escape(skill.lower())
            
            # Pattern: non-word-char + skill + non-word-char
            # We use \b but specialized for some edge cases like "C++" which \b breaks on (since + is non-word)
            # For "C++", \bC\+\+\b doesn't work well because + is a symbol.
            # So we check if the skill contains symbols.
            
            if re.search(r'[^a-zA-Z0-9]', skill):
                # If skill has symbols (C++, C#, .NET, Node.js), simple substring check is often safer 
                # but we try to avoid being part of a larger word if possible.
                # Heuristic: Check if it exists as a substring. 
                # For "C++", it's unlikely to be a substring of a common word essentially.
                if skill.lower() in r_text_lower:
                     real_matched.append(skill)
                else:
                     real_missing.append(skill)
            else:
                # Standard alphanumeric skill (Python, Java, AWS) -> Strict \b matching
                if re.search(rf'\b{s_clean}\b', r_text_lower):
                    real_matched.append(skill)
                else:
                    real_missing.append(skill)

        # Update lists
        return {
            "matched_skills": real_matched,
            "missing_skills": list(set(real_missing)), # Dedup
            "reasoning": data.get("reasoning", "Analysis completed.")
        }
    except json.JSONDecodeError:
        print(f"❌ JSON Decode Error. Raw: {content}")
        # Fallback empty
        return {
            "matched_skills": [],
            "missing_skills": [],
            "reasoning": "Error parsing AI response."
        }

from app.embeddings import calculate_similarity

def calculate_match_score(matched: list, missing: list, resume_text: str = "", jd_text: str = "") -> float:
    """
    Hybrid Match Score:
    - 60% Skill Match (Explicit)
    - 40% Semantic Match (Implicit/Vibe)
    """
    # 1. Skill Score
    total_skills = len(matched) + len(missing)
    if total_skills == 0:
        skill_score = 0.0
    else:
        skill_score = (len(matched) / total_skills) * 100
        
    # 2. Semantic Score
    semantic_score = 0.0
    if resume_text and jd_text:
        semantic_score = calculate_similarity(resume_text, jd_text)
        
    # Weighted Average
    # If no semantic info is passed (legacy calls), fallback to skill only
    # If no semantic info is passed (legacy calls), fallback to skill only
    if not resume_text or not jd_text:
        return round(skill_score, 2)
        
    final_score = (skill_score * 0.6) + (semantic_score * 0.4)
    return round(final_score, 2)

async def extract_skills_async(resume_text: str, jd_text: str) -> dict:
    """
    Async version of extract_skills.
    """
    llm = get_llm(temperature=0, max_tokens=1000)
    if not llm:
        raise ValueError("LLM not configured")
        
    chain = MATCHING_PROMPT | llm
    
    try:
        response = await chain.ainvoke({
            "context": resume_text,
            "job_description": jd_text
        })
        content = response.content.strip()
    except Exception as e:
        print(f"⚠️ Async LLM Error: {e}. Switching to Regex Fallback.")
        # Re-use sync fallback logic effectively or just call sync function wrapped
        # For simplicity, we just use the sync regex logic here or generic error
        return extract_skills(resume_text, jd_text) # Fallback to sync/regex if LLM fails

    # Reuse duplicate logic for cleaning
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    try:
        data = json.loads(content)
        # We can implement the same post-processing logic here or helper function
        # For strictness, let's just return raw first or duplicate the logic
        # A smart refactor would be to extract the post-processing to a pure function
        # But to be safe, let's copy the post-processing
        
        real_matched = []
        real_missing = data.get("missing_skills", [])
        r_text_lower = resume_text.lower()
        
        for skill in data.get("matched_skills", []):
            s_clean = re.escape(skill.lower())
            if re.search(r'[^a-zA-Z0-9]', skill):
                if skill.lower() in r_text_lower:
                     real_matched.append(skill)
                else:
                     real_missing.append(skill)
            else:
                if re.search(rf'\\b{s_clean}\\b', r_text_lower):
                    real_matched.append(skill)
                else:
                    real_missing.append(skill)

        return {
            "matched_skills": real_matched,
            "missing_skills": list(set(real_missing)),
            "reasoning": data.get("reasoning", "Async Analysis completed.")
        }
    except Exception as e:
        print(f"❌ Async JSON Error: {e}")
        return {
            "matched_skills": [],
            "missing_skills": [],
            "reasoning": "Error parsing Async AI response."
        }

async def extract_profile_async(resume_text: str) -> CandidateProfile:
    """
    Extracts structured profile (Education, Exp) using LLM.
    """
    llm = get_llm(temperature=0, max_tokens=2000)
    if not llm:
        # Return empty profile
        return CandidateProfile(name="Unknown", email="", phone="", skills=[])

    chain = PROFILE_EXTRACTION_PROMPT | llm.with_structured_output(CandidateProfile)

    try:
        profile = await chain.ainvoke({"resume_text": resume_text})
        return profile
    except Exception as e:
        print(f"❌ Profile Extraction Error: {e}")
        return CandidateProfile(name="Extraction Failed", email="", phone="", skills=[])

async def evaluate_resume_structured(
    resume_text: str,
    job_role: str,
    experience_level: str,
    required_skills: list,
    role_template: dict,
    thresholds: dict
) -> ResumeEvaluationOutput:
    """
    Evaluates a resume using the structured parameter-based approach.
    Enforces deterministic scoring and decision logic.
    """
    llm = get_llm(temperature=0, max_tokens=2000)
    if not llm:
        raise ValueError("LLM not configured")

    # 1. Invoke LLM for Extraction and Likert Scoring
    chain = RESUME_EVALUATION_PROMPT | llm.with_structured_output(ResumeEvaluationOutput)
    
    try:
        # We pass the raw template and thresholds to the LLM so it can 'try' to do it,
        # but we will overwrite the math in Python.
        result: ResumeEvaluationOutput = await chain.ainvoke({
            "resume_text": resume_text,
            "job_role": job_role,
            "experience_level": experience_level,
            "required_skills": ", ".join(required_skills),
            "role_template": json.dumps(role_template, indent=2),
            "thresholds": json.dumps(thresholds, indent=2)
        })
        
        # 2. Enforce Math (Deterministic Calculation)
        # resume_score = Σ(normalized_score × parameter_weight) × 100
        # normalized_score = likert_score / 5
        
        params = role_template.get("parameters", {})
        scores = result.likert_scores
        
        weighted_sum = 0.0
        
        # Mapping schema fields to parameter keys
        # "education" -> params["education"]
        param_map = {
            "education": scores.education,
            "experience": scores.experience,
            "skills": scores.skills,
            "projects": scores.projects,
            "certifications": scores.certifications
        }
        
        for key, likert_val in param_map.items():
            weight = params.get(key, 0.0)
            normalized = likert_val / 5.0
            weighted_sum += (normalized * weight)
            
        final_score = round(weighted_sum * 100, 2)
        
        # 3. Enforce Decision Logic
        shortlist_thresh = thresholds.get("shortlist", 75)
        interview_thresh = thresholds.get("interview", 50)
        
        decision = ""
        interview_req = False
        
        if final_score >= shortlist_thresh:
            decision = "Strong Resume – Direct Shortlist"
            interview_req = False
        elif final_score >= interview_thresh:
            decision = "Borderline Resume – Virtual Interview Required"
            interview_req = True
        else:
            decision = "Weak Resume – Reject"
            interview_req = False
            
        # 4. Update the Result Object
        result.weighted_resume_score = final_score
        result.decision = decision
        result.interview_required = interview_req
        
        return result
        
    except Exception as e:
        print(f"❌ Evaluation Error: {e}")
        # Return a fallback empty object or re-raise

async def detect_job_role(jd_text: str) -> str:
    """
    Uses LLM to deduce the primary job role from the JD.
    """
    llm = get_llm(temperature=0, max_tokens=50)
    if not llm: return "Candidate"
    
    chain = ROLE_DEDUCTION_PROMPT | llm
    try:
        resp = await chain.ainvoke({"job_description": jd_text})
        return resp.content.strip()
    except:
        return "Candidate"

async def extract_required_skills(jd_text: str) -> list[str]:
    """
    Simpler extraction of JUST the skills from the JD for evaluation context.
    Using a simplified version of the matching prompt logic or just reusing matching prompt with empty resume?
    Actually, let's use a simple direct prompt or just reuse the existing extraction logic but ignoring the match.
    For now, let's use a quick Regex fallback if LLM is overkill, but LLM is better.
    Let's borrow the logic from extract_skills but focused only on JD.
    """
    # Reuse extract_skills but with empty resume to force "missing_skills" to be the list of all JD skills?
    # No, matching prompt logic basically finds skills in JD and checks resume.
    # If we pass empty resume, ALL JD skills will be in 'missing_skills'.
    
    # We can reuse existing function!
    res = await extract_skills_async(resume_text="", jd_text=jd_text)
    # The 'missing_skills' + 'matched_skills' (which should be 0) = All JD Skills
    all_skills = res.get("missing_skills", []) + res.get("matched_skills", [])
    return all_skills

