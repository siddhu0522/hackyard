import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.database import get_db
from backend.app.models.detected_change import DetectedChange
from backend.app.models.repository import Repository
from backend.app.models.affected_file import AffectedFile
from backend.app.schemas.affected_file import AffectedFileResponse, CodeImpactAnalysisRequest
from backend.app.services.code_impact import CodeImpactAnalyzer
from backend.app.services.github_service import GitHubService

router = APIRouter(prefix="/impact", tags=["Code Impact Analysis"])
github_service = GitHubService()

@router.get("/affected-files/{change_id}", response_model=List[AffectedFileResponse])
def get_affected_files_for_change(change_id: int, db: Session = Depends(get_db)):
    return db.query(AffectedFile).filter(AffectedFile.detected_change_id == change_id).all()

@router.post("/analyze", response_model=List[AffectedFileResponse])
async def analyze_code_impact(payload: CodeImpactAnalysisRequest, db: Session = Depends(get_db)):
    change = db.query(DetectedChange).filter(DetectedChange.id == payload.detected_change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="DetectedChange not found")

    repo = db.query(Repository).filter(Repository.id == payload.repository_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Clear previous matches for this change and repo to allow fresh re-indexing
    db.query(AffectedFile).filter(
        AffectedFile.detected_change_id == change.id,
        AffectedFile.repository_id == repo.id
    ).delete()
    db.commit()

    # Load source files from repo
    owner, repo_name = (repo.full_name.split("/", 1)) if "/" in repo.full_name else ("owner", repo.name)
    tree = await github_service.get_repository_tree(owner, repo_name, branch=repo.default_branch or "main")
    
    file_contents = {}
    for item in tree:
        if item.get("type") == "file":
            rel_path = item["path"]
            # Filter only source code files to analyze
            if any(rel_path.endswith(ext) for ext in [".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".java"]):
                try:
                    content = await github_service.get_file_content(owner, repo_name, rel_path, ref=repo.default_branch or "main")
                    file_contents[rel_path] = content
                except Exception:
                    pass

    # Run analyzer
    analyzer = CodeImpactAnalyzer()
    change_dict = {
        "change_type": change.change_type,
        "path": change.path,
        "http_method": change.http_method,
        "description": change.description,
        "rule_code": change.rule_code
    }
    raw_matches = analyzer.analyze_repository(file_contents, change_dict)

    persisted_files = []
    for m in raw_matches:
        aff = AffectedFile(
            detected_change_id=change.id,
            repository_id=repo.id,
            file_path=m["file_path"],
            language=m["language"],
            function_name=m["function_name"],
            line_start=m["line_start"],
            line_end=m["line_end"],
            match_confidence=m["match_confidence"],
            snippet=m["snippet"],
            context_reason=m["context_reason"]
        )
        db.add(aff)
        persisted_files.append(aff)

    change.status = "analyzed"
    db.commit()

    for p in persisted_files:
        db.refresh(p)

    return persisted_files
