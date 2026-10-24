from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class RepositoryCreate(BaseModel):
    name: str = Field(..., description="Repository name, e.g. payment-service")
    full_name: str = Field(..., description="Full repository path, e.g. acme/payment-service")
    clone_url: Optional[str] = None
    default_branch: str = Field("main", description="Default branch name")
    is_demo: bool = Field(False, description="Whether this is a local demo repository")
    local_path: Optional[str] = None

class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    full_name: str
    clone_url: Optional[str] = None
    default_branch: str
    is_demo: bool
    github_id: Optional[int] = None
    local_path: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class RepositorySyncRequest(BaseModel):
    branch: Optional[str] = None

class FileTreeItem(BaseModel):
    path: str
    type: str  # file or dir
    size: Optional[int] = None
    language: Optional[str] = None
