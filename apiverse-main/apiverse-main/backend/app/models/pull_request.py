from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class PullRequestRecord(Base):
    __tablename__ = "pull_request_records"

    id = Column(Integer, primary_key=True, index=True)
    repair_attempt_id = Column(Integer, ForeignKey("repair_attempts.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    pr_number = Column(Integer, nullable=True)
    pr_url = Column(String(512), nullable=True)
    branch_name = Column(String(255), nullable=False)
    base_branch = Column(String(128), default="main", nullable=False)
    title = Column(String(512), nullable=False)
    body = Column(Text, nullable=False)
    commit_hash = Column(String(64), nullable=True)
    status = Column(String(64), default="created", nullable=False)  # pending, created, merged, closed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    repair_attempt = relationship("RepairAttempt", back_populates="pull_requests")
    repository = relationship("Repository", back_populates="pull_requests")
