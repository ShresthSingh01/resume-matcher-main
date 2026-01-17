
"""
Defines the Role Templates and Thresholds logic as per the Virex System.
"""

def get_role_template(role_name: str) -> tuple[dict, dict]:
    """
    Returns (template_weights, thresholds) for a given role name or key.
    Defaults to 'Junior' if not found or unsure.
    """
    role_lower = role_name.lower()
    
    # Direct Key Match (Manual Selection)
    if role_lower == "intern":
        return _intern_template()
    if role_lower == "senior":
         return _senior_template()
    if role_lower == "junior":
         return _junior_template()

    # Fuzzy Match (Auto-Detect)
    if "intern" in role_lower or "trainee" in role_lower or "fresher" in role_lower:
        return _intern_template()

    if "senior" in role_lower or "lead" in role_lower or "manager" in role_lower or "principal" in role_lower:
        return _senior_template()

    # Default
    return _junior_template()

# Helper functions to avoid duplication
def _intern_template():
    return ({
        "parameters": {
            "education": 0.35,        # GPA, degree relevance, college prestige
            "experience": 0.05,       # Internships only
            "skills": 0.25,           # Programming languages, tools
            "projects": 0.25,         # Personal, academic, or open-source
            "certifications": 0.10    # Online courses, tech certifications
        }
    }, {
        "shortlist": 65,           # 65%
        "interview": 40            # 40%
    })

def _senior_template():
    return ({
        "parameters": {
            "education": 0.10,        # Bare minimum needed
            "experience": 0.45,       # Depth and domain alignment
            "skills": 0.30,           # Mastery over core + peripheral tools
            "projects": 0.05,         # Leadership of major projects, not side ones
            "certifications": 0.10    # Role-specific or regulatory (e.g. AWS Pro)
        }
    }, {
        "shortlist": 80,
        "interview": 60
    })


def _junior_template():
    return ({
        "parameters": {
            "education": 0.20,        # Still valued, but less than skills/exp
            "experience": 0.25,       # Full-time role exposure matters
            "skills": 0.30,           # Stack match is critical
            "projects": 0.15,         # Personal/side projects still relevant
            "certifications": 0.10    # Helpful but not critical
        }
    }, {
        "shortlist": 70,
        "interview": 50
    })
