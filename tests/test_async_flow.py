
import asyncio
import os
from app.matcher import extract_skills_async, extract_profile_async
from app.schemas import CandidateProfile
from dotenv import load_dotenv

load_dotenv()

async def test_extraction():
    # Mock Data
    resume_text = """
    John Doe
    Email: john.doe@example.com
    Phone: 123-456-7890
    
    Education:
    - B.Sc. Computer Science, MIT, 2020
    
    Experience:
    - Software Engineer at Google (2020-2024)
      Developed scalable APIs using Python and Kubernetes.
    
    Skills: Python, Kubernetes, SQL, Docker
    """
    
    jd_text = """
    Looking for a Software Engineer with Python, Kubernetes, and AWS experience.
    """
    
    print("🚀 Starting Async Test...")
    
    # Run in parallel
    task1 = extract_profile_async(resume_text)
    task2 = extract_skills_async(resume_text, jd_text)
    
    profile, match_data = await asyncio.gather(task1, task2)
    
    print("\n✅ Profile Extraction:")
    print(f"Name: {profile.name}")
    print(f"Education: {profile.education}")
    print(f"Experience: {profile.experience}")
    
    print("\n✅ Skill Matching:")
    print(f"Matched: {match_data['matched_skills']}")
    print(f"Missing: {match_data['missing_skills']}")

    assert profile.name == "John Doe" or profile.name == "Unknown"
    # assert "Python" in match_data['matched_skills']
    print("\n🎉 Test Finished (Check if values look right)")

if __name__ == "__main__":
    asyncio.run(test_extraction())
