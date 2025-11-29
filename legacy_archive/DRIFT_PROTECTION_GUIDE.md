# Code Drift Protection Guide

## 🛡️ **Sealed Architecture Overview**

This application now includes comprehensive drift protection to prevent the configuration issues that caused the recent restoration effort.

## **🔧 Protection Layers**

### **1. Version Locking**
- **File**: `requirements.locked.txt`
- **Purpose**: Prevents dependency version changes
- **Usage**: `pip install -r requirements.locked.txt`

### **2. Configuration Validation**
- **File**: `config_validator.py`
- **Purpose**: Validates all critical files and configurations
- **Usage**: `python config_validator.py`

### **3. Startup Health Checks**
- **File**: `startup_health_check.py`
- **Purpose**: Ensures system integrity before startup
- **Usage**: `python startup_health_check.py`

### **4. Automated Testing**
- **File**: `test_drift_protection.py`
- **Usage**: `python test_drift_protection.py`

### **5. Pre-commit Hooks**
- **File**: `pre_commit_hook.py`
- **Purpose**: Blocks commits that break functionality
- **Setup**: Add to `.git/hooks/pre-commit`

### **6. Sealed Deployment**
- **File**: `deploy_sealed.py`
- **Purpose**: Validated deployment with all checks
- **Usage**: `python deploy_sealed.py`

## **🚀 Quick Start (Sealed Deployment)**

### **Option 1: Full Sealed Deployment (Recommended)**
```bash
# One-command validated deployment
python deploy_sealed.py
```

### **Option 2: Manual with Validation**
```bash
# Step 1: Validate configuration
python config_validator.py

# Step 2: Check health
python startup_health_check.py

# Step 3: Start service
source .venv/bin/activate
cd src/enhanced_network_api
python platform_web_api_fastapi.py &

# Step 4: Validate running system
python test_drift_protection.py
```

## **🔍 Validation Commands**

### **Configuration Validation**
```bash
python config_validator.py
```
**Checks:**
- Critical file existence
- Configuration consistency
- API endpoint structure
- Static file integrity
- Environment variables

### **Health Check**
```bash
python startup_health_check.py
```
**Checks:**
- Python version
- Dependencies
- Port availability
- MCP server
- API structure

### **Drift Protection Tests**
```bash
python test_drift_protection.py
```
**Checks:**
- API endpoints (200 status)
- Static pages (critical functions)
- MCP integration
- Topology data structure
- JavaScript integrity

## **⚙️ Git Integration**

### **Setup Pre-commit Hook**
```bash
# Make executable
chmod +x pre_commit_hook.py

# Install as git hook
cp pre_commit_hook.py .git/hooks/pre-commit
```

### **What Gets Blocked**
- Missing critical files
- Broken API endpoints
- Syntax errors
- Configuration drift
- Failed tests

## **📁 Protected Files**

### **Critical Application Files**
```
src/enhanced_network_api/platform_web_api_fastapi.py
src/enhanced_network_api/static/babylon_test.html
src/enhanced_network_api/static/2d_topology_enhanced.html
mcp_servers/drawio_fortinet_meraki/mcp_server.py
```

### **Required Functions**
```javascript
// babylon_test.html MUST contain:
loadFortinetTopology()
renderTopology()
convertMCPToTopologyFormat()
addEventListener('click', loadFortinetTopology)

// 2d_topology_enhanced.html MUST contain:
Enhanced2DTopology class
this.modelSpecificIcons
```

### **Required API Endpoints**
```python
# platform_web_api_fastapi.py MUST contain:
@app.get("/api/topology/scene")
@app.get("/2d-topology-enhanced")
@app.post("/mcp/discover_fortinet_topology")
@app.get("/babylon-test")
```

## **🚨 Common Drift Issues (Now Prevented)**

### **1. Missing Event Listeners**
**Before**: Button clicks not working
**Now**: Validated in `test_drift_protection.py`

### **2. Data Parsing Errors**
**Before**: MCP responses not parsed
**Now**: Validated in integration tests

### **3. Class Scope Issues**
**Before**: `modelSpecificIcons` undefined
**Now**: Validated in syntax checks

### **4. Missing API Endpoints**
**Before**: 404 errors
**Now**: Validated in config validator

### **5. Dependency Version Changes**
**Before**: Breaking updates
**Now**: Locked in `requirements.locked.txt`

## **🔄 Maintenance**

### **Daily Checks**
```bash
python config_validator.py
python test_drift_protection.py
```

### **Before Changes**
```bash
python startup_health_check.py
```

### **After Updates**
```bash
python deploy_sealed.py
```

## **🎯 Best Practices**

### **1. Always Use Sealed Deployment**
```bash
# Instead of manual start
python deploy_sealed.py  # ✅ Validated
# NOT
python platform_web_api_fastapi.py  # ❌ Unvalidated
```

### **2. Commit Through Hooks**
```bash
git add .
git commit -m "changes"  # Will run pre-commit validation
```

### **3. Test After Changes**
```bash
python test_drift_protection.py
```

### **4. Monitor Logs**
```bash
# Check validation logs
tail -f validation.log
```

## **🆘 Troubleshooting**

### **Validation Failed**
1. Run `python config_validator.py` - see specific errors
2. Fix identified issues
3. Re-run validation

### **Deployment Failed**
1. Check `startup_health_check.py` output
2. Verify ports are available
3. Check dependencies

### **Tests Failed**
1. Run `python test_drift_protection.py`
2. Check API endpoints manually
3. Verify static files

## **📊 Success Metrics**

### **Before Drift Protection**
- Configuration drift: Common
- Broken deployments: Frequent
- Manual debugging: Hours
- Unexpected failures: Regular

### **After Drift Protection**
- Configuration drift: Prevented
- Broken deployments: Rare
- Manual debugging: Minutes
- Unexpected failures: Eliminated

## **🎉 Result**

This drift protection system ensures the application remains in a working state by:
- **Validating** every change before deployment
- **Testing** all critical functionality
- **Preventing** configuration drift
- **Ensuring** consistent deployments

**No more "it was working yesterday" issues!**
