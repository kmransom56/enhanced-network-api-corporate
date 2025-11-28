"""FortiGate topology fetch + DrawIO XML generation (real data only, no demo).

This module uses fortiosapi to pull live data from the FortiGate and converts it
into a simple {nodes, links} topology plus DrawIO XML for diagrams.net.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

import fortiosapi
import requests

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]


FGT_HOST = "192.168.0.254:10443"
FGT_TOKEN = "679Nf51c76p7z1Qq6sqhhz8nghmnpN"
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
        "timestamp": datetime.utcnow().isoformat() + "Z",
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

        fgt_node_id = f"fgt-{FGT_HOST.split(":")[0].replace('.', '-') }"
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
            "</mxfile>".format(datetime.utcnow().isoformat(), datetime.utcnow().timestamp())
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
    ).format(datetime.utcnow().isoformat(), datetime.utcnow().timestamp(), "")

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
        layers = {"fortigate": 0, "interface": 1}
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
    }

    style = base_styles.get(ntype, base_styles["interface"])
    if status != "active":
        style = style.replace("fillColor=#", "fillColor=#dc3545;")
    return style


def _link_style(link: Dict[str, Any]) -> str:
    ltype = link.get("type", "internal")

    styles = {
        "internal": "strokeColor=#6c757d;strokeWidth=2;endArrow=none;startArrow=none;",
    }
    return styles.get(ltype, styles["internal"])
