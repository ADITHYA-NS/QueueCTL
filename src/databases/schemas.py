def individual_job(job):
    return {
        "id": str(job["id"]),
        "command": job["command"],
        "state": job["state"],
        "attempts": str(job["attempts"]),
        "max_retries": str(job["max_retries"]),
        "created_at": str(job["created_at"]),
        "updated_at": str(job["updated_at"])
    }

def all_jobs(jobs):
    return [individual_job(job) for job in jobs]