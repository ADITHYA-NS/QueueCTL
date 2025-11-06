from fastapi import FastAPI, APIRouter, HTTPException
from configurations import collection
from databases.schemas import all_jobs
from databases.models import Job
from bson.objectid import ObjectId
from datetime import datetime

app = FastAPI()
router = APIRouter()

@router.get("/list")
async def get_all_jobs():
    data = collection.find()
    return all_jobs(data)

@router.post("/enqueue")
async def add_job(new_job: Job):
    try:
        response = collection.insert_one(new_job.dict())
        return {"status": "Insertions Successfull","id": str(response.inserted_id) }
    except Exception as e:
        return HTTPException(status_code = 500,detail=f"Insertion Unsuccessfull - Error: {e}")

@router.put("/{job_id}")
async def update_job(job_id: str, new_job: Job):
    try:
        id = ObjectId(job_id)
        existing_job = collection.find_one({"_id": id, "is_deleted":False} )
        if not existing_job:
             return HTTPException(status_code = 404,detail=f"Updation Unsuccessfull - Job doesn't exisit")
        new_job.updated_at = datetime.timestamp(datetime.now())
        response = collection.update_one({"id": id}, {"$set": dict(new_job)})
        return {"status": "Updation Successfull","_id": str(response.inserted_id) }
    except Exception as e:
        return HTTPException(status_code = 500,detail=f"Insertion Unsuccessfull - Error: {e}")



app.include_router(router)