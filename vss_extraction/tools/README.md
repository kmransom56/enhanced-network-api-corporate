# VSS Extraction Tools - Improved Workflow

This directory contains improved tools for VSS extraction and 3D model generation, based on best practices from the `alternateconversion.md` guide.

## Tools Overview

### 1. `vss_to_svg_libvisio.py` - VSS to SVG Conversion
Converts VSS (Visio Stencil) files to SVG format using libvisio Python library:
- Uses libvisio Python library directly (if available)
- Falls back to libvisio2svg CLI tool
- Batch processing support
- Automatic filename sanitization

**Usage:**
```bash
# Convert single VSS file
python tools/vss_to_svg_libvisio.py input.vss -o output_dir

# Batch convert directory
python tools/vss_to_svg_libvisio.py vss_dir -o svg_output -r

# With custom scale
python tools/vss_to_svg_libvisio.py input.vss -o output_dir -s 2.0
```

**Requirements:**
- libvisio Python library: `pip install libvisio`
- Or libvisio2svg CLI tool installed

### 2. `svg_cleaner.py` - SVG Pre-processing
Fixes common SVG issues before Blender processing:
- Duplicate attributes in SVG tags
- Malformed XML entities
- Missing viewBox attributes
- Invalid XML structure

**Usage:**
```bash
# Clean a single file
python tools/svg_cleaner.py path/to/icon.svg

# Clean all SVGs in a directory
python tools/svg_cleaner.py assets/icons --recursive
```

### 3. `svg_to_glb_converter.py` - SVG to GLB Conversion
Converts SVG icons to 3D GLB models using Blender with:
- Environment isolation (prevents Python conflicts)
- Automatic SVG cleaning
- Error handling and timeout protection
- Batch processing support
- Progress tracking

**Usage:**
```bash
# Convert single file
python tools/svg_to_glb_converter.py icon.svg -o icon.glb

# Batch convert directory
python tools/svg_to_glb_converter.py assets/icons -o assets/models -r

# Custom extrusion depth
python tools/svg_to_glb_converter.py assets/icons -o assets/models -d 0.2
```

**Requirements:**
- Blender installed and in PATH
- Or set `BLENDER_CMD` environment variable

### 4. `build_assets_from_rules.py` - Asset Management
Automatically manages device model rules and asset mappings:
- Updates `device_model_rules.json` with actual asset paths
- Auto-converts missing GLB models from SVGs
- Scans for new devices and adds to rules
- Supports multiple vendors (Fortinet, Meraki, etc.)

**Usage:**
```bash
# Update rules with existing assets
python tools/build_assets_from_rules.py \
    --rules device_model_rules.json \
    --icons-dir assets/icons \
    --models-dir assets/models

# Scan for new devices and add to rules
python tools/build_assets_from_rules.py \
    --rules device_model_rules.json \
    --icons-dir assets/icons \
    --models-dir assets/models \
    --scan-new \
    --vendor Fortinet
```

## Complete Workflow

### Using Makefile (Recommended)

```bash
# Run complete workflow (includes VSS conversion)
make all

# Workflow without VSS (DrawIO only)
make all-drawio

# Individual steps
make convert-vss      # Convert VSS files to SVG using libvisio
make extract-icons    # Extract from DrawIO library
make clean-svgs       # Clean SVG files
make convert-svgs     # Convert to GLB
make build-assets     # Update rules

# Meraki support
make meraki-icons
make meraki-models
make meraki-assets

# Status and testing
make status           # Show current status
make test            # Test all tools
```

### Manual Workflow

```bash
# 1. Convert VSS files to SVG (if you have VSS files)
python tools/vss_to_svg_libvisio.py source_models -o assets/icons/vss_extracted -r

# 2. Extract icons from DrawIO library (alternative source)
python scripts/extract_fortinet_icons.py Fortinet.mxlibrary assets/icons

# 3. Clean SVG files
python tools/svg_cleaner.py assets/icons --recursive

# 4. Convert to GLB
python tools/svg_to_glb_converter.py assets/icons -o assets/models -r

# 5. Update rules
python tools/build_assets_from_rules.py \
    --rules device_model_rules.json \
    --icons-dir assets/icons \
    --models-dir assets/models \
    --scan-new
```

## Improvements Over Previous Workflow

### ✅ Fixed Issues

1. **SVG Cleaning**: Pre-processes SVGs to fix duplicate attributes and malformed XML
2. **Blender Isolation**: Prevents Python environment conflicts when running Blender
3. **Error Handling**: Better error messages and timeout protection
4. **Batch Processing**: Efficient batch conversion with progress tracking
5. **Auto-Conversion**: Automatically converts SVGs to GLB when models are missing
6. **Rules Management**: Auto-updates device_model_rules.json with asset paths

### 🔧 Technical Improvements

- **Environment Isolation**: Cleans PYTHONPATH/PYTHONHOME before Blender execution
- **DRACO Disabled**: Prevents compression issues in GLB export
- **Timeout Protection**: 60-second timeout prevents hanging conversions
- **Progress Tracking**: Shows conversion statistics and progress
- **Recursive Search**: Supports nested directory structures

## Directory Structure

```
vss_extraction/
├── tools/
│   ├── svg_cleaner.py              # SVG pre-processing
│   ├── svg_to_glb_converter.py     # SVG to GLB conversion
│   ├── build_assets_from_rules.py   # Asset management
│   └── README.md                    # This file
├── assets/
│   ├── icons/                       # SVG icons
│   │   ├── fortinet/
│   │   └── meraki/
│   └── models/                      # GLB 3D models
│       ├── fortinet/
│       └── meraki/
├── device_model_rules.json          # Device mapping rules
└── Makefile                         # One-command workflow
```

## Troubleshooting

### Blender Not Found
```bash
# Set BLENDER_CMD environment variable
export BLENDER_CMD=/path/to/blender
```

### Python Conflicts
The converter automatically isolates Blender from your Python environment. If issues persist:
```bash
# Run Blender directly to test
blender --background --python-expr "import sys; print(sys.executable)"
```

### SVG Import Errors
```bash
# Clean SVGs first
python tools/svg_cleaner.py assets/icons --recursive
```

### Missing GLB Models
```bash
# Auto-convert missing models
python tools/build_assets_from_rules.py \
    --rules device_model_rules.json \
    --icons-dir assets/icons \
    --models-dir assets/models
```

## Next Steps

1. Extract icons from your DrawIO libraries
2. Run `make all` to process everything
3. Check `make status` to verify results
4. Use generated GLB models in your 3D topology viewer

## References

- See `alternateconversion.md` for detailed workflow documentation
- Blender documentation: https://docs.blender.org/
- GLTF specification: https://www.khronos.org/gltf/

