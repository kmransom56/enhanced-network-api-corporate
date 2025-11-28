#!/usr/bin/env python3
"""
Configuration Validation Script
Validates environment configuration and detects drift
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from enhanced_network_api.shared.config_manager import config_manager
except ImportError as e:
    print(f"Error importing config_manager: {e}")
    sys.exit(1)

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]

class ConfigValidator:
    """Validates configuration and detects drift"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.template_path = Path(__file__).parent.parent / ".env.template"
        self.env_path = Path(__file__).parent.parent / ".env"
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for validation"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def validate_all(self) -> ValidationResult:
        """Run comprehensive validation"""
        errors = []
        warnings = []
        info = []
        
        # 1. Check file existence
        file_result = self._validate_files()
        errors.extend(file_result.errors)
        warnings.extend(file_result.warnings)
        info.extend(file_result.info)
        
        # 2. Validate environment variables
        env_result = self._validate_environment()
        errors.extend(env_result.errors)
        warnings.extend(env_result.warnings)
        info.extend(env_result.info)
        
        # 3. Test configuration loading
        load_result = self._test_config_loading()
        errors.extend(load_result.errors)
        warnings.extend(load_result.warnings)
        info.extend(load_result.info)
        
        # 4. Validate external connectivity
        conn_result = self._validate_connectivity()
        errors.extend(conn_result.errors)
        warnings.extend(conn_result.warnings)
        info.extend(conn_result.info)
        
        # 5. Check configuration drift
        drift_result = self._check_drift()
        errors.extend(drift_result.errors)
        warnings.extend(drift_result.warnings)
        info.extend(drift_result.info)
        
        # 6. Validate data types and formats
        format_result = self._validate_formats()
        errors.extend(format_result.errors)
        warnings.extend(format_result.warnings)
        info.extend(format_result.info)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info
        )
    
    def _validate_files(self) -> ValidationResult:
        """Validate required files exist"""
        errors = []
        warnings = []
        info = []
        
        if not self.env_path.exists():
            errors.append(".env file not found. Copy .env.template and configure it.")
        else:
            info.append("✅ .env file found")
        
        if not self.template_path.exists():
            warnings.append(".env.template not found for drift comparison")
        else:
            info.append("✅ .env.template found")
        
        # Check required source files
        required_files = [
            "src/enhanced_network_api/platform_web_api_fastapi.py",
            "src/enhanced_network_api/shared/config_manager.py",
            "src/enhanced_network_api/shared/mcp_base.py"
        ]
        
        for file_path in required_files:
            full_path = Path(__file__).parent.parent / file_path
            if full_path.exists():
                info.append(f"✅ {file_path}")
            else:
                errors.append(f"Missing required file: {file_path}")
        
        return ValidationResult(True, errors, warnings, info)
    
    def _validate_environment(self) -> ValidationResult:
        """Validate environment variables"""
        errors = []
        warnings = []
        info = []
        
        # Load environment
        try:
            from dotenv import load_dotenv
            load_dotenv(self.env_path)
            info.append("✅ Environment loaded from .env")
        except ImportError:
            warnings.append("python-dotenv not installed, using system environment")
        except Exception as e:
            errors.append(f"Failed to load environment: {e}")
        
        # Check required variables
        required_vars = {
            "API_HOST": "API server host",
            "API_PORT": "API server port",
            "LLM_BASE_URL": "LLM server URL"
        }
        
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                info.append(f"✅ {var}: {value}")
            else:
                errors.append(f"Required variable {var} ({description}) not set")
        
        # Check optional but recommended variables
        optional_vars = {
            "FORTIGATE_HOSTS": "FortiGate device hosts",
            "MERAKI_API_KEY": "Meraki API key",
            "DATABASE_URL": "Database connection URL"
        }
        
        for var, description in optional_vars.items():
            value = os.getenv(var)
            if value:
                info.append(f"✅ {var}: configured")
            else:
                warnings.append(f"Optional variable {var} ({description}) not set")
        
        return ValidationResult(True, errors, warnings, info)
    
    def _test_config_loading(self) -> ValidationResult:
        """Test configuration manager loading"""
        errors = []
        warnings = []
        info = []
        
        try:
            # Test config manager instantiation
            configs = config_manager.get_all_config()
            info.append("✅ Configuration manager loads successfully")
            
            # Test specific configurations
            if configs.get("api"):
                api_config = configs["api"]
                info.append(f"✅ API config: port {api_config.get('port', 'unknown')}")
            else:
                warnings.append("API configuration not found")
            
            if configs.get("llm"):
                llm_config = configs["llm"]
                info.append(f"✅ LLM config: {llm_config.get('base_url', 'unknown')}")
            else:
                warnings.append("LLM configuration not found")
            
            if configs.get("fortigate"):
                fg_count = len(configs["fortigate"])
                info.append(f"✅ FortiGate config: {fg_count} device(s)")
            else:
                warnings.append("No FortiGate devices configured")
            
        except Exception as e:
            errors.append(f"Configuration manager failed: {e}")
        
        return ValidationResult(True, errors, warnings, info)
    
    def _validate_connectivity(self) -> ValidationResult:
        """Validate external connectivity"""
        errors = []
        warnings = []
        info = []
        
        import httpx
        import asyncio
        
        async def test_connectivity():
            """Test external service connectivity"""
            try:
                # Test LLM server
                llm_base_url = os.getenv("LLM_BASE_URL")
                if llm_base_url:
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            response = await client.get(llm_base_url)
                            info.append(f"✅ LLM server reachable at {llm_base_url}")
                    except Exception as e:
                        warnings.append(f"LLM server not reachable: {e}")
                
                # Test FortiGate connectivity
                fortigate_hosts = os.getenv("FORTIGATE_HOSTS", "")
                if fortigate_hosts:
                    hosts = [h.strip() for h in fortigate_hosts.split(",") if h.strip()]
                    for host in hosts[:3]:  # Test first 3 hosts
                        try:
                            async with httpx.AsyncClient(timeout=5.0) as client:
                                response = await client.get(f"https://{host}:10443/api/v2/monitor/system/status")
                                info.append(f"✅ FortiGate {host} reachable")
                        except Exception as e:
                            warnings.append(f"FortiGate {host} not reachable: {e}")
                
                # Test Meraki API
                meraki_key = os.getenv("MERAKI_API_KEY")
                if meraki_key:
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            response = await client.get("https://api.meraki.com/api/v1/organizations")
                            info.append("✅ Meraki API reachable")
                    except Exception as e:
                        warnings.append(f"Meraki API not reachable: {e}")
                        
            except Exception as e:
                errors.append(f"Connectivity test failed: {e}")
        
        # Run async test
        try:
            asyncio.run(test_connectivity())
        except Exception as e:
            warnings.append(f"Connectivity tests incomplete: {e}")
        
        return ValidationResult(True, errors, warnings, info)
    
    def _check_drift(self) -> ValidationResult:
        """Check for configuration drift"""
        errors = []
        warnings = []
        info = []
        
        if not self.template_path.exists():
            warnings.append("Cannot check drift: .env.template not found")
            return ValidationResult(True, errors, warnings, info)
        
        try:
            # Parse template variables
            template_vars = self._parse_env_file(self.template_path)
            env_vars = self._parse_env_file(self.env_path)
            
            # Check for missing required variables
            required_template_vars = [v for v in template_vars.keys() if not v.startswith("#") and "=" in v]
            for var in required_template_vars:
                if var not in env_vars:
                    warnings.append(f"Template variable {var} not set in .env")
            
            # Check for new variables
            for var in env_vars.keys():
                if var not in template_vars and not var.startswith("#"):
                    info.append(f"Custom variable {var} in .env")
            
            # Check value changes for known variables
            drift_count = 0
            for var in template_vars:
                if var in env_vars and template_vars[var] != env_vars[var]:
                    if not var.startswith("FORTIGATE_") and not var.startswith("MERAKI_") and var != "DATABASE_URL":
                        info.append(f"Variable {var} differs from template")
                        drift_count += 1
            
            if drift_count == 0:
                info.append("✅ No configuration drift detected")
            else:
                warnings.append(f"{drift_count} variables differ from template")
            
        except Exception as e:
            errors.append(f"Drift check failed: {e}")
        
        return ValidationResult(True, errors, warnings, info)
    
    def _validate_formats(self) -> ValidationResult:
        """Validate data formats and types"""
        errors = []
        warnings = []
        info = []
        
        # Validate port numbers
        port_vars = ["API_PORT", "FORTIGATE_192_168_0_254_PORT", "MCP_FORTINET_PORT"]
        for var in port_vars:
            value = os.getenv(var)
            if value:
                try:
                    port = int(value)
                    if 1 <= port <= 65535:
                        info.append(f"✅ {var}: valid port {port}")
                    else:
                        errors.append(f"{var}: port {port} out of range (1-65535)")
                except ValueError:
                    errors.append(f"{var}: '{value}' is not a valid port number")
        
        # Validate URLs
        url_vars = ["LLM_BASE_URL", "MERAKI_BASE_URL"]
        for var in url_vars:
            value = os.getenv(var)
            if value:
                if value.startswith(("http://", "https://")):
                    info.append(f"✅ {var}: valid URL format")
                else:
                    warnings.append(f"{var}: '{value}' may not be a valid URL")
        
        # Validate boolean values
        bool_vars = ["API_DEBUG", "TOPOLOGY_AUTO_REFRESH", "SSL_ENABLED"]
        for var in bool_vars:
            value = os.getenv(var)
            if value:
                if value.lower() in ("true", "false", "1", "0", "yes", "no"):
                    info.append(f"✅ {var}: valid boolean format")
                else:
                    warnings.append(f"{var}: '{value}' may not be a valid boolean")
        
        return ValidationResult(True, errors, warnings, info)
    
    def _parse_env_file(self, file_path: Path) -> Dict[str, str]:
        """Parse .env file into dictionary"""
        vars = {}
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        vars[key.strip()] = value.strip()
        except Exception as e:
            self.logger.error(f"Failed to parse {file_path}: {e}")
        return vars
    
    def generate_report(self, result: ValidationResult) -> str:
        """Generate validation report"""
        report = []
        report.append("Configuration Validation Report")
        report.append("=" * 35)
        report.append("")
        
        if result.is_valid:
            report.append("🎉 VALIDATION PASSED")
        else:
            report.append("❌ VALIDATION FAILED")
        
        report.append("")
        
        if result.errors:
            report.append("ERRORS:")
            for error in result.errors:
                report.append(f"  ❌ {error}")
            report.append("")
        
        if result.warnings:
            report.append("WARNINGS:")
            for warning in result.warnings:
                report.append(f"  ⚠️  {warning}")
            report.append("")
        
        if result.info:
            report.append("INFO:")
            for info_item in result.info:
                report.append(f"  ℹ️  {info_item}")
            report.append("")
        
        # Summary
        report.append("SUMMARY:")
        report.append(f"  Errors: {len(result.errors)}")
        report.append(f"  Warnings: {len(result.warnings)}")
        report.append(f"  Info: {len(result.info)}")
        report.append("")
        
        if result.is_valid:
            if result.warnings:
                report.append("✅ Ready for deployment (review warnings)")
            else:
                report.append("✅ Ready for deployment")
        else:
            report.append("🛑 Fix errors before deployment")
        
        return "\n".join(report)

def main():
    """Main validation function"""
    validator = ConfigValidator()
    result = validator.validate_all()
    
    # Print report
    report = validator.generate_report(result)
    print(report)
    
    # Exit with appropriate code
    sys.exit(0 if result.is_valid else 1)

if __name__ == "__main__":
    main()
