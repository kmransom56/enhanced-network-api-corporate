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
from PIL import Image
import io

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
        
        # Use floats for maximum Babylon.js compatibility (models are small anyway)
        # Quantization can cause parsing issues with some loaders
        half_extents = [width / 2.0, height / 2.0, depth / 2.0]
        
        indices_bytes = self._pack_uint16(indices)
        positions_bytes = self._pack_floats(positions)
        normals_bytes = self._pack_floats(normals)  # Floats for compatibility
        texcoords_bytes = self._pack_floats(texcoords)  # Floats for compatibility
        
        buffer_bytes = indices_bytes + positions_bytes + normals_bytes + texcoords_bytes
        buffer_uri = "data:application/octet-stream;base64," + base64.b64encode(buffer_bytes).decode("ascii")
        
        vertex_count = len(positions) // 3
        
        # Create texture if enabled
        texture_data = None
        texture_index = None
        if self._should_use_texture(device_name, specs):
            texture_data, texture_uri = self._create_device_texture(device_name, specs)
            texture_index = 0
        
        accessor_indices = {
            "bufferView": 0,
            "componentType": 5123,  # UNSIGNED_SHORT
            "count": len(indices),
            "type": "SCALAR",
            "min": [0],
            "max": [vertex_count - 1]
        }
        
        pos_min = [-half_extents[0], -half_extents[1], -half_extents[2]]
        pos_max = [half_extents[0], half_extents[1], half_extents[2]]
        accessor_positions = {
            "bufferView": 1,
            "componentType": 5126,  # FLOAT (kept as float for compatibility)
            "count": vertex_count,
            "type": "VEC3",
            "min": pos_min,
            "max": pos_max
        }
        
        accessor_normals = {
            "bufferView": 2,
            "componentType": 5126,  # FLOAT (for compatibility)
            "count": vertex_count,
            "type": "VEC3"
        }
        
        accessor_texcoords = {
            "bufferView": 3,
            "componentType": 5126,  # FLOAT (for compatibility)
            "count": vertex_count,
            "type": "VEC2",
            "min": [0.0, 0.0],
            "max": [1.0, 1.0]
        }
        
        indices_length = len(indices_bytes)
        positions_length = len(positions_bytes)
        normals_length = len(normals_bytes)
        texcoords_length = len(texcoords_bytes)
        
        buffer_views = [
            {"buffer": 0, "byteOffset": 0, "byteLength": indices_length},
            {"buffer": 0, "byteOffset": indices_length, "byteLength": positions_length},
            {"buffer": 0, "byteOffset": indices_length + positions_length, "byteLength": normals_length},
            {"buffer": 0, "byteOffset": indices_length + positions_length + normals_length, "byteLength": texcoords_length}
        ]
        
        # Build material with optional texture
        material = {
            "name": f"{device_name}_Material",
            "doubleSided": True,
            "pbrMetallicRoughness": {
                "baseColorFactor": self.hex_to_rgba(specs.get("color", "#cccccc")),
                "metallicFactor": 0.3,
                "roughnessFactor": 0.7
            }
        }
        
        if texture_index is not None:
            material["pbrMetallicRoughness"]["baseColorTexture"] = {"index": texture_index}
        
        gltf_data = {
            "asset": {
                "version": "2.0",
                "generator": "VSS-Simulation-Linux-Optimized",
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
                    "features": specs.get("features", []),
                    "optimized": True,
                    "textured": texture_index is not None
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
        
        # Add texture if created
        if texture_data:
            gltf_data["textures"] = [{
                "sampler": 0,
                "source": 0
            }]
            gltf_data["images"] = [{
                "uri": texture_uri
            }]
            gltf_data["samplers"] = [{
                "magFilter": 9729,  # LINEAR
                "minFilter": 9729,  # LINEAR
                "wrapS": 10497,  # REPEAT
                "wrapT": 10497  # REPEAT
            }]
            # Add texture buffer view and accessor
            texture_buffer_view_idx = len(buffer_views)
            gltf_data["bufferViews"].append({
                "buffer": 1,
                "byteOffset": 0,
                "byteLength": len(texture_data)
            })
            gltf_data["buffers"].append({
                "byteLength": len(texture_data),
                "uri": texture_uri
            })
        
        return gltf_data
    
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
    
    def _quantize_positions(self, positions, half_extents):
        """Quantize positions to normalized shorts for size optimization"""
        quantized = []
        pos_min = [-half_extents[0], -half_extents[1], -half_extents[2]]
        pos_max = [half_extents[0], half_extents[1], half_extents[2]]
        
        for i in range(0, len(positions), 3):
            x, y, z = positions[i], positions[i+1], positions[i+2]
            # Normalize to 0-65535 range
            qx = int((x - pos_min[0]) / (pos_max[0] - pos_min[0]) * 65535) if pos_max[0] != pos_min[0] else 32767
            qy = int((y - pos_min[1]) / (pos_max[1] - pos_min[1]) * 65535) if pos_max[1] != pos_min[1] else 32767
            qz = int((z - pos_min[2]) / (pos_max[2] - pos_min[2]) * 65535) if pos_max[2] != pos_min[2] else 32767
            quantized.extend([max(0, min(65535, qx)), max(0, min(65535, qy)), max(0, min(65535, qz))])
        
        return quantized, pos_min, pos_max
    
    def _quantize_normals(self, normals):
        """Quantize normals to signed bytes (normalized) - more efficient than shorts"""
        quantized = []
        for i in range(0, len(normals), 3):
            x, y, z = normals[i], normals[i+1], normals[i+2]
            # Normalize to -127 to 127 range (signed byte)
            qx = int(x * 127)
            qy = int(y * 127)
            qz = int(z * 127)
            quantized.extend([max(-127, min(127, qx)), max(-127, min(127, qy)), max(-127, min(127, qz))])
        return quantized
    
    def _should_use_texture(self, device_name, specs):
        """Determine if texture should be generated for this device"""
        # Enable textures for all devices by default
        return True
    
    def _create_device_texture(self, device_name, specs):
        """Create a procedural texture for the device"""
        try:
            from PIL import ImageDraw
            import math
            
            # Create a 256x256 texture with device-specific pattern
            size = 256
            base_color = self.hex_to_rgb(specs.get("color", "#cccccc"))
            img = Image.new('RGB', (size, size), color=base_color)
            draw = ImageDraw.Draw(img)
            
            # Lighten base color for highlights
            highlight = tuple(min(255, c + 30) for c in base_color)
            shadow = tuple(max(0, c - 30) for c in base_color)
            
            # Draw device-specific patterns
            if 'switch' in device_name.lower():
                # Grid pattern for switches
                for i in range(0, size, 16):
                    draw.line([(i, 0), (i, size)], fill=shadow, width=1)
                    draw.line([(0, i), (size, i)], fill=shadow, width=1)
                # Port indicators
                for i in range(16, size-16, 32):
                    draw.rectangle([i-2, 8, i+2, 12], fill=highlight)
            
            elif 'gate' in device_name.lower():
                # Port indicators for FortiGate
                for i in range(8, size-8, 32):
                    draw.ellipse([i-4, 8, i+4, 16], fill=highlight)
                # Status LED pattern
                draw.ellipse([size-20, 8, size-12, 16], fill=(255, 200, 0))
            
            elif 'ap' in device_name.lower():
                # Antenna pattern for APs
                center = size // 2
                draw.ellipse([center-20, center-20, center+20, center+20], fill=highlight)
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    x1 = center + int(30 * math.cos(rad))
                    y1 = center + int(30 * math.sin(rad))
                    draw.line([(center, center), (x1, y1)], fill=shadow, width=2)
            
            # Add subtle border
            draw.rectangle([0, 0, size-1, size-1], outline=shadow, width=2)
            
            # Convert to PNG bytes (optimized)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG', optimize=True, compress_level=9)
            img_bytes.seek(0)
            texture_data = img_bytes.getvalue()
            
            # Create data URI
            texture_uri = "data:image/png;base64," + base64.b64encode(texture_data).decode("ascii")
            
            print(f"  ✅ Created texture ({len(texture_data)} bytes) for {device_name}")
            return texture_data, texture_uri
        except Exception as e:
            print(f"  ⚠️ Failed to create texture for {device_name}: {e}")
            # Return None to disable texture
            return None, None
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def _pack_uint16(values):
        return struct.pack(f"<{len(values)}H", *values)
    
    @staticmethod
    def _pack_int8(values):
        """Pack signed 8-bit integers (bytes)"""
        return struct.pack(f"<{len(values)}b", *values)
    
    @staticmethod
    def _pack_int16(values):
        """Pack signed 16-bit integers"""
        return struct.pack(f"<{len(values)}h", *values)
    
    @staticmethod
    def _pack_uint16_norm(values):
        """Pack normalized UV coordinates as uint16 (0-65535 maps to 0.0-1.0)"""
        quantized = []
        for i in range(0, len(values), 2):
            u, v = values[i], values[i+1]
            qu = int(max(0, min(1.0, u)) * 65535)
            qv = int(max(0, min(1.0, v)) * 65535)
            quantized.extend([qu, qv])
        return struct.pack(f"<{len(quantized)}H", *quantized)
    
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
