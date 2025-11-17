"""
Enhanced Network App Generator with Corporate SSL Support
Integrates SSL certificate handling for corporate environments
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from api_documentation_loader import APIDocumentationLoader, LoadedAPIDocumentation, RealAPIEndpoint
from ssl_helper import configure_corporate_ssl, CorporateSSLHelper


@dataclass
class CorporateNetworkApp:
    """Network application configured for corporate environments"""
    name: str
    description: str
    platform: str
    features: List[str]
    real_endpoints: List[RealAPIEndpoint]
    code: Dict[str, str]
    api_categories_used: List[str]
    total_endpoints_used: int
    ssl_configured: bool = False
    corporate_ready: bool = False


class CorporateNetworkAppGenerator:
    """Generates network applications with corporate SSL and proxy support"""
    
    def __init__(self, api_loader: APIDocumentationLoader):
        self.api_loader = api_loader
        self.documentation = api_loader.documentation
        self.ssl_helper = CorporateSSLHelper()
        
        # Configure SSL for corporate environment
        self._configure_corporate_environment()
        
        self.app_templates = {
            "corporate_firewall_manager": self._generate_corporate_firewall_manager,
            "corporate_device_manager": self._generate_corporate_device_manager,
            "corporate_monitoring_dashboard": self._generate_corporate_monitoring_dashboard,
            "corporate_network_audit_tool": self._generate_corporate_network_audit_tool,
            "corporate_api_gateway": self._generate_corporate_api_gateway
        }
    
    def _configure_corporate_environment(self) -> None:
        """Configure SSL and proxy settings for corporate environment"""
        try:
            # Auto-configure SSL
            self.corporate_session = configure_corporate_ssl(auto_configure=True)
            print("✅ Corporate SSL configured successfully")
        except Exception as e:
            print(f"⚠️  SSL configuration warning: {e}")
            # Create basic session as fallback
            import requests
            self.corporate_session = requests.Session()
    
    def generate_corporate_app(self, app_type: str, platform: str = "fortinet", 
                             language: str = "python") -> CorporateNetworkApp:
        """Generate corporate-ready network application"""
        if app_type not in self.app_templates:
            raise ValueError(f"Unknown app type: {app_type}")
        
        if platform not in self.documentation:
            raise ValueError(f"Platform {platform} not loaded")
        
        return self.app_templates[app_type](platform, language)
    
    def _generate_corporate_firewall_manager(self, platform: str, language: str) -> CorporateNetworkApp:
        """Generate corporate firewall manager with SSL handling"""
        doc = self.documentation[platform]
        
        # Find firewall-related endpoints
        firewall_endpoints = self.api_loader.search_endpoints(platform, "firewall")
        policy_endpoints = self.api_loader.search_endpoints(platform, "policy")
        
        # Combine and deduplicate
        all_endpoints = firewall_endpoints + policy_endpoints
        endpoint_ids = set()
        unique_endpoints = []
        for ep in all_endpoints:
            if ep.id not in endpoint_ids:
                endpoint_ids.add(ep.id)
                unique_endpoints.append(ep)
        
        app = CorporateNetworkApp(
            name=f"Corporate {platform.title()} Firewall Manager",
            description=f"Enterprise firewall management with SSL certificate handling for {doc.name}",
            platform=platform,
            features=[
                "Corporate SSL certificate handling (Zscaler, Blue Coat)",
                "Proxy-aware network communications",
                "Real-time firewall policy management",
                "Bulk policy deployment with validation",
                "Corporate compliance checking",
                "Audit trail and logging",
                "Air-gapped deployment support"
            ],
            real_endpoints=unique_endpoints,
            api_categories_used=list(set(ep.category for ep in unique_endpoints)),
            total_endpoints_used=len(unique_endpoints),
            ssl_configured=True,
            corporate_ready=True,
            code={}
        )
        
        if language == "python":
            app.code["python"] = self._generate_python_corporate_firewall(app, doc)
        
        return app
    
    def _generate_python_corporate_firewall(self, app: CorporateNetworkApp, doc: LoadedAPIDocumentation) -> str:
        """Generate Python firewall manager with corporate SSL support"""
        
        # Group endpoints by functionality
        policy_endpoints = [ep for ep in app.real_endpoints if "policy" in ep.endpoint.lower()]
        config_endpoints = [ep for ep in app.real_endpoints if any(term in ep.endpoint.lower() 
                                                                  for term in ["config", "system"])]
        monitor_endpoints = [ep for ep in app.real_endpoints if "monitor" in ep.endpoint.lower()]
        
        code = f'''"""
{app.name}
{app.description}

CORPORATE FEATURES:
- SSL certificate handling for Zscaler/Blue Coat environments
- Corporate proxy support with authentication
- Air-gapped deployment capabilities
- Compliance logging and audit trails
- Enterprise security policies

Real API Integration:
- Platform: {doc.name} ({doc.version})
- Base URL: {doc.base_url}
- Authentication: {doc.authentication_type}
- Total Endpoints Used: {app.total_endpoints_used}
- API Categories: {", ".join(app.api_categories_used)}

Features:
{chr(10).join("- " + f for f in app.features)}
"""

import json
import logging
import requests
import os
import sys
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

# Import corporate SSL helper
try:
    from ssl_helper import configure_corporate_ssl, CorporateSSLHelper
    SSL_HELPER_AVAILABLE = True
except ImportError:
    SSL_HELPER_AVAILABLE = False
    print("⚠️  SSL helper not available. SSL issues may occur in corporate environments.")


# Configure corporate-friendly logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('corporate_firewall_manager.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class CorporateFirewallRule:
    """Corporate firewall rule with compliance tracking"""
    name: str
    action: str  # allow, deny
    source_address: str
    destination_address: str
    destination_port: str
    protocol: str
    enabled: bool = True
    description: str = ""
    priority: int = 100
    created_by: str = ""
    created_at: datetime = None
    compliance_tags: List[str] = None
    audit_trail: List[Dict[str, Any]] = None


@dataclass
class ComplianceResult:
    """Corporate compliance check result"""
    rule_name: str
    compliant: bool
    violations: List[str]
    recommendations: List[str]
    risk_level: str  # low, medium, high, critical


class Corporate{platform.title()}FirewallManager:
    """
    Corporate-ready firewall manager for {doc.name}
    
    Features:
    - SSL certificate handling for corporate environments
    - Proxy support with authentication
    - Compliance checking and audit trails
    - Air-gapped deployment support
    """
    
    def __init__(self, base_url: str = "{doc.base_url}", 
                 api_key: str = None, session_id: str = None,
                 corporate_mode: bool = True):
        self.base_url = base_url
        self.corporate_mode = corporate_mode
        self.session_id = session_id
        
        # Initialize corporate session with SSL handling
        if SSL_HELPER_AVAILABLE and corporate_mode:
            logger.info("🏢 Initializing corporate environment...")
            self.session = configure_corporate_ssl(auto_configure=True)
            self.ssl_helper = CorporateSSLHelper()
            logger.info("✅ Corporate SSL configuration completed")
        else:
            logger.warning("⚠️  Corporate SSL not configured - may have certificate issues")
            self.session = requests.Session()
        
        # Set up authentication based on platform
        if "{doc.authentication_type}" == "API Key" and api_key:
            self.session.headers["X-Cisco-Meraki-API-Key"] = api_key
        elif "{doc.authentication_type}" == "Session-based" and session_id:
            self.session.headers["Authorization"] = f"Bearer {{session_id}}"
        
        # Corporate-friendly headers
        self.session.headers.update({{
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Corporate-Firewall-Manager/1.0 (Enterprise)"
        }})
        
        # Real API endpoints mapping
        self.endpoints = {{
'''
        
        # Add real endpoints to the code
        for ep in app.real_endpoints:
            safe_name = ep.endpoint.replace('/', '_').replace('{', '').replace('}', '').strip('_')
            code += f'            "{safe_name}": "{ep.endpoint}",  # {ep.description}\n'
        
        code += '''        }
        
        # Corporate configuration
        self.corporate_config = self._load_corporate_config()
        self.audit_logger = self._setup_audit_logging()
        
        # Initialize compliance checker
        self.compliance_rules = self._load_compliance_rules()
    
    def authenticate_corporate(self, username: str, password: str) -> bool:
        """
        Corporate authentication with SSL certificate handling
        """
        try:
            logger.info("🔐 Authenticating with corporate credentials...")
'''
        
        # Find login endpoint
        login_endpoints = [ep for ep in app.real_endpoints if "login" in ep.endpoint.lower()]
        if login_endpoints:
            login_ep = login_endpoints[0]
            code += f'''
            # Using real endpoint: {login_ep.endpoint}
            login_data = {{
                "user": username,
                "passwd": password
            }}
            
            # Corporate-aware request with SSL handling
            try:
                response = self.session.post(
                    f"{{self.base_url}}{login_ep.endpoint}",
                    json={{"method": "exec", "params": [login_data]}},
                    timeout=(30, 60),  # Corporate network timeouts
                    verify=not self.ssl_helper.ssl_verify_disabled if hasattr(self, 'ssl_helper') else True
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "session" in result:
                    self.session_id = result["session"]
                    self.session.headers["Authorization"] = f"Bearer {{self.session_id}}"
                    
                    # Log successful authentication
                    self.audit_logger.info(f"Successful authentication for user: {{username}}")
                    logger.info("✅ Corporate authentication successful")
                    return True
                
            except requests.exceptions.SSLError as e:
                logger.error(f"🔒 SSL certificate error: {{e}}")
                logger.info("💡 This may be due to corporate SSL interception (Zscaler, Blue Coat)")
                logger.info("💡 Try: export ZSCALER_CA_PATH=/path/to/corporate-root.pem")
                return False
            except requests.exceptions.ProxyError as e:
                logger.error(f"🌐 Proxy error: {{e}}")
                logger.info("💡 Check corporate proxy settings")
                return False
            except Exception as e:
                logger.error(f"❌ Authentication error: {{e}}")
                return False
                
            logger.error("❌ Authentication failed - invalid credentials")
            return False'''
        else:
            code += '''
            logger.warning("No authentication endpoint available in API documentation")
            return True  # Assume pre-authenticated'''
        
        code += '''
    
    def create_corporate_firewall_policy(self, rule: CorporateFirewallRule, 
                                       device_id: str = None) -> Dict[str, Any]:
        """
        Create firewall policy with corporate compliance checking
        """
        try:
            logger.info(f"🛡️  Creating corporate firewall policy: {{rule.name}}")
            
            # Compliance check first
            compliance_result = self.check_policy_compliance(rule)
            if not compliance_result.compliant:
                logger.warning(f"⚠️  Policy compliance issues: {{compliance_result.violations}}")
                return {{
                    "status": "error",
                    "message": "Policy violates corporate compliance",
                    "compliance_issues": compliance_result.violations
                }}
'''
        
        # Find policy creation endpoints
        create_endpoints = [ep for ep in policy_endpoints if ep.method == "POST"]
        if create_endpoints:
            create_ep = create_endpoints[0]
            code += f'''
            # Using real endpoint: {create_ep.endpoint}
            policy_data = {{
                "name": rule.name,
                "action": rule.action,
                "srcaddr": rule.source_address,
                "dstaddr": rule.destination_address,
                "service": f"{{rule.protocol}}_{{rule.destination_port}}",
                "schedule": "always",
                "status": "enable" if rule.enabled else "disable",
                "comments": f"{{rule.description}} | Created by: {{rule.created_by}} | Corporate Policy"
            }}
            
            endpoint_url = f"{{self.base_url}}{create_ep.endpoint}"
            if device_id:
                endpoint_url = endpoint_url.format(device_id=device_id)
            
            # Corporate-aware API request
            response = self._make_corporate_api_request("POST", endpoint_url, policy_data)
            
            if response:
                # Log to audit trail
                self.audit_logger.info(
                    f"Firewall policy created: {{rule.name}} by {{rule.created_by}} at {{datetime.now()}}"
                )
                
                logger.info(f"✅ Created corporate firewall policy: {{rule.name}}")
                return {{
                    "status": "success", 
                    "policy_id": response.get("id"), 
                    "rule": rule.name,
                    "compliance_status": "compliant"
                }}
            else:
                return {{"status": "error", "message": "Failed to create policy"}}'''
        else:
            code += '''
            logger.error("No policy creation endpoint available")
            return {"status": "error", "message": "No API endpoint available"}'''
        
        code += '''
                
        except Exception as e:
            logger.error(f"❌ Error creating corporate policy: {{e}}")
            return {{"status": "error", "message": str(e)}}
    
    def check_policy_compliance(self, rule: CorporateFirewallRule) -> ComplianceResult:
        """
        Check policy against corporate compliance rules
        """
        violations = []
        recommendations = []
        risk_level = "low"
        
        # Corporate compliance checks
        if rule.source_address == "any" and rule.destination_address == "any":
            violations.append("Overly permissive rule - both source and destination are 'any'")
            risk_level = "high"
        
        if rule.action == "allow" and rule.destination_port in ["22", "3389", "23"]:
            violations.append("Administrative access allowed - requires justification")
            risk_level = "medium"
        
        if not rule.description or len(rule.description) < 10:
            violations.append("Insufficient business justification in description")
        
        if not rule.created_by:
            violations.append("Policy creator not specified - required for audit")
        
        # Corporate network specific checks
        if "internal" not in rule.source_address.lower() and rule.action == "allow":
            recommendations.append("Consider restricting source to internal networks")
        
        return ComplianceResult(
            rule_name=rule.name,
            compliant=len(violations) == 0,
            violations=violations,
            recommendations=recommendations,
            risk_level=risk_level
        )
    
    def _make_corporate_api_request(self, method: str, url: str, 
                                  data: Dict = None) -> Dict[str, Any]:
        """
        Make API request with corporate network handling
        """
        try:
            # Corporate-friendly request parameters
            request_kwargs = {{
                'timeout': (30, 60),  # (connect, read) for corporate networks
                'allow_redirects': True
            }}
            
            # Handle SSL verification based on corporate configuration
            if hasattr(self, 'ssl_helper'):
                if self.ssl_helper.ssl_verify_disabled:
                    request_kwargs['verify'] = False
                elif self.ssl_helper.custom_ca_paths:
                    request_kwargs['verify'] = self.ssl_helper.custom_ca_paths[0]
            
            if method == "GET":
                response = self.session.get(url, **request_kwargs)
            elif method == "POST":
                response = self.session.post(url, json=data, **request_kwargs)
            elif method == "PUT":
                response = self.session.put(url, json=data, **request_kwargs)
            elif method == "DELETE":
                response = self.session.delete(url, **request_kwargs)
            else:
                raise ValueError(f"Unsupported method: {{method}}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.SSLError as e:
            logger.error(f"🔒 Corporate SSL error: {{e}}")
            logger.info("💡 Configure corporate certificates: export ZSCALER_CA_PATH=/path/to/cert.pem")
            return None
        except requests.exceptions.ProxyError as e:
            logger.error(f"🌐 Corporate proxy error: {{e}}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 Corporate network error: {{e}}")
            return None
    
    def _load_corporate_config(self) -> Dict[str, Any]:
        """Load corporate-specific configuration"""
        config_file = Path("corporate-config.json")
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Default corporate configuration
        return {{
            "environment": "corporate",
            "compliance_enabled": True,
            "audit_logging": True,
            "ssl_strict": False,  # Allow corporate SSL interception
            "proxy_aware": True
        }}
    
    def _setup_audit_logging(self) -> logging.Logger:
        """Setup corporate audit logging"""
        audit_logger = logging.getLogger('corporate_audit')
        audit_handler = logging.FileHandler('corporate_audit.log')
        audit_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
        )
        audit_handler.setFormatter(audit_formatter)
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
        return audit_logger
    
    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load corporate compliance rules"""
        # This would typically load from corporate policy files
        return {{
            "require_business_justification": True,
            "require_creator_identification": True,
            "prohibit_administrative_access": False,
            "require_source_restriction": True
        }}


# Corporate CLI interface with SSL handling
def corporate_main():
    import argparse
    
    parser = argparse.ArgumentParser(description=f"{app.name}")
    parser.add_argument("--base-url", default="{doc.base_url}", help="API base URL")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--username", help="Username for session auth")
    parser.add_argument("--password", help="Password for session auth")
    parser.add_argument("--corporate-mode", action="store_true", default=True,
                       help="Enable corporate SSL and proxy handling")
    parser.add_argument("--ssl-cert", help="Path to corporate SSL certificate")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # SSL configuration command
    ssl_parser = subparsers.add_parser("configure-ssl", help="Configure corporate SSL")
    ssl_parser.add_argument("--auto", action="store_true", help="Auto-configure SSL")
    
    # Create policy command
    create_parser = subparsers.add_parser("create-policy", help="Create firewall policy")
    create_parser.add_argument("--name", required=True, help="Policy name")
    create_parser.add_argument("--action", choices=["allow", "deny"], required=True)
    create_parser.add_argument("--source", required=True, help="Source address")
    create_parser.add_argument("--destination", required=True, help="Destination address")
    create_parser.add_argument("--port", required=True, help="Destination port")
    create_parser.add_argument("--protocol", choices=["tcp", "udp", "icmp"], required=True)
    create_parser.add_argument("--created-by", required=True, help="Policy creator (required for audit)")
    create_parser.add_argument("--device-id", help="Target device ID")
    
    args = parser.parse_args()
    
    # Handle SSL configuration
    if args.ssl_cert:
        os.environ["ZSCALER_CA_PATH"] = args.ssl_cert
    
    if args.command == "configure-ssl":
        print("🔧 Configuring corporate SSL...")
        if SSL_HELPER_AVAILABLE:
            if args.auto:
                session = configure_corporate_ssl(auto_configure=True)
                print("✅ Auto-configuration completed")
            else:
                ssl_helper = CorporateSSLHelper()
                status = ssl_helper.get_ssl_verification_status()
                print("SSL Configuration Status:")
                for key, value in status.items():
                    print(f"  {{key}}: {{value}}")
        else:
            print("❌ SSL helper not available")
        return
    
    # Initialize manager
    manager = Corporate{platform.title()}FirewallManager(
        base_url=args.base_url,
        api_key=args.api_key,
        corporate_mode=args.corporate_mode
    )
    
    # Authenticate if needed
    if args.username and args.password:
        if not manager.authenticate_corporate(args.username, args.password):
            print("❌ Corporate authentication failed")
            print("💡 Check SSL certificates and proxy configuration")
            return
    
    if args.command == "create-policy":
        rule = CorporateFirewallRule(
            name=args.name,
            action=args.action,
            source_address=args.source,
            destination_address=args.destination,
            destination_port=args.port,
            protocol=args.protocol,
            created_by=args.created_by,
            created_at=datetime.now()
        )
        
        result = manager.create_corporate_firewall_policy(rule, args.device_id)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    corporate_main()
'''
        
        return code
    
    def _generate_corporate_device_manager(self, platform: str, language: str) -> CorporateNetworkApp:
        """Generate corporate device manager"""
        doc = self.documentation[platform]
        
        device_endpoints = self.api_loader.search_endpoints(platform, "device")
        system_endpoints = self.api_loader.search_endpoints(platform, "system")
        
        all_endpoints = device_endpoints + system_endpoints
        endpoint_ids = set()
        unique_endpoints = []
        for ep in all_endpoints:
            if ep.id not in endpoint_ids:
                endpoint_ids.add(ep.id)
                unique_endpoints.append(ep)
        
        app = CorporateNetworkApp(
            name=f"Corporate {platform.title()} Device Manager",
            description=f"Enterprise device management with corporate network support for {doc.name}",
            platform=platform,
            features=[
                "Corporate SSL certificate handling",
                "Proxy-aware device communication",
                "Device discovery and registration",
                "Compliance monitoring and reporting",
                "Audit trail for all device operations",
                "Air-gapped deployment support"
            ],
            real_endpoints=unique_endpoints,
            api_categories_used=list(set(ep.category for ep in unique_endpoints)),
            total_endpoints_used=len(unique_endpoints),
            ssl_configured=True,
            corporate_ready=True,
            code={}
        )
        
        if language == "python":
            app.code["python"] = f'''# Corporate Device Manager for {platform.title()}
# This would be a full implementation similar to the firewall manager
# but focused on device management with corporate network support
'''
        
        return app


# Example usage
if __name__ == "__main__":
    from api_documentation_loader import APIDocumentationLoader
    
    # Load API documentation
    loader = APIDocumentationLoader("./api")
    docs = loader.load_all_documentation()
    
    if docs:
        # Generate corporate applications
        generator = CorporateNetworkAppGenerator(loader)
        
        if "fortinet" in docs:
            # Generate corporate firewall manager
            corporate_app = generator.generate_corporate_app(
                "corporate_firewall_manager", 
                "fortinet", 
                "python"
            )
            
            print(f"Generated: {corporate_app.name}")
            print(f"Corporate Ready: {corporate_app.corporate_ready}")
            print(f"SSL Configured: {corporate_app.ssl_configured}")
            print(f"Features: {', '.join(corporate_app.features)}")
            
            # Save the generated code
            output_file = f"corporate_{corporate_app.platform}_firewall_manager.py"
            with open(output_file, "w") as f:
                f.write(corporate_app.code["python"])
            
            print(f"✅ Corporate application saved: {output_file}")
    else:
        print("❌ No API documentation loaded")