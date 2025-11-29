#!/usr/bin/env python3
"""
Startup Health Check - Ensures Application Integrity
Runs before starting the FastAPI server
"""

import os
import sys
import json
import requests
import subprocess
import time
from pathlib import Path

class StartupHealthCheck:
    """Comprehensive startup health validation"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.issues = []
        
    def run_all_checks(self) -> bool:
        """Run all health checks"""
        print("🔍 Running startup health checks...")
        
        checks = [
            self._check_python_version,
            self._check_dependencies,
            self._check_config_files,
            self._check_static_files,
            self._check_mcp_server,
            self._check_api_structure,
            self._check_ports_available
        ]
        
        all_passed = True
        for check in checks:
            try:
                result = check()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ Health check failed: {e}")
                all_passed = False
        
        return all_passed
    
    def _check_python_version(self) -> bool:
        """Check Python version compatibility"""
        version = sys.version_info
        if version.major != 3 or version.minor < 8:
            self.issues.append(f"Python 3.8+ required, found {version.major}.{version.minor}")
            return False
        print("✅ Python version OK")
        return True
    
    def _check_dependencies(self) -> bool:
        """Check critical dependencies"""
        try:
            import fastapi
            import uvicorn
            import aiohttp
            print("✅ Core dependencies OK")
            return True
        except ImportError as e:
            self.issues.append(f"Missing dependency: {e}")
            return False
    
    def _check_config_files(self) -> bool:
        """Check configuration files"""
        critical_files = [
            "src/enhanced_network_api/platform_web_api_fastapi.py",
            "mcp_servers/drawio_fortinet_meraki/.env",
            "requirements.locked.txt"
        ]
        
        for file_path in critical_files:
            full_path = self.base_dir / file_path
            if not full_path.exists():
                self.issues.append(f"Missing config file: {file_path}")
                return False
        
        print("✅ Configuration files OK")
        return True
    
    def _check_static_files(self) -> bool:
        """Check static web files"""
        static_dir = self.base_dir / "src/enhanced_network_api/static"
        
        critical_html = [
            "babylon_test.html",
            "2d_topology_enhanced.html"
        ]
        
        for html_file in critical_html:
            full_path = static_dir / html_file
            if not full_path.exists() or full_path.stat().st_size < 1000:
                self.issues.append(f"Missing/corrupted HTML: {html_file}")
                return False
        
        print("✅ Static files OK")
        return True
    
    def _check_mcp_server(self) -> bool:
        """Check MCP server configuration"""
        mcp_server_file = self.base_dir / "mcp_servers/drawio_fortinet_meraki/mcp_server.py"
        if not mcp_server_file.exists():
            self.issues.append("MCP server file missing")
            return False
        
        content = mcp_server_file.read_text()
        if "class DrawIOMCPServer" not in content:
            self.issues.append("MCP server class missing")
            return False
        
        print("✅ MCP server OK")
        return True
    
    def _check_api_structure(self) -> bool:
        """Check API endpoint structure"""
        api_file = self.base_dir / "src/enhanced_network_api/platform_web_api_fastapi.py"
        content = api_file.read_text()
        
        required_endpoints = [
            "@app.get(\"/api/topology/scene\")",
            "@app.get(\"/2d-topology-enhanced\")",
            "@app.post(\"/mcp/discover_fortinet_topology\")"
        ]
        
        for endpoint in required_endpoints:
            if endpoint not in content:
                self.issues.append(f"Missing endpoint: {endpoint}")
                return False
        
        print("✅ API structure OK")
        return True
    
    def _check_ports_available(self) -> bool:
        """Check if required ports are available"""
        import socket
        
        ports_to_check = [11111, 11110]
        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('127.0.0.1', port))
                sock.close()
            except OSError:
                self.issues.append(f"Port {port} already in use")
                return False
        
        print("✅ Ports available OK")
        return True

def main():
    """Run startup health check"""
    health_check = StartupHealthCheck()
    
    if health_check.run_all_checks():
        print("\n🎉 All health checks passed! Starting application...")
        return True
    else:
        print("\n❌ Health check failed!")
        print("Issues found:")
        for issue in health_check.issues:
            print(f"  • {issue}")
        print("\nFix issues before starting the application.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
