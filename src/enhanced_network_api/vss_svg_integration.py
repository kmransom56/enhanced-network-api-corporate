#!/usr/bin/env python3
"""
VSS to SVG Integration for Network Topology Workflow
Extracts device icons from Fortinet VSS (Visio Stencil) files and integrates with Babylon.js
"""

import olefile
import struct
from pathlib import Path
from PIL import Image
import io
import base64
import json
import logging
from typing import Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


class VSSIconExtractor:
    """Extract and process icons from Fortinet VSS files"""
    
    def __init__(self, vss_path: Path, output_dir: Path = Path('realistic_device_svgs')):
        self.vss_path = vss_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_icons: List[Dict] = []
        
    def extract_all_icons(self) -> List[Dict]:
        """
        Extract all icons from VSS file
        
        Returns:
            List of dicts with icon metadata and paths
        """
        log.info(f"Extracting icons from {self.vss_path}")
        
        try:
            ole = olefile.OleFileIO(self.vss_path)
            visio_data = ole.openstream(['VisioDocument']).read()
            ole.close()
            
            # Extract JPG images (most common in VSS files)
            jpg_icons = self._extract_jpg_graphics(visio_data)
            
            # Extract BMP images (fallback)
            bmp_icons = self._extract_bmp_graphics(visio_data)
            
            all_icons = jpg_icons + bmp_icons
            
            # Convert to SVG and save
            for icon in all_icons:
                svg_path = self._convert_to_svg(icon)
                icon['svg_path'] = str(svg_path)
                icon['svg_url'] = f"/realistic_device_svgs/{svg_path.name}"
                self.extracted_icons.append(icon)
            
            log.info(f"Extracted {len(self.extracted_icons)} icons")
            return self.extracted_icons
            
        except Exception as e:
            log.error(f"Failed to extract icons from VSS: {e}")
            return []
    
    def _extract_jpg_graphics(self, visio_data: bytes) -> List[Dict]:
        """Extract JPG graphics from Visio data"""
        icons = []
        start = 0
        jpg_index = 0
        
        while True:
            pos = visio_data.find(b'\xff\xd8\xff', start)
            if pos == -1:
                break
            
            # Find end marker
            end_pos = visio_data.find(b'\xff\xd9', pos + 3)
            if end_pos == -1:
                start = pos + 1
                continue
            
            jpg_data = visio_data[pos:end_pos+2]
            
            # Validate with PIL
            try:
                img = Image.open(io.BytesIO(jpg_data))
                width, height = img.size
                
                # Filter out very small images (likely not device icons)
                if width >= 32 and height >= 32:
                    icons.append({
                        'type': 'jpg',
                        'data': jpg_data,
                        'name': f'fortinet_icon_{jpg_index:03d}',
                        'width': width,
                        'height': height,
                        'position': pos
                    })
                    jpg_index += 1
                    log.debug(f"Found JPG icon: {width}x{height} at position {pos}")
            except:
                pass
            
            start = pos + 1
        
        return icons
    
    def _extract_bmp_graphics(self, visio_data: bytes) -> List[Dict]:
        """Extract BMP graphics from Visio data"""
        icons = []
        start = 0
        bmp_index = 0
        
        while True:
            pos = visio_data.find(b'BM', start)
            if pos == -1:
                break
            
            # Check if valid BMP header
            if pos + 14 > len(visio_data):
                break
            
            try:
                size = struct.unpack('<I', visio_data[pos+2:pos+6])[0]
                if 1000 < size < 1000000:  # Reasonable size range
                    bmp_data = visio_data[pos:pos+size]
                    
                    # Validate with PIL
                    img = Image.open(io.BytesIO(bmp_data))
                    width, height = img.size
                    
                    if width >= 32 and height >= 32:
                        icons.append({
                            'type': 'bmp',
                            'data': bmp_data,
                            'name': f'fortinet_icon_bmp_{bmp_index:03d}',
                            'width': width,
                            'height': height,
                            'position': pos
                        })
                        bmp_index += 1
                        log.debug(f"Found BMP icon: {width}x{height} at position {pos}")
            except:
                pass
            
            start = pos + 1
        
        return icons
    
    def _convert_to_svg(self, icon: Dict) -> Path:
        """Convert extracted icon to SVG format with embedded image"""
        svg_path = self.output_dir / f"{icon['name']}.svg"
        
        # Encode image as base64
        data_b64 = base64.b64encode(icon['data']).decode('utf-8')
        
        # Determine MIME type
        mime_type = 'image/jpeg' if icon['type'] == 'jpg' else 'image/bmp'
        
        # Create SVG with embedded image
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{icon['width']}" height="{icon['height']}" 
     xmlns="http://www.w3.org/2000/svg" 
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {icon['width']} {icon['height']}">
    <title>{icon['name']}</title>
    <desc>Extracted from Fortinet VSS: {self.vss_path.name}</desc>
    
    <!-- Device icon image -->
    <image x="0" y="0" width="{icon['width']}" height="{icon['height']}" 
           xlink:href="data:{mime_type};base64,{data_b64}" 
           preserveAspectRatio="xMidYMid meet"/>
    
    <!-- Optional: Add a subtle border for visibility -->
    <rect x="1" y="1" width="{icon['width']-2}" height="{icon['height']-2}" 
          fill="none" stroke="rgba(0,0,0,0.1)" stroke-width="1"/>
</svg>'''
        
        svg_path.write_text(svg_content, encoding='utf-8')
        log.debug(f"Created SVG: {svg_path}")
        
        return svg_path
    
    def create_icon_mapping(self, device_types: List[str]) -> Dict[str, str]:
        """
        Create mapping between device types and extracted SVG icons
        
        Args:
            device_types: List of device types to map (e.g., ['fortigate', 'fortiswitch', 'fortiap'])
            
        Returns:
            Dict mapping device type to SVG path
        """
        mapping = {}
        
        # Simple heuristic: assign icons in order of extraction
        # In a real implementation, you might use image recognition or naming patterns
        for i, device_type in enumerate(device_types):
            if i < len(self.extracted_icons):
                mapping[device_type] = self.extracted_icons[i]['svg_url']
            else:
                # Fallback to generated icon
                mapping[device_type] = f"/realistic_device_svgs/generic_{device_type}.svg"
        
        return mapping
    
    def export_manifest(self) -> Path:
        """
        Export icon manifest for use by workflow
        
        Returns:
            Path to manifest JSON file
        """
        manifest_path = self.output_dir / 'vss_icon_manifest.json'
        
        manifest = {
            'source_vss': str(self.vss_path),
            'extraction_date': str(Path(self.vss_path).stat().st_mtime),
            'total_icons': len(self.extracted_icons),
            'icons': [
                {
                    'name': icon['name'],
                    'svg_path': icon['svg_path'],
                    'svg_url': icon['svg_url'],
                    'width': icon['width'],
                    'height': icon['height'],
                    'type': icon['type']
                }
                for icon in self.extracted_icons
            ]
        }
        
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        log.info(f"Exported icon manifest: {manifest_path}")
        
        return manifest_path


class VSSBabylonIntegration:
    """Integrate VSS-extracted icons with Babylon.js workflow"""
    
    def __init__(self, vss_extractor: VSSIconExtractor):
        self.extractor = vss_extractor
        self.icon_mapping: Dict[str, str] = {}
    
    def setup_device_icons(self, device_list: List[Dict]) -> List[Dict]:
        """
        Assign VSS-extracted icons to devices
        
        Args:
            device_list: List of device dicts from workflow
            
        Returns:
            Updated device list with icon_svg paths
        """
        # Extract device types
        device_types = list(set(d.get('type', 'generic') for d in device_list))
        
        # Create icon mapping
        self.icon_mapping = self.extractor.create_icon_mapping(device_types)
        
        # Assign icons to devices
        for device in device_list:
            device_type = device.get('type', 'generic')
            
            # Priority: VSS icon > existing icon > generated icon
            if device_type in self.icon_mapping and not device.get('icon_svg'):
                device['icon_svg'] = self.icon_mapping[device_type]
                device['icon_source'] = 'vss'
            elif not device.get('icon_svg'):
                device['icon_svg'] = self._get_fallback_icon(device_type)
                device['icon_source'] = 'generated'
        
        return device_list
    
    def _get_fallback_icon(self, device_type: str) -> str:
        """Get fallback icon for device type"""
        return f"/realistic_device_svgs/generated_{device_type.lower()}.svg"
    
    def create_babylon_texture_map(self) -> Dict[str, Dict]:
        """
        Create texture mapping for Babylon.js 3D models
        
        Returns:
            Dict mapping device types to texture configurations
        """
        texture_map = {}
        
        for device_type, svg_url in self.icon_mapping.items():
            texture_map[device_type] = {
                'diffuse_texture': svg_url,
                'emissive_texture': svg_url,
                'emissive_color': [0.3, 0.3, 0.3],  # Slight glow
                'diffuse_color': [1.0, 1.0, 1.0],
                'specular_color': [0.1, 0.1, 0.1],
                'use_alpha': True
            }
        
        return texture_map


# Convenience function for workflow integration
def extract_and_integrate_vss_icons(
    vss_path: str,
    device_list: List[Dict],
    output_dir: str = 'realistic_device_svgs'
) -> Tuple[List[Dict], Dict]:
    """
    Complete VSS extraction and device integration workflow
    
    Args:
        vss_path: Path to Fortinet VSS file
        device_list: List of devices from network discovery
        output_dir: Directory for SVG output
        
    Returns:
        Tuple of (updated device list, icon manifest)
    """
    log.info("Starting VSS icon extraction and integration")
    
    # Extract icons from VSS
    extractor = VSSIconExtractor(Path(vss_path), Path(output_dir))
    extracted_icons = extractor.extract_all_icons()
    
    if not extracted_icons:
        log.warning("No icons extracted from VSS, using generated icons")
        return device_list, {}
    
    # Export manifest
    manifest_path = extractor.export_manifest()
    
    # Integrate with Babylon.js workflow
    integration = VSSBabylonIntegration(extractor)
    updated_devices = integration.setup_device_icons(device_list)
    texture_map = integration.create_babylon_texture_map()
    
    log.info(f"VSS integration complete: {len(extracted_icons)} icons assigned to {len(updated_devices)} devices")
    
    return updated_devices, {
        'manifest_path': str(manifest_path),
        'texture_map': texture_map,
        'icon_count': len(extracted_icons)
    }


# CLI usage example
def main():
    """Example usage of VSS extraction"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python vss_svg_integration.py <path-to-vss-file>")
        sys.exit(1)
    
    vss_path = Path(sys.argv[1])
    if not vss_path.exists():
        print(f"Error: VSS file not found: {vss_path}")
        sys.exit(1)
    
    # Extract icons
    extractor = VSSIconExtractor(vss_path)
    icons = extractor.extract_all_icons()
    
    print(f"\n=== VSS Icon Extraction Results ===")
    print(f"Source: {vss_path}")
    print(f"Extracted: {len(icons)} icons")
    print(f"Output: {extractor.output_dir}")
    
    # Export manifest
    manifest_path = extractor.export_manifest()
    print(f"Manifest: {manifest_path}")
    
    # Show extracted icons
    print("\nExtracted Icons:")
    for icon in icons:
        print(f"  - {icon['name']}: {icon['width']}x{icon['height']} ({icon['type']}) -> {icon['svg_url']}")


if __name__ == '__main__':
    main()
