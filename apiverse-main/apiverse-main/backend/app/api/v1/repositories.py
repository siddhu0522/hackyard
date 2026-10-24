from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pathlib import Path

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.repository import Repository
from backend.app.schemas.repository import RepositoryResponse, RepositoryCreate
from backend.app.services.github_service import GitHubService

router = APIRouter(prefix="/repositories", tags=["Repositories"])
github_service = GitHubService()

@router.get("", response_model=List[RepositoryResponse])
def list_repositories(db: Session = Depends(get_db)):
    return db.query(Repository).order_by(Repository.updated_at.desc()).all()

@router.post("", response_model=RepositoryResponse)
def create_repository(payload: RepositoryCreate, db: Session = Depends(get_db)):
    existing = db.query(Repository).filter(Repository.full_name == payload.full_name).first()
    if existing:
        return existing

    repo = Repository(
        name=payload.name,
        full_name=payload.full_name,
        clone_url=payload.clone_url,
        default_branch=payload.default_branch,
        is_demo=payload.is_demo,
        local_path=payload.local_path
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo

@router.post("/discover-demo")
def discover_demo_repositories(db: Session = Depends(get_db)):
    """Discovers and registers local demo repositories into database."""
    demos = github_service.list_local_demo_repositories()
    added = []
    for d in demos:
        existing = db.query(Repository).filter(Repository.full_name == d["full_name"]).first()
        if not existing:
            repo = Repository(
                name=d["name"],
                full_name=d["full_name"],
                clone_url=d["clone_url"],
                default_branch=d["default_branch"],
                is_demo=True,
                local_path=d.get("local_path")
            )
            db.add(repo)
            added.append(d["name"])
    db.commit()
    return {"status": "ok", "added": added, "total_demo_repos": len(demos)}

@router.get("/github/status")
async def get_github_status():
    return await github_service.get_status()

@router.get("/{repo_id}/tree")
async def get_repository_tree(repo_id: int, branch: Optional[str] = None, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    branch_name = branch or repo.default_branch or "main"
    owner, repo_name = (repo.full_name.split("/", 1)) if "/" in repo.full_name else ("owner", repo.name)
    tree = await github_service.get_repository_tree(owner, repo_name, branch=branch_name)
    return {"repository": repo.full_name, "branch": branch_name, "tree": tree}

@router.get("/{repo_id}/file")
async def get_file_content(repo_id: int, file_path: str = Query(...), ref: Optional[str] = None, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    branch_name = ref or repo.default_branch or "main"
    owner, repo_name = (repo.full_name.split("/", 1)) if "/" in repo.full_name else ("owner", repo.name)
    try:
        content = await github_service.get_file_content(owner, repo_name, file_path, ref=branch_name)
        return {"file_path": file_path, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File {file_path} not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Access denied")
