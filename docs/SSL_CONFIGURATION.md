# 🔒 SSL Configuration for Corporate Environments

This guide covers SSL certificate configuration for corporate networks with SSL interception (Zscaler, Blue Coat, etc.).

## Quick Setup

### Auto-Configuration (Recommended)
```bash
# Auto-discover and configure corporate SSL certificates
python -m enhanced_network_api.ssl_helper --auto-configure

# Or use certificate discovery
python -m enhanced_network_api.certificate_discovery --discover --export-zscaler
```

### Manual Configuration
```bash
# Set certificate environment variable
export ZSCALER_CA_PATH=/path/to/zscaler-root.pem
export REQUESTS_CA_BUNDLE=/path/to/zscaler-root.pem

# Test SSL configuration
python -m enhanced_network_api.ssl_helper --test
```

## Corporate SSL Challenges

### Problem: SSL Certificate Verification Failed
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Cause**: Corporate networks often use SSL interception appliances (Zscaler, Blue Coat) that present their own certificates instead of the original server certificates.

**Solution**: Configure applications to trust the corporate root certificate.

### Problem: Certificate Not Found
```
No SSL certificates found automatically
```

**Cause**: Corporate certificates may be stored in non-standard locations or require manual export.

**Solutions**:
1. Use automatic discovery: `certificate_discovery --discover`
2. Manual export from corporate software
3. Contact IT department for certificate files

## Certificate Discovery

### Automatic Discovery
The certificate discovery system checks:

- **Environment Variables**: `ZSCALER_CA_PATH`, `CORPORATE_CA_PATH`, etc.
- **File System Locations**: Common certificate directories
- **System Certificate Store**: Windows/Linux certificate stores  
- **Network Analysis**: Detect SSL interception by testing connections
- **Corporate Software**: Check for Zscaler, Blue Coat installations

```python
from enhanced_network_api.certificate_discovery import auto_discover_corporate_certificates

# Run automatic discovery
results = auto_discover_corporate_certificates()
print(f"Found {len(results['certificates_found'])} certificates")
```

### Manual Certificate Export

#### Zscaler
1. Open Zscaler client application
2. Go to Settings → Advanced → Export Root Certificate  
3. Save as PEM format
4. Set `ZSCALER_CA_PATH` environment variable

#### Blue Coat ProxySG
1. Access Blue Coat management interface
2. Navigate to Configuration → SSL → Certificates
3. Export root CA certificate
4. Convert to PEM format if necessary

#### Windows Certificate Store
```bash
# Export certificate from Windows store
certlm.msc → Trusted Root Certification Authorities → Certificates
# Right-click corporate certificate → All Tasks → Export → Base-64 encoded X.509
```

## SSL Helper Usage

### Basic Usage
```python
from enhanced_network_api.ssl_helper import CorporateSSLHelper

ssl_helper = CorporateSSLHelper()

# Auto-configure SSL
ssl_helper.auto_configure_corporate_ssl()

# Create SSL-aware session
session = ssl_helper.create_corporate_session()
response = session.get("https://api.example.com")
```

### Advanced Configuration
```python
# Custom certificate path
ssl_helper.trust_zscaler_ca("/path/to/corporate-cert.pem")

# Test SSL configuration
test_results = ssl_helper.test_ssl_configuration()
print(f"SSL test passed: {test_results['success']}")

# Bypass SSL for development (not recommended for production)
session = ssl_helper.create_session_with_ssl_bypass()
```

## Environment Variables

Set these environment variables for SSL configuration:

```bash
# Primary certificate path
export ZSCALER_CA_PATH="/path/to/zscaler-root.pem"

# Alternative certificate paths
export CORPORATE_CA_PATH="/path/to/corporate-ca.pem"
export REQUESTS_CA_BUNDLE="/path/to/ca-bundle.pem"
export SSL_CERT_FILE="/path/to/cert-file.pem"
export SSL_CERT_DIR="/path/to/cert-directory"

# Disable SSL verification (development only)
export PYTHONHTTPSVERIFY=0  # Not recommended
```

## Testing SSL Configuration

### Command Line Testing
```bash
# Test SSL configuration
python -m enhanced_network_api.ssl_helper --test

# Test specific URL
python -m enhanced_network_api.ssl_helper --test --url https://api.github.com

# Validate certificate chain
python -m enhanced_network_api.ssl_helper --validate /path/to/certificate.pem
```

### Programmatic Testing
```python
from enhanced_network_api.ssl_helper import test_ssl_configuration

# Test SSL with corporate certificates
results = test_ssl_configuration([
    "https://httpbin.org",
    "https://api.github.com",
    "https://www.google.com"
])

for url, result in results.items():
    status = "✅" if result["success"] else "❌"
    print(f"{status} {url}: {result['status']}")
```

## Troubleshooting

### Common Issues

**Issue**: `SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]`
```bash
# Solution 1: Auto-configure
python -m enhanced_network_api.ssl_helper --auto-configure

# Solution 2: Set certificate path
export ZSCALER_CA_PATH=/path/to/certificate.pem

# Solution 3: Disable verification (temporary, not recommended)
export PYTHONHTTPSVERIFY=0
```

**Issue**: Certificate file not found
```bash
# Find certificates automatically
python -m enhanced_network_api.certificate_discovery --discover

# Search common locations
find /etc/ssl /usr/local/share -name "*zscaler*" -o -name "*corporate*" 2>/dev/null
```

**Issue**: Wrong certificate format
```bash
# Convert DER to PEM
openssl x509 -inform DER -outform PEM -in certificate.der -out certificate.pem

# Verify certificate format
openssl x509 -in certificate.pem -text -noout
```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from enhanced_network_api.ssl_helper import CorporateSSLHelper
ssl_helper = CorporateSSLHelper()
ssl_helper.auto_configure_corporate_ssl()  # Will show debug output
```

## Production Deployment

### Best Practices
1. **Always use proper certificates** in production
2. **Never disable SSL verification** in production
3. **Test thoroughly** in corporate environment before deployment
4. **Use environment variables** for certificate paths
5. **Monitor certificate expiration** dates

### Docker Deployment
```dockerfile
FROM python:3.10

# Copy corporate certificates
COPY corporate-certificates/ /etc/ssl/corporate/

# Set certificate environment
ENV ZSCALER_CA_PATH=/etc/ssl/corporate/zscaler-root.pem
ENV REQUESTS_CA_BUNDLE=/etc/ssl/corporate/ca-bundle.pem

# Install application
COPY . /app
WORKDIR /app
RUN pip install -e .

CMD ["enhanced-network-api"]
```

### System Service
```bash
# Create systemd service with SSL environment
cat > /etc/systemd/system/enhanced-network-api.service << EOF
[Unit]
Description=Enhanced Network API Corporate
After=network.target

[Service]
Type=simple
User=api-user
Environment=ZSCALER_CA_PATH=/etc/ssl/corporate/zscaler-root.pem
Environment=PYTHONPATH=/opt/enhanced-network-api
ExecStart=/opt/enhanced-network-api/bin/enhanced-network-api
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable enhanced-network-api
systemctl start enhanced-network-api
```

## Support

For SSL configuration issues:
1. Run automatic discovery: `certificate_discovery --discover`
2. Check debug output: Set `logging.DEBUG`
3. Test configuration: `ssl_helper --test`
4. Contact IT department for corporate certificate access

---

**Next**: [Network Troubleshooting Guide](NETWORK_TROUBLESHOOTING.md)