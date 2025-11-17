"""
Corporate Proxy and Firewall Bypass Helper
Handles corporate network restrictions, proxies, and firewall configurations
"""

import os
import sys
import json
import requests
import urllib3
from typing import Dict, List, Any, Optional, Tuple
import logging
from urllib.parse import urlparse
import socket
import subprocess
import platform

logger = logging.getLogger(__name__)


class CorporateNetworkHelper:
    """
    Comprehensive helper for corporate network environments
    Handles proxies, firewalls, and network restrictions
    """
    
    def __init__(self):
        self.proxy_config = {}
        self.firewall_rules = []
        self.bypass_hosts = []
        self.detected_restrictions = []
        
    def auto_detect_corporate_network(self) -> Dict[str, Any]:
        """
        Automatically detect corporate network configuration
        
        Returns:
            Dict: Detection results with network configuration
        """
        logger.info("🕵️  Auto-detecting corporate network configuration...")
        
        detection_results = {
            "proxy_detected": False,
            "firewall_detected": False,
            "ssl_interception": False,
            "restrictions": [],
            "recommendations": []
        }
        
        # 1. Detect proxy configuration
        proxy_info = self._detect_proxy_configuration()
        if proxy_info:
            detection_results["proxy_detected"] = True
            detection_results["proxy_config"] = proxy_info
            self.proxy_config = proxy_info
        
        # 2. Test for firewall restrictions
        firewall_info = self._test_firewall_restrictions()
        if firewall_info["blocked_ports"]:
            detection_results["firewall_detected"] = True
            detection_results["firewall_info"] = firewall_info
        
        # 3. Test for SSL interception
        ssl_info = self._test_ssl_interception()
        if ssl_info["interception_detected"]:
            detection_results["ssl_interception"] = True
            detection_results["ssl_info"] = ssl_info
        
        # 4. Generate recommendations
        detection_results["recommendations"] = self._generate_recommendations(detection_results)
        
        logger.info(f"✅ Corporate network detection completed")
        return detection_results
    
    def configure_corporate_proxy(self, proxy_url: str = None, 
                                username: str = None, password: str = None,
                                bypass_list: List[str] = None) -> requests.Session:
        """
        Configure session with corporate proxy settings
        
        Args:
            proxy_url: Proxy URL (e.g., http://proxy.company.com:8080)
            username: Proxy authentication username
            password: Proxy authentication password
            bypass_list: List of hosts to bypass proxy
            
        Returns:
            requests.Session: Configured session
        """
        logger.info("🌐 Configuring corporate proxy...")
        
        session = requests.Session()
        
        # Auto-detect proxy if not provided
        if not proxy_url:
            proxy_info = self._detect_proxy_configuration()
            if proxy_info:
                proxy_url = proxy_info.get("http_proxy") or proxy_info.get("https_proxy")
        
        if proxy_url:
            # Configure proxy with authentication if provided
            if username and password:
                parsed = urlparse(proxy_url)
                proxy_with_auth = f"{parsed.scheme}://{username}:{password}@{parsed.netloc}"
                proxies = {
                    'http': proxy_with_auth,
                    'https': proxy_with_auth
                }
            else:
                proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
            
            session.proxies.update(proxies)
            logger.info(f"✅ Proxy configured: {urlparse(proxy_url).netloc}")
            
            # Configure bypass list
            if bypass_list:
                # Set NO_PROXY environment variable
                os.environ["NO_PROXY"] = ",".join(bypass_list)
                logger.info(f"✅ Proxy bypass configured for: {bypass_list}")
        else:
            logger.warning("⚠️  No proxy configuration detected or provided")
        
        return session
    
    def test_network_connectivity(self, test_urls: List[str] = None) -> Dict[str, Any]:
        """
        Test network connectivity to various endpoints
        
        Args:
            test_urls: List of URLs to test (uses defaults if None)
            
        Returns:
            Dict: Connectivity test results
        """
        if not test_urls:
            test_urls = [
                "https://httpbin.org/json",
                "https://api.github.com",
                "https://www.google.com/generate_204",
                "https://1.1.1.1",  # Cloudflare DNS
                "https://8.8.8.8"   # Google DNS
            ]
        
        logger.info("🧪 Testing network connectivity...")
        
        results = {
            "total_tests": len(test_urls),
            "successful": 0,
            "failed": 0,
            "test_results": {},
            "issues_detected": []
        }
        
        # Create session with auto-detected corporate settings
        session = self.configure_corporate_proxy()
        
        for url in test_urls:
            try:
                response = session.get(url, timeout=10)
                results["test_results"][url] = {
                    "status": "success",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
                results["successful"] += 1
                logger.info(f"✅ {url}: {response.status_code}")
                
            except requests.exceptions.ProxyError as e:
                results["test_results"][url] = {
                    "status": "proxy_error",
                    "error": str(e)
                }
                results["failed"] += 1
                results["issues_detected"].append("proxy_authentication_failure")
                logger.error(f"🌐 {url}: Proxy error - {e}")
                
            except requests.exceptions.SSLError as e:
                results["test_results"][url] = {
                    "status": "ssl_error", 
                    "error": str(e)
                }
                results["failed"] += 1
                results["issues_detected"].append("ssl_certificate_error")
                logger.error(f"🔒 {url}: SSL error - {e}")
                
            except requests.exceptions.ConnectTimeout as e:
                results["test_results"][url] = {
                    "status": "timeout",
                    "error": str(e)
                }
                results["failed"] += 1
                results["issues_detected"].append("network_timeout")
                logger.error(f"⏱️  {url}: Timeout - {e}")
                
            except requests.exceptions.ConnectionError as e:
                results["test_results"][url] = {
                    "status": "connection_error",
                    "error": str(e)
                }
                results["failed"] += 1
                results["issues_detected"].append("connection_blocked")
                logger.error(f"🚫 {url}: Connection blocked - {e}")
                
            except Exception as e:
                results["test_results"][url] = {
                    "status": "unknown_error",
                    "error": str(e)
                }
                results["failed"] += 1
                logger.error(f"❌ {url}: Unknown error - {e}")
        
        results["success_rate"] = results["successful"] / results["total_tests"] * 100
        
        logger.info(f"📊 Connectivity test completed: {results['successful']}/{results['total_tests']} successful")
        return results
    
    def bypass_firewall_restrictions(self, target_hosts: List[str] = None,
                                   alternative_ports: List[int] = None) -> Dict[str, Any]:
        """
        Attempt to bypass firewall restrictions using alternative methods
        
        Args:
            target_hosts: List of hosts to test
            alternative_ports: Alternative ports to try (default: [8080, 8443, 9443])
            
        Returns:
            Dict: Bypass results and recommendations
        """
        logger.info("🔥 Testing firewall bypass methods...")
        
        if not target_hosts:
            target_hosts = ["api.github.com", "httpbin.org"]
        
        if not alternative_ports:
            alternative_ports = [443, 8080, 8443, 9443, 3128]
        
        results = {
            "bypass_methods": {},
            "working_alternatives": [],
            "recommendations": []
        }
        
        for host in target_hosts:
            host_results = {
                "standard_ports": {},
                "alternative_ports": {},
                "working_ports": []
            }
            
            # Test standard HTTPS (443)
            if self._test_port_connectivity(host, 443):
                host_results["standard_ports"][443] = "open"
                host_results["working_ports"].append(443)
            else:
                host_results["standard_ports"][443] = "blocked"
            
            # Test alternative ports
            for port in alternative_ports:
                if port != 443:  # Already tested
                    if self._test_port_connectivity(host, port):
                        host_results["alternative_ports"][port] = "open"
                        host_results["working_ports"].append(port)
                        results["working_alternatives"].append(f"{host}:{port}")
                    else:
                        host_results["alternative_ports"][port] = "blocked"
            
            results["bypass_methods"][host] = host_results
        
        # Generate recommendations
        if results["working_alternatives"]:
            results["recommendations"].append("Use alternative ports for API access")
            results["recommendations"].append("Configure applications to use non-standard ports")
        else:
            results["recommendations"].append("All tested ports blocked - contact IT for firewall exceptions")
            results["recommendations"].append("Consider VPN or tunnel solutions")
        
        logger.info(f"🔥 Firewall bypass test completed")
        return results
    
    def create_corporate_friendly_session(self, 
                                        enable_ssl_bypass: bool = False,
                                        custom_headers: Dict[str, str] = None) -> requests.Session:
        """
        Create a session optimized for corporate environments
        
        Args:
            enable_ssl_bypass: Whether to bypass SSL verification (dev only)
            custom_headers: Additional headers to include
            
        Returns:
            requests.Session: Corporate-optimized session
        """
        logger.info("🏢 Creating corporate-friendly session...")
        
        # Start with proxy-configured session
        session = self.configure_corporate_proxy()
        
        # Corporate-friendly headers
        corporate_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Corporate-Tool/1.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        if custom_headers:
            corporate_headers.update(custom_headers)
        
        session.headers.update(corporate_headers)
        
        # Configure timeouts for corporate networks
        session.timeout = (30, 120)  # (connect, read) - generous for slow corporate networks
        
        # SSL configuration for corporate environments
        if enable_ssl_bypass:
            session.verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning("⚠️  SSL verification disabled - use only in development")
        
        # Configure retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        logger.info("✅ Corporate session configured")
        return session
    
    def _detect_proxy_configuration(self) -> Optional[Dict[str, Any]]:
        """Detect proxy configuration from environment and system"""
        proxy_info = {}
        
        # Check environment variables
        env_proxies = {}
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        for var in proxy_vars:
            value = os.environ.get(var)
            if value:
                env_proxies[var.lower()] = value
        
        if env_proxies:
            proxy_info["source"] = "environment"
            proxy_info.update(env_proxies)
        
        # Check system proxy settings (Windows)
        if platform.system() == "Windows" and not env_proxies:
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                  r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as key:
                    proxy_enable = winreg.QueryValueEx(key, "ProxyEnable")[0]
                    if proxy_enable:
                        proxy_server = winreg.QueryValueEx(key, "ProxyServer")[0]
                        proxy_info["source"] = "windows_registry"
                        proxy_info["http_proxy"] = f"http://{proxy_server}"
                        proxy_info["https_proxy"] = f"http://{proxy_server}"
            except Exception as e:
                logger.debug(f"Could not read Windows proxy settings: {e}")
        
        return proxy_info if proxy_info else None
    
    def _test_firewall_restrictions(self) -> Dict[str, Any]:
        """Test for common firewall restrictions"""
        results = {
            "blocked_ports": [],
            "open_ports": [],
            "restrictions_detected": False
        }
        
        # Test common ports
        test_ports = [80, 443, 8080, 8443, 3128, 9443]
        test_host = "httpbin.org"
        
        for port in test_ports:
            if self._test_port_connectivity(test_host, port, timeout=5):
                results["open_ports"].append(port)
            else:
                results["blocked_ports"].append(port)
        
        if results["blocked_ports"]:
            results["restrictions_detected"] = True
        
        return results
    
    def _test_ssl_interception(self) -> Dict[str, Any]:
        """Test for SSL interception (Zscaler, Blue Coat, etc.)"""
        results = {
            "interception_detected": False,
            "indicators": []
        }
        
        try:
            import ssl
            import socket
            
            # Test SSL certificate chain for known interceptors
            context = ssl.create_default_context()
            
            with socket.create_connection(("httpbin.org", 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname="httpbin.org") as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check for common SSL interception indicators
                    issuer = dict(x[0] for x in cert['issuer'])
                    
                    zscaler_indicators = ["Zscaler", "ZscalerRootCA"]
                    bluecoat_indicators = ["Blue Coat", "ProxySG"]
                    corporate_indicators = ["Corporate", "Enterprise", "Internal"]
                    
                    for indicator in zscaler_indicators + bluecoat_indicators + corporate_indicators:
                        if any(indicator.lower() in str(value).lower() 
                              for value in issuer.values()):
                            results["interception_detected"] = True
                            results["indicators"].append(f"SSL interceptor detected: {indicator}")
                            
        except Exception as e:
            logger.debug(f"SSL interception test failed: {e}")
        
        return results
    
    def _test_port_connectivity(self, host: str, port: int, timeout: int = 5) -> bool:
        """Test if a specific port is reachable"""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False
    
    def _generate_recommendations(self, detection_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on detection results"""
        recommendations = []
        
        if detection_results["proxy_detected"]:
            recommendations.append("Configure applications to use detected proxy")
            recommendations.append("Set up proxy authentication if required")
        
        if detection_results["ssl_interception"]:
            recommendations.append("Export and configure corporate SSL certificates")
            recommendations.append("Set ZSCALER_CA_PATH or similar environment variable")
        
        if detection_results["firewall_detected"]:
            recommendations.append("Request firewall exceptions for required ports")
            recommendations.append("Consider using alternative ports (8080, 8443)")
        
        if not any([detection_results["proxy_detected"], 
                   detection_results["ssl_interception"],
                   detection_results["firewall_detected"]]):
            recommendations.append("Network appears to have minimal restrictions")
            recommendations.append("Standard configuration should work")
        
        return recommendations


# Convenience functions for common corporate network tasks

def detect_corporate_network() -> Dict[str, Any]:
    """Detect corporate network configuration"""
    helper = CorporateNetworkHelper()
    return helper.auto_detect_corporate_network()


def create_corporate_session(enable_ssl_bypass: bool = False) -> requests.Session:
    """Create a session configured for corporate environments"""
    helper = CorporateNetworkHelper()
    return helper.create_corporate_friendly_session(enable_ssl_bypass=enable_ssl_bypass)


def test_corporate_connectivity() -> Dict[str, Any]:
    """Test network connectivity in corporate environment"""
    helper = CorporateNetworkHelper()
    return helper.test_network_connectivity()


# CLI interface for corporate network testing
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Corporate Network Helper")
    parser.add_argument("--detect", action="store_true", help="Auto-detect corporate network")
    parser.add_argument("--test-connectivity", action="store_true", help="Test network connectivity")
    parser.add_argument("--test-firewall", action="store_true", help="Test firewall restrictions")
    parser.add_argument("--bypass-ssl", action="store_true", help="Enable SSL bypass for testing")
    parser.add_argument("--proxy", help="Proxy URL to use")
    parser.add_argument("--proxy-user", help="Proxy username")
    parser.add_argument("--proxy-pass", help="Proxy password")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    helper = CorporateNetworkHelper()
    
    if args.detect:
        print("🕵️  Detecting corporate network configuration...")
        results = helper.auto_detect_corporate_network()
        print(json.dumps(results, indent=2))
    
    if args.test_connectivity:
        print("🧪 Testing network connectivity...")
        results = helper.test_network_connectivity()
        print(f"Success rate: {results['success_rate']:.1f}%")
        
        if results['issues_detected']:
            print(f"Issues detected: {', '.join(results['issues_detected'])}")
    
    if args.test_firewall:
        print("🔥 Testing firewall restrictions...")
        results = helper.bypass_firewall_restrictions()
        
        if results['working_alternatives']:
            print(f"Working alternatives: {results['working_alternatives']}")
        
        for rec in results['recommendations']:
            print(f"💡 {rec}")
    
    if args.proxy:
        print(f"🌐 Configuring proxy: {args.proxy}")
        session = helper.configure_corporate_proxy(
            args.proxy, args.proxy_user, args.proxy_pass
        )
        print("✅ Proxy session configured")


if __name__ == "__main__":
    main()