from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.repair_attempt import RepairAttempt
from backend.app.models.test_run import TestRun
from backend.app.schemas.test_run import TestRunRequest, TestRunResponse
from backend.app.services.verifier import VerificationEngine

router = APIRouter(prefix="/verifications", tags=["Test Verifications"])
verifier = VerificationEngine()

@router.get("/{run_id}", response_model=TestRunResponse)
def get_test_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="TestRun not found")
    return run

@router.get("/by-repair/{repair_id}", response_model=List[TestRunResponse])
def get_runs_by_repair(repair_id: int, db: Session = Depends(get_db)):
    return db.query(TestRun).filter(TestRun.repair_attempt_id == repair_id).order_by(TestRun.created_at.desc()).all()

@router.post("/run", response_model=TestRunResponse)
def run_repair_verification(payload: TestRunRequest, db: Session = Depends(get_db)):
    repair = db.query(RepairAttempt).filter(RepairAttempt.id == payload.repair_attempt_id).first()
    if not repair:
        raise HTTPException(status_code=404, detail="RepairAttempt not found")

    change = repair.detected_change
    if not change or not change.affected_files:
        raise HTTPException(status_code=400, detail="No repository or affected files found for this repair")

    repo = change.affected_files[0].repository
    if not repo:
        raise HTTPException(status_code=400, detail="Repository record missing")

    # Determine source directory
    repo_source_path = Path(repo.local_path) if repo.local_path else (settings.DEMO_REPOS_DIR / repo.name)
    if not repo_source_path.exists():
        # Fallback to demo dir
        repo_source_path = settings.DEMO_REPOS_DIR / repo.name

    patches_data = [
        {"file_path": p.file_path, "patched_content": p.patched_content}
        for p in repair.patches
    ]

    # Execute in sandbox
    run_result = verifier.run_verification(
        repo_source_path=repo_source_path,
        patches=patches_data,
        custom_command=payload.custom_command
    )

    test_run = TestRun(
        repair_attempt_id=repair.id,
        repository_id=repo.id,
        command=run_result["command"],
        exit_code=run_result["exit_code"],
        stdout=run_result["stdout"],
        stderr=run_result["stderr"],
        duration_seconds=run_result["duration_seconds"],
        status=run_result["status"],
        total_tests=run_result["total_tests"],
        passed_tests=run_result["passed_tests"],
        failed_tests=run_result["failed_tests"]
    )
    db.add(test_run)

    # Update states
    if run_result["status"] == "passed":
        change.status = "verified"
        repair.status = "verified"
    else:
        change.status = "failed"
        repair.status = "failed"

    db.commit()
    db.refresh(test_run)
    return test_run
