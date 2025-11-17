#!/usr/bin/env python3
"""
AI Research Platform Web API (FastAPI)
Provides web-accessible endpoints for platform discovery and interaction
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import json
import os
from datetime import datetime
import requests

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
async def dashboard():
    # Minimal HTML dashboard for standalone access
    html = """
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>🤖 AI Research Platform Dashboard</title>
    </head>
    <body>
        <h1>🤖 AI Research Platform Dashboard</h1>
        <p>API endpoints are available.</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
