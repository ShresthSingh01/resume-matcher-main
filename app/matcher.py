import json
from app.llm import get_llm
from app.interview_prompts import MATCHING_PROMPT

def extract_skills(resume_text: str, jd_text: str) -> dict:
    """
    Extract skills and reasoning using LLM.
    Returns dict with matched_skills, missing_skills, reasoning.
    """
    llm = get_llm(temperature=0)
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
        import re
        jd_words = set(re.findall(r'\b\w+\b', jd_text.lower()))
        resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
        
        # Simple intersection (naive but works for fallback)
        # Filter for "skill-like" words (len > 3) to reduce noise
        meaningful_jd = {w for w in jd_words if len(w) > 3}
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
        
        # Ensure schema
        return {
            "matched_skills": data.get("matched_skills", []),
            "missing_skills": data.get("missing_skills", []),
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

def calculate_match_score(matched: list, missing: list) -> float:
    """
    Deterministic Match Score = matched / (matched + missing) * 100
    """
    total = len(matched) + len(missing)
    if total == 0:
        return 0.0
    return round((len(matched) / total) * 100, 2)
