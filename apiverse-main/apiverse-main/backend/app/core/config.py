import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# In Vercel serverless environment, filesystem is read-only except /tmp
IS_VERCEL = bool(os.environ.get("VERCEL"))

if IS_VERCEL:
    DATA_DIR = Path(tempfile.gettempdir()) / "bump_data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Copy pre-seeded SQLite database from bundle to /tmp if available
    bundled_db = BACKEND_DIR / "data" / "bump.db"
    dest_db = DATA_DIR / "bump.db"
    if bundled_db.exists() and not dest_db.exists():
        try:
            shutil.copy2(bundled_db, dest_db)
        except Exception:
            pass
    # Copy demo repos from bundle to /tmp if available
    bundled_demos = BACKEND_DIR / "data" / "demo_repos"
    dest_demos = DATA_DIR / "demo_repos"
    if bundled_demos.exists() and not dest_demos.exists():
        try:
            shutil.copytree(bundled_demos, dest_demos, dirs_exist_ok=True)
        except Exception:
            pass
else:
    DATA_DIR = BACKEND_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Self-Maintaining APIs (BUMP)"
    TAGLINE: str = "APIs change. Your code adapts."
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.environ.get("DATABASE_URL") or f"sqlite:///{DATA_DIR / 'bump.db'}"
    
    # GitHub Integration
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_APP_PRIVATE_KEY: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_ACCESS_TOKEN: Optional[str] = None  # PAT fallback
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    
    # AI Repair Provider: 'mock', 'openai', 'anthropic', 'gemini', 'custom'
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"
    CUSTOM_LLM_URL: Optional[str] = None
    CUSTOM_LLM_API_KEY: Optional[str] = None
    
    # Developer Safety
    REQUIRE_DEVELOPER_APPROVAL: bool = True
    ALLOW_AUTO_PR: bool = True
    MAX_TEST_TIMEOUT_SECONDS: int = 45
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ]
    
    # Demo and Storage paths
    DEMO_REPOS_DIR: Path = DATA_DIR / "demo_repos"
    SANDBOX_DIR: Path = DATA_DIR / "sandbox"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
try:
    settings.DEMO_REPOS_DIR.mkdir(parents=True, exist_ok=True)
    settings.SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
