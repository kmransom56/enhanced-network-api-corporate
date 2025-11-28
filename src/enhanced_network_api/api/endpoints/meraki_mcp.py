"""
Meraki MCP Server Integration
Connects to Meraki MCP server for cross-platform network analysis
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Meraki MCP server configuration
MERAKI_MCP_CONFIG = {
    "base_url": "http://127.0.0.1:11112",  # Adjust to your Meraki MCP port
    "timeout": 30.0
}

class MCPRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DeviceStatusRequest(BaseModel):
    network_id: Optional[str] = None
    serial: Optional[str] = None
    device_type: Optional[str] = None

class ConnectivityRequest(BaseModel):
    source_device: str
    target_device: str
    test_type: str = "ping"  # ping, traceroute, bandwidth

@router.post("/call-tool", response_model=MCPResponse)
async def call_meraki_mcp_tool(request: MCPRequest):
    """
    Call a tool on the Meraki MCP server
    """
    try:
        async with httpx.AsyncClient(timeout=MERAKI_MCP_CONFIG["timeout"]) as client:
            payload = {
                "name": request.tool_name,
                "arguments": request.arguments
            }

            response = await client.post(
                f"{MERAKI_MCP_CONFIG['base_url']}/mcp/call-tool",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return MCPResponse(success=True, data=result)
            else:
                error_text = response.text
                logger.error(f"Meraki MCP error: {response.status_code} - {error_text}")
                return MCPResponse(
                    success=False, 
                    error=f"MCP call failed: {response.status_code}"
                )

    except httpx.TimeoutException:
        logger.error("Meraki MCP timeout")
        return MCPResponse(success=False, error="Request timeout")
    except Exception as e:
        logger.error(f"Meraki MCP connection error: {e}")
        return MCPResponse(success=False, error=str(e))

@router.post("/device/status")
async def get_meraki_device_status(request: DeviceStatusRequest):
    """
    Get status of Meraki devices
    """
    try:
        # Try different approaches based on provided parameters
        if request.serial:
            # Get specific device by serial
            mcp_request = MCPRequest(
                tool_name="get_device_by_serial",
                arguments={"serial": request.serial}
            )
        elif request.network_id:
            # Get all devices in network
            mcp_request = MCPRequest(
                tool_name="get_network_devices",
                arguments={"network_id": request.network_id}
            )
        else:
            # List all organizations and networks
            mcp_request = MCPRequest(
                tool_name="list_organizations",
                arguments={}
            )

        return await call_meraki_mcp_tool(mcp_request)

    except Exception as e:
        logger.error(f"Device status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connectivity/check")
async def check_connectivity(request: ConnectivityRequest):
    """
    Check connectivity between devices
    """
    try:
        mcp_request = MCPRequest(
            tool_name="check_device_connectivity",
            arguments={
                "source": request.source_device,
                "target": request.target_device,
                "test_type": request.test_type
            }
        )

        return await call_meraki_mcp_tool(mcp_request)

    except Exception as e:
        logger.error(f"Connectivity check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/organizations")
async def list_meraki_organizations():
    """
    List all Meraki organizations
    """
    try:
        mcp_request = MCPRequest(
            tool_name="list_organizations",
            arguments={}
        )
        return await call_meraki_mcp_tool(mcp_request)

    except Exception as e:
        logger.error(f"Organizations list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/networks/{organization_id}")
async def list_organization_networks(organization_id: str):
    """
    List networks in a Meraki organization
    """
    try:
        mcp_request = MCPRequest(
            tool_name="get_organization_networks",
            arguments={"organization_id": organization_id}
        )
        return await call_meraki_mcp_tool(mcp_request)

    except Exception as e:
        logger.error(f"Networks list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/devices/{network_id}")
async def list_network_devices(network_id: str):
    """
    List devices in a Meraki network
    """
    try:
        mcp_request = MCPRequest(
            tool_name="get_network_devices",
            arguments={"network_id": network_id}
        )
        return await call_meraki_mcp_tool(mcp_request)

    except Exception as e:
        logger.error(f"Devices list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients/{network_id}")
async def list_network_clients(network_id: str, timespan: int = 86400):
    """
    List clients in a Meraki network
    """
    try:
        mcp_request = MCPRequest(
            tool_name="get_network_clients",
            arguments={
                "network_id": network_id,
                "timespan": timespan
            }
        )
        return await call_meraki_mcp_tool(mcp_request)

    except Exception as e:
        logger.error(f"Clients list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def meraki_mcp_health():
    """
    Check if Meraki MCP server is healthy
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MERAKI_MCP_CONFIG['base_url']}/health")
            
            if response.status_code == 200:
                return {"status": "healthy", "server": "meraki-mcp"}
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}

    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Cross-platform analysis functions

@router.post("/cross-platform-analysis")
async def cross_platform_analysis(
    fortinet_devices: List[Dict[str, Any]],
    meraki_network_id: Optional[str] = None
):
    """
    Perform cross-platform analysis between Fortinet and Meraki devices
    """
    try:
        analysis_results = {
            "fortinet_devices": fortinet_devices,
            "meraki_devices": [],
            "connectivity_matrix": [],
            "security_analysis": {},
            "recommendations": []
        }

        # Get Meraki devices if network_id provided
        if meraki_network_id:
            devices_response = await list_network_devices(meraki_network_id)
            if devices_response.success and devices_response.data:
                analysis_results["meraki_devices"] = devices_response.data.get("devices", [])

        # Analyze connectivity between platforms
        for fortinet_device in fortinet_devices:
            for meraki_device in analysis_results["meraki_devices"]:
                connectivity_check = await check_connectivity(
                    ConnectivityRequest(
                        source_device=fortinet_device.get("ip", ""),
                        target_device=meraki_device.get("serial", ""),
                        test_type="ping"
                    )
                )
                
                analysis_results["connectivity_matrix"].append({
                    "fortinet": fortinet_device.get("id"),
                    "meraki": meraki_device.get("serial"),
                    "result": connectivity_check.data if connectivity_check.success else None,
                    "status": "connected" if connectivity_check.success else "error"
                })

        # Generate cross-platform recommendations
        analysis_results["recommendations"] = generate_cross_platform_recommendations(
            analysis_results
        )

        return analysis_results

    except Exception as e:
        logger.error(f"Cross-platform analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_cross_platform_recommendations(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate recommendations based on cross-platform analysis
    """
    recommendations = []

    # Check for connectivity issues
    failed_connections = [
        conn for conn in analysis["connectivity_matrix"]
        if conn.get("status") == "error"
    ]

    if failed_connections:
        recommendations.append({
            "type": "connectivity",
            "priority": "high",
            "title": "Cross-platform connectivity issues detected",
            "description": f"{len(failed_connections)} connections between Fortinet and Meraki devices are failing",
            "actions": [
                "Check firewall rules on FortiGate devices",
                "Verify VPN tunnels between sites",
                "Review Meraki device network settings"
            ]
        })

    # Check for security inconsistencies
    fortinet_count = len(analysis["fortinet_devices"])
    meraki_count = len(analysis["meraki_devices"])

    if fortinet_count > 0 and meraki_count > 0:
        recommendations.append({
            "type": "security",
            "priority": "medium",
            "title": "Multi-platform security posture",
            "description": f"Environment has {fortinet_count} Fortinet and {meraki_count} Meraki devices",
            "actions": [
                "Align security policies across platforms",
                "Implement unified threat monitoring",
                "Configure cross-platform logging"
            ]
        })

    return recommendations
