from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.detected_change import DetectedChangeResponse

class ScanCreate(BaseModel):
    repository_id: Optional[int] = None
    previous_spec_id: int
    current_spec_id: int

class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: Optional[int] = None
    previous_spec_id: int
    current_spec_id: int
    status: str
    total_changes: int
    breaking_changes: int
    warnings: int
    infos: int
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class ScanDetailResponse(ScanResponse):
    detected_changes: List[DetectedChangeResponse] = []
