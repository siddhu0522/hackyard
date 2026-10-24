import pytest
from client import StoreApiClient

def test_client_init():
    client = StoreApiClient(base_url="https://api.test.com")
    assert client.base_url == "https://api.test.com"

def test_client_routes():
    client = StoreApiClient(base_url="https://api.test.com")
    assert hasattr(client, "list_items")
    assert hasattr(client, "delete_item")
    assert hasattr(client, "call_legacy_sync")
