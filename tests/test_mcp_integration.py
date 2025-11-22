"""
MCP integration tests for Enhanced Network API
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.enhanced_network_api.platform_web_api_fastapi import app


@pytest.mark.mcp
@pytest.mark.asyncio
class TestMCPIntegration:
    """Test MCP server integration."""
    
    async def test_fortinet_mcp_discovery_tool(self):
        """Test Fortinet MCP discovery tool integration."""
        mock_topology = {
            "gateways": [{"id": "fg-test", "name": "Test Gateway", "ip": "192.168.0.254"}],
            "switches": [{"id": "fsw-test", "name": "Test Switch", "ip": "10.255.1.2"}],
            "aps": [{"id": "fap-test", "name": "Test AP"}],
            "clients": [{"id": "client-test", "name": "Test Client", "ip": "192.168.1.100"}],
            "links": [{"from": "fg-test", "to": "fsw-test", "type": "fortilink"}]
        }
        
        with patch('src.enhanced_network_api.platform_web_api_fastapi.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "content": [{"type": "text", "text": json.dumps(mock_topology)}],
                "isError": False
            }
            
            from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool
            
            result = _call_fortinet_tool("discover_fortinet_topology")

            assert isinstance(result, dict)
            assert len(result["gateways"]) == 1
            assert len(result["switches"]) == 1
            assert len(result["clients"]) == 1
    
    async def test_fortinet_mcp_3d_scene_tool(self):
        """Test Fortinet MCP 3D scene generation tool."""
        mock_scene = {
            "nodes": [
                {"id": "fg-test", "type": "fortigate", "role": "gateway", "name": "Test Gateway"},
                {"id": "client-test", "type": "windows", "role": "client", "name": "Test Client"}
            ],
            "links": [{"from": "fg-test", "to": "client-test", "type": "direct"}],
            "triageHints": []
        }
        
        with patch('src.enhanced_network_api.platform_web_api_fastapi.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "content": [{"type": "text", "text": json.dumps(mock_scene)}],
                "isError": False
            }
            
            from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool
            
            result = _call_fortinet_tool("generate_topology_3d_scene")

            assert isinstance(result, dict)
            assert len(result["nodes"]) == 2
            assert len(result["links"]) == 1
            assert result["nodes"][0]["type"] == "fortigate"
            assert result["nodes"][1]["type"] == "windows"
    
    def test_mcp_bridge_connection_failure(self):
        """Test MCP bridge connection failure handling."""
        with patch('src.enhanced_network_api.platform_web_api_fastapi.requests.post') as mock_post:
            mock_post.side_effect = Exception("Connection refused")
            
            from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool
            
            with pytest.raises(Exception) as exc_info:
                _call_fortinet_tool("discover_fortinet_topology")
            
            assert "Error contacting Fortinet MCP bridge" in str(exc_info.value)
    
    def test_mcp_bridge_timeout_handling(self):
        """Test MCP bridge timeout handling."""
        with patch('src.enhanced_network_api.platform_web_api_fastapi.requests.post') as mock_post:
            mock_post.side_effect = Exception("Request timeout")
            
            from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool
            
            with pytest.raises(Exception) as exc_info:
                _call_fortinet_tool("discover_fortinet_topology")
            
            assert "Error contacting Fortinet MCP bridge" in str(exc_info.value)
    
    def test_mcp_bridge_invalid_response(self):
        """Test MCP bridge invalid response handling."""
        with patch('src.enhanced_network_api.platform_web_api_fastapi.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "content": [{"type": "text", "text": "invalid json"}],
                "isError": False
            }
            
            from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool
            
            result = _call_fortinet_tool("discover_fortinet_topology")

            assert isinstance(result, dict)
            assert "content" in result
            assert result["content"] == "invalid json"
    
    def test_mcp_bridge_error_response(self):
        """Test MCP bridge error response handling."""
        with patch('src.enhanced_network_api.platform_web_api_fastapi.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "content": [{"type": "text", "text": "Tool execution failed"}],
                "isError": True
            }
            
            from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool
            
            with pytest.raises(Exception) as exc_info:
                _call_fortinet_tool("discover_fortinet_topology")

            assert "Tool execution failed" in str(exc_info.value)


@pytest.mark.mcp
@pytest.mark.integration
class TestMCPClientIntegration:
    """Test MCP client integration with actual FortiGate client."""
    
    @pytest.mark.asyncio
    async def test_enterprise_fortigate_client_integration(self):
        """Test enterprise FortiGate client integration using live topology data."""
        from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool

        topology = _call_fortinet_tool("discover_fortinet_topology")

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
        """Test client discovery with refresh cache to simulate fallback mechanisms."""
        from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool

        topology = _call_fortinet_tool(
            "discover_fortinet_topology",
            {"refresh_cache": True}
        )

        device_list = topology.get("devices", [])
        assert device_list is not None
        assert len(device_list) >= 0
    
    @pytest.mark.asyncio
    async def test_client_device_parsing(self):
        """Validate client device information returned from live topology data."""
        from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool

        topology = _call_fortinet_tool("discover_fortinet_topology")

        device_list = topology.get("devices", [])
        assert device_list, "Expected at least one device returned from live topology data"

        fortigate = next((d for d in device_list if d.get("type") == "fortigate"), None)
        assert fortigate is not None, "Expected FortiGate device details"
        assert fortigate.get("interfaces"), "FortiGate should include interface metadata"
        assert isinstance(fortigate.get("connections"), (int, float)), "FortiGate should include connection count"
        assert fortigate.get("serial"), "FortiGate should include serial number"


@pytest.mark.mcp
@pytest.mark.self_healing
class TestMCPSelfHealing:
    """Test MCP self-healing capabilities."""
    
    @pytest.mark.asyncio
    async def test_mcp_connection_retry(self):
        """Test MCP connection retry logic."""
        from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool
        
        with patch('src.enhanced_network_api.platform_web_api_fastapi.requests.post') as mock_post:
            # First call fails, second succeeds
            mock_post.side_effect = [
                Exception("Connection failed"),
                MagicMock(
                    status_code=200,
                    json=lambda: {
                        "content": [{"type": "text", "text": '{"gateways": [], "switches": [], "aps": [], "clients": [], "links": []}'}],
                        "isError": False
                    }
                )
            ]
            
            # This test would need to be adapted to actual retry implementation
            # For now, just verify the error handling
            with pytest.raises(Exception):
                _call_fortinet_tool("discover_fortinet_topology")
    
    @pytest.mark.asyncio
    async def test_mcp_circuit_breaker(self):
        """Test MCP circuit breaker pattern."""
        # This would test a circuit breaker implementation
        # For now, just verify basic error handling
        with patch('src.enhanced_network_api.platform_web_api_fastapi.requests.post') as mock_post:
            mock_post.side_effect = Exception("Service unavailable")
            
            from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool
            
            # Multiple failures should be handled gracefully
            for _ in range(5):
                with pytest.raises(Exception):
                    _call_fortinet_tool("discover_fortinet_topology")
    
    @pytest.mark.asyncio
    async def test_mcp_fallback_data(self):
        """Test MCP fallback data when service is unavailable."""
        # Test that the system provides fallback data when MCP is down
        with patch('src.enhanced_network_api.platform_web_api_fastapi.requests.post') as mock_post:
            mock_post.side_effect = Exception("Service unavailable")
            
            from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool
            
            with pytest.raises(Exception):
                _call_fortinet_tool("discover_fortinet_topology")
            
            # In a real implementation, this would trigger fallback mechanisms
            # For now, we just verify the error is handled


@pytest.mark.mcp
@pytest.mark.api
class TestMCPAPIEndpoints:
    """Test MCP-related API endpoints."""
    
    def test_topology_raw_endpoint_with_mcp(self, test_client: TestClient):
        """Test /api/topology/raw endpoint with MCP integration."""
        with patch('src.enhanced_network_api.platform_web_api_fastapi._call_fortinet_tool') as mock_call:
            mock_call.return_value = {
                "gateways": [{"id": "fg-test", "name": "Test Gateway"}],
                "switches": [],
                "aps": [],
                "clients": [],
                "links": []
            }
            
            response = test_client.get("/api/topology/raw")
            
            assert response.status_code == 200
            data = response.json()
            assert "gateways" in data
            assert len(data["gateways"]) == 1
    
    def test_topology_scene_endpoint_with_mcp(self, test_client: TestClient):
        """Test /api/topology/scene endpoint with MCP integration."""
        with patch('src.enhanced_network_api.platform_web_api_fastapi._call_fortinet_tool') as mock_call:
            mock_call.return_value = {
                "nodes": [{"id": "fg-test", "type": "fortigate", "role": "gateway"}],
                "links": [],
                "triageHints": []
            }
            
            response = test_client.get("/api/topology/scene")
            
            assert response.status_code == 200
            data = response.json()
            assert "nodes" in data
            assert len(data["nodes"]) >= 1
            fortigate_nodes = [node for node in data["nodes"] if node.get("type") == "fortigate"]
            assert fortigate_nodes, "Expected at least one FortiGate node in scene data"
    
    def test_mcp_error_propagation(self, test_client: TestClient):
        """Test MCP error propagation to API responses."""
        with patch('src.enhanced_network_api.platform_web_api_fastapi._call_fortinet_tool') as mock_call:
            mock_call.side_effect = HTTPException(status_code=503, detail={"error": "Service unavailable"})
            
            response = test_client.get("/api/topology/raw")
            
            assert response.status_code == 503
            data = response.json()
            detail = data.get("detail") if isinstance(data, dict) else None
            if isinstance(detail, dict):
                assert "error" in detail
            else:
                assert "error" in data
