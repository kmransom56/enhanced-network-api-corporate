# 🔌 Complete API Specification for FortiGate + Meraki Application

## 📋 Overview

This document contains **all required API requests** for your FortiGate + Meraki intelligent topology application. These APIs power the MCP server, LLM integration, 3D visualization, and DrawIO diagram generation.

---

## 🏰 FortiGate REST API v2

### Base Configuration
```
Base URL: https://192.168.0.254:10443/api/v2/
Authentication: Bearer token
Token Source: FORTIGATE_192_168_0_254_TOKEN
Username: !cg@RW%G@o
SSL Verify: false (self-signed certs)
```

### Required API Endpoints

#### 1. System Status
**Request:**
```http
GET /api/v2/cmdb/system/status
Authorization: Bearer 679Nf51c76p7z1Qq6sqhhz8nghmnpN
```

**Response Schema:**
```json
{
  "hostname": "fg-192-168-0-254",
  "serial": "FG600E321X5901234",
  "version": "v7.4.0",
  "build": 3596,
  "model": "FG600E"
}
```

**Usage:** Device identification, firmware version, model detection

#### 2. Network Interfaces
**Request:**
```http
GET /api/v2/cmdb/system/interface
Authorization: Bearer 679Nf51c76p7z1Qq6sqhhz8nghmnpN
```

**Response Schema:**
```json
{
  "results": [
    {
      "name": "wan1",
      "ip": "203.0.113.1",
      "subnet": "255.255.255.0",
      "status": "up",
      "speed": "1Gbps",
      "mtu": 1500
    },
    {
      "name": "lan1",
      "ip": "192.168.0.254",
      "subnet": "255.255.255.0",
      "status": "up",
      "speed": "1Gbps"
    }
  ]
}
```

**Usage:** Network topology mapping, interface status monitoring

#### 3. Resource Usage
**Request:**
```http
GET /api/v2/monitor/system/resource/usage
Authorization: Bearer 679Nf51c76p7z1Qq6sqhhz8nghmnpN
```

**Response Schema:**
```json
{
  "results": [
    {
      "cpu_usage": 15.2,
      "memory_usage": 42.8,
      "current_sessions": 1250,
      "disk_usage": 23.1
    }
  ]
}
```

**Usage:** Performance metrics, health monitoring, alerting

#### 4. Firewall Policies
**Request:**
```http
GET /api/v2/cmdb/firewall/policy
Authorization: Bearer 679Nf51c76p7z1Qq6sqhhz8nghmnpN
```

**Response Schema:**
```json
{
  "results": [
    {
      "policyid": 1,
      "name": "LAN to WAN",
      "srcintf": "lan1",
      "dstintf": "wan1",
      "srcaddr": "all",
      "dstaddr": "all",
      "service": "ALL",
      "action": "accept",
      "status": "enabled"
    }
  ]
}
```

**Usage:** Security topology, policy visualization, compliance reporting

#### 5. Virtual IPs (VIP)
**Request:**
```http
GET /api/v2/cmdb/firewall/vip
Authorization: Bearer 679Nf51c76p7z1Qq6sqhhz8nghmnpN
```

**Response Schema:**
```json
{
  "results": [
    {
      "name": "web_server_vip",
      "type": "static-nat",
      "extip": "203.0.113.10",
      "extintf": "wan1",
      "mappedip": "192.168.0.10",
      "port": "80"
    }
  ]
}
```

**Usage:** NAT mapping, service discovery, external access points

---

## 🌐 Meraki Dashboard API v1

### Base Configuration
```
Base URL: https://api.meraki.com/api/v1
Authentication: X-Cisco-Meraki-API-Key header
API Key: MERAKI_API_KEY (currently disabled)
Rate Limit: 5 requests/second/organization
```

### Required API Endpoints

#### 1. Organizations
**Request:**
```http
GET /organizations
X-Cisco-Meraki-API-Key: your_meraki_api_key
```

**Response Schema:**
```json
[
  {
    "id": "123456",
    "name": "Corporate Network",
    "url": "https://dashboard.meraki.com/o/123456/manage"
  }
]
```

**Usage:** Organization discovery, hierarchy mapping

#### 2. Organization Networks
**Request:**
```http
GET /organizations/123456/networks
X-Cisco-Meraki-API-Key: your_meraki_api_key
```

**Response Schema:**
```json
[
  {
    "id": "N_123456",
    "name": "Main Office",
    "productTypes": ["switch", "wireless", "appliance"],
    "timeZone": "America/Los_Angeles"
  }
]
```

**Usage:** Network inventory, device grouping

#### 3. Organization Devices
**Request:**
```http
GET /organizations/123456/devices
X-Cisco-Meraki-API-Key: your_meraki_api_key
```

**Response Schema:**
```json
[
  {
    "name": "Main-Office-Switch-1",
    "serial": "Q2XX-XXXX-XXXX",
    "model": "MS225-48",
    "productType": "switch",
    "status": "online"
  }
]
```

**Usage:** Device discovery, status monitoring

#### 4. Switch Ports
**Request:**
```http
GET /devices/Q2XX-XXXX-XXXX/switch/ports
X-Cisco-Meraki-API-Key: your_meraki_api_key
```

**Response Schema:**
```json
[
  {
    "number": 1,
    "name": "Uplink",
    "type": "access",
    "status": "connected",
    "enabled": true
  }
]
```

**Usage:** Port mapping, connection topology

#### 5. Wireless Access Points
**Request:**
```http
GET /networks/N_123456/devices?productTypes=wireless
X-Cisco-Meraki-API-Key: your_meraki_api_key
```

**Response Schema:**
```json
[
  {
    "name": "AP-Office-1",
    "serial": "Q2XX-XXXX-XXXX",
    "model": "MR42",
    "productType": "wireless",
    "status": "online"
  }
]
```

**Usage:** Wireless topology, coverage mapping

---

## 🤖 LLM Integration APIs

### Ollama API Configuration
```
Base URL: http://localhost:11434/api/generate
Model: fortinet-custom
Timeout: 30 seconds
Temperature: 0.7
Max Tokens: 2048
```

### API Request Format
**Request:**
```http
POST /api/generate
Content-Type: application/json

{
  "model": "fortinet-custom",
  "prompt": "Generate API request for system status",
  "stream": false,
  "options": {
    "temperature": 0.1,
    "max_tokens": 500
  }
}
```

**Response Schema:**
```json
{
  "model": "fortinet-custom",
  "created_at": "2025-01-22T17:00:00Z",
  "response": "{\"method\": \"GET\", \"url\": \"/api/v2/cmdb/system/status\"}",
  "done": true
}
```

### CodeLlama Alternative
```
Model Path: /home/keith/chat-copilot/fortinet-meraki-llm/models/codellama-7b_fortinet_meraki_cpu_20251106_062854
Purpose: Future code generation and configuration assistance
Integration: Planned for v2.0
```

---

## 🔧 MCP Server Tools API

### Tool 1: collect_topology
**Input:**
```json
{
  "refresh": true,
  "device_types": ["fortigate", "meraki"]
}
```

**Output:**
```json
{
  "topology": {
    "devices": [...],
    "links": [...],
    "metadata": {
      "total_devices": 3,
      "total_links": 2,
      "source": "fortigate_api"
    }
  }
}
```

### Tool 2: generate_drawio_diagram
**Input:**
```json
{
  "layout": "hierarchical",
  "group_by": "type",
  "color_code": true
}
```

**Output:**
```xml
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- Device nodes and edges -->
  </root>
</mxGraphModel>
```

### Tool 3: query_api_documentation
**Input:**
```json
{
  "query": "system status monitoring",
  "device_type": "fortigate"
}
```

**Output:**
```json
{
  "query": "system status monitoring",
  "device_type": "fortigate",
  "results": [
    {
      "name": "system_status",
      "method": "GET",
      "path": "/api/v2/cmdb/system/status",
      "relevance_score": 3
    }
  ]
}
```

### Tool 4: generate_api_request
**Input:**
```json
{
  "query": "Show system status and resource usage",
  "device_info": {
    "type": "fortigate",
    "ip": "192.168.0.254",
    "model": "FG600E"
  },
  "device_type": "fortigate"
}
```

**Output:**
```json
{
  "generated_request": {
    "method": "GET",
    "url": "/api/v2/cmdb/system/status",
    "headers": {"Authorization": "Bearer <token>"},
    "confidence": 0.95
  }
}
```

---

## 🎮 3D Topology Integration APIs

### Fortinet HTTP Bridge
```
Service: FastAPI application
URL: http://127.0.0.1:11110
Purpose: API proxying and authentication
Endpoints:
- POST /fortigate/status - Proxy system status
- POST /fortigate/interfaces - Proxy interface data
- POST /fortigate/policies - Proxy firewall policies
```

### Enhanced Network API
```
Service: FastAPI web application
URL: http://0.0.0.0:11111
Purpose: 3D topology data and web UI
Endpoints:
- GET /api/topology/scene - Three.js topology data
- GET /api/topology/devices - Device list
- GET /api/topology/links - Connection data
- WebSocket /ws/topology - Real-time updates
```

### Topology Scene API
**Request:**
```http
GET /api/topology/scene
Accept: application/json
```

**Response Schema:**
```json
{
  "scene": {
    "nodes": [
      {
        "id": "fg-192-168-0-254",
        "type": "fortigate",
        "position": {"x": 0, "y": 0, "z": 0},
        "model": "FG600E",
        "status": "active",
        "icon": "/static/fortinet-icons/FortiGate.svg"
      }
    ],
    "edges": [
      {
        "source": "fg-192-168-0-254",
        "target": "switch-001",
        "type": "ethernet",
        "status": "up"
      }
    ],
    "metadata": {
      "total_devices": 3,
      "generated_at": "2025-01-22T17:00:00Z"
    }
  }
}
```

---

## 🔄 Complete API Flow Sequence

### 1. Initialization Flow
```
1. Load .env configuration
2. Initialize FortiGate collector with Bearer token
3. Initialize Meraki collector (when enabled)
4. Start LLM client (Ollama/CodeLlama)
5. Register MCP tools
6. Connect to 3D topology services
```

### 2. Topology Collection Flow
```
1. collect_topology() called
2. FortiGate APIs: status → interfaces → policies → VIPs → resources
3. Meraki APIs: orgs → networks → devices → ports → APs (when enabled)
4. Merge and normalize data
5. Generate device-link relationships
6. Store in current_topology
7. Return structured JSON
```

### 3. Diagram Generation Flow
```
1. generate_drawio_diagram() called
2. Extract devices/links from current_topology
3. Apply layout algorithm (hierarchical/circular)
4. Generate DrawIO XML with icons and styling
5. Return diagram data
```

### 4. LLM Query Flow
```
1. User natural language query
2. Search API documentation by relevance
3. Build context with device info
4. Query LLM for API request generation
5. Parse and validate generated request
6. Return executable API call
```

### 5. 3D Visualization Flow
```
1. Web UI requests /api/topology/scene
2. MCP server provides topology data
3. Convert to Three.js scene format
4. Apply device icons and positions
5. Establish WebSocket for updates
6. Render interactive 3D topology
```

---

## 🚨 Error Handling & Fallbacks

### API Connection Failures
```
FortiGate API Error → Use demo topology data
Meraki API Error → Skip Meraki devices
LLM API Error → Use keyword matching fallback
3D Service Error → Static topology display
```

### Authentication Issues
```
Token Expired → Log error and use demo data
Invalid Token → Prompt for reconfiguration
SSL Issues → Continue with verify_ssl=false
Rate Limits → Implement exponential backoff
```

### Data Validation
```
Missing Fields → Use default values
Invalid JSON → Log and skip record
Empty Responses → Return appropriate empty structures
Type Mismatches → Cast to expected types
```

---

## 📊 Performance Requirements

### Response Time Targets
```
API Documentation Query: <100ms
LLM Request Generation: <5s
Topology Collection: <10s
Diagram Generation: <2s
3D Scene Update: <500ms
```

### Rate Limits
```
FortiGate API: No official limit (self-hosted)
Meraki API: 5 req/sec per organization
LLM API: Limited by local hardware
MCP Tools: No hard limits
```

### Caching Strategy
```
Topology Data: 5 minutes TTL
API Documentation: Static (no cache)
LLM Responses: 1 hour TTL
3D Scenes: Real-time (no cache)
```

---

## 🔒 Security Considerations

### API Tokens
```
FortiGate Token: Store in .env, rotate quarterly
Meraki Key: Store in .env, scope to read-only
LLM API: Local deployment, no external access
MCP Server: Local only, no network exposure
```

### Network Security
```
FortiGate: HTTPS with self-signed cert
Meraki: HTTPS with valid cert
LLM: HTTP (localhost only)
3D Services: HTTP (internal network)
```

### Data Privacy
```
Topology Data: Stored in memory only
API Logs: No sensitive data recorded
LLM Prompts: Sanitized before sending
Error Messages: Sanitized for external display
```

---

## 🎯 Success Metrics

### API Availability
```
FortiGate APIs: >95% uptime
Meraki APIs: >99% uptime (Meraki SLA)
LLM Service: >90% uptime
MCP Server: Continuous operation
```

### Response Quality
```
Documentation Search: >80% relevance accuracy
LLM Generation: >70% correct API calls
Topology Completeness: >95% device discovery
Diagram Accuracy: >90% visual fidelity
```

### User Experience
```
Natural Language: <2s response time
Diagram Generation: <3s total time
3D Visualization: <1s load time
Error Recovery: Graceful fallbacks
```

---

## 📝 Implementation Checklist

### ✅ Completed
- [x] FortiGate API integration with Bearer token auth
- [x] Meraki API integration structure
- [x] LLM integration with Ollama
- [x] MCP server with 6 tools
- [x] 3D topology data format
- [x] DrawIO diagram generation
- [x] Error handling and fallbacks
- [x] Comprehensive documentation

### 🔄 In Progress
- [ ] Real FortiGate API authentication testing
- [ ] Meraki API key configuration
- [ ] CodeLlama model integration
- [ ] WebSocket real-time updates
- [ ] Performance optimization

### 📋 Planned
- [ ] API request execution module
- [ ] Advanced LLM prompt engineering
- [ ] Multi-organization Meraki support
- [ ] Enhanced 3D interactions
- [ ] Mobile-responsive UI

---

**This complete API specification provides all necessary requests, responses, and integration patterns for your FortiGate + Meraki intelligent topology application.** 🚀
