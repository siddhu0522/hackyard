import difflib
import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import httpx

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class RepairProviderError(Exception):
    pass

class MissingApiKeyError(RepairProviderError):
    pass

class BaseRepairProvider(ABC):
    @abstractmethod
    async def generate_repair(
        self,
        change: Dict[str, Any],
        affected_files: List[Dict[str, Any]],
        file_contents: Dict[str, str]
    ) -> Dict[str, Any]:
        """Generates repair explanation, reasoning, risks, and proposed patches."""
        pass

class MockRuleRepairProvider(BaseRepairProvider):
    """
    Deterministic rule-based repair engine.
    Used for local testing, offline demonstration, and predictable repairs.
    """
    async def generate_repair(
        self,
        change: Dict[str, Any],
        affected_files: List[Dict[str, Any]],
        file_contents: Dict[str, str]
    ) -> Dict[str, Any]:
        change_type = change.get("change_type", "")
        path = change.get("path", "")
        http_method = change.get("http_method") or ""
        desc = change.get("description", "")

        explanation = f"The client application is impacted by {change_type} on {path} ({desc})."
        reasoning = "Updating client code to comply with the updated specification contract and guard against null/missing values."
        known_risks = "Verify that downstream consumers do not strictly rely on the deprecated response schema or removed fields."

        patches = []
        for aff in affected_files:
            file_path = aff.get("file_path", "")
            original = file_contents.get(file_path, "")
            if not original:
                continue

            patched = self._apply_deterministic_fix(original, change, aff)
            diff = self._create_unified_diff(file_path, original, patched)
            
            # Validate patch
            is_valid, err = self._validate_patch(file_path, patched)

            patches.append({
                "file_path": file_path,
                "original_content": original,
                "patched_content": patched,
                "unified_diff": diff,
                "is_valid": is_valid,
                "validation_error": err
            })

        return {
            "provider": "mock",
            "model_name": "rule-repair-engine-v1",
            "explanation": explanation,
            "reasoning": reasoning,
            "known_risks": known_risks,
            "patches": patches
        }

    def _apply_deterministic_fix(self, content: str, change: Dict[str, Any], aff: Dict[str, Any]) -> str:
        change_type = change.get("change_type", "")
        path = change.get("path", "")
        desc = change.get("description", "")

        # Extract target property name if response property removed
        prop_match = re.search(r"'(.*?)'", desc)
        target_property = prop_match.group(1) if prop_match else ""

        lines = content.splitlines(keepends=True)
        new_lines = []

        for line in lines:
            modified_line = line
            # 1. Removed response property
            if "PROPERTY" in change_type and target_property:
                if f'item["{target_property}"]' in line:
                    modified_line = line.replace(f'item["{target_property}"]', f'item.get("{target_property}", None)')
                elif f"item['{target_property}']" in line:
                    modified_line = line.replace(f"item['{target_property}']", f'item.get("{target_property}", None)')
                elif f".{target_property}" in line and not line.strip().startswith("//"):
                    if ".ts" in aff.get("file_path", "") or ".js" in aff.get("file_path", ""):
                        modified_line = line.replace(f".{target_property}", f"?.{target_property}")

            # 2. Method removed (e.g. DELETE /v1/items removed)
            elif change_type == "METHOD_REMOVED":
                if f'"{path}"' in line or f"'{path}'" in line:
                    if "delete" in line.lower():
                        modified_line = f"        # Notice: HTTP method removed in API v2\n{line}"

            # 3. Endpoint removed
            elif change_type == "ENDPOINT_REMOVED":
                if path in line:
                    modified_line = line.replace(path, f"{path}  # TODO: endpoint removed in new spec")

            # 4. Required param added
            elif change_type == "REQUIRED_PARAM_ADDED":
                param_name = target_property or "api_token"
                if "params={" in line:
                    modified_line = line.replace("params={", f'params={{"{param_name}": "default_token", ')
                elif ".get(" in line and "params=" not in line:
                    modified_line = line.replace(".get(url)", f'.get(url, params={{"{param_name}": "default_token"}})')

            new_lines.append(modified_line)

        return "".join(new_lines)

    def _create_unified_diff(self, filename: str, original: str, patched: str) -> str:
        diff_lines = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            patched.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}"
        ))
        return "".join(diff_lines) or f"# No modifications required for {filename}"

    def _validate_patch(self, filename: str, content: str) -> Tuple[bool, Optional[str]]:
        if filename.endswith(".py"):
            import ast
            try:
                ast.parse(content, filename=filename)
                return True, None
            except SyntaxError as e:
                return False, f"Python SyntaxError in proposed patch: {str(e)}"
        return True, None

class OpenAIRepairProvider(BaseRepairProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    async def generate_repair(
        self,
        change: Dict[str, Any],
        affected_files: List[Dict[str, Any]],
        file_contents: Dict[str, str]
    ) -> Dict[str, Any]:
        prompt = self._build_prompt(change, affected_files, file_contents)
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an automated code repair agent for API breaking changes. Respond strictly with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
            )
            if resp.status_code != 200:
                raise RepairProviderError(f"OpenAI error ({resp.status_code}): {resp.text}")
            
            data = resp.json()
            raw_content = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_content)
            return self._format_response("openai", self.model, parsed, file_contents)

    def _build_prompt(self, change: Dict[str, Any], affected_files: List[Dict[str, Any]], file_contents: Dict[str, str]) -> str:
        return f"""
Analyze this API breaking change and repair the affected files.
Change: {json.dumps(change, indent=2)}
Affected files: {json.dumps(affected_files, indent=2)}
Source files:
{json.dumps(file_contents, indent=2)}

Return a JSON object with:
- "explanation": string
- "reasoning": string
- "known_risks": string
- "patches": array of objects with "file_path" and "patched_content"
"""

    def _format_response(self, provider: str, model: str, data: Dict[str, Any], original_contents: Dict[str, str]) -> Dict[str, Any]:
        patches = []
        for p in data.get("patches", []):
            file_path = p.get("file_path", "")
            orig = original_contents.get(file_path, "")
            patched = p.get("patched_content", orig)
            diff = "".join(difflib.unified_diff(
                orig.splitlines(keepends=True),
                patched.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}"
            ))
            patches.append({
                "file_path": file_path,
                "original_content": orig,
                "patched_content": patched,
                "unified_diff": diff,
                "is_valid": True,
                "validation_error": None
            })
        return {
            "provider": provider,
            "model_name": model,
            "explanation": data.get("explanation", ""),
            "reasoning": data.get("reasoning", ""),
            "known_risks": data.get("known_risks", ""),
            "patches": patches
        }

class AIRepairService:
    """
    Modular Repair Service managing configurable LLM providers,
    developer approvals, diff validation, and unified patch generation.
    """
    def __init__(self, provider_name: Optional[str] = None):
        self.provider_name = provider_name or settings.LLM_PROVIDER
        self.mock_provider = MockRuleRepairProvider()

    def get_provider(self, requested_provider: Optional[str] = None) -> BaseRepairProvider:
        p_name = requested_provider or self.provider_name

        if p_name == "mock":
            return self.mock_provider
        elif p_name == "openai":
            if not settings.OPENAI_API_KEY:
                raise MissingApiKeyError("OPENAI_API_KEY is not configured in environment or settings.")
            return OpenAIRepairProvider(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
        elif p_name in ["anthropic", "gemini"]:
            # Check key
            key = settings.ANTHROPIC_API_KEY if p_name == "anthropic" else settings.GEMINI_API_KEY
            if not key:
                raise MissingApiKeyError(f"{p_name.upper()}_API_KEY is not configured on the server.")
            # If missing live endpoint, fallback to mock with warning
            return self.mock_provider
        else:
            return self.mock_provider

    async def generate_repair(
        self,
        change: Dict[str, Any],
        affected_files: List[Dict[str, Any]],
        file_contents: Dict[str, str],
        provider_name: Optional[str] = None
    ) -> Dict[str, Any]:
        provider = self.get_provider(provider_name)
        result = await provider.generate_repair(change, affected_files, file_contents)
        
        # Verify repository boundary on all patch file paths
        for p in result.get("patches", []):
            fp = p.get("file_path", "")
            if ".." in fp or fp.startswith("/") or fp.startswith("\\"):
                raise ValueError(f"Path traversal detected in patch file path: {fp}")

        return result
