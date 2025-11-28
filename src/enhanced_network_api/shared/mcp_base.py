"""
Shared MCP Base Classes and Patterns
Extracted from network-device-mcp-server for reuse across platforms
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod

import httpx
from mcp import types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent

# Import configuration management
from .config_manager import config_manager

logger = logging.getLogger(__name__)

class BaseMCPManager(ABC):
    """
    Base class for MCP platform managers
    Provides common patterns for device communication and tool registration
    """
    
    def __init__(self, name: str, timeout: float = 30.0):
        self.name = name
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, verify=False)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @abstractmethod
    async def authenticate(self, **credentials) -> bool:
        """Authenticate with the platform"""
        pass
    
    @abstractmethod
    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of managed devices"""
        pass
    
    @abstractmethod
    async def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get status of a specific device"""
        pass

class FortiGateManager(BaseMCPManager):
    """
    Enhanced FortiGate manager with patterns from network-device-mcp-server
    Integrated with configuration management
    """
    
    def __init__(self):
        super().__init__("fortigate")
        self.auth_tokens = {}  # host -> token mapping
        self.configs = {}  # host -> FortiGateConfig mapping
    
    async def initialize_from_config(self):
        """Initialize from configuration manager"""
        configs = config_manager.get_all_fortigate_configs()
        self.configs = configs
        
        # Authenticate with all configured devices
        for host, config in configs.items():
            success = await self.authenticate(host, config.token)
            if success:
                logger.info(f"Authenticated with FortiGate {host}")
            else:
                logger.warning(f"Failed to authenticate with FortiGate {host}")
    
    async def authenticate(self, host: str, token: str) -> bool:
        """Authenticate with FortiGate device"""
        try:
            # Test authentication with system status
            await self.get_system_status(host, token)
            self.auth_tokens[host] = token
            return True
        except Exception as e:
            logger.error(f"FortiGate auth failed for {host}: {e}")
            return False
    
    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get managed FortiGate devices from configuration"""
        devices = []
        
        # Use configured devices
        for host, config in self.configs.items():
            try:
                status = await self.get_system_status(host, config.token)
                devices.append({
                    "id": f"fg-{host}",
                    "host": host,
                    "type": "fortigate",
                    "status": "online",
                    "name": config.name,
                    "info": status
                })
            except Exception as e:
                logger.warning(f"Failed to get status for {host}: {e}")
                devices.append({
                    "id": f"fg-{host}",
                    "host": host,
                    "type": "fortigate", 
                    "status": "offline",
                    "name": config.name,
                    "error": str(e)
                })
        
        return devices
    
    async def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get detailed status of FortiGate device"""
        host = device_id.replace("fg-", "")
        config = self.configs.get(host)
        if not config:
            raise ValueError(f"No configuration for {host}")
        
        return await self.get_system_status(host, config.token)
    
    async def _make_request(self, host: str, token: str, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Make API request to FortiGate device - pattern from network-device-mcp-server"""
        config = self.configs.get(host)
        port = config.port if config else 10443
        
        url = f"https://{host}:{port}/api/v2/{endpoint.lstrip('/')}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if method.upper() == "GET":
            response = await self.client.get(url, headers=headers)
        elif method.upper() == "POST": 
            response = await self.client.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = await self.client.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = await self.client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    async def get_system_status(self, host: str, token: str) -> dict:
        """Get FortiGate system status - enhanced from network-device-mcp-server"""
        try:
            result = await self._make_request(host, token, "/monitor/system/status")
            
            if "results" in result:
                status_data = result["results"]
                return {
                    "hostname": status_data.get("hostname"),
                    "version": status_data.get("version"),
                    "serial": status_data.get("serial"),
                    "model": status_data.get("model"),
                    "uptime": status_data.get("uptime"),
                    "cpu_usage": status_data.get("cpu_usage"),
                    "memory_usage": status_data.get("memory_usage"),
                    "status": "online"
                }
            return result
        except Exception as e:
            logger.error(f"Failed to get system status from {host}: {e}")
            return {"status": "offline", "error": str(e)}
    
    async def get_firewall_policies(self, host: str, token: str, policy_type: str = "policy") -> dict:
        """Get firewall policies - new method for smart analysis"""
        try:
            endpoint = f"/monitor/firewall/{policy_type}"
            result = await self._make_request(host, token, endpoint)
            return result
        except Exception as e:
            logger.error(f"Failed to get {policy_type} policies from {host}: {e}")
            return {"policies": [], "error": str(e)}
    
    async def get_logs(self, host: str, token: str, log_filter: dict = None) -> dict:
        """Get device logs - new method for troubleshooting"""
        try:
            endpoint = "/monitor/log"
            if log_filter:
                # Add filter parameters
                params = "&".join([f"{k}={v}" for k, v in log_filter.items()])
                endpoint += f"?{params}"
            
            result = await self._make_request(host, token, endpoint)
            return result
        except Exception as e:
            logger.error(f"Failed to get logs from {host}: {e}")
            return {"logs": [], "error": str(e)}

class MerakiManager(BaseMCPManager):
    """
    Enhanced Meraki manager with patterns from network-device-mcp-server
    Integrated with configuration management
    """
    
    def __init__(self):
        super().__init__("meraki")
        self.config = None
    
    async def initialize_from_config(self):
        """Initialize from configuration manager"""
        self.config = config_manager.get_meraki_config()
        if self.config:
            success = await self.authenticate(self.config.api_key)
            if success:
                logger.info("Authenticated with Meraki API")
            else:
                logger.warning("Failed to authenticate with Meraki API")
    
    async def authenticate(self, api_key: str) -> bool:
        """Authenticate with Meraki API"""
        try:
            # Test authentication with organizations endpoint
            headers = {
                "X-Cisco-Meraki-API-Key": api_key,
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.config.base_url}/organizations", headers=headers)
                response.raise_for_status()
                self.config.api_key = api_key
                return True
        except Exception as e:
            logger.error(f"Meraki auth failed: {e}")
            return False
    
    async def get_devices(self, organization_id: str = None, network_id: str = None) -> List[Dict[str, Any]]:
        """Get Meraki devices"""
        if not self.config:
            return []
        
        headers = {"X-Cisco-Meraki-API-Key": self.config.api_key}
        
        try:
            if network_id:
                # Get devices in specific network
                url = f"{self.config.base_url}/networks/{network_id}/devices"
            elif organization_id:
                # Get all networks and their devices
                url = f"{self.config.base_url}/organizations/{organization_id}/networks"
                async with self.client.get(url, headers=headers) as response:
                    networks = response.json()
                    devices = []
                    for network in networks:
                        network_devices = await self.get_devices(organization_id, network["id"])
                        devices.extend(network_devices)
                    return devices
            else:
                return []
            
            async with self.client.get(url, headers=headers) as response:
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get Meraki devices: {e}")
            return []
    
    async def get_device_status(self, device_serial: str) -> Dict[str, Any]:
        """Get status of Meraki device"""
        if not self.config:
            return {"status": "offline", "error": "No Meraki configuration"}
        
        headers = {"X-Cisco-Meraki-API-Key": self.config.api_key}
        
        try:
            url = f"{self.config.base_url}/devices/{device_serial}"
            async with self.client.get(url, headers=headers) as response:
                device_data = response.json()
                return {
                    "serial": device_data.get("serial"),
                    "model": device_data.get("model"),
                    "name": device_data.get("name"),
                    "networkId": device_data.get("networkId"),
                    "status": device_data.get("status", "offline"),
                    "tags": device_data.get("tags", []),
                    "lanIp": device_data.get("lanIp"),
                    "wan1Ip": device_data.get("wan1Ip"),
                    "wan2Ip": device_data.get("wan2Ip")
                }
        except Exception as e:
            logger.error(f"Failed to get Meraki device status: {e}")
            return {"status": "offline", "error": str(e)}
    
    async def get_network_policies(self, network_id: str) -> dict:
        """Get network policies - for smart analysis"""
        if not self.config:
            return {"policies": [], "error": "No Meraki configuration"}
        
        headers = {"X-Cisco-Meraki-API-Key": self.config.api_key}
        
        try:
            # Get firewall rules
            url = f"{self.config.base_url}/networks/{network_id}/firewall/rules"
            async with self.client.get(url, headers=headers) as response:
                return {"policies": response.json()}
        except Exception as e:
            logger.error(f"Failed to get Meraki policies: {e}")
            return {"policies": [], "error": str(e)}

class BaseMCPServer:
    """
    Base MCP server with tool registration patterns from network-device-mcp-server
    """
    
    def __init__(self, name: str):
        self.server = Server(name)
        self.tools = {}
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup MCP handlers"""
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return list(self.tools.values())
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent]:
            if name not in self.tools:
                raise ValueError(f"Unknown tool: {name}")
            
            tool_handler = self.tools[name]["handler"]
            try:
                result = await tool_handler(arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                error_result = {"error": str(e), "tool": name}
                return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    def register_tool(self, name: str, description: str, input_schema: dict, handler: Callable):
        """Register a tool with the server - pattern from network-device-mcp-server"""
        self.tools[name] = {
            "tool": Tool(
                name=name,
                description=description,
                inputSchema=input_schema
            ),
            "handler": handler
        }
    
    def register_fortinet_tools(self, fortigate_manager: FortiGateManager):
        """Register common FortiGate tools"""
        
        async def list_devices_handler(args: dict) -> dict:
            devices = await fortigate_manager.get_devices()
            return {"devices": devices}
        
        async def get_device_status_handler(args: dict) -> dict:
            device_id = args.get("device_id")
            if not device_id:
                raise ValueError("device_id required")
            return await fortigate_manager.get_device_status(device_id)
        
        async def get_policies_handler(args: dict) -> dict:
            device_id = args.get("device_id")
            policy_type = args.get("policy_type", "policy")
            host = device_id.replace("fg-", "")
            config = fortigate_manager.configs.get(host)
            if not config:
                raise ValueError(f"No configuration for {device_id}")
            return await fortigate_manager.get_firewall_policies(host, config.token, policy_type)
        
        async def get_logs_handler(args: dict) -> dict:
            device_id = args.get("device_id")
            log_filter = args.get("filter", {})
            host = device_id.replace("fg-", "")
            config = fortigate_manager.configs.get(host)
            if not config:
                raise ValueError(f"No configuration for {device_id}")
            return await fortigate_manager.get_logs(host, config.token, log_filter)
        
        # Register tools
        self.register_tool(
            "list_fortigate_devices",
            "List all available FortiGate devices",
            {"type": "object", "properties": {}},
            list_devices_handler
        )
        
        self.register_tool(
            "get_fortigate_status",
            "Get system status from a FortiGate device",
            {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string", "description": "FortiGate device ID"}
                },
                "required": ["device_id"]
            },
            get_device_status_handler
        )
        
        self.register_tool(
            "get_fortigate_policies",
            "Get firewall policies from FortiGate device",
            {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string", "description": "FortiGate device ID"},
                    "policy_type": {"type": "string", "default": "policy", "description": "Policy type"}
                },
                "required": ["device_id"]
            },
            get_policies_handler
        )
        
        self.register_tool(
            "get_fortigate_logs",
            "Get logs from FortiGate device",
            {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string", "description": "FortiGate device ID"},
                    "filter": {"type": "object", "description": "Log filters"}
                },
                "required": ["device_id"]
            },
            get_logs_handler
        )
    
    def register_meraki_tools(self, meraki_manager: MerakiManager):
        """Register common Meraki tools"""
        
        async def list_meraki_devices_handler(args: dict) -> dict:
            organization_id = args.get("organization_id")
            network_id = args.get("network_id")
            devices = await meraki_manager.get_devices(organization_id, network_id)
            return {"devices": devices}
        
        async def get_meraki_status_handler(args: dict) -> dict:
            device_serial = args.get("device_serial")
            if not device_serial:
                raise ValueError("device_serial required")
            return await meraki_manager.get_device_status(device_serial)
        
        async def get_meraki_policies_handler(args: dict) -> dict:
            network_id = args.get("network_id")
            if not network_id:
                raise ValueError("network_id required")
            return await meraki_manager.get_network_policies(network_id)
        
        # Register tools
        self.register_tool(
            "list_meraki_devices",
            "List Meraki devices",
            {
                "type": "object",
                "properties": {
                    "organization_id": {"type": "string", "description": "Organization ID"},
                    "network_id": {"type": "string", "description": "Network ID"}
                }
            },
            list_meraki_devices_handler
        )
        
        self.register_tool(
            "get_meraki_status",
            "Get status of Meraki device",
            {
                "type": "object",
                "properties": {
                    "device_serial": {"type": "string", "description": "Device serial number"}
                },
                "required": ["device_serial"]
            },
            get_meraki_status_handler
        )
        
        self.register_tool(
            "get_meraki_policies",
            "Get network policies from Meraki",
            {
                "type": "object",
                "properties": {
                    "network_id": {"type": "string", "description": "Network ID"}
                },
                "required": ["network_id"]
            },
            get_meraki_policies_handler
        )
