from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class AffectedFile(Base):
    __tablename__ = "affected_files"

    id = Column(Integer, primary_key=True, index=True)
    detected_change_id = Column(Integer, ForeignKey("detected_changes.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(512), nullable=False)
    language = Column(String(32), default="python", nullable=False)  # python, typescript, javascript, etc.
    function_name = Column(String(255), nullable=True)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    match_confidence = Column(String(32), default="confirmed", nullable=False)  # confirmed, possible
    snippet = Column(Text, nullable=False)
    context_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    detected_change = relationship("DetectedChange", back_populates="affected_files")
    repository = relationship("Repository", back_populates="affected_files")
