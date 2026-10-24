from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class RepairAttempt(Base):
    __tablename__ = "repair_attempts"

    id = Column(Integer, primary_key=True, index=True)
    detected_change_id = Column(Integer, ForeignKey("detected_changes.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(64), default="pending", nullable=False)  # pending, repairing, repaired, awaiting_approval, approved, rejected, failed
    provider = Column(String(64), default="mock", nullable=False)
    model_name = Column(String(128), default="internal-rule-engine", nullable=False)
    explanation = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    known_risks = Column(Text, nullable=True)
    developer_approved = Column(Boolean, default=False, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    detected_change = relationship("DetectedChange", back_populates="repair_attempts")
    patches = relationship("ProposedPatch", back_populates="repair_attempt", cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="repair_attempt", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequestRecord", back_populates="repair_attempt", cascade="all, delete-orphan")
