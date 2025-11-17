#!/usr/bin/env python3
"""
AI Research Platform MCP Server
Exposes discovered services as MCP tools for cagent integration
"""

import json
import asyncio
import httpx
from typing import Any, Dict, List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn


class MCPTool(BaseModel):
    """MCP Tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class MCPToolCall(BaseModel):
    """MCP Tool call request"""
    name: str
    arguments: Dict[str, Any]


class MCPResponse(BaseModel):
    """MCP Tool response"""
    content: List[Dict[str, Any]]
    isError: bool = False


class AIResearchPlatformMCP:
    """MCP Server for AI Research Platform"""
    
    def __init__(self, registry_path: str = "platform_discovery/platform_map.json"):
        self.registry_path = Path(registry_path)
        self.services = {}
        self.tools = []
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Load services
        self.load_services()
        self.register_tools()
    
    def load_services(self):
        """Load discovered services"""
        if not self.registry_path.exists():
            print(f"⚠️  Service registry not found: {self.registry_path}")
            return
        
        with open(self.registry_path) as f:
            platform_map = json.load(f)
        
        self.services = platform_map.get('service_mapping', {})
        print(f"✅ Loaded {len(self.services)} services")
    
    def register_tools(self):
        """Register MCP tools for each service"""
        # Health check tool
        self.tools.append(MCPTool(
            name="platform_health_check",
            description="Check health status of all AI platform services",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ))
        
        # Service query tool
        self.tools.append(MCPTool(
            name="query_service",
            description="Query a specific AI platform service by port",
            inputSchema={
                "type": "object",
                "properties": {
                    "port": {
                        "type": "string",
                        "description": "Service port number"
                    },
                    "endpoint": {
                        "type": "string",
                        "description": "API endpoint path (e.g., /api/v1/query)"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE"],
                        "description": "HTTP method",
                        "default": "GET"
                    },
                    "data": {
                        "type": "object",
                        "description": "Request body for POST/PUT",
                        "default": {}
                    }
                },
                "required": ["port", "endpoint"]
            }
        ))
        
        # List services tool
        self.tools.append(MCPTool(
            name="list_services",
            description="List all available AI platform services",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by category (optional)",
                        "enum": ["ai_interfaces", "databases", "monitoring", "automation", "mcp_services", "development"]
                    }
                },
                "required": []
            }
        ))
        
        # Batch query tool
        self.tools.append(MCPTool(
            name="batch_query_services",
            description="Query multiple services in parallel",
            inputSchema={
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "description": "Array of service queries",
                        "items": {
                            "type": "object",
                            "properties": {
                                "port": {"type": "string"},
                                "endpoint": {"type": "string"},
                                "method": {"type": "string", "default": "GET"}
                            }
                        }
                    }
                },
                "required": ["queries"]
            }
        ))
        
        # Service info tool
        self.tools.append(MCPTool(
            name="get_service_info",
            description="Get detailed information about a specific service",
            inputSchema={
                "type": "object",
                "properties": {
                    "port": {
                        "type": "string",
                        "description": "Service port number"
                    }
                },
                "required": ["port"]
            }
        ))
        
        print(f"✅ Registered {len(self.tools)} MCP tools")
    
    async def platform_health_check(self, args: Dict) -> MCPResponse:
        """Check health of all services"""
        results = {}
        
        for port, service_info in self.services.items():
            container = service_info.get('container')
            try:
                response = await self.http_client.get(
                    f"http://localhost:{port}/health",
                    timeout=5.0
                )
                results[container] = {
                    "port": port,
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response": response.json() if response.status_code == 200 else None
                }
            except Exception as e:
                results[container] = {
                    "port": port,
                    "status": "unreachable",
                    "error": str(e)
                }
        
        return MCPResponse(content=[{
            "type": "text",
            "text": json.dumps(results, indent=2)
        }])
    
    async def query_service(self, args: Dict) -> MCPResponse:
        """Query a specific service"""
        port = args.get('port')
        endpoint = args.get('endpoint')
        method = args.get('method', 'GET').upper()
        data = args.get('data', {})
        
        if port not in self.services:
            return MCPResponse(
                content=[{
                    "type": "text",
                    "text": f"Service on port {port} not found"
                }],
                isError=True
            )
        
        try:
            url = f"http://localhost:{port}{endpoint}"
            
            if method == 'GET':
                response = await self.http_client.get(url)
            elif method == 'POST':
                response = await self.http_client.post(url, json=data)
            elif method == 'PUT':
                response = await self.http_client.put(url, json=data)
            elif method == 'DELETE':
                response = await self.http_client.delete(url)
            else:
                return MCPResponse(
                    content=[{"type": "text", "text": f"Unsupported method: {method}"}],
                    isError=True
                )
            
            result = {
                "service": self.services[port].get('container'),
                "port": port,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            return MCPResponse(content=[{
                "type": "text",
                "text": json.dumps(result, indent=2)
            }])
            
        except Exception as e:
            return MCPResponse(
                content=[{
                    "type": "text",
                    "text": f"Error querying service: {str(e)}"
                }],
                isError=True
            )
    
    async def list_services(self, args: Dict) -> MCPResponse:
        """List all services"""
        category = args.get('category')
        
        # Load full platform map for categories
        with open(self.registry_path) as f:
            platform_map = json.load(f)
        
        categories = platform_map.get('categories', {})
        
        if category:
            services_list = categories.get(category, [])
            result = {
                "category": category,
                "services": []
            }
            
            for service_name in services_list:
                # Find port for this service
                for port, info in self.services.items():
                    if info.get('container') == service_name:
                        result["services"].append({
                            "name": service_name,
                            "port": port,
                            "image": info.get('image'),
                            "url": f"http://localhost:{port}"
                        })
                        break
        else:
            result = {
                "total_services": len(self.services),
                "categories": {}
            }
            
            for cat_name, services_list in categories.items():
                result["categories"][cat_name] = {
                    "count": len(services_list),
                    "services": []
                }
                
                for service_name in services_list:
                    for port, info in self.services.items():
                        if info.get('container') == service_name:
                            result["categories"][cat_name]["services"].append({
                                "name": service_name,
                                "port": port,
                                "url": f"http://localhost:{port}"
                            })
                            break
        
        return MCPResponse(content=[{
            "type": "text",
            "text": json.dumps(result, indent=2)
        }])
    
    async def batch_query_services(self, args: Dict) -> MCPResponse:
        """Query multiple services in parallel"""
        queries = args.get('queries', [])
        
        async def single_query(query: Dict):
            return await self.query_service(query)
        
        tasks = [single_query(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                formatted_results.append({
                    "query_index": i,
                    "error": str(result)
                })
            else:
                formatted_results.append({
                    "query_index": i,
                    "result": json.loads(result.content[0]['text'])
                })
        
        return MCPResponse(content=[{
            "type": "text",
            "text": json.dumps(formatted_results, indent=2)
        }])
    
    async def get_service_info(self, args: Dict) -> MCPResponse:
        """Get detailed service information"""
        port = args.get('port')
        
        if port not in self.services:
            return MCPResponse(
                content=[{"type": "text", "text": f"Service on port {port} not found"}],
                isError=True
            )
        
        service_info = self.services[port]
        
        # Try to get additional info from the service
        try:
            health_response = await self.http_client.get(
                f"http://localhost:{port}/health",
                timeout=5.0
            )
            service_info['health'] = health_response.json() if health_response.status_code == 200 else None
        except:
            service_info['health'] = None
        
        try:
            info_response = await self.http_client.get(
                f"http://localhost:{port}/info",
                timeout=5.0
            )
            service_info['info'] = info_response.json() if info_response.status_code == 200 else None
        except:
            service_info['info'] = None
        
        return MCPResponse(content=[{
            "type": "text",
            "text": json.dumps(service_info, indent=2)
        }])
    
    async def call_tool(self, tool_call: MCPToolCall) -> MCPResponse:
        """Execute tool call"""
        handlers = {
            'platform_health_check': self.platform_health_check,
            'query_service': self.query_service,
            'list_services': self.list_services,
            'batch_query_services': self.batch_query_services,
            'get_service_info': self.get_service_info
        }
        
        handler = handlers.get(tool_call.name)
        if not handler:
            return MCPResponse(
                content=[{"type": "text", "text": f"Unknown tool: {tool_call.name}"}],
                isError=True
            )
        
        try:
            return await handler(tool_call.arguments)
        except Exception as e:
            return MCPResponse(
                content=[{"type": "text", "text": f"Tool error: {str(e)}"}],
                isError=True
            )


# FastAPI app for MCP server
app = FastAPI(title="AI Research Platform MCP Server")
mcp_server = AIResearchPlatformMCP()


@app.get("/mcp/tools")
async def list_tools():
    """List available MCP tools"""
    return {"tools": [tool.dict() for tool in mcp_server.tools]}


@app.post("/mcp/call-tool")
async def call_tool(tool_call: MCPToolCall):
    """Execute a tool call"""
    response = await mcp_server.call_tool(tool_call)
    return response.dict()


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "services_loaded": len(mcp_server.services)}


def main():
    """Run MCP server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Research Platform MCP Server")
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=9000, help='Port to bind to')
    parser.add_argument('--registry', default='platform_discovery/platform_map.json', help='Service registry path')
    
    args = parser.parse_args()
    
    print("🚀 Starting AI Research Platform MCP Server")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Registry: {args.registry}")
    print()
    
    # Update registry path
    global mcp_server
    mcp_server = AIResearchPlatformMCP(args.registry)
    
    print(f"✅ MCP Server ready with {len(mcp_server.tools)} tools")
    print(f"   Tools endpoint: http://{args.host}:{args.port}/mcp/tools")
    print(f"   Call endpoint: http://{args.host}:{args.port}/mcp/call-tool")
    print()
    
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == '__main__':
    main()