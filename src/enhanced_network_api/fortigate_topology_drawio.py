"""FortiGate topology fetch + DrawIO XML generation (real data only, no demo).

This module uses fortiosapi to pull live data from the FortiGate and converts it
into a simple {nodes, links} topology plus DrawIO XML for diagrams.net.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

import fortiosapi
import requests

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


FGT_HOST = "192.168.0.254:10443"
FGT_TOKEN = "199psNw33b8bq581dNmQqNpkGH53bm"
VDOM_NAME = "root"


def fetch_fortigate_topology() -> Dict[str, Any]:
    """Fetch live topology data from FortiGate using fortiosapi.

    Returns a dict with at least:
      {"nodes": [...], "links": [...], "source": "fortiosapi", "timestamp": ...}
    """
    topo: Dict[str, Any] = {
        "nodes": [],
        "links": [],
        "source": "fortiosapi",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
    }

    fgt: fortiosapi.FortiOSAPI | None = None

    try:
        fgt = fortiosapi.FortiOSAPI()

        fgt.tokenlogin(
            host=FGT_HOST,
            apitoken=FGT_TOKEN,
            vdom=VDOM_NAME,
            verify=False,
            timeout=10,
        )

        # System status (hostname, version, serial)
        status = fgt.monitor("system", "status", vdom=VDOM_NAME) or {}
        status_results = status.get("results", {})

        fgt_node_id = f"fgt-{FGT_HOST.split(':')[0].replace('.', '-')}"
        fgt_node = {
            "id": fgt_node_id,
            "name": status_results.get("hostname", "FortiGate"),
            "type": "fortigate",
            "ip": FGT_HOST.split(":")[0],
            "model": status_results.get("version", "unknown"),
            "status": "active",
            "role": "firewall",
        }
        topo["nodes"].append(fgt_node)

        # Interfaces (system/interface)
        interfaces = fgt.get("system", "interface", vdom=VDOM_NAME) or {}
        iface_results = interfaces.get("results", [])

        for iface in iface_results:
            alias = iface.get("alias") or iface.get("name")
            ip = iface.get("ip")
            if not alias or not ip:
                continue

            if_node_id = f"if-{alias.replace(' ', '-')}"
            if_node = {
                "id": if_node_id,
                "name": alias,
                "type": "interface",
                "ip": ip,
                "model": "interface",
                "status": "active" if iface.get("status") == "up" else "inactive",
            }
            topo["nodes"].append(if_node)

            topo["links"].append(
                {
                    "source": fgt_node_id,
                    "target": if_node_id,
                    "type": "internal",
                    "status": if_node["status"],
                }
            )

        # Fetch connected devices/endpoints using new API endpoints
        connected_devices = _fetch_connected_devices(fgt, VDOM_NAME)
        for device in connected_devices:
            topo["nodes"].append(device)
            # Link device to FortiGate or to its parent switch/AP if available
            parent_id = device.get("parent_device_id")
            if parent_id:
                topo["links"].append(
                    {
                        "source": parent_id,
                        "target": device["id"],
                        "type": device.get("connection_type", "ethernet"),
                        "status": device.get("status", "online"),
                        "interfaces": [device.get("port")] if device.get("port") else [],
                    }
                )
            else:
                # Link directly to FortiGate if no parent specified
                topo["links"].append(
                    {
                        "source": fgt_node_id,
                        "target": device["id"],
                        "type": device.get("connection_type", "ethernet"),
                        "status": device.get("status", "online"),
                    }
                )

        return topo

    finally:
        if fgt is not None:
            try:
                fgt.logout()
            except Exception:
                pass


def generate_drawio_xml_from_topology(topology_data: Dict[str, Any], layout: str = "hierarchical") -> str:
    """Generate DrawIO XML from real topology data.

    topology_data must contain "nodes" and "links" with ids and source/target ids.
    """
    nodes: List[Dict[str, Any]] = topology_data.get("nodes", [])
    links: List[Dict[str, Any]] = topology_data.get("links", [])

    # If no nodes, return a minimal diagram with a warning label (still no demo devices)
    if not nodes:
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<mxfile host=\"app.diagrams.net\" modified=\"{}\" agent=\"5.0\" "
            "etag=\"{}\" version=\"21.6.5\" type=\"device\">\n"
            "  <diagram name=\"Network Topology\" id=\"topology\">\n"
            "    <mxGraphModel dx=\"1422\" dy=\"794\" grid=\"1\" gridSize=\"10\" "
            "guides=\"1\" tooltips=\"1\" connect=\"1\" arrows=\"1\" fold=\"1\" "
            "page=\"1\" pageScale=\"1\" pageWidth=\"1169\" pageHeight=\"827\" "
            "math=\"0\" shadow=\"0\">\n"
            "      <root>\n"
            "        <mxCell id=\"0\" />\n"
            "        <mxCell id=\"1\" parent=\"0\" />\n"
            "        <mxCell id=\"2\" value=\"No topology data available\" "
            "style=\"text;html=1;strokeColor=none;fillColor=none;align=center;"
            "verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=20;fontColor=#FF0000;\" "
            "vertex=\"1\" parent=\"1\">\n"
            "          <mxGeometry x=\"400\" y=\"350\" width=\"300\" height=\"60\" as=\"geometry\" />\n"
            "        </mxCell>\n"
            "      </root>\n"
            "    </mxGraphModel>\n"
            "  </diagram>\n"
            "</mxfile>".format(datetime.now(UTC).isoformat(), datetime.now(UTC).timestamp())
        )

    xml_template = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<mxfile host=\"app.diagrams.net\" modified=\"{}\" agent=\"5.0\" "
        "etag=\"{}\" version=\"21.6.5\" type=\"device\">\n"
        "  <diagram name=\"Network Topology\" id=\"topology\">\n"
        "    <mxGraphModel dx=\"1422\" dy=\"794\" grid=\"1\" gridSize=\"10\" "
        "guides=\"1\" tooltips=\"1\" connect=\"1\" arrows=\"1\" fold=\"1\" "
        "page=\"1\" pageScale=\"1\" pageWidth=\"1169\" pageHeight=\"827\" "
        "math=\"0\" shadow=\"0\">\n"
        "      <root>\n"
        "        <mxCell id=\"0\" />\n"
        "        <mxCell id=\"1\" parent=\"0\" />\n"
        "        {}  <!-- Cells will be inserted here -->\n"
        "      </root>\n"
        "    </mxGraphModel>\n"
        "  </diagram>\n"
        "</mxfile>"
    ).format(datetime.now(UTC).isoformat(), datetime.now(UTC).timestamp(), "")

    cells: List[str] = []
    cell_id = 2

    positions = _calculate_positions(nodes, layout)

    # Device cells
    for node in nodes:
        pos = positions.get(node["id"], {"x": 100, "y": 100})
        style = _device_style(node)
        label = node.get("name", "Device")
        label += f"\\n{node.get('ip', 'N/A')}\\n{node.get('model', node.get('type', ''))}"

        cell_xml = (
            f"        <mxCell id=\"{cell_id}\" value=\"{label}\" style=\"{style}\" "
            f"vertex=\"1\" parent=\"1\">\n"
            f"          <mxGeometry x=\"{pos['x']}\" y=\"{pos['y']}\" width=\"120\" height=\"60\" as=\"geometry\" />\n"
            f"        </mxCell>"
        )
        cells.append(cell_xml)
        node["_cell_id"] = cell_id
        cell_id += 1

    # Link cells
    for link in links:
        src_id = link.get("source")
        tgt_id = link.get("target")
        src = next((n for n in nodes if n["id"] == src_id), None)
        tgt = next((n for n in nodes if n["id"] == tgt_id), None)
        if not src or not tgt:
            continue

        src_pos = positions.get(src_id, {"x": 100, "y": 100})
        tgt_pos = positions.get(tgt_id, {"x": 300, "y": 100})
        style = _link_style(link)

        cell_xml = (
            f"        <mxCell id=\"{cell_id}\" style=\"{style}\" edge=\"1\" parent=\"1\" "
            f"source=\"{src['_cell_id']}\" target=\"{tgt['_cell_id']}\">\n"
            f"          <mxGeometry width=\"50\" height=\"50\" relative=\"1\" as=\"geometry\">\n"
            f"            <mxPoint x=\"{src_pos['x'] + 60}\" y=\"{src_pos['y'] + 30}\" as=\"sourcePoint\" />\n"
            f"            <mxPoint x=\"{tgt_pos['x'] + 60}\" y=\"{tgt_pos['y'] + 30}\" as=\"targetPoint\" />\n"
            f"          </mxGeometry>\n"
            f"        </mxCell>"
        )
        cells.append(cell_xml)
        cell_id += 1

    final_xml = xml_template.replace("        {}  <!-- Cells will be inserted here -->", "\n".join(cells))
    return final_xml


def _calculate_positions(nodes: List[Dict[str, Any]], layout: str) -> Dict[str, Dict[str, int]]:
    positions: Dict[str, Dict[str, int]] = {}

    if layout == "hierarchical":
        layers = {"fortigate": 0, "interface": 1, "fortiswitch": 1, "fortiap": 1, "client": 2}
        layer_nodes: Dict[int, List[Dict[str, Any]]] = {}

        for n in nodes:
            layer = layers.get(n.get("type", "interface"), 2)
            layer_nodes.setdefault(layer, []).append(n)

        for layer, items in layer_nodes.items():
            x_start = 100
            y = 100 + layer * 150
            spacing = 220
            for i, n in enumerate(items):
                positions[n["id"]] = {"x": x_start + i * spacing, "y": y}
    else:
        # Simple grid fallback
        for i, n in enumerate(nodes):
            positions[n["id"]] = {
                "x": 100 + (i % 4) * 220,
                "y": 100 + (i // 4) * 150,
            }

    return positions


def _device_style(node: Dict[str, Any]) -> str:
    ntype = node.get("type", "interface")
    status = node.get("status", "active")

    base_styles = {
        "fortigate": "shape=cloud;whiteSpace=wrap;html=1;fillColor=#1ba1e2;strokeColor=#006EAF;fontColor=#ffffff;",
        "interface": "shape=rectangle;whiteSpace=wrap;html=1;fillColor=#60a917;strokeColor=#2D7600;fontColor=#ffffff;",
        "client": "shape=ellipse;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontColor=#000000;",
        "fortiswitch": "shape=hexagon;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontColor=#000000;",
        "fortiap": "shape=rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontColor=#000000;",
    }

    style = base_styles.get(ntype, base_styles["interface"])
    if status != "active":
        style = style.replace("fillColor=#", "fillColor=#dc3545;")
    return style


def _link_style(link: Dict[str, Any]) -> str:
    ltype = link.get("type", "internal")

    styles = {
        "internal": "strokeColor=#6c757d;strokeWidth=2;endArrow=none;startArrow=none;",
        "ethernet": "strokeColor=#0078d4;strokeWidth=2;endArrow=block;startArrow=none;",
        "wifi": "strokeColor=#ff6b00;strokeWidth=2;endArrow=block;startArrow=none;dashed=1;",
        "wireless": "strokeColor=#ff6b00;strokeWidth=2;endArrow=block;startArrow=none;dashed=1;",
    }
    return styles.get(ltype, styles["internal"])


def _fetch_connected_devices(fgt: fortiosapi.FortiOSAPI, vdom: str) -> List[Dict[str, Any]]:
    """Fetch connected devices/endpoints from FortiGate using multiple API endpoints.
    
    Tries endpoints in order:
    1. /api/v2/monitor/user/device/query
    2. /api/v2/monitor/user/device/select
    3. /api/v2/monitor/endpoint-control/registered_ems
    
    Returns a list of normalized device dictionaries.
    """
    devices: List[Dict[str, Any]] = []
    
    # Endpoints to try in order of preference
    endpoints_to_try = [
        "/api/v2/monitor/user/device/query",
        "/api/v2/monitor/user/device/select",
        "/api/v2/monitor/endpoint-control/registered_ems",
    ]
    
    assets_data = None
    endpoint_used = None
    
    # Get the base URL and session from fortiosapi
    # fortiosapi stores the session in fgt._session (private attribute)
    base_url = f"https://{FGT_HOST}"
    session = getattr(fgt, '_session', None)
    if not session:
        logger.warning("No session available from fortiosapi")
        return devices
    
    # Get CSRF token if available
    headers = {}
    if hasattr(fgt, 'csrf_token') and fgt.csrf_token:
        headers['X-CSRFTOKEN'] = fgt.csrf_token
    
    for endpoint in endpoints_to_try:
        try:
            url = f"{base_url}{endpoint}"
            params = {"vdom": vdom} if vdom else {}
            response = session.get(url, headers=headers, params=params, verify=False, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # Check if this endpoint has data
                results = result.get("results") or result.get("data") or []
                if isinstance(results, dict):
                    results = results.get("entries", [])
                if isinstance(results, list) and len(results) > 0:
                    assets_data = results
                    endpoint_used = endpoint
                    logger.info(f"Successfully fetched {len(assets_data)} devices from {endpoint_used}")
                    break
        except Exception as e:
            logger.debug(f"Failed to fetch from {endpoint}: {e}")
            continue
    
    if not assets_data:
        logger.warning("No connected devices found from any endpoint")
        return devices
    
    # Normalize device data
    for asset in assets_data:
        # Extract device identification
        name = asset.get("name") or asset.get("hostname") or asset.get("host") or asset.get("mac") or asset.get("ip")
        if not name:
            continue
        
        # Determine device type
        os_type = (asset.get("os") or asset.get("os-type") or asset.get("software_os") or "").lower()
        device_type = "client"
        if "fortiap" in os_type or "ap" in os_type:
            device_type = "fortiap"
        elif "fortiswitch" in os_type or "switch" in os_type:
            device_type = "fortiswitch"
        elif "fortios" in os_type or "fortigate" in os_type:
            device_type = "fortigate"
        
        # Determine connection type
        connection_type = "ethernet"
        if asset.get("ssid") or asset.get("wireless") or "wifi" in os_type:
            connection_type = "wifi"
        
        # Create device ID
        device_id = f"device-{name.replace(' ', '-').replace(':', '-').replace('.', '-')}"
        
        # Find parent device (switch/AP) if available
        parent_device_id = None
        parent_serial = asset.get("ap_sn") or asset.get("switch_sn") or asset.get("switch") or asset.get("ap")
        if parent_serial:
            # Try to find parent in existing nodes (would need to be passed in, but for now we'll link to FortiGate)
            # This will be handled in the calling function
            pass
        
        device = {
            "id": device_id,
            "name": name,
            "type": device_type,
            "os": asset.get("os") or asset.get("os-type") or asset.get("software_os"),
            "ip": asset.get("ip") or asset.get("address"),
            "mac": asset.get("mac"),
            "status": asset.get("status") or "online",
            "connection_type": connection_type,
            "ssid": asset.get("ssid"),
            "port": asset.get("port") or asset.get("interface"),
            "vulnerabilities": asset.get("vulnerabilities", 0),
            "parent_device_id": parent_device_id,
            "parent_serial": parent_serial,
        }
        
        devices.append(device)
    
    return devices
