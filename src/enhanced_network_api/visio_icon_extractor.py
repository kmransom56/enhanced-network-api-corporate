#!/usr/bin/env python3
"""
Visio Icon Extraction Pipeline
Extract and convert vendor Visio stencils to SVG and 3D models
"""

import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass
import logging

log = logging.getLogger(__name__)

# Optional integrations from the 3d-network-topology-lab repository.
# These modules are not required for the core pipeline to work; if they are
# vendored into src/enhanced_network_api or installed on PYTHONPATH, the
# additional lab-style endpoints will become available.
try:  # pragma: no cover - optional dependency wiring
    from src.enhanced_network_api.vss_to_svg import VSSConverter, ConversionBackend  # type: ignore
except Exception as e:  # noqa: E722 - broad on purpose, purely optional
    log.warning(f"Failed to import vss_to_svg: {type(e).__name__}: {e}")
    VSSConverter = None  # type: ignore
    ConversionBackend = None  # type: ignore

try:  # pragma: no cover - optional dependency wiring
    from src.enhanced_network_api.svg_to_3d import SVGTo3DConverter  # type: ignore
except Exception:  # noqa: E722 - broad on purpose, purely optional
    SVGTo3DConverter = None  # type: ignore

@dataclass
class ExtractedIcon:
    name: str
    device_type: str
    vendor: str
    svg_path: Optional[str] = None
    obj_path: Optional[str] = None
    metadata: Optional[Dict] = None

class VisioExtractor:
    """Extract icons from Visio stencil files (.vssx, .vsdx)"""
    
    def __init__(self, output_dir: str = "extracted_icons"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.svg_dir = self.output_dir / "svg"
        self.svg_dir.mkdir(exist_ok=True)
        self.metadata_dir = self.output_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)
    
    def extract_from_visio_file(self, visio_path: str) -> List[ExtractedIcon]:
        """Extract all icons from a Visio stencil file"""
        icons = []
        visio_file = Path(visio_path)
        
        if not visio_file.exists():
            log.error(f"Visio file not found: {visio_path}")
            return icons
        
        try:
            with zipfile.ZipFile(visio_path, 'r') as zip_ref:
                # List all XML files
                file_list = zip_ref.namelist()
                
                # Find stencil master pages
                stencil_files = [f for f in file_list if 'masters/' in f and f.endswith('.xml')]
                
                for stencil_file in stencil_files:
                    with zip_ref.open(stencil_file) as xml_file:
                        tree = ET.parse(xml_file)
                        root = tree.getroot()
                        
                        # Extract shape definitions
                        shapes = root.findall('.//{http://schemas.microsoft.com/visio/2003/core}Shape')
                        
                        for shape in shapes:
                            icon = self._extract_shape_data(shape, visio_file.stem)
                            if icon:
                                icons.append(icon)
        
        except Exception as e:
            log.error(f"Failed to extract from {visio_path}: {e}")
        
        return icons
    
    def _extract_shape_data(self, shape_element: ET.Element, vendor: str) -> Optional[ExtractedIcon]:
        """Extract data from a single Visio shape element"""
        try:
            # Get shape name and ID
            shape_id = shape_element.get('ID')
            name_elem = shape_element.find('.//{http://schemas.microsoft.com/visio/2003/core}Text')
            shape_name = name_elem.text if name_elem is not None else f"Shape_{shape_id}"
            
            # Determine device type from name
            device_type = self._classify_device_type(shape_name)
            
            # Extract geometry data
            geometry = self._extract_geometry(shape_element)
            
            # Create SVG representation
            svg_content = self._create_svg_from_geometry(geometry, shape_name)
            
            # Save SVG file
            svg_filename = f"{self._sanitize_filename(shape_name)}.svg"
            svg_path = self.svg_dir / svg_filename
            
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            # Collect metadata
            metadata = {
                'shape_id': shape_id,
                'original_name': shape_name,
                'device_type': device_type,
                'vendor': vendor,
                'geometry_elements': len(geometry),
                'svg_path': str(svg_path)
            }
            
            # Save metadata
            metadata_path = self.metadata_dir / f"{svg_filename}.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            return ExtractedIcon(
                name=shape_name,
                device_type=device_type,
                vendor=vendor,
                svg_path=str(svg_path),
                metadata=metadata
            )
            
        except Exception as e:
            log.error(f"Failed to extract shape data: {e}")
            return None
    
    def _classify_device_type(self, shape_name: str) -> str:
        """Classify device type based on shape name"""
        name_lower = shape_name.lower()
        
        # Fortinet device patterns
        if 'fortigate' in name_lower:
            return 'Firewall/UTM'
        elif 'fortiap' in name_lower or 'wifi' in name_lower or 'wireless' in name_lower:
            return 'Wireless Access Point'
        elif 'fortiswitch' in name_lower or 'switch' in name_lower:
            return 'Switch'
        elif 'fortianalyzer' in name_lower:
            return 'Log Management'
        elif 'fortimanager' in name_lower:
            return 'Management Platform'
        
        # Meraki device patterns
        elif 'mr' in name_lower and ('wireless' in name_lower or 'wifi' in name_lower):
            return 'Wireless Access Point'
        elif 'mx' in name_lower or 'firewall' in name_lower:
            return 'Security Appliance/Firewall'
        elif 'ms' in name_lower and 'switch' in name_lower:
            return 'Switch'
        elif 'mv' in name_lower or 'camera' in name_lower:
            return 'Security Camera'
        elif 'mt' in name_lower or 'sensor' in name_lower:
            return 'IoT Sensor'
        elif 'mg' in name_lower or 'cellular' in name_lower:
            return 'Cellular Gateway'
        
        # Generic patterns
        elif 'router' in name_lower:
            return 'Router'
        elif 'switch' in name_lower:
            return 'Switch'
        elif 'ap' in name_lower or 'access point' in name_lower:
            return 'Wireless Access Point'
        elif 'firewall' in name_lower:
            return 'Firewall/UTM'
        elif 'camera' in name_lower:
            return 'Security Camera'
        elif 'server' in name_lower:
            return 'Server'
        elif 'laptop' in name_lower:
            return 'Laptop'
        elif 'phone' in name_lower or 'mobile' in name_lower:
            return 'Smartphone'
        elif 'tablet' in name_lower:
            return 'Tablet'
        
        return 'Unknown Device'
    
    def _extract_geometry(self, shape_element: ET.Element) -> List[Dict]:
        """Extract geometry data from shape element"""
        geometry = []
        
        # Find geometry elements
        geom_elements = shape_element.findall('.//{http://schemas.microsoft.com/visio/2003/core}Geom')
        
        for geom in geom_elements:
            # Extract path commands
            move_to = geom.find('.//{http://schemas.microsoft.com/visio/2003/core}MoveTo')
            if move_to is not None:
                x_elem = move_to.find('.//{http://schemas.microsoft.com/visio/2003/core}X')
                y_elem = move_to.find('.//{http://schemas.microsoft.com/visio/2003/core}Y')
                if x_elem is not None and y_elem is not None:
                    geometry.append({
                        'type': 'move',
                        'x': float(x_elem.text) if x_elem.text else 0,
                        'y': float(y_elem.text) if y_elem.text else 0
                    })
            
            # Extract line segments
            line_to_elements = geom.findall('.//{http://schemas.microsoft.com/visio/2003/core}LineTo')
            for line_to in line_to_elements:
                x_elem = line_to.find('.//{http://schemas.microsoft.com/visio/2003/core}X')
                y_elem = line_to.find('.//{http://schemas.microsoft.com/visio/2003/core}Y')
                if x_elem is not None and y_elem is not None:
                    geometry.append({
                        'type': 'line',
                        'x': float(x_elem.text) if x_elem.text else 0,
                        'y': float(y_elem.text) if y_elem.text else 0
                    })
        
        return geometry
    
    def _create_svg_from_geometry(self, geometry: List[Dict], shape_name: str) -> str:
        """Create SVG content from geometry data"""
        if not geometry:
            # Create a placeholder rectangle
            return '''<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
                <rect width="100" height="100" fill="#cccccc" stroke="#333333" stroke-width="2"/>
                <text x="50" y="50" text-anchor="middle" font-family="Arial" font-size="12">{name}</text>
            </svg>'''.format(name=shape_name)
        
        # Scale and translate coordinates for better visibility
        min_x = min(g['x'] for g in geometry if g['type'] in ['move', 'line'])
        max_x = max(g['x'] for g in geometry if g['type'] in ['move', 'line'])
        min_y = min(g['y'] for g in geometry if g['type'] in ['move', 'line'])
        max_y = max(g['y'] for g in geometry if g['type'] in ['move', 'line'])
        
        width = max_x - min_x or 100
        height = max_y - min_y or 100
        scale = 100 / max(width, height)
        
        # Build SVG path
        path_commands = []
        for geom in geometry:
            x = (geom['x'] - min_x) * scale
            y = (geom['y'] - min_y) * scale
            
            if geom['type'] == 'move':
                path_commands.append(f"M {x} {y}")
            elif geom['type'] == 'line':
                path_commands.append(f"L {x} {y}")
        
        path_data = " ".join(path_commands)
        
        svg_template = '''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
            <path d="{path}" fill="#cccccc" stroke="#333333" stroke-width="2"/>
            <text x="{text_x}" y="{text_y}" text-anchor="middle" font-family="Arial" font-size="10">{name}</text>
        </svg>'''
        
        return svg_template.format(
            width=width * scale,
            height=height * scale,
            path=path_data,
            text_x=width * scale / 2,
            text_y=height * scale / 2,
            name=shape_name
        )
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename

class IconDownloader:
    """Download vendor icon libraries"""
    
    def __init__(self, download_dir: str = "vendor_icons"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
    
    def download_fortinet_icons(self) -> Optional[str]:
        """Download Fortinet Visio stencil"""
        fortinet_url = "https://www.fortinet.com/content/dam/fortinet/assets/downloads/Fortinet%20Visio%20Stencil.zip"
        
        try:
            response = requests.get(fortinet_url, timeout=30)
            response.raise_for_status()
            
            zip_path = self.download_dir / "Fortinet_Visio_Stencil.zip"
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            log.info(f"Downloaded Fortinet stencil to {zip_path}")
            return str(zip_path)
            
        except Exception as e:
            log.error(f"Failed to download Fortinet stencil: {e}")
            return None
    
    def download_meraki_icons(self) -> Optional[str]:
        """Download Meraki Visio stencil"""
        # Note: Meraki stencils may need manual download due to authentication
        meraki_url = "https://meraki.cisco.com/product-collateral/cisco-meraki-visio-stencils/"
        
        log.warning("Meraki stencils may require manual download from: " + meraki_url)
        return None

class Blender3DGenerator:
    """Generate 3D models from SVG using Blender automation"""
    
    def __init__(self, blender_path: str = "blender", output_dir: str = "3d_models"):
        self.blender_path = blender_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_3d_models(self, svg_dir: str) -> List[str]:
        """Generate 3D models from all SVG files in directory"""
        svg_path = Path(svg_dir)
        if not svg_path.exists():
            log.error(f"SVG directory not found: {svg_dir}")
            return []
        
        generated_models = []
        
        for svg_file in svg_path.glob("*.svg"):
            obj_path = self.output_dir / f"{svg_file.stem}.obj"
            
            # Create Blender script
            blender_script = self._create_blender_script(str(svg_file), str(obj_path))
            
            # Run Blender
            try:
                import subprocess
                result = subprocess.run([
                    self.blender_path, "--background", "--python-expr", blender_script
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and obj_path.exists():
                    generated_models.append(str(obj_path))
                    log.info(f"Generated 3D model: {obj_path}")
                else:
                    log.error(f"Blender failed for {svg_file}: {result.stderr}")
            
            except Exception as e:
                log.error(f"Failed to generate 3D model for {svg_file}: {e}")
        
        return generated_models
    
    def _create_blender_script(self, svg_path: str, obj_path: str) -> str:
        """Create Blender Python script for SVG to 3D conversion"""
        script = f'''
import bpy
import os

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import SVG
svg_path = "{svg_path}"
bpy.ops.import_curve.svg(filepath=svg_path)

# Convert curves to mesh and extrude
for obj in bpy.context.selected_objects:
    if obj.type == 'CURVE':
        bpy.context.view_layer.objects.active = obj
        
        # Convert to mesh
        bpy.ops.object.convert(target='MESH')
        
        # Add Solidify modifier for 3D depth
        solidify = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
        solidify.thickness = 0.05
        
        # Apply modifier
        bpy.ops.object.modifier_apply(modifier="Solidify")

# Export as OBJ
obj_path = "{obj_path}"
bpy.ops.export_scene.obj(filepath=obj_path)
'''
        return script

def create_icon_extraction_api(app):
    """Create FastAPI endpoints for icon extraction"""
    from fastapi import HTTPException, UploadFile, File
    from pydantic import BaseModel
    
    class ExtractionRequest(BaseModel):
        vendor: str
        device_types: Optional[List[str]] = None
    
    class ExtractionResponse(BaseModel):
        icons: List[ExtractedIcon]
        total: int
    
    @app.post("/api/icons/extract", response_model=ExtractionResponse)
    async def extract_visio_icons(file: UploadFile = File(...), vendor: str = "Unknown"):
        """Extract icons from uploaded Visio stencil file"""
        try:
            # Save uploaded file
            temp_path = f"temp_{file.filename}"
            with open(temp_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Extract icons
            extractor = VisioExtractor()
            icons = extractor.extract_from_visio_file(temp_path)
            
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
            
            return ExtractionResponse(icons=icons, total=len(icons))
            
        except Exception as e:
            log.error(f"Icon extraction error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/icons/generate-3d")
    async def generate_3d_models(svg_directory: str = "extracted_icons/svg"):
        """Generate 3D models from SVG files"""
        try:
            generator = Blender3DGenerator()
            models = generator.generate_3d_models(svg_directory)
            return {"generated_models": models, "total": len(models)}
        except Exception as e:
            log.error(f"3D generation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/icons/vss-to-svg-lab")
    async def vss_to_svg_lab(file: UploadFile = File(...), scale: float = 1.0):
        """Convert uploaded VSS/VSSX stencil to SVGs using the lab VSSConverter.

        This endpoint is optional and only works when vss_to_svg.py from the
        3d-network-topology-lab project is available as a module. When it is
        not present, a clear 500 error is returned explaining the situation.
        """
        if VSSConverter is None:
            raise HTTPException(
                status_code=500,
                detail=(
                    "vss_to_svg backend not available. Ensure vss_to_svg.py from "
                    "3d-network-topology-lab is vendored into src/enhanced_network_api "
                    "or installed on PYTHONPATH."
                ),
            )

        temp_path = Path(f"temp_{file.filename}")
        try:
            with temp_path.open("wb") as buffer:
                buffer.write(await file.read())

            output_dir = Path("extracted_icons") / "lab_vss_svgs"
            converter = VSSConverter()
            svg_paths = converter.convert_vss(temp_path, output_dir, scale=scale, prefix="")

            return {
                "backend": getattr(converter, "backend", None).value
                if getattr(converter, "backend", None)
                else "unknown",
                "svg_files": [str(p) for p in svg_paths],
                "total": len(svg_paths),
            }
        except Exception as e:  # pragma: no cover - I/O heavy path
            log.error(f"VSS to SVG lab conversion error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            temp_path.unlink(missing_ok=True)

    @app.post("/api/icons/svg-to-3d-lab")
    async def svg_to_3d_lab(
        input_dir: str = "extracted_icons/lab_vss_svgs", output_dir: str = "lab_3d_models"
    ):
        """Convert SVGs to 3D models using the lab SVGTo3DConverter.

        This uses the lightweight OBJ-generation pipeline from svg_to_3d.py,
        which does not require Blender and is tailored for Babylon.js-friendly
        3D meshes.
        """
        if SVGTo3DConverter is None:
            raise HTTPException(
                status_code=500,
                detail=(
                    "svg_to_3d backend not available. Ensure svg_to_3d.py from "
                    "3d-network-topology-lab is vendored into src/enhanced_network_api "
                    "or installed on PYTHONPATH."
                ),
            )

        try:
            converter = SVGTo3DConverter(Path(input_dir), Path(output_dir))
            generated: List[str] = []
            for svg_path in Path(input_dir).glob("*.svg"):
                optimized = converter.optimize_svg_for_3d(svg_path)
                obj_path = converter.svg_to_obj(optimized)
                if obj_path:
                    generated.append(str(obj_path))

            return {"generated_models": generated, "total": len(generated)}
        except Exception as e:  # pragma: no cover - I/O heavy path
            log.error(f"SVG to 3D lab conversion error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/icons/download-vendor/{vendor}")
    async def download_vendor_icons(vendor: str):
        """Download vendor icon libraries"""
        try:
            downloader = IconDownloader()
            
            if vendor.lower() == "fortinet":
                zip_path = downloader.download_fortinet_icons()
                if zip_path:
                    return {"message": "Downloaded successfully", "path": zip_path}
            
            elif vendor.lower() == "meraki":
                return {"message": "Manual download required", "url": "https://meraki.cisco.com/product-collateral/cisco-meraki-visio-stencils/"}
            
            else:
                raise HTTPException(status_code=404, detail=f"Vendor {vendor} not supported")
                
        except Exception as e:
            log.error(f"Download error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

if __name__ == "__main__":
    # Demo usage
    extractor = VisioExtractor()
    
    # Example: Extract from a local Visio file
    # icons = extractor.extract_from_visio_file("Fortinet_Visio_Stencil.zip")
    
    print("Icon extraction pipeline ready")