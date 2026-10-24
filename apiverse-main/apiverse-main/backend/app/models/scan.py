from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True)
    previous_spec_id = Column(Integer, ForeignKey("api_specifications.id"), nullable=False)
    current_spec_id = Column(Integer, ForeignKey("api_specifications.id"), nullable=False)
    status = Column(String(64), default="succeeded", nullable=False)  # pending, running, succeeded, failed
    total_changes = Column(Integer, default=0, nullable=False)
    breaking_changes = Column(Integer, default=0, nullable=False)
    warnings = Column(Integer, default=0, nullable=False)
    infos = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    repository = relationship("Repository", back_populates="scans")
    previous_spec = relationship("ApiSpecification", foreign_keys=[previous_spec_id], back_populates="previous_scans")
    current_spec = relationship("ApiSpecification", foreign_keys=[current_spec_id], back_populates="current_scans")
    detected_changes = relationship("DetectedChange", back_populates="scan", cascade="all, delete-orphan")
