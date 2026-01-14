def rank_jobs(jobs, skills):
    ranked = []

    for job in jobs:
        score = 0
        desc = job["description"].lower()
        for s in skills:
            if s.lower() in desc:
                score += 1

        job["match_score"] = score
        ranked.append(job)

    return sorted(ranked, key=lambda x: x["match_score"], reverse=True)
