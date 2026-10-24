import pytest
from pathlib import Path
from backend.app.services.verifier import VerificationEngine
from backend.app.core.config import settings

def test_verifier_execution_demo_repo():
    engine = VerificationEngine()
    demo_repo = settings.DEMO_REPOS_DIR / "payment-service-py"
    
    assert demo_repo.exists(), "Demo repo payment-service-py should exist"
    
    # Test command discovery
    cmd = engine.discover_test_command(demo_repo)
    assert "pytest" in cmd
    
    # Run verification with no patches (baseline check)
    result = engine.run_verification(
        repo_source_path=demo_repo,
        patches=[],
        timeout_seconds=20
    )
    
    assert result["status"] == "passed"
    assert result["exit_code"] == 0
    assert result["passed_tests"] >= 1
    assert result["duration_seconds"] >= 0.0

def test_verifier_timeout():
    engine = VerificationEngine()
    demo_repo = settings.DEMO_REPOS_DIR / "payment-service-py"
    
    # Command that sleeps longer than timeout
    result = engine.run_verification(
        repo_source_path=demo_repo,
        patches=[],
        custom_command="python -c \"import time; time.sleep(5)\"",
        timeout_seconds=1
    )
    
    assert result["status"] == "timeout"
    assert "timed out" in result["stderr"]
