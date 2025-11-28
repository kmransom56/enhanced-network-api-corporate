#!/usr/bin/env python3
"""Extract vector assets and metadata from Visio stencil files."""

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List

try:
    from vsdx import VisioFile  # type: ignore
except ImportError:  # pragma: no cover
    VisioFile = None


def _sanitize(name: str) -> str:
    return ''.join(c if c.isalnum() or c in ('-', '_') else '_' for c in name).strip('_') or 'shape'


def extract_with_vsdx(stencil_path: Path, output_dir: Path) -> List[Dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    shapes_meta: List[Dict[str, Any]] = []

    if VisioFile is None:
        return shapes_meta

    with VisioFile(stencil_path) as vis:
        for page in vis.pages:
            for shape in page.all_shapes:
                shape_name = _sanitize(shape.text or shape.master_name or f'shape_{shape.ID}')
                shape_dir = output_dir / shape_name
                shape_dir.mkdir(exist_ok=True)

                # Persist raw XML for reference
                xml_path = shape_dir / 'shape.xml'
                xml_path.write_text(shape.xml, encoding='utf-8')

                # Attempt to export SVG via vsdx helper if available
                if hasattr(shape, 'export_svg'):
                    try:
                        shape.export_svg(str(shape_dir / f'{shape_name}.svg'))
                    except Exception:  # pragma: no cover
                        pass

                shapes_meta.append({
                    'id': shape.ID,
                    'name': shape.text,
                    'sanitized_name': shape_name,
                    'page': page.name,
                    'properties': getattr(shape, 'data_properties', []),
                })

    metadata_path = output_dir / 'shapes.json'
    metadata_path.write_text(json.dumps(shapes_meta, indent=2), encoding='utf-8')
    return shapes_meta


def extract_via_zip(stencil_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(stencil_path, 'r') as archive:
        for member in archive.namelist():
            if member.startswith('visio/masters/') or member.startswith('visio/pages/'):
                target = output_dir / member
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open('wb') as dest:
                    dest.write(source.read())


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Visio stencil assets")
    parser.add_argument('stencil', type=Path, help='Path to .vsdx/.vssx stencil file')
    parser.add_argument('--out', type=Path, default=Path('extracted_visio'))
    args = parser.parse_args()

    stencil_path = args.stencil
    output_dir = args.out

    metadata = extract_with_vsdx(stencil_path, output_dir / 'svg')
    if not metadata:
        extract_via_zip(stencil_path, output_dir / 'raw_xml')


if __name__ == '__main__':
    main()
