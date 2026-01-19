
import sys
import os
sys.path.append(os.getcwd())

from app.routers.candidates import background_rejection_flow
from app.db import get_db_session
from app.models.models import Candidate

# Mock _send_email to print
import app.email_service as es
def mock_send(to, sub, body):
    print(f"--- MOCKED EMAIL ---")
    print(f"To: {to}\nSubject: {sub}")
    # print("Body:") # Body is too long, just check if jobs are there
    if "Suggested Jobs" in body:
        print("✅ Body contains 'Suggested Jobs'")
    else:
        print("❌ Body DOES NOT contain 'Suggested Jobs'")
    print("--------------------")
es._send_email = mock_send

# Setup logging
from loguru import logger
logger.remove()
logger.add(sys.stdout, level="INFO")

import asyncio

def test_flow():
    email = "test_reject@example.com"
    name = "Test User"
    resume_text = """
    EXPERIENCE
    Software Engineer at Tech Corp.
    Skills: Python, AWS, Docker, FastAPI.
    """
    
    print("--- Triggering Background Flow ---")
    asyncio.run(background_rejection_flow(email, name, resume_text))
    print("--- Done ---")

if __name__ == "__main__":
    test_flow()
