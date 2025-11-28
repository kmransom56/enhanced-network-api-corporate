#!/usr/bin/env python3
"""
API Documentation and LLM Integration for FortiGate and Meraki
Provides intelligent API request generation and documentation lookup
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

@dataclass
class APIEndpoint:
    """API endpoint documentation"""
    method: str
    path: str
    description: str
    parameters: Dict[str, Any]
    response_schema: Dict[str, Any]
    examples: List[Dict[str, Any]]
    category: str

@dataclass
class LLMAPIRequest:
    """Generated API request from LLM"""
    endpoint: str
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]]
    description: str
    confidence: float

class APIKnowledgeBase:
    """Knowledge base for FortiGate and Meraki APIs"""
    
    def __init__(self):
        self.fortigate_endpoints = self._load_fortigate_docs()
        self.meraki_endpoints = self._load_meraki_docs()
        
    def _load_fortigate_docs(self) -> Dict[str, APIEndpoint]:
        """Load FortiGate API documentation"""
        return {
            "system_status": APIEndpoint(
                method="GET",
                path="/api/v2/cmdb/system/status",
                description="Get FortiGate system status and information",
                parameters={},
                response_schema={
                    "hostname": "string",
                    "serial": "string", 
                    "version": "string",
                    "model": "string",
                    "cpu_usage": "number",
                    "memory_usage": "number"
                },
                examples=[{
                    "description": "Get system status",
                    "request": "GET /api/v2/cmdb/system/status"
                }],
                category="system"
            ),
            "interfaces": APIEndpoint(
                method="GET",
                path="/api/v2/cmdb/system/interface",
                description="Get network interface configuration",
                parameters={
                    "filter": "string (optional)",
                    "scope": "string (optional)"
                },
                response_schema={
                    "results": [
                        {
                            "name": "string",
                            "ip": "string",
                            "subnet": "string",
                            "status": "string",
                            "speed": "string"
                        }
                    ]
                },
                examples=[{
                    "description": "Get all interfaces",
                    "request": "GET /api/v2/cmdb/system/interface"
                }],
                category="network"
            ),
            "firewall_policies": APIEndpoint(
                method="GET", 
                path="/api/v2/cmdb/firewall/policy",
                description="Get firewall policy configuration",
                parameters={
                    "filter": "string (optional)",
                    "scope": "string (optional)"
                },
                response_schema={
                    "results": [
                        {
                            "policyid": "number",
                            "name": "string",
                            "srcintf": "string",
                            "dstintf": "string",
                            "srcaddr": "string",
                            "dstaddr": "string",
                            "service": "string",
                            "action": "string"
                        }
                    ]
                },
                examples=[{
                    "description": "Get all firewall policies",
                    "request": "GET /api/v2/cmdb/firewall/policy"
                }],
                category="security"
            ),
            "vips": APIEndpoint(
                method="GET",
                path="/api/v2/cmdb/firewall/vip", 
                description="Get virtual IP configuration",
                parameters={
                    "filter": "string (optional)"
                },
                response_schema={
                    "results": [
                        {
                            "name": "string",
                            "type": "string",
                            "extip": "string",
                            "extintf": "string",
                            "mappedip": "string"
                        }
                    ]
                },
                examples=[{
                    "description": "Get all VIPs",
                    "request": "GET /api/v2/cmdb/firewall/vip"
                }],
                category="security"
            ),
            "resource_usage": APIEndpoint(
                method="GET",
                path="/api/v2/monitor/system/resource/usage",
                description="Get system resource usage (CPU, memory, sessions)",
                parameters={},
                response_schema={
                    "results": [
                        {
                            "cpu_usage": "number",
                            "memory_usage": "number", 
                            "current_sessions": "number"
                        }
                    ]
                },
                examples=[{
                    "description": "Get resource usage",
                    "request": "GET /api/v2/monitor/system/resource/usage"
                }],
                category="monitoring"
            )
        }
    
    def _load_meraki_docs(self) -> Dict[str, APIEndpoint]:
        """Load Meraki API documentation"""
        return {
            "organizations": APIEndpoint(
                method="GET",
                path="/organizations",
                description="List organizations",
                parameters={},
                response_schema={
                    "id": "string",
                    "name": "string",
                    "url": "string"
                },
                examples=[{
                    "description": "List all organizations",
                    "request": "GET /organizations"
                }],
                category="organization"
            ),
            "networks": APIEndpoint(
                method="GET",
                path="/organizations/{organizationId}/networks",
                description="List networks in an organization",
                parameters={
                    "organizationId": "string (required)",
                    "configTemplateId": "string (optional)",
                    "isBoundToConfigTemplate": "boolean (optional)"
                },
                response_schema={
                    "id": "string",
                    "name": "string",
                    "productTypes": ["string"]
                },
                examples=[{
                    "description": "Get networks for organization",
                    "request": "GET /organizations/12345/networks"
                }],
                category="network"
            ),
            "devices": APIEndpoint(
                method="GET",
                path="/organizations/{organizationId}/devices",
                description="List devices in an organization",
                parameters={
                    "organizationId": "string (required)",
                    "networkIds": "string (optional)",
                    "productTypes": "string (optional)"
                },
                response_schema={
                    "id": "string",
                    "name": "string",
                    "model": "string",
                    "productType": "string",
                    "status": "string"
                },
                examples=[{
                    "description": "Get all devices",
                    "request": "GET /organizations/12345/devices"
                }],
                category="device"
            ),
            "switch_ports": APIEndpoint(
                method="GET",
                path="/devices/{serial}/switch/ports",
                description="List switch ports",
                parameters={
                    "serial": "string (required)",
                    "numbers": "string (optional)"
                },
                response_schema={
                    "number": "number",
                    "name": "string",
                    "type": "string",
                    "status": "string"
                },
                examples=[{
                    "description": "Get switch ports",
                    "request": "GET /devices/Q2XX-XXXX-XXXX/switch/ports"
                }],
                category="switch"
            ),
            "access_points": APIEndpoint(
                method="GET",
                path="/networks/{networkId}/devices",
                description="List access points in a network",
                parameters={
                    "networkId": "string (required)",
                    "productTypes": "wireless"
                },
                response_schema={
                    "id": "string",
                    "name": "string",
                    "model": "string",
                    "status": "string"
                },
                examples=[{
                    "description": "Get wireless access points",
                    "request": "GET /networks/12345/devices?productTypes=wireless"
                }],
                category="wireless"
            )
        }

class LLMAPIClient:
    """Client for querying LLM for API request generation"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "fortinet-custom"):
        self.base_url = base_url
        self.model = model
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_api_request(self, user_query: str, api_docs: Dict[str, APIEndpoint], 
                                 device_info: Dict[str, Any]) -> LLMAPIRequest:
        """Generate API request from natural language query"""
        
        # Build context for LLM
        context = self._build_context(user_query, api_docs, device_info)
        
        # Create prompt for LLM
        prompt = f"""
You are a network API expert. Based on the user's request and available API endpoints, generate the appropriate API call.

USER REQUEST: {user_query}

DEVICE CONTEXT: {json.dumps(device_info, indent=2)}

AVAILABLE API ENDPOINTS:
{self._format_api_docs(api_docs)}

RESPONSE FORMAT (JSON):
{{
    "endpoint": "endpoint_name",
    "method": "HTTP_METHOD", 
    "url": "full_api_url",
    "headers": {{"Authorization": "Bearer token"}},
    "body": {{}} or null,
    "description": "what this API call does",
    "confidence": 0.95
}}

Generate the most appropriate API call for this request. Return only valid JSON.
"""
        
        try:
            # Query LLM (Ollama format)
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "max_tokens": 500
                    }
                },
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    llm_response = result.get("response", "")
                    
                    # Parse JSON from response
                    try:
                        api_request_data = json.loads(llm_response)
                        return LLMAPIRequest(**api_request_data)
                    except json.JSONDecodeError:
                        # Fallback: extract JSON from text
                        import re
                        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                        if json_match:
                            api_request_data = json.loads(json_match.group())
                            return LLMAPIRequest(**api_request_data)
                        else:
                            raise ValueError("Could not parse LLM response")
                else:
                    logger.error(f"LLM API error: {response.status}")
                    raise Exception("LLM request failed")
                    
        except Exception as e:
            logger.error(f"Error generating API request: {e}")
            # Return fallback request
            return self._generate_fallback_request(user_query, api_docs)
    
    def _build_context(self, query: str, api_docs: Dict[str, APIEndpoint], 
                      device_info: Dict[str, Any]) -> str:
        """Build context for LLM"""
        context_parts = [
            f"Query: {query}",
            f"Device Type: {device_info.get('type', 'unknown')}",
            f"Device IP: {device_info.get('ip', 'unknown')}",
            f"Available Endpoints: {len(api_docs)}"
        ]
        return "\n".join(context_parts)
    
    def _format_api_docs(self, api_docs: Dict[str, APIEndpoint]) -> str:
        """Format API docs for LLM"""
        formatted = []
        for name, endpoint in api_docs.items():
            formatted.append(f"""
{name}:
  Method: {endpoint.method}
  Path: {endpoint.path}  
  Description: {endpoint.description}
  Category: {endpoint.category}
""")
        return "\n".join(formatted)
    
    def _generate_fallback_request(self, query: str, api_docs: Dict[str, APIEndpoint]) -> LLMAPIRequest:
        """Generate fallback API request based on keywords"""
        query_lower = query.lower()
        
        # Simple keyword matching
        if "status" in query_lower or "system" in query_lower:
            endpoint = api_docs.get("system_status")
        elif "interface" in query_lower:
            endpoint = api_docs.get("interfaces")
        elif "firewall" in query_lower or "policy" in query_lower:
            endpoint = api_docs.get("firewall_policies")
        elif "vip" in query_lower or "virtual" in query_lower:
            endpoint = api_docs.get("vips")
        elif "resource" in query_lower or "cpu" in query_lower or "memory" in query_lower:
            endpoint = api_docs.get("resource_usage")
        else:
            endpoint = api_docs.get("system_status")  # Default
        
        if endpoint:
            return LLMAPIRequest(
                endpoint=endpoint.path.split("/")[-1],
                method=endpoint.method,
                url=endpoint.path,
                headers={"Authorization": "Bearer <API_TOKEN>"},
                body=None,
                description=f"Generated request for: {query}",
                confidence=0.5
            )
        else:
            raise ValueError("No suitable endpoint found")

class APIRequestExecutor:
    """Execute generated API requests safely"""
    
    def __init__(self, api_base_url: str, auth_token: str):
        self.api_base_url = api_base_url
        self.auth_token = auth_token
        
    async def execute_request(self, request: LLMAPIRequest) -> Dict[str, Any]:
        """Execute API request and return response"""
        
        headers = request.headers.copy()
        headers["Authorization"] = f"Bearer {self.auth_token}"
        
        full_url = urljoin(self.api_base_url, request.url)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=request.method,
                    url=full_url,
                    headers=headers,
                    json=request.body,
                    timeout=30
                ) as response:
                    
                    result = {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "url": str(response.url),
                        "method": request.method,
                        "success": response.status < 400
                    }
                    
                    try:
                        result["data"] = await response.json()
                    except:
                        result["data"] = await response.text()
                    
                    return result
                    
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
                "url": full_url,
                "method": request.method
            }

class IntelligentAPIMCP:
    """MCP server with intelligent API request generation"""
    
    def __init__(self):
        self.knowledge_base = APIKnowledgeBase()
        self.llm_client = None
        
    async def initialize(self, llm_base_url: str = "http://localhost:11434", 
                        llm_model: str = "fortinet-custom"):
        """Initialize LLM client"""
        self.llm_client = LLMAPIClient(llm_base_url, llm_model)
        logger.info("Intelligent API MCP initialized")
    
    async def query_api_documentation(self, query: str, device_type: str = "fortigate") -> Dict[str, Any]:
        """Query API documentation"""
        
        if device_type == "fortigate":
            docs = self.knowledge_base.fortigate_endpoints
        elif device_type == "meraki":
            docs = self.knowledge_base.meraki_endpoints
        else:
            docs = {**self.knowledge_base.fortigate_endpoints, **self.knowledge_base.meraki_endpoints}
        
        # Search for relevant endpoints
        results = []
        query_lower = query.lower()
        
        for name, endpoint in docs.items():
            score = 0
            if query_lower in endpoint.description.lower():
                score += 3
            if query_lower in endpoint.path.lower():
                score += 2
            if query_lower in endpoint.category.lower():
                score += 1
            
            if score > 0:
                results.append({
                    "name": name,
                    "endpoint": endpoint,
                    "relevance_score": score
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return {
            "query": query,
            "device_type": device_type,
            "results": [
                {
                    "name": r["name"],
                    "method": r["endpoint"].method,
                    "path": r["endpoint"].path,
                    "description": r["endpoint"].description,
                    "category": r["endpoint"].category,
                    "relevance_score": r["relevance_score"]
                }
                for r in results[:5]  # Top 5 results
            ]
        }
    
    async def generate_api_request(self, user_query: str, device_info: Dict[str, Any],
                                 device_type: str = "fortigate") -> LLMAPIRequest:
        """Generate API request using LLM"""
        
        if not self.llm_client:
            raise ValueError("LLM client not initialized")
        
        if device_type == "fortigate":
            api_docs = self.knowledge_base.fortigate_endpoints
        elif device_type == "meraki":
            api_docs = self.knowledge_base.meraki_endpoints
        else:
            api_docs = {**self.knowledge_base.fortigate_endpoints, **self.knowledge_base.meraki_endpoints}
        
        async with self.llm_client:
            return await self.llm_client.generate_api_request(user_query, api_docs, device_info)

# Test function
async def test_intelligent_api():
    """Test the intelligent API system"""
    api_mcp = IntelligentAPIMCP()
    await api_mcp.initialize()
    
    # Test documentation query
    docs = await api_mcp.query_api_documentation("get system status")
    print("📚 API Documentation Results:")
    for result in docs["results"]:
        print(f"  {result['name']}: {result['description']} (score: {result['relevance_score']})")
    
    # Test API request generation
    device_info = {
        "type": "fortigate",
        "ip": "192.168.0.254",
        "model": "FG600E"
    }
    
    request = await api_mcp.generate_api_request(
        "Show me the system status and resource usage",
        device_info
    )
    
    print(f"\n🤖 Generated API Request:")
    print(f"  Method: {request.method}")
    print(f"  URL: {request.url}")
    print(f"  Description: {request.description}")
    print(f"  Confidence: {request.confidence}")

if __name__ == "__main__":
    asyncio.run(test_intelligent_api())
