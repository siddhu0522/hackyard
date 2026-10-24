import ast
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class CodeImpactAnalyzer:
    """
    Language-aware code impact analyzer.
    Maps detected OpenAPI changes to client repository source code files,
    functions, exact line ranges, and surrounding context snippets.
    Distinguishes confirmed matches from possible matches deterministically.
    """

    def analyze_repository(
        self,
        repo_files: Dict[str, str],  # rel_path -> file_content
        detected_change: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Scans repo files and returns affected source locations for the given change.
        """
        matches: List[Dict[str, Any]] = []

        path = detected_change.get("path", "")
        http_method = (detected_change.get("http_method") or "").upper()
        change_type = detected_change.get("change_type", "")
        rule_code = detected_change.get("rule_code", "")

        # Extract target property name if response property or parameter change
        target_property = None
        if "PROPERTY" in change_type or "PARAM" in change_type or "ENUM" in change_type:
            desc = detected_change.get("description", "")
            prop_match = re.search(r"'(.*?)'", desc)
            if prop_match:
                target_property = prop_match.group(1)

        for file_path, content in repo_files.items():
            ext = Path(file_path).suffix.lower()
            if ext in [".py"]:
                file_matches = self._analyze_python(file_path, content, path, http_method, change_type, target_property)
                matches.extend(file_matches)
            elif ext in [".ts", ".tsx", ".js", ".jsx"]:
                file_matches = self._analyze_javascript(file_path, content, path, http_method, change_type, target_property)
                matches.extend(file_matches)
            elif ext in [".go", ".java", ".rb", ".cs"]:
                file_matches = self._analyze_generic(file_path, content, path, http_method, change_type, target_property)
                matches.extend(file_matches)

        return matches

    def _analyze_python(
        self,
        file_path: str,
        content: str,
        api_path: str,
        http_method: str,
        change_type: str,
        target_property: Optional[str]
    ) -> List[Dict[str, Any]]:
        matches = []
        lines = content.splitlines()

        try:
            tree = ast.parse(content, filename=file_path)
        except Exception:
            # Fallback to text matching if syntax error in file
            return self._analyze_generic(file_path, content, api_path, http_method, change_type, target_property)

        # Helper to find enclosing function
        def find_enclosing_function(lineno: int) -> Optional[str]:
            candidates = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = node.lineno
                    end = getattr(node, "end_lineno", node.lineno + 1000)
                    if start <= lineno <= end:
                        candidates.append((start, end, node.name))
            if candidates:
                candidates.sort(key=lambda c: (c[1] - c[0]))
                return candidates[0][2]
            return None

        # Check for path match
        path_segments = [seg for seg in api_path.strip("/").split("/") if seg and not seg.startswith("{")]
        clean_path = "/" + "/".join(path_segments)

        for lineno, line in enumerate(lines, start=1):
            has_path = (api_path in line) or (clean_path and clean_path in line)
            has_method = http_method and (
                f".{http_method.lower()}(" in line or
                f'method="{http_method}"' in line or
                f"method='{http_method}'" in line
            )
            has_prop = target_property and (
                f'["{target_property}"]' in line or
                f"['{target_property}']" in line or
                f".{target_property}" in line
            )

            confidence = None
            reason = None

            if change_type == "ENDPOINT_REMOVED":
                if has_path:
                    confidence = "confirmed"
                    reason = f"Explicit reference to removed endpoint '{api_path}'."
            elif change_type == "METHOD_REMOVED":
                if has_path and has_method:
                    confidence = "confirmed"
                    reason = f"Call to removed HTTP method {http_method} on '{api_path}'."
                elif has_path:
                    confidence = "possible"
                    reason = f"References endpoint '{api_path}' where method {http_method} was removed."
            elif "PROPERTY" in change_type:
                if has_prop:
                    # If this file also mentions the endpoint or is in a function related to it
                    if has_path or any(api_path in l for l in lines):
                        confidence = "confirmed"
                        reason = f"Accesses removed/modified response field '{target_property}'."
                    else:
                        confidence = "possible"
                        reason = f"References property '{target_property}' matching modified schema field."
            elif "PARAM" in change_type:
                if has_path:
                    confidence = "confirmed"
                    reason = f"Endpoint call at '{api_path}' missing newly required parameter."

            if confidence:
                func_name = find_enclosing_function(lineno)
                snippet = self._extract_snippet(lines, lineno)
                matches.append({
                    "file_path": file_path,
                    "language": "python",
                    "function_name": func_name or "module-level",
                    "line_start": max(1, lineno - 2),
                    "line_end": min(len(lines), lineno + 2),
                    "match_confidence": confidence,
                    "snippet": snippet,
                    "context_reason": reason
                })

        return self._deduplicate_matches(matches)

    def _analyze_javascript(
        self,
        file_path: str,
        content: str,
        api_path: str,
        http_method: str,
        change_type: str,
        target_property: Optional[str]
    ) -> List[Dict[str, Any]]:
        matches = []
        lines = content.splitlines()

        clean_path = api_path.split("{")[0].rstrip("/")

        for lineno, line in enumerate(lines, start=1):
            has_path = (api_path in line) or (clean_path and clean_path in line)
            has_method = http_method and (
                f".{http_method.lower()}(" in line or
                f"method: '{http_method}'" in line or
                f'method: "{http_method}"' in line or
                f"method: '{http_method.lower()}'" in line
            )
            has_prop = target_property and (
                f".{target_property}" in line or
                f"{target_property}:" in line or
                f"['{target_property}']" in line or
                f'["{target_property}"]' in line
            )

            confidence = None
            reason = None

            if change_type == "ENDPOINT_REMOVED":
                if has_path:
                    confidence = "confirmed"
                    reason = f"JavaScript/TypeScript client calls removed endpoint '{api_path}'."
            elif change_type == "METHOD_REMOVED":
                if has_path and has_method:
                    confidence = "confirmed"
                    reason = f"Call to removed HTTP method {http_method} on '{api_path}'."
                elif has_path:
                    confidence = "possible"
                    reason = f"Calls endpoint '{api_path}' where method {http_method} was removed."
            elif "PROPERTY" in change_type or "ENUM" in change_type:
                if has_prop:
                    if has_path or any(api_path in l for l in lines):
                        confidence = "confirmed"
                        reason = f"Field '{target_property}' referenced in interface or object mapping."
                    else:
                        confidence = "possible"
                        reason = f"Property '{target_property}' matches changed response/enum property."
            elif "PARAM" in change_type:
                if has_path:
                    confidence = "confirmed"
                    reason = f"Call to '{api_path}' needs update for parameter changes."

            if confidence:
                snippet = self._extract_snippet(lines, lineno)
                matches.append({
                    "file_path": file_path,
                    "language": "typescript" if file_path.endswith((".ts", ".tsx")) else "javascript",
                    "function_name": self._guess_js_function(lines, lineno),
                    "line_start": max(1, lineno - 2),
                    "line_end": min(len(lines), lineno + 2),
                    "match_confidence": confidence,
                    "snippet": snippet,
                    "context_reason": reason
                })

        return self._deduplicate_matches(matches)

    def _analyze_generic(
        self,
        file_path: str,
        content: str,
        api_path: str,
        http_method: str,
        change_type: str,
        target_property: Optional[str]
    ) -> List[Dict[str, Any]]:
        matches = []
        lines = content.splitlines()
        clean_path = api_path.split("{")[0].rstrip("/")

        for lineno, line in enumerate(lines, start=1):
            if (api_path in line) or (clean_path and clean_path in line):
                snippet = self._extract_snippet(lines, lineno)
                matches.append({
                    "file_path": file_path,
                    "language": Path(file_path).suffix.strip("."),
                    "function_name": "unknown",
                    "line_start": max(1, lineno - 2),
                    "line_end": min(len(lines), lineno + 2),
                    "match_confidence": "confirmed" if api_path in line else "possible",
                    "snippet": snippet,
                    "context_reason": f"Matches API route '{api_path}'"
                })

        return self._deduplicate_matches(matches)

    def _extract_snippet(self, lines: List[str], target_line: int, radius: int = 3) -> str:
        start = max(0, target_line - 1 - radius)
        end = min(len(lines), target_line + radius)
        formatted = []
        for idx in range(start, end):
            prefix = "-> " if idx == (target_line - 1) else "   "
            formatted.append(f"{prefix}{idx + 1:4d} | {lines[idx]}")
        return "\n".join(formatted)

    def _guess_js_function(self, lines: List[str], target_line: int) -> str:
        for idx in range(target_line - 1, -1, -1):
            line = lines[idx].strip()
            match = re.search(r"(?:function|const|let|async function)\s+([a-zA-Z0-9_$]+)", line)
            if match:
                return match.group(1)
            match_interface = re.search(r"interface\s+([a-zA-Z0-9_$]+)", line)
            if match_interface:
                return f"interface {match_interface.group(1)}"
        return "top-level"

    def _deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped = []
        for m in matches:
            key = (m["file_path"], m["line_start"], m["line_end"], m["match_confidence"])
            if key not in seen:
                seen.add(key)
                deduped.append(m)
        return deduped
