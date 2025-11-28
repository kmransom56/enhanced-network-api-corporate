"""
Pytest configuration for Enhanced Network API integration tests
"""

import asyncio
import os
import subprocess
import sys
import time
from multiprocessing import Process
from pathlib import Path
from typing import Generator

import pytest
import requests
from fastapi.testclient import TestClient

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.enhanced_network_api.platform_web_api_fastapi import app  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_mcp_bridge(host: str, port: int) -> None:
    """
    Launch the Fortinet MCP bridge (HTTP) in a dedicated process.
    This bridge executes real topology discovery via mcp_topology_server.py.
    """
    import uvicorn

    uvicorn.run("mcp_bridge:app", host=host, port=port, log_level="info")


def _run_platform_api(host: str, port: int) -> None:
    """
    Launch the main FastAPI application so browser-based tests can hit real endpoints.
    """
    import uvicorn

    uvicorn.run(
        "src.enhanced_network_api.platform_web_api_fastapi:app",
        host=host,
        port=port,
        log_level="info",
    )


@pytest.fixture(scope="session", autouse=True)
def start_mcp_http_bridge() -> Generator[None, None, None]:
    """
    Start the Fortinet MCP HTTP bridge for the duration of the test session.
    No mocked responses: we rely on the real bridge which shells out to
    mcp_topology_server.py for live FortiGate discovery.
    """
    host = os.getenv("FORTINET_MCP_HTTP_HOST", "127.0.0.1")
    port = int(os.getenv("FORTINET_MCP_HTTP_PORT", "11112"))

    # Ensure application reads the bridge address
    os.environ["FORTINET_MCP_HTTP_URL"] = f"http://{host}:{port}"

    proc = Process(target=_run_mcp_bridge, args=(host, port), daemon=True)
    proc.start()

    # Wait for bridge to become healthy
    health_url = f"http://{host}:{port}/health"
    for _ in range(60):
        try:
            resp = requests.get(health_url, timeout=1)
            if resp.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        proc.join()
        raise RuntimeError("Fortinet MCP HTTP bridge failed to start")

    yield

    proc.terminate()
    proc.join(timeout=5)


@pytest.fixture(scope="session", autouse=True)
def start_platform_api_server() -> Generator[None, None, None]:
    """
    Start the platform FastAPI application with production static assets.
    """
    host = os.getenv("PLATFORM_API_HOST", "127.0.0.1")
    port = int(os.getenv("PLATFORM_API_PORT", "11111"))

    # Ensure the static asset bundle mirrors production before tests hit UI routes.
    build_script = REPO_ROOT / "scripts" / "build_static_assets.py"
    if build_script.exists():
        subprocess.run([sys.executable, str(build_script)], check=True)

    proc = Process(target=_run_platform_api, args=(host, port), daemon=True)
    proc.start()

    health_url = f"http://{host}:{port}/health"
    for _ in range(60):
        try:
            resp = requests.get(health_url, timeout=1)
            if resp.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        proc.join()
        raise RuntimeError("Platform API server failed to start")

    try:
        yield
    finally:
        proc.terminate()
        proc.join(timeout=5)


@pytest.fixture(scope="session")
def event_loop():
    """Provide a single asyncio event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    """Expose FastAPI TestClient for live integration exercises."""
    with TestClient(app) as client:
        yield client
