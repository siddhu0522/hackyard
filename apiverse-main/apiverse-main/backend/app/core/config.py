import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Self-Maintaining APIs (BUMP)"
    TAGLINE: str = "APIs change. Your code adapts."
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'bump.db'}"
    
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
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    
    # Demo and Storage paths
    DEMO_REPOS_DIR: Path = DATA_DIR / "demo_repos"
    SANDBOX_DIR: Path = DATA_DIR / "sandbox"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
settings.DEMO_REPOS_DIR.mkdir(parents=True, exist_ok=True)
settings.SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
