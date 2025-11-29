#!/usr/bin/env python3
"""
VSS 3D Model Extraction - Linux Compatible Version
This script simulates VSS extraction on Linux systems
"""

import base64
import json
import struct
from pathlib import Path
from datetime import datetime

class VSSEXtractionLinux:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.output_dir = self.base_dir / "vss_exports"
        self.source_dir = self.base_dir / "source_models"
        
        # Fortinet device specifications
        self.device_models = {
            "FortiGate_600E": {
                "type": "fortigate",
                "description": "FortiGate 600E Next-Generation Firewall",
                "dimensions": {"width": 1.0, "height": 0.5, "depth": 0.8},
                "color": "#cc3333",
                "features": ["ports", "leds", "cooling_vents", "power_supply"]
            },
            "FortiSwitch_148E": {
                "type": "fortiswitch", 
                "description": "FortiSwitch 148E Secure Access Switch",
                "dimensions": {"width": 0.8, "height": 0.1, "depth": 0.6},
                "color": "#33cccc",
                "features": ["ports", "leds", "rack_mounts", "power"]
            },
            "FortiAP_432F": {
                "type": "fortiap",
                "description": "FortiAP 432F Wireless Access Point", 
                "dimensions": {"width": 0.2, "height": 0.3, "depth": 0.2},
                "color": "#3366cc",
                "features": ["antennas", "leds", "mounting_bracket", "ethernet_ports"]
            }
        }
    
    def create_directories(self):
        """Create necessary directories"""
        print("🔧 Creating VSS extraction directories...")
        
        for directory in [self.output_dir, self.source_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Created: {directory}")
    
    def create_placeholder_models(self):
        """Create placeholder GLTF models (simulating VSS extraction)"""
        print("🎨 Creating placeholder GLTF models (VSS simulation)...")
        
        for device_name, specs in self.device_models.items():
            gltf_data = self._build_placeholder_gltf(device_name, specs)
            
            output_file = self.output_dir / f"{device_name}.gltf"
            with open(output_file, "w") as f:
                json.dump(gltf_data, f, indent=2)
            
            print(f"  ✅ Created: {device_name}.gltf")
            
            metadata = {
                "device_name": device_name,
                "extraction_method": "VSS-Simulation-Linux",
                "extraction_date": datetime.now().isoformat(),
                "specifications": specs,
                "file_format": "GLTF",
                "ready_for_eraser_ai": True
            }
            
            metadata_file = self.output_dir / f"{device_name}_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
    
    def _build_placeholder_gltf(self, device_name, specs):
        dimensions = specs.get("dimensions", {"width": 1.0, "height": 1.0, "depth": 1.0})
        width = float(dimensions.get("width", 1.0))
        height = float(dimensions.get("height", 1.0))
        depth = float(dimensions.get("depth", 1.0))
        
        positions, normals, texcoords, indices = self._create_cuboid_geometry(width, height, depth)
        
        indices_bytes = self._pack_uint16(indices)
        positions_bytes = self._pack_floats(positions)
        normals_bytes = self._pack_floats(normals)
        texcoords_bytes = self._pack_floats(texcoords)
        
        buffer_bytes = indices_bytes + positions_bytes + normals_bytes + texcoords_bytes
        buffer_uri = "data:application/octet-stream;base64," + base64.b64encode(buffer_bytes).decode("ascii")
        
        vertex_count = len(positions) // 3
        accessor_indices = {
            "bufferView": 0,
            "componentType": 5123,
            "count": len(indices),
            "type": "SCALAR",
            "min": [0],
            "max": [vertex_count - 1]
        }
        half_extents = [width / 2.0, height / 2.0, depth / 2.0]
        accessor_positions = {
            "bufferView": 1,
            "componentType": 5126,
            "count": vertex_count,
            "type": "VEC3",
            "min": [-half_extents[0], -half_extents[1], -half_extents[2]],
            "max": [half_extents[0], half_extents[1], half_extents[2]]
        }
        accessor_normals = {
            "bufferView": 2,
            "componentType": 5126,
            "count": vertex_count,
            "type": "VEC3"
        }
        accessor_texcoords = {
            "bufferView": 3,
            "componentType": 5126,
            "count": vertex_count,
            "type": "VEC2",
            "min": [0.0, 0.0],
            "max": [1.0, 1.0]
        }
        
        indices_length = len(indices_bytes)
        positions_length = len(positions_bytes)
        normals_length = len(normals_bytes)
        
        buffer_views = [
            {"buffer": 0, "byteOffset": 0, "byteLength": indices_length},
            {"buffer": 0, "byteOffset": indices_length, "byteLength": positions_length},
            {"buffer": 0, "byteOffset": indices_length + positions_length, "byteLength": normals_length},
            {
                "buffer": 0,
                "byteOffset": indices_length + positions_length + normals_length,
                "byteLength": len(texcoords_bytes)
            }
        ]
        
        material = {
            "name": f"{device_name}_Material",
            "doubleSided": True,
            "pbrMetallicRoughness": {
                "baseColorFactor": self.hex_to_rgba(specs.get("color", "#cccccc")),
                "metallicFactor": 0.3,
                "roughnessFactor": 0.7
            }
        }
        
        return {
            "asset": {
                "version": "2.0",
                "generator": "VSS-Simulation-Linux",
                "copyright": "Fortinet Technologies"
            },
            "scene": 0,
            "scenes": [{
                "nodes": [0]
            }],
            "nodes": [{
                "name": device_name,
                "mesh": 0,
                "translation": [0, 0, 0],
                "rotation": [0, 0, 0, 1],
                "scale": [1, 1, 1],
                "extras": {
                    "device_type": specs.get("type"),
                    "features": specs.get("features", [])
                }
            }],
            "meshes": [{
                "name": f"{device_name}_Mesh",
                "primitives": [{
                    "attributes": {
                        "POSITION": 1,
                        "NORMAL": 2,
                        "TEXCOORD_0": 3
                    },
                    "indices": 0,
                    "material": 0,
                    "mode": 4
                }]
            }],
            "materials": [material],
            "accessors": [
                accessor_indices,
                accessor_positions,
                accessor_normals,
                accessor_texcoords
            ],
            "bufferViews": buffer_views,
            "buffers": [{
                "byteLength": len(buffer_bytes),
                "uri": buffer_uri
            }]
        }
    
    def _create_cuboid_geometry(self, width, height, depth):
        hx = width / 2.0
        hy = height / 2.0
        hz = depth / 2.0
        
        positions = [
            # Front (+Z)
            -hx, -hy, hz,
            hx, -hy, hz,
            hx, hy, hz,
            -hx, hy, hz,
            # Back (-Z)
            -hx, -hy, -hz,
            -hx, hy, -hz,
            hx, hy, -hz,
            hx, -hy, -hz,
            # Top (+Y)
            -hx, hy, -hz,
            -hx, hy, hz,
            hx, hy, hz,
            hx, hy, -hz,
            # Bottom (-Y)
            -hx, -hy, -hz,
            hx, -hy, -hz,
            hx, -hy, hz,
            -hx, -hy, hz,
            # Right (+X)
            hx, -hy, -hz,
            hx, hy, -hz,
            hx, hy, hz,
            hx, -hy, hz,
            # Left (-X)
            -hx, -hy, -hz,
            -hx, -hy, hz,
            -hx, hy, hz,
            -hx, hy, -hz,
        ]
        
        normals = [
            # Front
            0, 0, 1,
            0, 0, 1,
            0, 0, 1,
            0, 0, 1,
            # Back
            0, 0, -1,
            0, 0, -1,
            0, 0, -1,
            0, 0, -1,
            # Top
            0, 1, 0,
            0, 1, 0,
            0, 1, 0,
            0, 1, 0,
            # Bottom
            0, -1, 0,
            0, -1, 0,
            0, -1, 0,
            0, -1, 0,
            # Right
            1, 0, 0,
            1, 0, 0,
            1, 0, 0,
            1, 0, 0,
            # Left
            -1, 0, 0,
            -1, 0, 0,
            -1, 0, 0,
            -1, 0, 0,
        ]
        
        texcoords = [
            # Front
            0, 0,
            1, 0,
            1, 1,
            0, 1,
            # Back
            0, 0,
            1, 0,
            1, 1,
            0, 1,
            # Top
            0, 0,
            1, 0,
            1, 1,
            0, 1,
            # Bottom
            0, 0,
            1, 0,
            1, 1,
            0, 1,
            # Right
            0, 0,
            1, 0,
            1, 1,
            0, 1,
            # Left
            0, 0,
            1, 0,
            1, 1,
            0, 1,
        ]
        
        indices = []
        for face in range(6):
            base = face * 4
            indices.extend([base, base + 1, base + 2, base, base + 2, base + 3])
        
        return positions, normals, texcoords, indices
    
    @staticmethod
    def _pack_uint16(values):
        return struct.pack(f"<{len(values)}H", *values)
    
    @staticmethod
    def _pack_floats(values):
        return struct.pack(f"<{len(values)}f", *values)
    
    def hex_to_rgba(self, hex_color):
        """Convert hex color to RGBA"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return [r, g, b, 1.0]
    
    def create_extraction_report(self):
        """Create extraction report"""
        print("📋 Creating extraction report...")
        
        report = {
            "extraction_date": datetime.now().isoformat(),
            "method": "VSS-Simulation-Linux",
            "total_devices": len(self.device_models),
            "devices_extracted": list(self.device_models.keys()),
            "output_directory": str(self.output_dir),
            "file_format": "GLTF",
            "next_step": "Eraser AI Processing",
            "ready_for_eraser_ai": True
        }
        
        report_file = self.output_dir / "extraction_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"  ✅ Report saved: {report_file}")
        return report
    
    def run_extraction(self):
        """Run the complete VSS extraction process"""
        print("🚀 VSS 3D Model Extraction - Linux Version")
        print("=" * 50)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Create directories
        self.create_directories()
        
        # Create placeholder models
        self.create_placeholder_models()
        
        # Create extraction report
        report = self.create_extraction_report()
        
        print("\n🎯 VSS Extraction Complete!")
        print("=" * 50)
        print(f"✅ Devices extracted: {report['total_devices']}")
        print(f"✅ Output directory: {report['output_directory']}")
        print(f"✅ File format: {report['file_format']}")
        print(f"✅ Ready for Eraser AI: {report['ready_for_eraser_ai']}")
        
        print(f"\n📋 Extracted Files:")
        for device in report['devices_extracted']:
            print(f"  - {device}.gltf")
            print(f"  - {device}_metadata.json")
        
        print(f"\n🚀 Next Step:")
        print(f"cd /home/keith/enhanced-network-api-corporate/eraser_ai_processed")
        print(f"python eraser_ai_processing_linux.py")
        
        return report

if __name__ == "__main__":
    extractor = VSSEXtractionLinux()
    extractor.run_extraction()
