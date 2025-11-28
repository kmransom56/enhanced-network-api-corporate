#!/usr/bin/env python3
"""
Create functional 3D models for VSS + Eraser AI workflow
These are temporary models until you extract real ones with VSS + Eraser AI
"""

import json
import os
from pathlib import Path

def create_fortigate_model():
    """Create a FortiGate 3D model representation"""
    model_data = {
        "asset": {
            "version": "2.0",
            "generator": "VSS+EraserAI-Temp",
            "copyright": "Fortinet Technologies"
        },
        "scenes": [{
            "nodes": [{
                "name": "FortiGate_600E",
                "mesh": 0,
                "translation": [0, 0, 0],
                "rotation": [0, 0, 0, 1],
                "scale": [1, 1, 1]
            }]
        }],
        "meshes": [{
            "name": "FortiGate_Mesh",
            "primitives": [{
                "attributes": {
                    "POSITION": 0,
                    "NORMAL": 1,
                    "TEXCOORD_0": 2
                },
                "indices": 0,
                "material": 0,
                "mode": 4
            }]
        }],
        "materials": [{
            "name": "FortiGate_Material",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.8, 0.3, 0.3, 1.0],
                "metallicFactor": 0.3,
                "roughnessFactor": 0.7
            }
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5123, "count": 36, "type": "SCALAR"},
            {"bufferView": 1, "componentType": 5126, "count": 24, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 24, "type": "VEC3"},
            {"bufferView": 3, "componentType": 5126, "count": 24, "type": "VEC2"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 144},
            {"buffer": 0, "byteOffset": 144, "byteLength": 288},
            {"buffer": 0, "byteOffset": 432, "byteLength": 288},
            {"buffer": 0, "byteOffset": 720, "byteLength": 192}
        ],
        "buffers": [{
            "byteLength": 912,
            "uri": "data:application/octet-stream;base64,AABAAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
        }]
    }
    
    return json.dumps(model_data, indent=2)

def create_fortiswitch_model():
    """Create a FortiSwitch 3D model representation"""
    model_data = {
        "asset": {
            "version": "2.0",
            "generator": "VSS+EraserAI-Temp",
            "copyright": "Fortinet Technologies"
        },
        "scenes": [{
            "nodes": [{
                "name": "FortiSwitch_148E",
                "mesh": 0,
                "translation": [0, 0, 0],
                "rotation": [0, 0, 0, 1],
                "scale": [1, 1, 1]
            }]
        }],
        "meshes": [{
            "name": "FortiSwitch_Mesh",
            "primitives": [{
                "attributes": {
                    "POSITION": 0,
                    "NORMAL": 1,
                    "TEXCOORD_0": 2
                },
                "indices": 0,
                "material": 0,
                "mode": 4
            }]
        }],
        "materials": [{
            "name": "FortiSwitch_Material",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.2, 0.8, 0.8, 1.0],
                "metallicFactor": 0.4,
                "roughnessFactor": 0.6
            }
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5123, "count": 36, "type": "SCALAR"},
            {"bufferView": 1, "componentType": 5126, "count": 24, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 24, "type": "VEC3"},
            {"bufferView": 3, "componentType": 5126, "count": 24, "type": "VEC2"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 144},
            {"buffer": 0, "byteOffset": 144, "byteLength": 288},
            {"buffer": 0, "byteOffset": 432, "byteLength": 288},
            {"buffer": 0, "byteOffset": 720, "byteLength": 192}
        ],
        "buffers": [{
            "byteLength": 912,
            "uri": "data:application/octet-stream;base64,AABAAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
        }]
    }
    
    return json.dumps(model_data, indent=2)

def create_fortiap_model():
    """Create a FortiAP 3D model representation"""
    model_data = {
        "asset": {
            "version": "2.0",
            "generator": "VSS+EraserAI-Temp",
            "copyright": "Fortinet Technologies"
        },
        "scenes": [{
            "nodes": [{
                "name": "FortiAP_432F",
                "mesh": 0,
                "translation": [0, 0, 0],
                "rotation": [0, 0, 0, 1],
                "scale": [1, 1, 1]
            }]
        }],
        "meshes": [{
            "name": "FortiAP_Mesh",
            "primitives": [{
                "attributes": {
                    "POSITION": 0,
                    "NORMAL": 1,
                    "TEXCOORD_0": 2
                },
                "indices": 0,
                "material": 0,
                "mode": 4
            }]
        }],
        "materials": [{
            "name": "FortiAP_Material",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.3, 0.6, 0.9, 1.0],
                "metallicFactor": 0.2,
                "roughnessFactor": 0.8
            }
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5123, "count": 36, "type": "SCALAR"},
            {"bufferView": 1, "componentType": 5126, "count": 24, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 24, "type": "VEC3"},
            {"bufferView": 3, "componentType": 5126, "count": 24, "type": "VEC2"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 144},
            {"buffer": 0, "byteOffset": 144, "byteLength": 288},
            {"buffer": 0, "byteOffset": 432, "byteLength": 288},
            {"buffer": 0, "byteOffset": 720, "byteLength": 192}
        ],
        "buffers": [{
            "byteLength": 912,
            "uri": "data:application/octet-stream;base64,AABAAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAIAAAACAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
        }]
    }
    
    return json.dumps(model_data, indent=2)

def main():
    """Create all 3D models"""
    print("🎨 Creating VSS + Eraser AI 3D Models...")
    
    output_dir = Path("/home/keith/enhanced-network-api-corporate/src/enhanced_network_api/static/3d-models")
    output_dir.mkdir(exist_ok=True)
    
    # Create FortiGate model
    forti_gate_model = create_fortigate_model()
    with open(output_dir / "FortiGate.gltf", "w") as f:
        f.write(forti_gate_model)
    print("  ✅ FortiGate.gltf created")
    
    # Create FortiSwitch model
    forti_switch_model = create_fortiswitch_model()
    with open(output_dir / "FortiSwitch.gltf", "w") as f:
        f.write(forti_switch_model)
    print("  ✅ FortiSwitch.gltf created")
    
    # Create FortiAP model
    forti_ap_model = create_fortiap_model()
    with open(output_dir / "FortinetAP.gltf", "w") as f:
        f.write(forti_ap_model)
    print("  ✅ FortinetAP.gltf created")
    
    print("\n🎯 VSS + Eraser AI 3D Models Ready!")
    print("📁 Location: /static/3d-models/")
    print("🔄 Replace these with your actual VSS + Eraser AI GLB files")
    
    # Update model paths in Babylon.js to use GLTF for testing
    print("\n🔧 Updating Babylon.js to use GLTF models...")
    
    babylon_file = Path("/home/keith/enhanced-network-api-corporate/src/enhanced_network_api/static/babylon_test.html")
    if babylon_file.exists():
        with open(babylon_file, "r") as f:
            content = f.read()
        
        # Update model paths to use GLTF
        content = content.replace(".glb", ".gltf")
        
        with open(babylon_file, "w") as f:
            f.write(content)
        
        print("  ✅ Updated Babylon.js to use GLTF models")
    
    print("\n🚀 VSS + Eraser AI integration complete!")

if __name__ == "__main__":
    main()
