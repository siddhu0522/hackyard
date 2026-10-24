from typing import Optional, Dict, Any
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    scheduler: str
    tagline: str

class ConfigStatusResponse(BaseModel):
    llm_provider: str
    llm_configured: bool
    github_app_configured: bool
    github_pat_configured: bool
    developer_approval_required: bool
    database_path: str
    demo_repos_path: str
    sandbox_path: str
