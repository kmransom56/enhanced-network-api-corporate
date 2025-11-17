"""
Corporate Network Installation Scripts
Automated installation for restricted corporate networks
"""

import os
import sys
import json
import shutil
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import zipfile

logger = logging.getLogger(__name__)


class CorporateInstaller:
    """
    Handles installation in corporate networks with restrictions
    """
    
    def __init__(self, install_dir: str = "./corporate-network-api"):
        self.install_dir = Path(install_dir)
        self.platform = platform.system().lower()
        self.installation_log = []
        
    def install_corporate_package(self, package_path: str = None, 
                                offline_mode: bool = False) -> bool:
        """
        Install the enhanced network API package in corporate environment
        
        Args:
            package_path: Path to package ZIP file
            offline_mode: Install without internet connectivity
            
        Returns:
            bool: True if installation successful
        """
        logger.info("🏢 Starting corporate installation...")
        self.installation_log.append("Starting corporate installation")
        
        try:
            # 1. Prepare installation directory
            if not self._prepare_installation_directory():
                return False
            
            # 2. Extract package if provided
            if package_path:
                if not self._extract_package(package_path):
                    return False
            
            # 3. Detect corporate environment
            env_info = self._detect_corporate_environment()
            self.installation_log.append(f"Detected environment: {env_info.get('type', 'unknown')}")
            
            # 4. Install dependencies
            if not self._install_dependencies(offline_mode):
                logger.warning("⚠️  Some dependencies may not be installed")
            
            # 5. Configure for corporate environment
            if not self._configure_corporate_settings(env_info):
                logger.warning("⚠️  Corporate configuration may be incomplete")
            
            # 6. Create startup scripts
            if not self._create_startup_scripts():
                return False
            
            # 7. Run post-installation tests
            test_results = self._run_post_installation_tests()
            if test_results.get("critical_failures", 0) > 0:
                logger.error("❌ Critical installation failures detected")
                return False
            
            # 8. Generate installation report
            self._generate_installation_report(test_results)
            
            logger.info("✅ Corporate installation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Installation failed: {e}")
            self.installation_log.append(f"Installation failed: {e}")
            return False
    
    def create_offline_package(self, output_path: str = "corporate-offline-package.zip") -> str:
        """
        Create offline installation package for air-gapped environments
        
        Args:
            output_path: Path for output ZIP file
            
        Returns:
            str: Path to created package
        """
        logger.info("📦 Creating offline installation package...")
        
        # Create temporary directory for package contents
        temp_dir = Path("./temp-offline-package")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Copy core files
            self._copy_core_files_to_package(temp_dir)
            
            # Download and bundle dependencies
            if not self._bundle_offline_dependencies(temp_dir):
                logger.warning("⚠️  Could not bundle all dependencies")
            
            # Create installation scripts
            self._create_offline_installation_scripts(temp_dir)
            
            # Create package documentation
            self._create_offline_documentation(temp_dir)
            
            # Create ZIP package
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arc_path = file_path.relative_to(temp_dir)
                        zipf.write(file_path, arc_path)
            
            # Cleanup temporary directory
            shutil.rmtree(temp_dir)
            
            logger.info(f"✅ Offline package created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Failed to create offline package: {e}")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise
    
    def install_for_air_gapped_environment(self, package_path: str) -> bool:
        """
        Install in air-gapped environment without internet access
        
        Args:
            package_path: Path to offline package
            
        Returns:
            bool: Success status
        """
        logger.info("🔒 Installing for air-gapped environment...")
        
        return self.install_corporate_package(
            package_path=package_path,
            offline_mode=True
        )
    
    def _prepare_installation_directory(self) -> bool:
        """Prepare installation directory"""
        logger.info("📁 Preparing installation directory...")
        
        try:
            self.install_dir.mkdir(exist_ok=True, parents=True)
            
            # Check write permissions
            test_file = self.install_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            
            logger.info(f"✅ Installation directory prepared: {self.install_dir}")
            self.installation_log.append(f"Installation directory: {self.install_dir}")
            return True
            
        except PermissionError:
            logger.error("❌ Permission denied - run as administrator or check directory permissions")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to prepare installation directory: {e}")
            return False
    
    def _extract_package(self, package_path: str) -> bool:
        """Extract installation package"""
        logger.info(f"📦 Extracting package: {package_path}")
        
        try:
            with zipfile.ZipFile(package_path, 'r') as zipf:
                zipf.extractall(self.install_dir)
            
            logger.info("✅ Package extracted successfully")
            self.installation_log.append("Package extracted")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to extract package: {e}")
            return False
    
    def _detect_corporate_environment(self) -> Dict[str, Any]:
        """Detect corporate environment settings"""
        logger.info("🕵️  Detecting corporate environment...")
        
        env_info = {
            "type": "unknown",
            "proxy_detected": False,
            "ssl_interception": False,
            "domain_joined": False,
            "restrictions": []
        }
        
        # Check for proxy
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        for var in proxy_vars:
            if os.environ.get(var):
                env_info["proxy_detected"] = True
                env_info["type"] = "corporate"
                break
        
        # Check for domain membership
        if self.platform == "windows":
            try:
                result = subprocess.run(['echo', '%USERDNSDOMAIN%'], 
                                     capture_output=True, text=True, shell=True)
                if result.stdout.strip() and '%USERDNSDOMAIN%' not in result.stdout:
                    env_info["domain_joined"] = True
                    env_info["type"] = "corporate"
            except:
                pass
        
        # Check for SSL interception software
        ssl_software_paths = []
        if self.platform == "windows":
            ssl_software_paths = [
                r"C:\Program Files\Zscaler",
                r"C:\Program Files (x86)\Zscaler"
            ]
        else:
            ssl_software_paths = [
                "/opt/zscaler",
                "/usr/local/zscaler"
            ]
        
        for path in ssl_software_paths:
            if Path(path).exists():
                env_info["ssl_interception"] = True
                env_info["type"] = "corporate"
                break
        
        logger.info(f"Environment detected: {env_info['type']}")
        return env_info
    
    def _install_dependencies(self, offline_mode: bool = False) -> bool:
        """Install Python dependencies"""
        logger.info("📦 Installing dependencies...")
        
        # Create requirements.txt if not exists
        requirements_file = self.install_dir / "requirements.txt"
        if not requirements_file.exists():
            requirements_content = """
# Enhanced Network API Corporate Dependencies
requests>=2.28.0
urllib3>=1.26.0
certifi>=2022.12.7
PyYAML>=6.0

# Optional corporate features
cryptography>=3.4.8
pyOpenSSL>=22.0.0
PySocks>=1.7.1
"""
            requirements_file.write_text(requirements_content.strip())
        
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            
            if offline_mode:
                # Look for bundled wheels
                wheels_dir = self.install_dir / "wheels"
                if wheels_dir.exists():
                    cmd.extend(["--no-index", "--find-links", str(wheels_dir)])
                else:
                    logger.warning("⚠️  Offline mode requested but no wheels directory found")
                    return False
            else:
                # Add corporate-friendly options
                cmd.extend([
                    "--trusted-host", "pypi.org",
                    "--trusted-host", "pypi.python.org",
                    "--trusted-host", "files.pythonhosted.org",
                    "--user"  # Install to user directory
                ])
                
                # Use proxy if detected
                proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
                if proxy:
                    cmd.extend(["--proxy", proxy])
                    logger.info(f"Using proxy for dependency installation: {proxy}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Dependencies installed successfully")
                self.installation_log.append("Dependencies installed")
                return True
            else:
                logger.error(f"❌ Dependency installation failed: {result.stderr}")
                self.installation_log.append(f"Dependency installation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error installing dependencies: {e}")
            return False
    
    def _configure_corporate_settings(self, env_info: Dict[str, Any]) -> bool:
        """Configure settings for corporate environment"""
        logger.info("🔧 Configuring corporate settings...")
        
        try:
            # Create corporate configuration file
            corporate_config = {
                "environment": "corporate",
                "proxy_enabled": env_info.get("proxy_detected", False),
                "ssl_verification": not env_info.get("ssl_interception", False),
                "audit_logging": True,
                "installation_date": "2024-01-01T00:00:00",  # Would be actual timestamp
                "detected_restrictions": env_info.get("restrictions", [])
            }
            
            config_file = self.install_dir / "corporate-config.json"
            with open(config_file, 'w') as f:
                json.dump(corporate_config, f, indent=2)
            
            # Configure SSL if needed
            if env_info.get("ssl_interception"):
                self._configure_ssl_certificates()
            
            # Configure proxy if needed
            if env_info.get("proxy_detected"):
                self._configure_proxy_settings()
            
            logger.info("✅ Corporate settings configured")
            self.installation_log.append("Corporate settings configured")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to configure corporate settings: {e}")
            return False
    
    def _configure_ssl_certificates(self) -> None:
        """Configure SSL certificates for corporate environment"""
        logger.info("🔒 Configuring SSL certificates...")
        
        # Create SSL configuration script
        ssl_script = self.install_dir / "configure-ssl.py"
        ssl_script_content = '''#!/usr/bin/env python3
"""
Corporate SSL Configuration
Auto-generated during installation
"""

import os
import sys
from pathlib import Path

def configure_ssl():
    """Configure SSL for corporate environment"""
    print("🔒 Configuring SSL certificates...")
    
    # Common certificate locations
    cert_paths = []
    if os.name == 'nt':  # Windows
        cert_paths = [
            r"C:\\Program Files\\Zscaler\\ZSARoot.pem",
            r"C:\\certificates\\zscaler-root.pem"
        ]
    else:  # Unix-like
        cert_paths = [
            "/etc/ssl/certs/zscaler-root.pem",
            os.path.expanduser("~/.certificates/zscaler.pem")
        ]
    
    for cert_path in cert_paths:
        if Path(cert_path).exists():
            os.environ["ZSCALER_CA_PATH"] = cert_path
            os.environ["REQUESTS_CA_BUNDLE"] = cert_path
            print(f"✅ SSL certificate configured: {cert_path}")
            return
    
    print("⚠️  No SSL certificates found automatically")
    print("💡 Manual steps:")
    print("   1. Export your corporate root certificate")
    print("   2. Set ZSCALER_CA_PATH environment variable")

if __name__ == "__main__":
    configure_ssl()
'''
        ssl_script.write_text(ssl_script_content)
        
        # Make executable on Unix-like systems
        if self.platform != "windows":
            os.chmod(ssl_script, 0o755)
    
    def _configure_proxy_settings(self) -> None:
        """Configure proxy settings for corporate environment"""
        logger.info("🌐 Configuring proxy settings...")
        
        # Create proxy configuration script
        proxy_script = self.install_dir / "configure-proxy.py"
        proxy_script_content = '''#!/usr/bin/env python3
"""
Corporate Proxy Configuration
Auto-generated during installation
"""

import os

def configure_proxy():
    """Configure proxy settings"""
    print("🌐 Configuring corporate proxy...")
    
    # Check for existing proxy settings
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    
    proxy_found = False
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ Found proxy setting: {var}={value}")
            proxy_found = True
    
    if not proxy_found:
        print("⚠️  No proxy settings detected in environment")
        print("💡 If you need proxy configuration:")
        print("   export HTTP_PROXY=http://proxy.company.com:8080")
        print("   export HTTPS_PROXY=http://proxy.company.com:8080")

if __name__ == "__main__":
    configure_proxy()
'''
        proxy_script.write_text(proxy_script_content)
        
        # Make executable on Unix-like systems
        if self.platform != "windows":
            os.chmod(proxy_script, 0o755)
    
    def _create_startup_scripts(self) -> bool:
        """Create startup scripts for the application"""
        logger.info("📜 Creating startup scripts...")
        
        try:
            # Create main startup script
            if self.platform == "windows":
                self._create_windows_startup_script()
            else:
                self._create_unix_startup_script()
            
            # Create environment setup script
            self._create_environment_setup_script()
            
            logger.info("✅ Startup scripts created")
            self.installation_log.append("Startup scripts created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create startup scripts: {e}")
            return False
    
    def _create_windows_startup_script(self) -> None:
        """Create Windows batch startup script"""
        startup_script = self.install_dir / "start-corporate-api.bat"
        script_content = '''@echo off
echo Starting Enhanced Network API - Corporate Edition
echo ================================================

echo Configuring corporate environment...
python configure-ssl.py
python configure-proxy.py

echo Starting API agent...
python -m enhanced_network_api_agent

pause
'''
        startup_script.write_text(script_content)
    
    def _create_unix_startup_script(self) -> None:
        """Create Unix shell startup script"""
        startup_script = self.install_dir / "start-corporate-api.sh"
        script_content = '''#!/bin/bash
echo "Starting Enhanced Network API - Corporate Edition"
echo "================================================"

echo "Configuring corporate environment..."
python3 configure-ssl.py
python3 configure-proxy.py

echo "Starting API agent..."
python3 -m enhanced_network_api_agent
'''
        startup_script.write_text(script_content)
        os.chmod(startup_script, 0o755)
    
    def _create_environment_setup_script(self) -> None:
        """Create environment setup script"""
        setup_script = self.install_dir / "setup-corporate-environment.py"
        script_content = '''#!/usr/bin/env python3
"""
Corporate Environment Setup
Configures the enhanced network API for corporate use
"""

import os
import sys
import json
from pathlib import Path

def setup_corporate_environment():
    """Complete corporate environment setup"""
    print("🏢 Setting up corporate environment...")
    
    # Load corporate configuration
    config_file = Path("corporate-config.json")
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print(f"Environment: {config.get('environment', 'unknown')}")
        print(f"Proxy enabled: {config.get('proxy_enabled', False)}")
        print(f"SSL verification: {config.get('ssl_verification', True)}")
    
    # Run SSL configuration
    try:
        exec(open("configure-ssl.py").read())
    except FileNotFoundError:
        print("⚠️  SSL configuration script not found")
    
    # Run proxy configuration
    try:
        exec(open("configure-proxy.py").read())
    except FileNotFoundError:
        print("⚠️  Proxy configuration script not found")
    
    print("✅ Corporate environment setup completed")

if __name__ == "__main__":
    setup_corporate_environment()
'''
        setup_script.write_text(script_content)
        
        # Make executable on Unix-like systems
        if self.platform != "windows":
            os.chmod(setup_script, 0o755)
    
    def _run_post_installation_tests(self) -> Dict[str, Any]:
        """Run post-installation validation tests"""
        logger.info("🧪 Running post-installation tests...")
        
        test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "critical_failures": 0,
            "test_details": {}
        }
        
        # Test 1: Check core files
        core_files_test = self._test_core_files()
        test_results["test_details"]["core_files"] = core_files_test
        test_results["total_tests"] += 1
        if core_files_test["status"] == "pass":
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
            if core_files_test.get("critical", False):
                test_results["critical_failures"] += 1
        
        # Test 2: Check Python dependencies
        deps_test = self._test_dependencies()
        test_results["test_details"]["dependencies"] = deps_test
        test_results["total_tests"] += 1
        if deps_test["status"] == "pass":
            test_results["passed"] += 1
        elif deps_test["status"] == "warning":
            test_results["warnings"] += 1
        else:
            test_results["failed"] += 1
        
        # Test 3: Check corporate configuration
        config_test = self._test_corporate_configuration()
        test_results["test_details"]["corporate_config"] = config_test
        test_results["total_tests"] += 1
        if config_test["status"] == "pass":
            test_results["passed"] += 1
        else:
            test_results["warnings"] += 1
        
        # Test 4: Test network connectivity
        network_test = self._test_network_connectivity()
        test_results["test_details"]["network"] = network_test
        test_results["total_tests"] += 1
        if network_test["status"] == "pass":
            test_results["passed"] += 1
        else:
            test_results["warnings"] += 1
        
        logger.info(f"Tests completed: {test_results['passed']}/{test_results['total_tests']} passed")
        return test_results
    
    def _test_core_files(self) -> Dict[str, Any]:
        """Test that core files are present"""
        required_files = [
            "api_documentation_loader.py",
            "comprehensive_sdk_generator.py",
            "enhanced_network_app_generator.py",
            "ssl_helper.py"
        ]
        
        missing_files = []
        for file_name in required_files:
            if not (self.install_dir / file_name).exists():
                missing_files.append(file_name)
        
        if not missing_files:
            return {"status": "pass", "message": "All core files present"}
        else:
            return {
                "status": "fail",
                "message": f"Missing core files: {missing_files}",
                "critical": True
            }
    
    def _test_dependencies(self) -> Dict[str, Any]:
        """Test Python dependencies"""
        required_modules = ["requests", "urllib3", "yaml"]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if not missing_modules:
            return {"status": "pass", "message": "All dependencies available"}
        elif len(missing_modules) < len(required_modules):
            return {
                "status": "warning",
                "message": f"Some dependencies missing: {missing_modules}"
            }
        else:
            return {
                "status": "fail", 
                "message": f"Critical dependencies missing: {missing_modules}"
            }
    
    def _test_corporate_configuration(self) -> Dict[str, Any]:
        """Test corporate configuration"""
        config_file = self.install_dir / "corporate-config.json"
        
        if not config_file.exists():
            return {
                "status": "warning",
                "message": "Corporate configuration file not found"
            }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if config.get("environment") == "corporate":
                return {"status": "pass", "message": "Corporate configuration valid"}
            else:
                return {
                    "status": "warning",
                    "message": "Corporate configuration may be incomplete"
                }
        
        except Exception as e:
            return {
                "status": "warning",
                "message": f"Could not validate configuration: {e}"
            }
    
    def _test_network_connectivity(self) -> Dict[str, Any]:
        """Test basic network connectivity"""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return {"status": "pass", "message": "Network connectivity available"}
        except:
            return {
                "status": "warning", 
                "message": "Network connectivity issues detected"
            }
    
    def _generate_installation_report(self, test_results: Dict[str, Any]) -> None:
        """Generate installation report"""
        logger.info("📊 Generating installation report...")
        
        report = {
            "installation_summary": {
                "timestamp": "2024-01-01T00:00:00",  # Would be actual timestamp
                "platform": self.platform,
                "install_directory": str(self.install_dir),
                "success": test_results["critical_failures"] == 0
            },
            "test_results": test_results,
            "installation_log": self.installation_log,
            "next_steps": [
                "Run: python setup-corporate-environment.py",
                "Configure SSL certificates if needed",
                "Test with: python -m enhanced_network_api_agent",
                "Check corporate-config.json for settings"
            ]
        }
        
        report_file = self.install_dir / "installation-report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Create human-readable report
        readme_file = self.install_dir / "INSTALLATION-REPORT.md"
        readme_content = f"""# Corporate Installation Report

## Installation Summary
- **Status**: {"✅ Success" if report["installation_summary"]["success"] else "❌ Failed"}
- **Platform**: {self.platform}
- **Directory**: {self.install_dir}

## Test Results
- **Total Tests**: {test_results["total_tests"]}
- **Passed**: {test_results["passed"]}
- **Failed**: {test_results["failed"]}
- **Warnings**: {test_results["warnings"]}
- **Critical Failures**: {test_results["critical_failures"]}

## Next Steps
{chr(10).join("- " + step for step in report["next_steps"])}

## Support
If you encounter issues:
1. Check the installation log in installation-report.json
2. Run: python setup-corporate-environment.py
3. Verify SSL certificates and proxy settings
"""
        readme_file.write_text(readme_content)
        
        logger.info(f"✅ Installation report generated: {report_file}")


# CLI interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Corporate Network API Installer")
    parser.add_argument("--install", action="store_true", help="Install corporate package")
    parser.add_argument("--package", help="Path to installation package")
    parser.add_argument("--offline", action="store_true", help="Offline installation mode")
    parser.add_argument("--create-offline", action="store_true", help="Create offline package")
    parser.add_argument("--install-dir", default="./corporate-network-api", help="Installation directory")
    parser.add_argument("--output", help="Output path for offline package")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    installer = CorporateInstaller(args.install_dir)
    
    if args.create_offline:
        output_path = args.output or "corporate-offline-package.zip"
        package_path = installer.create_offline_package(output_path)
        print(f"✅ Offline package created: {package_path}")
    
    if args.install:
        success = installer.install_corporate_package(
            package_path=args.package,
            offline_mode=args.offline
        )
        
        if success:
            print("✅ Installation completed successfully")
            print(f"📁 Installed to: {installer.install_dir}")
            print("🚀 Next: python setup-corporate-environment.py")
        else:
            print("❌ Installation failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
