
from app.jobs_service import search_jobs
import os
from dotenv import load_dotenv

load_dotenv()

print(f"App ID: {os.getenv('ADZUNA_APP_ID')}")
# conceal key for logs
key = os.getenv('ADZUNA_APP_KEY')
print(f"App Key: {key[:4]}..." if key else "App Key: None")

print("\nSearching for 'Software Engineer'...")
jobs = search_jobs("Software Engineer")
print(f"Found {len(jobs)} jobs.")
for j in jobs:
    print(f"- {j['title']} @ {j['company']}")

print("\nSearching for 'Manager'...")
jobs2 = search_jobs("Manager")
print(f"Found {len(jobs2)} jobs.")
