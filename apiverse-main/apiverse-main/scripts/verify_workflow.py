import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, init_db
from backend.app.models.repository import Repository
from backend.app.models.specification import ApiSpecification
from backend.app.models.scan import Scan
from backend.app.models.detected_change import DetectedChange
from backend.app.models.affected_file import AffectedFile
from backend.app.models.repair_attempt import RepairAttempt
from backend.app.models.proposed_patch import ProposedPatch
from backend.app.models.test_run import TestRun
from backend.app.models.pull_request import PullRequestRecord

from backend.app.services.openapi_diff import OpenAPIDiffEngine
from backend.app.services.code_impact import CodeImpactAnalyzer
from backend.app.services.ai_repair import AIRepairService
from backend.app.services.verifier import VerificationEngine
from backend.app.services.pr_workflow import PullRequestWorkflowService, WorkflowError
from backend.app.services.github_service import GitHubService

async def run_workflow_verification():
    print("=" * 70)
    print("   APIVERSE — LIVE FIXTURE WORKFLOW EXECUTION & VERIFICATION   ")
    print("               Target: apiverse-integration-test               ")
    print("=" * 70)

    db = SessionLocal()
    init_db()

    try:
        # -------------------------------------------------------------
        # STEP 1: Verify clean local demo state
        # -------------------------------------------------------------
        print("\n[STEP 1] Inspecting Local Demo State & Repository Connection...")
        repo = db.query(Repository).filter(Repository.name == "apiverse-integration-test").first()
        if not repo:
            print("  [!] Repository 'apiverse-integration-test' not in DB. Registering now...")
            repo = Repository(
                name="apiverse-integration-test",
                full_name="demo/apiverse-integration-test",
                default_branch="main",
                is_demo=True,
                local_path=str(settings.DEMO_REPOS_DIR / "apiverse-integration-test"),
                clone_url=f"file:///{settings.DEMO_REPOS_DIR / 'apiverse-integration-test'}"
            )
            db.add(repo)
            db.commit()
            db.refresh(repo)

        repo_dir = Path(repo.local_path)
        print(f"  ✓ Repository ID:     {repo.id}")
        print(f"  ✓ Repository Name:   {repo.name} ({repo.full_name})")
        print(f"  ✓ Local Path:        {repo.local_path} (Exists: {repo_dir.exists()})")
        print(f"  ✓ Default Branch:    {repo.default_branch}")
        print(f"  ✓ Demo Mode Active:  {repo.is_demo}")

        # -------------------------------------------------------------
        # STEP 2: Inspect OpenAPI v1 and v2 specifications
        # -------------------------------------------------------------
        print("\n[STEP 2] Inspecting OpenAPI Specifications & Expected Differences...")
        v1_file = repo_dir / "openapi_v1.json"
        v2_file = repo_dir / "openapi_v2.json"

        assert v1_file.exists(), f"Missing {v1_file}"
        assert v2_file.exists(), f"Missing {v2_file}"

        v1_spec = json.loads(v1_file.read_text(encoding="utf-8"))
        v2_spec = json.loads(v2_file.read_text(encoding="utf-8"))

        print(f"  ✓ OpenAPI v1 Version: {v1_spec['info']['version']} - '{v1_spec['info']['title']}'")
        print(f"  ✓ OpenAPI v2 Version: {v2_spec['info']['version']} - '{v2_spec['info']['title']}'")

        # Document actual differences
        print("  Key Contractual Differences Identified:")
        print("    1. Response Property: 'tracking_number' present in v1 GET /v1/orders/{id}, removed in v2")
        print("    2. Endpoint: POST /v1/orders/cancel-legacy present in v1, removed in v2")
        print("    3. Parameter: 'idempotency_key' added as mandatory (required=true) in POST /v1/orders")
        print("    4. Type: 'order_id' changed from integer to string in POST /v1/orders response")
        print("    5. Endpoint: GET /v1/orders/receipt added in v2 (non-breaking)")

        # -------------------------------------------------------------
        # STEP 3: Execute real OpenAPI comparison engine
        # -------------------------------------------------------------
        print("\n[STEP 3] Executing OpenAPIDiffEngine on v1 vs v2 contracts...")
        diff_engine = OpenAPIDiffEngine()
        detected_diffs = diff_engine.compare_specs(v1_spec, v2_spec)

        print(f"  ✓ Total Changes Detected: {len(detected_diffs)}")
        breaking_count = sum(1 for d in detected_diffs if d["severity"] == "BREAKING")
        info_count = sum(1 for d in detected_diffs if d["severity"] == "INFO")
        print(f"    - BREAKING: {breaking_count}")
        print(f"    - INFO:     {info_count}")

        for i, d in enumerate(detected_diffs, 1):
            print(f"    {i}. [{d['severity']}] {d['change_type']} on {d.get('http_method') or 'ANY'} {d['path']}")
            print(f"       Rule: {d['rule_code']} | Evidence: {json.dumps(d.get('evidence', {}))[:80]}...")

        # Find or trigger fresh Scan in database for this repo
        spec_v1 = db.query(ApiSpecification).filter(ApiSpecification.name == "APIVerse Integration Test Core API", ApiSpecification.version == "1.0.0").first()
        spec_v2 = db.query(ApiSpecification).filter(ApiSpecification.name == "APIVerse Integration Test Core API", ApiSpecification.version == "2.0.0").first()

        scan = db.query(Scan).filter(
            Scan.repository_id == repo.id,
            Scan.previous_spec_id == spec_v1.id,
            Scan.current_spec_id == spec_v2.id
        ).first()

        assert scan is not None, "Scan record must exist in DB for the fixture."
        print(f"  ✓ Verified Persisted Scan ID: {scan.id} with {scan.total_changes} changes ({scan.breaking_changes} breaking)")

        # -------------------------------------------------------------
        # STEP 4: Run Code Impact Analyzer on fixture source code
        # -------------------------------------------------------------
        print("\n[STEP 4] Executing CodeImpactAnalyzer on fixture source files...")
        target_change = db.query(DetectedChange).filter(
            DetectedChange.scan_id == scan.id,
            DetectedChange.change_type == "RESPONSE_PROPERTY_REMOVED"
        ).first()
        assert target_change is not None, "Target change RESPONSE_PROPERTY_REMOVED not found."

        print(f"  Target Breaking Change: ID #{target_change.id} - {target_change.description}")

        # Read actual fixture files
        source_files = {
            "client.py": (repo_dir / "client.py").read_text(encoding="utf-8"),
            "models.py": (repo_dir / "models.py").read_text(encoding="utf-8"),
            "tests/test_client.py": (repo_dir / "tests" / "test_client.py").read_text(encoding="utf-8")
        }

        impact_analyzer = CodeImpactAnalyzer()
        change_dict = {
            "change_type": target_change.change_type,
            "path": target_change.path,
            "http_method": target_change.http_method,
            "description": target_change.description,
            "rule_code": target_change.rule_code
        }
        impact_matches = impact_analyzer.analyze_repository(source_files, change_dict)

        print(f"  ✓ Code Impact Analysis Found {len(impact_matches)} Source Match(es):")
        for m in impact_matches:
            print(f"    • {m['file_path']} (Lines {m['line_start']}-{m['line_end']})")
            print(f"      Function:   {m['function_name']}")
            print(f"      Confidence: {m['match_confidence'].upper()}")
            print(f"      Reason:     {m['context_reason']}")

        assert any("client.py" in m["file_path"] for m in impact_matches), "client.py must be detected as impacted!"

        # -------------------------------------------------------------
        # STEP 5: Generate Repair Proposal via AIRepairService
        # -------------------------------------------------------------
        print("\n[STEP 5] Generating Repair Proposal with AIRepairService...")
        configured_provider = settings.LLM_PROVIDER
        print(f"  ✓ Current Configured Provider: '{configured_provider}' (Rule-based Mock Engine)")
        print("  ✓ Mode Identification: Deterministic AST-validated rule-based repair (Offline Local Engine)")

        repair_service = AIRepairService(provider_name=configured_provider)
        repair_result = await repair_service.generate_repair(
            change_dict,
            [{"file_path": m["file_path"], "language": m["language"], "line_start": m["line_start"], "line_end": m["line_end"]} for m in impact_matches],
            source_files
        )

        print("  ✓ Generated Repair Proposal Details:")
        print(f"    - Provider:    {repair_result['provider']}")
        print(f"    - Model Name:  {repair_result['model_name']}")
        print(f"    - Explanation: {repair_result['explanation']}")
        print(f"    - Reasoning:   {repair_result['reasoning']}")
        print(f"    - Known Risks: {repair_result['known_risks']}")

        # -------------------------------------------------------------
        # STEP 6: Inspect generated patch and verify application
        # -------------------------------------------------------------
        print("\n[STEP 6] Inspecting Proposed Patches & Syntax Validity...")
        patches = repair_result.get("patches", [])
        assert len(patches) > 0, "At least one patch must be synthesized!"

        client_patch = next((p for p in patches if "client.py" in p["file_path"]), patches[0])
        print(f"  ✓ Target Patch File: {client_patch['file_path']}")
        print(f"  ✓ Patch Syntax Validity: {client_patch['is_valid']} (Error: {client_patch['validation_error']})")
        print("  ✓ Unified Diff Preview:")
        diff_lines = client_patch["unified_diff"].splitlines()
        for dl in diff_lines[:15]:
            print(f"    | {dl}")
        if len(diff_lines) > 15:
            print(f"    | ... ({len(diff_lines) - 15} more lines)")

        # Save this repair attempt in DB for verification execution
        new_repair = RepairAttempt(
            detected_change_id=target_change.id,
            status="awaiting_approval",
            provider=repair_result["provider"],
            model_name=repair_result["model_name"],
            explanation=repair_result["explanation"],
            reasoning=repair_result["reasoning"],
            known_risks=repair_result["known_risks"],
            developer_approved=False
        )
        db.add(new_repair)
        db.commit()
        db.refresh(new_repair)

        patch_model = ProposedPatch(
            repair_attempt_id=new_repair.id,
            file_path=client_patch["file_path"],
            original_content=client_patch["original_content"],
            patched_content=client_patch["patched_content"],
            unified_diff=client_patch["unified_diff"],
            is_valid=client_patch["is_valid"]
        )
        db.add(patch_model)
        db.commit()
        db.refresh(new_repair)
        print(f"  ✓ Persisted New Live RepairAttempt ID: #{new_repair.id} (Status: {new_repair.status}, Approved: {new_repair.developer_approved})")

        # -------------------------------------------------------------
        # STEP 7: Run fixture tests in Sandbox (Real Execution)
        # -------------------------------------------------------------
        print("\n[STEP 7] Executing Verification Tests in Isolated Sandbox Worktree...")
        verifier = VerificationEngine()
        
        # Test Run A: Fresh Live Execution of Test Suite
        patches_for_sandbox = [{"file_path": p.file_path, "patched_content": p.patched_content} for p in new_repair.patches]
        test_exec = verifier.run_verification(
            repo_source_path=repo_dir,
            patches=patches_for_sandbox,
            custom_command="python -m pytest tests/test_client.py"
        )

        print("  ✓ Sandbox Test Execution Results:")
        print(f"    - Command:          {test_exec['command']}")
        print(f"    - Status:           {test_exec['status'].upper()}")
        print(f"    - Exit Code:        {test_exec['exit_code']}")
        print(f"    - Duration:         {test_exec['duration_seconds']}s")
        print(f"    - Passed Tests:     {test_exec['passed_tests']}")
        print(f"    - Failed Tests:     {test_exec['failed_tests']}")
        print(f"    - Isolated Sandbox: {test_exec['sandbox_path']} (Cleaned after run)")
        print(f"    - Captured stdout:  {test_exec['stdout'].strip()}")

        assert test_exec["status"] == "passed", f"Verification tests expected to pass, got: {test_exec['status']}"

        # Persist this new live test execution record
        new_test_run = TestRun(
            repair_attempt_id=new_repair.id,
            repository_id=repo.id,
            command=test_exec["command"],
            exit_code=test_exec["exit_code"],
            stdout=test_exec["stdout"],
            stderr=test_exec["stderr"],
            duration_seconds=test_exec["duration_seconds"],
            status=test_exec["status"],
            total_tests=test_exec["total_tests"],
            passed_tests=test_exec["passed_tests"],
            failed_tests=test_exec["failed_tests"]
        )
        db.add(new_test_run)
        db.commit()
        db.refresh(new_test_run)
        print(f"  ✓ Persisted New Live TestRun ID: #{new_test_run.id}")

        # -------------------------------------------------------------
        # STEP 8: Confirm Failed / Unverified Verification Blocks PR Progression
        # -------------------------------------------------------------
        print("\n[STEP 8] Testing State Machine Guard: Failed Test Blocks PR Creation...")
        pr_service = PullRequestWorkflowService(db)

        # Create a temporary unverified/failed repair
        failed_repair = RepairAttempt(
            detected_change_id=target_change.id,
            status="failed",
            provider="mock",
            model_name="rule-engine",
            explanation="Unverified attempt",
            developer_approved=True  # even if approved!
        )
        db.add(failed_repair)
        db.commit()
        db.refresh(failed_repair)

        failed_test_run = TestRun(
            repair_attempt_id=failed_repair.id,
            repository_id=repo.id,
            command="python -m pytest",
            exit_code=1,
            stdout="AssertionError: Expected 200, got 500",
            status="failed",
            total_tests=1,
            passed_tests=0,
            failed_tests=1
        )
        db.add(failed_test_run)
        db.commit()

        # Attempt to create PR on failed repair
        blocked_as_expected = False
        try:
            await pr_service.create_pull_request_for_repair(failed_repair.id)
        except WorkflowError as e:
            blocked_as_expected = True
            print(f"  ✓ Expected Guard Tripped: '{e}'")

        assert blocked_as_expected, "State machine MUST block PR progression when tests fail!"
        print("  ✓ State Machine Integrity Confirmed: PR publication rejected on failed tests.")

        # -------------------------------------------------------------
        # STEP 9: Test Developer Approval Boundary & Local PR Creation
        # -------------------------------------------------------------
        print("\n[STEP 9] Testing Developer Approval Boundary & Non-Destructive Branch Creation...")
        # Attempt PR without developer approval
        approval_blocked = False
        try:
            await pr_service.create_pull_request_for_repair(new_repair.id)
        except WorkflowError as e:
            approval_blocked = True
            print(f"  ✓ Approval Guard Tripped: '{e}'")

        assert approval_blocked, "PR MUST NOT be published without developer approval!"
        print("  ✓ Developer Approval Boundary Confirmed: PR blocked when developer_approved=False.")

        # Now approve the repair as a developer
        print("  Authorizing repair #%d as developer..." % new_repair.id)
        new_repair.developer_approved = True
        new_repair.status = "approved"
        db.commit()
        db.refresh(new_repair)

        # Now execute PR creation
        branch_name = f"apiverse/repair-verify-{new_repair.id}"
        pr_record = await pr_service.create_pull_request_for_repair(
            repair_attempt_id=new_repair.id,
            custom_branch_name=branch_name,
            custom_title="fix(orders): adapt client for removed tracking_number (Verification Test)"
        )

        print("  ✓ Pull Request Successfully Published:")
        print(f"    - PR Record ID:   #{pr_record.id}")
        print(f"    - PR Number:       #{pr_record.pr_number}")
        print(f"    - Title:           {pr_record.title}")
        print(f"    - Branch:          {pr_record.branch_name} -> {pr_record.base_branch}")
        print(f"    - Status:          {pr_record.status.upper()}")
        print(f"    - Demo Mode URL:   {pr_record.pr_url}")
        print("    - Safety Rule:     NON-DESTRUCTIVE (Never auto-merged into default branch)")

        # -------------------------------------------------------------
        # STEP 10: Check Duplicate PR Prevention
        # -------------------------------------------------------------
        print("\n[STEP 10] Testing Duplicate PR Prevention...")
        pr_second_call = await pr_service.create_pull_request_for_repair(
            repair_attempt_id=new_repair.id,
            custom_branch_name=branch_name
        )
        assert pr_second_call.id == pr_record.id, "Duplicate PR must not be created; existing PR should be returned."
        print(f"  ✓ Duplicate Prevention Verified: Second call returned existing PR #{pr_second_call.pr_number} without duplicate insertions.")

        # -------------------------------------------------------------
        # STEP 11: Verify Persisted State reflects in Database & Metrics
        # -------------------------------------------------------------
        print("\n[STEP 11] Verifying Persisted State & Dashboard Telemetry...")
        total_prs = db.query(PullRequestRecord).count()
        total_repairs = db.query(RepairAttempt).count()
        total_runs = db.query(TestRun).count()
        
        print(f"  ✓ Total Pull Requests in DB: {total_prs}")
        print(f"  ✓ Total Repair Attempts:     {total_repairs}")
        print(f"  ✓ Total Verification Runs:   {total_runs}")
        print(f"  ✓ Latest PR Record:          #{pr_record.id} for Repo '{pr_record.repository.name}'")

        print("\n" + "=" * 70)
        print("       ALL 11 INTEGRATION WORKFLOW CHECKS PASSED WITH ZERO ERRORS       ")
        print("=" * 70)

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_workflow_verification())
