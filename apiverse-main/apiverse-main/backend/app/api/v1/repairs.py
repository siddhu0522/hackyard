import datetime
import difflib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.detected_change import DetectedChange
from backend.app.models.affected_file import AffectedFile
from backend.app.models.repair_attempt import RepairAttempt
from backend.app.models.proposed_patch import ProposedPatch
from backend.app.schemas.repair import (
    RepairRequest,
    RepairAttemptResponse,
    ProposedPatchResponse,
    DeveloperApprovalRequest,
    PatchEditRequest
)
from backend.app.services.ai_repair import AIRepairService, MissingApiKeyError
from backend.app.services.github_service import GitHubService

router = APIRouter(prefix="/repairs", tags=["AI Repairs"])
github_service = GitHubService()

@router.get("/{repair_id}", response_model=RepairAttemptResponse)
def get_repair(repair_id: int, db: Session = Depends(get_db)):
    repair = db.query(RepairAttempt).filter(RepairAttempt.id == repair_id).first()
    if not repair:
        raise HTTPException(status_code=404, detail="RepairAttempt not found")
    return repair

@router.get("/by-change/{change_id}", response_model=List[RepairAttemptResponse])
def get_repairs_by_change(change_id: int, db: Session = Depends(get_db)):
    return db.query(RepairAttempt).filter(RepairAttempt.detected_change_id == change_id).order_by(RepairAttempt.created_at.desc()).all()

@router.post("/generate", response_model=RepairAttemptResponse)
async def generate_repair(payload: RepairRequest, db: Session = Depends(get_db)):
    change = db.query(DetectedChange).filter(DetectedChange.id == payload.detected_change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="DetectedChange not found")

    affected_files = db.query(AffectedFile).filter(AffectedFile.detected_change_id == change.id).all()
    if not affected_files:
        raise HTTPException(status_code=400, detail="No affected files mapped. Run Code Impact Analysis first.")

    # Retrieve source files
    repo = affected_files[0].repository
    owner, repo_name = (repo.full_name.split("/", 1)) if "/" in repo.full_name else ("owner", repo.name)
    
    file_contents = {}
    for aff in affected_files:
        if aff.file_path not in file_contents:
            try:
                content = await github_service.get_file_content(owner, repo_name, aff.file_path, ref=repo.default_branch or "main")
                file_contents[aff.file_path] = content
            except Exception:
                pass

    repair_service = AIRepairService(provider_name=payload.provider)
    change_dict = {
        "change_type": change.change_type,
        "path": change.path,
        "http_method": change.http_method,
        "description": change.description,
        "rule_code": change.rule_code
    }
    aff_dict = [
        {"file_path": a.file_path, "language": a.language, "line_start": a.line_start, "line_end": a.line_end}
        for a in affected_files
    ]

    try:
        result = await repair_service.generate_repair(change_dict, aff_dict, file_contents, provider_name=payload.provider)
    except MissingApiKeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI repair generation failed: {str(e)}")

    status = "awaiting_approval" if settings.REQUIRE_DEVELOPER_APPROVAL else "repaired"

    repair = RepairAttempt(
        detected_change_id=change.id,
        status=status,
        provider=result.get("provider", "mock"),
        model_name=result.get("model_name", "rule-engine"),
        explanation=result.get("explanation"),
        reasoning=result.get("reasoning"),
        known_risks=result.get("known_risks"),
        developer_approved=False
    )
    db.add(repair)
    db.commit()
    db.refresh(repair)

    for p in result.get("patches", []):
        patch = ProposedPatch(
            repair_attempt_id=repair.id,
            file_path=p["file_path"],
            original_content=p["original_content"],
            patched_content=p["patched_content"],
            unified_diff=p["unified_diff"],
            is_valid=p["is_valid"],
            validation_error=p.get("validation_error")
        )
        db.add(patch)

    change.status = "repair_pending" if status == "awaiting_approval" else "repaired"
    db.commit()
    db.refresh(repair)
    return repair

@router.post("/approve", response_model=RepairAttemptResponse)
def approve_repair(payload: DeveloperApprovalRequest, db: Session = Depends(get_db)):
    repair = db.query(RepairAttempt).filter(RepairAttempt.id == payload.repair_attempt_id).first()
    if not repair:
        raise HTTPException(status_code=404, detail="RepairAttempt not found")

    repair.developer_approved = payload.approved
    repair.approved_at = datetime.datetime.utcnow() if payload.approved else None
    repair.status = "approved" if payload.approved else "rejected"
    
    if repair.detected_change:
        repair.detected_change.status = "approved" if payload.approved else "analyzed"

    db.commit()
    db.refresh(repair)
    return repair

@router.put("/patches/{patch_id}", response_model=ProposedPatchResponse)
def edit_patch(patch_id: int, payload: PatchEditRequest, db: Session = Depends(get_db)):
    patch = db.query(ProposedPatch).filter(ProposedPatch.id == patch_id).first()
    if not patch:
        raise HTTPException(status_code=404, detail="ProposedPatch not found")

    patch.patched_content = payload.patched_content
    # Recalculate diff
    diff_lines = list(difflib.unified_diff(
        patch.original_content.splitlines(keepends=True),
        patch.patched_content.splitlines(keepends=True),
        fromfile=f"a/{patch.file_path}",
        tofile=f"b/{patch.file_path}"
    ))
    patch.unified_diff = "".join(diff_lines)
    db.commit()
    db.refresh(patch)
    return patch
