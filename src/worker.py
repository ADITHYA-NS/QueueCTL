import subprocess
from databases.models import Job
from configurations import collection
import threading
import click
from datetime import datetime, timezone


def current_iso_time():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def schedule(worker_id):
    while True:
        job = collection.find_one_and_update({"state": "pending"}, {"$set": {"state": "processing", "updated_at": current_iso_time(),"worker_assigned":worker_id}}, sort=[("created_at",1)]) #FIFO
        click.secho(f"Worker {worker_id} executing job {job['id']} -> {job['command']}", fg="red")

        if job:
            try:
                response = subprocess.run(job["command"], shell=True, timeout=job.get("timeout", 30))
                state = "completed" if response.returncode == 0 else "failed"
            except subprocess.TimeoutExpired:
                state = "timeout"
        else:
            click.secho("No Pending Jobs Available")
            break

        collection.update_one({"id": job["id"]}, {"$set": {"state": state}})
        click.secho(f"Worker {worker_id} executed job {job['id']} -> Status: {state}")

        
def start_workers(num_worker):
    threads = []
    for i in range(num_worker):
        thread = threading.Thread(target=schedule, args=(i+1,))
        thread.start()
        threads.append(thread)
    
    for t in threads:
        t.join()
