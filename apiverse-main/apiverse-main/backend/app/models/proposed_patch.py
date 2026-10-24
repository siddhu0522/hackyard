from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class ProposedPatch(Base):
    __tablename__ = "proposed_patches"

    id = Column(Integer, primary_key=True, index=True)
    repair_attempt_id = Column(Integer, ForeignKey("repair_attempts.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(512), nullable=False)
    original_content = Column(Text, nullable=False)
    patched_content = Column(Text, nullable=False)
    unified_diff = Column(Text, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False)
    validation_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    repair_attempt = relationship("RepairAttempt", back_populates="patches")
