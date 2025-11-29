#!/usr/bin/env python3
"""
Unit tests for the lightweight MAC lookup FastAPI helper.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from device_mac_matcher import DeviceModelMatcher

app = FastAPI()
matcher = DeviceModelMatcher()


@app.get("/test/{mac_address}")
async def lookup_mac(mac_address: str):
    try:
        result = matcher.match_mac_to_model(mac_address)
        return {
            "mac": result.mac_address,
            "vendor": result.vendor,
            "device_type": result.device_type,
            "model_path": result.model_path,
            "confidence": result.confidence,
            "pos_system": result.pos_system,
        }
    except Exception as exc:  # pragma: no cover - defensive path
        return {"error": str(exc)}


@app.get("/")
async def root():
    return {"status": "ok", "message": "MAC API test server"}


@pytest.fixture
def mac_client(monkeypatch):
    class DummyResult:
        def __init__(self, mac_address: str) -> None:
            self.mac_address = mac_address
            self.vendor = "TestVendor"
            self.device_type = "fortinet"
            self.model_path = "/static/3d-models/generic_device.obj"
            self.confidence = 0.95
            self.pos_system = None

    def fake_match(mac_address: str, metadata=None):
        return DummyResult(mac_address)

    monkeypatch.setattr(matcher, "match_mac_to_model", fake_match)
    return TestClient(app)


def test_lookup_endpoint_returns_device_metadata(mac_client):
    response = mac_client.get("/test/00:11:22:33:44:55")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mac"] == "00:11:22:33:44:55"
    assert payload["vendor"] == "TestVendor"
    assert payload["device_type"] == "fortinet"
    assert payload["model_path"] == "/static/3d-models/generic_device.obj"
    assert pytest.approx(payload["confidence"], rel=1e-6) == 0.95
    assert payload["pos_system"] is None


def test_root_endpoint_reports_status(mac_client):
    response = mac_client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
