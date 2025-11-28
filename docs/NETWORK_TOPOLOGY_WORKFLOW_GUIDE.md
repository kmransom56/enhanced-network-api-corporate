# Network Topology Workflow Guide

Complete guide for building dynamic 2D and 3D network maps from FortiOS API data.

## Overview

This workflow provides end-to-end automation for creating interactive network topology visualizations by:

1. **Collecting** device information from FortiGate, FortiSwitch, FortiAP
2. **Identifying** devices by MAC address using OUI lookup
3. **Generating** SVG icons for each device type
4. **Creating** 3D models for Babylon.js visualization
5. **Exporting** to multiple formats (JSON, DrawIO, Babylon.js)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Network Topology Workflow                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
    ┌────────────────────────────────────────────────────┐
    │  Step 1: FortiOS API Data Collection               │
    │  - FortiGate authentication                         │
    │  - Discover FortiSwitch devices                     │
    │  - Discover FortiAP devices                         │
    │  - Collect connected clients (WiFi & wired)         │
    └────────────────────────────────────────────────────┘
                              ↓
    ┌────────────────────────────────────────────────────┐
    │  Step 2: Device Identification (MAC-based)         │
    │  - OUI lookup for vendor identification             │
    │  - Device classification (POS, AP, Switch, etc.)    │
    │  - Confidence scoring                               │
    │  - Restaurant tech detection                        │
    └────────────────────────────────────────────────────┘
                              ↓
    ┌────────────────────────────────────────────────────┐
    │  Step 3: SVG Icon Generation                       │
    │  - Device-type-specific SVG creation                │
    │  - Color-coded by category                          │
    │  - Status indicators                                │
    │  - Vendor branding                                  │
    └────────────────────────────────────────────────────┘
                              ↓
    ┌────────────────────────────────────────────────────┐
    │  Step 4: 3D Model Mapping                          │
    │  - Match devices to 3D models                       │
    │  - Position calculation                             │
    │  - Connection topology                              │
    └────────────────────────────────────────────────────┘
                              ↓
    ┌────────────────────────────────────────────────────┐
    │  Step 5: Export & Visualization                    │
    │  - Babylon.js 3D format                             │
    │  - DrawIO XML/JSON                                  │
    │  - Network map JSON                                 │
    └────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

```bash
# Python 3.12+
python --version

# Install dependencies
pip install -r requirements.txt

# Or using uv (recommended)
uv pip install -r requirements.txt
```

### Required Packages

- `fastapi` - REST API framework
- `requests` - HTTP client for FortiOS API
- `pydantic` - Data validation
- `asyncio` - Async workflow execution

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# FortiGate Configuration
FORTIGATE_HOST=192.168.1.99
FORTIGATE_TOKEN=your-api-token-here

# Optional: MAC address API (for enhanced device identification)
MACADDRESS_IO_API_KEY=your-api-key
MACADDRESS_IO_BASE_URL=https://api.macaddress.io/v1

# Optional: Custom paths
OUI_DATABASE_PATH=/path/to/oui.csv
MODEL_LIBRARY_PATH=/path/to/model_library.json
SVG_OUTPUT_DIR=realistic_device_svgs
```

### FortiGate API Token

Generate an API token in FortiGate:

```bash
# SSH to FortiGate
ssh admin@192.168.1.99

# Create API user
config system api-user
    edit "api-user"
        set api-key "your-generated-token"
        set accprofile "super_admin"
        set vdom "root"
        set comments "API access for topology workflow"
    next
end
```

## Usage

### Method 1: Python CLI

Run the workflow directly from command line:

```bash
# Set environment variables
export FORTIGATE_HOST=192.168.1.99
export FORTIGATE_TOKEN=your-api-token

# Execute workflow
python -m src.enhanced_network_api.network_topology_workflow
```

### Method 2: Python Script

```python
import asyncio
from src.enhanced_network_api.network_topology_workflow import NetworkTopologyWorkflow

async def main():
    # Initialize workflow
    workflow = NetworkTopologyWorkflow(
        fortigate_host='192.168.1.99',
        fortigate_token='your-api-token',
        verify_ssl=False
    )
    
    # Execute complete workflow
    result = await workflow.execute_workflow()
    
    # Access results
    print(f"Discovered {result['summary']['total_devices']} devices")
    print(f"Generated {result['summary']['total_connections']} connections")
    
    # Export paths
    print(f"Babylon.js: {result['export_paths']['babylon']}")
    print(f"DrawIO: {result['export_paths']['drawio']}")

if __name__ == '__main__':
    asyncio.run(main())
```

### Method 3: FastAPI REST API

Start the API server:

```bash
# Using uvicorn
uvicorn src.enhanced_network_api.api.main:app --reload --host 0.0.0.0 --port 8000

# Or using FastAPI CLI
fastapi dev src/enhanced_network_api/api/main.py
```

Execute workflow via API:

```bash
# Start workflow (returns job_id)
curl -X POST http://localhost:8000/api/topology/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "fortigate_host": "192.168.1.99",
    "fortigate_token": "your-api-token",
    "verify_ssl": false
  }'

# Check workflow status
curl http://localhost:8000/api/topology/workflow-status/workflow_20241128_040000

# Get devices
curl http://localhost:8000/api/topology/devices

# Get connections
curl http://localhost:8000/api/topology/connections

# Get Babylon.js format for 3D viewer
curl http://localhost:8000/api/topology/babylon-lab-format
```

## Workflow Steps Explained

### Step 1: Authenticate & Discover Infrastructure

```python
# Authenticate to FortiGate
fg_auth = FortiGateAuth(host, token)
fg_auth.login()

# Discover managed devices
fortiswitches = fg_module.get_fortiswitches()
fortiaps = fg_module.get_fortiaps()
```

**API Endpoints Used:**
- `/api/v2/monitor/switch-controller/managed-switch/status`
- `/api/v2/monitor/wifi/managed_ap`

### Step 2: Collect Connected Clients

```python
# Get WiFi clients
wifi_clients = fg_module.get_connected_clients()

# Get wired clients (from FortiSwitch)
# Note: Requires querying each FortiSwitch individually
```

**API Endpoints Used:**
- `/api/v2/monitor/wifi/client`
- `/api/v2/monitor/switch-controller/managed-switch/clients` (per switch)

### Step 3: Identify Devices by MAC

```python
# Use MAC matcher for device identification
matcher = DeviceModelMatcher()

device_info = matcher.match_mac_to_model(
    mac_address='AC:BC:32:11:22:33',
    additional_context={'hostname': 'POS-Terminal-01'}
)

# Returns: DeviceInfo(
#   vendor='Square',
#   device_type='POS Register/Cash Terminal',
#   confidence='high',
#   model_path='/static/3d-models/square_terminal.obj'
# )
```

**Device Classification Logic:**
1. OUI lookup for vendor
2. Pattern matching for device type
3. Restaurant tech detection (POS, KDS, etc.)
4. Confidence scoring

### Step 4: Generate SVG Icons

For each device, an SVG icon is generated based on device type:

```python
# SVG generation with device-specific styling
svg_content = workflow._create_device_svg(device)

# SVG features:
# - Color-coded by device type
# - Status indicator (online/offline)
# - Vendor branding
# - Device label
```

**Device Type → Color Mapping:**
- FortiGate (Firewall): Red (#dc3545)
- FortiSwitch: Green (#28a745)
- FortiAP: Yellow (#ffc107)
- POS Terminal: Purple (#6f42c1)
- Generic Client: Gray (#6c757d)

### Step 5: Build Topology Connections

```python
# Build connection graph
for device in devices:
    if device.connected_to:
        connection = NetworkConnection(
            from_device=device.connected_to,
            to_device=device.id,
            status='up',
            vlan=device.vlan
        )
```

### Step 6: Export to Visualization Formats

#### Babylon.js Format

```json
{
  "models": [
    {
      "id": "fortigate-primary",
      "name": "FortiGate-60F",
      "type": "fortigate",
      "vendor": "Fortinet",
      "icon_svg": "/realistic_device_svgs/fortinet_fortigate.svg",
      "ip": "192.168.1.99",
      "mac": "90:6C:AC:12:34:56",
      "position": {"x": 0, "y": 0, "z": 0}
    }
  ],
  "connections": [
    {
      "id": "conn-1",
      "from": "fortigate-primary",
      "to": "fortiswitch-01",
      "status": "up"
    }
  ]
}
```

#### DrawIO Format

```json
{
  "nodes": [
    {
      "id": "fortigate-primary",
      "label": "FortiGate-60F",
      "type": "fortigate",
      "x": 0,
      "y": 100,
      "width": 120,
      "height": 80
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "source": "fortigate-primary",
      "target": "fortiswitch-01"
    }
  ]
}
```

## 3D Visualization with Babylon.js

### Open the 3D Viewer

```bash
# Start the API server
uvicorn src.enhanced_network_api.api.main:app --host 0.0.0.0 --port 8000

# Open browser
http://localhost:8000/static/babylon_lab_view.html
```

### Viewer Features

- **3D Navigation**: Click and drag to rotate, scroll to zoom
- **Device Details**: Click devices to view information
- **Auto-Rotate**: Toggle automatic scene rotation
- **Labels**: Show/hide device labels
- **Live Data**: Loads from `/api/topology/babylon-lab-format`

### Customization

Edit `babylon_lab_view.html` to customize:

```javascript
// Modify device positioning
function _calculate_device_position(device, index) {
    // Your custom layout logic
}

// Change 3D model paths
const modelMap = {
    'fortigate': '/lab_3d_models/models/FortiGate.obj',
    'fortiswitch': '/lab_3d_models/models/FortiSwitch.obj'
};
```

## Device Identification Deep Dive

### OUI Lookup

MAC addresses are matched against IEEE OUI database:

```python
# Example: Square POS Terminal
mac = 'AC:BC:32:11:22:33'
oui = 'AC:BC:32'  # First 3 bytes

# Lookup result:
vendor = 'Square (Block Inc)'
```

### Restaurant Technology Detection

Special handling for restaurant devices:

```python
restaurant_tech_ouis = {
    'Clover': ['00:0C:F1', '00:1D:6A'],
    'Square': ['AC:BC:32', '44:38:39'],
    'Toast': ['B8:27:EB', 'DC:A6:32'],  # Raspberry Pi-based
    'NCR Aloha': ['00:0D:93', '00:40:AA']
}
```

### Device Types

Classified device types:
- `POS Register/Cash Terminal`
- `POS Tablet/Tabletop Ordering`
- `Kitchen Display Unit (KDS)`
- `Digital Menu Board`
- `Kitchen/Receipt Printer`
- `Payment Terminal`

## Troubleshooting

### Common Issues

#### 1. Authentication Failed

```
Error: Failed to authenticate to FortiGate
```

**Solution:**
- Verify FortiGate API token is correct
- Check firewall allows API access from your IP
- Ensure API user has correct permissions

#### 2. No Devices Discovered

```
Warning: Failed to discover FortiSwitch devices
```

**Solution:**
- Verify FortiSwitch devices are managed by FortiGate
- Check FortiGate can reach managed devices
- Review API endpoint permissions

#### 3. MAC Identification Failed

```
Warning: Device has no MAC address, skipping identification
```

**Solution:**
- Some devices may not report MAC addresses
- Check FortiOS API documentation for client details
- Use alternative identification methods (IP, hostname)

#### 4. SVG Generation Error

```
Error: Failed to create SVG for device
```

**Solution:**
- Check `svg_output_dir` is writable
- Verify device type mapping exists
- Review SVG template syntax

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

workflow = NetworkTopologyWorkflow(...)
result = await workflow.execute_workflow()
```

### API Testing

Use FastAPI docs for testing:

```
http://localhost:8000/docs
```

## Performance Optimization

### Caching

Workflow results are cached in memory:

```python
# Cache configuration
workflow_cache: Dict[str, WorkflowResult] = {}

# Clear cache manually
curl -X DELETE http://localhost:8000/api/topology/cache
```

### Batch Processing

For large networks, process devices in batches:

```python
# Batch device identification
device_infos = matcher.bulk_match(
    mac_addresses=[d.mac for d in devices],
    context_map={d.mac: {'hostname': d.name} for d in devices}
)
```

### Async Execution

Workflow runs asynchronously:

```python
# Background execution
background_tasks.add_task(run_workflow_background, job_id, config)

# Check status periodically
while True:
    status = await get_workflow_status(job_id)
    if status['status'] != 'running':
        break
    await asyncio.sleep(5)
```

## Integration Examples

### Integration with DrawIO

Export topology to DrawIO format:

```bash
curl http://localhost:8000/api/topology/drawio-xml -o topology.drawio
```

Open in DrawIO desktop or web app.

### Integration with Monitoring Systems

Use workflow data for monitoring:

```python
# Get device status
devices = await get_devices()
offline_devices = [d for d in devices if d['status'] != 'online']

# Alert on offline devices
if offline_devices:
    send_alert(f"{len(offline_devices)} devices offline")
```

### Integration with CMDB

Sync topology data to CMDB:

```python
# Export device inventory
devices = await get_devices()

for device in devices:
    cmdb.update_device(
        hostname=device['name'],
        ip=device['ip'],
        mac=device['mac'],
        vendor=device['vendor'],
        type=device['device_type']
    )
```

## Advanced Usage

### Custom Device Classification

Add custom device types:

```python
# In device_mac_matcher.py
restaurant_device_types = {
    'custom_kiosk': {
        'keywords': ['kiosk', 'self-order'],
        'ouis': ['XX:XX:XX'],
        'model': '/static/3d-models/custom_kiosk.obj'
    }
}
```

### Custom Layout Algorithms

Implement custom positioning:

```python
def custom_layout(devices, connections):
    """
    Force-directed layout for better visualization
    """
    # Your layout algorithm
    for device in devices:
        device.position = calculate_force_position(device, connections)
```

### Export to Additional Formats

Add new export formats:

```python
def export_custom_format(self) -> Dict[str, Any]:
    """Export to custom format"""
    return {
        'nodes': self._convert_devices_custom(),
        'edges': self._convert_connections_custom()
    }
```

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/topology/execute-workflow` | Start workflow execution |
| GET | `/api/topology/workflow-status/{job_id}` | Get workflow status |
| GET | `/api/topology/babylon-lab-format` | Get Babylon.js format |
| GET | `/api/topology/devices` | Get device list |
| GET | `/api/topology/connections` | Get connection list |
| GET | `/api/topology/summary` | Get topology summary |
| DELETE | `/api/topology/cache` | Clear workflow cache |

### Data Models

See `network_topology_workflow.py` for complete data models:
- `NetworkDevice`
- `NetworkConnection`
- `DeviceInfo`
- `WorkflowResult`

## Best Practices

1. **Authentication**: Use dedicated API users with minimal required permissions
2. **Caching**: Cache topology data for frequently accessed networks
3. **Error Handling**: Implement retry logic for API failures
4. **Monitoring**: Track workflow execution times and success rates
5. **Documentation**: Keep device type mappings documented
6. **Testing**: Test with different network configurations

## Contributing

To contribute improvements:

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit pull request

## Support

For issues or questions:
- Check troubleshooting section above
- Review API documentation at `/docs`
- Open GitHub issue with details

## License

See LICENSE file for details.

## Changelog

### Version 1.0.0 (2024-11-28)

- Initial release
- Complete workflow implementation
- FortiOS API integration
- MAC-based device identification
- SVG icon generation
- Babylon.js 3D visualization
- FastAPI REST endpoints
