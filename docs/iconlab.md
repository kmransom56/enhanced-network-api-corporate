I want to automate creating 3d models from vendor specific 2d icons. I know that Meraki and Fortinet Visio icons are 3d type. I want to extract them accurately. There are also repositories for restaurant technology icons. I want to automate finding so that I can match mac address with device information.

Based on my research, let me provide you with a comprehensive guide for automating the extraction of 3D models from vendor-specific Visio icons and matching devices via MAC address lookup.
Automating 3D Model Extraction from Visio Icons and Device Identification
Part 1: Understanding Visio 3D Icon Structure

Visio File Format Fundamentals:

Modern Visio files (.vsdx, .vssx, .vstx) use the Open Packaging Conventions (OPC) standard:

​

    Files are ZIP archives containing XML documents

    Structure includes pages, shapes, masters, and relationships

    3D-like Visio icons are actually 2.5D isometric projections with shading effects, not true 3D geometry

    ​

    True 3D shapes in Visio contain extrusion data but are still rendered as 2D projections

Key Insight: Meraki and Fortinet Visio stencils contain isometric 2D vector graphics that appear 3D through clever use of perspective, shading, and gradients—not actual 3D mesh data.

​
Part 2: Extracting Icon Data from Visio Files
Method 1: Python VSDX Library (Recommended)

The vsdx Python library provides direct programmatic access to Visio files:

​

Installation:

bash
pip install vsdx

Extract Shapes from Visio Stencils:

python
from vsdx import VisioFile

# Open Fortinet or Meraki Visio stencil
with VisioFile('Fortinet_Visio_Stencil.vssx') as vis:
    # Access first page (stencil master page)
    page = vis.pages[0]
    
    # Get all master shapes
    all_shapes = page.all_shapes
    
    for shape in all_shapes:
        shape_name = shape.text
        shape_id = shape.ID
        
        # Extract shape geometry data
        print(f"Shape: {shape_name}, ID: {shape_id}")
        
        # Get shape properties
        if hasattr(shape, 'data_properties'):
            for prop in shape.data_properties:
                print(f"  Property: {prop.label} = {prop.value}")

Find Specific Device Icons:

python
with VisioFile('Meraki_Visio_Stencil.vssx') as vis:
    page = vis.pages[0]
    
    # Find specific device types
    fortigate = page.find_shape_by_text('FortiGate')
    meraki_ap = page.find_shape_by_text('MR')  # Meraki AP models
    
    if fortigate:
        # Access shape XML data
        shape_xml = fortigate.xml
        
        # Extract visual properties
        fill_color = fortigate.fill
        line_color = fortigate.line

Method 2: Aspose.Diagram Library (Commercial, Full-Featured)

Aspose.Diagram for Python provides comprehensive Visio manipulation:

​

python
import aspose.diagram as diagram

# Load Visio stencil
visio_file = diagram.Diagram("Fortinet_Stencil.vssx")

# Access master shapes
masters = visio_file.masters

for master in masters:
    master_name = master.name
    master_id = master.id
    
    # Extract shape data
    for shape in master.shapes:
        # Get shape geometry
        geometry = shape.geoms
        
        # Extract path data for 2D outline
        for geom in geometry:
            move_to = geom.moveTo
            line_to = geom.lineTo
            # Process path commands

Export Shapes as Images:

python
# Extract individual icon as image
shape = visio_file.pages[0].shapes[0]

# Save as PNG with transparent background
shape_stream = shape.to_image("PNG")

# Or export to SVG (vector format)
shape.to_svg("fortigate_icon.svg")

Method 3: Direct XML Parsing (Low-Level Access)

Since VSDX files are ZIP archives with XML content:

​

python
import zipfile
import xml.etree.ElementTree as ET

# Extract Visio XML structure
with zipfile.ZipFile('Meraki_Stencil.vssx', 'r') as zip_ref:
    # List all XML files
    file_list = zip_ref.namelist()
    
    # Extract page XML (contains shape definitions)
    with zip_ref.open('visio/pages/page1.xml') as page_xml:
        tree = ET.parse(page_xml)
        root = tree.getroot()
        
        # Find shape elements
        shapes = root.findall('.//Shape')
        
        for shape in shapes:
            # Extract shape attributes
            shape_id = shape.get('ID')
            name = shape.get('Name')
            
            # Get geometry data (paths, fills, strokes)
            geom = shape.find('.//Geom')
            if geom is not None:
                # Process path commands
                paths = geom.findall('.//LineTo')
                # Extract coordinate data

Part 3: Converting Visio 2.5D Icons to True 3D Models

Since Visio icons are isometric 2D projections, you need to extrude or reconstruct them into 3D mesh files.
Option A: SVG to 3D Extrusion Workflow

Step 1: Export Visio Shapes to SVG

python
# Using Aspose.Diagram
shape.to_svg("device_icon.svg")

# Or using Visio COM API (Windows only)
import win32com.client

visio = win32com.client.Dispatch("Visio.Application")
doc = visio.Documents.Open("stencil.vssx")
page = doc.Pages[1]
shape = page.Shapes[1]

# Export single shape to SVG
shape.Export("device_icon.svg")

Step 2: Import SVG into Blender for 3D Extrusion

python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import SVG
bpy.ops.import_curve.svg(filepath="device_icon.svg")

# Convert curves to mesh
for obj in bpy.context.selected_objects:
    if obj.type == 'CURVE':
        bpy.context.view_layer.objects.active = obj
        # Convert to mesh
        bpy.ops.object.convert(target='MESH')
        
        # Add Solidify modifier for 3D depth
        solidify = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
        solidify.thickness = 0.05  # Adjust depth
        
        # Apply modifier
        bpy.ops.object.modifier_apply(modifier="Solidify")

# Export as OBJ or STL
bpy.ops.export_scene.obj(filepath="device_3d_model.obj")
# Or STL for 3D printing
bpy.ops.export_mesh.stl(filepath="device_3d_model.stl")

Automated Blender Script (Batch Processing):

python
import bpy
import os

svg_folder = "/path/to/exported/svgs"
output_folder = "/path/to/3d/models"

for svg_file in os.listdir(svg_folder):
    if svg_file.endswith('.svg'):
        # Clear scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        # Import SVG
        svg_path = os.path.join(svg_folder, svg_file)
        bpy.ops.import_curve.svg(filepath=svg_path)
        
        # Extrude to 3D
        for obj in bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.convert(target='MESH')
            
            solidify = obj.modifiers.new("Solidify", 'SOLIDIFY')
            solidify.thickness = 0.1
            bpy.ops.object.modifier_apply(modifier="Solidify")
        
        # Export
        output_name = svg_file.replace('.svg', '.obj')
        output_path = os.path.join(output_folder, output_name)
        bpy.ops.export_scene.obj(filepath=output_path)
        
        print(f"Converted {svg_file} to {output_name}")

Option B: Image-Based 3D Reconstruction

For vendor product photos in icon libraries, use image-to-3D tools:

Using ImageToSTL Online Tools:

    Extract device images from Visio stencils

​

Upload to ImageToSTL or similar services

Apply heightmap or extrude conversion

    ​

    Download as OBJ/STL

Python Script Using Online API:

python
import requests

def convert_image_to_3d(image_path, output_path):
    # Example using hypothetical API
    files = {'file': open(image_path, 'rb')}
    params = {
        'extrude_depth': 10,
        'quality': 'high',
        'format': 'obj'
    }
    
    response = requests.post(
        'https://api.imagetostl.com/convert',
        files=files,
        data=params
    )
    
    with open(output_path, 'wb') as f:
        f.write(response.content)

Part 4: Vendor Icon Sources
Fortinet Icons

Official Sources:

    Fortinet Icon Library: https://www.fortinet.com/resources/icon-library

​

Fortinet Visio Stencil: https://www.fortinet.com/content/dam/fortinet/assets/downloads/Fortinet%20Visio%20Stencil.zip

​

Icons Portal: https://icons.fortinet.com/

    ​

Community Sources:

    Graffletopia Fortinet Stencils: Converted from official Visio stencils for OmniGraffle

​

VisioCafe: Independent repository

​

GitHub Repositories: Community-maintained collections

    ​

Meraki Icons

Official Sources:

    Cisco Meraki Visio Stencils: https://meraki.cisco.com/product-collateral/cisco-meraki-visio-stencils/

​

Cisco Visio Stencil Listing: https://www.cisco.com/c/en/us/products/visio-stencil-listing.html

​

Meraki Collateral Library: Search with keyword "photograph" for product images

    ​

Notes:

    Meraki stencils last updated December 2019

​

Newer models (MX75/85/95, MS130, etc.) missing from stencil library

​

Community creating custom stencils from web images

    ​

Restaurant Technology Icons

Icon Repositories:

    Icons8 - POS System Icons

​

    Customizable restaurant/retail POS icons

    Multiple styles (flat, 3D, isometric)

    API available for programmatic access

iStock - POS System Illustrations

​

    945+ POS system vector images

    Royalty-free licensing

    Includes POS terminals, cash registers, tablets

Adobe Stock - Restaurant Tech Icons

​

    Line-style restaurant technology icons

    POS systems, tablet ordering, kitchen displays

Vecteezy - Restaurant POS Vectors

​

    636+ free restaurant POS vectors

    SVG and PNG formats

    Commercial use allowed

Freepik - Restaurant POS Graphics

    ​

        Free and premium options

        Multiple file formats (SVG, AI, EPS)

Extracting Icons Programmatically:

python
import requests
from bs4 import BeautifulSoup

def scrape_icon_repository(url, search_term):
    response = requests.get(f"{url}/search?q={search_term}")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find icon download links (site-specific selectors)
    icon_links = soup.find_all('a', class_='download-link')
    
    for link in icon_links:
        icon_url = link['href']
        icon_name = link.get('data-name', 'icon.svg')
        
        # Download icon
        icon_data = requests.get(icon_url).content
        with open(f"icons/{icon_name}", 'wb') as f:
            f.write(icon_data)

Part 5: MAC Address to Device Type Matching
Understanding MAC Address Structure

MAC Address Format:

    6 bytes (48 bits): AA:BB:CC:DD:EE:FF

    First 3 bytes (OUI): Organizationally Unique Identifier - identifies manufacturer

    ​

    Last 3 bytes: Device-specific identifier

OUI Database Sources:

    IEEE Registration Authority (Official)

​

    MA-L (Large): 16.7 million addresses

    MA-M (Medium): 1 million addresses

    MA-S (Small): 4,096 addresses

    Updated constantly

Wireshark Manufacturer Database

    ​

        Enhanced vendor names

        Application-specific identifiers

        Community-maintained additions

Automated MAC Lookup Implementation

Option 1: Using MAC Lookup APIs

WhoisXML API:

python
import requests

def lookup_mac_address(mac):
    api_key = "YOUR_API_KEY"
    url = f"https://mac-address.whoisxmlapi.com/api/v1"
    
    params = {
        'apiKey': api_key,
        'macAddress': mac,
        'outputFormat': 'JSON'
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    return {
        'vendor': data.get('vendorDetails', {}).get('companyName'),
        'oui': data.get('oui'),
        'is_virtual': data.get('isVirtualMachine'),
        'device_type': data.get('deviceType'),
        'address': data.get('vendorDetails', {}).get('companyAddress')
    }

# Example
device_info = lookup_mac_address("44:38:39:ff:ef:57")
print(f"Vendor: {device_info['vendor']}")
print(f"Device Type: {device_info['device_type']}")

macaddress.io API:

python
def lookup_mac_detailed(mac):
    url = f"https://api.macaddress.io/v1?apiKey=${MACADDREESS_IO_API_KEY}&output=json"
    params = {'search': mac}
    
    response = requests.get(url, params=params)
    data = response.json()
    
    vendor_details = data.get('vendorDetails', {})
    block_details = data.get('blockDetails', {})
    
    return {
        'company': vendor_details.get('companyName'),
        'country': vendor_details.get('countryCode'),
        'block_type': block_details.get('assignmentBlockSize'),
        'is_private': block_details.get('isPrivate'),
        'mac_type': data.get('macAddressDetails', {}).get('transmissionType')
    }

Option 2: Local OUI Database

Download and Process IEEE OUI Database:

python
import requests
import csv
import re

# Download IEEE OUI database
def download_oui_database():
    url = "https://standards-oui.ieee.org/oui/oui.csv"
    response = requests.get(url)
    
    with open('oui_database.csv', 'wb') as f:
        f.write(response.content)

# Build fast lookup dictionary
def build_oui_lookup():
    oui_dict = {}
    
    with open('oui_database.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            oui = row['Assignment'].replace('-', ':').upper()
            vendor = row['Organization Name']
            address = row['Organization Address']
            
            oui_dict[oui] = {
                'vendor': vendor,
                'address': address
            }
    
    return oui_dict

# Fast MAC lookup
def lookup_mac_local(mac, oui_dict):
    # Normalize MAC address
    mac_clean = mac.replace(':', '').replace('-', '').replace('.', '').upper()
    
    # Extract OUI (first 6 hex digits)
    oui = ':'.join([mac_clean[i:i+2] for i in range(0, 6, 2)])
    
    return oui_dict.get(oui, {'vendor': 'Unknown', 'address': ''})

# Build database once
oui_lookup = build_oui_lookup()

# Fast lookups
device1 = lookup_mac_local("F0:9F:C2:12:34:56", oui_lookup)  # Cisco Meraki
device2 = lookup_mac_local("90:6C:AC:98:76:54", oui_lookup)  # Fortinet

Enhanced Device Classification

Beyond OUI: Device Fingerprinting

python
def classify_device_type(mac, vendor, additional_data=None):
    """
    Classify device type based on MAC, vendor, and optional network behavior
    """
    
    # Normalize vendor name
    vendor_lower = vendor.lower()
    
    # Vendor-specific device classification
    device_classifications = {
        'cisco meraki': {
            'MR': 'Wireless Access Point',
            'MS': 'Switch',
            'MX': 'Security Appliance/Firewall',
            'MV': 'Security Camera',
            'MT': 'IoT Sensor',
            'MG': 'Cellular Gateway'
        },
        'fortinet': {
            'FortiGate': 'Firewall/UTM',
            'FortiAP': 'Wireless Access Point',
            'FortiSwitch': 'Switch',
            'FortiAnalyzer': 'Log Management',
            'FortiManager': 'Management Platform'
        },
        'apple': {
            'iPad': 'Tablet',
            'iPhone': 'Smartphone',
            'MacBook': 'Laptop',
            'Apple TV': 'Media Device'
        }
    }
    
    # Check for specific device patterns
    for vendor_key, devices in device_classifications.items():
        if vendor_key in vendor_lower:
            # If additional context available (DHCP hostname, etc.)
            if additional_data and 'hostname' in additional_data:
                hostname = additional_data['hostname']
                for device_prefix, device_type in devices.items():
                    if device_prefix.lower() in hostname.lower():
                        return device_type
            
            # Default classification based on vendor
            return f"{vendor} Device"
    
    # Generic classification based on OUI patterns
    if 'random' in detect_random_mac(mac):
        return 'Mobile Device (Randomized MAC)'
    
    return 'Unknown Device'

def detect_random_mac(mac):
    """
    Detect if MAC uses privacy randomization
    """
    mac_clean = mac.replace(':', '').replace('-', '')
    second_char = mac_clean[1].upper()
    
    # Locally administered bit check
    if second_char in ['2', '6', 'A', 'E']:
        return 'random_mac'
    return 'static_mac'

Restaurant POS Device Classification

Mapping MAC to POS Equipment:

python
# Restaurant technology vendor OUIs
restaurant_tech_ouis = {
    'Clover (Ingenico)': ['00:0C:F1', '00:1D:6A'],
    'Square (Block Inc)': ['AC:BC:32', 'C4:AD:34'],
    'Toast': ['B8:27:EB'],  # Often Raspberry Pi-based
    'NCR Aloha': ['00:0D:93', '00:40:AA'],
    'Micros (Oracle)': ['00:0C:29', '00:50:56'],
    'Revel Systems': ['iPad-based'],  # Uses Apple MACs
    'Lightspeed': ['Varies'],
    'ShopKeep': ['iPad-based'],
    'Vend': ['Varies'],
    'Loyverse': ['Android/iOS']
}

def identify_pos_device(mac, oui_dict):
    """
    Identify POS system from MAC address
    """
    vendor_info = lookup_mac_local(mac, oui_dict)
    vendor = vendor_info['vendor']
    
    # Check against known POS vendors
    for pos_system, oui_list in restaurant_tech_ouis.items():
        if any(mac.upper().startswith(oui) for oui in oui_list):
            return {
                'pos_system': pos_system,
                'device_type': 'POS Terminal',
                'vendor': vendor
            }
    
    # Heuristic detection
    if 'apple' in vendor.lower():
        return {
            'pos_system': 'iPad-based POS (Square/Toast/Revel)',
            'device_type': 'POS Terminal',
            'vendor': vendor
        }
    
    if 'raspberry' in vendor.lower():
        return {
            'pos_system': 'Embedded POS System',
            'device_type': 'POS Terminal',
            'vendor': vendor
        }
    
    return {
        'pos_system': 'Unknown',
        'device_type': 'Undetermined',
        'vendor': vendor
    }

Part 6: Integrated Workflow - MAC Address to 3D Model Matching

Complete Automation Pipeline:

python
import json
from pathlib import Path

class DeviceModelMatcher:
    def __init__(self, oui_database_path, model_library_path):
        self.oui_dict = self.load_oui_database(oui_database_path)
        self.model_library = self.load_model_library(model_library_path)
    
    def load_oui_database(self, path):
        # Load pre-built OUI lookup
        with open(path, 'r') as f:
            return json.load(f)
    
    def load_model_library(self, path):
        """
        Load mapping of vendor/device to 3D model file
        
        Format:
        {
            "Cisco Meraki MR46": "models/meraki_mr46.obj",
            "Fortinet FortiGate 60F": "models/fortigate_60f.obj",
            "Square POS Terminal": "models/square_terminal.obj"
        }
        """
        with open(path, 'r') as f:
            return json.load(f)
    
    def match_mac_to_model(self, mac_address, additional_context=None):
        """
        Given MAC address, return vendor, device type, and 3D model path
        """
        # Step 1: Lookup vendor from MAC
        oui = ':'.join(mac_address.split(':')[:3]).upper()
        vendor_info = self.oui_dict.get(oui, {})
        vendor = vendor_info.get('vendor', 'Unknown')
        
        # Step 2: Classify device type
        device_type = self.classify_device(mac_address, vendor, additional_context)
        
        # Step 3: Match to 3D model
        model_key = f"{vendor} {device_type}"
        
        # Try exact match first
        model_path = self.model_library.get(model_key)
        
        # Try partial matches
        if not model_path:
            for key in self.model_library.keys():
                if vendor.lower() in key.lower():
                    model_path = self.model_library[key]
                    break
        
        # Default generic model if no match
        if not model_path:
            model_path = self.get_generic_model(device_type)
        
        return {
            'mac_address': mac_address,
            'vendor': vendor,
            'device_type': device_type,
            'model_path': model_path,
            'confidence': 'high' if model_path in self.model_library.values() else 'low'
        }
    
    def classify_device(self, mac, vendor, context):
        # Use classification logic from earlier
        return classify_device_type(mac, vendor, context)
    
    def get_generic_model(self, device_type):
        """Return generic 3D model based on device category"""
        generic_models = {
            'Wireless Access Point': 'models/generic_ap.obj',
            'Firewall/UTM': 'models/generic_firewall.obj',
            'Switch': 'models/generic_switch.obj',
            'POS Terminal': 'models/generic_pos.obj',
            'Camera': 'models/generic_camera.obj'
        }
        return generic_models.get(device_type, 'models/generic_device.obj')

# Usage Example
matcher = DeviceModelMatcher('oui_database.json', 'model_library.json')

# Discover devices on network (example MAC addresses)
discovered_devices = [
    {'mac': 'F0:9F:C2:12:34:56', 'hostname': 'MR46-Office'},
    {'mac': '90:6C:AC:98:76:54', 'hostname': 'FortiGate-60F'},
    {'mac': 'AC:BC:32:11:22:33', 'hostname': 'Square-Terminal-01'}
]

# Match each device to 3D model
matched_devices = []
for device in discovered_devices:
    match = matcher.match_mac_to_model(
        device['mac'],
        additional_context={'hostname': device['hostname']}
    )
    matched_devices.append(match)
    
    print(f"MAC: {match['mac_address']}")
    print(f"Vendor: {match['vendor']}")
    print(f"Device: {match['device_type']}")
    print(f"3D Model: {match['model_path']}")
    print(f"Confidence: {match['confidence']}")
    print("---")

# Export mapping for use in visualization tools
with open('device_3d_mapping.json', 'w') as f:
    json.dump(matched_devices, f, indent=2)

Integration with Network Topology Visualization:

python
# Generate DrawIO/NetBrain input with 3D model references
def generate_topology_with_models(matched_devices, output_file):
    topology_data = {
        'devices': []
    }
    
    for device in matched_devices:
        topology_data['devices'].append({
            'id': device['mac_address'],
            'name': device['device_type'],
            'vendor': device['vendor'],
            'icon_3d': device['model_path'],
            'icon_2d': device['model_path'].replace('.obj', '.svg'),
            'position': {'x': 0, 'y': 0, 'z': 0}  # To be determined by layout algorithm
        })
    
    with open(output_file, 'w') as f:
        json.dump(topology_data, f, indent=2)

generate_topology_with_models(matched_devices, 'topology_with_3d.json')

Key Takeaways

3D Model Extraction:

    Visio "3D" icons are 2.5D isometric projections, not true 3D geometry

    Extract via vsdx Python library or Aspose.Diagram

    Convert to SVG, then extrude in Blender for true 3D models

    Automate batch processing with Python scripts

MAC Address Matching:

    Use IEEE OUI database for vendor identification

    Enhance with device fingerprinting for specific model detection

    Build local OUI lookup for fast bulk processing

    Map vendor + hostname patterns to specific device types

Restaurant POS Integration:

    Many POS systems use iPad (Apple OUI) or Android tablets

    Specialized POS hardware (NCR, Micros) has dedicated OUIs

    Use icon repositories (Icons8, Adobe Stock) for POS graphics

    Extract and convert to 3D using same workflow as network devices

Automation Pipeline:

    Network scan → MAC address collection

    MAC → Vendor lookup (OUI database)

    Vendor + Context → Device classification

    Device type → 3D model mapping

    Export to topology visualization tools
   
This integrated approach enables automatic generation of 3D network topology diagrams with accurate device representations matched from live network discovery data.

## Enhanced Network API Integration

The Enhanced Network API platform now provides integrated endpoints for VSS to SVG and SVG to 3D conversion, leveraging the 3D Network Topology Lab's conversion pipelines.

### FastAPI Endpoints

#### VSS to SVG Conversion

```python
# Endpoint: POST /api/icons/vss-to-svg-lab
# Converts uploaded VSS/VSSX stencil to SVGs using the lab VSSConverter

curl -F "file=@FortiGate_Series_R22_2025Q2.vss" \
     -F "scale=1.0" \
     http://localhost:8001/api/icons/vss-to-svg-lab
```

Response:
```json
{
  "backend": "vss_extractor",
  "svg_files": [
    "extracted_icons/lab_vss_svgs/shape_001_FortiGate.svg",
    "extracted_icons/lab_vss_svgs/shape_002_FortiSwitch.svg"
  ],
  "total": 2
}
```

#### SVG to 3D Conversion

```python
# Endpoint: POST /api/icons/svg-to-3d-lab
# Converts SVGs to 3D models using the lab SVGTo3DConverter

curl -X POST http://localhost:8001/api/icons/svg-to-3d-lab \
     -H "Content-Type: application/json" \
     -d '{"input_dir": "extracted_icons/lab_vss_svgs", "output_dir": "lab_3d_models"}'
```

Response:
```json
{
  "generated_models": [
    "lab_3d_models/shape_001_FortiGate.obj",
    "lab_3d_models/shape_002_FortiSwitch.obj"
  ],
  "total": 2
}
```

### Lab Integration Code

The integration uses the actual conversion classes from the 3D Network Topology Lab:

```python
# From vss_to_svg.py - VSSConverter class
class VSSConverter:
    """Converter for VSS (Visio Stencil) files to SVG format"""
    
    def __init__(self, backend: Optional[ConversionBackend] = None):
        self.backend = backend or self._detect_backend()
    
    def convert_vss(
        self, 
        input_path: Path, 
        output_dir: Path, 
        scale: float = 1.0,
        prefix: str = ""
    ) -> List[Path]:
        """Convert a VSS file to SVG format"""
        # Implementation supports multiple backends:
        # - vss_extractor (default, uses olefile)
        # - libvisio2svg (CLI tool)
        # - pywin32 (Windows Visio COM)
        # - aspose (commercial library)
```

```python
# From svg_to_3d.py - SVGTo3DConverter class
class SVGTo3DConverter:
    """Convert SVG files to 3D models for Babylon.js"""
    
    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
    
    def optimize_svg_for_3d(self, svg_path: Path) -> Path:
        """Optimize SVG file for 3D conversion"""
        # Removes unnecessary attributes, standardizes dimensions
    
    def svg_to_obj(self, svg_path: Path) -> Optional[Path]:
        """Convert SVG to OBJ file using lightweight generation"""
        # Creates rectangular prism OBJ models (no Blender required)
```

### 3D Lab Topology Integration

The platform also includes a Babylon.js lab viewer that consumes topology data in the lab's JSON format:

```python
# Endpoint: GET /api/topology/babylon-lab-format
# Returns topology in lab-style {"models", "connections"} format

curl http://localhost:8001/api/topology/babylon-lab-format
```

Response format (matches 3d-network-topology-lab/babylon_topology.json):
```json
{
  "models": [
    {
      "id": "fortigate-01",
      "name": "FortiGate 60F",
      "type": "firewall",
      "model": "FortiGate-60F",
      "position": {"x": 0, "y": 2, "z": 0},
      "status": "online",
      "ip": "192.168.1.1",
      "mac": "90:6C:AC:12:34:56",
      "vendor": "Fortinet"
    }
  ],
  "connections": [
    {
      "from": "fortigate-01",
      "to": "switch-01",
      "status": "active",
      "bandwidth": "1Gbps"
    }
  ]
}
```

Access the 3D lab viewer at: `http://localhost:8001/3d-lab`

## Developer Workflow: Agent-Assisted Coding for Enhanced Network API
=================================================================

To implement and evolve this pipeline inside the `enhanced-network-api-corporate` repository, use the cagent-based workflow script as a low-friction entry point:

Script location:

- `/home/keith/cagent/run-enhanced-network-api.sh`

This script always runs from the project root `/home/keith/enhanced-network-api-corporate` and supports the following subcommands:

- **Agent (default)**  
  Start the Enhanced Network API cagent agent for planning and coding:

  ```bash
  /home/keith/cagent/run-enhanced-network-api.sh
  # or explicitly
  /home/keith/cagent/run-enhanced-network-api.sh agent

  # Optional: pass an initial task description
  /home/keith/cagent/run-enhanced-network-api.sh agent "Implement new DrawIO / FortiOS feature and run deploy_sealed.py"
  ```

- **Build**  
  Install Python dependencies (using `.venv` if present) and perform a light setup:

  ```bash
  /home/keith/cagent/run-enhanced-network-api.sh build
  ```

- **Deploy**  
  Run the sealed deployment (includes drift protection tests):

  ```bash
  /home/keith/cagent/run-enhanced-network-api.sh deploy
  ```

- **Tests**  
  Run only the drift protection test suite (`test_drift_protection.py`):

  ```bash
  /home/keith/cagent/run-enhanced-network-api.sh tests
  ```

Recommended loop when extending the MAC → 3D model → topology pipeline:

1. Use **agent** to plan and implement changes (FastAPI endpoints, FortiOS/Meraki integrations, DrawIO/3D workflows).
2. Run **tests** to ensure topology structure and critical node IDs remain stable.
3. Run **deploy** to apply changes under sealed deployment with drift protection.

Research Agent
--------------

For deeper Fortinet/FortiManager and Meraki API exploration (endpoint discovery, comparison, and integration design), use the dedicated research agent wired to `network_api_agent.yaml`:

```bash
/home/keith/cagent/run-enhanced-network-api.sh research

# Example: start with a concrete research request
/home/keith/cagent/run-enhanced-network-api.sh research \
  "Compare FortiManager and Meraki topology APIs and propose endpoint mappings for this 3D icon pipeline."
```

Use the **research** subcommand when you want API-focused analysis and design, and the **agent** subcommand when you are ready to implement or refactor code in the Enhanced Network API project.

Local GPU Model (vLLM) Configuration
------------------------------------

Both the **agent** and **research** workflows are backed by a local vLLM model tuned for Fortinet/Meraki work.

Model directory:

- `/home/keith/models/codellama-7b_fortinet_meraki_20251107_185952`

Start the vLLM OpenAI-compatible server (uses GPU):

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /home/keith/models/codellama-7b_fortinet_meraki_20251107_185952 \
  --host 0.0.0.0 \
  --port 8000
```

The cagent YAMLs (`enhanced_network_api_agent.yaml` and `network_api_agent.yaml`) are configured with a `network` model entry pointing to this server:

```yaml
network:
  provider: openai
  model: codellama-7b_fortinet_meraki_20251107_185952
  base_url: http://127.0.0.1:8000/v1
  temperature: 0.2
  max_tokens: 4096
```

As long as the vLLM server is running on port `8000`, the **agent** and **research** subcommands will use this GPU-backed model for all Enhanced Network API coding and API research tasks.


Methods to Convert Icons to SVG
1. Vector Tracing with Potrace
bash
# Install potrace and ImageMagick
sudo apt-get install potrace imagemagick

# Convert PNG to bitmap, then trace to SVG
convert -flatten input.png output.pbm
potrace -s output.pbm -o output.svg
rm output.pbm
Advantage: Command-line automation, highly configurable tracing parameters

Best for: Batch processing, server-side conversion

2. Inkscape Command-Line Conversion
bash
# Modern Inkscape syntax
inkscape "device.png" --export-type="svg" --export-filename="device.svg"
Advantage: Superior trace quality, supports various image formats

Best for: High-quality conversions, preserving details

3. Cloud-Based API Services
Cloudinary - Upload PNG, retrieve SVG via transformation URL

javascript
const cloudinary = require('cloudinary').v2;
// Convert to SVG programmatically
cloudinary.image('device-icon.png', { effect: 'vectorize' })
Vector Magic API - Professional-grade tracing algorithm

ConvertAPI - REST API for PNG to SVG conversion

Advantage: No local dependencies, scalable, high-quality results

4. Node.js Libraries
javascript
// Using svg-path-to-polygons for programmatic control
const { pathParse } = require('svg-path-parse');
const sharp = require('sharp');

// Extract paths from existing SVG
const pathData = pathParse(svgPathString).getSegments();
svg-path-parser - Parse and manipulate SVG paths

svg-path-parse - Normalize and transform SVG data

Advantage: Full programmatic control, integrate into build pipeline

5. Extract from Visio Stencils
python
# Visio .vsdx files are ZIP archives containing XML
import zipfile
import xml.etree.ElementTree as ET

# Extract SVG-like data from Visio shapes
with zipfile.ZipFile('cisco-icons.vsdx', 'r') as vsdx:
    # Parse shape XML, extract path data
    shape_xml = vsdx.read('visio/pages/page1.xml')
Advantage: Access vendor-official vector data directly

Best for: Cisco/Fortinet stencils already in Visio format

5 Methods to Convert SVG to 3D for Babylon.js
1. SVG Path Extrusion (ExtrudeShape)
javascript
// Parse SVG path to Babylon.js Path2
const { parseSVG } = require('svg-path-parser');
const svgPath = parseSVG('M10,10 L50,10 L50,50 L10,50 Z');

// Convert to Babylon.js Vector3 points
const points = svgPath.map(cmd => 
  new BABYLON.Vector3(cmd.x, cmd.y, 0)
);

// Extrude the shape
const shape = BABYLON.MeshBuilder.ExtrudeShape("device", {
  shape: points,
  path: [new BABYLON.Vector3(0, 0, 0), new BABYLON.Vector3(0, 0, depth)],
  cap: BABYLON.Mesh.CAP_ALL
}, scene);
Advantage: Full control, lightweight, real-time manipulation

Best for: Simple icons, logos, flat device representations

2. CSG (Constructive Solid Geometry) Operations
javascript
// Create basic 3D primitives from SVG outlines
const profile = BABYLON.MeshBuilder.CreatePolygon("profile", {
  shape: svgPoints,
  depth: 5
}, scene);

// Combine multiple CSG operations for complex shapes
const csg1 = BABYLON.CSG.FromMesh(profile);
const csg2 = BABYLON.CSG.FromMesh(cutout);
const result = csg1.subtract(csg2);
Advantage: Boolean operations, create complex geometries

Best for: Router/switch chassis with ports and details

3. AI-Powered 2D to 3D Generation
Meshy AI - Upload SVG/PNG, get 3D model (GLB/OBJ)

Spline AI - Image to 3D with text prompt guidance

CSM.ai - Single image to voxel-based 3D model

Alpha3D - Generate game-ready 3D assets from 2D images

javascript
// After AI generation, load into Babylon.js
BABYLON.SceneLoader.ImportMesh("", "models/", "device.glb", scene, 
  function (meshes) {
    // Use generated 3D model
  }
);
Advantage: Automatic depth perception, realistic 3D appearance

Best for: Converting flat vendor icons to 3D representations

4. Normal Map/Displacement from SVG
javascript
// Use SVG as albedo texture + generate normal map
const material = new BABYLON.PBRMaterial("deviceMat", scene);

// Convert SVG to texture
const svgBlob = new Blob([svgString], {type: 'image/svg+xml'});
const url = URL.createObjectURL(svgBlob);
material.albedoTexture = new BABYLON.Texture(url, scene);

// Apply to plane with slight extrusion
const plane = BABYLON.MeshBuilder.CreatePlane("icon", {
  width: 2, height: 2
}, scene);
plane.material = material;
Advantage: Lightweight, billboard-style 3D effect

Best for: Large network diagrams with many devices

5. Hybrid SVG + Primitive Composition
javascript
// Combine extruded SVG front face with 3D primitives for depth
const frontFace = extrudeSVGPath(svgData, 0.1); // Thin extrusion
const body = BABYLON.MeshBuilder.CreateBox("body", {
  width: iconWidth,
  height: iconHeight, 
  depth: deviceDepth
}, scene);

// Position front face slightly forward
frontFace.position.z = deviceDepth / 2;

// Parent both to create composite device
frontFace.parent = body;
Advantage: Balance between detail and performance

Best for: Recognizable device icons with 3D depth

Recommended Workflow for Your Application
Given your Fortinet/Meraki API integration background, here's an optimal pipeline:

javascript
// 1. Fetch device data from API
const devices = await fetchDevicesFromAPI(); // Meraki/Fortinet APIs

// 2. Map to icon (MAC OUI or model number)
const iconPath = mapDeviceToIcon(device.model, device.macAddress);

// 3. Convert to SVG if needed (use Potrace CLI or Cloudinary API)
const svgData = await convertToSVG(iconPath);

// 4. Parse SVG path and extrude in Babylon.js
const deviceMesh = createExtrudedDevice(svgData, scene);

// 5. Position in 3D topology based on network hierarchy
positionDeviceInTopology(deviceMesh, device.location);