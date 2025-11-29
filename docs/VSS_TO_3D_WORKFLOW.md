# VSS Extraction to 3D Network Map - Complete Workflow

This document describes the complete workflow from VSS extraction to 3D network topology rendering with the Network Tree layout.

## Overview

The workflow converts Visio Stencil (VSS) files into 3D GLB models and renders them in a hierarchical network topology matching the Fortinet diagram layout.

## Complete Workflow

### Step 1: VSS to SVG Conversion

Extract SVG icons from VSS files using libvisio:

```bash
# Convert VSS files to SVG
cd vss_extraction
python tools/vss_to_svg_libvisio.py source_models -o assets/icons/vss_extracted -r
```

**Output**: SVG icons for:
- FortiGate devices
- FortiSwitch devices  
- FortiAP devices
- Endpoint devices (if present in VSS)

### Step 2: SVG Cleaning

Clean SVG files to fix duplicate attributes and malformed XML:

```bash
python tools/svg_cleaner.py assets/icons --recursive
```

**Output**: Cleaned SVG files ready for 3D conversion

### Step 3: SVG to GLB Conversion

Convert SVG icons to 3D GLB models using Blender:

```bash
python tools/svg_to_glb_converter.py assets/icons -o assets/models -r
```

**Output**: GLB 3D models for:
- `FortiGate_600E.glb` - Firewall device
- `FortiSwitch_148E.glb` - Switch device
- `FortiAP_432F.glb` - Access point device
- `Laptop.glb` - Wired endpoint device
- `Smartphone.glb` - Wireless endpoint device

### Step 4: Asset Management

Update device model rules with generated assets:

```bash
python tools/build_assets_from_rules.py \
    --rules device_model_rules.json \
    --icons-dir assets/icons \
    --models-dir assets/models \
    --scan-new
```

**Output**: Updated `device_model_rules.json` mapping device types to 3D models

### Step 5: One-Command Workflow

Run the complete workflow with a single command:

```bash
cd vss_extraction
make all
```

This executes:
1. VSS to SVG conversion
2. SVG cleaning
3. SVG to GLB conversion
4. Asset rules update

## 3D Model Assignment

The system automatically assigns 3D models based on device type:

### Network Infrastructure

- **Internet**: Generic network model
- **FortiGate**: `/vss_extraction/vss_exports/FortiGate_600E.gltf`
- **FortiSwitch**: `/vss_extraction/vss_exports/FortiSwitch_148E.gltf`
- **FortiAP**: `/vss_extraction/vss_exports/FortiAP_432F.gltf`

### Endpoint Devices

- **Wired Clients** (ethernet connection):
  - Laptops/Computers: `/realistic_3d_models/models/Laptop.obj`
  - Generic: `/realistic_3d_models/models/Laptop.obj`

- **Wireless Clients** (wifi connection):
  - Phones/Mobile: `/realistic_3d_models/models/Smartphone.obj`
  - Generic: `/realistic_3d_models/models/Smartphone.obj`

## Network Tree Layout

All devices are automatically positioned using the Network Tree layout:

```
        Internet (top center)
          |
      FortiGate (center)
       /     \
  FortiSwitch  FortiAP (left/right)
     |            |
  Laptop      Smartphone
  Laptop      Smartphone
```

### Layout Layers

1. **Layer 1 (Y=24)**: Internet - Center top
2. **Layer 2 (Y=16)**: FortiGate - Center
3. **Layer 3 (Y=8)**: 
   - FortiSwitch - Left (X=-6)
   - FortiAP - Right (X=6)
4. **Layer 4 (Y=0)**: 
   - Wired clients - Below switch (X=-6 ± spacing)
   - Wireless clients - Below AP (X=6 ± spacing)

## Rendering in 3D Viewer

The topology is automatically rendered in the 3D viewer at `/2d-topology-enhanced`:

1. **Device Loading**: Each device loads its assigned 3D model
2. **Positioning**: Network Tree layout positions devices hierarchically
3. **Connections**: Links are drawn between connected devices
4. **Labels**: Device names and IPs are displayed

## API Endpoints

### Get Topology Scene

```bash
GET /api/topology/scene
```

Returns JSON with:
- `nodes`: Array of devices with `position`, `device_model`, `type`
- `links`: Array of connections between devices

Example response:
```json
{
  "nodes": [
    {
      "id": "fg1",
      "name": "FortiGate Firewall",
      "type": "fortigate",
      "position": {"x": 0, "y": 16, "z": 0},
      "device_model": "/vss_extraction/vss_exports/FortiGate_600E.gltf"
    },
    {
      "id": "sw1",
      "name": "FortiSwitch",
      "type": "fortiswitch",
      "position": {"x": -6, "y": 8, "z": 0},
      "device_model": "/vss_extraction/vss_exports/FortiSwitch_148E.gltf"
    },
    {
      "id": "client1",
      "name": "End Device 1",
      "type": "client",
      "connection_type": "ethernet",
      "position": {"x": -8, "y": 0, "z": 0},
      "device_model": "/realistic_3d_models/models/Laptop.obj"
    }
  ],
  "links": [
    {"from": "fg1", "to": "sw1"},
    {"from": "sw1", "to": "client1"}
  ]
}
```

## File Structure

```
vss_extraction/
├── source_models/              # Input VSS files
├── assets/
│   ├── icons/                  # Extracted SVG icons
│   │   ├── vss_extracted/      # From VSS conversion
│   │   ├── fortinet/           # From DrawIO
│   │   └── meraki/             # Meraki icons
│   └── models/                 # Generated GLB models
│       ├── fortinet/
│       └── meraki/
├── vss_exports/                # VSS extraction output (GLTF)
│   ├── FortiGate_600E.gltf
│   ├── FortiSwitch_148E.gltf
│   └── FortiAP_432F.gltf
├── tools/                      # Conversion tools
│   ├── vss_to_svg_libvisio.py
│   ├── svg_cleaner.py
│   ├── svg_to_glb_converter.py
│   └── build_assets_from_rules.py
└── device_model_rules.json     # Device-to-model mapping

realistic_3d_models/
└── models/
    ├── Laptop.obj              # Wired endpoint model
    └── Smartphone.obj          # Wireless endpoint model
```

## Verification

To verify the complete workflow:

1. **Check VSS extraction**:
   ```bash
   ls vss_extraction/vss_exports/*.gltf
   ```

2. **Check SVG icons**:
   ```bash
   ls vss_extraction/assets/icons/vss_extracted/*.svg
   ```

3. **Check GLB models**:
   ```bash
   ls vss_extraction/assets/models/*.glb
   ```

4. **View topology**:
   - Open browser to `http://localhost:11111/2d-topology-enhanced`
   - Devices should appear in Network Tree layout
   - Each device should have its 3D model loaded

## Troubleshooting

### Missing 3D Models

If devices don't have models:
1. Check `device_model_rules.json` has correct mappings
2. Verify GLB files exist in expected paths
3. Check browser console for model loading errors

### Incorrect Layout

If layout doesn't match diagram:
1. Verify Network Tree layout is selected (default)
2. Check device types are correctly identified
3. Verify links exist between devices

### Model Not Loading

If 3D models don't load:
1. Check file paths are correct
2. Verify GLB files are valid
3. Check browser console for errors
4. Ensure static file serving is configured

## Next Steps

1. **Add More Device Types**: Extend VSS extraction to support more Fortinet models
2. **Custom Models**: Replace placeholder models with actual device models
3. **Texture Enhancement**: Use Eraser AI to enhance model textures
4. **Animation**: Add device status indicators and animations

