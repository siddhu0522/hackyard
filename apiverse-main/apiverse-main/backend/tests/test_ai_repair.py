import pytest
from backend.app.services.ai_repair import AIRepairService, MissingApiKeyError

@pytest.mark.anyio
async def test_ai_repair_service_mock():
    service = AIRepairService(provider_name="mock")
    
    change = {
        "change_type": "RESPONSE_PROPERTY_REMOVED",
        "path": "/v1/items",
        "http_method": "GET",
        "description": "Property 'name' was removed from response schema."
    }
    
    affected = [{
        "file_path": "client.py",
        "language": "python",
        "line_start": 5,
        "line_end": 7
    }]
    
    source = {
        "client.py": 'item_id = item["id"]\nitem_name = item["name"]\n'
    }
    
    result = await service.generate_repair(change, affected, source)
    
    assert result["provider"] == "mock"
    assert len(result["patches"]) == 1
    patch = result["patches"][0]
    assert patch["file_path"] == "client.py"
    assert patch["is_valid"] is True
    assert 'item.get("name", None)' in patch["patched_content"]
    assert "--- a/client.py" in patch["unified_diff"]

@pytest.mark.anyio
async def test_ai_repair_service_missing_key():
    service = AIRepairService(provider_name="openai")
    # When OPENAI_API_KEY is not set, must raise MissingApiKeyError
    with pytest.raises(MissingApiKeyError):
        await service.generate_repair({}, [], {}, provider_name="openai")
