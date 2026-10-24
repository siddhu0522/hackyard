from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class DetectedChange(Base):
    __tablename__ = "detected_changes"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    change_type = Column(String(128), nullable=False)  # ENDPOINT_REMOVED, RESPONSE_PROPERTY_REMOVED, etc.
    severity = Column(String(32), default="BREAKING", nullable=False)  # BREAKING, WARNING, INFO
    path = Column(String(512), nullable=False)  # e.g. /v1/customers/{id}
    http_method = Column(String(16), nullable=True)  # GET, POST, DELETE, etc.
    description = Column(Text, nullable=False)
    rule_code = Column(String(64), nullable=False)  # e.g. BREAKING_001
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=False)  # JSON-pointer, specific subpaths, explanations
    status = Column(String(64), default="detected", nullable=False)  # detected, analyzing, analyzed, repair_pending, repairing, repaired, verifying, verified, pr_created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    scan = relationship("Scan", back_populates="detected_changes")
    affected_files = relationship("AffectedFile", back_populates="detected_change", cascade="all, delete-orphan")
    repair_attempts = relationship("RepairAttempt", back_populates="detected_change", cascade="all, delete-orphan")
