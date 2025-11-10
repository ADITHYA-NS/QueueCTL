# QueueCTL - Job Queue System

A robust job queue system with worker management, retry logic, and Dead Letter Queue (DLQ) support built with FastAPI and MongoDB.

## Features

- ✅ Job queue management (pending, processing, completed, failed, dead states)
- ✅ Configurable worker pool with concurrent job execution
- ✅ Exponential backoff retry mechanism
- ✅ Dead Letter Queue (DLQ) for permanently failed jobs
- ✅ RESTful API with FastAPI
- ✅ Command-line interface (CLI) for queue operations
- ✅ MongoDB persistence
- ✅ Graceful worker shutdown
- ✅ Real-time system status monitoring

## Tech Stack

- **Backend Framework**: FastAPI
- **Database**: MongoDB Atlas
- **CLI**: Click
- **Language**: Python 3.11+

---

## Installation & Setup

### Prerequisites

- Python 3.11 or higher
- MongoDB Atlas account (free tier works fine)
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/ADITHYA-NS/QueueCTL.git
cd QueueCTL
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install CLI Tool

```bash
cd src
pip install -e .
```

This installs the `queuectl` command globally in your virtual environment.

### Step 5: Configure Environment Variables

Edit `.env` and add your MongoDB connection string:

```env
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?appName=queueCLI
```

**Getting MongoDB URI:**
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free cluster (if you don't have one)
3. Click "Connect" → "Connect your application"
4. Copy the connection string
5. Replace `<username>` and `<password>` with your database credentials

---

## Running the Application

### Terminal 1: Start the API Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Move to src folder
cd src

# Start FastAPI server
uvicorn base:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Terminal 2: Use the CLI

Open a new terminal window:

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Use queuectl commands
queuectl --help
```

---

## CLI Usage Guide

### 1. Job Management

**Enqueue a job:**
```bash
queuectl enqueue '{"id": "job1", "command": "echo Hello World"}'
queuectl enqueue '{"id": "job2", "command": "sleep 5 && echo Done"}'
queuectl enqueue '{"id": "job3", "command": "python -c \"print(2+2)\""}'
```

**List all jobs:**
```bash
queuectl list
```

**List jobs by state:**
```bash
queuectl list --state pending
queuectl list --state completed
queuectl list --state processing
```

**Update a job:**
```bash
queuectl update '{"id": "job1", "state": "pending"}'
```

### 2. Worker Management

**Start workers:**
```bash
# Start 3 worker threads
queuectl worker start --count 3
```

**Stop workers:**
```bash
# In another terminal
queuectl worker stop
```

### 3. System Status

**Check overall status:**
```bash
queuectl status
```

Output example:
```
📊 Overall Status

Timestamp       : 2025-01-15T10:30:00Z
System Status  : healthy
Active Workers  : 3

Jobs Summary:
   • Total Jobs   : 10
   • Pending      : 2
   • Processing   : 1
   • Completed    : 5
   • Failed       : 1
   • Dead         : 1
```

### 4. Dead Letter Queue (DLQ)

**List failed jobs in DLQ:**
```bash
queuectl dlq list
```

**Retry a job from DLQ:**
```bash
queuectl dlq retry job1
```

### 5. Configuration

**Set max retries:**
```bash
queuectl config set max_retries 5
```

**Get configuration value:**
```bash
queuectl config get max_retries
```

---

## API Endpoints

### Job Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/enqueue` | Add a new job to the queue |
| `GET` | `/list?state=<state>` | List all jobs (optional state filter) |
| `PUT` | `/update` | Update an existing job |

### Worker Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/worker/start?num_workers=<n>` | Start worker threads |
| `GET` | `/worker/stop` | Stop all workers gracefully |

### System Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/status` | Get system status and metrics |

### Dead Letter Queue

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dlq/list` | List all DLQ jobs |
| `POST` | `/dlq/retry?job_id=<id>` | Adds the specific DLQ job back to the main collection to retry |

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/config/set` | Set configuration parameter |
| `GET` | `/config/get?key=<key>` | Get configuration value |

---

## Complete Usage Example

```bash
# Terminal 1: Start API server
uvicorn base:app --reload

# Terminal 2: Interact with queue
# Enqueue some jobs
queuectl enqueue '{"id": "task1", "command": "echo Task 1"}'
queuectl enqueue '{"id": "task2", "command": "sleep 3 && echo Task 2"}'
queuectl enqueue '{"id": "task3", "command": "echo Task 3"}'

# Check status
queuectl status

# List pending jobs
queuectl list --state pending

# Start workers to process jobs
queuectl worker start --count 2

# Watch status as jobs process
queuectl status

# List completed jobs
queuectl list --state completed

# Stop workers when done
queuectl worker stop
```

---

## Job States

Jobs transition through the following states:

```
pending → processing → completed ✓
             ↓
           failed → (retry with exponential backoff)
             ↓
           dead → DLQ
```

- **pending**: Job is waiting to be picked up by a worker
- **processing**: Job is currently being executed
- **completed**: Job finished successfully
- **failed**: Job failed but hasn't exceeded max retries
- **dead**: Job failed after max retries (moved to DLQ)

---

## Configuration

Default settings in `configurations.py`:

- **max_retries**: 3 (can be changed via CLI)
- **base_delay**: 2.0 seconds (exponential backoff base)
- **Job timeout**: 30 seconds

**Retry Behavior:**
- Attempt 1: Immediate
- Attempt 2: ~2 seconds delay
- Attempt 3: ~4 seconds delay
- Attempt 4: ~8 seconds delay
- After max retries: Job moves to DLQ

---

## Project Structure

```
queuectl/
├── base.py                 # FastAPI application & API routes
├── worker.py               # Worker thread logic and job execution
├── configurations.py       # MongoDB connection & configuration
├── queuectl.py             # CLI tool implementation
├── databases/
│   ├── models.py           # Pydantic data models
│   └── schemas.py          # Data transformation schemas
├── requirements.txt        # Python dependencies
├── setup.py                # Package configuration for CLI
├── .env                    # Environment variable template
├── tests                   # Bash Scripts to test functionalities
|   ├── test.sh             # Tests including invalid commands, Long running commands etc
|   ├── quick_validation.sh # Tests basics functionalities
└── README.md               # This file
```
---


## Development

### Running in Development Mode

```bash
# Start with auto-reload
uvicorn base:app --reload --log-level debug
```

### Viewing API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI documentation.

---

## Test 
 ```bash
# Move to test directory
cd test

# Run a quick test
bash quick_validation.sh

# Run full tests
bash test.sh

```

## ✅ **Checklist Before Submission**

- ✅  All required commands functional
- ✅  Jobs persist after restart
- ✅  Retry and backoff implemented correctly
- ✅  DLQ operational
- ✅  CLI user-friendly and documented
- ✅  Code is modular and maintainable
- ✅  Includes test or script verifying main flows

---

## 🎬 CLI Demo
Google Drive: https://1drv.ms/v/c/12da93b45eb2a407/EeP8OPUhdetFqZLM0nG0zCoBRo_w4CMuLcBYp-ETG6bxdQ?e=iTwoSD

---

## Author

Adithya N S </br>
Contact: nsadithya004@gmail.com

---

## License

This project is licensed under the [MIT License](./LICENSE) © 2025 Adithya N S.
