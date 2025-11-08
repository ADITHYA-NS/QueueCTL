import subprocess
from databases.models import Job
from configurations import collection, dlq_collection  # add DLQ collection if not already present
import threading
import click
from datetime import datetime, timezone
import time
import random
import sys

stop_event = threading.Event()

def current_iso_time():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# ==========================
# Worker Function
# ==========================
def schedule(worker_id, base_delay=2):
    try:
        while not stop_event.is_set():
           
            job = collection.find_one_and_update(
                {"state": "pending"},
                {"$set": {
                    "state": "processing",
                    "updated_at": current_iso_time(),
                    "worker_assigned": worker_id
                }},
                sort=[("created_at", 1)]
            )

            if not job:
                click.secho(f"Worker {worker_id}: No pending jobs available", fg="yellow")
                time.sleep(1)
                continue

            click.secho(f"Worker {worker_id} executing job {job['id']} -> {job['command']}", fg="cyan")

            retries = job.get("attemps", 0)
            max_retries = job.get("max_retries", 3)
            base_delay = job.get("base_delay", base_delay)

            while retries <= max_retries:
                try:
                    response = subprocess.run(job["command"], shell=True, timeout=job.get("timeout", 30))
                    if response.returncode == 0:
                        state = "completed"
                        click.secho(f"Job {job['id']} completed successfully ✅", fg="green")
                        break
                    else:
                        raise subprocess.CalledProcessError(response.returncode, job["command"])
                except subprocess.TimeoutExpired:
                    click.secho(f"Job {job['id']} timed out", fg="red")
                    state = "failed"

                except Exception as e:
                    click.secho(f"Error executing job {job['id']}: {e}", fg="red")
                    state = "failed"

                if state == "failed":
                    retries += 1
                    if retries <= max_retries:
                        delay = min(base_delay ** retries + random.uniform(0, 1), 60)
                        click.secho(f"Retry {retries}/{max_retries} for job {job['id']} in {delay:.2f}s...", fg="yellow")
                        time.sleep(delay)
                        collection.update_one({"id": job["id"]}, {"$set": {"attempts": retries}})
                        continue  
                    else:
                        state = "dead"
                        job["state"] = state
                        collection.update_one({"id": job["id"]}, {"$set": {"state": state}})
                        dlq_collection.insert_one(job)
                        click.secho(f"Job {job['id']} moved to DLQ after {max_retries} retries", fg="red")
                        break
            
            collection.update_one(
                {"id": job["id"]},
                {"$set": {
                    "state": state,
                    "attempts": retries,
                    "updated_at": current_iso_time()
                }}
            )

            click.secho(f"Worker {worker_id} executed job {job['id']} -> Status: {state}", fg="green")

    finally:
        # If thread is stopped, mark processing jobs as failed
        updated = collection.update_many(
            {"state": "processing", "worker_assigned": worker_id},
            {"$set": {"state": "failed", "updated_at": current_iso_time()}}
        )
        click.secho(f"Worker {worker_id} stopped — {updated.modified_count} jobs marked as failed", fg="red")


# ==========================
# Start and Stop Workers
# ==========================
def start_workers(num_workers):
    threads = []
    try:
        for i in range(num_workers):
            thread = threading.Thread(target=schedule, args=(i + 1,))
            thread.start()
            threads.append(thread)

        for t in threads:
            t.join()
    except KeyboardInterrupt:
        click.secho("Keyboard interrupt received, stopping workers...", fg="yellow")
        stop_workers()


def stop_workers():
    stop_event.set()
    updated = collection.update_many(
        {"state": "processing"},
        {"$set": {"state": "failed", "updated_at": current_iso_time()}}
    )
    click.secho(f"Workers stopped gracefully. {updated.modified_count} jobs marked as failed.", fg="red")
