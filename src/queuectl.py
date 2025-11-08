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
        click.echo(f"Created At: {job['created_at']}")
        click.echo(f"Updated At: {job['updated_at']}")
        click.echo("-" * 60)


@click.group()
def cli():
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
            click.echo(response.json())
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
            click.echo(response.json())
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


@click.group(help="Manage and start workers")
def worker():
    pass

@worker.command(help="Start worker nodes to execute commands mentioend in each job")
@click.option("--count", default=1, type=int, help="Number of workers to start")
def start(count):
        try:
            params = {}
            if count:
                params["count"] = count

            response = requests.get(f"{BASE_URL}/worker/start", params=params)
            if response.ok:
                click.secho(response.json().get("message", "Workers started!"), fg="green")
            else:
                click.secho(f"Error: {response.text}", fg="red")
        except requests.exceptions.RequestException as e:
            click.secho(f"Failed to connect to server: {e}", fg="red")

cli.add_command(worker)

if __name__ == "__main__":
    cli()
