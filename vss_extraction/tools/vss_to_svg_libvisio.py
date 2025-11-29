#!/usr/bin/env python3
"""
VSS to SVG Converter using libvisio Python library
Converts VSS (Visio Stencil) files to SVG format using libvisio
"""

import sys
from pathlib import Path
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def convert_vss_to_svg_libvisio(
    vss_path: Path,
    output_dir: Path,
    scale: float = 1.0,
    prefix: str = ""
) -> List[Path]:
    """
    Convert VSS file to SVG using libvisio Python library.
    
    Args:
        vss_path: Path to input VSS file
        output_dir: Directory to save SVG files
        scale: Scaling factor for output (default 1.0)
        prefix: Optional prefix for output filenames
        
    Returns:
        List of paths to generated SVG files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Try to import libvisio Python library
        try:
            import libvisio
            logger.info("Using libvisio Python library")
            return _convert_with_libvisio_python(vss_path, output_dir, scale, prefix)
        except ImportError:
            # Fall back to CLI tool
            logger.info("libvisio Python library not found, trying CLI tool")
            return _convert_with_libvisio_cli(vss_path, output_dir, scale, prefix)
            
    except Exception as e:
        logger.error(f"VSS to SVG conversion failed: {e}")
        raise


def _convert_with_libvisio_python(
    vss_path: Path,
    output_dir: Path,
    scale: float,
    prefix: str
) -> List[Path]:
    """Convert using libvisio Python library directly"""
    import libvisio
    
    logger.info(f"Converting {vss_path.name} using libvisio Python library...")
    
    svg_files = []
    
    try:
        # Open VSS file
        document = libvisio.VSDDocument(vss_path)
        
        # Get all pages/masters in the stencil
        pages = document.getPages()
        
        for i, page in enumerate(pages):
            # Get page name or use index
            try:
                page_name = page.getName() or f"shape_{i+1:03d}"
            except:
                page_name = f"shape_{i+1:03d}"
            
            # Sanitize filename
            safe_name = _sanitize_filename(page_name)
            output_file = output_dir / f"{prefix}{safe_name}.svg"
            
            # Convert page to SVG
            svg_content = page.getSVG(scale=scale)
            
            # Write SVG file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            svg_files.append(output_file)
            logger.info(f"  ✓ Exported: {safe_name}.svg")
        
        logger.info(f"Generated {len(svg_files)} SVG files")
        return svg_files
        
    except AttributeError:
        # If API is different, try alternative approach
        logger.info("Trying alternative libvisio API...")
        return _convert_with_libvisio_alternative(vss_path, output_dir, scale, prefix)
    except Exception as e:
        logger.error(f"libvisio Python conversion error: {e}")
        raise


def _convert_with_libvisio_alternative(
    vss_path: Path,
    output_dir: Path,
    scale: float,
    prefix: str
) -> List[Path]:
    """Alternative conversion method if API differs"""
    import libvisio
    
    logger.info("Using alternative libvisio conversion method...")
    
    svg_files = []
    
    try:
        # Try different API patterns
        # Pattern 1: Direct conversion
        if hasattr(libvisio, 'convert'):
            result = libvisio.convert(str(vss_path), str(output_dir), format='svg', scale=scale)
            svg_files = list(Path(output_dir).glob('*.svg'))
        
        # Pattern 2: Document-based
        elif hasattr(libvisio, 'Document'):
            doc = libvisio.Document(str(vss_path))
            for i, shape in enumerate(doc.getShapes()):
                safe_name = _sanitize_filename(shape.getName() or f"shape_{i+1:03d}")
                output_file = output_dir / f"{prefix}{safe_name}.svg"
                shape.exportSVG(str(output_file), scale=scale)
                svg_files.append(output_file)
        
        # Pattern 3: Reader-based
        elif hasattr(libvisio, 'Reader'):
            reader = libvisio.Reader()
            reader.parse(str(vss_path))
            for i, shape in enumerate(reader.getShapes()):
                safe_name = _sanitize_filename(shape.getName() or f"shape_{i+1:03d}")
                output_file = output_dir / f"{prefix}{safe_name}.svg"
                shape.writeSVG(str(output_file), scale=scale)
                svg_files.append(output_file)
        
        else:
            raise RuntimeError("Unknown libvisio API structure")
        
        logger.info(f"Generated {len(svg_files)} SVG files")
        return svg_files
        
    except Exception as e:
        logger.error(f"Alternative conversion failed: {e}")
        raise


def _convert_with_libvisio_cli(
    vss_path: Path,
    output_dir: Path,
    scale: float,
    prefix: str
) -> List[Path]:
    """Convert using libvisio2svg CLI tool as fallback"""
    import subprocess
    import shutil
    
    # Check for CLI tool
    cli_tool = shutil.which('vss2svg-conv') or shutil.which('libvisio2svg')
    
    if not cli_tool:
        raise RuntimeError(
            "Neither libvisio Python library nor CLI tool found.\n"
            "Install libvisio Python library: pip install libvisio\n"
            "Or install libvisio2svg CLI tool: https://github.com/kakwa/libvisio2svg"
        )
    
    logger.info(f"Using CLI tool: {cli_tool}")
    
    cmd = [
        cli_tool,
        '-i', str(vss_path),
        '-o', str(output_dir),
        '-s', str(scale)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.debug(result.stdout)
        
        # Find generated SVG files
        svg_files = sorted(output_dir.glob('*.svg'))
        
        # Apply prefix if specified
        if prefix:
            renamed_files = []
            for svg_file in svg_files:
                new_name = output_dir / f"{prefix}{svg_file.name}"
                svg_file.rename(new_name)
                renamed_files.append(new_name)
            svg_files = renamed_files
        
        logger.info(f"Generated {len(svg_files)} SVG files")
        return svg_files
        
    except subprocess.CalledProcessError as e:
        logger.error(f"CLI conversion failed: {e.stderr}")
        raise RuntimeError(f"libvisio2svg conversion failed: {e.stderr}")


def _sanitize_filename(name: str) -> str:
    """Sanitize filename for filesystem"""
    import re
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove leading/trailing spaces and dots
    name = name.strip(' .')
    # Replace multiple underscores with single
    name = re.sub(r'_+', '_', name)
    # Limit length
    if len(name) > 100:
        name = name[:100]
    return name or "unnamed"


def batch_convert_vss(
    vss_dir: Path,
    output_dir: Path,
    scale: float = 1.0,
    recursive: bool = False
) -> dict:
    """
    Batch convert multiple VSS files to SVG.
    
    Args:
        vss_dir: Directory containing VSS files
        output_dir: Directory for output SVG files
        scale: Scaling factor
        recursive: Whether to search recursively
        
    Returns:
        Dictionary with conversion statistics
    """
    stats = {
        'total': 0,
        'success': 0,
        'failed': 0
    }
    
    pattern = '**/*.vss' if recursive else '*.vss'
    
    for vss_path in vss_dir.glob(pattern):
        stats['total'] += 1
        
        try:
            # Create subdirectory for this VSS file
            vss_output_dir = output_dir / vss_path.stem
            svg_files = convert_vss_to_svg_libvisio(
                vss_path,
                vss_output_dir,
                scale=scale
            )
            stats['success'] += 1
            logger.info(f"✓ Converted {vss_path.name}: {len(svg_files)} SVGs")
        except Exception as e:
            stats['failed'] += 1
            logger.error(f"✗ Failed to convert {vss_path.name}: {e}")
    
    return stats


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert VSS (Visio Stencil) files to SVG using libvisio'
    )
    parser.add_argument('input', type=Path, help='Input VSS file or directory')
    parser.add_argument('-o', '--output', type=Path, help='Output directory for SVG files')
    parser.add_argument('-s', '--scale', type=float, default=1.0,
                       help='Scaling factor (default: 1.0)')
    parser.add_argument('-p', '--prefix', default='',
                       help='Prefix for output filenames')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='Search recursively in directories')
    
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: {args.input} does not exist")
        sys.exit(1)
    
    if args.input.is_file():
        # Single file conversion
        if not args.output:
            args.output = args.input.parent / 'svg_output'
        
        try:
            svg_files = convert_vss_to_svg_libvisio(
                args.input,
                args.output,
                scale=args.scale,
                prefix=args.prefix
            )
            print(f"\n✅ Conversion complete: {len(svg_files)} SVG files generated")
            print(f"   Output directory: {args.output}")
        except Exception as e:
            print(f"\n❌ Conversion failed: {e}")
            sys.exit(1)
    
    elif args.input.is_dir():
        # Batch conversion
        if not args.output:
            args.output = args.input / 'svg_output'
        
        stats = batch_convert_vss(
            args.input,
            args.output,
            scale=args.scale,
            recursive=args.recursive
        )
        
        print(f"\n📊 Batch Conversion Summary:")
        print(f"   Total: {stats['total']}")
        print(f"   Success: {stats['success']}")
        print(f"   Failed: {stats['failed']}")
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        sys.exit(1)

