"""
Extended Network API Parser with additional format support
Adds PDF, RAML, GraphQL, and Postman collection parsing
"""

import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import PyPDF2
import ramlpy
from graphql import build_schema, parse
from dataclasses import dataclass, field
from network_api_parser import (
    APIDocumentation, APIEndpoint, APIParameter, 
    APIMethod, NetworkAPIParser
)


class ExtendedNetworkAPIParser(NetworkAPIParser):
    """Extended parser with support for additional formats"""
    
    def __init__(self, documentation_path: str):
        super().__init__(documentation_path)
        self.supported_formats = {
            'pdf': self._parse_pdf_file,
            'raml': self._parse_raml_file,
            'graphql': self._parse_graphql_file,
            'gql': self._parse_graphql_file,
            'postman': self._parse_postman_collection,
            'har': self._parse_har_file,
            'curl': self._parse_curl_commands,
            'wadl': self._parse_wadl_file
        }
    
    def parse_documentation(self, platform: str = "both") -> Dict[str, APIDocumentation]:
        """Extended parse method with additional format support"""
        # First use parent class parsing
        results = super().parse_documentation(platform)
        
        # Then parse additional formats
        self._parse_extended_formats(results, platform)
        
        return results
    
    def _parse_extended_formats(self, results: Dict[str, APIDocumentation], platform: str):
        """Parse additional documentation formats"""
        # Look for files with extended formats
        for ext, parser_func in self.supported_formats.items():
            pattern = f"**/*.{ext}"
            files = list(self.doc_path.glob(pattern))
            
            for file_path in files:
                # Determine platform from file path or name
                file_platform = self._determine_platform(file_path)
                
                if platform != "both" and file_platform != platform:
                    continue
                
                # Parse the file
                try:
                    if file_platform not in results:
                        results[file_platform] = self._create_default_doc(file_platform)
                    
                    parser_func(file_path, results[file_platform], file_platform)
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
    
    def _parse_pdf_file(self, file_path: Path, doc: APIDocumentation, platform: str):
        """Parse API documentation from PDF files"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                # Extract text from all pages
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
                
                # Parse API endpoints from text
                self._extract_apis_from_text(text, doc, platform)
                
        except Exception as e:
            print(f"Error parsing PDF {file_path}: {e}")
    
    def _extract_apis_from_text(self, text: str, doc: APIDocumentation, platform: str):
        """Extract API information from unstructured text"""
        # Common API patterns
        endpoint_patterns = [
            r'(GET|POST|PUT|DELETE|PATCH)\s+(/api/[^\s]+)',
            r'Endpoint:\s*([A-Z]+)\s+([^\s]+)',
            r'URL:\s*([A-Z]+)\s+([^\s]+)',
            r'Method:\s*([A-Z]+).*?Path:\s*([^\s]+)',
        ]
        
        for pattern in endpoint_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                method, path = match
                
                # Skip if not a valid method
                if method.upper() not in [m.value for m in APIMethod]:
                    continue
                
                # Extract description (look for text before/after endpoint)
                desc_pattern = rf'{re.escape(path)}[:\s]+([^.\n]+)'
                desc_match = re.search(desc_pattern, text)
                description = desc_match.group(1) if desc_match else "Extracted endpoint"
                
                endpoint = APIEndpoint(
                    path=path,
                    method=APIMethod(method.upper()),
                    description=description.strip()
                )
                
                # Try to extract parameters
                self._extract_parameters_from_text(text, endpoint, path)
                
                doc.endpoints.append(endpoint)
    
    def _extract_parameters_from_text(self, text: str, endpoint: APIEndpoint, path: str):
        """Extract parameters from text around endpoint definition"""
        # Look for parameter definitions near the endpoint
        param_patterns = [
            r'Parameters?:\s*\n((?:[-*]\s*[^:\n]+:[^\n]+\n?)+)',
            r'Query Parameters?:\s*\n((?:[-*]\s*[^:\n]+:[^\n]+\n?)+)',
            r'Request Body:\s*\n((?:[-*]\s*[^:\n]+:[^\n]+\n?)+)',
        ]
        
        # Search within 500 characters of endpoint mention
        endpoint_pos = text.find(path)
        if endpoint_pos != -1:
            context = text[max(0, endpoint_pos-500):endpoint_pos+500]
            
            for pattern in param_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    param_text = match.group(1)
                    self._parse_parameter_list(param_text, endpoint)
    
    def _parse_parameter_list(self, param_text: str, endpoint: APIEndpoint):
        """Parse parameter list from text"""
        # Parse bullet points or similar
        param_lines = param_text.split('\n')
        
        for line in param_lines:
            # Remove bullet points
            line = re.sub(r'^[-*]\s*', '', line.strip())
            
            # Try to extract parameter info
            # Format: name: type - description (required)
            param_match = re.match(r'(\w+):\s*(\w+)(?:\s*-\s*(.+?))?(?:\s*\((required|optional)\))?$', line)
            
            if param_match:
                name, param_type, description, required = param_match.groups()
                
                param = APIParameter(
                    name=name,
                    type=param_type or "string",
                    required=required == "required" if required else False,
                    description=description or ""
                )
                endpoint.parameters.append(param)
    
    def _parse_raml_file(self, file_path: Path, doc: APIDocumentation, platform: str):
        """Parse RAML (RESTful API Modeling Language) files"""
        try:
            with open(file_path, 'r') as f:
                raml_content = f.read()
            
            # Parse RAML
            raml_data = ramlpy.parse(raml_content)
            
            # Extract base information
            if 'title' in raml_data:
                doc.name = raml_data['title']
            if 'version' in raml_data:
                doc.version = raml_data['version']
            if 'baseUri' in raml_data:
                doc.base_url = raml_data['baseUri']
            
            # Extract resources (endpoints)
            self._parse_raml_resources(raml_data, doc, "")
            
        except Exception as e:
            print(f"Error parsing RAML {file_path}: {e}")
    
    def _parse_raml_resources(self, raml_data: Dict, doc: APIDocumentation, parent_path: str):
        """Recursively parse RAML resources"""
        for key, value in raml_data.items():
            if key.startswith('/'):
                # This is a resource path
                full_path = parent_path + key
                
                # Parse methods for this resource
                for method in ['get', 'post', 'put', 'delete', 'patch']:
                    if method in value:
                        method_data = value[method]
                        
                        endpoint = APIEndpoint(
                            path=full_path,
                            method=APIMethod(method.upper()),
                            description=method_data.get('description', '')
                        )
                        
                        # Parse parameters
                        if 'queryParameters' in method_data:
                            for param_name, param_data in method_data['queryParameters'].items():
                                param = APIParameter(
                                    name=param_name,
                                    type=param_data.get('type', 'string'),
                                    required=param_data.get('required', False),
                                    description=param_data.get('description', '')
                                )
                                endpoint.parameters.append(param)
                        
                        doc.endpoints.append(endpoint)
                
                # Recursively parse nested resources
                self._parse_raml_resources(value, doc, full_path)
    
    def _parse_graphql_file(self, file_path: Path, doc: APIDocumentation, platform: str):
        """Parse GraphQL schema files"""
        try:
            with open(file_path, 'r') as f:
                schema_content = f.read()
            
            # Build GraphQL schema
            schema = build_schema(schema_content)
            
            # Convert GraphQL to REST-like endpoints
            doc.name = f"{platform.title()} GraphQL API"
            doc.authentication_type = "GraphQL Token"
            
            # Extract queries
            query_type = schema.query_type
            if query_type:
                for field_name, field in query_type.fields.items():
                    endpoint = APIEndpoint(
                        path=f"/graphql?query={field_name}",
                        method=APIMethod.POST,
                        description=field.description or f"GraphQL query: {field_name}"
                    )
                    
                    # Add parameters from field arguments
                    for arg_name, arg in field.args.items():
                        param = APIParameter(
                            name=arg_name,
                            type=str(arg.type),
                            required=arg.type.is_non_null,
                            description=arg.description or ""
                        )
                        endpoint.parameters.append(param)
                    
                    doc.endpoints.append(endpoint)
            
            # Extract mutations
            mutation_type = schema.mutation_type
            if mutation_type:
                for field_name, field in mutation_type.fields.items():
                    endpoint = APIEndpoint(
                        path=f"/graphql?mutation={field_name}",
                        method=APIMethod.POST,
                        description=field.description or f"GraphQL mutation: {field_name}"
                    )
                    
                    # Add parameters
                    for arg_name, arg in field.args.items():
                        param = APIParameter(
                            name=arg_name,
                            type=str(arg.type),
                            required=arg.type.is_non_null,
                            description=arg.description or ""
                        )
                        endpoint.parameters.append(param)
                    
                    doc.endpoints.append(endpoint)
                    
        except Exception as e:
            print(f"Error parsing GraphQL {file_path}: {e}")
    
    def _parse_postman_collection(self, file_path: Path, doc: APIDocumentation, platform: str):
        """Parse Postman collection files"""
        try:
            with open(file_path, 'r') as f:
                collection = json.load(f)
            
            # Extract collection info
            if 'info' in collection:
                doc.name = collection['info'].get('name', doc.name)
                doc.version = collection['info'].get('version', '1.0.0')
            
            # Parse items recursively
            if 'item' in collection:
                self._parse_postman_items(collection['item'], doc)
                
        except Exception as e:
            print(f"Error parsing Postman collection {file_path}: {e}")
    
    def _parse_postman_items(self, items: List[Dict], doc: APIDocumentation, folder_path: str = ""):
        """Recursively parse Postman collection items"""
        for item in items:
            if 'item' in item:
                # This is a folder, recurse
                folder_name = item.get('name', '')
                self._parse_postman_items(item['item'], doc, f"{folder_path}/{folder_name}")
            elif 'request' in item:
                # This is a request
                request = item['request']
                
                # Extract method and URL
                method = request.get('method', 'GET')
                url_data = request.get('url', {})
                
                if isinstance(url_data, str):
                    path = url_data
                else:
                    # Build path from URL components
                    raw = url_data.get('raw', '')
                    # Extract path from full URL
                    path_match = re.search(r'https?://[^/]+(/.*?)(?:\?|$)', raw)
                    path = path_match.group(1) if path_match else raw
                
                endpoint = APIEndpoint(
                    path=path,
                    method=APIMethod(method),
                    description=item.get('name', 'Postman request')
                )
                
                # Extract query parameters
                if isinstance(url_data, dict) and 'query' in url_data:
                    for param in url_data['query']:
                        api_param = APIParameter(
                            name=param.get('key', ''),
                            type='string',
                            required=not param.get('disabled', False),
                            description=param.get('description', ''),
                            default=param.get('value', '')
                        )
                        endpoint.parameters.append(api_param)
                
                # Extract headers
                if 'header' in request:
                    for header in request['header']:
                        if header.get('key', '').lower() in ['authorization', 'x-api-key']:
                            doc.authentication_type = f"Header: {header['key']}"
                
                doc.endpoints.append(endpoint)
    
    def _parse_har_file(self, file_path: Path, doc: APIDocumentation, platform: str):
        """Parse HAR (HTTP Archive) files"""
        try:
            with open(file_path, 'r') as f:
                har_data = json.load(f)
            
            entries = har_data.get('log', {}).get('entries', [])
            
            for entry in entries:
                request = entry.get('request', {})
                
                # Extract method and URL
                method = request.get('method', 'GET')
                url = request.get('url', '')
                
                # Parse URL to get path
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                path = parsed_url.path
                
                # Skip non-API requests
                if not path.startswith('/api'):
                    continue
                
                endpoint = APIEndpoint(
                    path=path,
                    method=APIMethod(method),
                    description=f"Captured from HAR: {path}"
                )
                
                # Extract query parameters
                for param in request.get('queryString', []):
                    api_param = APIParameter(
                        name=param.get('name', ''),
                        type='string',
                        required=True,
                        description='',
                        default=param.get('value', '')
                    )
                    endpoint.parameters.append(api_param)
                
                doc.endpoints.append(endpoint)
                
        except Exception as e:
            print(f"Error parsing HAR file {file_path}: {e}")
    
    def _parse_curl_commands(self, file_path: Path, doc: APIDocumentation, platform: str):
        """Parse files containing curl commands"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find all curl commands
            curl_pattern = r'curl\s+[^;]+(?:;|$)'
            curl_commands = re.findall(curl_pattern, content, re.MULTILINE)
            
            for cmd in curl_commands:
                endpoint = self._parse_single_curl(cmd)
                if endpoint:
                    doc.endpoints.append(endpoint)
                    
        except Exception as e:
            print(f"Error parsing curl commands {file_path}: {e}")
    
    def _parse_single_curl(self, curl_cmd: str) -> Optional[APIEndpoint]:
        """Parse a single curl command"""
        # Extract method
        method_match = re.search(r'-X\s+([A-Z]+)', curl_cmd)
        method = method_match.group(1) if method_match else 'GET'
        
        # Extract URL
        url_match = re.search(r'(?:curl\s+|")(https?://[^"\s]+)', curl_cmd)
        if not url_match:
            return None
            
        url = url_match.group(1)
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        
        endpoint = APIEndpoint(
            path=parsed_url.path,
            method=APIMethod(method),
            description=f"Extracted from curl command"
        )
        
        # Extract headers for auth info
        header_matches = re.findall(r'-H\s+["\']([^"\']+)["\']', curl_cmd)
        for header in header_matches:
            if 'authorization' in header.lower() or 'api-key' in header.lower():
                endpoint.authentication_required = True
        
        return endpoint
    
    def _parse_wadl_file(self, file_path: Path, doc: APIDocumentation, platform: str):
        """Parse WADL (Web Application Description Language) files"""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # WADL namespace
            ns = {'wadl': 'http://wadl.dev.java.net/2009/02'}
            
            # Extract base URL
            resources = root.find('.//wadl:resources', ns)
            if resources is not None:
                doc.base_url = resources.get('base', doc.base_url)
            
            # Extract all resources
            for resource in root.findall('.//wadl:resource', ns):
                self._parse_wadl_resource(resource, doc, "", ns)
                
        except Exception as e:
            print(f"Error parsing WADL {file_path}: {e}")
    
    def _parse_wadl_resource(self, resource, doc: APIDocumentation, parent_path: str, ns: Dict):
        """Parse WADL resource element"""
        path = resource.get('path', '')
        full_path = parent_path + '/' + path if path else parent_path
        
        # Parse methods
        for method in resource.findall('wadl:method', ns):
            method_name = method.get('name', 'GET')
            
            endpoint = APIEndpoint(
                path=full_path,
                method=APIMethod(method_name),
                description=method.get('id', '')
            )
            
            # Parse request parameters
            request = method.find('wadl:request', ns)
            if request is not None:
                for param in request.findall('wadl:param', ns):
                    api_param = APIParameter(
                        name=param.get('name', ''),
                        type=param.get('type', 'string').split(':')[-1],
                        required=param.get('required', 'false') == 'true',
                        description=param.get('doc', '')
                    )
                    endpoint.parameters.append(api_param)
            
            doc.endpoints.append(endpoint)
        
        # Recursively parse child resources
        for child_resource in resource.findall('wadl:resource', ns):
            self._parse_wadl_resource(child_resource, doc, full_path, ns)
    
    def _determine_platform(self, file_path: Path) -> str:
        """Determine platform from file path or name"""
        path_str = str(file_path).lower()
        
        if any(term in path_str for term in ['fortinet', 'forti', 'fortigate']):
            return 'fortinet'
        elif any(term in path_str for term in ['meraki', 'cisco', 'dashboard']):
            return 'meraki'
        else:
            # Default to fortinet if unclear
            return 'fortinet'
    
    def _create_default_doc(self, platform: str) -> APIDocumentation:
        """Create default documentation object for platform"""
        if platform == 'fortinet':
            return APIDocumentation(
                name="Fortinet API",
                version="7.0",
                base_url="https://fortigate.example.com",
                authentication_type="Bearer Token"
            )
        else:
            return APIDocumentation(
                name="Meraki Dashboard API",
                version="1.0",
                base_url="https://api.meraki.com/api/v1",
                authentication_type="API Key"
            )


# Additional format converters
class APIFormatConverter:
    """Convert between different API documentation formats"""
    
    @staticmethod
    def to_openapi(api_doc: APIDocumentation) -> Dict[str, Any]:
        """Convert APIDocumentation to OpenAPI 3.0 format"""
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": api_doc.name,
                "version": api_doc.version
            },
            "servers": [
                {"url": api_doc.base_url}
            ],
            "paths": {},
            "components": {
                "securitySchemes": {}
            }
        }
        
        # Add security scheme
        if api_doc.authentication_type == "Bearer Token":
            openapi["components"]["securitySchemes"]["bearerAuth"] = {
                "type": "http",
                "scheme": "bearer"
            }
        elif api_doc.authentication_type == "API Key":
            openapi["components"]["securitySchemes"]["apiKey"] = {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        
        # Convert endpoints
        for endpoint in api_doc.endpoints:
            path = endpoint.path
            if path not in openapi["paths"]:
                openapi["paths"][path] = {}
            
            operation = {
                "summary": endpoint.description,
                "parameters": [],
                "responses": {
                    "200": {
                        "description": "Successful response"
                    }
                }
            }
            
            # Add parameters
            for param in endpoint.parameters:
                operation["parameters"].append({
                    "name": param.name,
                    "in": "query",
                    "required": param.required,
                    "schema": {
                        "type": param.type
                    },
                    "description": param.description
                })
            
            openapi["paths"][path][endpoint.method.value.lower()] = operation
        
        return openapi
    
    @staticmethod
    def to_postman(api_doc: APIDocumentation) -> Dict[str, Any]:
        """Convert APIDocumentation to Postman Collection format"""
        collection = {
            "info": {
                "name": api_doc.name,
                "version": api_doc.version,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }
        
        # Group endpoints by path prefix
        groups = {}
        for endpoint in api_doc.endpoints:
            # Get first path segment as group
            parts = endpoint.path.strip('/').split('/')
            group = parts[0] if parts else 'root'
            
            if group not in groups:
                groups[group] = []
            groups[group].append(endpoint)
        
        # Create Postman items
        for group_name, endpoints in groups.items():
            group_item = {
                "name": group_name,
                "item": []
            }
            
            for endpoint in endpoints:
                request_item = {
                    "name": endpoint.description or endpoint.path,
                    "request": {
                        "method": endpoint.method.value,
                        "url": {
                            "raw": f"{api_doc.base_url}{endpoint.path}",
                            "host": [api_doc.base_url.replace('https://', '').replace('http://', '')],
                            "path": endpoint.path.strip('/').split('/'),
                            "query": []
                        },
                        "header": []
                    }
                }
                
                # Add authentication header
                if api_doc.authentication_type == "Bearer Token":
                    request_item["request"]["header"].append({
                        "key": "Authorization",
                        "value": "Bearer {{token}}",
                        "type": "text"
                    })
                elif api_doc.authentication_type == "API Key":
                    request_item["request"]["header"].append({
                        "key": "X-API-Key",
                        "value": "{{apiKey}}",
                        "type": "text"
                    })
                
                # Add query parameters
                for param in endpoint.parameters:
                    request_item["request"]["url"]["query"].append({
                        "key": param.name,
                        "value": param.default if param.default else "",
                        "description": param.description,
                        "disabled": not param.required
                    })
                
                group_item["item"].append(request_item)
            
            collection["item"].append(group_item)
        
        return collection
    
    @staticmethod
    def to_raml(api_doc: APIDocumentation) -> str:
        """Convert APIDocumentation to RAML format"""
        raml = f"""#%RAML 1.0
title: {api_doc.name}
version: {api_doc.version}
baseUri: {api_doc.base_url}
"""
        
        # Add security schemes
        if api_doc.authentication_type:
            raml += f"""
securitySchemes:
  {api_doc.authentication_type.lower().replace(' ', '_')}:
    type: x-custom
    description: {api_doc.authentication_type}
"""
        
        # Group endpoints by resource
        resources = {}
        for endpoint in api_doc.endpoints:
            # Extract resource path
            parts = endpoint.path.split('/')
            resource_path = '/'.join(parts[:-1]) if parts else '/'
            
            if resource_path not in resources:
                resources[resource_path] = []
            resources[resource_path].append(endpoint)
        
        # Generate RAML resources
        for resource_path, endpoints in resources.items():
            raml += f"\n{resource_path}:\n"
            
            for endpoint in endpoints:
                raml += f"  {endpoint.method.value.lower()}:\n"
                raml += f"    description: {endpoint.description}\n"
                
                if endpoint.parameters:
                    raml += "    queryParameters:\n"
                    for param in endpoint.parameters:
                        raml += f"      {param.name}:\n"
                        raml += f"        type: {param.type}\n"
                        raml += f"        required: {str(param.required).lower()}\n"
                        if param.description:
                            raml += f"        description: {param.description}\n"
        
        return raml