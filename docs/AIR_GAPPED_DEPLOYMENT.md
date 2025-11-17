# 📦 Air-Gapped Deployment Guide

This guide covers deploying the Enhanced Network API Builder in air-gapped environments without internet connectivity.

## Overview

Air-gapped deployment is designed for:
- **Classified environments** with no external network access
- **High-security environments** that prohibit internet connectivity  
- **Isolated networks** in corporate or government settings
- **Offline development** environments

## Quick Start

### 1. Create Offline Package (Internet-Connected Machine)
```bash
# Clone repository on machine with internet access
git clone https://github.com/your-username/enhanced-network-api-corporate.git
cd enhanced-network-api-corporate

# Create complete air-gapped package
python -m enhanced_network_api.air_gapped_deployment --create

# Package created: enhanced-network-api-airgapped-YYYYMMDD.zip
```

### 2. Transfer to Air-Gapped Environment
```bash
# Transfer package to air-gapped machine via:
# - USB drive, CD/DVD, or approved media
# - Secure file transfer through approved gateway
# - Physical media transfer following security protocols
```

### 3. Install in Air-Gapped Environment
```bash
# Extract and install package
python -m enhanced_network_api.air_gapped_deployment --install enhanced-network-api-airgapped-YYYYMMDD.zip

# Quick setup
cd enhanced-network-api-airgapped
python quick-setup.py

# Verify installation
python verify-integrity.py
```

## Package Contents

### Complete Air-Gapped Package Includes:
- **Core Components**: All Enhanced Network API modules
- **API Documentation**: Complete offline documentation (1,342+ endpoints)
- **Python Dependencies**: All required packages as wheels
- **SSL Certificates**: Bundled corporate certificates
- **Verification Scripts**: SHA256 integrity checking
- **Documentation**: Complete offline guides and examples

### Package Structure:
```
enhanced-network-api-airgapped/
├── src/                           # Core application modules
├── api/                           # Offline API documentation
├── wheels/                        # Python dependency wheels
├── certificates/                  # SSL certificates
├── scripts/                       # Installation and setup scripts
├── docs/                         # Complete documentation
├── install-airgapped.py          # Main installation script
├── verify-integrity.py           # Package integrity verification
├── air-gapped-config.json        # Air-gapped configuration
└── README-AIRGAPPED.md           # Air-gapped specific instructions
```

## Creating Air-Gapped Packages

### Standard Air-Gapped Package
```bash
# Create package with all dependencies
python -m enhanced_network_api.air_gapped_deployment --create --output-dir ./offline-packages
```

### Advanced Package Options
```bash
# Create package with Python interpreter (larger but more complete)
python -m enhanced_network_api.air_gapped_deployment --create --include-python

# Create package for specific platform
python -m enhanced_network_api.air_gapped_deployment --create --platform linux-x86_64

# Create minimal package (core only)
python -m enhanced_network_api.air_gapped_deployment --create --minimal
```

### Custom Package Configuration
```python
from enhanced_network_api.air_gapped_deployment import AirGappedDeployment

deployment = AirGappedDeployment("./custom-airgapped")

# Create package with custom components
package_path = deployment.create_air_gapped_package(
    include_python=True,
    include_documentation=True,
    include_examples=True,
    platform="linux-x86_64"
)

print(f"Custom package created: {package_path}")
```

## Installation in Air-Gapped Environments

### Automated Installation
```bash
# Run main installer (recommended)
python install-airgapped.py

# Follow prompts for configuration options
```

### Manual Installation Steps
```bash
# 1. Set up environment
source air-gapped-environment.sh  # Linux/Mac
# or
air-gapped-environment.bat        # Windows

# 2. Install dependencies from bundled wheels
pip install --no-index --find-links wheels -r requirements-airgapped.txt

# 3. Set up Python path
export PYTHONPATH="${PYTHONPATH}:./src"

# 4. Test installation
python -c "import enhanced_network_api; print('✅ Installation successful')"
```

### Verification and Testing
```bash
# Verify package integrity
python verify-integrity.py

# Test core functionality
python -c "
from src.enhanced_network_api.api_documentation_loader import APIDocumentationLoader
loader = APIDocumentationLoader()
print('✅ API documentation loader functional')
"

# Test SSL helper
python -c "
from src.enhanced_network_api.ssl_helper import CorporateSSLHelper
helper = CorporateSSLHelper()
print('✅ SSL helper functional')
"
```

## Air-Gapped Configuration

### Automatic Air-Gapped Mode
The package automatically detects air-gapped environments and:
- **Disables external API calls** 
- **Uses bundled documentation** instead of downloading
- **Configures offline SSL certificate validation**
- **Enables audit logging** for compliance
- **Disables telemetry** and external reporting

### Configuration File: `air-gapped-config.json`
```json
{
  "deployment_type": "air_gapped",
  "offline_mode": true,
  "ssl_verification": "bundled_certificates", 
  "proxy_enabled": false,
  "external_api_calls": false,
  "audit_logging": true,
  "security_mode": "high",
  "update_check": false,
  "telemetry": false
}
```

### Environment Variables for Air-Gapped Mode
```bash
export AIRGAPPED_MODE=true
export OFFLINE_MODE=true  
export NO_EXTERNAL_CALLS=true
export SSL_CERT_DIR="./certificates"
export API_DOCS_PATH="./api"
```

## Working with Air-Gapped APIs

### API Documentation (Offline)
```python
from enhanced_network_api.api_documentation_loader import APIDocumentationLoader

# Load API documentation from bundled files
loader = APIDocumentationLoader(offline_mode=True)

# FortiManager APIs (342 endpoints)
fortinet_apis = loader.load_fortinet_documentation()
print(f"Loaded {len(fortinet_apis['endpoints'])} FortiManager endpoints")

# Meraki APIs (1000+ endpoints)  
meraki_apis = loader.load_meraki_documentation()
print(f"Loaded {len(meraki_apis['endpoints'])} Meraki endpoints")
```

### Generate Applications (Offline)
```python
from enhanced_network_api.corporate_network_app_generator import CorporateNetworkAppGenerator

# Generate applications using offline API documentation
generator = CorporateNetworkAppGenerator(offline_mode=True)

# Create firewall management app
app_code = generator.create_corporate_firewall_app(
    api_platform="fortinet",
    offline_mode=True
)

print("✅ Firewall management application generated offline")
```

### SSL Certificate Management (Air-Gapped)
```python
from enhanced_network_api.ssl_helper import CorporateSSLHelper

ssl_helper = CorporateSSLHelper(offline_mode=True)

# Use bundled certificates
ssl_helper.configure_bundled_certificates("./certificates")

# Test with bundled CA bundle
session = ssl_helper.create_corporate_session(
    ca_bundle_path="./certificates/ca-bundle.pem"
)
```

## Security Considerations

### Air-Gapped Security Features
- **No External Communications**: Zero network connectivity required
- **Bundled Dependencies**: All packages included, no external downloads
- **Certificate Verification**: All components verified with SHA256 hashes
- **Audit Logging**: Complete audit trail of all operations
- **Minimal Attack Surface**: Only essential components included

### Integrity Verification
```bash
# Verify all package components
python verify-integrity.py

# Expected output:
# ✅ Verified: src/enhanced_network_api/ssl_helper.py
# ✅ Verified: api/fortimanager_api_endpoints.json
# ✅ Verified: wheels/requests-2.28.0-py3-none-any.whl
# 🎉 Package integrity verified!
```

### Security Recommendations
1. **Verify package integrity** before installation
2. **Use checksums** to validate file transfers
3. **Audit all components** before deployment
4. **Enable logging** for compliance requirements
5. **Regular security reviews** of offline packages

## Troubleshooting Air-Gapped Deployments

### Common Issues

**Issue**: Python dependencies missing
```bash
# Solution: Install from bundled wheels
pip install --no-index --find-links wheels -r requirements-airgapped.txt
```

**Issue**: Module import errors
```bash
# Solution: Set Python path
export PYTHONPATH="${PYTHONPATH}:./src"

# Or use installation script
python install-airgapped.py
```

**Issue**: SSL certificate errors
```bash
# Solution: Use bundled certificates
export SSL_CERT_DIR="./certificates"
export REQUESTS_CA_BUNDLE="./certificates/ca-bundle.pem"
```

**Issue**: API documentation not found
```bash
# Solution: Verify API files exist
ls -la api/
# Should show: fortimanager_api_endpoints.json, meraki_dashboard_api.json

# Set API documentation path
export API_DOCS_PATH="./api"
```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug mode for air-gapped deployment
import os
os.environ["AIRGAPPED_DEBUG"] = "true"

from enhanced_network_api.air_gapped_deployment import AirGappedDeployment
```

## Updating Air-Gapped Deployments

### Creating Update Packages
```bash
# Create update package with only changed components
python -m enhanced_network_api.air_gapped_deployment --create-update --from-version 1.0.0

# Create full replacement package
python -m enhanced_network_api.air_gapped_deployment --create --replace-existing
```

### Applying Updates in Air-Gapped Environment
```bash
# Backup current installation
cp -r enhanced-network-api enhanced-network-api-backup

# Apply update package
python apply-airgapped-update.py --package update-package.zip

# Verify update
python verify-integrity.py
```

## Performance Optimization

### Air-Gapped Performance Tips
- **Bundle frequently used APIs** to reduce disk I/O
- **Use local caching** for API documentation
- **Optimize Python path** for faster imports
- **Pre-compile Python bytecode** for faster startup

### Disk Space Management
```bash
# Check package size
du -sh enhanced-network-api-airgapped/

# Typical sizes:
# Standard package: ~50-100 MB
# With Python interpreter: ~200-300 MB
# Minimal package: ~20-30 MB
```

## Compliance and Auditing

### Audit Features
- **Complete operation logging** to audit files
- **SHA256 verification** of all components
- **No external communications** guarantee
- **Compliance reporting** capabilities

### Audit Log Example
```
2024-01-01 10:00:00 INFO Air-gapped mode enabled
2024-01-01 10:00:01 INFO Loading API documentation from ./api/
2024-01-01 10:00:02 INFO SSL certificates loaded from ./certificates/
2024-01-01 10:00:03 INFO Generated firewall application (offline mode)
```

---

**Next**: [Corporate Deployment Guide](CORPORATE_DEPLOYMENT_GUIDE.md)