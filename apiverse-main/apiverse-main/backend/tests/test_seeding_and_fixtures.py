import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.models.repository import Repository
from backend.app.models.specification import ApiSpecification
from backend.app.models.scan import Scan
from backend.app.models.detected_change import DetectedChange
from backend.app.models.affected_file import AffectedFile
from backend.app.models.repair_attempt import RepairAttempt
from backend.app.models.proposed_patch import ProposedPatch
from backend.app.models.test_run import TestRun
from backend.app.models.pull_request import PullRequestRecord
from backend.app.models.monitoring import MonitoringConfiguration, BackgroundJob, NotificationRecord
from backend.app.services.seeding import DatabaseSeeder
from backend.app.services.openapi_diff import OpenAPIDiffEngine

@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()

@pytest.mark.anyio
async def test_seeder_populates_all_entities_and_is_idempotent(in_memory_db):
    seeder = DatabaseSeeder(in_memory_db)
    
    # Run 1: First seed
    res1 = await seeder.seed_all()
    assert res1["status"] == "success"
    stats1 = res1["stats"]
    assert stats1["inserted"] > 0
    assert stats1["failed"] == 0

    # Verify counts in DB
    assert in_memory_db.query(Repository).count() >= 3
    assert in_memory_db.query(ApiSpecification).count() >= 5
    assert in_memory_db.query(Scan).count() >= 3
    assert in_memory_db.query(DetectedChange).count() >= 5
    assert in_memory_db.query(AffectedFile).count() >= 1
    assert in_memory_db.query(RepairAttempt).count() >= 1
    assert in_memory_db.query(ProposedPatch).count() >= 1
    assert in_memory_db.query(TestRun).count() >= 1
    assert in_memory_db.query(PullRequestRecord).count() >= 1
    assert in_memory_db.query(MonitoringConfiguration).count() >= 2
    assert in_memory_db.query(NotificationRecord).count() >= 2

    # Verify foreign key consistency
    for change in in_memory_db.query(DetectedChange).all():
        assert change.scan_id is not None
        assert change.scan is not None

    for patch in in_memory_db.query(ProposedPatch).all():
        assert patch.repair_attempt is not None

    for pr in in_memory_db.query(PullRequestRecord).all():
        assert pr.repository is not None
        assert pr.repair_attempt is not None

    # Run 2: Second seed to verify idempotency
    seeder2 = DatabaseSeeder(in_memory_db)
    res2 = await seeder2.seed_all()
    assert res2["status"] == "success"
    stats2 = res2["stats"]
    
    # Zero new insertions on second run
    assert stats2["inserted"] == 0
    assert stats2["reused"] > 0
    assert stats2["failed"] == 0

def test_apiverse_integration_test_fixture_diff():
    import json
    from backend.app.core.config import settings

    v1_path = settings.DEMO_REPOS_DIR / "apiverse-integration-test" / "openapi_v1.json"
    v2_path = settings.DEMO_REPOS_DIR / "apiverse-integration-test" / "openapi_v2.json"

    assert v1_path.exists(), "openapi_v1.json must exist in fixture repo"
    assert v2_path.exists(), "openapi_v2.json must exist in fixture repo"

    v1_dict = json.loads(v1_path.read_text(encoding="utf-8"))
    v2_dict = json.loads(v2_path.read_text(encoding="utf-8"))

    engine = OpenAPIDiffEngine()
    diffs = engine.compare_specs(v1_dict, v2_dict)

    change_types = [d["change_type"] for d in diffs]
    assert "RESPONSE_PROPERTY_REMOVED" in change_types
    assert "ENDPOINT_REMOVED" in change_types
    assert "REQUIRED_PARAM_ADDED" in change_types
    assert "RESPONSE_PROPERTY_TYPE_CHANGED" in change_types
    assert "ENDPOINT_ADDED" in change_types
