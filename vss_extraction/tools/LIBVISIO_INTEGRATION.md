# Libvisio Integration Guide

This document explains how to use the libvisio Python library for VSS to SVG conversion.

## Installation

### Option 1: Python Library (Recommended)
```bash
pip install libvisio
```

### Option 2: CLI Tool (Fallback)
If the Python library is not available, the tool will automatically fall back to the CLI tool:
```bash
# Install libvisio2svg CLI tool
# See: https://github.com/kakwa/libvisio2svg
```

## Usage

### Basic Conversion
```bash
# Convert single VSS file
python tools/vss_to_svg_libvisio.py input.vss -o output_dir

# Batch convert all VSS files in a directory
python tools/vss_to_svg_libvisio.py source_models -o assets/icons/vss_extracted -r
```

### With Makefile
```bash
# Convert VSS files (automatically integrated in full workflow)
make convert-vss

# Or run complete workflow
make all
```

## How It Works

The tool tries multiple methods in order:

1. **Python libvisio library** (if installed)
   - Direct Python API access
   - Faster and more reliable
   - Better error handling

2. **libvisio2svg CLI tool** (fallback)
   - Uses subprocess to call CLI tool
   - Works if Python library not available

## API Compatibility

The tool handles different libvisio API patterns:

- **VSDDocument-based**: `libvisio.VSDDocument(file)`
- **Document-based**: `libvisio.Document(file)`
- **Reader-based**: `libvisio.Reader()`

If your libvisio installation uses a different API, the tool will try to detect and adapt.

## Troubleshooting

### "libvisio Python library not found"
- Install: `pip install libvisio`
- Or ensure libvisio2svg CLI tool is in PATH

### "Unknown libvisio API structure"
- The tool couldn't detect the API pattern
- Check libvisio documentation for your version
- You may need to modify `_convert_with_libvisio_python()` function

### Conversion produces empty SVGs
- Check that VSS file is not corrupted
- Try different scale factor: `-s 2.0`
- Check libvisio version compatibility

## Integration with Workflow

The VSS conversion is automatically integrated into the complete workflow:

```
VSS Files → SVG Icons → Clean → GLB Models → Rules Update
```

Place your VSS files in `source_models/` directory and run:
```bash
make all
```

## Examples

### Convert Fortinet VSS Stencil
```bash
python tools/vss_to_svg_libvisio.py \
    source_models/FortiGate_Series.vss \
    -o assets/icons/fortinet \
    -s 1.0
```

### Batch Convert with Custom Prefix
```bash
python tools/vss_to_svg_libvisio.py \
    source_models \
    -o assets/icons/vss_extracted \
    -p "fortinet_" \
    -r
```

## Next Steps

After converting VSS to SVG:
1. Clean SVGs: `make clean-svgs`
2. Convert to GLB: `make convert-svgs`
3. Update rules: `make build-assets`

See `README.md` for complete workflow documentation.

