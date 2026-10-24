from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class TestRunRequest(BaseModel):
    repair_attempt_id: int
    custom_command: Optional[str] = None

class TestRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repair_attempt_id: int
    repository_id: int
    command: str
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    duration_seconds: float
    status: str  # passed, failed, timeout, skipped, not_run
    total_tests: int
    passed_tests: int
    failed_tests: int
    created_at: datetime
