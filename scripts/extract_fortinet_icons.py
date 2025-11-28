#!/usr/bin/env python3
"""
Extract Fortinet SVG icons from DrawIO libraries for VSS + Eraser AI workflow
"""

import json
import base64
import os
import re
from pathlib import Path

def extract_svg_from_base64(base64_data):
    """Extract SVG content from base64 data URI"""
    # Remove data:image/svg+xml;base64, prefix if present
    if base64_data.startswith('data:image/svg+xml;base64,'):
        base64_data = base64_data.split(',')[1]
    
    try:
        svg_content = base64.b64decode(base64_data).decode('utf-8')
        return svg_content
    except Exception as e:
        print(f"Error decoding base64: {e}")
        return None

def clean_svg_content(svg_content):
    """Clean and optimize SVG content for 3D rendering"""
    if not svg_content:
        return None
    
    # Remove XML declaration and DOCTYPE
    svg_content = re.sub(r'<\?xml[^>]*\?>', '', svg_content)
    svg_content = re.sub(r'<!DOCTYPE[^>]*>', '', svg_content)
    
    # Remove comments
    svg_content = re.sub(r'<!--.*?-->', '', svg_content, flags=re.DOTALL)
    
    # Add viewBox if missing (standardize to 192x192)
    if 'viewBox' not in svg_content:
        svg_content = svg_content.replace('<svg', '<svg viewBox="0 0 192 192"', 1)
    
    # Remove Adobe Illustrator generator comments
    svg_content = re.sub(r'<!-- Generator:.*?-->', '', svg_content, flags=re.DOTALL)
    
    return svg_content.strip()

def extract_icons_from_library(library_path, output_dir):
    """Extract all SVG icons from a DrawIO library"""
    print(f"Processing library: {library_path}")
    
    with open(library_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove <mxlibrary> wrapper if present
    if content.startswith('<mxlibrary>'):
        content = content[11:]  # Remove <mxlibrary>
        if content.endswith('</mxlibrary>'):
            content = content[:-12]  # Remove </mxlibrary>
    
    # Parse JSON
    try:
        library_data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  ❌ Error parsing JSON: {e}")
        return 0
    
    extracted_count = 0
    
    for item in library_data:
        title = item.get('title', 'unknown')
        base64_data = item.get('data', '')
        
        if not base64_data:
            continue
        
        # Extract and clean SVG
        svg_content = extract_svg_from_base64(base64_data)
        if not svg_content:
            continue
        
        svg_content = clean_svg_content(svg_content)
        if not svg_content:
            continue
        
        # Create safe filename
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        filename = f"{safe_title}.svg"
        
        # Save SVG file
        output_path = output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        extracted_count += 1
        print(f"  ✓ Extracted: {filename}")
    
    return extracted_count

def categorize_icons(output_dir):
    """Categorize icons by device type for easy access"""
    categories = {
        'fortigate': [],
        'fortiswitch': [],
        'fortiap': [],
        'fortimanager': [],
        'fortianalyzer': [],
        'other': []
    }
    
    for svg_file in output_dir.glob('*.svg'):
        filename = svg_file.name.lower()
        
        if 'fortigate' in filename or 'fg' in filename:
            categories['fortigate'].append(svg_file.name)
        elif 'fortiswitch' in filename or 'fsw' in filename or 'switch' in filename:
            categories['fortiswitch'].append(svg_file.name)
        elif 'fortiap' in filename or 'fap' in filename or 'ap' in filename:
            categories['fortiap'].append(svg_file.name)
        elif 'fortimanager' in filename or 'fmg' in filename or 'manager' in filename:
            categories['fortimanager'].append(svg_file.name)
        elif 'fortianalyzer' in filename or 'faz' in filename or 'analyzer' in filename:
            categories['fortianalyzer'].append(svg_file.name)
        else:
            categories['other'].append(svg_file.name)
    
    return categories

def create_icon_mapping(categories, output_dir):
    """Create mapping file for the topology system"""
    mapping = {
        "device_types": {
            "fortigate": {
                "primary_icon": "FortiGate.svg",
                "variants": [f for f in categories['fortigate'] if f != 'FortiGate.svg'],
                "model_path": "/static/3d-models/FortiGate.glb",
                "description": "FortiGate Next-Generation Firewall"
            },
            "fortiswitch": {
                "primary_icon": "FortiSwitch.svg", 
                "variants": [f for f in categories['fortiswitch'] if f != 'FortiSwitch.svg'],
                "model_path": "/static/3d-models/FortiSwitch.glb",
                "description": "FortiSwitch Secure Access Switch"
            },
            "fortiap": {
                "primary_icon": "FortiAP.svg",
                "variants": [f for f in categories['fortiap'] if f != 'FortiAP.svg'],
                "model_path": "/static/3d-models/FortinetAP.glb", 
                "description": "FortiAP Wireless Access Point"
            },
            "fortimanager": {
                "primary_icon": "FortiManager.svg",
                "variants": [f for f in categories['fortimanager']],
                "model_path": "/static/3d-models/FortiManager.glb",
                "description": "FortiManager Centralized Management"
            },
            "fortianalyzer": {
                "primary_icon": "FortiAnalyzer.svg",
                "variants": [f for f in categories['fortianalyzer']],
                "model_path": "/static/3d-models/FortiAnalyzer.glb",
                "description": "FortiAnalyzer Analytics Platform"
            }
        }
    }
    
    # Save mapping
    mapping_path = output_dir / 'icon_mapping.json'
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2)
    
    return mapping

def main():
    """Main extraction process"""
    print("🎨 Extracting Fortinet Icons for VSS + Eraser AI Workflow")
    print("=" * 60)
    
    # Setup paths
    library_dir = Path("/media/keith/Windows Backup/CascadeProjects/DrawIO/libraries")
    output_dir = Path("/home/keith/enhanced-network-api-corporate/src/enhanced_network_api/static/fortinet-icons-extracted")
    output_dir.mkdir(exist_ok=True)
    
    # Process all libraries
    total_extracted = 0
    library_files = [
        "Fortinet-Custom-Library.mxlibrary",
        "Fortinet-Gate.mxlibrary", 
        "Fortinet-Manager.mxlibrary",
        "Fortinet-Analyzer.mxlibrary",
        "Fortinet-Authenticator.mxlibrary"
    ]
    
    for library_file in library_files:
        library_path = library_dir / library_file
        if library_path.exists():
            extracted = extract_icons_from_library(library_path, output_dir)
            total_extracted += extracted
            print(f"  Extracted {extracted} icons from {library_file}")
        else:
            print(f"  ⚠ Library not found: {library_file}")
    
    print(f"\n🎯 Total icons extracted: {total_extracted}")
    
    # Categorize icons
    categories = categorize_icons(output_dir)
    
    print("\n📊 Icon Categories:")
    for category, icons in categories.items():
        if icons:
            print(f"  {category}: {len(icons)} icons")
            for icon in icons[:3]:  # Show first 3
                print(f"    - {icon}")
            if len(icons) > 3:
                print(f"    ... and {len(icons) - 3} more")
    
    # Create mapping
    mapping = create_icon_mapping(categories, output_dir)
    
    print(f"\n✅ Extraction complete!")
    print(f"📁 Output directory: {output_dir}")
    print(f"🗺 Icon mapping: {output_dir / 'icon_mapping.json'}")
    
    print(f"\n🚀 Next Steps for VSS + Eraser AI Workflow:")
    print(f"1. Extract 3D models from Visual Studio (VSS)")
    print(f"2. Process models with Eraser AI for enhanced textures")
    print(f"3. Place GLB files in /static/3d-models/")
    print(f"4. Update topology system to use extracted icons and 3D models")
    print(f"5. Test with production topology visualizations")

if __name__ == "__main__":
    main()
