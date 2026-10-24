import pytest
from client import OrderClient

def test_get_order_details():
    client = OrderClient(mock_mode=True)
    order = client.get_order("1001")
    assert order["order_id"] == 1001
    assert order["status"] == "shipped"
    assert order["tracking_number"] == "TRK-9876543210"

def test_cancel_order_legacy():
    client = OrderClient(mock_mode=True)
    success = client.cancel_order_legacy("1001", reason="Fraud check")
    assert success is True

def test_create_order():
    client = OrderClient(mock_mode=True)
    res = client.create_order(5000, ["widget-1", "widget-2"])
    assert res["status"] == "pending"
    assert res["order_id"] == 2048
