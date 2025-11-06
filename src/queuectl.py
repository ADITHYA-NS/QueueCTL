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
    """QueueCTL - Manage your job queue from the CLI."""
    pass


@cli.command(help="Enqueue a new job into the queue")
@click.argument("data")
def enqueue(data):
    """Enqueue a new job"""
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
    """Update a job by ID"""
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
    """List all jobs or filter by state"""
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


if __name__ == "__main__":
    cli()
