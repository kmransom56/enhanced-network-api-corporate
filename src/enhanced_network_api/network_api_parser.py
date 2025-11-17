"""
Network API Documentation Parser for Fortinet and Meraki
This module provides comprehensive parsing capabilities for network device API documentation
"""

import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import markdown
from bs4 import BeautifulSoup


class APIMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class APIParameter:
    name: str
    type: str
    required: bool
    description: str
    default: Optional[Any] = None
    enum_values: List[str] = field(default_factory=list)
    example: Optional[Any] = None


@dataclass
class APIEndpoint:
    path: str
    method: APIMethod
    description: str
    parameters: List[APIParameter] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    authentication_required: bool = True
    rate_limit: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class APIDocumentation:
    name: str
    version: str
    base_url: str
    authentication_type: str
    endpoints: List[APIEndpoint] = field(default_factory=list)
    global_headers: Dict[str, str] = field(default_factory=dict)
    rate_limits: Dict[str, str] = field(default_factory=dict)


class NetworkAPIParser:
    """Main parser class for network API documentation"""
    
    def __init__(self, documentation_path: str):
        self.doc_path = Path(documentation_path)
        self.fortinet_patterns = {
            'endpoint': r'/api/v\d+/cmdb/.*',
            'auth': r'Authorization:\s*Bearer\s+.*',
            'method': r'(GET|POST|PUT|DELETE|PATCH)',
        }
        self.meraki_patterns = {
            'endpoint': r'/api/v\d+/.*',
            'auth': r'X-Cisco-Meraki-API-Key:\s*.*',
            'method': r'(GET|POST|PUT|DELETE)',
        }
        
    def parse_documentation(self, platform: str = "both") -> Dict[str, APIDocumentation]:
        """Parse API documentation for specified platform(s)"""
        results = {}
        
        if platform in ["fortinet", "both"]:
            fortinet_docs = self._parse_fortinet_docs()
            if fortinet_docs:
                results["fortinet"] = fortinet_docs
                
        if platform in ["meraki", "both"]:
            meraki_docs = self._parse_meraki_docs()
            if meraki_docs:
                results["meraki"] = meraki_docs
                
        return results
    
    def _parse_fortinet_docs(self) -> Optional[APIDocumentation]:
        """Parse Fortinet API documentation"""
        doc = APIDocumentation(
            name="Fortinet FortiGate API",
            version="7.0",
            base_url="https://fortigate.example.com",
            authentication_type="Bearer Token"
        )
        
        # Look for Fortinet documentation files
        fortinet_files = list(self.doc_path.glob("**/fortinet*.{json,yaml,yml,md,html}"))
        fortinet_files.extend(list(self.doc_path.glob("**/forti*.{json,yaml,yml,md,html}")))
        
        for file_path in fortinet_files:
            if file_path.suffix == '.json':
                self._parse_json_file(file_path, doc, "fortinet")
            elif file_path.suffix in ['.yaml', '.yml']:
                self._parse_yaml_file(file_path, doc, "fortinet")
            elif file_path.suffix == '.md':
                self._parse_markdown_file(file_path, doc, "fortinet")
            elif file_path.suffix == '.html':
                self._parse_html_file(file_path, doc, "fortinet")
                
        return doc if doc.endpoints else None
    
    def _parse_meraki_docs(self) -> Optional[APIDocumentation]:
        """Parse Meraki API documentation"""
        doc = APIDocumentation(
            name="Cisco Meraki Dashboard API",
            version="1.0",
            base_url="https://api.meraki.com/api/v1",
            authentication_type="API Key"
        )
        
        # Look for Meraki documentation files
        meraki_files = list(self.doc_path.glob("**/meraki*.{json,yaml,yml,md,html}"))
        meraki_files.extend(list(self.doc_path.glob("**/dashboard*.{json,yaml,yml,md,html}")))
        
        for file_path in meraki_files:
            if file_path.suffix == '.json':
                self._parse_json_file(file_path, doc, "meraki")
            elif file_path.suffix in ['.yaml', '.yml']:
                self._parse_yaml_file(file_path, doc, "meraki")
            elif file_path.suffix == '.md':
                self._parse_markdown_file(file_path, doc, "meraki")
            elif file_path.suffix == '.html':
                self._parse_html_file(file_path, doc, "meraki")
                
        return doc if doc.endpoints else None
    
    def _parse_json_file(self, file_path: Path, doc: APIDocumentation, platform: str):
        """Parse JSON API documentation file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Handle OpenAPI/Swagger format
            if 'openapi' in data or 'swagger' in data:
                self._parse_openapi(data, doc)
            # Handle custom JSON format
            else:
                self._parse_custom_json(data, doc, platform)
                
        except Exception as e:
            print(f"Error parsing JSON file {file_path}: {e}")
    
    def _parse_yaml_file(self, file_path: Path, doc: APIDocumentation, platform: str):
        """Parse YAML API documentation file"""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
                
            # Handle OpenAPI/Swagger format
            if 'openapi' in data or 'swagger' in data:
                self._parse_openapi(data, doc)
            # Handle custom YAML format
            else:
                self._parse_custom_yaml(data, doc, platform)
                
        except Exception as e:
            print(f"Error parsing YAML file {file_path}: {e}")
    
    def _parse_openapi(self, data: Dict[str, Any], doc: APIDocumentation):
        """Parse OpenAPI/Swagger specification"""
        # Extract base information
        if 'info' in data:
            doc.name = data['info'].get('title', doc.name)
            doc.version = data['info'].get('version', doc.version)
            
        # Extract servers/base URL
        if 'servers' in data and data['servers']:
            doc.base_url = data['servers'][0].get('url', doc.base_url)
        elif 'host' in data:
            scheme = data.get('schemes', ['https'])[0]
            doc.base_url = f"{scheme}://{data['host']}{data.get('basePath', '')}"
            
        # Extract security schemes
        if 'components' in data and 'securitySchemes' in data['components']:
            self._extract_auth_from_openapi(data['components']['securitySchemes'], doc)
            
        # Extract endpoints
        if 'paths' in data:
            for path, path_data in data['paths'].items():
                for method, operation in path_data.items():
                    if method.upper() in [m.value for m in APIMethod]:
                        endpoint = self._create_endpoint_from_openapi(
                            path, method.upper(), operation
                        )
                        doc.endpoints.append(endpoint)
    
    def _create_endpoint_from_openapi(self, path: str, method: str, operation: Dict) -> APIEndpoint:
        """Create APIEndpoint from OpenAPI operation"""
        endpoint = APIEndpoint(
            path=path,
            method=APIMethod(method),
            description=operation.get('summary', operation.get('description', '')),
            tags=operation.get('tags', [])
        )
        
        # Extract parameters
        if 'parameters' in operation:
            for param in operation['parameters']:
                api_param = APIParameter(
                    name=param.get('name', ''),
                    type=param.get('schema', {}).get('type', 'string'),
                    required=param.get('required', False),
                    description=param.get('description', ''),
                    default=param.get('default'),
                    example=param.get('example')
                )
                endpoint.parameters.append(api_param)
                
        # Extract request body
        if 'requestBody' in operation:
            endpoint.request_body = operation['requestBody']
            
        # Extract response schema
        if 'responses' in operation and '200' in operation['responses']:
            endpoint.response_schema = operation['responses']['200']
            
        return endpoint
    
    def _parse_markdown_file(self, file_path: Path, doc: APIDocumentation, platform: str):
        """Parse Markdown API documentation"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Convert markdown to HTML for easier parsing
            html = markdown.markdown(content, extensions=['tables', 'fenced_code'])
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract API endpoints from code blocks or tables
            self._extract_endpoints_from_markdown(soup, doc, platform)
            
        except Exception as e:
            print(f"Error parsing Markdown file {file_path}: {e}")
    
    def _extract_endpoints_from_markdown(self, soup: BeautifulSoup, doc: APIDocumentation, platform: str):
        """Extract API endpoint information from parsed Markdown"""
        # Look for code blocks with API examples
        for code_block in soup.find_all('code'):
            text = code_block.get_text()
            
            # Check for HTTP method and path patterns
            patterns = self.fortinet_patterns if platform == "fortinet" else self.meraki_patterns
            method_match = re.search(patterns['method'], text)
            endpoint_match = re.search(patterns['endpoint'], text)
            
            if method_match and endpoint_match:
                # Try to find associated description
                parent = code_block.find_parent(['p', 'div', 'section'])
                description = parent.get_text() if parent else ""
                
                endpoint = APIEndpoint(
                    path=endpoint_match.group(),
                    method=APIMethod(method_match.group()),
                    description=description[:200]  # Limit description length
                )
                doc.endpoints.append(endpoint)
    
    def generate_api_client(self, api_doc: APIDocumentation, language: str = "python") -> str:
        """Generate API client code for the parsed documentation"""
        if language == "python":
            return self._generate_python_client(api_doc)
        elif language == "go":
            return self._generate_go_client(api_doc)
        elif language == "javascript":
            return self._generate_javascript_client(api_doc)
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    def _generate_python_client(self, api_doc: APIDocumentation) -> str:
        """Generate Python API client code"""
        client_code = f'''"""
{api_doc.name} API Client
Version: {api_doc.version}
Auto-generated from API documentation
"""

import requests
from typing import Dict, Any, Optional
from urllib.parse import urljoin


class {api_doc.name.replace(" ", "")}Client:
    """API Client for {api_doc.name}"""
    
    def __init__(self, base_url: str = "{api_doc.base_url}", api_key: str = None):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Set up authentication
        if api_key:
            if "{api_doc.authentication_type}" == "Bearer Token":
                self.session.headers["Authorization"] = f"Bearer {{api_key}}"
            elif "{api_doc.authentication_type}" == "API Key":
                self.session.headers["X-Cisco-Meraki-API-Key"] = api_key
        
        # Set default headers
        self.session.headers.update({{
            "Content-Type": "application/json",
            "Accept": "application/json"
        }})
'''
        
        # Generate methods for each endpoint
        for endpoint in api_doc.endpoints:
            method_name = self._generate_method_name(endpoint.path)
            client_code += self._generate_python_method(endpoint, method_name)
            
        return client_code
    
    def _generate_method_name(self, path: str) -> str:
        """Generate a Python method name from API path"""
        # Remove parameters and clean up path
        clean_path = re.sub(r'\{[^}]+\}', '', path)
        parts = [p for p in clean_path.split('/') if p and p != 'api' and not p.startswith('v')]
        return '_'.join(parts).lower()
    
    def _generate_python_method(self, endpoint: APIEndpoint, method_name: str) -> str:
        """Generate a Python method for an API endpoint"""
        # Build parameter list
        params = []
        for param in endpoint.parameters:
            if param.required:
                params.append(f"{param.name}: {self._python_type(param.type)}")
            else:
                params.append(f"{param.name}: Optional[{self._python_type(param.type)}] = None")
        
        params_str = ", ".join(params) if params else ""
        if params_str:
            params_str = ", " + params_str
            
        method_code = f'''
    def {method_name}(self{params_str}) -> Dict[str, Any]:
        """
        {endpoint.description}
        
        Endpoint: {endpoint.method.value} {endpoint.path}
        """
        url = urljoin(self.base_url, "{endpoint.path}")
        
'''
        
        # Add parameter handling
        if endpoint.parameters:
            method_code += "        params = {}\n"
            for param in endpoint.parameters:
                if param.required:
                    method_code += f'        params["{param.name}"] = {param.name}\n'
                else:
                    method_code += f'        if {param.name} is not None:\n'
                    method_code += f'            params["{param.name}"] = {param.name}\n'
                    
        # Add request execution
        if endpoint.method in [APIMethod.GET, APIMethod.DELETE]:
            method_code += f'        response = self.session.{endpoint.method.value.lower()}(url'
            if endpoint.parameters:
                method_code += ', params=params'
            method_code += ')\n'
        else:
            method_code += f'        response = self.session.{endpoint.method.value.lower()}(url'
            if endpoint.parameters:
                method_code += ', params=params'
            if endpoint.request_body:
                method_code += ', json=data'
            method_code += ')\n'
            
        method_code += '''        response.raise_for_status()
        return response.json()
'''
        
        return method_code
    
    def _python_type(self, api_type: str) -> str:
        """Convert API type to Python type"""
        type_mapping = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "list",
            "object": "dict"
        }
        return type_mapping.get(api_type, "Any")
    
    def compare_apis(self, fortinet_doc: APIDocumentation, meraki_doc: APIDocumentation) -> Dict[str, Any]:
        """Compare Fortinet and Meraki API capabilities"""
        comparison = {
            "summary": {
                "fortinet_endpoints": len(fortinet_doc.endpoints),
                "meraki_endpoints": len(meraki_doc.endpoints),
                "fortinet_auth": fortinet_doc.authentication_type,
                "meraki_auth": meraki_doc.authentication_type
            },
            "common_operations": [],
            "unique_to_fortinet": [],
            "unique_to_meraki": [],
            "feature_comparison": {}
        }
        
        # Extract operation categories
        fortinet_ops = self._categorize_operations(fortinet_doc.endpoints)
        meraki_ops = self._categorize_operations(meraki_doc.endpoints)
        
        # Find common and unique operations
        all_categories = set(fortinet_ops.keys()) | set(meraki_ops.keys())
        
        for category in all_categories:
            if category in fortinet_ops and category in meraki_ops:
                comparison["common_operations"].append(category)
                comparison["feature_comparison"][category] = {
                    "fortinet": len(fortinet_ops[category]),
                    "meraki": len(meraki_ops[category])
                }
            elif category in fortinet_ops:
                comparison["unique_to_fortinet"].append(category)
            else:
                comparison["unique_to_meraki"].append(category)
                
        return comparison
    
    def _categorize_operations(self, endpoints: List[APIEndpoint]) -> Dict[str, List[APIEndpoint]]:
        """Categorize endpoints by operation type"""
        categories = {}
        
        # Common network operation patterns
        category_patterns = {
            "firewall": r"(firewall|policy|rule|acl)",
            "vlan": r"(vlan|subnet|network)",
            "vpn": r"(vpn|ipsec|tunnel)",
            "routing": r"(route|routing|bgp|ospf)",
            "device": r"(device|appliance|system)",
            "monitoring": r"(monitor|metric|stat|traffic)",
            "configuration": r"(config|setting|backup)",
            "user": r"(user|admin|authentication)"
        }
        
        for endpoint in endpoints:
            path_lower = endpoint.path.lower()
            categorized = False
            
            for category, pattern in category_patterns.items():
                if re.search(pattern, path_lower):
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(endpoint)
                    categorized = True
                    break
                    
            if not categorized:
                if "other" not in categories:
                    categories["other"] = []
                categories["other"].append(endpoint)
                
        return categories


# Example usage functions
def parse_network_apis(doc_path: str, output_format: str = "summary"):
    """Main function to parse network API documentation"""
    parser = NetworkAPIParser(doc_path)
    
    # Parse both platforms
    apis = parser.parse_documentation("both")
    
    if output_format == "summary":
        return generate_summary(apis)
    elif output_format == "client":
        return generate_clients(parser, apis)
    elif output_format == "comparison":
        return generate_comparison(parser, apis)
    else:
        return apis


def generate_summary(apis: Dict[str, APIDocumentation]) -> str:
    """Generate a summary of parsed APIs"""
    summary = "# Network API Documentation Summary\n\n"
    
    for platform, api_doc in apis.items():
        summary += f"## {api_doc.name}\n"
        summary += f"- Version: {api_doc.version}\n"
        summary += f"- Base URL: {api_doc.base_url}\n"
        summary += f"- Authentication: {api_doc.authentication_type}\n"
        summary += f"- Total Endpoints: {len(api_doc.endpoints)}\n\n"
        
        # Group endpoints by method
        by_method = {}
        for endpoint in api_doc.endpoints:
            method = endpoint.method.value
            if method not in by_method:
                by_method[method] = []
            by_method[method].append(endpoint)
            
        summary += "### Endpoints by Method:\n"
        for method, endpoints in sorted(by_method.items()):
            summary += f"- {method}: {len(endpoints)} endpoints\n"
            
        summary += "\n"
        
    return summary


def generate_clients(parser: NetworkAPIParser, apis: Dict[str, APIDocumentation]) -> Dict[str, str]:
    """Generate API clients for each platform"""
    clients = {}
    
    for platform, api_doc in apis.items():
        clients[f"{platform}_python"] = parser.generate_api_client(api_doc, "python")
        
    return clients


def generate_comparison(parser: NetworkAPIParser, apis: Dict[str, APIDocumentation]) -> Dict[str, Any]:
    """Generate API comparison"""
    if "fortinet" in apis and "meraki" in apis:
        return parser.compare_apis(apis["fortinet"], apis["meraki"])
    else:
        return {"error": "Both Fortinet and Meraki APIs must be present for comparison"}


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python network_api_parser.py <documentation_path> [output_format]")
        sys.exit(1)
        
    doc_path = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "summary"
    
    result = parse_network_apis(doc_path, output_format)
    print(json.dumps(result, indent=2) if isinstance(result, dict) else result)