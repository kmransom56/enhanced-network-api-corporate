#!/usr/bin/env python3
"""
Convert legacy VSS files to SVG format with proper graphics extraction
"""

import olefile
import struct
import base64
from pathlib import Path
from PIL import Image
import io
import xml.etree.ElementTree as ET
import re

class VSSGraphicsExtractor:
    def __init__(self, vss_path: Path):
        self.vss_path = vss_path
        self.visio_data = None
        self.graphics = []
        
    def load_vss(self):
        """Load the VSS file and extract VisioDocument stream"""
        try:
            ole = olefile.OleFileIO(self.vss_path)
            self.visio_data = ole.openstream(['VisioDocument']).read()
            ole.close()
            return True
        except Exception as e:
            print(f"Failed to load VSS file: {e}")
            return False
    
    def extract_graphics(self):
        """Extract graphics from the VSS file"""
        if not self.visio_data:
            return []
        
        graphics = []
        
        # Extract JPG images
        jpg_positions = self._find_jpg_positions()
        for i, pos in enumerate(jpg_positions):
            try:
                jpg_data = self._extract_jpg_at_position(pos)
                if jpg_data:
                    graphics.append({
                        'type': 'jpg',
                        'data': jpg_data,
                        'name': f'fortigate_{i+1}',
                        'position': pos
                    })
            except Exception as e:
                print(f"Failed to extract JPG at position {pos}: {e}")
        
        # Extract BMP images
        bmp_positions = self._find_bmp_positions()
        for i, pos in enumerate(bmp_positions):
            try:
                bmp_data = self._extract_bmp_at_position(pos)
                if bmp_data:
                    graphics.append({
                        'type': 'bmp', 
                        'data': bmp_data,
                        'name': f'fortigate_bmp_{i+1}',
                        'position': pos
                    })
            except Exception as e:
                print(f"Failed to extract BMP at position {pos}: {e}")
        
        return graphics
    
    def _find_jpg_positions(self):
        """Find JPG start positions"""
        positions = []
        start = 0
        while True:
            pos = self.visio_data.find(b'\xff\xd8\xff', start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        return positions
    
    def _find_bmp_positions(self):
        """Find BMP start positions"""
        positions = []
        start = 0
        while True:
            pos = self.visio_data.find(b'BM', start)
            if pos == -1:
                break
            # Check if this looks like a valid BMP header
            if pos + 14 < len(self.visio_data):
                size = struct.unpack('<I', self.visio_data[pos+2:pos+6])[0]
                if size > 1000 and size < 1000000:  # Reasonable size range
                    positions.append(pos)
            start = pos + 1
        return positions
    
    def _extract_jpg_at_position(self, pos):
        """Extract JPG data at given position"""
        # Find JPG end marker
        end_pos = self.visio_data.find(b'\xff\xd9', pos + 3)
        if end_pos == -1:
            # Try to estimate size by looking for next JPG start or reasonable limit
            next_jpg = self.visio_data.find(b'\xff\xd8\xff', pos + 10)
            if next_jpg != -1:
                end_pos = next_jpg - 1
            else:
                end_pos = pos + 50000  # Max 50KB
        
        jpg_data = self.visio_data[pos:end_pos+2]
        
        # Validate with PIL
        try:
            img = Image.open(io.BytesIO(jpg_data))
            return jpg_data
        except:
            return None
    
    def _extract_bmp_at_position(self, pos):
        """Extract BMP data at given position"""
        # Read BMP header to get size
        if pos + 14 > len(self.visio_data):
            return None
        
        size = struct.unpack('<I', self.visio_data[pos+2:pos+6])[0]
        if size < 1000 or size > 1000000:
            return None
        
        bmp_data = self.visio_data[pos:pos+size]
        
        # Validate with PIL
        try:
            img = Image.open(io.BytesIO(bmp_data))
            return bmp_data
        except:
            return None
    
    def convert_graphics_to_svg(self, output_dir: Path):
        """Convert extracted graphics to SVG files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        svg_files = []
        
        for i, graphic in enumerate(self.graphics):
            try:
                svg_content = self._create_svg_from_graphic(graphic, i)
                svg_path = output_dir / f"{graphic['name']}.svg"
                svg_path.write_text(svg_content, encoding='utf-8')
                svg_files.append(svg_path)
                print(f"Created SVG: {svg_path}")
            except Exception as e:
                print(f"Failed to convert graphic {i} to SVG: {e}")
        
        return svg_files
    
    def _create_svg_from_graphic(self, graphic, index):
        """Create SVG from graphic data"""
        data_b64 = base64.b64encode(graphic['data']).decode('utf-8')
        
        # Get image dimensions
        try:
            img = Image.open(io.BytesIO(graphic['data']))
            width, height = img.size
        except:
            width, height = 200, 200  # Default size
        
        if graphic['type'] == 'jpg':
            mime_type = 'image/jpeg'
        elif graphic['type'] == 'bmp':
            mime_type = 'image/bmp'
        else:
            mime_type = 'image/png'
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <title>{graphic['name']}</title>
    <desc>Extracted from VSS file: {self.vss_path.name}</desc>
    
    <!-- Main device image -->
    <image x="0" y="0" width="{width}" height="{height}" 
           xlink:href="data:{mime_type};base64,{data_b64}" />
    
    <!-- Device label -->
    <text x="{width//2}" y="{height-5}" text-anchor="middle" 
          font-family="Arial, sans-serif" font-size="10" fill="black">
        {graphic['name']}
    </text>
    
    <!-- Border for visibility -->
    <rect x="0" y="0" width="{width}" height="{height}" 
          fill="none" stroke="gray" stroke-width="1" />
</svg>'''
        
        return svg_content

def main():
    vss_path = Path('/home/keith/obsidian-vault/00-Inbox/chat-copilot-import/DrawIO_project/fortinet_visio/FortiGate_Series_R22_2025Q2.vss')
    output_dir = Path('real_fortinet_svgs')
    
    print(f"Converting VSS to SVG: {vss_path}")
    
    extractor = VSSGraphicsExtractor(vss_path)
    
    if not extractor.load_vss():
        print("Failed to load VSS file")
        return
    
    graphics = extractor.extract_graphics()
    print(f"Found {len(graphics)} graphics")
    
    svg_files = extractor.convert_graphics_to_svg(output_dir)
    print(f"Created {len(svg_files)} SVG files")
    
    # Show first SVG as example
    if svg_files:
        print(f"\nExample SVG content:")
        print(svg_files[0].read_text()[:500] + '...')

if __name__ == '__main__':
    main()
