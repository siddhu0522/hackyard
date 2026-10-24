from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class MonitoringConfiguration(Base):
    __tablename__ = "monitoring_configurations"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    api_spec_url = Column(String(1024), nullable=False)
    schedule_cron = Column(String(64), nullable=True)  # e.g. "0 */6 * * *"
    interval_minutes = Column(Integer, default=60, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    webhook_secret = Column(String(255), nullable=True)
    auto_repair = Column(Boolean, default=False, nullable=False)
    auto_pr = Column(Boolean, default=False, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    repository = relationship("Repository", back_populates="monitoring_configs")
    jobs = relationship("BackgroundJob", back_populates="monitoring_config", cascade="all, delete-orphan")

class BackgroundJob(Base):
    __tablename__ = "background_jobs"

    id = Column(Integer, primary_key=True, index=True)
    monitoring_id = Column(Integer, ForeignKey("monitoring_configurations.id", ondelete="CASCADE"), nullable=True)
    job_type = Column(String(64), nullable=False)  # scan, repair, verify, sync
    status = Column(String(32), default="pending", nullable=False)  # pending, running, succeeded, failed
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    logs = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    monitoring_config = relationship("MonitoringConfiguration", back_populates="jobs")

class NotificationRecord(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(64), nullable=False)  # BREAKING_CHANGE_DETECTED, REPAIR_PROPOSED, TEST_FAILED, PR_CREATED
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(32), default="info", nullable=False)  # info, warning, error, success
    is_read = Column(Boolean, default=False, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
