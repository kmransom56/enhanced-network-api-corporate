# Network Tree Layout

This document describes the Network Tree layout algorithm that matches the specific Fortinet topology diagram layout.

## Layout Structure

The layout arranges devices in a hierarchical tree structure:

```
        Internet
          |
      Fortigate
       /     \
  FortiSwitch  Wireless AP
     |            |
  Device 1    Device 2
  Device 2    Device 2
```

### Layer Structure

1. **Layer 1 (Top)**: Internet
   - Position: Center top
   - Y coordinate: Highest

2. **Layer 2**: Fortigate Firewall
   - Position: Center, below Internet
   - Y coordinate: Second highest

3. **Layer 3**: Network Distribution
   - **Left side**: FortiSwitch (wired network)
   - **Right side**: Wireless Access Point (wireless network)
   - Y coordinate: Middle

4. **Layer 4 (Bottom)**: End Devices
   - **Left side**: Wired clients (below FortiSwitch)
   - **Right side**: Wireless clients (below Wireless AP)
   - Y coordinate: Lowest

## Implementation

### Python Backend

The layout is implemented in `src/enhanced_network_api/layout_network_tree.py`:

```python
from src.enhanced_network_api.layout_network_tree import calculate_network_tree_layout

positioned_nodes = calculate_network_tree_layout(nodes, links)
```

### JavaScript Frontend

The layout is implemented in:
- `src/enhanced_network_api/static/babylon_lab_view.html` (3D viewer)
- `src/enhanced_network_api/static/network_topology_viewer.html` (2D viewer)

Both use the `network_tree` layout algorithm.

## Device Type Detection

The layout automatically detects device types based on:

- **Internet**: `type` contains "internet" or "wan"
- **Fortigate**: `type` contains "fortigate", "firewall", or "gateway"
- **FortiSwitch**: `type` contains "fortiswitch" or "switch"
- **Wireless AP**: `type` contains "fortiap", "access_point", "ap", or "wireless"
- **Wired Clients**: `connection_type` is "ethernet" or device type is "client"/"endpoint"
- **Wireless Clients**: `connection_type` is "wifi" or device has `ssid` property

## Spacing Configuration

Default spacing values:

- **Vertical spacing**: 8.0 units (between layers)
- **Horizontal spacing**: 6.0 units (between left/right branches)
- **Device spacing**: 4.0 units (between devices in same group)

These can be customized when calling the layout function.

## Usage

### In API

The layout is automatically applied when requesting topology scenes:

```python
# In platform_web_api_fastapi.py
_apply_hierarchical_layout(scene, layout_type="network_tree")
```

### In Frontend

Select "Network Tree (Fortinet)" from the layout dropdown in the topology viewer.

## Example Topology

For a topology matching the diagram:

```json
{
  "nodes": [
    {"id": "internet", "type": "internet", "name": "Internet"},
    {"id": "fg1", "type": "fortigate", "name": "FortiGate Firewall"},
    {"id": "sw1", "type": "fortiswitch", "name": "FortiSwitch"},
    {"id": "ap1", "type": "fortiap", "name": "Wireless AP"},
    {"id": "dev1", "type": "client", "name": "End Device 1", "connection_type": "ethernet"},
    {"id": "dev2", "type": "client", "name": "End Device 2", "connection_type": "ethernet"},
    {"id": "wdev1", "type": "client", "name": "Wireless Device 1", "connection_type": "wifi"},
    {"id": "wdev2", "type": "client", "name": "Wireless Device 2", "connection_type": "wifi"}
  ],
  "links": [
    {"from": "internet", "to": "fg1"},
    {"from": "fg1", "to": "sw1"},
    {"from": "fg1", "to": "ap1"},
    {"from": "sw1", "to": "dev1"},
    {"from": "sw1", "to": "dev2"},
    {"from": "ap1", "to": "wdev1"},
    {"from": "ap1", "to": "wdev2"}
  ]
}
```

This will produce the exact layout shown in the diagram.

## Customization

To customize spacing or positioning, modify the `spacing` dictionary:

```python
custom_spacing = {
    'vertical': 10.0,    # More vertical space
    'horizontal': 8.0,   # More horizontal separation
    'device': 5.0        # More space between devices
}

positioned_nodes = calculate_network_tree_layout(nodes, links, spacing=custom_spacing)
```

