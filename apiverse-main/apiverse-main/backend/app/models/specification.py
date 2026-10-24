from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class ApiSpecification(Base):
    __tablename__ = "api_specifications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(64), nullable=False, default="1.0.0")
    content_json = Column(Text, nullable=False)
    content_yaml = Column(Text, nullable=True)
    format = Column(String(32), default="json", nullable=False)
    source_type = Column(String(64), default="upload", nullable=False)  # upload, url, github
    source_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    previous_scans = relationship("Scan", foreign_keys="Scan.previous_spec_id", back_populates="previous_spec")
    current_scans = relationship("Scan", foreign_keys="Scan.current_spec_id", back_populates="current_spec")
