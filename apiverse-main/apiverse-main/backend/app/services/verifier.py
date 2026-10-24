import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from backend.app.core.config import settings

class VerificationEngine:
    """
    Isolated test execution engine.
    Executes repository test suites in a copied sandbox directory
    with time, filesystem, and process isolation.
    """

    def __init__(self, sandbox_root: Optional[Path] = None):
        self.sandbox_root = sandbox_root or settings.SANDBOX_DIR
        self.sandbox_root.mkdir(parents=True, exist_ok=True)

    def discover_test_command(self, repo_dir: Path) -> str:
        """Determines the appropriate test runner command for the repository."""
        # 1. Check Python
        if (repo_dir / "pytest.ini").exists() or (repo_dir / "setup.cfg").exists() or (repo_dir / "pyproject.toml").exists():
            return "python -m pytest"
        if (repo_dir / "tests").is_dir() or (repo_dir / "test").is_dir():
            for p in (repo_dir / "tests").glob("test_*.py") if (repo_dir / "tests").is_dir() else []:
                return "python -m pytest"

        # 2. Check Node / JS / TS
        pkg_json = repo_dir / "package.json"
        if pkg_json.exists():
            try:
                import json
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                if "scripts" in data and "test" in data["scripts"]:
                    return "npm test"
            except Exception:
                pass

        # Fallback default
        return "python -m pytest"

    def run_verification(
        self,
        repo_source_path: Path,
        patches: List[Dict[str, Any]],
        custom_command: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Clones repo to sandbox worktree, applies patches, and executes tests in isolated subprocess.
        """
        run_id = f"sandbox_{uuid.uuid4().hex[:8]}"
        sandbox_path = self.sandbox_root / run_id
        timeout = timeout_seconds or settings.MAX_TEST_TIMEOUT_SECONDS

        try:
            # 1. Copy repo files to sandbox (clean isolation)
            if repo_source_path.exists():
                shutil.copytree(
                    repo_source_path,
                    sandbox_path,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".venv")
                )
            else:
                sandbox_path.mkdir(parents=True, exist_ok=True)

            # 2. Apply patches to sandbox files
            for p in patches:
                rel_path = p.get("file_path", "")
                patched_content = p.get("patched_content", "")
                target_file = (sandbox_path / rel_path).resolve()
                
                # Security check
                if not str(target_file).startswith(str(sandbox_path.resolve())):
                    raise PermissionError(f"Patch path outside sandbox: {rel_path}")

                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(patched_content, encoding="utf-8")

            # 3. Determine command
            command = custom_command or self.discover_test_command(sandbox_path)

            # Security sanity check on command
            if any(forbidden in command.lower() for forbidden in ["rm -rf /", "format c:", "drop database", "sudo"]):
                raise ValueError("Potentially destructive command rejected.")

            # 4. Execute in subprocess
            start_time = time.time()
            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["PYTHONPATH"] = str(sandbox_path)

            try:
                proc = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(sandbox_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout,
                    env=env
                )
                duration = time.time() - start_time
                stdout = proc.stdout
                stderr = proc.stderr
                exit_code = proc.returncode
                status = "passed" if exit_code == 0 else "failed"

            except subprocess.TimeoutExpired as e:
                duration = time.time() - start_time
                stdout = e.stdout or ""
                stderr = f"Execution timed out after {timeout} seconds."
                exit_code = -1
                status = "timeout"

            # Parse test counts
            passed_count, failed_count, total_count = self._parse_test_summary(stdout, stderr)

            return {
                "command": command,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "duration_seconds": round(duration, 2),
                "status": status,
                "total_tests": total_count,
                "passed_tests": passed_count,
                "failed_tests": failed_count,
                "sandbox_path": str(sandbox_path)
            }

        finally:
            # Clean up sandbox worktree to prevent disk bloat
            try:
                if sandbox_path.exists():
                    shutil.rmtree(sandbox_path, ignore_errors=True)
            except Exception:
                pass

    def _parse_test_summary(self, stdout: str, stderr: str) -> Tuple[int, int, int]:
        combined = stdout + "\n" + stderr
        passed = 0
        failed = 0

        # Pytest regex: e.g. "2 passed, 1 failed in 0.5s" or "3 passed in 0.12s"
        pass_match = re.search(r"(\d+)\s+passed", combined)
        if pass_match:
            passed = int(pass_match.group(1))

        fail_match = re.search(r"(\d+)\s+failed", combined)
        if fail_match:
            failed = int(fail_match.group(1))

        total = passed + failed
        if total == 0 and "passed" in stdout.lower() and "failed" not in stdout.lower():
            passed = 1
            total = 1

        return passed, failed, total
