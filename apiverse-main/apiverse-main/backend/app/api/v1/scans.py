import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.core.database import get_db
from backend.app.models.scan import Scan
from backend.app.models.specification import ApiSpecification
from backend.app.models.detected_change import DetectedChange
from backend.app.schemas.scan import ScanCreate, ScanResponse, ScanDetailResponse
from backend.app.schemas.detected_change import DetectedChangeResponse
from backend.app.services.openapi_diff import OpenAPIDiffEngine

router = APIRouter(prefix="/scans", tags=["Scans & Change Detection"])

@router.get("", response_model=List[ScanResponse])
def list_scans(
    repository_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Scan)
    if repository_id:
        query = query.filter(Scan.repository_id == repository_id)
    return query.order_by(Scan.created_at.desc()).offset(offset).limit(limit).all()

@router.get("/{scan_id}", response_model=ScanDetailResponse)
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@router.get("/{scan_id}/changes", response_model=List[DetectedChangeResponse])
def get_scan_changes(
    scan_id: int,
    severity: Optional[str] = Query(None, description="Filter by severity: BREAKING, WARNING, INFO"),
    db: Session = Depends(get_db)
):
    query = db.query(DetectedChange).filter(DetectedChange.scan_id == scan_id)
    if severity:
        query = query.filter(DetectedChange.severity == severity.upper())
    return query.order_by(DetectedChange.id.asc()).all()

@router.post("", response_model=ScanDetailResponse)
def trigger_scan(payload: ScanCreate, db: Session = Depends(get_db)):
    prev_spec = db.query(ApiSpecification).filter(ApiSpecification.id == payload.previous_spec_id).first()
    curr_spec = db.query(ApiSpecification).filter(ApiSpecification.id == payload.current_spec_id).first()

    if not prev_spec:
        raise HTTPException(status_code=404, detail="Previous specification not found")
    if not curr_spec:
        raise HTTPException(status_code=404, detail="Current specification not found")

    engine = OpenAPIDiffEngine()
    try:
        old_dict = json.loads(prev_spec.content_json)
        new_dict = json.loads(curr_spec.content_json)
        changes = engine.compare_specs(old_dict, new_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Comparison failed: {str(e)}")

    breaking = [c for c in changes if c["severity"] == "BREAKING"]
    warnings = [c for c in changes if c["severity"] == "WARNING"]
    infos = [c for c in changes if c["severity"] == "INFO"]

    scan = Scan(
        repository_id=payload.repository_id,
        previous_spec_id=prev_spec.id,
        current_spec_id=curr_spec.id,
        status="succeeded",
        total_changes=len(changes),
        breaking_changes=len(breaking),
        warnings=len(warnings),
        infos=len(infos),
        completed_at=datetime.datetime.utcnow()
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    for c in changes:
        detected = DetectedChange(
            scan_id=scan.id,
            change_type=c["change_type"],
            severity=c["severity"],
            path=c["path"],
            http_method=c["http_method"],
            description=c["description"],
            rule_code=c["rule_code"],
            old_value=c.get("old_value"),
            new_value=c.get("new_value"),
            evidence_json=json.dumps(c.get("evidence", {})),
            status="detected"
        )
        db.add(detected)

    db.commit()
    db.refresh(scan)
    return scan
