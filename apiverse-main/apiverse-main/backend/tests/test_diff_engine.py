import pytest
from backend.app.services.openapi_diff import OpenAPIDiffEngine

def test_openapi_diff_engine_comprehensive():
    engine = OpenAPIDiffEngine()
    old_spec = {
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
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "status": {"type": "string", "enum": ["active", "archived", "draft"]}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "delete": {"responses": {"204": {"description": "Deleted"}}}
            },
            "/v1/legacy": {
                "get": {"responses": {"200": {"description": "OK"}}}
            }
        }
    }

    new_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Store API", "version": "2.0.0"},
        "paths": {
            "/v1/items": {
                "get": {
                    "parameters": [{"name": "api_token", "in": "query", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "status": {"type": "string", "enum": ["active", "archived"]}
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

    changes = engine.compare_specs(old_spec, new_spec)
    change_types = [c["change_type"] for c in changes]

    # Verify detected changes
    assert "ENDPOINT_REMOVED" in change_types  # /v1/legacy removed
    assert "METHOD_REMOVED" in change_types    # DELETE /v1/items removed
    assert "REQUIRED_PARAM_ADDED" in change_types  # api_token added as required
    assert "RESPONSE_PROPERTY_REMOVED" in change_types  # 'name' removed
    assert "RESPONSE_PROPERTY_TYPE_CHANGED" in change_types  # 'id' integer -> string
    assert "ENUM_VALUE_REMOVED" in change_types  # 'draft' removed

    # Verify rule codes and evidence
    for c in changes:
        assert c["rule_code"].startswith("BREAK_") or c["rule_code"].startswith("WARN_") or c["rule_code"].startswith("INFO_")
        assert "evidence" in c
        assert "json_pointer" in c["evidence"]
        assert "explanation" in c["evidence"]
