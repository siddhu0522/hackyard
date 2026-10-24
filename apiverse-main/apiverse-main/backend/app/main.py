import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.services.monitoring import monitoring_service

from backend.app.api.v1.dashboard import router as dashboard_router
from backend.app.api.v1.repositories import router as repositories_router
from backend.app.api.v1.specifications import router as specifications_router
from backend.app.api.v1.scans import router as scans_router
from backend.app.api.v1.impact import router as impact_router
from backend.app.api.v1.repairs import router as repairs_router
from backend.app.api.v1.verifications import router as verifications_router
from backend.app.api.v1.pull_requests import router as pull_requests_router
from backend.app.api.v1.monitoring import router as monitoring_router
from backend.app.api.v1.system import router as system_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bump")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and background scheduler
    logger.info("Initializing Self-Maintaining APIs SQLite database...")
    init_db()
    logger.info("Starting background monitoring scheduler...")
    monitoring_service.start()
    yield
    # Shutdown
    logger.info("Stopping background monitoring scheduler...")
    monitoring_service.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="APIs change. Your code adapts. Complete Self-Maintaining APIs platform.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 Routers
prefix = settings.API_V1_PREFIX
app.include_router(dashboard_router, prefix=prefix)
app.include_router(repositories_router, prefix=prefix)
app.include_router(specifications_router, prefix=prefix)
app.include_router(scans_router, prefix=prefix)
app.include_router(impact_router, prefix=prefix)
app.include_router(repairs_router, prefix=prefix)
app.include_router(verifications_router, prefix=prefix)
app.include_router(pull_requests_router, prefix=prefix)
app.include_router(monitoring_router, prefix=prefix)
app.include_router(system_router, prefix=prefix)

@app.get("/health")
def health():
    return {"status": "ok", "tagline": settings.TAGLINE}

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "docs_url": "/docs",
        "api_v1": prefix
    }
