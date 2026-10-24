import json
import yaml
from typing import Dict, Any, List, Optional, Tuple

class OpenAPIDiffEngine:
    """
    Deterministic OpenAPI 3.0 / 3.1 specification comparison engine.
    Detects breaking, warning, and informational changes with rigorous JSON-pointer evidence.
    """

    @staticmethod
    def parse_spec(content: str, fmt: str = "json") -> Dict[str, Any]:
        """Parses a JSON or YAML string into a Python dict."""
        content = content.strip()
        if fmt == "yaml" or (not content.startswith("{") and not content.startswith("[")):
            try:
                parsed = yaml.safe_load(content)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
        
        # Default try json
        try:
            return json.loads(content)
        except Exception as e:
            try:
                parsed = yaml.safe_load(content)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                raise ValueError(f"Failed to parse specification as JSON or YAML: {str(e)}")

    def compare_specs(self, old_spec: Dict[str, Any], new_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Runs deterministic diff rules between old_spec and new_spec.
        Returns a list of structured change dicts.
        """
        changes: List[Dict[str, Any]] = []

        old_paths = old_spec.get("paths", {}) or {}
        new_paths = new_spec.get("paths", {}) or {}

        # 1. Compare Paths
        for path, old_path_item in old_paths.items():
            if path not in new_paths:
                changes.append({
                    "change_type": "ENDPOINT_REMOVED",
                    "severity": "BREAKING",
                    "path": path,
                    "http_method": None,
                    "description": f"Endpoint '{path}' was removed completely from the API specification.",
                    "rule_code": "BREAK_PATH_REMOVED",
                    "old_value": json.dumps(list(old_path_item.keys())),
                    "new_value": None,
                    "evidence": {
                        "json_pointer": f"/paths/{path}",
                        "explanation": f"The entire route '{path}' has been deleted. Any client calling this endpoint will receive HTTP 404.",
                        "rule_name": "Endpoint Removal Rule",
                        "impact_summary": f"Clients calling {path} will fail."
                    }
                })
                continue

            new_path_item = new_paths[path] or {}
            self._compare_path_item(path, old_path_item, new_path_item, changes)

        # Check for newly added paths (INFO)
        for path, new_path_item in new_paths.items():
            if path not in old_paths:
                changes.append({
                    "change_type": "ENDPOINT_ADDED",
                    "severity": "INFO",
                    "path": path,
                    "http_method": None,
                    "description": f"New endpoint '{path}' was added to the API specification.",
                    "rule_code": "INFO_PATH_ADDED",
                    "old_value": None,
                    "new_value": json.dumps(list(new_path_item.keys())),
                    "evidence": {
                        "json_pointer": f"/paths/{path}",
                        "explanation": f"A new endpoint '{path}' is now available for integration.",
                        "rule_name": "Endpoint Addition Rule",
                        "impact_summary": f"New capability available at {path}."
                    }
                })

        return changes

    def _compare_path_item(self, path: str, old_item: Dict[str, Any], new_item: Dict[str, Any], changes: List[Dict[str, Any]]):
        http_methods = ["get", "post", "put", "delete", "patch", "options", "head"]

        for method in http_methods:
            if method in old_item and method not in new_item:
                changes.append({
                    "change_type": "METHOD_REMOVED",
                    "severity": "BREAKING",
                    "path": path,
                    "http_method": method.upper(),
                    "description": f"HTTP method {method.upper()} was removed from endpoint '{path}'.",
                    "rule_code": "BREAK_METHOD_REMOVED",
                    "old_value": f"{method.upper()} {path}",
                    "new_value": None,
                    "evidence": {
                        "json_pointer": f"/paths/{path}/{method}",
                        "explanation": f"The HTTP {method.upper()} operation was removed from {path}. Calls will receive HTTP 405 Method Not Allowed.",
                        "rule_name": "HTTP Method Removal Rule",
                        "impact_summary": f"Method {method.upper()} no longer supported."
                    }
                })
            elif method in new_item and method not in old_item:
                changes.append({
                    "change_type": "METHOD_ADDED",
                    "severity": "INFO",
                    "path": path,
                    "http_method": method.upper(),
                    "description": f"HTTP method {method.upper()} was added to endpoint '{path}'.",
                    "rule_code": "INFO_METHOD_ADDED",
                    "old_value": None,
                    "new_value": f"{method.upper()} {path}",
                    "evidence": {
                        "json_pointer": f"/paths/{path}/{method}",
                        "explanation": f"The HTTP {method.upper()} operation was newly added to {path}.",
                        "rule_name": "HTTP Method Addition Rule",
                        "impact_summary": f"Method {method.upper()} is now supported."
                    }
                })
            elif method in old_item and method in new_item:
                self._compare_operation(path, method.upper(), old_item[method], new_item[method], changes)

    def _compare_operation(self, path: str, method: str, old_op: Dict[str, Any], new_op: Dict[str, Any], changes: List[Dict[str, Any]]):
        # 1. Deprecation warning
        if not old_op.get("deprecated") and new_op.get("deprecated"):
            changes.append({
                "change_type": "OPERATION_DEPRECATED",
                "severity": "WARNING",
                "path": path,
                "http_method": method,
                "description": f"Operation {method} '{path}' has been marked as deprecated.",
                "rule_code": "WARN_DEPRECATED",
                "old_value": "deprecated: false",
                "new_value": "deprecated: true",
                "evidence": {
                    "json_pointer": f"/paths/{path}/{method.lower()}/deprecated",
                    "explanation": "Operation is deprecated and may be removed in future versions.",
                    "rule_name": "Deprecation Rule",
                    "impact_summary": "Plan migration away from deprecated operation."
                }
            })

        # 2. Parameters
        self._compare_parameters(path, method, old_op.get("parameters", []) or [], new_op.get("parameters", []) or [], changes)

        # 3. Request Body
        self._compare_request_body(path, method, old_op.get("requestBody", {}), new_op.get("requestBody", {}), changes)

        # 4. Responses
        self._compare_responses(path, method, old_op.get("responses", {}), new_op.get("responses", {}), changes)

    def _compare_parameters(self, path: str, method: str, old_params: List[Dict[str, Any]], new_params: List[Dict[str, Any]], changes: List[Dict[str, Any]]):
        old_param_map = {f"{p.get('in', '')}:{p.get('name', '')}": p for p in old_params if isinstance(p, dict)}
        new_param_map = {f"{p.get('in', '')}:{p.get('name', '')}": p for p in new_params if isinstance(p, dict)}

        for key, old_p in old_param_map.items():
            param_in, param_name = key.split(":", 1)
            if key not in new_param_map:
                changes.append({
                    "change_type": "PARAM_REMOVED",
                    "severity": "BREAKING" if old_p.get("required") else "WARNING",
                    "path": path,
                    "http_method": method,
                    "description": f"Parameter '{param_name}' (in: {param_in}) was removed from {method} {path}.",
                    "rule_code": "BREAK_PARAM_REMOVED" if old_p.get("required") else "WARN_PARAM_REMOVED",
                    "old_value": json.dumps(old_p),
                    "new_value": None,
                    "evidence": {
                        "json_pointer": f"/paths/{path}/{method.lower()}/parameters/{param_name}",
                        "explanation": f"Parameter {param_name} in {param_in} was removed.",
                        "rule_name": "Parameter Removal Rule",
                        "impact_summary": f"Parameter {param_name} will be ignored or rejected."
                    }
                })
            else:
                new_p = new_param_map[key]
                # Check if changed to required
                if not old_p.get("required", False) and new_p.get("required", False):
                    changes.append({
                        "change_type": "PARAM_BECAME_REQUIRED",
                        "severity": "BREAKING",
                        "path": path,
                        "http_method": method,
                        "description": f"Existing parameter '{param_name}' became required in {method} {path}.",
                        "rule_code": "BREAK_PARAM_BECAME_REQ",
                        "old_value": "required: false",
                        "new_value": "required: true",
                        "evidence": {
                            "json_pointer": f"/paths/{path}/{method.lower()}/parameters/{param_name}/required",
                            "explanation": f"Existing optional parameter {param_name} is now mandatory. Existing client calls omitting it will fail validation (HTTP 400/422).",
                            "rule_name": "Required Parameter Rule",
                            "impact_summary": f"Calls without {param_name} will fail."
                        }
                    })

                # Check parameter type changes
                old_type = old_p.get("schema", {}).get("type")
                new_type = new_p.get("schema", {}).get("type")
                if old_type and new_type and old_type != new_type:
                    changes.append({
                        "change_type": "PARAM_TYPE_CHANGED",
                        "severity": "BREAKING",
                        "path": path,
                        "http_method": method,
                        "description": f"Parameter '{param_name}' type changed from '{old_type}' to '{new_type}'.",
                        "rule_code": "BREAK_PARAM_TYPE_CHANGED",
                        "old_value": old_type,
                        "new_value": new_type,
                        "evidence": {
                            "json_pointer": f"/paths/{path}/{method.lower()}/parameters/{param_name}/schema/type",
                            "explanation": f"Type mismatch: parameter {param_name} expects {new_type} instead of {old_type}.",
                            "rule_name": "Parameter Type Compatibility Rule",
                            "impact_summary": f"Values formatted as {old_type} may fail validation."
                        }
                    })

        # Newly required parameters added
        for key, new_p in new_param_map.items():
            if key not in old_param_map:
                param_in, param_name = key.split(":", 1)
                if new_p.get("required", False):
                    changes.append({
                        "change_type": "REQUIRED_PARAM_ADDED",
                        "severity": "BREAKING",
                        "path": path,
                        "http_method": method,
                        "description": f"Newly added parameter '{param_name}' (in: {param_in}) is marked as required.",
                        "rule_code": "BREAK_REQ_PARAM_ADDED",
                        "old_value": None,
                        "new_value": json.dumps(new_p),
                        "evidence": {
                            "json_pointer": f"/paths/{path}/{method.lower()}/parameters/{param_name}",
                            "explanation": f"A brand new mandatory parameter '{param_name}' was introduced. All existing client calls will fail unless updated to provide it.",
                            "rule_name": "New Required Parameter Rule",
                            "impact_summary": f"Existing clients do not send {param_name}."
                        }
                    })

    def _compare_request_body(self, path: str, method: str, old_body: Optional[Dict[str, Any]], new_body: Optional[Dict[str, Any]], changes: List[Dict[str, Any]]):
        old_body = old_body or {}
        new_body = new_body or {}

        old_req = old_body.get("required", False)
        new_req = new_body.get("required", False)

        if not old_req and new_req:
            changes.append({
                "change_type": "REQUIRED_BODY_ADDED",
                "severity": "BREAKING",
                "path": path,
                "http_method": method,
                "description": f"Request body became required for {method} {path}.",
                "rule_code": "BREAK_REQ_BODY_ADDED",
                "old_value": "required: false",
                "new_value": "required: true",
                "evidence": {
                    "json_pointer": f"/paths/{path}/{method.lower()}/requestBody/required",
                    "explanation": f"A request body is now mandatory for {method} {path}.",
                    "rule_name": "Required Request Body Rule",
                    "impact_summary": f"Requests without payload will fail with HTTP 400."
                }
            })

        # Compare json schema properties
        old_schema = old_body.get("content", {}).get("application/json", {}).get("schema", {})
        new_schema = new_body.get("content", {}).get("application/json", {}).get("schema", {})

        if old_schema and new_schema:
            self._compare_schema_properties(path, method, "requestBody", old_schema, new_schema, changes, is_request=True)

    def _compare_responses(self, path: str, method: str, old_responses: Dict[str, Any], new_responses: Dict[str, Any], changes: List[Dict[str, Any]]):
        for status_code, old_resp in old_responses.items():
            if status_code.startswith("2") and status_code not in new_responses:
                changes.append({
                    "change_type": "RESPONSE_STATUS_REMOVED",
                    "severity": "BREAKING",
                    "path": path,
                    "http_method": method,
                    "description": f"Successful response status '{status_code}' was removed from {method} {path}.",
                    "rule_code": "BREAK_RESP_STATUS_REMOVED",
                    "old_value": status_code,
                    "new_value": None,
                    "evidence": {
                        "json_pointer": f"/paths/{path}/{method.lower()}/responses/{status_code}",
                        "explanation": f"HTTP status {status_code} is no longer documented or returned.",
                        "rule_name": "Response Status Removal Rule",
                        "impact_summary": f"Client code expecting {status_code} will break."
                    }
                })
                continue

            if status_code in new_responses:
                new_resp = new_responses[status_code]
                old_schema = old_resp.get("content", {}).get("application/json", {}).get("schema", {})
                new_schema = new_resp.get("content", {}).get("application/json", {}).get("schema", {})
                if old_schema and new_schema:
                    self._compare_schema_properties(path, method, f"responses/{status_code}", old_schema, new_schema, changes, is_request=False)

    def _compare_schema_properties(self, path: str, method: str, location: str, old_schema: Dict[str, Any], new_schema: Dict[str, Any], changes: List[Dict[str, Any]], is_request: bool):
        old_props = old_schema.get("properties", {}) or {}
        new_props = new_schema.get("properties", {}) or {}
        old_required = set(old_schema.get("required", []) or [])
        new_required = set(new_schema.get("required", []) or [])

        # Check properties removed
        for prop_name, old_prop in old_props.items():
            if prop_name not in new_props:
                severity = "BREAKING" if not is_request else ("BREAKING" if prop_name in old_required else "WARNING")
                change_type = "RESPONSE_PROPERTY_REMOVED" if not is_request else "REQUEST_PROPERTY_REMOVED"
                rule_code = "BREAK_RESP_PROP_REMOVED" if not is_request else "WARN_REQ_PROP_REMOVED"
                
                changes.append({
                    "change_type": change_type,
                    "severity": severity,
                    "path": path,
                    "http_method": method,
                    "description": f"Property '{prop_name}' was removed from {location} in {method} {path}.",
                    "rule_code": rule_code,
                    "old_value": json.dumps(old_prop),
                    "new_value": None,
                    "evidence": {
                        "json_pointer": f"/paths/{path}/{method.lower()}/{location}/schema/properties/{prop_name}",
                        "explanation": f"The field '{prop_name}' was removed from the schema payload. Client code parsing response.{prop_name} will encounter KeyError or AttributeError.",
                        "rule_name": "Response Property Removal Rule",
                        "impact_summary": f"Field '{prop_name}' is missing."
                    }
                })
            else:
                new_prop = new_props[prop_name]
                # Check property type changed
                old_type = old_prop.get("type")
                new_type = new_prop.get("type")
                if old_type and new_type and old_type != new_type:
                    changes.append({
                        "change_type": "RESPONSE_PROPERTY_TYPE_CHANGED" if not is_request else "REQUEST_PROPERTY_TYPE_CHANGED",
                        "severity": "BREAKING",
                        "path": path,
                        "http_method": method,
                        "description": f"Property '{prop_name}' type changed from '{old_type}' to '{new_type}' in {location}.",
                        "rule_code": "BREAK_RESP_PROP_TYPE_CHANGED" if not is_request else "BREAK_REQ_PROP_TYPE_CHANGED",
                        "old_value": old_type,
                        "new_value": new_type,
                        "evidence": {
                            "json_pointer": f"/paths/{path}/{method.lower()}/{location}/schema/properties/{prop_name}/type",
                            "explanation": f"Field '{prop_name}' changed type from {old_type} to {new_type}. Client deserialization will raise TypeErrors.",
                            "rule_name": "Property Type Change Rule",
                            "impact_summary": f"Type changed from {old_type} to {new_type}."
                        }
                    })

                # Check enum value removed
                old_enums = old_prop.get("enum", [])
                new_enums = new_prop.get("enum", [])
                if old_enums and new_enums:
                    removed_enums = set(old_enums) - set(new_enums)
                    if removed_enums:
                        changes.append({
                            "change_type": "ENUM_VALUE_REMOVED",
                            "severity": "BREAKING",
                            "path": path,
                            "http_method": method,
                            "description": f"Enum values {list(removed_enums)} were removed from property '{prop_name}'.",
                            "rule_code": "BREAK_ENUM_VAL_REMOVED",
                            "old_value": json.dumps(old_enums),
                            "new_value": json.dumps(new_enums),
                            "evidence": {
                                "json_pointer": f"/paths/{path}/{method.lower()}/{location}/schema/properties/{prop_name}/enum",
                                "explanation": f"Permitted values {list(removed_enums)} are no longer valid for '{prop_name}'.",
                                "rule_name": "Enum Value Removal Rule",
                                "impact_summary": f"Values {list(removed_enums)} no longer supported."
                            }
                        })

                # Recursively compare array items
                if old_type == "array" and new_type == "array":
                    old_items = old_prop.get("items", {})
                    new_items = new_prop.get("items", {})
                    if isinstance(old_items, dict) and isinstance(new_items, dict):
                        self._compare_schema_properties(
                            path, method, f"{location}/properties/{prop_name}/items",
                            old_items, new_items, changes, is_request
                        )
                # Recursively compare nested objects
                elif old_type == "object" and new_type == "object":
                    self._compare_schema_properties(
                        path, method, f"{location}/properties/{prop_name}",
                        old_prop, new_prop, changes, is_request
                    )

        # In request body: check newly required properties
        if is_request:
            for prop_name, new_prop in new_props.items():
                if prop_name in new_required and prop_name not in old_required:
                    changes.append({
                        "change_type": "REQUIRED_BODY_PROP_ADDED",
                        "severity": "BREAKING",
                        "path": path,
                        "http_method": method,
                        "description": f"Property '{prop_name}' in request body became required in {method} {path}.",
                        "rule_code": "BREAK_REQ_BODY_PROP_ADDED",
                        "old_value": "required: false" if prop_name in old_props else None,
                        "new_value": "required: true",
                        "evidence": {
                            "json_pointer": f"/paths/{path}/{method.lower()}/requestBody/schema/required/{prop_name}",
                            "explanation": f"Field '{prop_name}' is now strictly required. Requests omitting it will fail validation.",
                            "rule_name": "Required Body Property Rule",
                            "impact_summary": f"Payload must include '{prop_name}'."
                        }
                    })
        else:
            # In response: check newly added optional properties
            for prop_name, new_prop in new_props.items():
                if prop_name not in old_props:
                    changes.append({
                        "change_type": "RESPONSE_PROPERTY_ADDED",
                        "severity": "INFO",
                        "path": path,
                        "http_method": method,
                        "description": f"New optional property '{prop_name}' added to response in {method} {path}.",
                        "rule_code": "INFO_RESP_PROP_ADDED",
                        "old_value": None,
                        "new_value": json.dumps(new_prop),
                        "evidence": {
                            "json_pointer": f"/paths/{path}/{method.lower()}/responses/schema/properties/{prop_name}",
                            "explanation": f"Additional data property '{prop_name}' is now provided by the server.",
                            "rule_name": "Response Property Addition Rule",
                            "impact_summary": f"Field '{prop_name}' available in response."
                        }
                    })
