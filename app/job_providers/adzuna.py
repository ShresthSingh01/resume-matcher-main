import requests
import os
from dotenv import load_dotenv
load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")

print("APP ID:", ADZUNA_APP_ID)
print("API KEY:", ADZUNA_API_KEY[:6] if ADZUNA_API_KEY else None)

def normalize_skills(skills):
    core = []
    for s in skills:
        s = s.lower()
        if "python" in s:
            core.append("python")
        elif "data" in s:
            core.append("data")
        elif "sql" in s or "mysql" in s:
            core.append("sql")
        elif "machine learning" in s:
            core.append("machine learning")
        elif "power bi" in s or "tableau" in s:
            core.append("bi")
    return list(dict.fromkeys(core))[:2]


def search_jobs(skills, location="in", limit=10):
    #query = " ".join(skills[:5])
    core_skills = normalize_skills(skills)
    query = " ".join(core_skills) if core_skills else "software developer"


    url = f"https://api.adzuna.com/v1/api/jobs/{location}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "what": query,
        "results_per_page": limit,
        "content-type": "application/json"
    }

    r = requests.get(url, params=params)
    if r.status_code != 200:
        return []

    jobs = []
    for j in r.json().get("results", []):
        jobs.append({
            "title": j.get("title"),
            "company": j.get("company", {}).get("display_name"),
            "location": j.get("location", {}).get("display_name"),
            "url": j.get("redirect_url"),
            "description": j.get("description", "")[:300]
        })

    return jobs
