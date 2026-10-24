import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx

from backend.app.core.database import get_db
from backend.app.models.specification import ApiSpecification
from backend.app.schemas.specification import ApiSpecificationCreate, ApiSpecificationResponse
from backend.app.services.openapi_diff import OpenAPIDiffEngine

router = APIRouter(prefix="/specifications", tags=["OpenAPI Specifications"])

@router.get("", response_model=List[ApiSpecificationResponse])
def list_specifications(db: Session = Depends(get_db)):
    return db.query(ApiSpecification).order_by(ApiSpecification.created_at.desc()).all()

@router.get("/{spec_id}", response_model=ApiSpecificationResponse)
def get_specification(spec_id: int, db: Session = Depends(get_db)):
    spec = db.query(ApiSpecification).filter(ApiSpecification.id == spec_id).first()
    if not spec:
        raise HTTPException(status_code=404, detail="Specification not found")
    return spec

@router.post("", response_model=ApiSpecificationResponse)
def create_specification(payload: ApiSpecificationCreate, db: Session = Depends(get_db)):
    engine = OpenAPIDiffEngine()
    try:
        parsed = engine.parse_spec(payload.content, fmt=payload.format)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid OpenAPI format: {str(e)}")

    spec = ApiSpecification(
        name=payload.name,
        version=payload.version or parsed.get("info", {}).get("version", "1.0.0"),
        content_json=json.dumps(parsed),
        content_yaml=payload.content if payload.format == "yaml" else None,
        format=payload.format,
        source_type=payload.source_type,
        source_url=payload.source_url
    )
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec

@router.post("/fetch-url", response_model=ApiSpecificationResponse)
async def fetch_specification_from_url(url: str, name: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Failed to fetch specification from URL: HTTP {resp.status_code}")
            content = resp.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"URL fetch error: {str(e)}")

    engine = OpenAPIDiffEngine()
    try:
        parsed = engine.parse_spec(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse downloaded spec: {str(e)}")

    api_name = name or parsed.get("info", {}).get("title", "Remote API")
    version = parsed.get("info", {}).get("version", "1.0.0")

    spec = ApiSpecification(
        name=api_name,
        version=version,
        content_json=json.dumps(parsed),
        format="json" if content.strip().startswith("{") else "yaml",
        source_type="url",
        source_url=url
    )
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec
