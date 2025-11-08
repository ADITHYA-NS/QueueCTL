from fastapi import FastAPI, APIRouter, HTTPException, Query, Body
from configurations import collection, dlq_collection, config
from databases.schemas import all_jobs
from databases.models import Job
from datetime import datetime, timezone
from worker import start_workers, stop_workers
import threading

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
            "max_retries": config["max_retries"],
            "created_at": new_job.created_at or now,
            "updated_at": new_job.updated_at or now,
            "worker_assigned": 0
        }

        response = collection.insert_one(job_data)
        return {"status_code": 200,"status": "Insertion Successful","inserted_id": str(response.inserted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insertion Unsuccessful - Error: {e}")



@router.put("/update")
async def update_job(new_job: Job):
    try:
        existing_job = collection.find_one({"id": new_job.id})
        if not existing_job:
            raise HTTPException(status_code=404, detail="Updation Unsuccessful - Job doesn't exist")

       
        update_data = {k: v for k, v in new_job.dict().items() if v is not None}
        update_data["updated_at"] = current_iso_time()

        response = collection.update_one({"id": new_job.id}, {"$set": update_data})

        if response.modified_count == 0:
            raise HTTPException(status_code=400, detail="Updation Unsuccessful - No changes were made")

        return {"status_code": 200, "details": f"Updation Successful for job {new_job.id}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Updation Unsuccessful - Error: {e}")

@router.get("/worker/start")
def start_worker(num_workers: int = Query(..., description="Number of worker threads to start")):
    """
    Starts the specified number of worker threads in the background.
    """
    try:
        # Start workers in a background thread so FastAPI doesn't block
        threading.Thread(target=start_workers, args=(num_workers,), daemon=True).start()
        return {"status_code": 200, "details": f"Started {num_workers} worker(s) successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workers: {e}")
    
@router.get("/worker/stop")
def stop_worker():
    try:
        stop_workers()
        return {"status_code": 200, "details": "Workers Stopped Gracefully"}
    except Exception as e:
        return {"detail": f"Failed to stop workers: {str(e)}"}
   

@router.get("/status")
def overall_status():
    try:
        total_jobs = collection.count_documents({})
        pending_jobs = collection.count_documents({"state": "pending"})
        processing_jobs = collection.count_documents({"state": "processing"})
        completed_jobs = collection.count_documents({"state": "completed"})
        failed_jobs = collection.count_documents({"state": "failed"})
        dead_jobs = collection.count_documents({"state": "dead"})

        active_workers = len(set([
            job.get("worker_assigned")
            for job in collection.find({"state": "processing"}, {"worker_assigned": 1})
            if job.get("worker_assigned") is not None
        ]))

        return {
            "timestamp": current_iso_time(),
            "summary": {
                "total_jobs": total_jobs,
                "pending": pending_jobs,
                "processing": processing_jobs,
                "completed": completed_jobs,
                "failed": failed_jobs,
                "dead": dead_jobs
            },
            "active_workers": active_workers,
            "system_status": "healthy" if processing_jobs > 0 or pending_jobs > 0 else "idle"
        }

    except Exception as e:
        return {"error": f"Failed to fetch status: {e}"}

@router.get("/dlq/list")
def get_dlq_jobs():
    try:
        jobs = list(dlq_collection.find())
        if not jobs:
            return {"status": "DLQ is empty", "jobs": []}
        return {"status": "success", "jobs": [{"id": j["id"], "command": j["command"], "attempts": j.get("attempts", 0)} for j in jobs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch DLQ jobs: {e}")


@router.post("/dlq/retry")
def retry_dlq_job(job_id: str = Query(..., description="ID of the job to retry from DLQ")):
    try:
        job = dlq_collection.find_one({"id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found in DLQ")
        
        job["state"] = "pending"
        job["attempts"] = 0
        job["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        job.pop("_id", None)
        # Add back to main collection
        collection.insert_one(job)
        dlq_collection.delete_one({"id": job_id})
        return {"status": "success", "details": f"Job {job_id} retried successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry job {job_id}: {e}")



@router.post("/config/set")
def set_config(key: str = Body(...), value: int = Body(...)):
    if key not in config:
        raise HTTPException(status_code=400, detail=f"Invalid config key: {key}")
    config[key] = value
    return {"status": "success", "key": key, "value": value}

@router.get("/config/get")
def get_config(key: str):
    if key not in config:
        raise HTTPException(status_code=400, detail=f"Invalid config key: {key}")
    return {"status": "success", "key": key, "value": config[key]}  
app.include_router(router)
