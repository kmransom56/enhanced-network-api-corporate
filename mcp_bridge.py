#!/usr/bin/env python3
"""
FastAPI Bridge for MCP Topology Server
Provides HTTP endpoints to access MCP server functionality
"""

import asyncio
import json
import subprocess
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

from mcp_servers.drawio_fortinet_meraki.mcp_server import DrawIOMCPServer, CallToolResult

# Load root .env to make FortiGate credentials available in subprocess environments
load_dotenv(Path("/home/keith/enhanced-network-api-corporate/.env"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Fortinet MCP Bridge",
    description="HTTP bridge for Fortinet Topology MCP Server",
    version="1.0.0"
)

class TopologyRequest(BaseModel):
    """Topology discovery request"""
    device_ip: str = "192.168.0.254"
    username: str = "admin"
    password: str = ""
    include_performance: bool = True
    refresh_cache: bool = False

class DeviceDetailsRequest(BaseModel):
    """Device details request"""
    device_serial: Optional[str] = None
    device_ip: Optional[str] = None

class HealthMonitoringRequest(BaseModel):
    """Health monitoring request"""
    device_serials: list = []
    duration_minutes: int = 5

class ReportRequest(BaseModel):
    """Report generation request"""
    format: str = "json"
    include_metrics: bool = True

class ToolCallRequest(BaseModel):
    """Generic MCP call request"""
    name: str
    arguments: Dict[str, Any] = {}

# MCP server process
mcp_process: Optional[subprocess.Popen] = None
drawio_server = DrawIOMCPServer()
DRAWIO_TOOL_MAP: Dict[str, Callable[[Dict[str, Any]], Awaitable[CallToolResult]]] = {
    "discover_fortinet_topology": drawio_server.collect_topology,
    "collect_topology": drawio_server.collect_topology,
    "generate_topology_3d_scene": drawio_server.generate_drawio_diagram,
    "generate_drawio_diagram": drawio_server.generate_drawio_diagram,
    "get_topology_summary": drawio_server.get_topology_summary,
    "export_topology_json": drawio_server.export_topology_json,
    "query_api_documentation": drawio_server.query_api_documentation,
    "generate_api_request": drawio_server.generate_api_request,
}

EXTERNAL_MCP_SCRIPTS: Dict[str, str] = {
    # Fortinet topology server
    "discover_fortinet_topology": "mcp_topology_server.py",
    "get_device_details": "mcp_topology_server.py",
    "monitor_device_health": "mcp_topology_server.py",
    "generate_topology_report": "mcp_topology_server.py",
    # Perplexity knowledge server
    "search_knowledge": "mcp_perplexity_server.py",
    "synthesize_answer": "mcp_perplexity_server.py",
    "generate_insights": "mcp_perplexity_server.py",
    "extract_entities": "mcp_perplexity_server.py",
    # Sequential thinking server
    "sequential_thinking": "mcp_sequential_thinking_server.py",
    "generate_hypothesis": "mcp_sequential_thinking_server.py",
    "verify_solution": "mcp_sequential_thinking_server.py",
}

@app.on_event("startup")
async def initialize_drawio_server():
    try:
        await drawio_server.initialize_topology_collector()
    except Exception as exc:
        logger.warning(f"DrawIO MCP server initialization failed: {exc}")

def _calltool_result_to_dict(result: CallToolResult) -> Dict[str, Any]:
    if result.isError:
        # Extract human-readable error text from the MCP result so callers see the real cause
        message: Optional[str] = None
        if result.content:
            content = result.content[0]
            if getattr(content, "type", None) == "text":
                message = content.text
        if not message:
            message = "MCP tool reported an error"
        raise HTTPException(status_code=500, detail=message)
    if result.content:
        content = result.content[0]
        if getattr(content, "type", None) == "text":
            try:
                return json.loads(content.text or "{}")
            except json.JSONDecodeError:
                return {"content": content.text}
    return {}

async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Call MCP server tool"""
    
    if tool_name in DRAWIO_TOOL_MAP:
        handler = DRAWIO_TOOL_MAP[tool_name]
        call_result = await handler(arguments or {})
        return _calltool_result_to_dict(call_result)
    
    try:
        # Prepare MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Call MCP server via subprocess
        script = EXTERNAL_MCP_SCRIPTS.get(tool_name, "mcp_topology_server.py")
        cmd = ["python3", script]
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/home/keith/enhanced-network-api-corporate"
        )
        
        # Send request
        request_json = json.dumps(mcp_request) + "\n"
        stdout, stderr = process.communicate(input=request_json, timeout=30)
        
        if process.returncode != 0:
            logger.error(f"MCP server error: {stderr}")
            raise HTTPException(status_code=500, detail=f"MCP server error: {stderr}")
        
        # Parse response
        response = json.loads(stdout)
        
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
        
        if "result" in response and response["result"]:
            content = response["result"][0]
            if content.get("type") == "text":
                return json.loads(content.get("text", "{}"))
        
        return response
        
    except subprocess.TimeoutExpired:
        logger.error("MCP server timeout")
        raise HTTPException(status_code=500, detail="MCP server timeout")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid MCP response: {e}")
        raise HTTPException(status_code=500, detail="Invalid MCP response")
    except Exception as e:
        logger.error(f"MCP call failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Fortinet MCP Bridge",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "discover": "/mcp/discover_fortinet_topology",
            "device_details": "/mcp/get_device_details", 
            "monitor": "/mcp/monitor_device_health",
            "report": "/mcp/generate_topology_report"
        }
    }

@app.post("/mcp/discover_fortinet_topology")
async def discover_topology(request: TopologyRequest):
    """Discover Fortinet topology via MCP server"""
    
    try:
        logger.info(f"Discovering topology for {request.device_ip}")
        
        arguments = {
            "device_ip": request.device_ip,
            "username": request.username,
            "password": request.password,
            "include_performance": request.include_performance,
            "refresh_cache": request.refresh_cache
        }
        
        result = await call_mcp_tool("discover_fortinet_topology", arguments)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Topology discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/get_device_details")
async def get_device_details(request: DeviceDetailsRequest):
    """Get device details via MCP server"""
    
    try:
        arguments = {
            "device_serial": request.device_serial,
            "device_ip": request.device_ip
        }
        
        result = await call_mcp_tool("get_device_details", arguments)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Device details failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/monitor_device_health")
async def monitor_health(request: HealthMonitoringRequest, background_tasks: BackgroundTasks):
    """Monitor device health via MCP server"""
    
    try:
        arguments = {
            "device_serials": request.device_serials,
            "duration_minutes": request.duration_minutes
        }
        
        result = await call_mcp_tool("monitor_device_health", arguments)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health monitoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/generate_topology_report")
async def generate_report(request: ReportRequest):
    """Generate topology report via MCP server"""
    
    try:
        arguments = {
            "format": request.format,
            "include_metrics": request.include_metrics
        }
        
        result = await call_mcp_tool("generate_topology_report", arguments)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/call-tool")
async def call_tool_endpoint(request: ToolCallRequest):
    """Generic MCP call endpoint with standard MCP result envelope"""
    try:
        result = await call_mcp_tool(request.name, request.arguments or {})
        return JSONResponse(content={
            "content": [{
                "type": "text",
                "text": json.dumps(result)
            }],
            "isError": False
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"call-tool failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mcp_bridge": "running"
    }

if __name__ == "__main__":
    uvicorn.run(
        "mcp_bridge:app",
        host="127.0.0.1",
        port=11112,
        reload=True,
        log_level="info"
    )
