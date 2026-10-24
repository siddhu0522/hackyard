from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.database import get_db
from backend.app.models.pull_request import PullRequestRecord
from backend.app.schemas.pull_request import PullRequestCreateRequest, PullRequestResponse
from backend.app.services.pr_workflow import PullRequestWorkflowService, WorkflowError

router = APIRouter(prefix="/pull-requests", tags=["Pull Requests"])

@router.get("", response_model=List[PullRequestResponse])
def list_pull_requests(repository_id: int = None, db: Session = Depends(get_db)):
    query = db.query(PullRequestRecord)
    if repository_id:
        query = query.filter(PullRequestRecord.repository_id == repository_id)
    return query.order_by(PullRequestRecord.created_at.desc()).all()

@router.get("/{pr_id}", response_model=PullRequestResponse)
def get_pull_request(pr_id: int, db: Session = Depends(get_db)):
    pr = db.query(PullRequestRecord).filter(PullRequestRecord.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="PullRequestRecord not found")
    return pr

@router.post("", response_model=PullRequestResponse)
async def create_pull_request(payload: PullRequestCreateRequest, db: Session = Depends(get_db)):
    service = PullRequestWorkflowService(db)
    try:
        pr_record = await service.create_pull_request_for_repair(
            repair_attempt_id=payload.repair_attempt_id,
            custom_branch_name=payload.branch_name,
            custom_title=payload.title
        )
        return pr_record
    except WorkflowError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PR workflow failed: {str(e)}")
