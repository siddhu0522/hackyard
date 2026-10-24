from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.app.core.database import get_db
from backend.app.models.repository import Repository
from backend.app.models.specification import ApiSpecification
from backend.app.models.scan import Scan
from backend.app.models.detected_change import DetectedChange
from backend.app.models.repair_attempt import RepairAttempt
from backend.app.models.pull_request import PullRequestRecord
from backend.app.models.monitoring import MonitoringConfiguration, NotificationRecord

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    total_repos = db.query(Repository).count()
    total_specs = db.query(ApiSpecification).count()
    total_scans = db.query(Scan).count()
    
    breaking_changes = db.query(DetectedChange).filter(DetectedChange.severity == "BREAKING").count()
    warnings = db.query(DetectedChange).filter(DetectedChange.severity == "WARNING").count()
    
    total_repairs = db.query(RepairAttempt).count()
    approved_repairs = db.query(RepairAttempt).filter(RepairAttempt.developer_approved == True).count()
    
    open_prs = db.query(PullRequestRecord).filter(PullRequestRecord.status.in_(["created", "open"])).count()
    active_monitors = db.query(MonitoringConfiguration).filter(MonitoringConfiguration.is_active == True).count()
    
    unread_notifications = db.query(NotificationRecord).filter(NotificationRecord.is_read == False).count()

    recent_scans = (
        db.query(Scan)
        .order_by(Scan.created_at.desc())
        .limit(5)
        .all()
    )

    recent_scans_data = [
        {
            "id": s.id,
            "created_at": s.created_at.isoformat(),
            "repository": s.repository.name if s.repository else "Standalone",
            "previous_spec": s.previous_spec.name if s.previous_spec else "v1",
            "current_spec": s.current_spec.name if s.current_spec else "v2",
            "status": s.status,
            "breaking_changes": s.breaking_changes,
            "total_changes": s.total_changes
        }
        for s in recent_scans
    ]

    return {
        "tagline": "APIs change. Your code adapts.",
        "counts": {
            "repositories": total_repos,
            "specifications": total_specs,
            "scans": total_scans,
            "breaking_changes": breaking_changes,
            "warnings": warnings,
            "total_repairs": total_repairs,
            "approved_repairs": approved_repairs,
            "open_prs": open_prs,
            "active_monitors": active_monitors,
            "unread_notifications": unread_notifications
        },
        "recent_scans": recent_scans_data
    }
