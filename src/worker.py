import subprocess
from databases.models import Job
from configurations import collection, dlq_collection , config
import click
from datetime import datetime, timezone
import time
import random
import threading

stop_event = threading.Event()
threads = []
def current_iso_time():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def schedule(worker_id, base_delay=2):
    """
    Schedule Workers with Jobs.
    """
    try:
        while not stop_event.is_set():
            job = collection.find_one_and_update({"state": "pending"},{"$set": {"state": "processing","updated_at": current_iso_time(),"worker_assigned": worker_id}},sort=[("created_at", 1)])

            if not job:
                click.secho(f"Worker {worker_id}: No pending jobs available", fg="yellow")
                time.sleep(1)
                continue

            click.secho(f"Worker {worker_id} picked job {job['id']} -> {job['command']}", fg="blue")

            retries = job.get("attempts", 0)
            max_retries = job.get("max_retries", config.get("max_retries", 3))
            base_delay = job.get("base_delay", base_delay)

            while retries <= max_retries:
                try:
                    response = subprocess.run(
                        job["command"],
                        shell=True,
                        timeout=job.get("timeout", 30)
                    )

                    if response.returncode == 0:
                        state = "completed"
                        click.secho(f"Job {job['id']} completed successfully", fg="green")
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
                        job_copy = dict(job)
                        job_copy.pop("_id", None)
                        if not dlq_collection.find_one({"id": job["id"]}):
                            dlq_collection.insert_one(job_copy)
                        collection.delete_one({"id": job["id"]})
                        click.secho(f"Job {job['id']} moved to DLQ after {max_retries} retries", fg="red")
                        break

            collection.update_one({"id": job["id"]},{"$set": {"state": state, "attempts": retries, "updated_at": current_iso_time()}})
            click.secho(f"Worker {worker_id} finished job {job['id']} -> Status: {state}", fg="green")

    finally:
        updated = collection.update_many({"state": "processing", "worker_assigned": worker_id},{"$set": {"state": "failed", "updated_at": current_iso_time()}})
        if updated.modified_count:
            click.secho(f"Worker {worker_id} crashed — {updated.modified_count} jobs marked as failed", fg="red")


def start_workers(num_workers):
    """
    Start Worker Threads .
    """

    try:
        for i in range(num_workers):
            time.sleep(random.uniform(0, 0.2))  
            thread = threading.Thread(target=schedule, args=(i + 1,), daemon=True, name=f"Worker-{i+1}")
            thread.start()
            threads.append(thread)
            click.secho(f"Started worker {i + 1}", fg="cyan")


        while any(t.is_alive() for t in threads):
            time.sleep(0.5)

    except KeyboardInterrupt:
        click.secho("\nKeyboard interrupt received, stopping workers gracefully...", fg="yellow")
        stop_event.set()
    finally:
        for t in threads:
            t.join()
        click.secho("All workers stopped after finishing current jobs.", fg="red")


def stop_workers():
    """
    Stop Workers Gracefully.
    """
    stop_event.set()
    
    for t in threads:
        t.join(timeout=3)
        count += 1
    updated = collection.update_many(
        {"state": "processing"},
        {"$set": {"state": "pending", "updated_at": current_iso_time()}}
    )
    click.secho("All workers stopped gracefully after finishing current jobs.", fg="red")


def dlq_list():
    """
    List all jobs in the Dead Letter Queue
    """
    jobs = list(dlq_collection.find())
    if not jobs:
        click.secho("DLQ is empty", fg="yellow")
        return
    for job in jobs:
        click.secho(f"Job ID: {job['id']} | Command: {job['command']} | Attempts: {job.get('attempts', 0)}", fg="red")


def dlq_retry(job_id):
    """
    Retry a specific job from the Dead Letter Queue
    """
    job = dlq_collection.find_one({"id": job_id})
    if not job:
        click.secho(f"Job {job_id} not found in DLQ", fg="yellow")
        return

   
    job["state"] = "pending"
    job["attempts"] = 0
    job["updated_at"] = current_iso_time()
    job.pop("_id", None)  


    collection.insert_one(job)
    dlq_collection.delete_one({"id": job_id})

    click.secho(f"Job {job_id} moved from DLQ back to the main queue", fg="green")
