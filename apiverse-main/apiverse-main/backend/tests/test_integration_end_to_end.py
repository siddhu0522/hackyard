import json
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal, init_db
from backend.app.core.config import settings

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()
    yield

def test_system_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["tagline"] == "APIs change. Your code adapts."

def test_system_config_status():
    response = client.get("/api/v1/system/config/status")
    assert response.status_code == 200
    data = response.json()
    assert "llm_provider" in data
    assert "developer_approval_required" in data
    assert "database_path" in data

def test_full_autonomous_repair_workflow():
    # 1. Discover local demo repositories
    resp_discover = client.post("/api/v1/repositories/discover-demo")
    assert resp_discover.status_code == 200
    
    # 2. List repositories and get payment-service-py
    resp_repos = client.get("/api/v1/repositories")
    assert resp_repos.status_code == 200
    repos = resp_repos.json()
    assert len(repos) >= 1
    target_repo = next((r for r in repos if "payment-service" in r["name"]), repos[0])

    # 3. Create Base OpenAPI Spec (v1)
    v1_content = {
        "openapi": "3.0.0",
        "info": {"title": "Store API", "version": "1.0.0"},
        "paths": {
            "/v1/items": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "items": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "integer"},
                                                        "name": {"type": "string"},
                                                        "status": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    resp_v1 = client.post("/api/v1/specifications", json={
        "name": "Integration Test API",
        "version": "1.0.0",
        "content": json.dumps(v1_content),
        "format": "json",
        "source_type": "upload"
    })
    assert resp_v1.status_code == 200
    spec_v1_id = resp_v1.json()["id"]

    # 4. Create Target OpenAPI Spec (v2) with breaking change ('name' property removed)
    v2_content = {
        "openapi": "3.0.0",
        "info": {"title": "Store API", "version": "2.0.0"},
        "paths": {
            "/v1/items": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "items": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "integer"},
                                                        "status": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    resp_v2 = client.post("/api/v1/specifications", json={
        "name": "Integration Test API",
        "version": "2.0.0",
        "content": json.dumps(v2_content),
        "format": "json",
        "source_type": "upload"
    })
    assert resp_v2.status_code == 200
    spec_v2_id = resp_v2.json()["id"]

    # 5. Trigger Diff Scan
    resp_scan = client.post("/api/v1/scans", json={
        "repository_id": target_repo["id"],
        "previous_spec_id": spec_v1_id,
        "current_spec_id": spec_v2_id
    })
    assert resp_scan.status_code == 200
    scan_data = resp_scan.json()
    assert scan_data["breaking_changes"] >= 1
    assert len(scan_data["detected_changes"]) >= 1
    
    primary_change = scan_data["detected_changes"][0]
    assert primary_change["severity"] == "BREAKING"
    assert primary_change["change_type"] == "RESPONSE_PROPERTY_REMOVED"
    assert "evidence_json" in primary_change

    # 6. Run Code Impact Analysis against target repository
    resp_impact = client.post("/api/v1/impact/analyze", json={
        "detected_change_id": primary_change["id"],
        "repository_id": target_repo["id"]
    })
    assert resp_impact.status_code == 200
    impacted_files = resp_impact.json()
    assert len(impacted_files) >= 1
    assert impacted_files[0]["file_path"] == "client.py"
    assert impacted_files[0]["match_confidence"] == "confirmed"

    # 7. Generate AI Repair Proposal
    resp_repair = client.post("/api/v1/repairs/generate", json={
        "detected_change_id": primary_change["id"],
        "provider": "mock"
    })
    assert resp_repair.status_code == 200
    repair_data = resp_repair.json()
    repair_id = repair_data["id"]
    assert repair_data["developer_approved"] is False
    assert len(repair_data["patches"]) >= 1
    assert "unified_diff" in repair_data["patches"][0]

    # 8. Test State Machine Guard: Attempting to publish PR without developer approval & verification must fail
    resp_pr_blocked = client.post("/api/v1/pull-requests", json={
        "repair_attempt_id": repair_id
    })
    assert resp_pr_blocked.status_code == 400
    assert "approval is required" in resp_pr_blocked.json()["detail"].lower()

    # 9. Developer Grants Approval
    resp_approve = client.post("/api/v1/repairs/approve", json={
        "repair_attempt_id": repair_id,
        "approved": True
    })
    assert resp_approve.status_code == 200
    assert resp_approve.json()["developer_approved"] is True

    # 10. Execute Test Verification in Sandbox
    resp_verify = client.post("/api/v1/verifications/run", json={
        "repair_attempt_id": repair_id
    })
    assert resp_verify.status_code == 200
    verify_data = resp_verify.json()
    assert verify_data["status"] == "passed"
    assert verify_data["exit_code"] == 0

    # 11. Create Pull Request
    resp_pr = client.post("/api/v1/pull-requests", json={
        "repair_attempt_id": repair_id
    })
    assert resp_pr.status_code == 200
    pr_data = resp_pr.json()
    assert pr_data["status"] == "created"
    assert pr_data["branch_name"].startswith("bump/repair-change-")
    assert pr_data["base_branch"] == target_repo["default_branch"]
    assert "APIs change. Your code adapts." in pr_data["body"]

    # 12. Duplicate PR Check: Repeated request must return existing record idempotently
    resp_pr_duplicate = client.post("/api/v1/pull-requests", json={
        "repair_attempt_id": repair_id
    })
    assert resp_pr_duplicate.status_code == 200
    assert resp_pr_duplicate.json()["id"] == pr_data["id"]

def test_monitoring_and_webhook():
    # 1. Create a monitor
    resp_repos = client.get("/api/v1/repositories")
    repo_id = resp_repos.json()[0]["id"]

    resp_mon = client.post("/api/v1/monitoring", json={
        "repository_id": repo_id,
        "name": "E2E Monitored API",
        "api_spec_url": "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/petstore.json",
        "interval_minutes": 30,
        "is_active": True,
        "auto_repair": False,
        "auto_pr": False
    })
    assert resp_mon.status_code == 200
    mon_data = resp_mon.json()
    assert mon_data["webhook_secret"] is not None

    # 2. Pause and resume
    resp_pause = client.post(f"/api/v1/monitoring/{mon_data['id']}/pause")
    assert resp_pause.status_code == 200
    assert resp_pause.json()["is_active"] is False

    resp_resume = client.post(f"/api/v1/monitoring/{mon_data['id']}/resume")
    assert resp_resume.status_code == 200
    assert resp_resume.json()["is_active"] is True
