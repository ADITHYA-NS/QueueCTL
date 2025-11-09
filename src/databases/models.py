from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional

def current_iso_time():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

class Job(BaseModel):
    id: str
    command: Optional[str] = None
    state: Optional[str] = "pending"
    attempts: Optional[int] = 0
    max_retries: Optional[int] = None
    created_at: Optional[str] = datetime.utcnow().isoformat() + "Z"
    updated_at: Optional[str] = datetime.utcnow().isoformat() + "Z"
    worker_assigned: Optional[int] = 0
