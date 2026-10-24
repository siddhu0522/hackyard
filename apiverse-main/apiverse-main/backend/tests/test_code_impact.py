import pytest
from backend.app.services.code_impact import CodeImpactAnalyzer

def test_code_impact_analyzer_python():
    analyzer = CodeImpactAnalyzer()
    
    python_client_code = """
import requests

def get_items():
    res = requests.get("https://api.store.example.com/v1/items")
    data = res.json()
    for item in data["items"]:
        item_id = item["id"]
        item_name = item["name"]
    return data

def delete_item(item_id):
    requests.delete("https://api.store.example.com/v1/items", params={"id": item_id})
"""

    files = {"client.py": python_client_code}
    
    # 1. Test Endpoint Removed
    change1 = {
        "change_type": "ENDPOINT_REMOVED",
        "path": "/v1/items",
        "http_method": None,
        "description": "Endpoint /v1/items removed"
    }
    matches1 = analyzer.analyze_repository(files, change1)
    assert len(matches1) >= 1
    assert matches1[0]["file_path"] == "client.py"
    assert matches1[0]["match_confidence"] == "confirmed"

    # 2. Test Response Property Removed
    change2 = {
        "change_type": "RESPONSE_PROPERTY_REMOVED",
        "path": "/v1/items",
        "http_method": "GET",
        "description": "Property 'name' was removed from response in GET /v1/items"
    }
    matches2 = analyzer.analyze_repository(files, change2)
    assert any(m["match_confidence"] == "confirmed" for m in matches2)
    assert any("name" in m["snippet"] for m in matches2)

    # 3. Test HTTP Method Removed
    change3 = {
        "change_type": "METHOD_REMOVED",
        "path": "/v1/items",
        "http_method": "DELETE",
        "description": "HTTP method DELETE removed from /v1/items"
    }
    matches3 = analyzer.analyze_repository(files, change3)
    assert len(matches3) >= 1
    assert any("delete_item" in m["function_name"] for m in matches3)
