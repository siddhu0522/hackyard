from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class ProposedPatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repair_attempt_id: int
    file_path: str
    original_content: str
    patched_content: str
    unified_diff: str
    is_valid: bool
    validation_error: Optional[str] = None
    created_at: datetime

class RepairAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detected_change_id: int
    status: str
    provider: str
    model_name: str
    explanation: Optional[str] = None
    reasoning: Optional[str] = None
    known_risks: Optional[str] = None
    developer_approved: bool
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    patches: List[ProposedPatchResponse] = []

class RepairRequest(BaseModel):
    detected_change_id: int
    provider: Optional[str] = None  # mock, openai, anthropic, gemini, custom
    model_name: Optional[str] = None
    instructions: Optional[str] = None

class DeveloperApprovalRequest(BaseModel):
    repair_attempt_id: int
    approved: bool
    notes: Optional[str] = None

class PatchEditRequest(BaseModel):
    patch_id: int
    patched_content: str
