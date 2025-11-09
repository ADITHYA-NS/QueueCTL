#!/usr/bin/env python3
import click
import requests
import json
import sys
import builtins

BASE_URL = "http://127.0.0.1:8000"  # FastAPI backend


def pretty_print_jobs(jobs):
    """Helper to print job list nicely."""
    click.echo("Job List:")
    click.echo("=" * 60)
    for job in jobs:
        click.echo(f"ID: {job['id']}")
        click.echo(f"Command: {job['command']}")
        click.echo(f"State: {job['state']}")
        click.echo(f"Attempts: {job['attempts']}")
        click.echo(f"Max Retries: {job['max_retries']}")
        click.echo(f"Created At: {job['created_at']}")
        click.echo(f"Updated At: {job['updated_at']}")
        click.echo("-" * 60)


@click.group()
def cli():
    pass

@click.group(help="Dead Letter Queue (DLQ) operations")
def dlq():
    pass

@click.group(help="Manage and start workers")
def worker():
    pass

@click.group(help="Manage queue configurations")
def config():
    pass

@cli.command(help="Add a job to the queue")
@click.argument("data")
def enqueue(data):
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        click.secho("Invalid JSON data.", fg="red")
        sys.exit(1)

    try:
        response = requests.post(f"{BASE_URL}/enqueue", json=payload)
        if response.status_code == 200:
            click.secho("Job enqueued successfully!", fg="green")
            
        else:
            click.secho(f"Error: {response.text}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"Failed to connect to server: {e}", fg="red")


@cli.command(help="Update an existing job")
@click.argument("data")
def update(data):
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        click.secho("Invalid JSON data.", fg="red")
        sys.exit(1)

    try:
        response = requests.put(f"{BASE_URL}/update", json=payload)
        if response.status_code == 200:
            click.secho("Job updated successfully!", fg="green")
            
        else:
            click.secho(f"Error: {response.text}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"Failed to connect to server: {e}", fg="red")


@cli.command(help="List jobs with optional state filter")
@click.option("--state", help="Filter by job state (pending, running, completed, etc.)")
def list(state):
    try:
        params = {}
        if state:
            params["state"] = state

        response = requests.get(f"{BASE_URL}/list", params=params)
        if response.ok:
            data = response.json()
            if isinstance(data, builtins.list) and data:
                pretty_print_jobs(data)
            else:
                click.secho("No jobs found.", fg="yellow")
        else:
            click.secho(f"Error: {response.text}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"Failed to connect to server: {e}", fg="red")





@worker.command(help="Start worker nodes to execute commands mentioend in each job")
@click.option("--count",  help="Number of workers to start")
def start(count):
        try:
            params = {}
            if count:
                params["num_workers"] = count

            response = requests.get(f"{BASE_URL}/worker/start", params=params)
            if response.ok:
                click.secho(response.json().get("details", "Workers started!"), fg="green")
            else:
                click.secho(f"Error cli: {response.text}", fg="red")
            
        except requests.exceptions.RequestException as e:
            click.secho(f"Failed to connect to server: {e}", fg="red")



@worker.command(help="Stop all running workers gracefully")
def stop():
    try:
        response = requests.get(f"{BASE_URL}/worker/stop")
        if response.ok:
            click.secho(response.json().get("details", "Workers stopped!"), fg="green")
        else:
            click.secho(f"Error from server: {response.text}", fg="red")
    except requests.exceptions.ConnectionError:
        click.secho("Cannot connect to backend server. Is it running?", fg="red")
    except requests.exceptions.Timeout:
        click.secho("Server timeout while trying to stop workers.", fg="red")
    except Exception as e:
        click.secho(f"Unexpected error: {e}", fg="red")

@cli.command()
def status():
    """Show summary of all job states and active workers."""
    try:
        response = requests.get(f"{BASE_URL}/status")
        if response.status_code != 200:
            click.echo(f"Failed to fetch status: {response.text}")
            return

        data = response.json()

        click.echo("\n📊 Overall Status\n")
        summary = data.get("summary", {})

        click.echo(f"Timestamp       : {data.get('timestamp')}")
        click.echo(f"System Status  : {data.get('system_status', 'unknown')}")
        click.echo(f"Active Workers  : {data.get('active_workers', 0)}\n")

        click.echo("Jobs Summary:")
        click.echo(f"   • Total Jobs   : {summary.get('total_jobs', 0)}")
        click.echo(f"   • Pending      : {summary.get('pending', 0)}")
        click.echo(f"   • Processing   : {summary.get('processing', 0)}")
        click.echo(f"   • Completed    : {summary.get('completed', 0)}")
        click.echo(f"   • Failed       : {summary.get('failed', 0)}")
        click.echo(f"   • Dead         : {summary.get('dead', 0)}\n")

    except Exception as e:
        click.echo(f"Error fetching status: {e}")


@dlq.command(help="List all jobs in the Dead Letter Queue")
def list():
    try:
        response = requests.get(f"{BASE_URL}/dlq/list")
        if response.ok:
            data = response.json()
            jobs = data.get("jobs", [])
            if not jobs:
                click.secho("DLQ is empty.", fg="yellow")
                return
            click.secho("DLQ Jobs:", fg="red")
            click.echo("=" * 60)
            for job in jobs:
                click.echo(f"ID       : {job['id']}")
                click.echo(f"Command  : {job['command']}")
                click.echo(f"Attempts : {job['attempts']}")
                click.echo("-" * 60)
        else:
            click.secho(f"Error fetching DLQ: {response.text}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"Failed to connect to server: {e}", fg="red")


@dlq.command(help="Retry a job from the Dead Letter Queue")
@click.argument("job_id")
def retry(job_id):
    try:
        response = requests.post(f"{BASE_URL}/dlq/retry", params={"job_id": job_id})
        if response.ok:
            click.secho(f"Job {job_id} added to original collection successfully!", fg="green")
        else:
            click.secho(f"Error retrying job: {response.text}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"Failed to connect to server: {e}", fg="red")



@config.command(help="Set a configuration key")
@click.argument("key")
@click.argument("value", type=int)
def set(key, value):
    try:
        response = requests.post(f"{BASE_URL}/config/set", json={"key": key, "value": value})
        if response.ok:
            click.secho(f"Config updated: {key} = {value}", fg="green")
        else:
            click.secho(f"Error: {response.text}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"Failed to connect to server: {e}", fg="red")


@config.command(help="Get a configuration key")
@click.argument("key")
def get(key):
    try:
        response = requests.get(f"{BASE_URL}/config/get", params={"key": key})
        if response.ok:
            value = response.json().get("value")
            click.secho(f"{key} = {value}", fg="green")
        else:
            click.secho(f"Error: {response.text}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"Failed to connect to server: {e}", fg="red")


cli.add_command(dlq)
cli.add_command(worker)
cli.add_command(config)
if __name__ == "__main__":
    cli()
