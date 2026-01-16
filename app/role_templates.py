
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
            "education": 0.25,
            "experience": 0.10,
            "skills": 0.30,
            "projects": 0.25,
            "certifications": 0.10
        }
    }, {
        "shortlist": 70,
        "interview": 45
    })

def _senior_template():
    return ({
        "parameters": {
             "education": 0.05,
             "experience": 0.40,
             "skills": 0.35,
             "projects": 0.15,
             "certifications": 0.05
        }
    }, {
        "shortlist": 80,
        "interview": 60
    })

def _junior_template():
    return ({
        "parameters": {
            "education": 0.15,
            "experience": 0.25,
            "skills": 0.30,
            "projects": 0.20,
            "certifications": 0.10
        }
    }, {
        "shortlist": 75,
        "interview": 50
    })
