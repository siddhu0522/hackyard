from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AffectedFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detected_change_id: int
    repository_id: int
    file_path: str
    language: str
    function_name: Optional[str] = None
    line_start: int
    line_end: int
    match_confidence: str  # confirmed, possible
    snippet: str
    context_reason: Optional[str] = None
    created_at: datetime

class CodeImpactAnalysisRequest(BaseModel):
    detected_change_id: int
    repository_id: int
