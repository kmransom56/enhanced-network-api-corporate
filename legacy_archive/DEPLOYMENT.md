# Network Observability Platform Deployment Guide

## Overview
This platform provides enterprise-grade network observability without commercial licensing costs. It combines:
- Real-time network topology visualization (2D/3D)
- Intelligent troubleshooting with custom Fortinet LLM
- Cross-platform analysis (Fortinet + Meraki)
- Smart policy analysis and incident triage
- Change management and configuration drift detection

## Architecture

```mermaid
graph TD
    A[Development Machine] --> B[Corporate Deployment]
    
    subgraph "Development"
        C[Enhanced Network API]
        D[Custom Fortinet LLM]
        E[MCP Servers]
        F[Local Testing]
    end
    
    subgraph "Corporate"
        G[Docker Containers]
        H[Production Database]
        I[Corporate Network Access]
        J[Team Sharing]
    end
    
    C --> G
    D --> G
    E --> G
    F --> J
```

## Development Setup (Current Machine)

### Prerequisites
```bash
# Python environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Optional: python-dotenv for configuration
pip install python-dotenv
```

### Configuration
```bash
# Copy template and configure
cp .env.template .env
# Edit .env with your development credentials
```

### Local Development
```bash
# Start the platform
cd /home/keith/enhanced-network-api-corporate
source venv/bin/activate
python src/enhanced_network_api/platform_web_api_fastapi.py

# Access: http://127.0.0.1:11111
```

## Corporate Deployment Strategy

### Option 1: Docker Deployment (Recommended)

#### Build Docker Image
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env.template .env.template

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 11111

CMD ["python", "src/enhanced_network_api/platform_web_api_fastapi.py"]
```

#### Docker Compose for Corporate
```yaml
# docker-compose.corporate.yml
version: '3.8'

services:
  enhanced-network-api:
    build: .
    ports:
      - "11111:11111"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=11111
      - LOG_LEVEL=INFO
    volumes:
      - ./corporate.env:/app/.env
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    
  # Optional: PostgreSQL for production
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: enhanced_network
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    
  # Optional: Redis for caching
  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

### Option 2: Portable Python Package

#### Create Installable Package
```bash
# Setup for packaging
pip install build twine

# Build the package
python -m build

# Creates dist/ directory with .whl file
```

#### Corporate Installation
```bash
# On corporate machine
python -m venv enhanced-network-env
source enhanced-network-env/bin/activate

# Install from package
pip install enhanced_network_api-1.0.0-py3-none-any.whl

# Configure environment
cp enhanced_network_api/.env.template .env
# Edit with corporate credentials

# Run service
enhanced-network-api --port 11111 --host 0.0.0.0
```

## Corporate Environment Setup

### 1. Network Access Requirements
- **FortiGate Access**: HTTPS (port 10443) to management interfaces
- **Meraki API**: HTTPS (port 443) to api.meraki.com
- **LLM Server**: HTTP to your custom Fortinet model endpoint
- **Team Access**: HTTP/HTTPS to the application port

### 2. Security Considerations
- Use corporate-approved ports (e.g., 8443 instead of 11111)
- Implement SSL/TLS termination
- Use corporate authentication if available
- Secure credential management

### 3. Corporate Configuration Template
```bash
# corporate.env.template
# Network Configuration
API_HOST=0.0.0.0
API_PORT=8443
API_CORS_ORIGINS=https://your-corp-domain.com

# FortiGate Devices (corporate)
FORTIGATE_HOSTS=192.168.1.1,10.0.0.1
FORTIGATE_192_168_1_1_TOKEN=corporate_token_1
FORTIGATE_10_0_0_1_TOKEN=corporate_token_2

# Meraki Configuration
MERAKI_API_KEY=corporate_meraki_key
MERAKI_ORG_ID=corporate_org_id

# LLM Configuration
LLM_BASE_URL=http://your-llm-server:11434

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://appuser:password@postgres:5432/enhanced_network

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/enhanced-network.log
```

## Team Sharing Setup

### 1. Multi-User Access
```python
# Add to platform_web_api_fastapi.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    # Simple corporate user validation
    valid_users = {
        "team.member1": "password1",
        "team.member2": "password2",
        # Add team members
    }
    
    if credentials.username in valid_users and secrets.compare_digest(credentials.password, valid_users[credentials.username]):
        return credentials.username
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

# Protect endpoints
@app.get("/api/topology/scene")
async def get_topology_scene(user: str = Depends(get_current_user)):
    # Existing implementation
    pass
```

### 2. Team Dashboard Features
- **Shared Views**: Custom topology layouts
- **Collaborative Troubleshooting**: Shared sessions
- **Knowledge Base**: Store runbooks and solutions
- **Alert Sharing**: Team notifications

## Deployment Checklist

### Pre-Deployment
- [ ] Test all API endpoints with corporate credentials
- [ ] Verify LLM integration works in corporate network
- [ ] Test MCP server connectivity
- [ ] Validate security configurations
- [ ] Create backup/restore procedures

### Deployment Steps
1. **Package Application**: Build Docker image or Python package
2. **Configure Environment**: Set up corporate.env with actual credentials
3. **Deploy Infrastructure**: Run Docker containers or install package
4. **Test Connectivity**: Verify all external integrations
5. **Team Onboarding**: Add user accounts and provide access

### Post-Deployment
- [ ] Monitor application logs
- [ ] Set up log rotation
- [ ] Configure backup schedules
- [ ] Document team procedures
- [ ] Plan for updates/maintenance

## Cost Comparison

### Commercial Solutions (Annual)
- **SolarWinds Network Performance Monitor**: $2,999 - $12,999
- **PRTG Network Monitor**: $1,600 - $14,500
- **ManageEngine OpManager**: $711 - $10,995
- **Datadog Network Monitoring**: $21 - $23+ per host/month

### This Platform (Annual)
- **Development Time**: Your time investment
- **Infrastructure**: Existing corporate servers
- **LLM Costs**: Your custom model (already developed)
- **MCP Servers**: Open source components
- **Total**: ~$0 additional licensing costs

## Value Proposition

### For You
- **Portfolio Enhancement**: Enterprise-grade network observability platform
- **Skill Development**: Full-stack development with modern tech
- **Problem Solving**: Real business value for your organization

### For Your Company
- **Cost Savings**: $10K+ annual licensing savings
- **Customization**: Tailored to your specific network environment
- **No Vendor Lock-in**: Full control over features and data
- **Team Collaboration**: Shared knowledge and troubleshooting

### For Your Team
- **Better Visibility**: Real-time network topology and health
- **Faster Troubleshooting**: AI-powered incident analysis
- **Consistent Processes**: Standardized runbooks and procedures
- **Knowledge Sharing**: Centralized network expertise

## Next Steps

1. **Complete Development**: Finish any remaining features
2. **Corporate Testing**: Set up test environment with corporate credentials
3. **Team Demo**: Show value to teammates and management
4. **Production Deployment**: Roll out to corporate environment
5. **Continuous Improvement**: Add features based on team feedback

This platform positions you as a technical leader while delivering significant business value to your organization.
