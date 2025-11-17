"""
Comprehensive SDK Generator with Real API Documentation
Generates complete SDKs using actual API endpoint data from Fortinet and Meraki
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import re


@dataclass
class SDKMethod:
    """Represents a method in the generated SDK"""
    name: str
    endpoint: str
    http_method: str
    description: str
    parameters: List[str]
    category: str
    examples: List[Dict[str, Any]]
    return_type: str = "Dict[str, Any]"


class ComprehensiveSDKGenerator:
    """Generates comprehensive SDKs from real API documentation"""
    
    def __init__(self, api_directory: str = "./api"):
        self.api_dir = Path(api_directory)
    
    def generate_fortinet_sdk(self, output_file: str = "fortinet_comprehensive_sdk.py") -> str:
        """Generate comprehensive Fortinet SDK"""
        # Load Fortinet API endpoints
        endpoints_file = self.api_dir / "fortimanager_api_endpoints.json"
        
        if not endpoints_file.exists():
            raise FileNotFoundError(f"Fortinet endpoints file not found: {endpoints_file}")
        
        with open(endpoints_file, 'r') as f:
            api_data = json.load(f)
        
        # Generate SDK
        sdk_code = self._generate_fortinet_sdk_code(api_data)
        
        # Save to file
        with open(output_file, 'w') as f:
            f.write(sdk_code)
        
        return sdk_code
    
    def generate_meraki_sdk(self, output_file: str = "meraki_comprehensive_sdk.py") -> str:
        """Generate comprehensive Meraki SDK"""
        # Load Meraki API from Postman collection
        postman_file = self.api_dir / "Meraki Dashboard API - v1.63.0.postman_collection.json"
        
        if not postman_file.exists():
            raise FileNotFoundError(f"Meraki Postman collection not found: {postman_file}")
        
        with open(postman_file, 'r') as f:
            collection = json.load(f)
        
        # Parse Postman collection and generate SDK
        sdk_code = self._generate_meraki_sdk_code(collection)
        
        # Save to file
        with open(output_file, 'w') as f:
            f.write(sdk_code)
        
        return sdk_code
    
    def _generate_fortinet_sdk_code(self, api_data: Dict[str, Any]) -> str:
        """Generate Fortinet SDK code from API data"""
        
        # Extract metadata
        total_endpoints = api_data.get("total_endpoints", 0)
        categories = api_data.get("categories", [])
        extraction_date = api_data.get("extraction_date", "")
        
        # Start building SDK
        sdk_code = f'''"""
Comprehensive Fortinet FortiManager API SDK
Auto-generated from real API documentation

Total Endpoints: {total_endpoints}
Categories: {len(categories)}
Generated: {extraction_date}
Source: FortiManager API Documentation
"""

import json
import requests
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Standard API response wrapper"""
    success: bool
    data: Any
    error: str = ""
    status_code: int = 200
    raw_response: Dict = None


class FortiManagerAPIException(Exception):
    """Custom exception for FortiManager API errors"""
    pass


class FortiManagerComprehensiveSDK:
    """
    Comprehensive FortiManager API SDK with {total_endpoints} real endpoints
    
    Authentication: Session-based (JSON-RPC)
    Base URL: https://your-fortimanager/jsonrpc
    """
    
    def __init__(self, host: str, username: str = None, password: str = None, 
                 verify_ssl: bool = True, timeout: int = 30):
        self.host = host.rstrip('/')
        self.base_url = f"{{self.host}}/jsonrpc"
        self.session = requests.Session()
        self.session_id = None
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        
        # Configure session
        self.session.verify = verify_ssl
        self.session.headers.update({{
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }})
        
        # Authentication
        if username and password:
            self.authenticate(username, password)
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with FortiManager using real API endpoint"""
        try:
            auth_data = {{
                "id": 1,
                "method": "exec",
                "params": [{{
                    "url": "/sys/login/user",
                    "data": {{
                        "user": username,
                        "passwd": password
                    }}
                }}]
            }}
            
            response = self.session.post(self.base_url, json=auth_data, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            if result.get("result", [{{}}])[0].get("status", {{}}).get("code") == 0:
                self.session_id = result["session"]
                logger.info("Authentication successful")
                return True
            else:
                logger.error("Authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {{e}}")
            return False
    
    def logout(self) -> bool:
        """Logout from FortiManager session"""
        if not self.session_id:
            return True
        
        try:
            logout_data = {{
                "id": 1,
                "method": "exec",
                "params": [{{
                    "url": "/sys/logout"
                }}],
                "session": self.session_id
            }}
            
            response = self.session.post(self.base_url, json=logout_data, timeout=self.timeout)
            self.session_id = None
            logger.info("Logout successful")
            return True
            
        except Exception as e:
            logger.error(f"Logout error: {{e}}")
            return False
    
    def _make_request(self, endpoint: str, method: str = "get", data: Dict = None, 
                     params: Dict = None) -> APIResponse:
        """Make API request with proper FortiManager JSON-RPC format"""
        if not self.session_id:
            raise FortiManagerAPIException("Not authenticated. Call authenticate() first.")
        
        request_data = {{
            "id": 1,
            "method": method,
            "params": [{{
                "url": endpoint
            }}],
            "session": self.session_id,
            "verbose": 1
        }}
        
        # Add data for POST/PUT requests
        if data and method in ["set", "add", "update"]:
            request_data["params"][0]["data"] = data
        
        # Add filters/parameters
        if params:
            request_data["params"][0].update(params)
        
        try:
            response = self.session.post(self.base_url, json=request_data, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            
            # Check for API errors
            if "error" in result:
                return APIResponse(
                    success=False,
                    data=None,
                    error=str(result["error"]),
                    raw_response=result
                )
            
            # Extract result data
            api_result = result.get("result", [])
            if api_result and isinstance(api_result, list):
                status = api_result[0].get("status", {{}})
                if status.get("code") == 0:
                    data = api_result[0].get("data", api_result[0])
                    return APIResponse(success=True, data=data, raw_response=result)
                else:
                    return APIResponse(
                        success=False,
                        data=None,
                        error=status.get("message", "API request failed"),
                        raw_response=result
                    )
            
            return APIResponse(success=True, data=result, raw_response=result)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {{e}}")
            return APIResponse(success=False, data=None, error=str(e))

    # ========================================
    # AUTO-GENERATED METHODS FROM REAL API
    # ========================================
'''
        
        # Generate methods for each category
        for category_data in categories:
            category_name = category_data.get("category", "")
            endpoints = category_data.get("endpoints", [])
            
            if not endpoints:
                continue
            
            # Add category comment
            sdk_code += f'''
    # {category_name} ({len(endpoints)} endpoints)
    # {'=' * (len(category_name) + 20)}
'''
            
            for endpoint_data in endpoints:
                method_code = self._generate_fortinet_method(endpoint_data)
                sdk_code += method_code
        
        # Add utility methods
        sdk_code += '''
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_system_status(self) -> APIResponse:
        """Get system status information"""
        return self._make_request("/sys/status")
    
    def get_ha_status(self) -> APIResponse:
        """Get High Availability status"""
        return self._make_request("/sys/ha/status")
    
    def backup_system(self, backup_name: str = None) -> APIResponse:
        """Create system backup"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return self._make_request("/sys/backup", "exec", {
            "filename": backup_name
        })
    
    def get_device_list(self, adom: str = "root") -> APIResponse:
        """Get list of managed devices"""
        return self._make_request(f"/dvmdb/adom/{adom}/device")
    
    def get_policy_packages(self, adom: str = "root") -> APIResponse:
        """Get policy packages for ADOM"""
        return self._make_request(f"/pm/pkg/adom/{adom}")


# Example usage and testing
def example_usage():
    """Example of how to use the SDK"""
    
    # Initialize SDK
    fmg = FortiManagerComprehensiveSDK(
        host="https://your-fortimanager.com",
        username="admin",
        password="password"
    )
    
    try:
        # Get system status
        status = fmg.get_system_status()
        if status.success:
            print("System Status:", status.data)
        
        # Get device list
        devices = fmg.get_device_list()
        if devices.success:
            print(f"Found {len(devices.data)} devices")
        
        # Get policy packages
        packages = fmg.get_policy_packages()
        if packages.success:
            print(f"Found {len(packages.data)} policy packages")
            
    finally:
        # Always logout
        fmg.logout()


if __name__ == "__main__":
    example_usage()
'''
        
        return sdk_code
    
    def _generate_fortinet_method(self, endpoint_data: Dict[str, Any]) -> str:
        """Generate a single method for Fortinet endpoint"""
        
        endpoint = endpoint_data.get("endpoint", "")
        method = endpoint_data.get("method", "POST")
        description = endpoint_data.get("description", "")
        parameters = endpoint_data.get("parameters", [])
        
        # Generate method name
        method_name = self._create_method_name(endpoint, description)
        
        # Determine if this is a read or write operation
        fmg_method = "get" if method == "GET" else "set"
        if "add" in description.lower() or "create" in description.lower():
            fmg_method = "add"
        elif "delete" in description.lower() or "remove" in description.lower():
            fmg_method = "delete"
        elif "update" in description.lower() or "modify" in description.lower():
            fmg_method = "update"
        
        # Build method signature
        method_params = ["self"]
        if any("adom" in p.lower() for p in parameters):
            method_params.append('adom: str = "root"')
        if fmg_method in ["set", "add", "update"]:
            method_params.append("data: Dict[str, Any]")
        method_params.append("**kwargs")
        
        method_signature = f"def {method_name}({', '.join(method_params)}) -> APIResponse:"
        
        # Build docstring
        param_docs = []
        for param in parameters:
            param_docs.append(f"        {param}")
        
        docstring = f'''        """
        {description}
        
        Endpoint: {method} {endpoint}
        Parameters:
{chr(10).join(param_docs) if param_docs else "        None"}
        
        Returns:
            APIResponse: Response with success status and data
        """'''
        
        # Build method body
        method_body = f'''        return self._make_request("{endpoint}", "{fmg_method}"'''
        if fmg_method in ["set", "add", "update"]:
            method_body += ", data"
        method_body += ", kwargs)"
        
        return f'''
    {method_signature}
{docstring}
{method_body}
'''
    
    def _create_method_name(self, endpoint: str, description: str) -> str:
        """Create a valid Python method name from endpoint and description"""
        
        # Start with endpoint
        name_parts = []
        
        # Extract meaningful parts from endpoint
        endpoint_parts = [p for p in endpoint.split('/') if p and not p.startswith('{')]
        
        # Remove common prefixes
        filtered_parts = []
        for part in endpoint_parts:
            if part not in ['api', 'v1', 'v2', 'sys', 'pm', 'dvmdb', 'monitor']:
                filtered_parts.append(part)
        
        if not filtered_parts:
            filtered_parts = endpoint_parts[-2:] if len(endpoint_parts) >= 2 else endpoint_parts
        
        # Use description to determine action
        action = "get"
        desc_lower = description.lower()
        if any(word in desc_lower for word in ["create", "add", "new"]):
            action = "create"
        elif any(word in desc_lower for word in ["update", "modify", "edit", "set"]):
            action = "update"
        elif any(word in desc_lower for word in ["delete", "remove"]):
            action = "delete"
        elif any(word in desc_lower for word in ["list", "get", "retrieve"]):
            action = "get"
        
        # Build method name
        if filtered_parts:
            resource = '_'.join(filtered_parts)
            method_name = f"{action}_{resource}"
        else:
            # Fallback to description
            clean_desc = re.sub(r'[^a-zA-Z0-9\s]', '', description)
            desc_words = clean_desc.lower().split()[:3]
            method_name = '_'.join([action] + desc_words)
        
        # Clean up method name
        method_name = re.sub(r'[^a-zA-Z0-9_]', '_', method_name)
        method_name = re.sub(r'_+', '_', method_name)
        method_name = method_name.strip('_')
        
        # Ensure it starts with a letter
        if method_name and method_name[0].isdigit():
            method_name = f"endpoint_{method_name}"
        
        return method_name or "unknown_endpoint"


# Example usage
if __name__ == "__main__":
    generator = ComprehensiveSDKGenerator()
    
    try:
        print("Generating Fortinet SDK...")
        fortinet_sdk = generator.generate_fortinet_sdk()
        print(f"Generated Fortinet SDK: {len(fortinet_sdk)} characters")
        
        print("Generating Meraki SDK...")
        # meraki_sdk = generator.generate_meraki_sdk()
        # print(f"Generated Meraki SDK: {len(meraki_sdk)} characters")
        
    except Exception as e:
        print(f"Error generating SDKs: {e}")
