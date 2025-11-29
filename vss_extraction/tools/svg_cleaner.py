#!/usr/bin/env python3
"""
SVG Cleaner - Pre-process SVGs before Blender conversion
Fixes duplicate attributes, malformed XML, and other issues
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


def clean_svg_file(svg_path: Path) -> bool:
    """
    Clean an SVG file by fixing duplicate attributes and malformed XML.
    
    Args:
        svg_path: Path to the SVG file to clean
        
    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(svg_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix duplicate attributes in <svg> tag
        content = _fix_duplicate_attributes(content)
        
        # Fix malformed XML entities
        content = _fix_xml_entities(content)
        
        # Validate and fix SVG structure
        content = _fix_svg_structure(content)
        
        # Only write if content changed
        if content != original_content:
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"  ⚠️  Error cleaning {svg_path}: {e}")
        return False


def _fix_duplicate_attributes(content: str) -> str:
    """Fix duplicate attributes in SVG tags"""
    lines = content.split('\n')
    cleaned_lines = []
    seen_attrs = set()
    
    for line in lines:
        if '<svg' in line and '=' in line:
            # Extract and deduplicate attributes
            parts = line.split()
            new_parts = []
            seen_attrs.clear()
            
            for part in parts:
                if '=' in part:
                    attr_name = part.split('=')[0].strip()
                    # Remove namespace prefixes for comparison
                    attr_key = attr_name.split(':')[-1]
                    
                    if attr_key not in seen_attrs:
                        seen_attrs.add(attr_key)
                        new_parts.append(part)
                    # Skip duplicate
                else:
                    new_parts.append(part)
            
            cleaned_lines.append(' '.join(new_parts) + '\n')
        else:
            cleaned_lines.append(line)
    
    return ''.join(cleaned_lines)


def _fix_xml_entities(content: str) -> str:
    """Fix XML entity encoding issues"""
    # Fix common entity issues
    content = content.replace('&amp;', '&')
    content = content.replace('&lt;', '<')
    content = content.replace('&gt;', '>')
    
    # Re-encode properly
    content = content.replace('&', '&amp;')
    content = content.replace('&amp;lt;', '&lt;')
    content = content.replace('&amp;gt;', '&gt;')
    content = content.replace('&amp;amp;', '&amp;')
    
    return content


def _fix_svg_structure(content: str) -> str:
    """Fix SVG structure issues"""
    # Ensure viewBox is present if width/height are missing
    if '<svg' in content and 'viewBox' not in content:
        # Try to extract width and height
        width_match = re.search(r'width=["\']?(\d+)', content)
        height_match = re.search(r'height=["\']?(\d+)', content)
        
        if width_match and height_match:
            width = width_match.group(1)
            height = height_match.group(1)
            viewbox = f'viewBox="0 0 {width} {height}"'
            content = content.replace('<svg', f'<svg {viewbox}', 1)
    
    # Remove empty or invalid elements
    content = re.sub(r'<[^>]+>\s*</[^>]+>', '', content)
    
    return content


def batch_clean_svgs(svg_dir: Path, recursive: bool = False) -> dict:
    """
    Clean all SVG files in a directory.
    
    Args:
        svg_dir: Directory containing SVG files
        recursive: Whether to search recursively
        
    Returns:
        Dictionary with cleaning statistics
    """
    stats = {
        'total': 0,
        'cleaned': 0,
        'errors': 0,
        'skipped': 0
    }
    
    pattern = '**/*.svg' if recursive else '*.svg'
    
    for svg_path in svg_dir.glob(pattern):
        stats['total'] += 1
        
        try:
            if clean_svg_file(svg_path):
                stats['cleaned'] += 1
                print(f"  ✓ Cleaned: {svg_path.name}")
            else:
                stats['skipped'] += 1
        except Exception as e:
            stats['errors'] += 1
            print(f"  ✗ Error cleaning {svg_path.name}: {e}")
    
    return stats


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: svg_cleaner.py <svg_file_or_dir> [--recursive]")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    recursive = '--recursive' in sys.argv
    
    if path.is_file():
        if path.suffix.lower() == '.svg':
            clean_svg_file(path)
            print(f"✓ Cleaned: {path}")
        else:
            print(f"Error: {path} is not an SVG file")
    elif path.is_dir():
        stats = batch_clean_svgs(path, recursive)
        print(f"\n📊 Cleaning Summary:")
        print(f"  Total: {stats['total']}")
        print(f"  Cleaned: {stats['cleaned']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"  Errors: {stats['errors']}")
    else:
        print(f"Error: {path} does not exist")

