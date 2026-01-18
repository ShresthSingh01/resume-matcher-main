from fastapi import APIRouter
from app.jobs_service import search_jobs

router = APIRouter()

@router.get("/jobs/recommend")
async def get_job_recommendations(role: str):
    """
    Fetches job recommendations from Adzuna based on the role.
    """
    # Basic cleaning of role text
    clean_role = role.split(',')[0].strip() # Take first part if comma separated
    
    jobs = search_jobs(clean_role)
    return {"role": clean_role, "jobs": jobs}
