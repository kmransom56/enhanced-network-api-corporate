#!/usr/bin/env python3
"""
SVG to GLB Converter - Convert SVG icons to 3D GLB models using Blender
Includes environment isolation and error handling improvements
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Import SVG cleaner
try:
    from svg_cleaner import clean_svg_file
except ImportError:
    # Fallback if not in same directory
    sys.path.insert(0, str(Path(__file__).parent))
    from svg_cleaner import clean_svg_file


BLENDER_CMD = os.environ.get('BLENDER_CMD', 'blender')
DEFAULT_EXTRUDE_DEPTH = 0.1


def convert_svg_to_glb(
    svg_path: Path,
    output_path: Path,
    depth: float = DEFAULT_EXTRUDE_DEPTH,
    clean_svg: bool = True
) -> bool:
    """
    Convert an SVG file to GLB format using Blender.
    
    Args:
        svg_path: Path to input SVG file
        output_path: Path to output GLB file
        depth: Extrusion depth for 3D model
        clean_svg: Whether to clean SVG before conversion
        
    Returns:
        True if conversion successful, False otherwise
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clean SVG if requested
    if clean_svg:
        try:
            clean_svg_file(svg_path)
        except Exception as e:
            print(f"  ⚠️  SVG cleaning warning: {e}")
    
    # Create temporary Blender script
    temp_script = Path(__file__).parent / "temp_blender_script.py"
    
    # Generate Blender script
    blender_script_content = f'''import bpy
import sys
import os

# Get arguments
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []

svg_path = r"{svg_path}"
glb_path = r"{output_path}"
depth = {depth}

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

try:
    # Import SVG
    bpy.ops.import_curve.svg(filepath=svg_path)
    
    # Convert curves to mesh
    for obj in bpy.context.selected_objects:
        if obj.type == 'CURVE':
            bpy.context.view_layer.objects.active = obj
            
            # Convert to mesh
            bpy.ops.object.convert(target='MESH')
            
            # Set origin to center
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
    
    # Extrude meshes
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={{'value': (0, 0, depth)}})
            bpy.ops.object.editmode_toggle()
    
    # Export GLB
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        export_draco_mesh_compression_enable=False,
        export_apply=True,
        export_colors=False,
        export_materials='EXPORT'
    )
    
    print(f"SUCCESS: Exported {{glb_path}}")
    
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
'''
    
    # Write temporary script
    with open(temp_script, 'w', encoding='utf-8') as f:
        f.write(blender_script_content)
    
    try:
        # Prepare environment (isolate from venv)
        env = os.environ.copy()
        env.pop('PYTHONPATH', None)
        env.pop('PYTHONHOME', None)
        env.pop('VIRTUAL_ENV', None)
        
        # Run Blender
        command = [
            BLENDER_CMD,
            '--background',
            '--python', str(temp_script),
            '--',
            str(svg_path),
            str(output_path),
            str(depth)
        ]
        
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        if result.returncode != 0:
            print(f"  ✗ Blender error: {result.stderr}")
            return False
        
        # Check if output file was created
        if output_path.exists():
            print(f"  ✓ Created: {output_path.name} ({output_path.stat().st_size} bytes)")
            return True
        else:
            print(f"  ✗ Output file not created: {output_path}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ✗ Conversion timeout for {svg_path.name}")
        return False
    except FileNotFoundError:
        print(f"  ✗ Blender not found. Install Blender and ensure 'blender' is in PATH")
        print(f"     Or set BLENDER_CMD environment variable")
        return False
    except Exception as e:
        print(f"  ✗ Conversion error: {e}")
        return False
    finally:
        # Clean up temporary script
        if temp_script.exists():
            temp_script.unlink()


def batch_convert_svg_to_glb(
    svg_dir: Path,
    output_dir: Path,
    depth: float = DEFAULT_EXTRUDE_DEPTH,
    pattern: str = "*.svg",
    recursive: bool = False
) -> dict:
    """
    Batch convert SVG files to GLB format.
    
    Args:
        svg_dir: Directory containing SVG files
        output_dir: Directory for output GLB files
        depth: Extrusion depth
        pattern: File pattern to match
        recursive: Whether to search recursively
        
    Returns:
        Dictionary with conversion statistics
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'skipped': 0
    }
    
    # Find SVG files
    if recursive:
        svg_files = list(svg_dir.rglob(pattern))
    else:
        svg_files = list(svg_dir.glob(pattern))
    
    stats['total'] = len(svg_files)
    
    print(f"🔄 Converting {stats['total']} SVG files to GLB...")
    print(f"   Input: {svg_dir}")
    print(f"   Output: {output_dir}")
    print(f"   Depth: {depth}\n")
    
    for svg_path in svg_files:
        # Create output filename
        glb_name = svg_path.stem + '.glb'
        glb_path = output_dir / glb_name
        
        # Skip if already exists
        if glb_path.exists():
            print(f"  ⊘ Skipped (exists): {glb_name}")
            stats['skipped'] += 1
            continue
        
        print(f"  → Converting: {svg_path.name}")
        
        if convert_svg_to_glb(svg_path, glb_path, depth):
            stats['success'] += 1
        else:
            stats['failed'] += 1
    
    print(f"\n📊 Conversion Summary:")
    print(f"   Total: {stats['total']}")
    print(f"   Success: {stats['success']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Skipped: {stats['skipped']}")
    
    return stats


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert SVG icons to GLB 3D models using Blender'
    )
    parser.add_argument('input', type=Path, help='Input SVG file or directory')
    parser.add_argument('-o', '--output', type=Path, help='Output GLB file or directory')
    parser.add_argument('-d', '--depth', type=float, default=DEFAULT_EXTRUDE_DEPTH,
                       help=f'Extrusion depth (default: {DEFAULT_EXTRUDE_DEPTH})')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='Search recursively in directories')
    parser.add_argument('--no-clean', action='store_true',
                       help='Skip SVG cleaning step')
    
    args = parser.parse_args()
    
    if args.input.is_file():
        # Single file conversion
        if not args.output:
            args.output = args.input.with_suffix('.glb')
        
        convert_svg_to_glb(
            args.input,
            args.output,
            args.depth,
            clean_svg=not args.no_clean
        )
    elif args.input.is_dir():
        # Batch conversion
        if not args.output:
            args.output = args.input / 'glb_models'
        
        batch_convert_svg_to_glb(
            args.input,
            args.output,
            args.depth,
            recursive=args.recursive
        )
    else:
        print(f"Error: {args.input} does not exist")
        sys.exit(1)

