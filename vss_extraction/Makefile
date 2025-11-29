# Makefile for VSS Extraction and 3D Model Generation Workflow
# One-command workflow for extracting icons, converting to 3D, and building assets

.PHONY: help clean-icons clean-models clean-all extract-icons clean-svgs convert-svgs build-assets update-rules all test

# Configuration
ICONS_DIR := assets/icons
MODELS_DIR := assets/models
RULES_FILE := device_model_rules.json
SVG_DIR := $(ICONS_DIR)/fortinet
MXLIBRARY := Fortinet.mxlibrary
VSS_DIR := source_models
VSS_FILES := $(wildcard $(VSS_DIR)/*.vss)
EXTRUDE_DEPTH := 0.1

# Tools
PYTHON := python3
BLENDER := blender
TOOLS_DIR := tools

help:
	@echo "VSS Extraction and 3D Model Generation Workflow"
	@echo "================================================"
	@echo ""
	@echo "Available targets:"
	@echo "  make all              - Run complete workflow (VSS → SVG → clean → convert → build)"
	@echo "  make all-drawio        - Run workflow without VSS (DrawIO only)"
	@echo "  make convert-vss       - Convert VSS files to SVG using libvisio"
	@echo "  make extract-icons     - Extract SVG icons from DrawIO library"
	@echo "  make clean-svgs        - Clean SVG files (fix duplicates, malformed XML)"
	@echo "  make convert-svgs      - Convert SVG icons to GLB 3D models"
	@echo "  make build-assets      - Build assets from rules and update JSON"
	@echo "  make update-rules      - Update device_model_rules.json with asset paths"
	@echo "  make clean-icons       - Remove all generated icons"
	@echo "  make clean-models      - Remove all generated 3D models"
	@echo "  make clean-all         - Remove all generated files"
	@echo "  make test              - Test the workflow with sample files"
	@echo ""
	@echo "Configuration:"
	@echo "  ICONS_DIR=$(ICONS_DIR)"
	@echo "  MODELS_DIR=$(MODELS_DIR)"
	@echo "  RULES_FILE=$(RULES_FILE)"
	@echo "  EXTRUDE_DEPTH=$(EXTRUDE_DEPTH)"

# Create directories
$(ICONS_DIR) $(MODELS_DIR):
	mkdir -p $@

# Convert VSS files to SVG using libvisio
convert-vss: $(ICONS_DIR)
	@echo "🔄 Converting VSS files to SVG using libvisio..."
	@if [ -n "$(VSS_FILES)" ]; then \
		$(PYTHON) $(TOOLS_DIR)/vss_to_svg_libvisio.py $(VSS_DIR) -o $(ICONS_DIR)/vss_extracted -r || \
		echo "⚠️  VSS conversion failed. Ensure libvisio is installed."; \
	else \
		echo "⚠️  No VSS files found in $(VSS_DIR). Skipping VSS conversion."; \
	fi
	@echo "✅ VSS conversion complete"

# Extract icons from DrawIO library
extract-icons: $(ICONS_DIR)
	@echo "📥 Extracting icons from DrawIO library..."
	@if [ -f "$(MXLIBRARY)" ]; then \
		$(PYTHON) scripts/extract_fortinet_icons.py $(MXLIBRARY) $(ICONS_DIR) || \
		$(PYTHON) $(TOOLS_DIR)/extract_drawio_icons.py $(MXLIBRARY) $(ICONS_DIR); \
	else \
		echo "⚠️  $(MXLIBRARY) not found. Skipping icon extraction."; \
	fi
	@echo "✅ Icon extraction complete"

# Clean SVG files
clean-svgs: $(ICONS_DIR)
	@echo "🧹 Cleaning SVG files..."
	@$(PYTHON) $(TOOLS_DIR)/svg_cleaner.py $(ICONS_DIR) --recursive || echo "⚠️  SVG cleaning failed"
	@echo "✅ SVG cleaning complete"

# Convert SVG to GLB
convert-svgs: $(MODELS_DIR) clean-svgs
	@echo "🔄 Converting SVG icons to GLB 3D models..."
	@$(PYTHON) $(TOOLS_DIR)/svg_to_glb_converter.py $(ICONS_DIR) -o $(MODELS_DIR) -d $(EXTRUDE_DEPTH) -r || \
		echo "⚠️  GLB conversion failed. Ensure Blender is installed and in PATH."
	@echo "✅ GLB conversion complete"

# Build assets from rules
build-assets: $(ICONS_DIR) $(MODELS_DIR)
	@echo "🔧 Building assets from rules..."
	@$(PYTHON) $(TOOLS_DIR)/build_assets_from_rules.py \
		--rules $(RULES_FILE) \
		--icons-dir $(ICONS_DIR) \
		--models-dir $(MODELS_DIR) \
		--scan-new \
		--vendor Fortinet || echo "⚠️  Asset building failed"
	@echo "✅ Asset building complete"

# Update rules with asset paths
update-rules: $(ICONS_DIR) $(MODELS_DIR)
	@echo "📝 Updating device model rules..."
	@$(PYTHON) $(TOOLS_DIR)/build_assets_from_rules.py \
		--rules $(RULES_FILE) \
		--icons-dir $(ICONS_DIR) \
		--models-dir $(MODELS_DIR) || echo "⚠️  Rules update failed"
	@echo "✅ Rules update complete"

# Complete workflow (with VSS conversion)
all: convert-vss extract-icons clean-svgs convert-svgs build-assets
	@echo ""
	@echo "🎉 Complete workflow finished!"
	@echo "   Icons: $(ICONS_DIR)"
	@echo "   Models: $(MODELS_DIR)"
	@echo "   Rules: $(RULES_FILE)"

# Workflow without VSS (DrawIO only)
all-drawio: extract-icons clean-svgs convert-svgs build-assets
	@echo ""
	@echo "🎉 DrawIO workflow finished!"
	@echo "   Icons: $(ICONS_DIR)"
	@echo "   Models: $(MODELS_DIR)"
	@echo "   Rules: $(RULES_FILE)"

# Clean targets
clean-icons:
	@echo "🗑️  Cleaning generated icons..."
	@rm -rf $(ICONS_DIR)/*.svg $(ICONS_DIR)/**/*.svg 2>/dev/null || true
	@echo "✅ Icons cleaned"

clean-models:
	@echo "🗑️  Cleaning generated 3D models..."
	@rm -rf $(MODELS_DIR)/*.glb $(MODELS_DIR)/**/*.glb 2>/dev/null || true
	@echo "✅ Models cleaned"

clean-all: clean-icons clean-models
	@echo "🗑️  Cleaning temporary files..."
	@rm -f $(TOOLS_DIR)/temp_blender_script.py
	@rm -f *.gltf *.glb 2>/dev/null || true
	@echo "✅ All cleaned"

# Test workflow
test:
	@echo "🧪 Testing workflow..."
	@echo "   Checking tools..."
	@$(PYTHON) -c "import sys; print(f'Python: {sys.version}')"
	@which $(BLENDER) > /dev/null && echo "   ✓ Blender found" || echo "   ✗ Blender not found"
	@$(PYTHON) $(TOOLS_DIR)/svg_cleaner.py --help > /dev/null && echo "   ✓ SVG cleaner OK" || echo "   ✗ SVG cleaner failed"
	@$(PYTHON) $(TOOLS_DIR)/svg_to_glb_converter.py --help > /dev/null && echo "   ✓ SVG to GLB converter OK" || echo "   ✗ SVG to GLB converter failed"
	@$(PYTHON) $(TOOLS_DIR)/build_assets_from_rules.py --help > /dev/null && echo "   ✓ Asset builder OK" || echo "   ✗ Asset builder failed"
	@echo "✅ Test complete"

# Meraki-specific targets
meraki-icons:
	@echo "📥 Extracting Meraki icons..."
	@mkdir -p $(ICONS_DIR)/meraki
	@if [ -f "Meraki.mxlibrary" ]; then \
		$(PYTHON) $(TOOLS_DIR)/extract_drawio_icons.py Meraki.mxlibrary $(ICONS_DIR)/meraki; \
	else \
		echo "⚠️  Meraki.mxlibrary not found"; \
	fi

meraki-models: meraki-icons
	@echo "🔄 Converting Meraki icons to GLB..."
	@mkdir -p $(MODELS_DIR)/meraki
	@$(PYTHON) $(TOOLS_DIR)/svg_to_glb_converter.py $(ICONS_DIR)/meraki -o $(MODELS_DIR)/meraki -d $(EXTRUDE_DEPTH) -r

meraki-assets: meraki-models
	@echo "🔧 Building Meraki assets..."
	@$(PYTHON) $(TOOLS_DIR)/build_assets_from_rules.py \
		--rules $(RULES_FILE) \
		--icons-dir $(ICONS_DIR)/meraki \
		--models-dir $(MODELS_DIR)/meraki \
		--scan-new \
		--vendor Meraki

# Show status
status:
	@echo "📊 Workflow Status"
	@echo "=================="
	@echo "Icons:"
	@find $(ICONS_DIR) -name "*.svg" 2>/dev/null | wc -l | xargs echo "   SVG files:"
	@echo "Models:"
	@find $(MODELS_DIR) -name "*.glb" 2>/dev/null | wc -l | xargs echo "   GLB files:"
	@echo "Rules:"
	@if [ -f $(RULES_FILE) ]; then \
		echo "   ✓ $(RULES_FILE) exists"; \
		$(PYTHON) -c "import json; d=json.load(open('$(RULES_FILE)')); print(f'   OUI entries: {len(d.get(\"oui_map\", {}))}'); print(f'   Model entries: {len(d.get(\"model_map\", {}))}")"; \
	else \
		echo "   ✗ $(RULES_FILE) not found"; \
	fi

