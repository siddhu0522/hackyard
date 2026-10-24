from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class MonitoringConfigCreate(BaseModel):
    repository_id: int
    name: str
    api_spec_url: str
    schedule_cron: Optional[str] = None
    interval_minutes: int = 60
    is_active: bool = True
    auto_repair: bool = False
    auto_pr: bool = False

class MonitoringConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    name: str
    api_spec_url: str
    schedule_cron: Optional[str] = None
    interval_minutes: int
    is_active: bool
    webhook_secret: Optional[str] = None
    auto_repair: bool
    auto_pr: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime

class BackgroundJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    monitoring_id: Optional[int] = None
    job_type: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    logs: Optional[str] = None
    error_message: Optional[str] = None

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    title: str
    message: str
    severity: str
    is_read: bool
    metadata_json: Optional[str] = None
    created_at: datetime
