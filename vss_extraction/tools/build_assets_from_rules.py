#!/usr/bin/env python3
"""
Build Assets from Rules - Auto-generate icons and models based on device rules
Updates device_model_rules.json with generated asset paths
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

try:
    from svg_to_glb_converter import convert_svg_to_glb
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from svg_to_glb_converter import convert_svg_to_glb


def find_asset_files(assets_dir: Path, pattern: str = "*.svg") -> Dict[str, Path]:
    """Find all asset files and create a mapping by name"""
    assets = {}
    
    if not assets_dir.exists():
        return assets
    
    for asset_path in assets_dir.rglob(pattern):
        # Use stem (filename without extension) as key
        key = asset_path.stem.lower().replace('_', '-').replace(' ', '-')
        assets[key] = asset_path
    
    return assets


def update_rules_with_assets(
    rules_path: Path,
    icons_dir: Path,
    models_dir: Path,
    auto_convert: bool = True
) -> Dict:
    """
    Update device_model_rules.json with actual asset paths.
    
    Args:
        rules_path: Path to device_model_rules.json
        icons_dir: Directory containing SVG icons
        models_dir: Directory containing GLB models
        auto_convert: Whether to auto-convert missing GLB models from SVGs
        
    Returns:
        Updated rules dictionary
    """
    # Load existing rules
    if rules_path.exists():
        with open(rules_path, 'r') as f:
            rules = json.load(f)
    else:
        rules = {
            "oui_map": {},
            "model_map": {},
            "device_types": {}
        }
    
    # Find available assets
    svg_assets = find_asset_files(icons_dir, "*.svg")
    glb_assets = find_asset_files(models_dir, "*.glb")
    
    print(f"📦 Found {len(svg_assets)} SVG icons and {len(glb_assets)} GLB models")
    
    # Update OUI map
    updated_count = 0
    converted_count = 0
    
    for oui, rule in rules.get("oui_map", {}).items():
        # Try to find matching icon
        icon_name = rule.get("icon", "")
        if icon_name:
            icon_basename = Path(icon_name).stem.lower().replace('_', '-')
            
            # Search for matching SVG
            matching_svg = None
            for key, svg_path in svg_assets.items():
                if icon_basename in key or key in icon_basename:
                    matching_svg = svg_path
                    break
            
            if matching_svg:
                # Update icon path (relative to rules file)
                rel_icon_path = os.path.relpath(matching_svg, rules_path.parent)
                rule["icon"] = rel_icon_path
                updated_count += 1
                
                # Check for corresponding GLB model
                model_name = rule.get("model3d", "")
                if model_name:
                    model_basename = Path(model_name).stem.lower().replace('_', '-')
                    matching_glb = None
                    
                    for key, glb_path in glb_assets.items():
                        if model_basename in key or key in model_basename:
                            matching_glb = glb_path
                            break
                    
                    if matching_glb:
                        rel_model_path = os.path.relpath(matching_glb, rules_path.parent)
                        rule["model3d"] = rel_model_path
                    elif auto_convert and matching_svg:
                        # Auto-convert SVG to GLB
                        glb_name = matching_svg.stem + '.glb'
                        glb_path = models_dir / glb_name
                        
                        print(f"  🔄 Converting {matching_svg.name} → {glb_name}")
                        if convert_svg_to_glb(matching_svg, glb_path):
                            rel_model_path = os.path.relpath(glb_path, rules_path.parent)
                            rule["model3d"] = rel_model_path
                            converted_count += 1
                        else:
                            print(f"  ✗ Failed to convert {matching_svg.name}")
    
    # Update model map similarly
    for model_key, rule in rules.get("model_map", {}).items():
        # Similar logic for model-based rules
        icon_name = rule.get("icon", "")
        if icon_name:
            icon_basename = Path(icon_name).stem.lower()
            for key, svg_path in svg_assets.items():
                if icon_basename in key:
                    rel_icon_path = os.path.relpath(svg_path, rules_path.parent)
                    rule["icon"] = rel_icon_path
                    updated_count += 1
                    break
    
    print(f"\n✅ Updated {updated_count} rules")
    if converted_count > 0:
        print(f"✅ Converted {converted_count} new GLB models")
    
    return rules


def scan_and_add_new_devices(
    rules_path: Path,
    icons_dir: Path,
    models_dir: Path,
    vendor: str = "Fortinet"
) -> Dict:
    """
    Scan for new device icons/models and add them to rules.
    
    Args:
        rules_path: Path to device_model_rules.json
        icons_dir: Directory containing SVG icons
        models_dir: Directory containing GLB models
        vendor: Vendor name for new entries
        
    Returns:
        Updated rules dictionary
    """
    if rules_path.exists():
        with open(rules_path, 'r') as f:
            rules = json.load(f)
    else:
        rules = {"oui_map": {}, "model_map": {}, "device_types": {}}
    
    svg_assets = find_asset_files(icons_dir, "*.svg")
    glb_assets = find_asset_files(models_dir, "*.glb")
    
    added_count = 0
    
    # Add new entries for unmatched SVGs
    for key, svg_path in svg_assets.items():
        # Check if already in rules
        found = False
        for rule in rules.get("oui_map", {}).values():
            if svg_path.name in str(rule.get("icon", "")):
                found = True
                break
        
        if not found:
            # Infer device type from filename
            device_type = "device"
            if "gate" in key or "firewall" in key:
                device_type = "firewall"
            elif "switch" in key:
                device_type = "switch"
            elif "ap" in key or "access" in key:
                device_type = "access_point"
            elif "client" in key or "endpoint" in key:
                device_type = "client"
            
            # Find matching GLB
            glb_path = None
            for glb_key, glb_file in glb_assets.items():
                if key in glb_key or glb_key in key:
                    glb_path = glb_file
                    break
            
            # Add to model_map
            model_key = f"{vendor}_{key}"
            rel_icon = os.path.relpath(svg_path, rules_path.parent)
            rel_model = os.path.relpath(glb_path, rules_path.parent) if glb_path else None
            
            rules.setdefault("model_map", {})[model_key] = {
                "vendor": vendor,
                "device_type": device_type,
                "icon": rel_icon,
                "model3d": rel_model
            }
            
            added_count += 1
            print(f"  ➕ Added: {model_key} ({device_type})")
    
    if added_count > 0:
        print(f"\n✅ Added {added_count} new device entries")
    
    return rules


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Build and update device model rules from assets'
    )
    parser.add_argument(
        '--rules',
        type=Path,
        default=Path('device_model_rules.json'),
        help='Path to device_model_rules.json'
    )
    parser.add_argument(
        '--icons-dir',
        type=Path,
        default=Path('assets/icons'),
        help='Directory containing SVG icons'
    )
    parser.add_argument(
        '--models-dir',
        type=Path,
        default=Path('assets/models'),
        help='Directory containing GLB models'
    )
    parser.add_argument(
        '--no-convert',
        action='store_true',
        help='Skip auto-conversion of SVGs to GLB'
    )
    parser.add_argument(
        '--scan-new',
        action='store_true',
        help='Scan for new devices and add to rules'
    )
    parser.add_argument(
        '--vendor',
        default='Fortinet',
        help='Vendor name for new entries'
    )
    
    args = parser.parse_args()
    
    # Ensure directories exist
    args.icons_dir.mkdir(parents=True, exist_ok=True)
    args.models_dir.mkdir(parents=True, exist_ok=True)
    
    print("🔧 Building assets from rules...")
    print(f"   Rules: {args.rules}")
    print(f"   Icons: {args.icons_dir}")
    print(f"   Models: {args.models_dir}\n")
    
    # Update existing rules
    rules = update_rules_with_assets(
        args.rules,
        args.icons_dir,
        args.models_dir,
        auto_convert=not args.no_convert
    )
    
    # Scan for new devices if requested
    if args.scan_new:
        rules = scan_and_add_new_devices(
            args.rules,
            args.icons_dir,
            args.models_dir,
            vendor=args.vendor
        )
    
    # Save updated rules
    args.rules.parent.mkdir(parents=True, exist_ok=True)
    with open(args.rules, 'w') as f:
        json.dump(rules, f, indent=2)
    
    print(f"\n✅ Saved updated rules to {args.rules}")


if __name__ == '__main__':
    main()

