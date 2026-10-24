from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(255), unique=True, index=True, nullable=False)
    clone_url = Column(String(512), nullable=True)
    default_branch = Column(String(128), default="main", nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    github_id = Column(Integer, nullable=True)
    local_path = Column(String(1024), nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    scans = relationship("Scan", back_populates="repository", cascade="all, delete-orphan")
    affected_files = relationship("AffectedFile", back_populates="repository", cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="repository", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequestRecord", back_populates="repository", cascade="all, delete-orphan")
    monitoring_configs = relationship("MonitoringConfiguration", back_populates="repository", cascade="all, delete-orphan")
