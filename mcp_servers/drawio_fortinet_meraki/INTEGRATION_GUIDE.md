# DrawIO Fortinet/Meraki MCP Integration Guide

## 🎯 Overview

This integration enables AI-assisted network diagram generation by combining:
- **DrawIO MCP Server** - Natural language diagram generation
- **FortiManager/FortiGate APIs** - Real Fortinet device data
- **Meraki Dashboard APIs** - Cloud-managed device data
- **Your existing 3D topology viewer** - Babylon.js visualization

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/keith/enhanced-network-api-corporate/mcp_servers/drawio_fortinet_meraki
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Test the Server

```bash
python -c "
import asyncio
from mcp_server import DrawIOMCPServer

async def test():
    server = DrawIOMCPServer()
    await server.initialize_topology_collector()
    result = await server.collect_topology({'refresh': True})
    print(f'✅ Found {json.loads(result.content[0].text)[\"total_devices\"]} devices')

asyncio.run(test())
"
```

## 🔧 Configuration

### FortiManager/FortiGate Setup

```bash
# .env configuration
FORTIMANAGER_HOST=192.168.0.254
FORTIMANAGER_USERNAME=admin
FORTIMANAGER_PASSWORD=your_password
FORTIMANAGER_PORT=443
FORTIMANAGER_VERIFY_SSL=false
```

### Meraki Dashboard Setup

```bash
# .env configuration
MERAKI_API_KEY=your_meraki_api_key_here
MERAKI_BASE_URL=https://api.meraki.com
```

## 🎨 Usage Examples

### Natural Language Diagram Generation

```
User: "Create a hierarchical diagram showing my FortiGate at the top, switches in the middle, and access points at the bottom. Use appropriate icons and label devices with their IPs."

AI: [Executes MCP tools]
✅ Generated hierarchical network diagram with 3 devices
```

### Real-time Topology Updates

```
User: "Show me the current network topology and highlight any devices that are down"

AI: [Collects live data → Generates diagram → Color-codes by status]
✅ Live topology with health status visualization
```

### Export and Integration

```
User: "Export the topology as JSON and create a DrawIO file I can edit"

AI: [Exports data → Generates DrawIO XML]
✅ Created fortinet_topology.json and fortinet_topology.drawio
```

## 🔗 Integration with Existing Systems

### 1. Connect to Your Fortinet MCP Server

The server includes a bridge to your existing `server_enhanced.py`:

```python
from fortinet_integration import DrawIOFortinetIntegration

integration = DrawIOFortinetIntegration()
result = await integration.collect_and_generate(layout="hierarchical")
```

### 2. Update Babylon.js 3D Viewer

Use the generated scene data with your existing `babylon_test_organized.html`:

```javascript
// Load from MCP-generated scene
async function loadMCPScene() {
    const response = await fetch('/mcp/topology_scene');
    const sceneData = await response.json();
    
    // Use with your existing renderTopology function
    await renderTopology(sceneData);
}
```

### 3. CI/CD Integration

```yaml
# .gitlab-ci.yml
topology-diagrams:
  stage: documentation
  script:
    - python generate_topology_docs.py
  artifacts:
    paths:
      - network-topology.drawio
      - network-topology.json
```

## 🛠 MCP Tools Available

### collect_topology
Collect network topology from APIs

```python
result = await server.collect_topology({
    "refresh": True,
    "device_types": ["fortigate", "fortiswitch", "fortiap"]
})
```

### generate_drawio_diagram
Generate DrawIO diagram from topology

```python
result = await server.generate_drawio_diagram({
    "layout": "hierarchical",
    "group_by": "type",
    "show_details": True,
    "color_code": True
})
```

### get_topology_summary
Get topology statistics

```python
result = await server.get_topology_summary({})
# Returns: device counts, link counts, sites, health metrics
```

### export_topology_json
Export data in multiple formats

```python
result = await server.export_topology_json({
    "include_health": True,
    "format": "json"  # json, csv, yaml
})
```

## 🎯 Advanced Features

### Real-time Monitoring

```python
# Continuous topology monitoring
async def monitor_network():
    server = DrawIOMCPServer()
    await server.initialize_topology_collector()
    
    while True:
        topology = await server.collect_topology({'refresh': True})
        
        # Check for changes
        if network_changed(topology):
            # Auto-generate updated diagram
            await server.generate_drawio_diagram({'layout': 'hierarchical'})
        
        await asyncio.sleep(300)  # 5 minutes
```

### Multi-vendor Integration

```python
# Support for additional vendors
VENDOR_MAPPINGS = {
    'cisco': {'router': 'cisco_router', 'switch': 'cisco_switch'},
    'juniper': {'router': 'juniper_router', 'switch': 'juniper_switch'},
    'aruba': {'ap': 'aruba_ap', 'switch': 'aruba_switch'}
}
```

### Custom Layout Algorithms

```python
# Force-directed layout using NetworkX
def calculate_force_directed_positions(devices, links):
    import networkx as nx
    
    G = nx.Graph()
    for device in devices:
        G.add_node(device['id'])
    for link in links:
        G.add_edge(link['source_id'], link['target_id'])
    
    pos = nx.spring_layout(G, k=2, iterations=50)
    return pos
```

## 🔍 Troubleshooting

### Common Issues

1. **API Authentication Errors**
   ```bash
   # Test FortiManager connection
   curl -k -X GET "https://192.168.0.254/api/v2/monitor/firewall/status" \
        -H "Authorization: Bearer <token>"
   
   # Test Meraki API
   curl -H "X-Cisco-Meraki-API-Key: <key>" \
        "https://api.meraki.com/api/v1/organizations"
   ```

2. **DrawIO Extension Not Connecting**
   - Install DrawIO MCP Extension
   - Check WebSocket connection (port 3333)
   - Restart browser

3. **MCP Server Not Starting**
   ```bash
   # Check Python version
   python --version  # Should be 3.8+
   
   # Verify dependencies
   pip list | grep mcp
   ```

### Debug Mode

```bash
export LOG_LEVEL=DEBUG
python mcp_server.py
```

### Performance Optimization

For large networks (500+ devices):

1. **Enable device filtering**
   ```python
   result = await server.collect_topology({
       "device_types": ["fortigate", "fortiswitch"]  # Exclude APs
   })
   ```

2. **Use caching**
   ```python
   # Cache topology for 5 minutes
   result = await server.collect_topology({"refresh": False})
   ```

3. **Incremental updates**
   ```python
   # Only update changed devices
   if devices_changed:
       await server.generate_drawio_diagram({"layout": "hierarchical"})
   ```

## 📊 File Structure

```
mcp_servers/drawio_fortinet_meraki/
├── mcp_server.py              # Main MCP server
├── fortinet_integration.py    # Bridge to existing Fortinet MCP
├── start_server.py           # Startup script
├── test_mcp_server.py        # Test suite
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── mcp_config.json          # MCP client configuration
├── setup.py                 # Package setup
└── README.md                # Documentation
```

## 🎯 Next Steps

### 1. Configure Real APIs
- Set up FortiManager API access
- Configure Meraki Dashboard API key
- Test API connectivity

### 2. Integrate with DrawIO
- Install DrawIO MCP browser extension
- Test natural language diagram generation
- Customize device icons and styling

### 3. Connect to 3D Viewer
- Update babylon_test_organized.html to use MCP data
- Implement real-time topology updates
- Add device health visualization

### 4. Deploy to Production
- Set up CI/CD pipeline integration
- Configure monitoring and alerting
- Document workflows for team

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/enhanced-network-api/drawio-fortinet-meraki-mcp/issues)
- **Documentation**: [Wiki](https://github.com/enhanced-network-api/drawio-fortinet-meraki-mcp/wiki)
- **Community**: [Discussions](https://github.com/enhanced-network-api/drawio-fortinet-meraki-mcp/discussions)

## 🎉 Success Metrics

- ✅ **Speed**: Generate diagrams in seconds vs hours manually
- ✅ **Accuracy**: Real API data ensures diagrams match actual network
- ✅ **Flexibility**: Natural language enables rapid iterations
- ✅ **Integration**: Works with existing tools and workflows
- ✅ **Scalability**: Handles enterprise networks with 500+ devices

---

**Ready to transform your network documentation?** Start with the quick test above and gradually integrate with your production environment!
