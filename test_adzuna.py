from app.job_providers.adzuna import search_jobs

jobs = search_jobs(["python", "django"])

for j in jobs[:3]:
    print(j["title"], "-", j["company"])
