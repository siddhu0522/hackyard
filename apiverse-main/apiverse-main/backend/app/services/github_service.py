import os
import base64
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import httpx

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class GitHubError(Exception):
    pass

class GitHubAuthError(GitHubError):
    pass

class GitHubRateLimitError(GitHubError):
    pass

class GitHubNotFoundError(GitHubError):
    pass

class GitHubService:
    """
    Server-side GitHub integration handling GitHub App tokens and Personal Access Tokens.
    Safely indexes repositories, retrieves source files, branches, and manages Pull Requests.
    Transparently supports isolated local demonstration repositories when configured.
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_ACCESS_TOKEN
        self.api_base = "https://api.github.com"
        self.demo_root = settings.DEMO_REPOS_DIR

    @property
    def is_configured(self) -> bool:
        return bool(self.token)

    def _get_headers(self) -> Dict[str, str]:
        if not self.token:
            raise GitHubAuthError("GitHub token is not configured on the server.")
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Self-Maintaining-APIs-BUMP"
        }

    async def get_status(self) -> Dict[str, Any]:
        """Checks authentication status and API rate limits."""
        if not self.is_configured:
            return {
                "configured": False,
                "authenticated": False,
                "user": None,
                "rate_limit_remaining": None,
                "demo_mode": True,
                "message": "GitHub token not provided. Operating in Local Demonstration Mode."
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.api_base}/user", headers=self._get_headers())
                rate_remaining = resp.headers.get("x-ratelimit-remaining")
                if resp.status_code == 200:
                    user_data = resp.json()
                    return {
                        "configured": True,
                        "authenticated": True,
                        "user": user_data.get("login"),
                        "rate_limit_remaining": int(rate_remaining) if rate_remaining else None,
                        "demo_mode": False,
                        "message": f"Connected as @{user_data.get('login')}"
                    }
                elif resp.status_code == 401:
                    raise GitHubAuthError("GitHub token is invalid or expired.")
                elif resp.status_code == 403:
                    raise GitHubRateLimitError("GitHub API rate limit exceeded or permissions insufficient.")
                else:
                    return {
                        "configured": True,
                        "authenticated": False,
                        "user": None,
                        "rate_limit_remaining": None,
                        "demo_mode": True,
                        "message": f"GitHub API responded with status {resp.status_code}: {resp.text}"
                    }
        except httpx.RequestError as e:
            logger.warning(f"GitHub network check failed: {e}")
            return {
                "configured": True,
                "authenticated": False,
                "user": None,
                "rate_limit_remaining": None,
                "demo_mode": True,
                "message": f"GitHub API unreachable: {str(e)}"
            }

    async def list_repositories(self) -> List[Dict[str, Any]]:
        """Lists authorized repositories from GitHub, falling back to local demo repos if unconfigured."""
        if not self.is_configured:
            return self.list_local_demo_repositories()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.api_base}/user/repos?per_page=100&sort=updated",
                    headers=self._get_headers()
                )
                if resp.status_code == 200:
                    repos = resp.json()
                    return [
                        {
                            "id": r["id"],
                            "name": r["name"],
                            "full_name": r["full_name"],
                            "clone_url": r["clone_url"],
                            "default_branch": r.get("default_branch", "main"),
                            "is_demo": False,
                            "description": r.get("description", ""),
                            "private": r.get("private", False),
                            "updated_at": r.get("updated_at")
                        }
                        for r in repos
                    ]
                elif resp.status_code == 401:
                    raise GitHubAuthError("Invalid GitHub credentials.")
                elif resp.status_code == 403:
                    raise GitHubRateLimitError("GitHub rate limit exceeded.")
                else:
                    raise GitHubError(f"Failed to fetch repositories: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f"Error fetching GitHub repos: {e}. Falling back to demo repositories.")
            return self.list_local_demo_repositories()

    def list_local_demo_repositories(self) -> List[Dict[str, Any]]:
        """Scans local demo directories to provide rich offline demonstration repos."""
        repos = []
        if not self.demo_root.exists():
            return repos

        for item in self.demo_root.iterdir():
            if item.is_dir():
                repos.append({
                    "id": hash(item.name) % 1000000,
                    "name": item.name,
                    "full_name": f"demo/{item.name}",
                    "clone_url": f"file:///{item.resolve()}",
                    "default_branch": "main",
                    "is_demo": True,
                    "description": f"Local demonstration repository ({item.name})",
                    "private": True,
                    "local_path": str(item.resolve())
                })
        return repos

    async def get_repository_tree(self, owner: str, repo: str, branch: str = "main") -> List[Dict[str, Any]]:
        """Retrieves tree of files for the repository."""
        if not self.is_configured:
            return self._get_local_repository_tree(f"{owner}/{repo}")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.api_base}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    tree_data = resp.json()
                    results = []
                    for item in tree_data.get("tree", []):
                        results.append({
                            "path": item["path"],
                            "type": "dir" if item["type"] == "tree" else "file",
                            "size": item.get("size", 0),
                            "sha": item.get("sha")
                        })
                    return results
                elif resp.status_code == 404:
                    raise GitHubNotFoundError(f"Repository {owner}/{repo} or branch {branch} not found.")
                else:
                    raise GitHubError(f"GitHub tree error: {resp.status_code} {resp.text}")
        except Exception:
            return self._get_local_repository_tree(f"{owner}/{repo}")

    def _get_local_repository_tree(self, repo_name: str) -> List[Dict[str, Any]]:
        repo_dir = self._find_local_repo_dir(repo_name)
        if not repo_dir or not repo_dir.exists():
            return []

        tree = []
        for p in repo_dir.rglob("*"):
            if ".git" in p.parts or "__pycache__" in p.parts or "node_modules" in p.parts:
                continue
            rel_path = str(p.relative_to(repo_dir)).replace("\\", "/")
            tree.append({
                "path": rel_path,
                "type": "dir" if p.is_dir() else "file",
                "size": p.stat().st_size if p.is_file() else 0
            })
        return tree

    async def get_file_content(self, owner: str, repo: str, file_path: str, ref: str = "main") -> str:
        """Retrieves raw content of a file."""
        if not self.is_configured:
            return self._get_local_file_content(f"{owner}/{repo}", file_path)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.api_base}/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("encoding") == "base64":
                        return base64.b64decode(data["content"]).decode("utf-8")
                    return data.get("content", "")
                elif resp.status_code == 404:
                    raise GitHubNotFoundError(f"File {file_path} not found in {owner}/{repo}")
                else:
                    raise GitHubError(f"Error reading file: {resp.status_code}")
        except Exception:
            return self._get_local_file_content(f"{owner}/{repo}", file_path)

    def _get_local_file_content(self, repo_name: str, file_path: str) -> str:
        repo_dir = self._find_local_repo_dir(repo_name)
        if not repo_dir:
            raise FileNotFoundError(f"Local repo {repo_name} not found.")
        target_file = (repo_dir / file_path).resolve()
        # Security boundary check: ensure file is inside repo_dir
        if not str(target_file).startswith(str(repo_dir.resolve())):
            raise PermissionError("Access outside repository root is prohibited.")
        if not target_file.exists():
            raise FileNotFoundError(f"File {file_path} does not exist.")
        return target_file.read_text(encoding="utf-8")

    async def create_branch(self, owner: str, repo: str, new_branch: str, base_branch: str = "main") -> str:
        """Creates a new branch on GitHub or locally."""
        if not self.is_configured:
            return f"refs/heads/{new_branch}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            # 1. Get SHA of base_branch
            ref_resp = await client.get(
                f"{self.api_base}/repos/{owner}/{repo}/git/refs/heads/{base_branch}",
                headers=self._get_headers()
            )
            if ref_resp.status_code != 200:
                raise GitHubError(f"Could not find base branch {base_branch}: {ref_resp.text}")
            base_sha = ref_resp.json()["object"]["sha"]

            # 2. Create new branch ref
            create_resp = await client.post(
                f"{self.api_base}/repos/{owner}/{repo}/git/refs",
                headers=self._get_headers(),
                json={"ref": f"refs/heads/{new_branch}", "sha": base_sha}
            )
            if create_resp.status_code in [200, 201]:
                return new_branch
            elif create_resp.status_code == 422:
                # Branch already exists
                return new_branch
            else:
                raise GitHubError(f"Failed to create branch {new_branch}: {create_resp.text}")

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> Dict[str, Any]:
        """Creates a Pull Request on GitHub, or mock PR record in demo mode."""
        if not self.is_configured:
            # Return demo PR record
            import random
            pr_num = random.randint(101, 999)
            return {
                "number": pr_num,
                "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_num}#demo-mode",
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch,
                "state": "open",
                "is_demo": True
            }

        async with httpx.AsyncClient(timeout=20.0) as client:
            url = f"{self.api_base}/repos/{owner}/{repo}/pulls"
            payload = {
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch
            }
            resp = await client.post(url, headers=self._get_headers(), json=payload)
            if resp.status_code in [200, 201]:
                data = resp.json()
                return {
                    "number": data["number"],
                    "html_url": data["html_url"],
                    "title": data["title"],
                    "body": data.get("body", ""),
                    "head": head_branch,
                    "base": base_branch,
                    "state": data.get("state", "open"),
                    "is_demo": False
                }
            elif resp.status_code == 422:
                # Likely already exists
                err_msg = resp.json().get("message", "A pull request already exists for this branch.")
                raise GitHubError(f"GitHub PR creation error (422): {err_msg}")
            else:
                raise GitHubError(f"GitHub PR failed: {resp.status_code} {resp.text}")

    def _find_local_repo_dir(self, repo_name: str) -> Optional[Path]:
        short_name = repo_name.split("/")[-1]
        candidate1 = self.demo_root / short_name
        if candidate1.exists():
            return candidate1
        candidate2 = self.demo_root / repo_name.replace("/", "_")
        if candidate2.exists():
            return candidate2
        return None
