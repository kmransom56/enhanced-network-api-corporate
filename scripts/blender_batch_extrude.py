#!/usr/bin/env python3
"""Batch convert SVG icons into simple 3D meshes using Blender."""

import argparse
import os
from pathlib import Path

BLENDER_SCRIPT = """
import bpy
import os

svg_dir = r"{svg_dir}"
output_dir = r"{output_dir}"

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

for svg_name in os.listdir(svg_dir):
    if not svg_name.lower().endswith('.svg'):
        continue

    clear_scene()
    svg_path = os.path.join(svg_dir, svg_name)
    bpy.ops.import_curve.svg(filepath=svg_path)

    for obj in bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target='MESH')
        solidify = obj.modifiers.new(name='Solidify', type='SOLIDIFY')
        solidify.thickness = 0.05
        bpy.ops.object.modifier_apply(modifier='Solidify')

    output_path = os.path.join(output_dir, svg_name.replace('.svg', '.obj'))
    bpy.ops.export_scene.obj(filepath=output_path)
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Blender batch extrusion script")
    parser.add_argument('svg_dir', type=Path, help='Directory of SVG icons')
    parser.add_argument('--out', type=Path, default=Path('models'))
    parser.add_argument('--script', type=Path, default=Path('blender_extrude.py'))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    args.script.write_text(BLENDER_SCRIPT.format(svg_dir=args.svg_dir, output_dir=args.out), encoding='utf-8')
    print(f"Generated Blender script at {args.script}. Run with: blender --background --python {args.script}")


if __name__ == '__main__':
    main()
