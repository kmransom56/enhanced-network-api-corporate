#!/usr/bin/env python3
"""
DrawIO MCP Server for Fortinet/Meraki Network Topology Generation

This MCP server integrates with DrawIO to enable AI-assisted network diagram generation
from FortiManager and Meraki API data using natural language commands.

Author: Enhanced Network API Team
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass
from datetime import datetime

# MCP imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult, ReadResourceRequest, ReadResourceResult,
    ListResourcesRequest, ListResourcesResult, ListToolsRequest, ListToolsResult
)

# FortiManager and Meraki imports
try:
    from fortiosapi import FortiOSAPI as FortiGateAPI
except ImportError:
    print("Warning: fortiosapi not installed. Install with: pip install fortiosapi")
    FortiGateAPI = None

try:
    import meraki
except ImportError:
    print("Warning: meraki not installed. Install with: pip install meraki")
    meraki = None

# Import our FortiGate collector
try:
    from .fortigate_collector import FortiGateTopologyCollector
except ImportError:
    try:
        from fortigate_collector import FortiGateTopologyCollector
    except ImportError:
        print("Warning: fortigate_collector not found")
        FortiGateTopologyCollector = None

# Import API documentation and LLM integration
try:
    from .api_documentation import IntelligentAPIMCP
except ImportError:
    try:
        from api_documentation import IntelligentAPIMCP
    except ImportError:
        print("Warning: api_documentation not found")
        IntelligentAPIMCP = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("drawio-fortinet-meraki-mcp")

@dataclass
class NetworkDevice:
    """Represents a network device in the topology"""
    id: str
    name: str
    type: str  # fortigate, fortiswitch, fortiap, meraki_mr, meraki_ms, meraki_mx
    ip: str
    status: str
    model: Optional[str] = None
    serial: Optional[str] = None
    site: Optional[str] = None
    interfaces: Optional[List[Dict]] = None
    health_metrics: Optional[Dict] = None

@dataclass
class NetworkLink:
    """Represents a connection between devices"""
    source_id: str
    target_id: str
    source_interface: Optional[str] = None
    target_interface: Optional[str] = None
    bandwidth: Optional[str] = None
    status: str = "active"
    link_type: str = "physical"

class FortinetMerakiTopologyCollector:
    """Collects topology data from FortiManager and Meraki APIs"""
    
    def __init__(self, fortimanager_config: Dict, meraki_config: Dict):
        self.fortimanager_config = fortimanager_config
        self.meraki_config = meraki_config
        self.fortimanager = None
        self.meraki = None
        
    async def initialize(self):
        """Initialize API connections"""
        try:
            # Initialize FortiManager connection
            if self.fortimanager_config:
                self.fortimanager = FortiGateAPI(
                    host=self.fortimanager_config['host'],
                    username=self.fortimanager_config['username'],
                    password=self.fortimanager_config['password']
                )
                logger.info("Connected to FortiManager")
            
            # Initialize Meraki connection
            if self.meraki_config and meraki:
                self.meraki = meraki.DashboardAPI(
                    api_key=self.meraki_config['api_key'],
                    base_url=self.meraki_config.get('base_url', 'https://api.meraki.com')
                )
                logger.info("Connected to Meraki Dashboard")
                
        except Exception as e:
            logger.error(f"Failed to initialize API connections: {e}")
            raise
    
    async def collect_fortinet_devices(self) -> List[NetworkDevice]:
        """Collect FortiGate, FortiSwitch, and FortiAP devices"""
        devices = []
        
        if not self.fortimanager:
            return devices
            
        try:
            # Get FortiGate devices
            firewalls = self.fortimanager.get('firewall', 'status')
            for fw in firewalls.get('results', []):
                device = NetworkDevice(
                    id=fw.get('serial', fw.get('name', '')),
                    name=fw.get('name', 'Unknown'),
                    type='fortigate',
                    ip=fw.get('ip', ''),
                    status=fw.get('status', 'unknown'),
                    model=fw.get('model', ''),
                    serial=fw.get('serial', ''),
                    site=fw.get('site', '')
                )
                devices.append(device)
            
            # Get FortiSwitch devices
            switches = self.fortimanager.get('switch', 'status')
            for sw in switches.get('results', []):
                device = NetworkDevice(
                    id=sw.get('serial', sw.get('name', '')),
                    name=sw.get('name', 'Unknown'),
                    type='fortiswitch',
                    ip=sw.get('ip', ''),
                    status=sw.get('status', 'unknown'),
                    model=sw.get('model', ''),
                    serial=sw.get('serial', ''),
                    site=sw.get('site', '')
                )
                devices.append(device)
            
            # Get FortiAP devices
            access_points = self.fortimanager.get('wireless', 'status')
            for ap in access_points.get('results', []):
                device = NetworkDevice(
                    id=ap.get('serial', ap.get('name', '')),
                    name=ap.get('name', 'Unknown'),
                    type='fortiap',
                    ip=ap.get('ip', ''),
                    status=ap.get('status', 'unknown'),
                    model=ap.get('model', ''),
                    serial=ap.get('serial', ''),
                    site=ap.get('site', '')
                )
                devices.append(device)
                
        except Exception as e:
            logger.error(f"Failed to collect Fortinet devices: {e}")
            
        return devices
    
    async def collect_meraki_devices(self) -> List[NetworkDevice]:
        """Collect Meraki MX, MS, and MR devices"""
        devices = []
        
        if not self.meraki:
            return devices
            
        try:
            # Get organization devices
            organizations = self.meraki.organizations.getOrganizations()
            
            for org in organizations:
                org_devices = self.meraki.organizations.getOrganizationDevices(org['id'])
                
                for device in org_devices:
                    device_type = device.get('model', '').split('_')[0].lower()
                    
                    # Map Meraki model types to our types
                    type_mapping = {
                        'mx': 'meraki_mx',
                        'ms': 'meraki_ms', 
                        'mr': 'meraki_mr'
                    }
                    
                    device = NetworkDevice(
                        id=device.get('serial', ''),
                        name=device.get('name', 'Unknown'),
                        type=type_mapping.get(device_type, 'meraki_unknown'),
                        ip=device.get('lanIp', ''),
                        status=device.get('status', 'unknown'),
                        model=device.get('model', ''),
                        serial=device.get('serial', ''),
                        tags=device.get('tags', [])
                    )
                    devices.append(device)
                    
        except Exception as e:
            logger.error(f"Failed to collect Meraki devices: {e}")
            
        return devices
    
    async def collect_topology_links(self) -> List[NetworkLink]:
        """Collect network links and connections between devices"""
        links = []
        
        # This would require additional API calls to get interface connections
        # For now, return empty list - can be enhanced with CDP/LLDP data
        
        return links
    
    async def get_complete_topology(self) -> Dict[str, Any]:
        """Get complete network topology"""
        devices = []
        links = []
        
        # Collect devices from both platforms
        if self.fortimanager:
            fortinet_devices = await self.collect_fortinet_devices()
            devices.extend(fortinet_devices)
            
        if self.meraki:
            meraki_devices = await self.collect_meraki_devices()
            devices.extend(meraki_devices)
        
        # Collect links
        links = await self.collect_topology_links()
        
        return {
            'devices': [device.__dict__ for device in devices],
            'links': [link.__dict__ for link in links],
            'timestamp': datetime.now().isoformat(),
            'total_devices': len(devices),
            'total_links': len(links)
        }

class DrawIOMCPServer:
    """Main MCP Server for DrawIO integration"""
    
    def __init__(self):
        self.server = Server("drawio-fortinet-meraki")
        self.fortigate_collector = None
        self.intelligent_api = None
        
        # Register handlers
        self.server.list_tools = self.list_tools
        self.server.call_tool = self.call_tool
        self.server.list_resources = self.list_resources
        self.server.get_resource = self.get_resource
        
        # Store current topology data
        self.current_topology = None
        
    async def initialize_topology_collector(self):
        """Initialize the FortiGate topology collector and LLM integration"""
        # Load configuration from environment 
        import os
        
        fortigate_host = os.getenv('FORTIGATE_HOSTS') or os.getenv('FORTIMANAGER_HOST')
        fortigate_username = os.getenv('FORTIGATE_USERNAME') or os.getenv('FORTIMANAGER_USERNAME')
        fortigate_password = os.getenv('FORTIGATE_PASSWORD') or os.getenv('FORTIMANAGER_PASSWORD')

        forti_slug = None
        if fortigate_host:
            forti_slug = fortigate_host.replace(".", "_").replace("-", "_").replace(":", "_")

        token_candidates = []
        if forti_slug:
            token_candidates.append(f"FORTIGATE_{forti_slug}_TOKEN")
        token_candidates.extend(["FORTIGATE_TOKEN", "FORTIGATE_DEFAULT_TOKEN"])
        fortigate_token = next((os.getenv(key) for key in token_candidates if os.getenv(key)), None)

        fortigate_port = (
            os.getenv(f"FORTIGATE_{forti_slug}_PORT") if forti_slug else None
        ) or os.getenv('FORTIMANAGER_PORT', '443')
        
        # Initialize FortiGate collector
        if fortigate_host and fortigate_username and FortiGateTopologyCollector:
            if not (fortigate_token or fortigate_password):
                logger.warning("FortiGate collector missing both token and password - using demo data")
            else:
                self.fortigate_collector = FortiGateTopologyCollector(
                    host=fortigate_host,
                    username=fortigate_username,
                    password=fortigate_password,
                    token=fortigate_token,
                    port=int(fortigate_port),
                    verify_ssl=False
                )
                logger.info(f"FortiGate collector initialized for {fortigate_host}:{fortigate_port}")
                logger.info(f"Username: {fortigate_username}")
                logger.info(f"Token supplied: {'✅' if fortigate_token else '❌'} / Password supplied: {'✅' if fortigate_password else '❌'}")
                return

        # Fallback if configuration incomplete
        logger.warning("FortiGate collector not configured - will use demo data")
        logger.warning(f"Host: {fortigate_host}, Username: {fortigate_username}, Token: {'✅' if fortigate_token else '❌'}, Password: {'✅' if fortigate_password else '❌'}")
        
        # Initialize collector with demo defaults to keep interface usable
        if FortiGateTopologyCollector:
            self.fortigate_collector = FortiGateTopologyCollector(
                host=fortigate_host or "192.168.0.254",
                username=fortigate_username or "admin",
                password=None,
                token=None,
                port=int(fortigate_port or 10443),
                verify_ssl=False
            )
        
        # Initialize Intelligent API with LLM
        llm_base_url = os.getenv('LLM_BASE_URL', 'http://localhost:11434')
        llm_model = os.getenv('LLM_MODEL', 'fortinet-custom')
        
        if IntelligentAPIMCP:
            try:
                self.intelligent_api = IntelligentAPIMCP()
                await self.intelligent_api.initialize(llm_base_url, llm_model)
                logger.info(f"Intelligent API initialized with LLM: {llm_model} at {llm_base_url}")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM integration: {e}")
                self.intelligent_api = None
    
    async def list_tools(self) -> List[Tool]:
        """List available MCP tools"""
        return [
            Tool(
                name="collect_topology",
                description="Collect network topology from FortiGate API",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "refresh": {
                            "type": "boolean",
                            "description": "Force refresh of topology data",
                            "default": False
                        },
                        "device_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by device types (fortigate, network, vip)",
                            "default": []
                        }
                    }
                }
            ),
            Tool(
                name="generate_drawio_diagram",
                description="Generate DrawIO diagram from collected topology data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "layout": {
                            "type": "string",
                            "enum": ["hierarchical", "circular", "force-directed", "custom"],
                            "description": "Diagram layout style",
                            "default": "hierarchical"
                        },
                        "group_by": {
                            "type": "string",
                            "enum": ["site", "type", "vendor", "none"],
                            "description": "Group devices by category",
                            "default": "type"
                        },
                        "show_details": {
                            "type": "boolean",
                            "description": "Include device details in labels",
                            "default": True
                        },
                        "color_code": {
                            "type": "boolean", 
                            "description": "Color code devices by type/status",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="get_topology_summary",
                description="Get summary of collected network topology",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="export_topology_json",
                description="Export topology data as JSON for external tools",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_health": {
                            "type": "boolean",
                            "description": "Include health metrics in export",
                            "default": False
                        },
                        "format": {
                            "type": "string",
                            "enum": ["json", "csv", "yaml"],
                            "description": "Export format",
                            "default": "json"
                        }
                    }
                }
            ),
            Tool(
                name="query_api_documentation",
                description="Query FortiGate and Meraki API documentation using natural language",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query about API endpoints"
                        },
                        "device_type": {
                            "type": "string",
                            "enum": ["fortigate", "meraki", "all"],
                            "description": "Filter by device type",
                            "default": "all"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="generate_api_request",
                description="Generate API requests using LLM based on natural language",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language description of desired API operation"
                        },
                        "device_info": {
                            "type": "object",
                            "description": "Device information for context",
                            "properties": {
                                "type": {"type": "string"},
                                "ip": {"type": "string"},
                                "model": {"type": "string"}
                            }
                        },
                        "device_type": {
                            "type": "string",
                            "enum": ["fortigate", "meraki"],
                            "description": "Target device type",
                            "default": "fortigate"
                        }
                    },
                    "required": ["query"]
                }
            ),
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Execute MCP tool calls"""
        
        if name == "collect_topology":
            return await self.collect_topology(arguments)
        
        elif name == "generate_drawio_diagram":
            return await self.generate_drawio_diagram(arguments)
        
        elif name == "get_topology_summary":
            return await self.get_topology_summary(arguments)
        
        elif name == "export_topology_json":
            return await self.export_topology_json(arguments)
        
        elif name == "query_api_documentation":
            return await self.query_api_documentation(arguments)
        
        elif name == "generate_api_request":
            return await self.generate_api_request(arguments)
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def collect_topology(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Collect network topology data"""
        try:
            refresh = arguments.get("refresh", False)
            device_types = arguments.get("device_types", [])
            
            if not self.fortigate_collector:
                # No collector configured: return an explicit error instead of demo data
                error_text = "FortiGate collector is not configured; unable to collect topology (no demo fallback)."
                return CallToolResult(
                    content=[TextContent(type="text", text=error_text)],
                    isError=True,
                )
            
            # Collect real topology data from FortiGate
            topology = await self.fortigate_collector.collect_topology()
            
            # Filter by device types if specified
            if device_types:
                topology['devices'] = [
                    device for device in topology['devices']
                    if device.get('type') in device_types
                ]
                topology['total_devices'] = len(topology['devices'])
            
            self.current_topology = topology

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(topology, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"Error collecting topology: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True
            )
    
    async def generate_drawio_diagram(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Generate DrawIO diagram from topology data"""
        try:
            if not self.current_topology:
                # Collect topology first
                await self.collect_topology({})
            
            layout = arguments.get("layout", "hierarchical")
            group_by = arguments.get("group_by", "type")
            show_details = arguments.get("show_details", True)
            color_code = arguments.get("color_code", True)
            
            # Generate DrawIO XML
            diagram_xml = self.generate_drawio_xml(
                self.current_topology,
                layout=layout,
                group_by=group_by,
                show_details=show_details,
                color_code=color_code
            )
            
            return CallToolResult(
                content=[
                    TextContent(type="text", text=diagram_xml)
                ]
            )
            
        except Exception as e:
            logger.error(f"Error generating diagram: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True
            )
    
    async def get_topology_summary(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get topology summary"""
        try:
            if not self.current_topology:
                await self.collect_topology({})
            
            devices = self.current_topology['devices']
            links = self.current_topology['links']
            
            # Count devices by type
            device_counts = {}
            for device in devices:
                device_type = device.get('type', 'unknown')
                device_counts[device_type] = device_counts.get(device_type, 0) + 1
            
            # Count links by type
            link_counts = {}
            for link in links:
                link_type = link.get('link_type', 'unknown')
                link_counts[link_type] = link_counts.get(link_type, 0) + 1
            
            summary = {
                "total_devices": len(devices),
                "total_links": len(links),
                "device_types": device_counts,
                "link_types": link_counts,
                "last_updated": self.current_topology.get('timestamp'),
                "sites": list(set(d.get('site', 'Unknown') for d in devices if d.get('site')))
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(summary, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True
            )
    
    async def export_topology_json(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Export topology data"""
        try:
            if not self.current_topology:
                await self.collect_topology({})
            
            include_health = arguments.get("include_health", False)
            format_type = arguments.get("format", "json")
            
            export_data = {
                "topology": self.current_topology,
                "export_timestamp": datetime.now().isoformat(),
                "export_format": format_type
            }
            
            if format_type == "json":
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(export_data, indent=2))]
                )
            elif format_type == "csv":
                # Convert to CSV format
                csv_data = self.convert_to_csv(export_data)
                return CallToolResult(
                    content=[TextContent(type="text", text=csv_data)]
                )
            elif format_type == "yaml":
                try:
                    import yaml
                    yaml_data = yaml.dump(export_data, default_flow_style=False)
                    return CallToolResult(
                        content=[TextContent(type="text", text=yaml_data)]
                    )
                except ImportError:
                    return CallToolResult(
                        content=[TextContent(type="text", text="YAML export requires PyYAML: pip install PyYAML")],
                        isError=True
                    )
            
        except Exception as e:
            logger.error(f"Error exporting topology: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True
            )
    
    async def list_resources(self) -> ListResourcesResult:
        """List available resources"""
        return ListResourcesResult(resources=[
            Resource(
                uri="topology://current",
                name="Current Network Topology",
                description="Latest collected network topology data",
                mimeType="application/json"
            ),
            Resource(
                uri="topology://summary",
                name="Topology Summary",
                description="Summary statistics of network topology",
                mimeType="application/json"
            )
        ])
    
    async def get_resource(self, uri: str) -> ReadResourceResult:
        """Get specific resource"""
        if uri == "topology://current":
            if not self.current_topology:
                await self.collect_topology({})
            return ReadResourceResult(
                contents=[TextContent(type="text", text=json.dumps(self.current_topology, indent=2))]
            )
        
        elif uri == "topology://summary":
            summary_result = await self.get_topology_summary({})
            return ReadResourceResult(contents=summary_result.content)
        
        else:
            raise ValueError(f"Unknown resource: {uri}")
    
    def get_demo_topology(self) -> Dict[str, Any]:
        """Generate demo topology data for testing"""
        return {
            "devices": [
                {
                    "id": "fg-001",
                    "name": "FortiGate-HQ",
                    "type": "fortigate",
                    "ip": "192.168.1.1",
                    "status": "active",
                    "model": "FG600E",
                    "serial": "FG600E1234567890",
                    "site": "Headquarters"
                },
                {
                    "id": "ms-001", 
                    "name": "CoreSwitch-01",
                    "type": "fortiswitch",
                    "ip": "192.168.1.10",
                    "status": "active",
                    "model": "FS-124E",
                    "serial": "FS124E1234567890",
                    "site": "Headquarters"
                },
                {
                    "id": "mr-001",
                    "name": "AP-HQ-Floor1",
                    "type": "meraki_mr",
                    "ip": "192.168.1.101",
                    "status": "active",
                    "model": "MR42",
                    "serial": "Q2XX-XXXX-XXXX",
                    "site": "Headquarters"
                }
            ],
            "links": [
                {
                    "source_id": "fg-001",
                    "target_id": "ms-001",
                    "source_interface": "port1",
                    "target_interface": "port24",
                    "link_type": "physical",
                    "bandwidth": "1Gbps",
                    "status": "active"
                },
                {
                    "source_id": "ms-001",
                    "target_id": "mr-001",
                    "source_interface": "port1",
                    "target_interface": "eth0",
                    "link_type": "physical",
                    "bandwidth": "1Gbps",
                    "status": "active"
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "total_devices": 3,
            "total_links": 2
        }
    
    def generate_drawio_xml(self, topology: Dict, layout: str = "hierarchical", 
                           group_by: str = "type", show_details: bool = True, 
                           color_code: bool = True) -> str:
        """Generate DrawIO XML from topology data"""
        
        devices = topology.get('devices', [])
        links = topology.get('links', [])
        
        # If no devices, return empty XML - NO DEMO DATA
        if not devices:
            return '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="{}" agent="5.0" etag="{}" version="21.6.5" type="device">
  <diagram name="Network Topology" id="topology">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="2" value="No topology data available" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=20;fontColor=#FF0000;" vertex="1" parent="1">
          <mxGeometry x="400" y="350" width="300" height="60" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''.format(datetime.now().isoformat(), datetime.now().timestamp())
        
        # DrawIO XML template
        timestamp = datetime.now()
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="{modified}" agent="5.0" etag="{etag}" version="21.6.5" type="device">
  <diagram name="Network Topology" id="topology">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
{cells}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
        
        cells = []
        cell_id = 2
        
        # Position devices based on layout
        try:
            positions = self.calculate_positions(devices, layout, group_by)
        except Exception as e:
            # Fallback positioning
            positions = {}
            for i, device in enumerate(devices):
                positions[device['id']] = {'x': 100 + (i % 3) * 200, 'y': 100 + (i // 3) * 150}
        
        # Create device cells
        for device in devices:
            pos = positions.get(device['id'], {'x': 100, 'y': 100})
            try:
                style = self.get_device_style(device, color_code)
            except Exception as e:
                style = 'shape=rectangle;whiteSpace=wrap;html=1;fillColor=#6c757d;strokeColor=#495057;fontColor=#ffffff;'
            
            label = device.get('name', 'Unknown Device')
            if show_details:
                label += f"\\n{device.get('ip', 'N/A')}\\n{device.get('model', '')}"
            
            cell_xml = f'''
        <mxCell id="{cell_id}" value="{label}" style="{style}" vertex="1" parent="1">
          <mxGeometry x="{pos['x']}" y="{pos['y']}" width="120" height="60" as="geometry" />
        </mxCell>'''
            
            cells.append(cell_xml)
            device['cell_id'] = cell_id
            cell_id += 1
        
        # Create link cells
        for link in links:
            source_device = next((d for d in devices if d['id'] == link['source_id']), None)
            target_device = next((d for d in devices if d['id'] == link['target_id']), None)
            
            if source_device and target_device:
                try:
                    link_style = self.get_link_style(link)
                except Exception as e:
                    link_style = 'strokeColor=#6c757d;strokeWidth=2;endArrow=none;startArrow=none;'
                
                source_pos = positions.get(source_device['id'], {'x': 100, 'y': 100})
                target_pos = positions.get(target_device['id'], {'x': 200, 'y': 200})
                
                cell_xml = f'''
        <mxCell id="{cell_id}" style="{link_style}" edge="1" parent="1" source="{source_device['cell_id']}" target="{target_device['cell_id']}">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="{source_pos['x'] + 60}" y="{source_pos['y'] + 30}" as="sourcePoint" />
            <mxPoint x="{target_pos['x'] + 60}" y="{target_pos['y'] + 30}" as="targetPoint" />
          </mxGeometry>
        </mxCell>'''
                
                cells.append(cell_xml)
                cell_id += 1
        
        # Insert cells into XML
        cells_html = "".join(cells)
        final_xml = xml_template.format(
            modified=timestamp.isoformat(),
            etag=timestamp.timestamp(),
            cells=cells_html
        )
        
        return final_xml
    
    def calculate_positions(self, devices: List[Dict], layout: str, group_by: str) -> Dict[str, Dict]:
        """Calculate device positions based on layout"""
        positions = {}
        
        if layout == "hierarchical":
            # Group by type and arrange in layers
            layers = {"fortigate": 0, "meraki_mx": 0, "fortiswitch": 1, "meraki_ms": 1, "fortiap": 2, "meraki_mr": 2}
            
            layer_devices = {}
            for device in devices:
                layer = layers.get(device['type'], 3)
                if layer not in layer_devices:
                    layer_devices[layer] = []
                layer_devices[layer].append(device)
            
            for layer, layer_devs in layer_devices.items():
                x_start = 100
                y_start = 100 + layer * 150
                spacing = 200
                
                for i, device in enumerate(layer_devs):
                    positions[device['id']] = {
                        'x': x_start + i * spacing,
                        'y': y_start
                    }
        
        elif layout == "circular":
            # Arrange devices in a circle
            center_x, center_y = 400, 300
            radius = 200
            angle_step = 2 * 3.14159 / len(devices)
            
            for i, device in enumerate(devices):
                angle = i * angle_step
                positions[device['id']] = {
                    'x': center_x + radius * (3.14159 + angle),
                    'y': center_y + radius * (3.14159 + angle)
                }
        
        else:  # force-directed or custom
            # Simple grid layout
            cols = 3
            for i, device in enumerate(devices):
                row = i // cols
                col = i % cols
                positions[device['id']] = {
                    'x': 100 + col * 200,
                    'y': 100 + row * 150
                }
        
        return positions
    
    def get_device_style(self, device: Dict, color_code: bool) -> str:
        """Get DrawIO style for device based on type and status"""
        base_styles = {
            'fortigate': 'shape=cloud;whiteSpace=wrap;html=1;fillColor=#1ba1e2;strokeColor=#006EAF;fontColor=#ffffff;',
            'fortiswitch': 'shape=rectangle;whiteSpace=wrap;html=1;fillColor=#60a917;strokeColor=#2D7600;fontColor=#ffffff;',
            'fortiap': 'shape=ellipse;whiteSpace=wrap;html=1;fillColor=#f5a623;strokeColor=#B79500;fontColor=#ffffff;',
            'meraki_mx': 'shape=cloud;whiteSpace=wrap;html=1;fillColor=#dc3545;strokeColor=#A71E2A;fontColor=#ffffff;',
            'meraki_ms': 'shape=rectangle;whiteSpace=wrap;html=1;fillColor=#28a745;strokeColor="#1E7E34";fontColor=#ffffff;',
            'meraki_mr': 'shape=ellipse;whiteSpace=wrap;html=1;fillColor=#ffc107;strokeColor="#D39E00";fontColor=#000000;'
        }
        
        style = base_styles.get(device['type'], 'shape=rectangle;whiteSpace=wrap;html=1;fillColor=#6c757d;strokeColor="#495057";fontColor=#ffffff;')
        
        # Modify style based on status
        if device.get('status') != 'active' and color_code:
            style = style.replace('fillColor=#', 'fillColor=#dc3545;')
        
        return style
    
    def get_link_style(self, link: Dict) -> str:
        """Get DrawIO style for link based on type"""
        link_styles = {
            'fortilink': 'strokeColor=#1ba1e2;strokeWidth=3;endArrow=none;startArrow=none;',
            'wired': 'strokeColor=#60a917;strokeWidth=2;endArrow=none;startArrow=none;',
            'wifi': 'strokeColor=#f5a623;strokeWidth=2;dashed=1;endArrow=none;startArrow=none;',
            'wan': 'strokeColor=#dc3545;strokeWidth=3;endArrow=block;startArrow=none;',
            'lan': 'strokeColor=#28a745;strokeWidth=2;endArrow=none;startArrow=none;'
        }
        
        return link_styles.get(link['type'], 'strokeColor=#6c757d;strokeWidth=2;endArrow=none;startArrow=none;')
    
    def convert_to_csv(self, data: Dict) -> str:
        """Convert topology data to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        
        # Devices CSV
        data_topology = data.get('topology', data)
        devices = data_topology.get('devices', [])
        if devices:
            fieldnames = set()
            for device in devices:
                fieldnames.update(device.keys())
            writer = csv.DictWriter(output, fieldnames=sorted(fieldnames))
            writer.writeheader()
            for device in devices:
                writer.writerow({key: device.get(key, "") for key in writer.fieldnames})
        
        return output.getvalue()
    
    async def query_api_documentation(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Query API documentation using natural language"""
        try:
            if not self.intelligent_api:
                return CallToolResult(
                    content=[TextContent(type="text", text="❌ LLM integration not available")],
                    isError=True
                )
            
            query = arguments.get("query", "")
            device_type = arguments.get("device_type", "all")
            
            results = await self.intelligent_api.query_api_documentation(query, device_type)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(results, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"Error querying API documentation: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True
            )
    
    async def generate_api_request(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Generate API requests using LLM"""
        try:
            if not self.intelligent_api:
                return CallToolResult(
                    content=[TextContent(type="text", text="❌ LLM integration not available")],
                    isError=True
                )
            
            query = arguments.get("query", "")
            device_info = arguments.get("device_info", {})
            device_type = arguments.get("device_type", "fortigate")
            
            # Use current topology device info if not provided
            if not device_info and self.current_topology:
                devices = self.current_topology.get('topology', {}).get('devices', [])
                if devices:
                    device_info = {
                        "type": devices[0].get('type', 'unknown'),
                        "ip": devices[0].get('ip', 'unknown'),
                        "model": devices[0].get('model', 'unknown')
                    }
            
            request = await self.intelligent_api.generate_api_request(query, device_info, device_type)
            
            result = {
                "generated_request": {
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "url": request.url,
                    "headers": request.headers,
                    "body": request.body,
                    "description": request.description,
                    "confidence": request.confidence
                },
                "device_context": device_info,
                "query": query
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"Error generating API request: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True
            )

async def main():
    """Main server entry point"""
    server = DrawIOMCPServer()
    
    # Initialize topology collector
    await server.initialize_topology_collector()
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="drawio-fortinet-meraki",
                server_version="1.0.0",
                capabilities={
                    "tools": {},
                    "resources": {}
                }
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
