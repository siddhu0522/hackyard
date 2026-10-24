from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class PullRequestCreateRequest(BaseModel):
    repair_attempt_id: int
    branch_name: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None

class PullRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repair_attempt_id: int
    repository_id: int
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    branch_name: str
    base_branch: str
    title: str
    body: str
    commit_hash: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
