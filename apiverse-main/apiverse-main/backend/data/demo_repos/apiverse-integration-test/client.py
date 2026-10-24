from typing import Dict, Any, List, Optional
import urllib.request
import json

class OrderClient:
    """
    API client integrating with APIVerse Integration Test Core API.
    """
    def __init__(self, base_url: str = "https://api.integration-test.example.com", mock_mode: bool = True):
        self.base_url = base_url.rstrip("/")
        self.mock_mode = mock_mode

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Retrieves order details.
        Note: Accesses response property 'tracking_number'.
        """
        url = f"{self.base_url}/v1/orders/{order_id}"
        if self.mock_mode:
            # Baseline v1 contract payload
            data = {
                "order_id": int(order_id) if order_id.isdigit() else 1001,
                "status": "shipped",
                "tracking_number": "TRK-9876543210",
                "amount": 2500
            }
        else:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))

        tracking = data["tracking_number"]
        return {
            "order_id": data["order_id"],
            "status": data["status"],
            "tracking_number": tracking,
            "amount": data["amount"]
        }

    def cancel_order_legacy(self, order_id: str, reason: str = "Customer request") -> bool:
        """
        Cancels an order via legacy endpoint.
        Calls removed endpoint '/v1/orders/cancel-legacy'.
        """
        url = f"{self.base_url}/v1/orders/cancel-legacy"
        payload = {"order_id": order_id, "reason": reason}
        if self.mock_mode:
            return True
        else:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("cancelled", False)

    def create_order(self, amount: int, items: List[str]) -> Dict[str, Any]:
        """
        Creates a new order.
        In v1: Does not send 'idempotency_key'.
        Expects 'order_id' as integer.
        """
        url = f"{self.base_url}/v1/orders"
        payload = {"amount": amount, "items": items}
        if self.mock_mode:
            return {
                "order_id": 2048,
                "status": "pending"
            }
        else:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
