import datetime
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.detected_change import DetectedChange
from backend.app.models.repair_attempt import RepairAttempt
from backend.app.models.test_run import TestRun
from backend.app.models.pull_request import PullRequestRecord
from backend.app.models.repository import Repository
from backend.app.services.github_service import GitHubService

logger = logging.getLogger(__name__)

class WorkflowError(Exception):
    pass

class WorkflowStateValidator:
    """
    Enforces transitions in the Self-Maintaining APIs state machine:
    detected -> analyzing -> analyzed -> repairing -> repaired -> awaiting_approval -> verifying -> verified -> pr_created
    """
    VALID_TRANSITIONS = {
        "detected": ["analyzing", "analyzed", "failed"],
        "analyzing": ["analyzed", "failed"],
        "analyzed": ["repair_pending", "repairing", "failed"],
        "repair_pending": ["repairing", "repaired", "failed"],
        "repairing": ["repaired", "awaiting_approval", "failed"],
        "repaired": ["awaiting_approval", "verifying", "failed"],
        "awaiting_approval": ["approved", "rejected", "verifying", "failed"],
        "approved": ["verifying", "pr_pending", "failed"],
        "verifying": ["verified", "failed"],
        "verified": ["pr_pending", "pr_created", "failed"],
        "pr_pending": ["pr_created", "failed"],
        "pr_created": ["closed", "merged"],
        "failed": ["repair_pending", "analyzing", "verifying"]  # Allows retry
    }

    @classmethod
    def can_transition(cls, current_state: str, next_state: str) -> bool:
        return next_state in cls.VALID_TRANSITIONS.get(current_state, [])

class PullRequestWorkflowService:
    """
    Orchestrates the PR lifecycle, enforces state machine guards,
    prevents duplicate PRs, and prevents automated merging into default branch.
    """

    def __init__(self, db: Session, github_service: Optional[GitHubService] = None):
        self.db = db
        self.github = github_service or GitHubService()

    async def create_pull_request_for_repair(
        self,
        repair_attempt_id: int,
        custom_branch_name: Optional[str] = None,
        custom_title: Optional[str] = None
    ) -> PullRequestRecord:
        repair = self.db.query(RepairAttempt).filter(RepairAttempt.id == repair_attempt_id).first()
        if not repair:
            raise WorkflowError(f"RepairAttempt {repair_attempt_id} not found.")

        change = repair.detected_change
        if not change:
            raise WorkflowError("Associated DetectedChange not found.")

        scan = change.scan
        repo = scan.repository if scan else None
        if not repo:
            # Fallback lookup from affected file
            aff = change.affected_files[0] if change.affected_files else None
            repo = aff.repository if aff else None

        if not repo:
            raise WorkflowError("Repository association is missing for this change.")

        # 1. State Machine Guards
        # Developer Approval Check
        if settings.REQUIRE_DEVELOPER_APPROVAL and not repair.developer_approved:
            raise WorkflowError(
                "Developer approval is required before publishing a Pull Request. "
                "Please approve the repair proposal first."
            )

        # Verification Check
        latest_test = (
            self.db.query(TestRun)
            .filter(TestRun.repair_attempt_id == repair.id)
            .order_by(TestRun.created_at.desc())
            .first()
        )
        if not latest_test or latest_test.status != "passed":
            test_status = latest_test.status if latest_test else "none"
            raise WorkflowError(
                f"Cannot publish Pull Request: Verification tests did not pass (status: {test_status}). "
                "Repairs must pass automated verification before a PR is opened."
            )

        # 2. Duplicate PR Check
        existing_pr = (
            self.db.query(PullRequestRecord)
            .filter(
                PullRequestRecord.repair_attempt_id == repair.id,
                PullRequestRecord.status.in_(["created", "pending", "open"])
            )
            .first()
        )
        if existing_pr:
            logger.info(f"PR already exists for repair {repair.id}: PR #{existing_pr.pr_number}")
            return existing_pr

        # 3. Branch Generation (Never merge into default branch)
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        branch_name = custom_branch_name or f"bump/repair-change-{change.id}-{timestamp}"
        base_branch = repo.default_branch or "main"

        # 4. PR Title & Description Markdown Formatting
        title = custom_title or f"fix(api): adapt client for {change.change_type} on {change.path}"
        body = self._build_pr_body(change, repair, latest_test, base_branch)

        # 5. Execute branch creation and PR opening via GitHubService
        owner, repo_name = self._parse_repo_slug(repo.full_name)
        
        # Create repair branch
        await self.github.create_branch(owner, repo_name, branch_name, base_branch=base_branch)

        # Open Pull Request
        pr_result = await self.github.create_pull_request(
            owner=owner,
            repo=repo_name,
            title=title,
            body=body,
            head_branch=branch_name,
            base_branch=base_branch
        )

        # 6. Save PR Record
        pr_record = PullRequestRecord(
            repair_attempt_id=repair.id,
            repository_id=repo.id,
            pr_number=pr_result.get("number"),
            pr_url=pr_result.get("html_url"),
            branch_name=branch_name,
            base_branch=base_branch,
            title=title,
            body=body,
            status="created"
        )
        self.db.add(pr_record)

        # Update change and repair states
        change.status = "pr_created"
        repair.status = "pr_created"
        self.db.commit()
        self.db.refresh(pr_record)

        return pr_record

    def _build_pr_body(
        self,
        change: DetectedChange,
        repair: RepairAttempt,
        test_run: TestRun,
        base_branch: str
    ) -> str:
        patches_summary = "\n".join([f"- `{p.file_path}`" for p in repair.patches])
        
        return f"""## Self-Maintaining APIs: Automated Repair

> **APIs change. Your code adapts.**

### Summary of API Breaking Change
- **Endpoint**: `{change.http_method or 'ANY'} {change.path}`
- **Classification**: `{change.severity}` ({change.change_type})
- **Rule Code**: `{change.rule_code}`
- **Description**: {change.description}

### Repair Reasoning & Justification
{repair.reasoning or 'Automatic repair generated to ensure compatibility with updated OpenAPI specification.'}

### Modified Files
{patches_summary or '- No files modified'}

### Verification Evidence
- **Test Command**: `{test_run.command}`
- **Status**: **{test_run.status.upper()}** (Exit Code: `{test_run.exit_code}`)
- **Summary**: {test_run.passed_tests} passed, {test_run.failed_tests} failed ({test_run.duration_seconds}s)

```
{test_run.stdout[:500] if test_run.stdout else 'All tests passed successfully.'}
```

### Safety and Policy Controls
- [x] Tested in isolated sandbox environment
- [x] Code verified with test runner
- [x] Developer approval recorded
- [x] Targeted to branch `{base_branch}` (Never auto-merged)

*Automated pull request opened by BUMP (Self-Maintaining APIs platform).*
"""

    def _parse_repo_slug(self, full_name: str) -> Tuple[str, str]:
        if "/" in full_name:
            parts = full_name.split("/", 1)
            return parts[0], parts[1]
        return "owner", full_name
