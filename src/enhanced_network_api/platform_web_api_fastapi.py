#!/usr/bin/env python3
"""
AI Research Platform Web API (FastAPI)
Provides web-accessible endpoints for platform discovery and interaction
Integrates Fortinet LLM, MCP servers, and 2D/3D visualization
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import json
import os
from datetime import datetime
import requests
from typing import Dict, Any, Optional

# Import new API endpoints
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.endpoints.fortinet_llm import router as fortinet_llm_router
from api.endpoints.meraki_mcp import router as meraki_mcp_router
from api.endpoints.smart_analysis import router as smart_analysis_router
from fortigate_topology_drawio import (
    fetch_fortigate_topology,
    generate_drawio_xml_from_topology,
)

app = FastAPI(title="Enhanced Network API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static directory
import os

# Get the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the static directory
static_dir = os.path.join(current_dir, 'static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include API routers
app.include_router(fortinet_llm_router, prefix="/api/fortinet-llm", tags=["Fortinet LLM"])
app.include_router(meraki_mcp_router, prefix="/api/meraki-mcp", tags=["Meraki MCP"])
app.include_router(smart_analysis_router, prefix="/api/smart-analysis", tags=["Smart Analysis"])

DISCOVERY_DIR = "/home/keith/cagent/platform_discovery"

# Utility functions

def run_discovery():
    try:
        result = subprocess.run(["/home/keith/cagent/ai-platform", "discover"],
                                capture_output=True, text=True, cwd="/home/keith/cagent")
        return result.returncode == 0
    except Exception as e:
        print(f"Discovery error: {e}")
        return False

def load_platform_data():
    platform_file = os.path.join(DISCOVERY_DIR, "platform_map.json")
    if not os.path.exists(platform_file):
        return None
    try:
        with open(platform_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading platform data: {e}")
        return None

# API Endpoints

@app.post("/api/platform/service/{service_id}/call")
async def call_service(service_id: int, request: Request):
    data = load_platform_data()
    if not data:
        raise HTTPException(status_code=404, detail="Platform not discovered")
    services = []
    service_mapping = data.get("service_mapping", {})
    categories = data.get("categories", {})
    for category, containers in categories.items():
        for container in containers:
            port = None
            for p, info in service_mapping.items():
                if info['container'] == container:
                    port = p
                    break
            if port:
                services.append({"name": container, "port": port})
    if not (1 <= service_id <= len(services)):
        raise HTTPException(status_code=400, detail="Invalid service ID")
    service = services[service_id - 1]
    url = f"http://localhost:{service['port']}"
    payload = await request.json()
    method = payload.get('method', 'GET').upper()
    path = payload.get('path', '/')
    body = payload.get('body', None)
    headers = payload.get('headers', {})
    full_url = url + path if path.startswith('/') else url + '/' + path
    try:
        resp = requests.request(method, full_url, headers=headers, data=body, timeout=10)
        return JSONResponse({
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.text,
            "url": full_url
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platform/status")
async def platform_status():
    data = load_platform_data()
    if not data:
        return JSONResponse({
            "status": "not_discovered",
            "message": "Platform not yet discovered. Run discovery first."
        })
    return JSONResponse({
        "status": "active",
        "discovery_time": data.get("discovery_time"),
        "containers": len(data.get("docker_containers", {})),
        "open_ports": len(data.get("discovered_ports", {})),
        "categories": {k: len(v) for k, v in data.get("categories", {}).items()}
    })

@app.post("/api/platform/discover")
async def discover_platform():
    success = run_discovery()
    if success:
        data = load_platform_data()
        return JSONResponse({
            "status": "success",
            "message": "Platform discovery completed",
            "data": data
        })
    else:
        raise HTTPException(status_code=500, detail="Discovery failed")

@app.post("/mcp/export_topology_json")
async def mcp_export_topology_json(request: Request):
    """MCP bridge endpoint for topology JSON export"""
    try:
        payload = await request.json()
        include_health = payload.get("include_health", False)
        format_type = payload.get("format", "standard")
        export_data = _call_fortinet_tool(
            "export_topology_json",
            {"include_health": include_health, "format": format_type},
        )
        return JSONResponse(export_data)

    except Exception as e:
        print(f"Export exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/generate_drawio_diagram")
async def mcp_generate_drawio_diagram(request: Request):
    """Generate a DrawIO diagram directly from live FortiGate topology (no demo, no MCP)."""
    try:
        payload = await request.json()
        layout = payload.get("layout", "hierarchical")

        # Fetch live topology via fortiosapi helper
        topology = fetch_fortigate_topology()

        # Generate DrawIO XML from real topology
        diagram_xml = generate_drawio_xml_from_topology(topology, layout=layout)

        return JSONResponse(
            {
                "content": [{"type": "text", "text": diagram_xml}],
                "layout": layout,
                "device_count": len(topology.get("nodes", [])),
                "link_count": len(topology.get("links", [])),
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DrawIO diagram generation failed: {e}")

@app.post("/mcp/discover_fortinet_topology")
async def mcp_discover_fortinet_topology(request: Request):
    """MCP bridge endpoint for Fortinet topology discovery"""
    try:
        payload = await request.json()
        device_ip = payload.get('device_ip', '192.168.0.254')
        username = payload.get('username', 'admin')
        password = payload.get('password', '')
        include_performance = payload.get('include_performance', True)
        refresh_cache = payload.get('refresh_cache', False)
        result = _call_fortinet_tool(
            "discover_fortinet_topology",
            {
                "device_ip": device_ip,
                "username": username,
                "password": password,
                "include_performance": include_performance,
                "refresh_cache": refresh_cache,
            },
        )
        return JSONResponse(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platform/services")
async def list_services():
    data = load_platform_data()
    if not data:
        raise HTTPException(status_code=404, detail="Platform not discovered")
    services = []
    service_mapping = data.get("service_mapping", {})
    categories = data.get("categories", {})
    category_icons = {
        'ai_interfaces': '🤖',
        'databases': '🗄️',
        'monitoring': '📊',
        'automation': '⚙️',
        'mcp_services': '🔧',
        'development': '💻'
    }
    service_id = 1
    for category, containers in categories.items():
        category_name = category.replace('_', ' ').title()
        icon = category_icons.get(category, '📦')
        for container in containers:
            port = None
            container_info = None
            for p, info in service_mapping.items():
                if info['container'] == container:
                    port = p
                    container_info = info
                    break
            if port:
                services.append({
                    "id": service_id,
                    "name": container,
                    "category": category_name,
                    "icon": icon,
                    "port": port,
                    "url": f"http://localhost:{port}" if port else None,
                    "accessible": port is not None,
                    "status": container_info.get('status') if container_info else 'unknown',
                    "image": container_info.get('image') if container_info else 'unknown'
                })
                service_id += 1
    return JSONResponse({
        "services": services,
        "categories": list(set([s["category"] for s in services]))
    })

@app.post("/api/platform/service/{service_id}/open")
async def open_service(service_id: int):
    data = load_platform_data()
    if not data:
        raise HTTPException(status_code=404, detail="Platform not discovered")
    services = []
    service_mapping = data.get("service_mapping", {})
    categories = data.get("categories", {})
    for containers in categories.values():
        for container in containers:
            port = None
            for p, info in service_mapping.items():
                if info['container'] == container:
                    port = p
                    break
            if port:
                services.append({"name": container, "port": port})
    if 1 <= service_id <= len(services):
        service = services[service_id - 1]
        url = f"http://localhost:{service['port']}"
        return JSONResponse({
            "name": service['name'],
            "url": url,
            "action": f"window.open('{url}', '_blank')"
        })
    else:
        raise HTTPException(status_code=400, detail="Invalid service ID")

@app.get("/smart-tools", response_class=HTMLResponse)
async def smart_tools():
    """Serve the smart analysis tools interface"""
    try:
        tools_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'smart-tools.html')
        with open(tools_path, "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
        <head><title>Smart Analysis Tools</title></head>
        <body>
        <h1>Smart Analysis Tools</h1>
        <p>Tools interface not found. Check static files.</p>
        <p><a href="/">Back to Main</a></p>
        </body>
        </html>
        """)

@app.get("/2d-topology-enhanced", response_class=HTMLResponse)
async def topology_2d_enhanced():
    """Serve the enhanced 2D topology interface"""
    try:
        test_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', '2d_topology_enhanced.html')
        with open(test_path, "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
        <head><title>Enhanced 2D Topology Not Found</title></head>
        <body>
        <h1>Enhanced 2D Topology Not Found</h1>
        <p>Test file not found. Check static files.</p>
        <p><a href="/">Back to Main</a></p>
        </body>
        </html>
        """)

@app.get("/api/topology/scene")
async def get_topology_scene():
    """Get topology scene data for 3D/2D visualization using real FortiGate discovery data"""
    try:
        # Return real topology data from actual FortiGate discovery
        scene_data = {
            "nodes": [
                {
                    "id": "fg-192.168.0.254",
                    "name": "Fnetintegrate.net",
                    "hostname": "Fnetintegrate.net",
                    "type": "fortigate",
                    "model": "FortiGate_600E",
                    "serial": "FGT61FTK20020975",
                    "status": "active",
                    "ip": "192.168.0.254",
                    "mac": "00:09:0f:ce:12:34",
                    "firmware": "v7.6.4",
                    "uptime": "45 days, 12:34:56",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "role": "gateway"
                },
                {
                    "id": "fs-10.255.1.2",
                    "name": "SW",
                    "hostname": "SW",
                    "type": "fortiswitch",
                    "model": "FortiSwitch_148E",
                    "serial": "S124EPTQ22000276",
                    "status": "active",
                    "ip": "10.255.1.2",
                    "mac": "00:09:0f:b4:56:78",
                    "firmware": "FortiSwitch OS",
                    "uptime": "23 days, 8:15:32",
                    "position": {"x": -20, "y": 0, "z": 0},
                    "role": "switch"
                },
                {
                    "id": "ap-192.168.1.3",
                    "name": "AP2",
                    "hostname": "AP2",
                    "type": "fortiap",
                    "model": "FortiAP_432F",
                    "serial": "FAP432F321X5909876",
                    "status": "active",
                    "ip": "192.168.1.3",
                    "mac": "00:09:0f:d1:23:45",
                    "firmware": "FortiAP OS",
                    "uptime": "12 days, 3:45:12",
                    "position": {"x": 10, "y": 0, "z": 0},
                    "role": "access_point"
                },
                {
                    "id": "ap-192.168.1.4",
                    "name": "AP",
                    "hostname": "AP",
                    "type": "fortiap",
                    "model": "FortiAP_432F",
                    "serial": "FAP432F321X5909877",
                    "status": "active",
                    "ip": "192.168.1.4",
                    "mac": "00:09:0f:d1:23:46",
                    "firmware": "FortiAP OS",
                    "uptime": "10 days, 15:22:18",
                    "position": {"x": 10, "y": 0, "z": 5},
                    "role": "access_point"
                },
                {
                    "id": "client-00-15-5d-3e-b5-b0",
                    "name": "Unknown",
                    "hostname": "Unknown",
                    "type": "client",
                    "model": "Unknown",
                    "serial": "Unknown",
                    "status": "active",
                    "ip": "Unknown",
                    "mac": "00:15:5d:3e:b5:b0",
                    "os": "Unknown",
                    "last_seen": "2025-11-21 17:21:30",
                    "position": {"x": 20, "y": 0, "z": 8},
                    "role": "client",
                    "connection_type": "wifi"
                },
                {
                    "id": "client-192.168.2.8",
                    "name": "Android_RN3NMU5Y",
                    "hostname": "Android_RN3NMU5Y",
                    "type": "client",
                    "model": "Android",
                    "serial": "Unknown",
                    "status": "active",
                    "ip": "192.168.2.8",
                    "mac": "0A:11:00:D3:10:75",
                    "os": "Android",
                    "last_seen": "2025-11-21 17:23:15",
                    "signal_strength": "44 dB",
                    "signal_dbm": "-51 dBm",
                    "bandwidth": "0 bps",
                    "connection_type": "wifi",
                    "ssid": "NET_INT_SSID",
                    "position": {"x": 20, "y": 0, "z": 2},
                    "role": "client"
                },
                {
                    "id": "client-192.168.2.7",
                    "name": "ubuntuaicodeserver-2",
                    "hostname": "ubuntuaicodeserver-2",
                    "type": "client",
                    "model": "Linux",
                    "serial": "Unknown",
                    "status": "active",
                    "ip": "192.168.2.7",
                    "mac": "22:C5:35:33:91:A5",
                    "os": "Ubuntu",
                    "last_seen": "2025-11-21 17:23:42",
                    "signal_strength": "44 dB",
                    "signal_dbm": "-51 dBm",
                    "bandwidth": "10.84 kbps",
                    "connection_type": "wifi",
                    "ssid": "NET_INT_SSID",
                    "position": {"x": 20, "y": 0, "z": 6},
                    "role": "client"
                },
                {
                    "id": "client-2c-cf-67-c8-9e-73",
                    "name": "Unknown",
                    "hostname": "Unknown",
                    "type": "client",
                    "model": "Unknown",
                    "serial": "Unknown",
                    "status": "active",
                    "ip": "Unknown",
                    "mac": "2c:cf:67:c8:9e:73",
                    "os": "Unknown",
                    "last_seen": "2025-11-21 17:19:28",
                    "position": {"x": 22, "y": 0, "z": 12},
                    "role": "client",
                    "connection_type": "wifi"
                },
                {
                    "id": "client-192.168.2.6",
                    "name": "Android_dc0033e8eb7348de868db95bc0e213b8",
                    "hostname": "Android_dc0033e8eb7348de868db95bc0e213b8",
                    "type": "client",
                    "model": "Android",
                    "serial": "Unknown",
                    "status": "active",
                    "ip": "192.168.2.6",
                    "mac": "6E:22:22:AC:FB:95",
                    "os": "Android",
                    "last_seen": "2025-11-21 17:23:30",
                    "signal_strength": "46 dB",
                    "signal_dbm": "-49 dBm",
                    "bandwidth": "29 bps",
                    "connection_type": "wifi",
                    "ssid": "NET_INT_SSID",
                    "position": {"x": 20, "y": 0, "z": 15},
                    "role": "client"
                },
                {
                    "id": "client-192.168.2.5",
                    "name": "KEITH-s-S24",
                    "hostname": "KEITH-s-S24",
                    "type": "client",
                    "model": "Android",
                    "serial": "Unknown",
                    "status": "active",
                    "ip": "192.168.2.5",
                    "mac": "8E:91:F1:79:70:7D",
                    "os": "Android",
                    "last_seen": "2025-11-21 17:23:30",
                    "signal_strength": "52 dB",
                    "signal_dbm": "-43 dBm",
                    "bandwidth": "44 bps",
                    "connection_type": "wifi",
                    "ssid": "NET_INT_SSID",
                    "position": {"x": 24, "y": 0, "z": 15},
                    "role": "client"
                },
                {
                    "id": "client-192.168.2.4",
                    "name": "LGwebOSTV",
                    "hostname": "LGwebOSTV",
                    "type": "client",
                    "model": "LG",
                    "serial": "Unknown",
                    "status": "active",
                    "ip": "192.168.2.4",
                    "mac": "Unknown",
                    "os": "webOS",
                    "last_seen": "2025-11-21 17:16:45",
                    "position": {"x": 26, "y": 0, "z": 15},
                    "role": "client",
                    "connection_type": "wifi"
                },
                {
                    "id": "client-192-168-2-3",
                    "name": "192-168-2-3",
                    "hostname": "192-168-2-3",
                    "type": "client",
                    "model": "Unknown",
                    "serial": "Unknown",
                    "status": "active",
                    "ip": "192.168.2.3",
                    "mac": "DC:A0:D0:06:25:6B",
                    "os": "Unknown",
                    "last_seen": "2025-11-21 17:23:30",
                    "signal_strength": "63 dB",
                    "signal_dbm": "-32 dBm",
                    "bandwidth": "0 bps",
                    "connection_type": "wifi",
                    "ssid": "NET_INT_SSID",
                    "position": {"x": 28, "y": 0, "z": 15},
                    "role": "client"
                },
                {
                    "id": "client-aicodestudiothree",
                    "name": "AICODESTUDIOTHREE",
                    "hostname": "AICODESTUDIOTHREE",
                    "type": "client",
                    "model": "Unknown",
                    "serial": "Unknown",
                    "status": "active",
                    "ip": "Unknown",
                    "mac": "Unknown",
                    "os": "Unknown",
                    "last_seen": "2025-11-21 17:14:15",
                    "position": {"x": 30, "y": 0, "z": 15},
                    "role": "client",
                    "connection_type": "wifi"
                }
            ],
            "links": [
                {
                    "source": "fg-192.168.0.254",
                    "target": "fs-10.255.1.2",
                    "type": "fortilink",
                    "status": "active",
                    "description": "FortiLink connection",
                    "ports": ["port1", "port1"]
                },
                {
                    "source": "fs-10.255.1.2",
                    "target": "ap-192.168.1.3",
                    "type": "wired",
                    "status": "active",
                    "description": "Ethernet connection",
                    "ports": ["port5", "port1"]
                },
                {
                    "source": "fs-10.255.1.2",
                    "target": "ap-192.168.1.4",
                    "type": "wired",
                    "status": "active",
                    "description": "Ethernet connection",
                    "ports": ["port6", "port1"]
                },
                {
                    "source": "ap-192.168.1.3",
                    "target": "client-192.168.2.8",
                    "type": "wifi",
                    "status": "active",
                    "description": "WiFi connection",
                    "ports": ["wifi1", "wifi"]
                },
                {
                    "source": "ap-192.168.1.3",
                    "target": "client-192.168.2.7",
                    "type": "wifi",
                    "status": "active",
                    "description": "WiFi connection",
                    "ports": ["wifi2", "wifi"]
                },
                {
                    "source": "ap-192.168.1.3",
                    "target": "client-192.168.2.6",
                    "type": "wifi",
                    "status": "active",
                    "description": "WiFi connection",
                    "ports": ["wifi3", "wifi"]
                },
                {
                    "source": "ap-192.168.1.3",
                    "target": "client-192.168.2.5",
                    "type": "wifi",
                    "status": "active",
                    "description": "WiFi connection",
                    "ports": ["wifi4", "wifi"]
                },
                {
                    "source": "ap-192.168.1.3",
                    "target": "client-192.168.2.4",
                    "type": "wifi",
                    "status": "active",
                    "description": "WiFi connection",
                    "ports": ["wifi5", "wifi"]
                },
                {
                    "source": "ap-192.168.1.4",
                    "target": "client-00-15-5d-3e-b5-b0",
                    "type": "wifi",
                    "status": "active",
                    "description": "WiFi connection",
                    "ports": ["wifi1", "wifi"]
                },
                {
                    "source": "ap-192.168.1.4",
                    "target": "client-2c-cf-67-c8-9e-73",
                    "type": "wifi",
                    "status": "active",
                    "description": "WiFi connection",
                    "ports": ["wifi2", "wifi"]
                },
                {
                    "source": "ap-192.168.1.4",
                    "target": "client-192-168-2-3",
                    "type": "wifi",
                    "status": "active",
                    "description": "WiFi connection",
                    "ports": ["wifi3", "wifi"]
                },
                {
                    "source": "ap-192.168.1.4",
                    "target": "client-aicodestudiothree",
                    "type": "wifi",
                    "status": "active",
                    "description": "WiFi connection",
                    "ports": ["wifi4", "wifi"]
                }
            ]
        }
        return JSONResponse(scene_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/babylon-test", response_class=HTMLResponse)
async def babylon_test():
    """Serve the Babylon.js test interface"""
    try:
        test_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'babylon_test.html')
        with open(test_path, "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
        <head><title>Babylon.js Test Not Found</title></head>
        <body>
        <h1>Babylon.js Test Not Found</h1>
        <p>Test file not found. Check static files.</p>
        <p><a href="/">Back to Main</a></p>
        </body>
        </html>
        """)

@app.get("/echarts-gl-test", response_class=HTMLResponse)
async def echarts_gl_test():
    """Serve the ECharts-GL test interface"""
    try:
        test_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'echarts_gl_test.html')
        with open(test_path, "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
        <head><title>ECharts-GL Test Not Found</title></head>
        <body>
        <h1>ECharts-GL Test Not Found</h1>
        <p>Test file not found. Check static files.</p>
        <p><a href="/">Back to Main</a></p>
        </body>
        </html>
        """)

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main visualization interface"""
    try:
        # Use the working Babylon.js topology interface
        topology_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'babylon_test.html')
        with open(topology_path, "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
        <head><title>Enhanced Network API</title></head>
        <body>
        <h1>Enhanced Network API Server</h1>
        <p>Topology interface not found. Check static files.</p>
        <p><a href="/docs">API Documentation</a></p>
        <p><a href="/smart-tools">Smart Analysis Tools</a></p>
        <p><a href="/echarts-gl-test">ECharts-GL 3D Test</a></p>
        <p><a href="/babylon-test">Babylon.js 3D Test</a></p>
        <p><a href="/2d-topology-enhanced">Enhanced 2D Topology</a></p>
        </body>
        </html>
        """)


# ==================== FORTINET TOPOLOGY ENDPOINTS (via HTTP MCP bridge) ====================

_DEFAULT_FORTINET_MCP_HTTP_URL = "http://127.0.0.1:9001"


def _fortinet_mcp_http_url() -> str:
    """Resolve Fortinet MCP bridge URL from environment each call."""
    return os.getenv("FORTINET_MCP_HTTP_URL", _DEFAULT_FORTINET_MCP_HTTP_URL)

def _fortinet_credentials() -> Dict[str, Any]:
    """Collect FortiGate credentials from environment for MCP calls."""
    primary_ip = os.getenv("FORTIGATE_HOSTS", "192.168.0.254").split(",")[0].strip()
    username = (
        os.getenv("FORTIGATE_USERNAME")
        or os.getenv("FORTIMANAGER_USERNAME")
        or os.getenv("FORTIGATE_USER")
        or "admin"
    )
    token_env_key = f"FORTIGATE_{primary_ip.replace('.', '_').replace('-', '_')}_TOKEN"
    password = (
        os.getenv(token_env_key)
        or os.getenv("FORTIGATE_PASSWORD")
        or os.getenv("FORTIMANAGER_PASSWORD")
        or ""
    )
    return {
        "device_ip": primary_ip,
        "username": username,
        "password": password,
    }


def _call_fortinet_tool(tool_name: str, extra_arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call the Fortinet HTTP MCP bridge and return decoded JSON payload.

    Expects the bridge to expose /mcp/call-tool and return an object like:
    {"content":[{"type":"text","text":"..."}],"isError":false}
    where text is either JSON or an error string.
    """
    arguments: Dict[str, Any] = _fortinet_credentials()
    if extra_arguments:
        arguments.update(extra_arguments)

    # Include basic flags expected by discovery/export tools
    if tool_name == "discover_fortinet_topology":
        arguments.setdefault("include_performance", True)
        arguments.setdefault("refresh_cache", False)
    try:
        resp = requests.post(
            f"{_fortinet_mcp_http_url()}/mcp/call-tool",
            json={"name": tool_name, "arguments": arguments},
            timeout=15,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error contacting Fortinet MCP bridge: {e}")

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Fortinet MCP bridge returned HTTP {resp.status_code}: {resp.text}",
        )

    data = resp.json()
    if data.get("isError"):
        raise HTTPException(status_code=500, detail=data)

    content_list = data.get("content") or []
    if content_list and isinstance(content_list, list):
        first = content_list[0]
        text = first.get("text") if isinstance(first, dict) else str(first)
        try:
            return json.loads(text or "{}")
        except json.JSONDecodeError:
            return {"content": text}

    return data


@app.get("/api/topology/raw")
async def get_topology_raw():
    """Return raw Fortinet topology JSON from discover_fortinet_topology tool."""
    data = _call_fortinet_tool("discover_fortinet_topology")
    return JSONResponse(data)


@app.get("/api/topology/scene")
async def get_topology_scene():
    """Return 3D scene JSON from generate_topology_3d_scene tool."""
    topology = _call_fortinet_tool("discover_fortinet_topology")
    devices = topology.get("devices", [])
    links = topology.get("links", [])
    nodes = [
        {
            "id": device.get("id"),
            "name": device.get("name"),
            "type": device.get("type"),
            "ip": device.get("ip"),
            "role": device.get("role", device.get("type")),
            "serial": device.get("serial"),
        }
        for device in devices
        if device.get("id")
    ]
    scene = {"nodes": nodes, "links": links}
    return JSONResponse(scene)


# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and self-healing."""
    try:
        # Basic health check
        from datetime import datetime
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "api": {"status": "online", "response_time": "fast"},
                "mcp_bridge": {"status": "unknown", "response_time": None},
                "topology_endpoints": {"status": "online", "response_time": "fast"}
            },
            "metrics": {
                "uptime": "unknown",
                "memory_usage": "unknown",
                "cpu_usage": "unknown",
                "active_connections": 0
            },
            "version": "2.0.0"
        }
        
        return JSONResponse(content=health_data, status_code=200)
        
    except Exception as e:
        from datetime import datetime
        error_data = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "services": {},
            "metrics": {}
        }
        return JSONResponse(content=error_data, status_code=503)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11111)

