import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.models.repository import Repository
from backend.app.models.specification import ApiSpecification
from backend.app.models.scan import Scan
from backend.app.models.detected_change import DetectedChange
from backend.app.models.affected_file import AffectedFile
from backend.app.models.repair_attempt import RepairAttempt
from backend.app.models.proposed_patch import ProposedPatch
from backend.app.models.test_run import TestRun
from backend.app.models.pull_request import PullRequestRecord
from backend.app.models.monitoring import (
    MonitoringConfiguration,
    BackgroundJob,
    NotificationRecord
)
from backend.app.services.openapi_diff import OpenAPIDiffEngine
from backend.app.services.code_impact import CodeImpactAnalyzer
from backend.app.services.ai_repair import AIRepairService

logger = logging.getLogger(__name__)

class DatabaseSeeder:
    """
    Comprehensive, safe, and idempotent database seeder for APIVerse.
    Exercises every model, status, filter, parameter, and workflow stage
    without wiping or corrupting existing records.
    """

    @staticmethod
    def _now() -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    def __init__(self, db: Session):
        self.db = db
        self.stats = {
            "inserted": 0,
            "reused": 0,
            "skipped": 0,
            "failed": 0,
            "entities": {}
        }

    def _record_stat(self, entity_name: str, action: str):
        self.stats[action] = self.stats.get(action, 0) + 1
        if entity_name not in self.stats["entities"]:
            self.stats["entities"][entity_name] = {"inserted": 0, "reused": 0, "skipped": 0, "failed": 0}
        self.stats["entities"][entity_name][action] = self.stats["entities"][entity_name].get(action, 0) + 1

    async def seed_all(self) -> Dict[str, Any]:
        """Runs the complete comprehensive fixture seeding sequence."""
        try:
            init_db()

            # 1. Repositories
            repos = self._seed_repositories()

            # 2. API Specifications
            specs = self._seed_specifications()

            # 3. Scans & Detected Changes (Diff Engine execution)
            scans, changes = self._seed_scans_and_changes(repos, specs)

            # 4. Code Impact Analysis (AST engine execution)
            affected_map = self._seed_code_impact(repos, changes)

            # 5. AI Repair Proposals & Patches
            repairs = await self._seed_repairs(changes, affected_map)

            # 6. Test Verifications (Sandbox execution records)
            tests = self._seed_test_runs(repairs, repos)

            # 7. Pull Request Records
            prs = self._seed_pull_requests(repairs, repos, tests)

            # 8. Monitoring Configurations & Background Job Logs
            monitors = self._seed_monitoring_and_jobs(repos)

            # 9. Notifications History
            notifs = self._seed_notifications()

            self.db.commit()

            return {
                "status": "success",
                "message": "APIVerse comprehensive test fixtures successfully synchronized.",
                "stats": self.stats,
                "summary": {
                    "repositories": len(repos),
                    "specifications": len(specs),
                    "scans": len(scans),
                    "changes": len(changes),
                    "repairs": len(repairs),
                    "test_runs": len(tests),
                    "pull_requests": len(prs),
                    "monitors": len(monitors),
                    "notifications": len(notifs)
                }
            }

        except Exception as e:
            self.db.rollback()
            self._record_stat("general", "failed")
            logger.error(f"Seeding failed: {e}", exc_info=True)
            raise e

    def _seed_repositories(self) -> Dict[str, Repository]:
        """Seeds primary, secondary, and integration-test repositories."""
        repo_definitions = [
            {
                "name": "payment-service-py",
                "full_name": "demo/payment-service-py",
                "default_branch": "main",
                "is_demo": True,
                "local_path": str(settings.DEMO_REPOS_DIR / "payment-service-py"),
                "clone_url": f"file:///{settings.DEMO_REPOS_DIR / 'payment-service-py'}"
            },
            {
                "name": "storefront-app-ts",
                "full_name": "demo/storefront-app-ts",
                "default_branch": "main",
                "is_demo": True,
                "local_path": str(settings.DEMO_REPOS_DIR / "storefront-app-ts"),
                "clone_url": f"file:///{settings.DEMO_REPOS_DIR / 'storefront-app-ts'}"
            },
            {
                "name": "apiverse-integration-test",
                "full_name": "demo/apiverse-integration-test",
                "default_branch": "main",
                "is_demo": True,
                "local_path": str(settings.DEMO_REPOS_DIR / "apiverse-integration-test"),
                "clone_url": f"file:///{settings.DEMO_REPOS_DIR / 'apiverse-integration-test'}"
            },
            {
                "name": "cloud-gateway-adapter",
                "full_name": "external/cloud-gateway-adapter",
                "default_branch": "master",
                "is_demo": False,
                "local_path": None,  # Exercises standalone/unindexed edge case
                "clone_url": "https://github.com/external/cloud-gateway-adapter.git"
            }
        ]

        result = {}
        for r_def in repo_definitions:
            existing = self.db.query(Repository).filter(Repository.full_name == r_def["full_name"]).first()
            if existing:
                # Update attributes safely without re-inserting
                existing.local_path = r_def["local_path"]
                existing.clone_url = r_def["clone_url"]
                existing.default_branch = r_def["default_branch"]
                result[r_def["name"]] = existing
                self._record_stat("Repository", "reused")
            else:
                repo = Repository(
                    name=r_def["name"],
                    full_name=r_def["full_name"],
                    clone_url=r_def["clone_url"],
                    default_branch=r_def["default_branch"],
                    is_demo=r_def["is_demo"],
                    local_path=r_def["local_path"]
                )
                self.db.add(repo)
                self.db.flush()
                result[r_def["name"]] = repo
                self._record_stat("Repository", "inserted")

        return result

    def _seed_specifications(self) -> Dict[str, ApiSpecification]:
        """Seeds multiple versioned OpenAPI contracts in JSON and YAML."""
        # 1. Store Payment API
        v1_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Store Payment API", "version": "1.0.0"},
            "paths": {
                "/v1/items": {
                    "get": {
                        "summary": "List store items",
                        "responses": {
                            "200": {
                                "description": "Item list",
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
                                                            "status": {"type": "string", "enum": ["active", "archived", "draft"]}
                                                        },
                                                        "required": ["id", "name", "status"]
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "delete": {
                        "summary": "Delete store item",
                        "parameters": [{"name": "id", "in": "query", "required": True, "schema": {"type": "integer"}}],
                        "responses": {"204": {"description": "Item deleted"}}
                    }
                },
                "/v1/legacy": {
                    "get": {
                        "summary": "Legacy data sync",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }

        v2_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Store Payment API", "version": "2.0.0"},
            "paths": {
                "/v1/items": {
                    "get": {
                        "summary": "List store items v2",
                        "parameters": [
                            {"name": "api_token", "in": "query", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {
                            "200": {
                                "description": "Item list",
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
                                                            "status": {"type": "string", "enum": ["active", "archived"]}
                                                        },
                                                        "required": ["id"]
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

        # 2. Storefront Customer API (YAML format)
        cust_v1_yaml = """
openapi: 3.0.0
info:
  title: Storefront Customer API
  version: 1.1.0
paths:
  /v1/customers:
    get:
      summary: Get customers
      responses:
        '200':
          description: Customer list
          content:
            application/json:
              schema:
                type: object
                properties:
                  customers:
                    type: array
                    items:
                      type: object
                      properties:
                        customer_id: { type: integer }
                        email: { type: string }
                        tier: { type: string, enum: [bronze, silver, gold] }
                      required: [customer_id, email]
  /v1/customers/{id}/phone:
    put:
      summary: Update phone
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: integer }
      responses:
        '200': { description: Phone updated }
"""

        cust_v2_yaml = """
openapi: 3.0.0
info:
  title: Storefront Customer API
  version: 2.0.0
paths:
  /v1/customers:
    get:
      summary: Get customers v2
      parameters:
        - name: organization_id
          in: query
          required: true
          schema: { type: string }
      responses:
        '200':
          description: Customer list
          content:
            application/json:
              schema:
                type: object
                properties:
                  customers:
                    type: array
                    items:
                      type: object
                      properties:
                        customer_id: { type: integer }
                        tier: { type: string, enum: [silver, gold, platinum] }
                      required: [customer_id]
"""

        # 3. Load Integration Test Specs from files
        it_v1_path = settings.DEMO_REPOS_DIR / "apiverse-integration-test" / "openapi_v1.json"
        it_v2_path = settings.DEMO_REPOS_DIR / "apiverse-integration-test" / "openapi_v2.json"

        it_v1_content = it_v1_path.read_text(encoding="utf-8") if it_v1_path.exists() else json.dumps(v1_dict)
        it_v2_content = it_v2_path.read_text(encoding="utf-8") if it_v2_path.exists() else json.dumps(v2_dict)

        engine = OpenAPIDiffEngine()

        spec_specs = [
            ("Store Payment API", "1.0.0", json.dumps(v1_dict), "json", "upload", None),
            ("Store Payment API", "2.0.0", json.dumps(v2_dict), "json", "upload", None),
            ("Storefront Customer API", "1.1.0", json.dumps(engine.parse_spec(cust_v1_yaml, "yaml")), "yaml", "upload", None),
            ("Storefront Customer API", "2.0.0", json.dumps(engine.parse_spec(cust_v2_yaml, "yaml")), "yaml", "upload", None),
            ("APIVerse Integration Test Core API", "1.0.0", it_v1_content, "json", "upload", None),
            ("APIVerse Integration Test Core API", "2.0.0", it_v2_content, "json", "upload", None),
            ("Public Petstore API", "3.0.0", json.dumps({"openapi": "3.0.0", "info": {"title": "Petstore API", "version": "3.0.0"}, "paths": {}}), "json", "url", "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/petstore.json")
        ]

        result = {}
        for name, ver, content, fmt, stype, surl in spec_specs:
            key = f"{name}:{ver}"
            existing = self.db.query(ApiSpecification).filter(
                ApiSpecification.name == name,
                ApiSpecification.version == ver
            ).first()

            if existing:
                existing.content_json = content
                existing.format = fmt
                result[key] = existing
                self._record_stat("ApiSpecification", "reused")
            else:
                spec = ApiSpecification(
                    name=name,
                    version=ver,
                    content_json=content,
                    format=fmt,
                    source_type=stype,
                    source_url=surl
                )
                self.db.add(spec)
                self.db.flush()
                result[key] = spec
                self._record_stat("ApiSpecification", "inserted")

        return result

    def _seed_scans_and_changes(
        self,
        repos: Dict[str, Repository],
        specs: Dict[str, ApiSpecification]
    ) -> Tuple[List[Scan], List[DetectedChange]]:
        """Executes real contract diffs and persists scans and detected changes."""
        engine = OpenAPIDiffEngine()
        scans = []
        all_changes = []

        scan_configurations = [
            # 1. Primary demo scan: payment-service-py with Store Payment API v1 -> v2
            (
                repos["payment-service-py"],
                specs["Store Payment API:1.0.0"],
                specs["Store Payment API:2.0.0"],
                "succeeded",
                None,
                self._now() - datetime.timedelta(hours=2)
            ),
            # 2. Storefront app scan: storefront-app-ts with Customer API v1.1 -> v2
            (
                repos["storefront-app-ts"],
                specs["Storefront Customer API:1.1.0"],
                specs["Storefront Customer API:2.0.0"],
                "succeeded",
                None,
                self._now() - datetime.timedelta(hours=6)
            ),
            # 3. Integration-test fixture scan: apiverse-integration-test v1 -> v2
            (
                repos["apiverse-integration-test"],
                specs["APIVerse Integration Test Core API:1.0.0"],
                specs["APIVerse Integration Test Core API:2.0.0"],
                "succeeded",
                None,
                self._now() - datetime.timedelta(minutes=30)
            ),
            # 4. Historical scan (7 days ago) to exercise date filters
            (
                repos["payment-service-py"],
                specs["Store Payment API:1.0.0"],
                specs["Store Payment API:1.0.0"],
                "succeeded",
                None,
                self._now() - datetime.timedelta(days=7)
            ),
            # 5. Failed scan to exercise error presentation on UI
            (
                repos["cloud-gateway-adapter"],
                specs["Store Payment API:1.0.0"],
                specs["Public Petstore API:3.0.0"],
                "failed",
                "Schema validation failed: Missing remote target schema definitions.",
                self._now() - datetime.timedelta(hours=12)
            )
        ]

        for repo, prev_s, curr_s, status, err_msg, created_ts in scan_configurations:
            existing_scan = self.db.query(Scan).filter(
                Scan.repository_id == repo.id,
                Scan.previous_spec_id == prev_s.id,
                Scan.current_spec_id == curr_s.id,
                Scan.status == status
            ).first()

            if existing_scan:
                scan = existing_scan
                self._record_stat("Scan", "reused")
            else:
                # Calculate real diff changes if not failed
                if status == "succeeded":
                    try:
                        p_dict = json.loads(prev_s.content_json)
                        c_dict = json.loads(curr_s.content_json)
                        diff_results = engine.compare_specs(p_dict, c_dict)
                    except Exception:
                        diff_results = []
                else:
                    diff_results = []

                breaking = [c for c in diff_results if c["severity"] == "BREAKING"]
                warnings = [c for c in diff_results if c["severity"] == "WARNING"]
                infos = [c for c in diff_results if c["severity"] == "INFO"]

                scan = Scan(
                    repository_id=repo.id,
                    previous_spec_id=prev_s.id,
                    current_spec_id=curr_s.id,
                    status=status,
                    total_changes=len(diff_results),
                    breaking_changes=len(breaking),
                    warnings=len(warnings),
                    infos=len(infos),
                    error_message=err_msg,
                    created_at=created_ts,
                    completed_at=created_ts + datetime.timedelta(seconds=2) if status == "succeeded" else None
                )
                self.db.add(scan)
                self.db.flush()
                self._record_stat("Scan", "inserted")

                # Persist detected changes
                for c in diff_results:
                    det = DetectedChange(
                        scan_id=scan.id,
                        change_type=c["change_type"],
                        severity=c["severity"],
                        path=c["path"],
                        http_method=c.get("http_method"),
                        description=c["description"],
                        rule_code=c["rule_code"],
                        old_value=c.get("old_value"),
                        new_value=c.get("new_value"),
                        evidence_json=json.dumps(c.get("evidence", {})),
                        status="detected",
                        created_at=created_ts
                    )
                    self.db.add(det)
                    self._record_stat("DetectedChange", "inserted")

                self.db.flush()

            scans.append(scan)
            all_changes.extend(scan.detected_changes)

        return scans, all_changes

    def _seed_code_impact(
        self,
        repos: Dict[str, Repository],
        changes: List[DetectedChange]
    ) -> Dict[int, List[AffectedFile]]:
        """Maps detected changes to real client source files using AST analysis."""
        analyzer = CodeImpactAnalyzer()
        affected_by_change: Dict[int, List[AffectedFile]] = {}

        for change in changes:
            scan = change.scan
            if not scan or not scan.repository:
                continue

            repo = scan.repository
            existing_affs = self.db.query(AffectedFile).filter(
                AffectedFile.detected_change_id == change.id,
                AffectedFile.repository_id == repo.id
            ).all()

            if existing_affs:
                affected_by_change[change.id] = existing_affs
                self._record_stat("AffectedFile", "reused")
                continue

            # Load repo source files from local disk
            repo_path = Path(repo.local_path) if repo.local_path else (settings.DEMO_REPOS_DIR / repo.name)
            file_contents = {}
            if repo_path.exists():
                for p in repo_path.rglob("*"):
                    if p.is_file() and p.suffix.lower() in [".py", ".ts", ".js"]:
                        rel_path = str(p.relative_to(repo_path)).replace("\\", "/")
                        try:
                            file_contents[rel_path] = p.read_text(encoding="utf-8")
                        except Exception:
                            pass

            if not file_contents:
                continue

            change_dict = {
                "change_type": change.change_type,
                "path": change.path,
                "http_method": change.http_method,
                "description": change.description,
                "rule_code": change.rule_code
            }

            raw_matches = analyzer.analyze_repository(file_contents, change_dict)
            aff_list = []
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
                self.db.add(aff)
                aff_list.append(aff)
                self._record_stat("AffectedFile", "inserted")

            if aff_list:
                change.status = "analyzed"
                self.db.flush()

            affected_by_change[change.id] = aff_list

        return affected_by_change

    async def _seed_repairs(
        self,
        changes: List[DetectedChange],
        affected_map: Dict[int, List[AffectedFile]]
    ) -> List[RepairAttempt]:
        """Synthesizes AI repair proposals with unified diffs and approval states."""
        repair_service = AIRepairService(provider_name="mock")
        repairs = []

        # Find changes that have mapped source code
        actionable_changes = [c for c in changes if c.id in affected_map and affected_map[c.id]]

        for idx, change in enumerate(actionable_changes):
            existing_repair = self.db.query(RepairAttempt).filter(
                RepairAttempt.detected_change_id == change.id
            ).first()

            if existing_repair:
                repairs.append(existing_repair)
                self._record_stat("RepairAttempt", "reused")
                continue

            aff_files = affected_map[change.id]
            repo = aff_files[0].repository
            repo_path = Path(repo.local_path) if repo.local_path else (settings.DEMO_REPOS_DIR / repo.name)

            file_contents = {}
            for aff in aff_files:
                target_f = repo_path / aff.file_path
                if target_f.exists():
                    file_contents[aff.file_path] = target_f.read_text(encoding="utf-8")

            # Determine varied state for this repair
            if idx == 0:
                # Primary verified & approved repair
                status = "approved"
                approved = True
                provider = "mock"
                model_name = "rule-repair-engine-v1"
            elif idx == 1:
                # Awaiting approval state
                status = "awaiting_approval"
                approved = False
                provider = "openai"
                model_name = "gpt-4o"
            elif idx == 2:
                # Rejected repair
                status = "rejected"
                approved = False
                provider = "anthropic"
                model_name = "claude-3-5-sonnet-20241022"
            else:
                # Repaired baseline
                status = "repaired"
                approved = False
                provider = "mock"
                model_name = "rule-engine"

            change_dict = {
                "change_type": change.change_type,
                "path": change.path,
                "description": change.description,
                "http_method": change.http_method
            }
            aff_dict = [
                {"file_path": a.file_path, "language": a.language, "line_start": a.line_start, "line_end": a.line_end}
                for a in aff_files
            ]

            repair_data = await repair_service.generate_repair(change_dict, aff_dict, file_contents)

            repair = RepairAttempt(
                detected_change_id=change.id,
                status=status,
                provider=provider,
                model_name=model_name,
                explanation=repair_data.get("explanation"),
                reasoning=repair_data.get("reasoning"),
                known_risks=repair_data.get("known_risks"),
                developer_approved=approved,
                approved_at=self._now() if approved else None
            )
            self.db.add(repair)
            self.db.flush()
            self._record_stat("RepairAttempt", "inserted")

            for p in repair_data.get("patches", []):
                patch = ProposedPatch(
                    repair_attempt_id=repair.id,
                    file_path=p["file_path"],
                    original_content=p["original_content"],
                    patched_content=p["patched_content"],
                    unified_diff=p["unified_diff"],
                    is_valid=p["is_valid"],
                    validation_error=p.get("validation_error")
                )
                self.db.add(patch)
                self._record_stat("ProposedPatch", "inserted")

            self.db.flush()
            repairs.append(repair)

        return repairs

    def _seed_test_runs(
        self,
        repairs: List[RepairAttempt],
        repos: Dict[str, Repository]
    ) -> List[TestRun]:
        """Seeds sandbox test runs with passed, failed, and timeout records."""
        test_runs = []

        for idx, repair in enumerate(repairs):
            existing_run = self.db.query(TestRun).filter(
                TestRun.repair_attempt_id == repair.id
            ).first()

            if existing_run:
                test_runs.append(existing_run)
                self._record_stat("TestRun", "reused")
                continue

            change = repair.detected_change
            repo = change.affected_files[0].repository if change and change.affected_files else repos["payment-service-py"]

            # Alternate outcomes: passed, failed, timeout
            if idx == 0:
                # Passed verification run
                status = "passed"
                exit_code = 0
                stdout = "test_client.py .. [100%]\n2 passed in 0.45s"
                stderr = ""
                duration = 0.45
                passed_tests = 2
                failed_tests = 0
            elif idx == 1:
                # Failed verification run
                status = "failed"
                exit_code = 1
                stdout = "test_client.py F. [100%]\nFAILURES:\nAssertionError: Expected 200 OK, got 400 Bad Request"
                stderr = "Traceback (most recent call last):\n  File 'test_client.py', line 18, in test_get_order\n    assert order['tracking_number'] is not None"
                duration = 0.82
                passed_tests = 1
                failed_tests = 1
            else:
                # Timeout run
                status = "timeout"
                exit_code = 124
                stdout = "Running integration sandbox tests..."
                stderr = "Process killed: Execution exceeded MAX_TEST_TIMEOUT_SECONDS (45s)"
                duration = 45.0
                passed_tests = 0
                failed_tests = 1

            run = TestRun(
                repair_attempt_id=repair.id,
                repository_id=repo.id,
                command="python -m pytest",
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration,
                status=status,
                total_tests=passed_tests + failed_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests
            )
            self.db.add(run)
            self.db.flush()
            self._record_stat("TestRun", "inserted")
            test_runs.append(run)

        return test_runs

    def _seed_pull_requests(
        self,
        repairs: List[RepairAttempt],
        repos: Dict[str, Repository],
        tests: List[TestRun]
    ) -> List[PullRequestRecord]:
        """Seeds realistic Pull Request workflow records with markdown justifications."""
        prs = []

        # Find approved & verified repairs
        verified_repairs = [r for r in repairs if r.developer_approved and any(t.status == "passed" for t in r.test_runs)]
        if not verified_repairs and repairs:
            verified_repairs = [repairs[0]]

        pr_definitions = [
            (
                verified_repairs[0] if verified_repairs else repairs[0],
                repos["payment-service-py"],
                101,
                "bump/repair-change-1",
                "main",
                "fix(api): adapt client for RESPONSE_PROPERTY_REMOVED on /v1/items",
                "created"
            ),
            (
                verified_repairs[0] if verified_repairs else repairs[0],
                repos["apiverse-integration-test"],
                102,
                "apiverse/repair-tracking-number-2026",
                "main",
                "fix(orders): handle removed tracking_number in GET /v1/orders/{id}",
                "open"
            ),
            (
                verified_repairs[0] if verified_repairs else repairs[0],
                repos["storefront-app-ts"],
                99,
                "bump/repair-customer-tier-99",
                "main",
                "fix(customers): update interface for ENUM_VALUE_REMOVED on /v1/customers",
                "merged"
            )
        ]

        for repair, repo, pr_num, branch, base_branch, title, status in pr_definitions:
            existing_pr = self.db.query(PullRequestRecord).filter(
                PullRequestRecord.branch_name == branch,
                PullRequestRecord.repository_id == repo.id
            ).first()

            if existing_pr:
                prs.append(existing_pr)
                self._record_stat("PullRequestRecord", "reused")
                continue

            change = repair.detected_change
            body = f"""## APIVerse Automated Code Adaptation

> **APIs change. Your code adapts.**

### Summary of Contract Change
- **Endpoint**: `{change.http_method or 'ANY'} {change.path if change else '/v1/items'}`
- **Classification**: `{change.severity if change else 'BREAKING'}`
- **Rule Code**: `{change.rule_code if change else 'BREAKING_PROPERTY_REMOVED'}`

### Repair Justification
{repair.reasoning or 'Automatic repair generated to ensure backward compatibility with updated OpenAPI specification.'}

### Safety Guarantees
- [x] Code verified with automated test suite in sandbox worktree
- [x] Developer approval authorization recorded
- [x] Targeted to `{base_branch}` branch (Never automatically merged)
"""

            pr = PullRequestRecord(
                repair_attempt_id=repair.id,
                repository_id=repo.id,
                pr_number=pr_num,
                pr_url=f"https://github.com/{repo.full_name}/pull/{pr_num}#demo-mode",
                branch_name=branch,
                base_branch=base_branch,
                title=title,
                body=body,
                status=status
            )
            self.db.add(pr)
            self.db.flush()
            self._record_stat("PullRequestRecord", "inserted")
            prs.append(pr)

            if change:
                change.status = "pr_created"

        return prs

    def _seed_monitoring_and_jobs(self, repos: Dict[str, Repository]) -> List[MonitoringConfiguration]:
        """Seeds active and paused monitoring configurations and background job execution logs."""
        configs = []

        mon_defs = [
            (
                repos["payment-service-py"],
                "Payment API Gateway Poller",
                "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/petstore.json",
                "0 */6 * * *",
                60,
                True,
                "hmac-secret-demo-payment-12345"
            ),
            (
                repos["apiverse-integration-test"],
                "Integration Test Core Contract Monitor",
                "https://api.integration-test.example.com/openapi.json",
                None,
                15,
                True,
                "hmac-secret-demo-integration-67890"
            ),
            (
                repos["storefront-app-ts"],
                "Legacy Storefront Weekly Audit",
                "https://api.store.example.com/v1/openapi.yaml",
                "0 0 * * 0",
                1440,
                False,  # Paused state
                "hmac-secret-demo-storefront-99999"
            )
        ]

        for repo, name, url, cron, interval, active, secret in mon_defs:
            existing = self.db.query(MonitoringConfiguration).filter(
                MonitoringConfiguration.name == name,
                MonitoringConfiguration.repository_id == repo.id
            ).first()

            if existing:
                config = existing
                self._record_stat("MonitoringConfiguration", "reused")
            else:
                config = MonitoringConfiguration(
                    repository_id=repo.id,
                    name=name,
                    api_spec_url=url,
                    schedule_cron=cron,
                    interval_minutes=interval,
                    is_active=active,
                    webhook_secret=secret,
                    last_run_at=self._now() - datetime.timedelta(minutes=45) if active else None
                )
                self.db.add(config)
                self.db.flush()
                self._record_stat("MonitoringConfiguration", "inserted")

                # Add sample background jobs
                job1 = BackgroundJob(
                    monitoring_id=config.id,
                    job_type="scan",
                    status="succeeded",
                    started_at=self._now() - datetime.timedelta(minutes=45),
                    finished_at=self._now() - datetime.timedelta(minutes=44),
                    logs=f"Fetched {url}\nComputed diff: 0 breaking changes detected.\nAll specifications synchronized."
                )
                self.db.add(job1)
                self._record_stat("BackgroundJob", "inserted")

                if not active:
                    job2 = BackgroundJob(
                        monitoring_id=config.id,
                        job_type="sync",
                        status="failed",
                        started_at=self._now() - datetime.timedelta(days=1),
                        finished_at=self._now() - datetime.timedelta(days=1),
                        logs="Connecting to remote spec server...\nConnection refused (HTTP 503 Service Unavailable).",
                        error_message="HTTP 503: Service Unavailable"
                    )
                    self.db.add(job2)
                    self._record_stat("BackgroundJob", "inserted")

            configs.append(config)

        return configs

    def _seed_notifications(self) -> List[NotificationRecord]:
        """Seeds notifications across varied severities and read/unread states."""
        notifs = []
        notif_defs = [
            (
                "BREAKING_CHANGE_DETECTED",
                "Breaking Contract Changes Detected",
                "Scan on 'payment-service-py' detected 9 breaking changes in OpenAPI contract.",
                "error",
                False,
                self._now() - datetime.timedelta(minutes=25)
            ),
            (
                "REPAIR_PROPOSED",
                "AI Repair Synthesized",
                "Automated repair patch synthesized for RESPONSE_PROPERTY_REMOVED on /v1/items.",
                "info",
                False,
                self._now() - datetime.timedelta(minutes=20)
            ),
            (
                "TEST_FAILED",
                "Sandbox Verification Alert",
                "Test run failed in isolated sandbox for repair #2 (AssertionError).",
                "warning",
                True,
                self._now() - datetime.timedelta(hours=1)
            ),
            (
                "PR_CREATED",
                "Pull Request Published",
                "Pull Request #102 opened on branch 'apiverse/repair-tracking-number-2026'.",
                "success",
                True,
                self._now() - datetime.timedelta(hours=2)
            )
        ]

        for etype, title, msg, sev, is_read, created_at in notif_defs:
            existing = self.db.query(NotificationRecord).filter(
                NotificationRecord.title == title,
                NotificationRecord.event_type == etype
            ).first()

            if existing:
                notifs.append(existing)
                self._record_stat("NotificationRecord", "reused")
            else:
                notif = NotificationRecord(
                    event_type=etype,
                    title=title,
                    message=msg,
                    severity=sev,
                    is_read=is_read,
                    created_at=created_at
                )
                self.db.add(notif)
                self.db.flush()
                self._record_stat("NotificationRecord", "inserted")
                notifs.append(notif)

        return notifs
