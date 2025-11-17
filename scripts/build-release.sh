#!/bin/bash
"""
Release Packaging Script for Enhanced Network API Builder - Corporate Edition
Creates distribution packages and releases
"""

set -e  # Exit on any error

echo "📦 Enhanced Network API Builder - Release Packaging"
echo "=================================================="

# Configuration
VERSION=${1:-"1.0.0"}
BUILD_DIR="./build"
DIST_DIR="./dist"

echo "🔧 Configuration:"
echo "  Version: $VERSION"
echo "  Build Directory: $BUILD_DIR"
echo "  Distribution Directory: $DIST_DIR"
echo

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Update version in setup.py if provided
if [ "$VERSION" != "1.0.0" ]; then
    echo "📝 Updating version to $VERSION..."
    sed -i.bak "s/version=\"1.0.0\"/version=\"$VERSION\"/" setup.py
    rm setup.py.bak
fi

# Validate package structure
echo "✅ Validating package structure..."
python -c "
import sys
from pathlib import Path

required_files = [
    'src/enhanced_network_api/__init__.py',
    'setup.py',
    'requirements.txt',
    'README.md',
    'LICENSE',
]

missing = []
for file in required_files:
    if not Path(file).exists():
        missing.append(file)

if missing:
    print('❌ Missing required files:')
    for file in missing:
        print(f'  - {file}')
    sys.exit(1)

print('✅ All required files present')
"

# Install build dependencies
echo "📋 Installing build dependencies..."
pip install --upgrade build twine wheel

# Build source distribution
echo "📦 Building source distribution..."
python -m build --sdist

# Build wheel distribution  
echo "🎡 Building wheel distribution..."
python -m build --wheel

# Validate distributions
echo "🔍 Validating distributions..."
twine check dist/*

# Create corporate deployment package
echo "🏢 Creating corporate deployment package..."
python -c "
from src.enhanced_network_api.corporate_deployment_packager import CorporateDeploymentPackager

packager = CorporateDeploymentPackager('./corporate-deployment-$VERSION')
package_path = packager.create_corporate_deployment()
print(f'✅ Corporate package: {package_path}')
" || echo "⚠️  Corporate package creation skipped (requires full environment)"

# Create air-gapped deployment package
echo "🔒 Creating air-gapped deployment package..."
python -c "
from src.enhanced_network_api.air_gapped_deployment import AirGappedDeployment

deployment = AirGappedDeployment('./airgapped-deployment-$VERSION')
try:
    package_path = deployment.create_air_gapped_package()
    print(f'✅ Air-gapped package: {package_path}')
except Exception as e:
    print(f'⚠️  Air-gapped package creation skipped: {e}')
" || echo "⚠️  Air-gapped package creation skipped (requires full environment)"

# Generate checksums
echo "🔐 Generating checksums..."
cd dist
for file in *; do
    sha256sum "$file" >> checksums.sha256
done
cd ..

# Display build results
echo
echo "🎉 Build completed successfully!"
echo "================================="
echo
echo "📦 Distribution files:"
ls -la dist/

echo
echo "🔐 Checksums:"
cat dist/checksums.sha256

echo
echo "🚀 Ready for release:"
echo "  • Source distribution: dist/*.tar.gz"
echo "  • Wheel distribution: dist/*.whl"  
echo "  • Checksums: dist/checksums.sha256"

if [ -d "./corporate-deployment-$VERSION" ]; then
    echo "  • Corporate package: ./corporate-deployment-$VERSION/"
fi

if [ -d "./airgapped-deployment-$VERSION" ]; then
    echo "  • Air-gapped package: ./airgapped-deployment-$VERSION/"
fi

echo
echo "📋 Next steps:"
echo "  1. Test installation: pip install dist/*.whl"
echo "  2. Test corporate features"
echo "  3. Upload to PyPI: twine upload dist/*"
echo "  4. Create GitHub release"
echo "  5. Update documentation"

echo
echo "✅ Release packaging completed!"