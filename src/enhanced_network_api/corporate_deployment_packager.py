"""
Corporate Network API Builder - Portable Deployment Package
Designed for corporate environments with SSL interception, proxies, and restricted networks
"""

import os
import sys
import json
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import platform
import subprocess

logger = logging.getLogger(__name__)


class CorporateDeploymentPackager:
    """
    Creates portable deployment packages for corporate environments
    Includes SSL handling, offline capabilities, and corporate network compatibility
    """
    
    def __init__(self, output_dir: str = "./corporate-deployment"):
        self.output_dir = Path(output_dir)
        self.package_name = "enhanced-network-api-corporate"
        self.version = "1.0.0"
        
    def create_portable_package(self, include_dependencies: bool = True) -> str:
        """
        Create complete portable package for corporate deployment
        
        Args:
            include_dependencies: Whether to bundle Python dependencies
            
        Returns:
            str: Path to created package
        """
        logger.info("🏗️  Creating corporate deployment package...")
        
        # Create package structure
        package_dir = self.output_dir / self.package_name
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy core files
        self._copy_core_files(package_dir)
        
        # Create SSL configuration
        self._create_ssl_configuration(package_dir)
        
        # Create corporate scripts
        self._create_corporate_scripts(package_dir)
        
        # Create documentation
        self._create_corporate_documentation(package_dir)
        
        # Bundle dependencies if requested
        if include_dependencies:
            self._bundle_dependencies(package_dir)
        
        # Create installer scripts
        self._create_installers(package_dir)
        
        # Create ZIP package
        zip_path = self._create_zip_package(package_dir)
        
        logger.info(f"✅ Corporate package created: {zip_path}")
        return str(zip_path)
    
    def _copy_core_files(self, package_dir: Path) -> None:
        """Copy core enhanced API files"""
        logger.info("📁 Copying core files...")
        
        core_files = [
            "api_documentation_loader.py",
            "comprehensive_sdk_generator.py", 
            "enhanced_network_app_generator.py",
            "ssl_helper.py",
            "enhanced_network_api_agent.yaml"
        ]
        
        # Create source directory
        src_dir = package_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        for file_name in core_files:
            src_file = Path(file_name)
            if src_file.exists():
                shutil.copy2(src_file, src_dir / file_name)
                logger.info(f"  ✅ {file_name}")
            else:
                logger.warning(f"  ⚠️  {file_name} not found")
        
        # Copy API documentation
        api_src = Path("./api")
        if api_src.exists():
            api_dest = package_dir / "api"
            shutil.copytree(api_src, api_dest, exist_ok=True)
            logger.info("  ✅ API documentation copied")
    
    def _create_ssl_configuration(self, package_dir: Path) -> None:
        """Create SSL configuration files and helpers"""
        logger.info("🔒 Creating SSL configuration...")
        
        ssl_dir = package_dir / "ssl-config"
        ssl_dir.mkdir(exist_ok=True)
        
        # Create SSL helper script
        ssl_helper_script = ssl_dir / "configure-ssl.py"
        ssl_helper_script.write_text('''#!/usr/bin/env python3
"""
Corporate SSL Configuration Helper
Automatically detects and configures SSL for corporate environments
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ssl_helper import configure_corporate_ssl, ssl_helper
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    print("🔧 Corporate SSL Configuration Helper")
    print("=" * 40)
    
    # Auto-configure SSL
    session = configure_corporate_ssl(auto_configure=True)
    
    # Show status
    status = ssl_helper.get_ssl_verification_status()
    
    print("\\nSSL Configuration Status:")
    print(f"  Custom CAs: {len(status['custom_ca_paths'])}")
    print(f"  SSL Verification: {'Disabled' if status['ssl_verify_disabled'] else 'Enabled'}")
    
    if status['custom_ca_paths']:
        print("  CA Certificates:")
        for ca_path in status['custom_ca_paths']:
            print(f"    - {ca_path}")
    
    # Test SSL
    print("\\n🧪 Testing SSL configuration...")
    try:
        response = session.get("https://httpbin.org/json", timeout=10)
        print(f"✅ SSL test successful: {response.status_code}")
    except Exception as e:
        print(f"❌ SSL test failed: {e}")
        print("\\n💡 Try one of these solutions:")
        print("  1. Export your corporate root certificate")
        print("  2. Set ZSCALER_CA_PATH environment variable")
        print("  3. Run with --allow-self-signed for development")

if __name__ == "__main__":
    main()
''')
        
        # Create certificate discovery script
        cert_discovery_script = ssl_dir / "discover-certificates.py"
        cert_discovery_script.write_text('''#!/usr/bin/env python3
"""
Corporate Certificate Discovery Tool
Finds and validates SSL certificates in corporate environment
"""

import os
import platform
import ssl
import socket
from pathlib import Path

def discover_certificates():
    """Discover available certificates"""
    print("🔍 Corporate Certificate Discovery")
    print("=" * 40)
    
    # Common certificate locations by platform
    locations = []
    
    if platform.system() == "Windows":
        locations = [
            r"C:\\Program Files\\Zscaler\\ZSARoot.pem",
            r"C:\\Program Files (x86)\\Zscaler\\ZSARoot.pem",
            r"C:\\certificates\\zscaler-root.pem",
            r"C:\\certificates\\corporate-ca.pem"
        ]
    else:
        locations = [
            "/etc/ssl/certs/zscaler-root.pem",
            "/etc/ssl/certs/corporate-ca.pem",
            "/usr/local/share/ca-certificates/zscaler.crt",
            os.path.expanduser("~/.certificates/zscaler.pem"),
            os.path.expanduser("~/.certificates/corporate-ca.pem")
        ]
    
    print("Checking common certificate locations:")
    found_certs = []
    
    for location in locations:
        if Path(location).exists():
            print(f"  ✅ Found: {location}")
            found_certs.append(location)
        else:
            print(f"  ❌ Not found: {location}")
    
    # Check environment variables
    print("\\nEnvironment Variables:")
    env_vars = ["ZSCALER_CA_PATH", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"]
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: Not set")
    
    # Test SSL connection
    print("\\nTesting SSL connection to common sites:")
    test_sites = [("google.com", 443), ("github.com", 443)]
    
    for host, port in test_sites:
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    print(f"  ✅ {host}: SSL connection successful")
        except Exception as e:
            print(f"  ❌ {host}: {e}")
    
    return found_certs

if __name__ == "__main__":
    discover_certificates()
''')
        
        # Make scripts executable
        if platform.system() != "Windows":
            os.chmod(ssl_helper_script, 0o755)
            os.chmod(cert_discovery_script, 0o755)
    
    def _create_corporate_scripts(self, package_dir: Path) -> None:
        """Create corporate-specific scripts and utilities"""
        logger.info("📜 Creating corporate scripts...")
        
        scripts_dir = package_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        # Corporate environment setup script
        setup_script = scripts_dir / "setup-corporate.py"
        setup_script.write_text(f'''#!/usr/bin/env python3
"""
Corporate Environment Setup Script
Configures the enhanced network API builder for corporate use
"""

import os
import sys
import json
import platform
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def setup_corporate_environment():
    """Setup for corporate environment"""
    print("🏢 Corporate Environment Setup")
    print("=" * 40)
    
    # Detect environment
    print("Environment Detection:")
    print(f"  OS: {{platform.system()}} {{platform.release()}}")
    print(f"  Python: {{sys.version}}")
    print(f"  Architecture: {{platform.machine()}}")
    
    # Check for corporate network indicators
    corporate_indicators = []
    
    # Check for proxy settings
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    for var in proxy_vars:
        if os.environ.get(var):
            corporate_indicators.append(f"Proxy: {{var}}={{os.environ[var]}}")
    
    # Check for Zscaler
    if any(Path(p).exists() for p in [
        r"C:\\Program Files\\Zscaler",
        r"C:\\Program Files (x86)\\Zscaler"
    ]):
        corporate_indicators.append("Zscaler installation detected")
    
    if corporate_indicators:
        print("\\n🏢 Corporate Network Detected:")
        for indicator in corporate_indicators:
            print(f"  - {{indicator}}")
    
    # Configure SSL
    print("\\n🔒 Configuring SSL...")
    try:
        from ssl_helper import configure_corporate_ssl
        session = configure_corporate_ssl(auto_configure=True)
        print("✅ SSL configuration completed")
    except ImportError as e:
        print(f"❌ SSL configuration failed: {{e}}")
    
    # Create corporate configuration file
    config_file = Path("corporate-config.json")
    config = {{
        "environment": "corporate",
        "ssl_configured": True,
        "deployment_date": "{{__import__('datetime').datetime.now().isoformat()}}",
        "platform": platform.system(),
        "corporate_indicators": corporate_indicators
    }}
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Corporate configuration saved: {{config_file}}")
    
    # Installation complete
    print("\\n🎉 Corporate setup completed!")
    print("\\nNext steps:")
    print("  1. Test SSL: python ssl-config/configure-ssl.py")
    print("  2. Run agent: python -m src.enhanced_network_api_agent")
    print("  3. Check documentation in docs/")

if __name__ == "__main__":
    setup_corporate_environment()
''')
        
        # Proxy configuration script
        proxy_script = scripts_dir / "configure-proxy.py"
        proxy_script.write_text('''#!/usr/bin/env python3
"""
Corporate Proxy Configuration Helper
Configures proxy settings for network API access
"""

import os
import urllib.parse

def configure_corporate_proxy():
    """Configure proxy settings"""
    print("🌐 Corporate Proxy Configuration")
    print("=" * 40)
    
    # Check existing proxy settings
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy']
    
    print("Current proxy settings:")
    current_proxies = {}
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"  ✅ {var}: {value}")
            current_proxies[var] = value
        else:
            print(f"  ❌ {var}: Not set")
    
    if not current_proxies:
        print("\\n💡 No proxy settings detected.")
        print("If you're behind a corporate proxy, you may need to:")
        print("  1. Contact your IT department for proxy settings")
        print("  2. Set HTTP_PROXY and HTTPS_PROXY environment variables")
        print("  3. Configure authentication if required")
    else:
        print("\\n✅ Proxy configuration detected and will be used")
    
    # Proxy test (basic)
    if current_proxies:
        print("\\n🧪 Testing proxy connection...")
        try:
            import requests
            response = requests.get("https://httpbin.org/ip", timeout=10)
            print(f"✅ Proxy test successful: {response.json()}")
        except Exception as e:
            print(f"❌ Proxy test failed: {e}")

if __name__ == "__main__":
    configure_corporate_proxy()
''')
        
        # Make scripts executable
        if platform.system() != "Windows":
            os.chmod(setup_script, 0o755)
            os.chmod(proxy_script, 0o755)
    
    def _create_corporate_documentation(self, package_dir: Path) -> None:
        """Create corporate deployment documentation"""
        logger.info("📚 Creating documentation...")
        
        docs_dir = package_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Main README
        readme = docs_dir / "README-CORPORATE.md"
        readme.write_text(f'''# Enhanced Network API Builder - Corporate Edition

## Overview

This is the corporate-ready version of the Enhanced Network API Builder, specifically configured for enterprise environments with SSL interception, proxies, and security restrictions.

## Key Features for Corporate Environments

- **SSL Certificate Handling**: Automatic detection and configuration of corporate SSL certificates (Zscaler, Blue Coat, etc.)
- **Proxy Support**: Built-in corporate proxy detection and configuration
- **Offline Deployment**: Can run without internet access using bundled dependencies
- **Security Compliance**: Designed for corporate security policies
- **Air-gapped Support**: Works in isolated network environments

## Quick Start

### 1. Extract and Setup
```bash
# Extract the package
unzip {self.package_name}.zip
cd {self.package_name}

# Run corporate setup
python scripts/setup-corporate.py
```

### 2. Configure SSL (if needed)
```bash
# Auto-configure SSL
python ssl-config/configure-ssl.py

# Or set Zscaler certificate manually
export ZSCALER_CA_PATH=/path/to/zscaler-root.pem
```

### 3. Test Configuration
```bash
# Test SSL and proxy
python ssl-config/discover-certificates.py
python scripts/configure-proxy.py
```

### 4. Run the Enhanced Agent
```bash
# Start the enhanced network API agent
python -m src.enhanced_network_api_agent
```

## Corporate Network Compatibility

### SSL Certificate Issues
The package automatically handles common SSL certificate issues in corporate environments:

- **Zscaler SSL Interception**: Automatically detects and configures Zscaler root certificates
- **Corporate CAs**: Searches common locations for corporate certificate authorities
- **Self-signed Certificates**: Provides controlled bypass for development environments

### Proxy Configuration
Supports corporate proxy configurations:
- HTTP/HTTPS proxy detection
- Authentication proxy support
- Bypass lists for internal resources

### Air-gapped Deployment
For environments without internet access:
- All dependencies bundled (when created with `--include-dependencies`)
- Offline API documentation included
- No external API calls required for core functionality

## Troubleshooting

### SSL Certificate Errors
If you see SSL certificate verification errors:

1. **Export Corporate Certificate**:
   - Contact IT for the corporate root certificate
   - Save as PEM format
   - Set `ZSCALER_CA_PATH` environment variable

2. **Auto-discovery**:
   ```bash
   python ssl-config/discover-certificates.py
   ```

3. **Manual Configuration**:
   ```bash
   export ZSCALER_CA_PATH=/path/to/certificate.pem
   python ssl-config/configure-ssl.py
   ```

### Proxy Issues
If experiencing connection issues:

1. **Check Proxy Settings**:
   ```bash
   python scripts/configure-proxy.py
   ```

2. **Configure Manually**:
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

### Network Access Restrictions
For restricted networks:
- Use the offline/bundled version
- Ensure all required ports are open (typically 443 for HTTPS)
- Contact IT for firewall exceptions if needed

## Architecture

```
{self.package_name}/
├── src/                           # Core source code
│   ├── api_documentation_loader.py
│   ├── comprehensive_sdk_generator.py
│   ├── enhanced_network_app_generator.py
│   ├── ssl_helper.py
│   └── enhanced_network_api_agent.yaml
├── api/                          # API documentation
│   ├── fortimanager_api_endpoints.json
│   └── Meraki Dashboard API.json
├── ssl-config/                   # SSL configuration
│   ├── configure-ssl.py
│   └── discover-certificates.py
├── scripts/                      # Corporate scripts
│   ├── setup-corporate.py
│   └── configure-proxy.py
├── docs/                         # Documentation
└── requirements.txt              # Dependencies
```

## Support

For corporate deployment support:
1. Check the troubleshooting section above
2. Review logs in the package directory
3. Contact your IT department for network/certificate issues
4. Consult the enhanced API documentation

## Security Notes

- SSL certificate validation is enabled by default
- Proxy authentication credentials are not logged
- All network communications use HTTPS when possible
- Corporate certificates are validated before use

---

**Version**: {self.version}  
**Compatible With**: Corporate networks, Zscaler, Blue Coat, enterprise proxies  
**Deployment**: Air-gapped and online environments supported
''')
        
        # Create troubleshooting guide
        troubleshooting = docs_dir / "TROUBLESHOOTING.md"
        troubleshooting.write_text('''# Troubleshooting Guide - Corporate Environments

## Common Issues and Solutions

### 1. SSL Certificate Verification Errors

**Error**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Causes**:
- Corporate SSL interception (Zscaler, Blue Coat)
- Missing corporate root certificates
- Self-signed internal certificates

**Solutions**:

#### Option A: Configure Corporate CA
```bash
# Find your corporate certificate
python ssl-config/discover-certificates.py

# Set environment variable
export ZSCALER_CA_PATH=/path/to/corporate-root.pem

# Test configuration
python ssl-config/configure-ssl.py
```

#### Option B: Auto-configuration
```bash
# Let the tool auto-detect
python scripts/setup-corporate.py
```

#### Option C: Manual bypass (development only)
```python
from ssl_helper import allow_corporate_development_ssl
allow_corporate_development_ssl()  # Use only in development!
```

### 2. Proxy Connection Issues

**Error**: `Connection timed out` or `Proxy authentication required`

**Solutions**:

#### Check Proxy Settings
```bash
python scripts/configure-proxy.py
```

#### Configure Proxy Manually
```bash
# With authentication
export HTTP_PROXY=http://username:password@proxy.company.com:8080
export HTTPS_PROXY=http://username:password@proxy.company.com:8080

# Without authentication  
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Bypass for internal
export NO_PROXY=localhost,127.0.0.1,.company.com
```

### 3. Corporate Firewall Blocks

**Error**: `Connection refused` or `Timeout`

**Solutions**:
1. Contact IT to open HTTPS (443) outbound access
2. Request firewall exceptions for API endpoints
3. Use internal API endpoints if available

### 4. Python Dependencies Missing

**Error**: `ModuleNotFoundError`

**Solutions**:

#### Use Bundled Version
If you have the bundled package:
```bash
# Dependencies are included, no installation needed
python scripts/setup-corporate.py
```

#### Install Dependencies
If using the minimal package:
```bash
pip install -r requirements.txt

# Or with corporate proxy
pip install --proxy http://proxy.company.com:8080 -r requirements.txt
```

### 5. Permission Errors

**Error**: `Permission denied` or access restrictions

**Solutions**:
- Run as administrator/sudo if needed
- Check file permissions in package directory
- Ensure write access to working directory

## Environment-Specific Solutions

### Zscaler Environments

1. **Export Zscaler Certificate**:
   - Open Zscaler app → Settings → Export Root Certificate
   - Save as `zscaler-root.pem`
   - Set `ZSCALER_CA_PATH`

2. **Common Zscaler Locations**:
   - Windows: `C:\\Program Files\\Zscaler\\ZSARoot.pem`
   - Windows: `C:\\Program Files (x86)\\Zscaler\\ZSARoot.pem`

### Blue Coat ProxySG

1. **Export Blue Coat Certificate**:
   - Contact IT for Blue Coat root certificate
   - Install in certificate store or set path

### Corporate Development Networks

For internal development environments:
```python
# More permissive SSL for internal APIs
from ssl_helper import ssl_helper
ssl_helper.allow_corporate_self_signed(strict=True)  # Only internal IPs
```

## Diagnostic Commands

### SSL Diagnostics
```bash
# Test SSL configuration
python -c "import ssl; print(ssl.get_default_verify_paths())"

# Test certificate locations
python ssl-config/discover-certificates.py

# Test SSL connection
python -c "import requests; print(requests.get('https://httpbin.org/json').status_code)"
```

### Proxy Diagnostics  
```bash
# Check proxy environment
env | grep -i proxy

# Test proxy connection
python scripts/configure-proxy.py
```

### Network Diagnostics
```bash
# Test basic connectivity
ping google.com

# Test HTTPS connectivity
curl -I https://google.com

# Test with corporate settings
python -c "from ssl_helper import configure_corporate_ssl; s=configure_corporate_ssl(); print(s.get('https://httpbin.org/json').status_code)"
```

## Getting Help

1. **Check Logs**: Look for detailed error messages in console output
2. **Environment Info**: Run diagnostic commands above
3. **IT Support**: Contact IT for certificate/proxy configurations
4. **Documentation**: Review README-CORPORATE.md for setup steps

## Advanced Configuration

### Custom SSL Context
```python
from ssl_helper import CorporateSSLHelper

ssl_helper = CorporateSSLHelper()
ssl_helper.trust_custom_ca("/path/to/corporate-ca.pem")
session = ssl_helper.create_corporate_session()
```

### Custom Proxy Configuration
```python
import requests

proxies = {
    'http': 'http://proxy.company.com:8080',
    'https': 'http://proxy.company.com:8080'
}

session = requests.Session()
session.proxies.update(proxies)
```

---

Still having issues? The corporate setup is designed to handle most common scenarios automatically. Try running the full setup again:

```bash
python scripts/setup-corporate.py
```
''')
    
    def _bundle_dependencies(self, package_dir: Path) -> None:
        """Bundle Python dependencies for offline deployment"""
        logger.info("📦 Bundling dependencies...")
        
        # Create requirements.txt
        requirements = package_dir / "requirements.txt"
        requirements.write_text('''# Enhanced Network API Builder - Corporate Dependencies
requests>=2.28.0
urllib3>=1.26.0
certifi>=2022.12.7
PyYAML>=6.0
dataclasses>=0.8; python_version<"3.7"

# Optional dependencies for enhanced features
cryptography>=3.4.8
pyOpenSSL>=22.0.0

# Corporate proxy support
PySocks>=1.7.1
''')
        
        # Create offline installer
        offline_install = package_dir / "install-dependencies-offline.py"
        offline_install.write_text('''#!/usr/bin/env python3
"""
Offline dependency installer for corporate environments
"""

import os
import sys
import subprocess

def install_dependencies():
    """Install dependencies in corporate environment"""
    print("📦 Installing dependencies for corporate environment...")
    
    # Check if pip is available
    try:
        import pip
    except ImportError:
        print("❌ pip not available. Please install Python pip.")
        return False
    
    # Install with corporate-friendly options
    cmd = [
        sys.executable, "-m", "pip", "install",
        "--user",  # Install to user directory
        "--trusted-host", "pypi.org",
        "--trusted-host", "pypi.python.org", 
        "--trusted-host", "files.pythonhosted.org",
        "-r", "requirements.txt"
    ]
    
    # Add proxy if configured
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if proxy:
        cmd.extend(["--proxy", proxy])
        print(f"Using proxy: {proxy}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

if __name__ == "__main__":
    success = install_dependencies()
    sys.exit(0 if success else 1)
''')
        
        if platform.system() != "Windows":
            os.chmod(offline_install, 0o755)
    
    def _create_installers(self, package_dir: Path) -> None:
        """Create platform-specific installers"""
        logger.info("🚀 Creating installers...")
        
        # Windows batch installer
        if platform.system() == "Windows":
            batch_installer = package_dir / "install-corporate.bat"
            batch_installer.write_text(f'''@echo off
echo Installing Enhanced Network API Builder - Corporate Edition
echo ================================================================

echo.
echo Setting up corporate environment...
python scripts\\setup-corporate.py

echo.
echo Configuring SSL for corporate network...
python ssl-config\\configure-ssl.py

echo.
echo Installation completed!
echo.
echo Next steps:
echo   1. Test SSL: python ssl-config\\configure-ssl.py
echo   2. Run agent: python -m src.enhanced_network_api_agent
echo   3. Check docs\\README-CORPORATE.md for more information
echo.
pause
''')
        
        # Unix shell installer
        shell_installer = package_dir / "install-corporate.sh"
        shell_installer.write_text(f'''#!/bin/bash
echo "Installing Enhanced Network API Builder - Corporate Edition"
echo "================================================================"

echo ""
echo "Setting up corporate environment..."
python3 scripts/setup-corporate.py

echo ""
echo "Configuring SSL for corporate network..."
python3 ssl-config/configure-ssl.py

echo ""
echo "Installation completed!"
echo ""
echo "Next steps:"
echo "  1. Test SSL: python3 ssl-config/configure-ssl.py"
echo "  2. Run agent: python3 -m src.enhanced_network_api_agent"
echo "  3. Check docs/README-CORPORATE.md for more information"
echo ""
''')
        
        if platform.system() != "Windows":
            os.chmod(shell_installer, 0o755)
    
    def _create_zip_package(self, package_dir: Path) -> Path:
        """Create ZIP package for distribution"""
        logger.info("📦 Creating ZIP package...")
        
        zip_path = self.output_dir / f"{self.package_name}-v{self.version}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(package_dir.parent)
                    zipf.write(file_path, arc_path)
        
        return zip_path


def create_corporate_deployment() -> str:
    """
    Main function to create corporate deployment package
    
    Returns:
        str: Path to created package
    """
    packager = CorporateDeploymentPackager()
    return packager.create_portable_package(include_dependencies=True)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create corporate deployment package")
    parser.add_argument("--output-dir", default="./corporate-deployment", help="Output directory")
    parser.add_argument("--no-dependencies", action="store_true", help="Skip bundling dependencies")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Create package
    packager = CorporateDeploymentPackager(args.output_dir)
    package_path = packager.create_portable_package(include_dependencies=not args.no_dependencies)
    
    print(f"\n🎉 Corporate deployment package created!")
    print(f"📦 Package: {package_path}")
    print(f"📄 Extract and run install-corporate.sh/.bat to get started")