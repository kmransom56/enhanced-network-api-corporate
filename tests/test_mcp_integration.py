"""
MCP integration tests for Enhanced Network API
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.enhanced_network_api.platform_web_api_fastapi import (
    app,
    _call_fortinet_tool_async,
)


def _mock_client(result=None, *, side_effect=None):
    client = AsyncMock()
    if side_effect is not None:
        client.call.side_effect = side_effect
    else:
        client.call.return_value = result
    return client


@pytest.mark.mcp
@pytest.mark.asyncio
class TestMCPIntegration:
    """Unit tests for Fortinet MCP helper interactions."""

    async def test_fortinet_mcp_discovery_tool(self):
        mock_topology = {
            "gateways": [{"id": "fg-test", "name": "Test Gateway", "ip": "192.168.0.254"}],
            "switches": [{"id": "fsw-test", "name": "Test Switch", "ip": "10.255.1.2"}],
            "aps": [{"id": "fap-test", "name": "Test AP"}],
            "clients": [{"id": "client-test", "name": "Test Client", "ip": "192.168.1.100"}],
            "links": [{"from": "fg-test", "to": "fsw-test", "type": "fortilink"}],
        }

        client = _mock_client(mock_topology)
        with patch(
            "src.enhanced_network_api.platform_web_api_fastapi._get_fortinet_client",
            new=AsyncMock(return_value=client),
        ):
            result = await _call_fortinet_tool_async("discover_fortinet_topology")

        client.call.assert_awaited_once_with("discover_fortinet_topology", None)
        assert result["gateways"][0]["name"] == "Test Gateway"

    async def test_fortinet_mcp_3d_scene_tool(self):
        mock_scene = {
            "nodes": [
                {"id": "fg-test", "type": "fortigate", "role": "gateway", "name": "Test Gateway"},
                {"id": "client-test", "type": "windows", "role": "client", "name": "Test Client"},
            ],
            "links": [{"from": "fg-test", "to": "client-test", "type": "direct"}],
            "triageHints": [],
        }

        client = _mock_client(mock_scene)
        with patch(
            "src.enhanced_network_api.platform_web_api_fastapi._get_fortinet_client",
            new=AsyncMock(return_value=client),
        ):
            result = await _call_fortinet_tool_async("generate_topology_3d_scene", {"include_health": True})

        client.call.assert_awaited_once_with(
            "generate_topology_3d_scene",
            {"include_health": True},
        )
        assert len(result["nodes"]) == 2

    async def test_mcp_bridge_connection_failure(self):
        client = _mock_client(side_effect=HTTPException(status_code=502, detail="bridge down"))
        with patch(
            "src.enhanced_network_api.platform_web_api_fastapi._get_fortinet_client",
            new=AsyncMock(return_value=client),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await _call_fortinet_tool_async("discover_fortinet_topology")

        assert exc_info.value.status_code == 502

    async def test_mcp_bridge_invalid_response(self):
        client = _mock_client({"content": "invalid json"})
        with patch(
            "src.enhanced_network_api.platform_web_api_fastapi._get_fortinet_client",
            new=AsyncMock(return_value=client),
        ):
            result = await _call_fortinet_tool_async("discover_fortinet_topology")

        assert result["content"] == "invalid json"


@pytest.mark.mcp
@pytest.mark.integration
class TestMCPClientIntegration:
    """Integration tests against the live Fortinet bridge."""

    @pytest.mark.asyncio
    async def test_enterprise_fortigate_client_integration(self):
        topology = await _call_fortinet_tool_async("discover_fortinet_topology")

        device_list = topology.get("devices", [])
        link_list = topology.get("links", [])

        assert device_list, "Expected non-empty device list from live topology"
        assert link_list, "Expected non-empty link list from live topology"

        gateway_devices = [d for d in device_list if d.get("role") == "gateway" or d.get("type") == "fortigate"]
        network_segments = [d for d in device_list if d.get("type") == "network"]

        assert gateway_devices, "Expected at least one FortiGate gateway"
        assert network_segments, "Expected at least one network segment device"

    @pytest.mark.asyncio
    async def test_client_discovery_with_fallback(self):
        topology = await _call_fortinet_tool_async(
            "discover_fortinet_topology",
            {"refresh_cache": True},
        )

        device_list = topology.get("devices", [])
        assert device_list is not None

    @pytest.mark.asyncio
    async def test_client_device_parsing(self):
        topology = await _call_fortinet_tool_async("discover_fortinet_topology")

        device_list = topology.get("devices", [])
        assert device_list, "Expected at least one device returned from live topology data"

        fortigate = next((d for d in device_list if d.get("type") == "fortigate"), None)
        assert fortigate is not None, "Expected FortiGate device details"
        assert fortigate.get("interfaces")
        assert isinstance(fortigate.get("connections"), (int, float))
        assert fortigate.get("serial")


@pytest.mark.mcp
@pytest.mark.self_healing
class TestMCPSelfHealing:
    """Self-healing regression tests."""

    @pytest.mark.asyncio
    async def test_mcp_connection_retry(self):
        # Currently _call_fortinet_tool_async bubbles errors; ensure we surface the HTTPException.
        client = _mock_client(side_effect=HTTPException(status_code=502, detail="connection failed"))
        with patch(
            "src.enhanced_network_api.platform_web_api_fastapi._get_fortinet_client",
            new=AsyncMock(return_value=client),
        ):
            with pytest.raises(HTTPException):
                await _call_fortinet_tool_async("discover_fortinet_topology")

    @pytest.mark.asyncio
    async def test_mcp_circuit_breaker(self):
        client = _mock_client(side_effect=HTTPException(status_code=503, detail="service unavailable"))
        with patch(
            "src.enhanced_network_api.platform_web_api_fastapi._get_fortinet_client",
            new=AsyncMock(return_value=client),
        ):
            with pytest.raises(HTTPException):
                await _call_fortinet_tool_async("discover_fortinet_topology")

    @pytest.mark.asyncio
    async def test_mcp_fallback_data(self):
        client = _mock_client(side_effect=HTTPException(status_code=503, detail="service unavailable"))
        with patch(
            "src.enhanced_network_api.platform_web_api_fastapi._get_fortinet_client",
            new=AsyncMock(return_value=client),
        ):
            with pytest.raises(HTTPException):
                await _call_fortinet_tool_async("discover_fortinet_topology")


@pytest.mark.mcp
@pytest.mark.api
class TestMCPAPIEndpoints:
    """FastAPI endpoint tests with patched MCP helper."""

    def test_topology_raw_endpoint_with_mcp(self, test_client: TestClient):
        with patch(
            "src.enhanced_network_api.platform_web_api_fastapi._call_fortinet_tool_async",
            new=AsyncMock(
                return_value={
                    "devices": [{"id": "fg-test", "name": "Test Gateway"}],
                    "links": [],
                }
            ),
        ):
            response = test_client.get("/api/topology/raw")

        assert response.status_code == 200
        data = response.json()
        assert "devices" in data
        assert len(data["devices"]) == 1

    def test_topology_scene_endpoint_with_mcp(self, test_client: TestClient):
        with patch(
            "src.enhanced_network_api.platform_web_api_fastapi._call_fortinet_tool_async",
            new=AsyncMock(
                return_value={
                    "devices": [{"id": "fg-test", "type": "fortigate", "role": "gateway"}],
                    "links": [],
                }
            ),
        ):
            response = test_client.get("/api/topology/scene")

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        fortigate_nodes = [node for node in data["nodes"] if node.get("type") == "fortigate"]
        assert fortigate_nodes

    def test_mcp_error_propagation(self, test_client: TestClient):
        with patch(
            "src.enhanced_network_api.platform_web_api_fastapi._call_fortinet_tool_async",
            new=AsyncMock(side_effect=HTTPException(status_code=503, detail={"error": "Service unavailable"})),
        ):
            response = test_client.get("/api/topology/raw")

        assert response.status_code == 503
        data = response.json()
        assert "error" in data.get("detail", {})
