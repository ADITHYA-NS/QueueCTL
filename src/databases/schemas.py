def individual_job(job):
    return {
        "id": str(job["id"]),
        "command": job["command"],
        "state": job["state"],
        "attempts": int(job["attempts"]),
        "max_retries": int(job["max_retries"]),
        "created_at": job["created_at"],
        "updated_at": job["updated_at"]
    }

def all_jobs(jobs):
    return [individual_job(job) for job in jobs]
