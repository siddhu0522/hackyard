from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class DetectedChangeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_id: int
    change_type: str
    severity: str  # BREAKING, WARNING, INFO
    path: str
    http_method: Optional[str] = None
    description: str
    rule_code: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    evidence_json: str
    status: str
    created_at: datetime
