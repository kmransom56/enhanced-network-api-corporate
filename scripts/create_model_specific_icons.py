#!/usr/bin/env python3
"""
Create Model-Specific Fortinet Icons from VSS Extraction
Generates SVG icons for specific Fortinet models based on VSS extraction data
"""

import os
import json
from pathlib import Path
from datetime import datetime

class ModelSpecificIconGenerator:
    def __init__(self):
        self.output_dir = Path("src/enhanced_network_api/static/model-specific-icons")
        self.vss_data_dir = Path("vss_extraction/vss_exports")
        
        # Model-specific icon configurations
        self.model_icons = {
            "FortiGate_600E": {
                "base_icon": "FortiGate",
                "model_label": "600E",
                "color": "#cc3333",
                "features": ["ngfw", "threat_protection", "ssl_inspection"],
                "ports": "12x1GE + 4xSFP",
                "throughput": "10 Gbps"
            },
            "FortiSwitch_148E": {
                "base_icon": "FortiSwitch", 
                "model_label": "148E",
                "color": "#00a652",
                "features": ["fortilink", "poe", "vlan_support"],
                "ports": "48x1GE + 4xSFP",
                "switching_capacity": "176 Gbps"
            },
            "FortiAP_432F": {
                "base_icon": "FortiAP",
                "model_label": "432F", 
                "color": "#0066cc",
                "features": ["wifi6", "beamforming", "mu_mimo"],
                "bands": "Dual-Band (2.4/5 GHz)",
                "throughput": "3.5 Gbps"
            }
        }
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_model_icon_svg(self, model_name, config):
        """Generate SVG icon for specific model"""
        
        # Base template for model-specific icons
        svg_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192" width="192" height="192">
  <defs>
    <style>
      .model-bg {{ fill: {config['color']}; opacity: 0.9; }}
      .model-frame {{ fill: none; stroke: #ffffff; stroke-width: 2; }}
      .model-text {{ fill: #ffffff; font-family: Arial, sans-serif; font-weight: bold; }}
      .model-label {{ font-size: 24px; text-anchor: middle; }}
      .model-features {{ font-size: 8px; text-anchor: middle; }}
      .port-indicator {{ fill: #333333; }}
      .status-led {{ fill: #00ff00; }}
    </style>
  </defs>
  
  <!-- Main device background -->
  <rect class="model-bg" x="32" y="48" width="128" height="96" rx="8" />
  <rect class="model-frame" x="32" y="48" width="128" height="96" rx="8" />
  
  <!-- Model label background -->
  <rect fill="#000000" opacity="0.7" x="52" y="56" width="88" height="28" rx="4" />
  
  <!-- Model label -->
  <text class="model-text model-label" x="96" y="75">{config['model_label']}</text>
  
  <!-- Device type indicator -->
  <text class="model-text model-features" x="96" y="95">{config['base_icon'].upper()}</text>
  
  <!-- Feature indicators -->
  <g id="features">
    {self._generate_feature_indicators(config['features'])}
  </g>
  
  <!-- Port indicators -->
  <g id="ports">
    {self._generate_port_indicators(model_name)}
  </g>
  
  <!-- Status LED -->
  <circle class="status-led" cx="160" cy="56" r="4" />
  
  <!-- Model-specific details -->
  <text class="model-text model-features" x="96" y="130" opacity="0.8">
    {self._get_model_details(model_name, config)}
  </text>
</svg>'''
        
        return svg_template
    
    def _generate_feature_indicators(self, features):
        """Generate feature indicator dots"""
        indicators = ""
        x_positions = [48, 64, 80]
        
        for i, feature in enumerate(features[:3]):
            x = x_positions[i]
            indicators += f'<circle class="port-indicator" cx="{x}" cy="108" r="3" />\n'
            
        return indicators
    
    def _generate_port_indicators(self, model_name):
        """Generate port indicators based on model"""
        if "FortiGate" in model_name:
            return '''
            <!-- FortiGate port layout -->
            <rect class="port-indicator" x="40" y="120" width="4" height="12" />
            <rect class="port-indicator" x="48" y="120" width="4" height="12" />
            <rect class="port-indicator" x="56" y="120" width="4" height="12" />
            <rect class="port-indicator" x="64" y="120" width="4" height="12" />
            <rect class="port-indicator" x="72" y="120" width="4" height="12" />
            <rect class="port-indicator" x="80" y="120" width="4" height="12" />
            <rect class="port-indicator" x="88" y="120" width="4" height="12" />
            <rect class="port-indicator" x="96" y="120" width="4" height="12" />
            <rect class="port-indicator" x="104" y="120" width="4" height="12" />
            <rect class="port-indicator" x="112" y="120" width="4" height="12" />
            <rect class="port-indicator" x="120" y="120" width="4" height="12" />
            <rect class="port-indicator" x="128" y="120" width="4" height="12" />
            '''
        elif "FortiSwitch" in model_name:
            return '''
            <!-- FortiSwitch port layout -->
            <rect class="port-indicator" x="36" y="115" width="3" height="8" />
            <rect class="port-indicator" x="42" y="115" width="3" height="8" />
            <rect class="port-indicator" x="48" y="115" width="3" height="8" />
            <rect class="port-indicator" x="54" y="115" width="3" height="8" />
            <rect class="port-indicator" x="60" y="115" width="3" height="8" />
            <rect class="port-indicator" x="66" y="115" width="3" height="8" />
            <rect class="port-indicator" x="72" y="115" width="3" height="8" />
            <rect class="port-indicator" x="78" y="115" width="3" height="8" />
            '''
        elif "FortiAP" in model_name:
            return '''
            <!-- FortiAP antenna indicators -->
            <line stroke="#ffffff" stroke-width="2" x1="96" y1="96" x2="96" y2="84" />
            <circle fill="#ffffff" cx="96" cy="84" r="2" />
            <line stroke="#ffffff" stroke-width="2" x1="96" y1="96" x2="88" y2="90" />
            <circle fill="#ffffff" cx="88" cy="90" r="2" />
            <line stroke="#ffffff" stroke-width="2" x1="96" y1="96" x2="104" y2="90" />
            <circle fill="#ffffff" cx="104" cy="90" r="2" />
            '''
        return ""
    
    def _get_model_details(self, model_name, config):
        """Get model-specific details text"""
        if "FortiGate" in model_name:
            return config.get('throughput', 'NGFW')
        elif "FortiSwitch" in model_name:
            return config.get('switching_capacity', 'L2/L3')
        elif "FortiAP" in model_name:
            return config.get('throughput', 'WiFi6')
        return ""
    
    def create_all_model_icons(self):
        """Generate all model-specific icons"""
        print("🎨 Creating Model-Specific Fortinet Icons...")
        
        generated_icons = []
        
        for model_name, config in self.model_icons.items():
            # Generate SVG content
            svg_content = self.generate_model_icon_svg(model_name, config)
            
            # Save to file
            icon_file = self.output_dir / f"{model_name}.svg"
            with open(icon_file, 'w') as f:
                f.write(svg_content)
            
            generated_icons.append({
                "model": model_name,
                "file": str(icon_file),
                "base_icon": config['base_icon'],
                "model_label": config['model_label'],
                "color": config['color']
            })
            
            print(f"✅ Created: {icon_file}")
        
        # Create icon mapping file
        self.create_icon_mapping(generated_icons)
        
        print(f"🎉 Generated {len(generated_icons)} model-specific icons!")
        return generated_icons
    
    def create_icon_mapping(self, generated_icons):
        """Create mapping file for icon usage"""
        mapping = {
            "generated_at": datetime.now().isoformat(),
            "total_icons": len(generated_icons),
            "icons": generated_icons,
            "usage": {
                "2d_topology": "/static/model-specific-icons/{model}.svg",
                "3d_topology": "/static/model-specific-icons/{model}.svg",
                "fallback": "/static/fortinet-icons-extracted/{base_icon}.svg"
            }
        }
        
        mapping_file = self.output_dir / "icon_mapping.json"
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2)
        
        print(f"📋 Created mapping: {mapping_file}")

def main():
    """Main execution"""
    generator = ModelSpecificIconGenerator()
    
    print("🚀 Model-Specific Icon Generator")
    print("=" * 50)
    
    # Create all model-specific icons
    icons = generator.create_all_model_icons()
    
    print("\n🎯 Usage Instructions:")
    print("1. Icons created in: src/enhanced_network_api/static/model-specific-icons/")
    print("2. Update topology code to use model-specific paths")
    print("3. Fallback to generic icons if model-specific not available")
    print("\n📁 Generated Icons:")
    for icon in icons:
        print(f"   - {icon['model']}: {icon['file']}")

if __name__ == "__main__":
    main()
