from fastapi import FastAPI, APIRouter, HTTPException, Query
from configurations import collection
from databases.schemas import all_jobs
from databases.models import Job
from datetime import datetime, timezone
from worker import start_workers

app = FastAPI()
router = APIRouter()



def current_iso_time():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


@router.post("/enqueue")
async def add_job(new_job: Job):
    try:
        if collection.find_one({"id": new_job.id}):
            raise HTTPException( status_code=400, detail=f"A job with id '{new_job.id}' already exists.")
        now = datetime.utcnow().isoformat() + "Z" 
        job_data = {
            "id": new_job.id,
            "command": new_job.command,
            "state": new_job.state or "pending",
            "attempts": new_job.attempts or 0,
            "max_retries": new_job.max_retries or 3,
            "created_at": new_job.created_at or now,
            "updated_at": new_job.updated_at or now,
            "worker_assigned": 0
        }

        response = collection.insert_one(job_data)
        return {"status_code": 200,"status": "Insertion Successful","inserted_id": str(response.inserted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insertion Unsuccessful - Error: {e}")



@router.put("/update")
async def update_job( new_job: Job):
    try:
        existing_job = collection.find_one({"id": new_job.id})
        if not existing_job:
            raise HTTPException(status_code=404, detail="Updation Unsuccessful - Job doesn't exist")

        new_job.updated_at = current_iso_time()
    
        response = collection.update_one({"id": new_job.id}, {"$set": dict(new_job)})

        if response.modified_count == 0:
            raise HTTPException(status_code=400, detail="Updation Unsuccessful - No changes were made")

        return {"status_code": 200,"details": "Updation Successful"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Updation Unsuccessful - Error: {e}")

@router.get("/worker/start")
def start_worker(num_workers: int = Query(1, ge=1)):
    try:
        start_workers(num_workers)
        return {"status_code": 200,"details": f"Started {num_workers} worker(s) successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workers: {e}")




app.include_router(router)
