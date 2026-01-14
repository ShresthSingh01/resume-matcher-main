import os
import requests
from dotenv import load_dotenv

load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

def search_jobs(role: str, country="us", results_per_page=5):
    """
    Fetches job listings from Adzuna API.
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("Warning: Adzuna credentials missing.")
        return []

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": results_per_page,
        "what": role,
        "content-type": "application/json"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        jobs = []
        for item in data.get('results', []):
            jobs.append({
                "title": item.get('title'),
                "company": item.get('company', {}).get('display_name'),
                "location": item.get('location', {}).get('display_name'),
                "url": item.get('redirect_url'),
                "description": item.get('description')
            })
            
        return jobs

    except Exception as e:
        print(f"Adzuna API Error: {e}")
        return []
