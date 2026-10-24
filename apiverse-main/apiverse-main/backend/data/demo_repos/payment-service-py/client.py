import requests
from typing import Dict, Any, List, Optional

class StoreApiClient:
    """Python Client for the Store and Payment API."""
    
    def __init__(self, base_url: str = "https://api.store.example.com", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def list_items(self) -> List[Dict[str, Any]]:
        """Fetch all store items."""
        url = f"{self.base_url}/v1/items"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Accesses response properties directly
        results = []
        for item in data.get("items", []):
            item_id = item["id"]  # Expects integer id
            item_name = item["name"]  # Breaking change: 'name' removed in v2
            status = item["status"]  # Enum: active, archived, draft
            results.append({
                "id": item_id,
                "name": item_name,
                "status": status
            })
        return results

    def delete_item(self, item_id: int) -> bool:
        """Delete an item by id."""
        url = f"{self.base_url}/v1/items"
        response = self.session.delete(url, params={"id": item_id})
        return response.status_code == 204

    def call_legacy_sync(self) -> Dict[str, Any]:
        """Calls legacy endpoint."""
        url = f"{self.base_url}/v1/legacy"
        response = self.session.get(url)
        return response.json()
