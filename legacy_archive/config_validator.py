#!/usr/bin/env python3
"""
Configuration Validator - Prevents Code Drift
Validates all critical configurations on startup
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any
import logging

class ConfigValidator:
    """Validates application configuration to prevent drift"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.config_dir = Path(__file__).parent
        self.static_dir = self.config_dir / "src" / "enhanced_network_api" / "static"
        
    def validate_all(self) -> bool:
        """Run all validations"""
        success = True
        
        # Critical file existence checks
        success &= self._validate_critical_files()
        
        # Configuration consistency checks  
        success &= self._validate_config_consistency()
        
        # API endpoint validation
        success &= self._validate_api_endpoints()
        
        # Static file integrity
        success &= self._validate_static_files()
        
        # Environment variables
        success &= self._validate_environment()
        
        # Report results
        self._report_results()
        
        return success
    
    def _validate_critical_files(self) -> bool:
        """Validate critical application files exist"""
        critical_files = [
            "src/enhanced_network_api/platform_web_api_fastapi.py",
            "src/enhanced_network_api/static/babylon_test.html", 
            "src/enhanced_network_api/static/2d_topology_enhanced.html",
            "mcp_servers/drawio_fortinet_meraki/mcp_server.py",
            "requirements.locked.txt"
        ]
        
        success = True
        for file_path in critical_files:
            full_path = self.config_dir / file_path
            if not full_path.exists():
                self.errors.append(f"CRITICAL: Missing file {file_path}")
                success = False
            elif full_path.stat().st_size == 0:
                self.errors.append(f"CRITICAL: Empty file {file_path}")
                success = False
                
        return success
    
    def _validate_config_consistency(self) -> bool:
        """Validate configuration consistency across files"""
        success = True
        
        # Check FastAPI routes match HTML expectations
        fastapi_file = self.config_dir / "src/enhanced_network_api/platform_web_api_fastapi.py"
        if fastapi_file.exists():
            content = fastapi_file.read_text()
            
            # Required routes (flexible matching)
            required_routes = [
                ('@app.get("/2d-topology-enhanced"', '2d-topology-enhanced route'),
                ('@app.get("/babylon-test"', 'babylon-test route'),
                ('@app.get("/api/topology/scene")', 'api/topology/scene route'),
                ('@app.post("/mcp/discover_fortinet_topology")', 'mcp discover route')
            ]
            
            for route_pattern, route_name in required_routes:
                if route_pattern not in content:
                    self.errors.append(f'CRITICAL: Missing {route_name}')
                    success = False
        
        return success
    
    def _validate_api_endpoints(self) -> bool:
        """Validate API endpoint structure"""
        success = True
        
        # Check babylon_test.html has required functions (flexible matching)
        babylon_file = self.static_dir / "babylon_test.html"
        if babylon_file.exists():
            content = babylon_file.read_text()
            
            required_functions = [
                ('function loadFortinetTopology', 'loadFortinetTopology function'),
                ('function loadTopologyFromAPI', 'loadTopologyFromAPI function'), 
                ('function renderTopology', 'renderTopology function'),
                ('function convertMCPToTopologyFormat', 'convertMCPToTopologyFormat function'),
                ("addEventListener('click', loadFortinetTopology)", 'button event listener')
            ]
            
            for func_pattern, func_name in required_functions:
                if func_pattern not in content:
                    self.errors.append(f"CRITICAL: Missing {func_name} in babylon_test.html")
                    success = False
        
        return success
    
    def _validate_static_files(self) -> bool:
        """Validate static file integrity"""
        success = True
        
        # Check for required CSS and JS
        required_static = [
            "babylon_test.css",
            "2d_topology_enhanced.css",
            "fortinet-icons/FortiGate.svg"
        ]
        
        for static_file in required_static:
            full_path = self.static_dir / static_file
            if not full_path.exists():
                self.warnings.append(f"Missing static file: {static_file}")
        
        return success
    
    def _validate_environment(self) -> bool:
        """Validate environment configuration"""
        success = True
        
        # Check .env file exists
        env_file = self.config_dir / "mcp_servers" / "drawio_fortinet_meraki" / ".env"
        if not env_file.exists():
            self.errors.append("CRITICAL: Missing .env file")
            return False
        
        # Check critical env vars
        env_content = env_file.read_text()
        critical_vars = [
            "FORTIGATE_HOSTS",
            "FORTIGATE_USERNAME", 
            "CODELLAMA_ENABLED"
        ]
        
        for var in critical_vars:
            if var not in env_content:
                self.warnings.append(f"Missing environment variable: {var}")
        
        return success
    
    def _report_results(self):
        """Report validation results"""
        print("=" * 60)
        print("CONFIGURATION VALIDATION REPORT")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ CRITICAL ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All validations passed!")
        elif not self.errors:
            print("\n⚠️  Warnings detected but configuration is functional")
        else:
            print(f"\n❌ {len(self.errors)} critical errors found - FIX REQUIRED")
        
        print("=" * 60)

def main():
    """Run configuration validation"""
    validator = ConfigValidator()
    success = validator.validate_all()
    
    if not success:
        print("\n🚫 Configuration validation failed!")
        print("Fix critical errors before proceeding.")
        sys.exit(1)
    else:
        print("\n✅ Configuration validated successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
