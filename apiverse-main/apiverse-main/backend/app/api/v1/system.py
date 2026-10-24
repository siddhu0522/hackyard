import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.app.core.database import get_db, init_db
from backend.app.core.config import settings
from backend.app.schemas.system import HealthResponse, ConfigStatusResponse
from backend.app.models.repository import Repository
from backend.app.services.monitoring import monitoring_service
from backend.app.services.seeding import DatabaseSeeder

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.query(Repository).count()
    except Exception as e:
        db_status = f"error: {str(e)}"

    scheduler_status = "running" if monitoring_service.scheduler.running else "stopped"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": "1.0.0",
        "database": db_status,
        "scheduler": scheduler_status,
        "tagline": settings.TAGLINE
    }

@router.get("/config/status", response_model=ConfigStatusResponse)
def get_config_status():
    return {
        "llm_provider": settings.LLM_PROVIDER,
        "llm_configured": bool(
            settings.LLM_PROVIDER == "mock" or
            (settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY) or
            (settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY) or
            (settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY)
        ),
        "github_app_configured": bool(settings.GITHUB_APP_ID and settings.GITHUB_APP_PRIVATE_KEY),
        "github_pat_configured": bool(settings.GITHUB_ACCESS_TOKEN),
        "developer_approval_required": settings.REQUIRE_DEVELOPER_APPROVAL,
        "database_path": settings.DATABASE_URL,
        "demo_repos_path": str(settings.DEMO_REPOS_DIR),
        "sandbox_path": str(settings.SANDBOX_DIR)
    }

@router.post("/seed-demo")
async def seed_demo_data(db: Session = Depends(get_db)):
    """
    Populates comprehensive, relationally consistent demonstration dataset linking
    OpenAPI specifications, repositories, scans, detected changes, code impact matches,
    AI repairs, verification test runs, pull request records, and monitoring logs.
    Safe and idempotent.
    """
    seeder = DatabaseSeeder(db)
    try:
        result = await seeder.seed_all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database seeding failed: {str(e)}")
