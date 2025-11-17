"""
Enhanced API Documentation Loader
Loads and processes Fortinet and Meraki API documentation for accurate application building
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from network_api_parser import APIDocumentation, APIEndpoint, APIParameter, APIMethod


@dataclass
class RealAPIEndpoint:
    """Enhanced API endpoint with real documentation data"""
    id: int
    endpoint: str
    method: str
    description: str
    category: str
    subcategory: str
    parameters: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    authentication: Dict[str, Any] = field(default_factory=dict)
    rate_limits: Dict[str, Any] = field(default_factory=dict)
    response_schema: Dict[str, Any] = field(default_factory=dict)
    request_schema: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class LoadedAPIDocumentation:
    """Complete API documentation with real data"""
    name: str
    version: str
    platform: str  # fortinet, meraki
    base_url: str
    authentication_type: str
    endpoints: List[RealAPIEndpoint] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    total_endpoints: int = 0
    extraction_date: str = ""
    source: str = ""


class APIDocumentationLoader:
    """Loads real API documentation from the uploaded files"""
    
    def __init__(self, api_directory: str = "./api"):
        self.api_dir = Path(api_directory)
        self.documentation = {}
        
    def load_all_documentation(self) -> Dict[str, LoadedAPIDocumentation]:
        """Load all available API documentation"""
        # Load Fortinet/FortiManager API documentation
        fortinet_doc = self._load_fortinet_documentation()
        if fortinet_doc:
            self.documentation["fortinet"] = fortinet_doc
            
        # Load Meraki API documentation
        meraki_doc = self._load_meraki_documentation()
        if meraki_doc:
            self.documentation["meraki"] = meraki_doc
            
        return self.documentation
    
    def _load_fortinet_documentation(self) -> Optional[LoadedAPIDocumentation]:
        """Load Fortinet/FortiManager API documentation"""
        endpoints_file = self.api_dir / "fortimanager_api_endpoints.json"
        detailed_file = self.api_dir / "fortimanager_api_detailed.json"
        summary_file = self.api_dir / "FORTIMANAGER_API_SUMMARY.md"
        
        if not endpoints_file.exists():
            print(f"FortiManager endpoints file not found: {endpoints_file}")
            return None
            
        try:
            # Load main endpoints data
            with open(endpoints_file, 'r') as f:
                endpoints_data = json.load(f)
            
            # Load detailed data if available
            detailed_data = {}
            if detailed_file.exists():
                with open(detailed_file, 'r') as f:
                    detailed_data = json.load(f)
            
            # Create documentation object
            doc = LoadedAPIDocumentation(
                name="FortiManager API",
                version="7.0",
                platform="fortinet",
                base_url="https://fortimanager.example.com/jsonrpc",
                authentication_type="Session-based",
                extraction_date=endpoints_data.get("extraction_date", ""),
                source=endpoints_data.get("source", ""),
                total_endpoints=endpoints_data.get("total_endpoints", 0)
            )
            
            # Extract categories
            categories = endpoints_data.get("categories", [])
            doc.categories = [cat.get("category", "") for cat in categories]
            
            # Load all endpoints
            for category in categories:
                for endpoint_data in category.get("endpoints", []):
                    endpoint = RealAPIEndpoint(
                        id=endpoint_data.get("id", 0),
                        endpoint=endpoint_data.get("endpoint", ""),
                        method=endpoint_data.get("method", "POST"),
                        description=endpoint_data.get("description", ""),
                        category=endpoint_data.get("category", ""),
                        subcategory=endpoint_data.get("subcategory", ""),
                        parameters=endpoint_data.get("parameters", []),
                        examples=endpoint_data.get("examples", [])
                    )
                    
                    # Add detailed information if available
                    endpoint_id = str(endpoint.id)
                    if endpoint_id in detailed_data:
                        detail = detailed_data[endpoint_id]
                        endpoint.authentication = detail.get("authentication", {})
                        endpoint.rate_limits = detail.get("rate_limits", {})
                        endpoint.response_schema = detail.get("response_schema", {})
                        endpoint.request_schema = detail.get("request_schema", {})
                        endpoint.tags = detail.get("tags", [])
                    
                    doc.endpoints.append(endpoint)
            
            return doc
            
        except Exception as e:
            print(f"Error loading Fortinet documentation: {e}")
            return None
    
    def _load_meraki_documentation(self) -> Optional[LoadedAPIDocumentation]:
        """Load Meraki API documentation from Postman collection"""
        postman_file = self.api_dir / "Meraki Dashboard API - v1.63.0.postman_collection.json"
        
        if not postman_file.exists():
            print(f"Meraki Postman collection not found: {postman_file}")
            return None
            
        try:
            with open(postman_file, 'r') as f:
                collection = json.load(f)
            
            # Create documentation object
            info = collection.get("info", {})
            doc = LoadedAPIDocumentation(
                name=info.get("name", "Meraki Dashboard API"),
                version="v1.63.0",
                platform="meraki",
                base_url="https://api.meraki.com/api/v1",
                authentication_type="API Key",
                extraction_date=datetime.now().isoformat(),
                source="Postman Collection v1.63.0"
            )
            
            # Parse items recursively
            endpoint_id = 1
            self._parse_meraki_items(collection.get("item", []), doc, "", endpoint_id)
            
            doc.total_endpoints = len(doc.endpoints)
            
            return doc
            
        except Exception as e:
            print(f"Error loading Meraki documentation: {e}")
            return None
    
    def _parse_meraki_items(self, items: List[Dict], doc: LoadedAPIDocumentation, 
                           category: str, endpoint_id: int) -> int:
        """Recursively parse Meraki Postman collection items"""
        for item in items:
            if 'item' in item:
                # This is a folder
                folder_name = item.get('name', '')
                doc.categories.append(folder_name)
                endpoint_id = self._parse_meraki_items(
                    item['item'], doc, folder_name, endpoint_id
                )
            elif 'request' in item:
                # This is a request
                request = item['request']
                
                # Extract method and URL
                method = request.get('method', 'GET')
                url_data = request.get('url', {})
                
                # Build endpoint path
                if isinstance(url_data, str):
                    endpoint_path = url_data
                else:
                    raw_url = url_data.get('raw', '')
                    # Extract path from full URL
                    import re
                    path_match = re.search(r'{{baseUrl}}(/.*?)(?:\?|$|}})', raw_url)
                    if path_match:
                        endpoint_path = path_match.group(1)
                    else:
                        # Try to build from path array
                        path_array = url_data.get('path', [])
                        endpoint_path = '/' + '/'.join(path_array) if path_array else raw_url
                
                # Extract parameters
                parameters = []
                if isinstance(url_data, dict) and 'query' in url_data:
                    for param in url_data['query']:
                        param_str = f"{param.get('key', '')} - {param.get('description', '')}"
                        parameters.append(param_str)
                
                # Create endpoint
                endpoint = RealAPIEndpoint(
                    id=endpoint_id,
                    endpoint=endpoint_path,
                    method=method,
                    description=item.get('name', ''),
                    category=category,
                    subcategory="",
                    parameters=parameters
                )
                
                # Extract examples from request
                if 'body' in request and request['body'].get('mode') == 'raw':
                    try:
                        example_body = json.loads(request['body']['raw'])
                        endpoint.examples = [{"request_body": example_body}]
                    except:
                        pass
                
                # Extract auth requirements
                if 'auth' in request or any(h.get('key', '').lower() in ['authorization', 'x-cisco-meraki-api-key'] 
                                         for h in request.get('header', [])):
                    endpoint.authentication = {"required": True, "type": "API Key"}
                
                doc.endpoints.append(endpoint)
                endpoint_id += 1
        
        return endpoint_id
    
    def get_endpoints_by_category(self, platform: str, category: str) -> List[RealAPIEndpoint]:
        """Get all endpoints for a specific category"""
        if platform not in self.documentation:
            return []
            
        doc = self.documentation[platform]
        return [ep for ep in doc.endpoints if category.lower() in ep.category.lower()]
    
    def search_endpoints(self, platform: str, search_term: str) -> List[RealAPIEndpoint]:
        """Search endpoints by term in endpoint path, description, or category"""
        if platform not in self.documentation:
            return []
            
        doc = self.documentation[platform]
        search_lower = search_term.lower()
        
        return [
            ep for ep in doc.endpoints
            if (search_lower in ep.endpoint.lower() or
                search_lower in ep.description.lower() or
                search_lower in ep.category.lower())
        ]
    
    def get_endpoint_by_id(self, platform: str, endpoint_id: int) -> Optional[RealAPIEndpoint]:
        """Get specific endpoint by ID"""
        if platform not in self.documentation:
            return None
            
        doc = self.documentation[platform]
        for endpoint in doc.endpoints:
            if endpoint.id == endpoint_id:
                return endpoint
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded API documentation"""
        stats = {
            "platforms": list(self.documentation.keys()),
            "total_endpoints": 0,
            "by_platform": {}
        }
        
        for platform, doc in self.documentation.items():
            platform_stats = {
                "name": doc.name,
                "version": doc.version,
                "total_endpoints": doc.total_endpoints,
                "categories": len(doc.categories),
                "category_list": doc.categories,
                "extraction_date": doc.extraction_date,
                "source": doc.source
            }
            
            # Count by method
            method_counts = {}
            for endpoint in doc.endpoints:
                method = endpoint.method
                method_counts[method] = method_counts.get(method, 0) + 1
            
            platform_stats["methods"] = method_counts
            stats["by_platform"][platform] = platform_stats
            stats["total_endpoints"] += doc.total_endpoints
        
        return stats
    
    def export_to_openapi(self, platform: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Export loaded documentation to OpenAPI 3.0 format"""
        if platform not in self.documentation:
            raise ValueError(f"Platform {platform} not loaded")
        
        doc = self.documentation[platform]
        
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": doc.name,
                "version": doc.version,
                "description": f"Auto-generated from {doc.source}"
            },
            "servers": [
                {"url": doc.base_url}
            ],
            "security": [],
            "components": {
                "securitySchemes": {},
                "schemas": {}
            },
            "paths": {}
        }
        
        # Add security scheme
        if doc.authentication_type == "API Key":
            openapi_spec["components"]["securitySchemes"]["ApiKeyAuth"] = {
                "type": "apiKey",
                "in": "header",
                "name": "X-Cisco-Meraki-API-Key" if platform == "meraki" else "Authorization"
            }
            openapi_spec["security"] = [{"ApiKeyAuth": []}]
        elif doc.authentication_type == "Session-based":
            openapi_spec["components"]["securitySchemes"]["SessionAuth"] = {
                "type": "http",
                "scheme": "bearer",
                "description": "Session-based authentication"
            }
            openapi_spec["security"] = [{"SessionAuth": []}]
        
        # Convert endpoints to OpenAPI paths
        for endpoint in doc.endpoints:
            path = endpoint.endpoint
            method = endpoint.method.lower()
            
            if path not in openapi_spec["paths"]:
                openapi_spec["paths"][path] = {}
            
            operation = {
                "summary": endpoint.description,
                "description": f"Category: {endpoint.category}",
                "tags": [endpoint.category],
                "parameters": [],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
            
            # Add parameters from documentation
            for param_str in endpoint.parameters:
                # Parse parameter string (format: "name - description")
                if " - " in param_str:
                    param_name, param_desc = param_str.split(" - ", 1)
                    operation["parameters"].append({
                        "name": param_name.strip(),
                        "in": "query",
                        "description": param_desc.strip(),
                        "required": False,
                        "schema": {"type": "string"}
                    })
            
            # Add request body for POST/PUT methods
            if method in ['post', 'put', 'patch']:
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
            
            openapi_spec["paths"][path][method] = operation
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(openapi_spec, f, indent=2)
        
        return openapi_spec
    
    def create_endpoint_reference(self, platform: str, output_file: Optional[str] = None) -> str:
        """Create a comprehensive endpoint reference document"""
        if platform not in self.documentation:
            raise ValueError(f"Platform {platform} not loaded")
        
        doc = self.documentation[platform]
        
        reference = f"""# {doc.name} - API Endpoint Reference
**Version:** {doc.version}  
**Platform:** {platform.title()}  
**Base URL:** {doc.base_url}  
**Authentication:** {doc.authentication_type}  
**Total Endpoints:** {doc.total_endpoints}  
**Source:** {doc.source}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
        
        # Group endpoints by category
        categories = {}
        for endpoint in doc.endpoints:
            category = endpoint.category or "Uncategorized"
            if category not in categories:
                categories[category] = []
            categories[category].append(endpoint)
        
        # Generate reference for each category
        for category, endpoints in sorted(categories.items()):
            reference += f"## {category}\n\n"
            reference += f"**Endpoints in this category:** {len(endpoints)}\n\n"
            
            for endpoint in sorted(endpoints, key=lambda x: x.endpoint):
                reference += f"### {endpoint.method} {endpoint.endpoint}\n"
                reference += f"**ID:** {endpoint.id}  \n"
                reference += f"**Description:** {endpoint.description}  \n"
                
                if endpoint.subcategory:
                    reference += f"**Subcategory:** {endpoint.subcategory}  \n"
                
                if endpoint.parameters:
                    reference += f"**Parameters:**\n"
                    for param in endpoint.parameters:
                        reference += f"- {param}\n"
                
                if endpoint.examples:
                    reference += f"**Examples:** {len(endpoint.examples)} available\n"
                
                reference += "\n---\n\n"
        
        # Add summary statistics
        reference += f"## API Statistics\n\n"
        reference += f"- **Total Categories:** {len(categories)}\n"
        reference += f"- **Total Endpoints:** {len(doc.endpoints)}\n"
        
        # Method distribution
        method_counts = {}
        for endpoint in doc.endpoints:
            method = endpoint.method
            method_counts[method] = method_counts.get(method, 0) + 1
        
        reference += f"- **Methods Distribution:**\n"
        for method, count in sorted(method_counts.items()):
            reference += f"  - {method}: {count} endpoints\n"
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(reference)
        
        return reference


# Example usage and testing
if __name__ == "__main__":
    # Load all API documentation
    loader = APIDocumentationLoader()
    docs = loader.load_all_documentation()
    
    print("Loaded API Documentation:")
    for platform, doc in docs.items():
        print(f"  {platform}: {doc.name} ({doc.total_endpoints} endpoints)")
    
    # Print statistics
    stats = loader.get_statistics()
    print(f"\nTotal endpoints across all platforms: {stats['total_endpoints']}")
    
    # Search for firewall-related endpoints
    if "fortinet" in docs:
        firewall_endpoints = loader.search_endpoints("fortinet", "firewall")
        print(f"\nFound {len(firewall_endpoints)} firewall-related endpoints in Fortinet API")
        
        # Show first few
        for endpoint in firewall_endpoints[:3]:
            print(f"  {endpoint.method} {endpoint.endpoint} - {endpoint.description}")
    
    # Generate OpenAPI spec for Fortinet
    if "fortinet" in docs:
        try:
            openapi = loader.export_to_openapi("fortinet", "fortinet_api_openapi.json")
            print(f"\nGenerated OpenAPI spec with {len(openapi['paths'])} paths")
        except Exception as e:
            print(f"Error generating OpenAPI: {e}")
    
    # Generate endpoint reference
    if "fortinet" in docs:
        try:
            reference = loader.create_endpoint_reference("fortinet", "fortinet_api_reference.md")
            print(f"\nGenerated API reference document ({len(reference)} characters)")
        except Exception as e:
            print(f"Error generating reference: {e}")