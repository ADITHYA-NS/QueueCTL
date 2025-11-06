from pydantic import BaseModel
from datetime import datetime
class Job(BaseModel):
    id: str
    command: str
    state: str
    attempts: int
    max_retries: int
    created_at: int = int(datetime.timestamp(datetime.now()))
    updated_at: int = int(datetime.timestamp(datetime.now()))