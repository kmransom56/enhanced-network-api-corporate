#!/usr/bin/env python3
"""
Integration bridge with existing Fortinet MCP server
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FortinetDevice:
    """Device from existing Fortinet MCP server"""
    id: str
    name: str
    type: str
    ip: str
    status: str
    model: Optional[str] = None
    serial: Optional[str] = None
    interfaces: Optional[List[Dict]] = None

class FortinetMCPBridge:
    """Bridge between existing Fortinet MCP and DrawIO MCP"""
    
    def __init__(self, fortinet_mcp_host: str = "localhost", fortinet_mcp_port: int = 8000):
        self.fortinet_mcp_host = fortinet_mcp_host
        self.fortinet_mcp_port = fortinet_mcp_port
        
    async def discover_fortinet_topology(self) -> Dict[str, Any]:
        """Call existing Fortinet MCP discover_fortinet_topology tool"""
        try:
            # This would integrate with your existing server_enhanced.py
            # For now, return demo data that matches your existing format
            
            # Simulate calling your existing MCP server
            topology = {
                "content": {
                    "nodes": [
                        {
                            "id": "fg-192.168.0.254",
                            "name": "FortiGate",
                            "type": "fortigate",
                            "serial": "FG600E321X5901234",
                            "status": "active",
                            "ip": "192.168.0.254",
                            "model": "FG600E"
                        },
                        {
                            "id": "sw-001",
                            "name": "CoreSwitch",
                            "type": "fortiswitch", 
                            "serial": "FS124E1234567890",
                            "status": "active",
                            "ip": "192.168.0.10",
                            "model": "FS-124E"
                        },
                        {
                            "id": "ap-001",
                            "name": "WiFi-AP",
                            "type": "fortiap",
                            "serial": "FAP421E1234567890",
                            "status": "active", 
                            "ip": "192.168.0.101",
                            "model": "FAP-421E"
                        }
                    ],
                    "links": [
                        {
                            "source": "fg-192.168.0.254",
                            "target": "sw-001",
                            "source_interface": "port1",
                            "target_interface": "port24",
                            "link_type": "physical",
                            "bandwidth": "1Gbps"
                        },
                        {
                            "source": "sw-001", 
                            "target": "ap-001",
                            "source_interface": "port1",
                            "target_interface": "eth0",
                            "link_type": "physical",
                            "bandwidth": "1Gbps"
                        }
                    ]
                }
            }
            
            logger.info(f"Discovered {len(topology['content']['nodes'])} Fortinet devices")
            return topology
            
        except Exception as e:
            logger.error(f"Failed to discover Fortinet topology: {e}")
            return {"content": {"nodes": [], "links": []}}
    
    def convert_to_drawio_format(self, fortinet_topology: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Fortinet MCP format to DrawIO MCP format"""
        
        content = fortinet_topology.get("content", {})
        nodes = content.get("nodes", [])
        links = content.get("links", [])
        
        # Convert nodes to DrawIO device format
        devices = []
        for node in nodes:
            device = {
                "id": node.get("id", ""),
                "name": node.get("name", "Unknown"),
                "type": node.get("type", "unknown"),
                "ip": node.get("ip", ""),
                "status": node.get("status", "unknown"),
                "model": node.get("model", ""),
                "serial": node.get("serial", ""),
                "site": node.get("site", "Default"),
                "interfaces": node.get("interfaces", [])
            }
            devices.append(device)
        
        # Convert links to DrawIO link format
        drawio_links = []
        for link in links:
            drawio_link = {
                "source_id": link.get("source", ""),
                "target_id": link.get("target", ""),
                "source_interface": link.get("source_interface"),
                "target_interface": link.get("target_interface"),
                "link_type": link.get("link_type", "physical"),
                "bandwidth": link.get("bandwidth"),
                "status": link.get("status", "active")
            }
            drawio_links.append(drawio_link)
        
        return {
            "devices": devices,
            "links": drawio_links,
            "timestamp": asyncio.get_event_loop().time(),
            "total_devices": len(devices),
            "total_links": len(drawio_links),
            "source": "fortinet_mcp_bridge"
        }
    
    async def generate_3d_scene_for_drawio(self, topology: Dict[str, Any]) -> Dict[str, Any]:
        """Generate 3D scene data compatible with your existing babylon_test.html"""
        
        devices = topology.get("devices", [])
        
        # Convert to format expected by your 3D visualization
        scene_data = {
            "nodes": [],
            "links": []
        }
        
        for device in devices:
            node = {
                "id": device["id"],
                "name": device["name"],
                "type": device["type"],
                "ip": device["ip"],
                "status": device["status"],
                "model": device.get("model", ""),
                "serial": device.get("serial", ""),
                "position": self.calculate_device_position(device, devices),
                "rotation": {"x": 0, "y": 0, "z": 0},
                "scale": {"x": 1, "y": 1, "z": 1}
            }
            scene_data["nodes"].append(node)
        
        # Add links
        for link in topology.get("links", []):
            scene_link = {
                "source": link["source_id"],
                "target": link["target_id"],
                "type": link.get("link_type", "physical"),
                "bandwidth": link.get("bandwidth", ""),
                "status": link.get("status", "active")
            }
            scene_data["links"].append(scene_link)
        
        return scene_data
    
    def calculate_device_position(self, device: Dict, all_devices: List[Dict]) -> Dict[str, float]:
        """Calculate 3D position for device based on type and existing devices"""
        
        device_type = device.get("type", "unknown")
        
        # Define base positions by device type
        type_positions = {
            "fortigate": {"x": 0, "y": 1, "z": 0},
            "fortiswitch": {"x": -3, "y": 1, "z": 3},
            "fortiap": {"x": 3, "y": 1, "z": 3}
        }
        
        base_pos = type_positions.get(device_type, {"x": 0, "y": 1, "z": 0})
        
        # Offset if multiple devices of same type
        same_type_devices = [d for d in all_devices if d.get("type") == device_type]
        if len(same_type_devices) > 1:
            index = same_type_devices.index(device)
            offset = index * 2
            base_pos["x"] += offset
        
        return base_pos

class DrawIOFortinetIntegration:
    """Enhanced integration combining DrawIO with existing Fortinet MCP"""
    
    def __init__(self):
        self.bridge = FortinetMCPBridge()
        
    async def collect_and_generate(self, layout: str = "hierarchical") -> Dict[str, Any]:
        """Collect from Fortinet MCP and generate DrawIO diagram"""
        
        # Step 1: Discover topology from existing Fortinet MCP
        logger.info("🔍 Discovering Fortinet topology...")
        fortinet_topology = await self.bridge.discover_fortinet_topology()
        
        # Step 2: Convert to DrawIO format
        logger.info("🔄 Converting to DrawIO format...")
        drawio_topology = self.bridge.convert_to_drawio_format(fortinet_topology)
        
        # Step 3: Generate 3D scene data
        logger.info("🎮 Generating 3D scene data...")
        scene_data = await self.bridge.generate_3d_scene_for_drawio(drawio_topology)
        
        # Step 4: Generate DrawIO XML
        logger.info("🎨 Generating DrawIO diagram...")
        drawio_xml = self.generate_drawio_xml(drawio_topology, layout)
        
        return {
            "fortinet_topology": fortinet_topology,
            "drawio_topology": drawio_topology,
            "scene_data": scene_data,
            "drawio_xml": drawio_xml
        }
    
    def generate_drawio_xml(self, topology: Dict[str, Any], layout: str = "hierarchical") -> str:
        """Generate DrawIO XML from topology"""
        
        devices = topology.get("devices", [])
        links = topology.get("links", [])
        
        # Generate DrawIO XML (simplified version)
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="{asyncio.get_event_loop().time()}" agent="5.0">
  <diagram name="Fortinet Network Topology" id="fortinet-topology">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />'''
        
        cell_id = 2
        
        # Add devices
        positions = self.calculate_device_positions(devices, layout)
        
        for device in devices:
            pos = positions[device["id"]]
            style = self.get_device_style(device)
            
            label = f"{device['name']}\\n{device['ip']}\\n{device.get('model', '')}"
            
            xml += f'''
        <mxCell id="{cell_id}" value="{label}" style="{style}" vertex="1" parent="1">
          <mxGeometry x="{pos['x']}" y="{pos['y']}" width="120" height="60" as="geometry" />
        </mxCell>'''
            
            device["cell_id"] = cell_id
            cell_id += 1
        
        # Add links
        for link in links:
            source_device = next((d for d in devices if d["id"] == link["source_id"]), None)
            target_device = next((d for d in devices if d["id"] == link["target_id"]), None)
            
            if source_device and target_device:
                edge_style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
                label = f"{link.get('source_interface', '')}\\n{link.get('bandwidth', '')}"
                
                xml += f'''
        <mxCell id="{cell_id}" value="{label}" style="{edge_style}" edge="1" parent="1" source="{source_device['cell_id']}" target="{target_device['cell_id']}">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>'''
                
                cell_id += 1
        
        xml += '''
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
        
        return xml
    
    def calculate_device_positions(self, devices: List[Dict], layout: str) -> Dict[str, Dict]:
        """Calculate device positions for DrawIO layout"""
        
        positions = {}
        
        if layout == "hierarchical":
            # Arrange by device type in layers
            layers = {"fortigate": 0, "fortiswitch": 1, "fortiap": 2}
            
            for device in devices:
                layer = layers.get(device.get("type"), 3)
                devices_in_layer = [d for d in devices if layers.get(d.get("type"), 3) == layer]
                index = devices_in_layer.index(device)
                
                positions[device["id"]] = {
                    "x": 100 + index * 200,
                    "y": 100 + layer * 150
                }
        
        else:  # Default grid layout
            cols = 3
            for i, device in enumerate(devices):
                row = i // cols
                col = i % cols
                positions[device["id"]] = {
                    "x": 100 + col * 200,
                    "y": 100 + row * 150
                }
        
        return positions
    
    def get_device_style(self, device: Dict) -> str:
        """Get DrawIO style for Fortinet device"""
        
        device_type = device.get("type", "unknown")
        
        styles = {
            "fortigate": "shape=cloud;whiteSpace=wrap;html=1;fillColor=#1ba1e2;strokeColor=#006EAF;fontColor=#ffffff;",
            "fortiswitch": "shape=rectangle;whiteSpace=wrap;html=1;fillColor=#60a917;strokeColor=#2D7600;fontColor=#ffffff;",
            "fortiap": "shape=ellipse;whiteSpace=wrap;html=1;fillColor=#f5a623;strokeColor=#B79500;fontColor=#ffffff;"
        }
        
        return styles.get(device_type, "shape=rectangle;whiteSpace=wrap;html=1;fillColor=#6c757d;strokeColor=#495057;fontColor=#ffffff;")

# Example usage
async def main():
    """Test the integration"""
    integration = DrawIOFortinetIntegration()
    
    result = await integration.collect_and_generate(layout="hierarchical")
    
    print("🎉 Integration test successful!")
    print(f"📊 Found {result['drawio_topology']['total_devices']} devices")
    print(f"🔗 Found {result['drawio_topology']['total_links']} links")
    print(f"🎨 Generated DrawIO XML ({len(result['drawio_xml'])} characters)")
    
    # Save DrawIO diagram
    with open("fortinet_topology.drawio", "w") as f:
        f.write(result["drawio_xml"])
    
    # Save 3D scene data for babylon_test.html
    with open("fortinet_scene.json", "w") as f:
        json.dump(result["scene_data"], f, indent=2)
    
    print("💾 Saved fortinet_topology.drawio and fortinet_scene.json")

if __name__ == "__main__":
    asyncio.run(main())
