import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.core.database import get_db
from backend.app.models.monitoring import MonitoringConfiguration, BackgroundJob, NotificationRecord
from backend.app.schemas.monitoring import (
    MonitoringConfigCreate,
    MonitoringConfigResponse,
    BackgroundJobResponse,
    NotificationResponse
)
from backend.app.services.monitoring import monitoring_service

router = APIRouter(prefix="/monitoring", tags=["Monitoring & Automation"])

@router.get("", response_model=List[MonitoringConfigResponse])
def list_monitoring_configs(db: Session = Depends(get_db)):
    return db.query(MonitoringConfiguration).order_by(MonitoringConfiguration.created_at.desc()).all()

@router.post("", response_model=MonitoringConfigResponse)
def create_monitoring_config(payload: MonitoringConfigCreate, db: Session = Depends(get_db)):
    secret = uuid.uuid4().hex
    config = MonitoringConfiguration(
        repository_id=payload.repository_id,
        name=payload.name,
        api_spec_url=payload.api_spec_url,
        schedule_cron=payload.schedule_cron,
        interval_minutes=payload.interval_minutes,
        is_active=payload.is_active,
        webhook_secret=secret,
        auto_repair=payload.auto_repair,
        auto_pr=payload.auto_pr
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    if config.is_active:
        monitoring_service.add_or_update_schedule(config.id, config.interval_minutes, config.schedule_cron)

    return config

@router.post("/{config_id}/pause", response_model=MonitoringConfigResponse)
def pause_monitoring(config_id: int, db: Session = Depends(get_db)):
    config = db.query(MonitoringConfiguration).filter(MonitoringConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="MonitoringConfiguration not found")
    config.is_active = False
    monitoring_service.pause_schedule(config.id)
    db.commit()
    db.refresh(config)
    return config

@router.post("/{config_id}/resume", response_model=MonitoringConfigResponse)
def resume_monitoring(config_id: int, db: Session = Depends(get_db)):
    config = db.query(MonitoringConfiguration).filter(MonitoringConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="MonitoringConfiguration not found")
    config.is_active = True
    monitoring_service.resume_schedule(config.id)
    db.commit()
    db.refresh(config)
    return config

@router.post("/{config_id}/run-now", response_model=BackgroundJobResponse)
async def trigger_monitor_now(config_id: int, db: Session = Depends(get_db)):
    config = db.query(MonitoringConfiguration).filter(MonitoringConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="MonitoringConfiguration not found")
    job = await monitoring_service.run_monitor_job(config_id, db)
    return job

@router.get("/{config_id}/jobs", response_model=List[BackgroundJobResponse])
def get_monitoring_jobs(config_id: int, db: Session = Depends(get_db)):
    return db.query(BackgroundJob).filter(BackgroundJob.monitoring_id == config_id).order_by(BackgroundJob.started_at.desc()).limit(20).all()

@router.get("/notifications", response_model=List[NotificationResponse])
def list_notifications(db: Session = Depends(get_db)):
    return db.query(NotificationRecord).order_by(NotificationRecord.created_at.desc()).limit(50).all()

@router.post("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int, db: Session = Depends(get_db)):
    notif = db.query(NotificationRecord).filter(NotificationRecord.id == notif_id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "ok"}

@router.post("/webhook/github")
async def github_webhook_handler(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    body_bytes = await request.body()
    # If GitHub webhook secret is configured, verify HMAC
    from backend.app.core.config import settings
    if settings.GITHUB_WEBHOOK_SECRET:
        if not monitoring_service.verify_webhook_signature(body_bytes, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    return {"status": "accepted", "event": request.headers.get("X-GitHub-Event", "push")}

@router.post("/webhook/spec/{config_id}")
async def spec_webhook_handler(
    config_id: int,
    request: Request,
    x_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    config = db.query(MonitoringConfiguration).filter(MonitoringConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Monitoring configuration not found")

    body_bytes = await request.body()
    if config.webhook_secret:
        if not monitoring_service.verify_webhook_signature(body_bytes, x_signature, config.webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Trigger scan immediately in background
    job = await monitoring_service.run_monitor_job(config_id, db)
    return {"status": "triggered", "job_id": job.id}
