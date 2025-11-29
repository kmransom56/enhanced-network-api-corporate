"""
Integration tests for platform service endpoints using live files and HTTP server.
"""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.enhanced_network_api.platform_web_api_fastapi import app, DISCOVERY_DIR

SERVICE_PORT = 9876


class DemoServiceHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler serving JSON payloads."""

    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"path": self.path}).encode("utf-8"))

    def log_message(self, format, *args):  # noqa: D401, N802 - suppress noisy logging
        return


@pytest.fixture(scope="module")
def platform_environment() -> None:
    """Create discovery map and start demo HTTP service."""
    discovery_dir = Path(DISCOVERY_DIR)
    discovery_dir.mkdir(parents=True, exist_ok=True)
    platform_file = discovery_dir / "platform_map.json"
    platform_data = {
        "service_mapping": {
            str(SERVICE_PORT): {
                "container": "demo-service",
                "status": "running",
                "image": "demo:latest",
            }
        },
        "categories": {"automation": ["demo-service"]},
        "docker_containers": {},
        "discovered_ports": {},
        "discovery_time": "2025-11-22T00:00:00",
    }
    platform_file.write_text(json.dumps(platform_data), encoding="utf-8")

    server = HTTPServer(("127.0.0.1", SERVICE_PORT), DemoServiceHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield
    finally:
        server.shutdown()
        thread.join(timeout=2)
        try:
            platform_file.unlink()
        except FileNotFoundError:
            pass


@pytest.fixture(scope="module")
def client(platform_environment):
    """Provide FastAPI test client with platform map in place."""
    with TestClient(app) as test_client:
        yield test_client


def test_platform_status(client: TestClient):
    response = client.get("/api/platform/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"active", "not_discovered"}
    assert "containers" in payload


def test_platform_services_listing(client: TestClient):
    response = client.get("/api/platform/services")
    assert response.status_code == 200
    payload = response.json()
    assert payload["services"]
    assert payload["services"][0]["name"] == "demo-service"


def test_platform_open_service(client: TestClient):
    response = client.post("/api/platform/service/1/open")
    assert response.status_code == 200
    payload = response.json()
    assert payload["url"] == f"http://localhost:{SERVICE_PORT}"


def test_platform_call_service(client: TestClient):
    response = client.post(
        "/api/platform/service/1/call",
        json={"method": "GET", "path": "/health"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status_code"] == 200
    assert json.loads(payload["body"]) == {"path": "/health"}
