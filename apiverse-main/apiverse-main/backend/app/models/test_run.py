from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class TestRun(Base):
    __tablename__ = "test_runs"
    __test__ = False

    id = Column(Integer, primary_key=True, index=True)
    repair_attempt_id = Column(Integer, ForeignKey("repair_attempts.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    command = Column(String(512), nullable=False)
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    duration_seconds = Column(Float, default=0.0, nullable=False)
    status = Column(String(32), default="not_run", nullable=False)  # passed, failed, timeout, skipped, not_run
    total_tests = Column(Integer, default=0, nullable=False)
    passed_tests = Column(Integer, default=0, nullable=False)
    failed_tests = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    repair_attempt = relationship("RepairAttempt", back_populates="test_runs")
    repository = relationship("Repository", back_populates="test_runs")
