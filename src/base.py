from fastapi import FastAPI, APIRouter, HTTPException
from configurations import collection
from databases.schemas import all_jobs
from databases.models import Job
from datetime import datetime, timezone

app = FastAPI()
router = APIRouter()


# Utility for ISO 8601 UTC time
def current_iso_time():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# -------------------------------
#  GET: List all jobs
# -------------------------------
@router.get("/list")
async def get_all_jobs(state: str | None = None):
    try:
        if state:
            data = collection.find({"state": state})
            return all_jobs(data)
        else:
            data = collection.find()
            return all_jobs(data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch Unsuccessful - Error: {e}")


# -------------------------------
#  POST: Enqueue a new job
# -------------------------------
@router.post("/enqueue")
async def add_job(new_job: Job):
    try:
        # Set ISO time
        if collection.find_one({"id": new_job.id}):
            raise HTTPException( status_code=400, detail=f"A job with id '{new_job.id}' already exists.")
        now = datetime.utcnow().isoformat() + "Z"  # ISO 8601 UTC time
        job_data = {
            "id": new_job.id,
            "command": new_job.command,
            "state": new_job.state or "pending",
            "attempts": new_job.attempts or 0,
            "max_retries": new_job.max_retries or 3,
            "created_at": new_job.created_at or now,
            "updated_at": new_job.updated_at or now
        }

        # Insert to DB
        response = collection.insert_one(job_data)
        return {"status_code": 200,"status": "Insertion Successful","inserted_id": str(response.inserted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insertion Unsuccessful - Error: {e}")


# -------------------------------
#  PUT: Update a job by its ID
# -------------------------------
@router.put("/update")
async def update_job( new_job: Job):
    try:
        existing_job = collection.find_one({"id": new_job.id})
        if not existing_job:
            raise HTTPException(status_code=404, detail="Updation Unsuccessful - Job doesn't exist")

        # Update timestamp and ID consistency
        new_job.updated_at = current_iso_time()
    
        # Perform update
        response = collection.update_one({"id": new_job.id}, {"$set": dict(new_job)})

        if response.modified_count == 0:
            raise HTTPException(status_code=400, detail="Updation Unsuccessful - No changes were made")

        return {"status_code": 200,"details": "Updation Successful"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Updation Unsuccessful - Error: {e}")


# Register router
app.include_router(router)
