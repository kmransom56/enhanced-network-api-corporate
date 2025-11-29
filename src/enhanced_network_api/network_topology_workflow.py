#!/usr/bin/env python3
"""
Network Topology Workflow - Unified orchestration for 2D/3D network mapping
This module provides end-to-end workflow for:
1. Collecting device data from FortiGate, FortiSwitch, FortiAP via FortiOS API
2. Identifying devices by MAC address (OUI lookup + device classification)
3. Generating SVG icons for each device type
4. Exporting to Babylon.js 3D visualization format
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import base64
from datetime import datetime

from .fortigate_auth import FortiGateAuth
from .fortigate import FortiGateModule
from .fortiswitch import FortiSwitchModule
from .fortiap import FortiAPModule
from .device_mac_matcher import DeviceModelMatcher, DeviceInfo, OUILookup, DeviceClassifier
from .device_collector import DeviceCollector
from .vss_svg_integration import extract_and_integrate_vss_icons

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

MANUFACTURER_ICON_MAP = {
    # Fortinet devices
    'fortinet': {
        'firewall': 'fortigate_1u.svg',
        'access_point': 'fortiap_indoor.svg',
        'switch': 'fortiswitch_124e.svg',
        'extender': 'fortiextender_appliance.svg',
    },
    
    # Cisco (routers, switches)
    'cisco': {
        'router': 'cisco_router.svg',
        'switch': 'cisco_catalyst.svg',
        'access_point': 'cisco_meraki_ap.svg',
        'firewall': 'cisco_asa.svg',
    },
    
    # Printers & office
    'canon': 'printer_generic.svg',
    'hp': 'printer_generic.svg',
    'xerox': 'printer_generic.svg',
    'brother': 'printer_generic.svg',
    
    # Mobile & endpoints
    'apple': 'smartphone_apple.svg',
    'samsung': 'smartphone_android.svg',
    'lg': 'monitor.svg',
    'dell': 'workstation.svg',
    'lenovo': 'workstation.svg',
    'microsoft': 'workstation.svg',
    
    # Generic fallbacks
    'default_iot': 'device_generic.svg',
    'default_client': 'client_generic.svg',
}


@dataclass
class NetworkDevice:
    """Unified device representation across all network devices"""
    id: str
    name: str
    type: str  # fortigate, fortiswitch, fortiap, client
    ip: Optional[str] = None
    mac: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    status: str = 'online'
    vlan: Optional[str] = None
    port: Optional[str] = None
    
    # Device identification from MAC matcher
    device_type: Optional[str] = None
    confidence: Optional[str] = None
    pos_system: Optional[str] = None
    
    # 3D visualization paths
    icon_svg: Optional[str] = None
    model_3d: Optional[str] = None
    
    # Connection details
    connected_to: Optional[str] = None
    interface: Optional[str] = None
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class NetworkConnection:
    """Represents a connection between two network devices"""
    id: str
    from_device: str
    to_device: str
    from_port: Optional[str] = None
    to_port: Optional[str] = None
    status: str = 'up'
    protocol: Optional[str] = None
    bandwidth: Optional[str] = None
    vlan: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class NetworkTopologyWorkflow:
    """
    Main workflow orchestrator for network topology mapping
    
    Workflow Steps:
    1. Connect to FortiGate and authenticate
    2. Discover FortiSwitch and FortiAP devices
    3. Collect connected clients from all devices
    4. Identify each device by MAC address
    5. Generate/assign SVG icons for each device
    6. Create 3D model mappings
    7. Build topology graph (devices + connections)
    8. Export to visualization formats (Babylon.js, DrawIO)
    """
    
    def __init__(
        self,
        fortigate_host: str,
        fortigate_token: str,
        oui_database_path: Optional[str] = None,
        model_library_path: Optional[str] = None,
        svg_output_dir: str = 'realistic_device_svgs',
        vss_file_path: Optional[str] = None,
        use_vss_icons: bool = True,
        verify_ssl: bool = False,
        ca_cert_path: Optional[str] = None
    ):
        self.fortigate_host = fortigate_host
        self.fortigate_token = fortigate_token
        self.verify_ssl = verify_ssl
        self.ca_cert_path = ca_cert_path
        
        # Initialize FortiOS API authentication
        self.fg_auth = FortiGateAuth(
            host=fortigate_host,
            api_token=fortigate_token,
            verify_ssl=verify_ssl,
            ca_cert=ca_cert_path
        )
        
        # Initialize device modules
        self.fg_module = None
        self.fs_module = None
        self.fa_module = None
        
        # Initialize device identification
        self.device_matcher = DeviceModelMatcher(
            model_library_path=model_library_path,
            oui_database_path=oui_database_path
        )
        
        # Storage for discovered devices and connections
        self.devices: List[NetworkDevice] = []
        self.connections: List[NetworkConnection] = []
        
        # Output configuration
        self.svg_output_dir = Path(svg_output_dir)
        self.svg_output_dir.mkdir(parents=True, exist_ok=True)
        
        # VSS icon extraction configuration
        self.vss_file_path = vss_file_path
        self.use_vss_icons = use_vss_icons and vss_file_path is not None
        
        log.info(f"Initialized NetworkTopologyWorkflow for {fortigate_host}")
        if self.use_vss_icons:
            log.info(f"VSS icon extraction enabled: {vss_file_path}")
    
    async def execute_workflow(self) -> Dict[str, Any]:
        """
        Execute the complete workflow from data collection to visualization
        
        Returns:
            Dict containing devices, connections, and export paths
        """
        log.info("=== Starting Network Topology Workflow ===")
        
        try:
            # Step 1: Authenticate and initialize modules
            await self.step1_authenticate()
            
            # Step 2: Discover infrastructure devices
            await self.step2_discover_infrastructure()
            
            # Step 3: Collect connected clients
            await self.step3_collect_clients()
            
            # Step 4: Identify all devices by MAC
            await self.step4_identify_devices()
            
            # Step 5: Generate SVG icons
            await self.step5_generate_svg_icons()
            
            # Step 6: Build topology connections
            await self.step6_build_connections()
            
            # Step 7: Export to visualization formats
            result = await self.step7_export_visualizations()
            
            log.info("=== Workflow Completed Successfully ===")
            return result
            
        except Exception as e:
            log.error(f"Workflow failed: {e}", exc_info=True)
            raise
    
    async def step1_authenticate(self):
        """Step 1: Authenticate to FortiGate and initialize API modules"""
        log.info("Step 1: Authenticating to FortiGate...")
        
        # Create session
        if not self.fg_auth.login():
            raise Exception("Failed to authenticate to FortiGate")
        
        # Initialize device modules
        self.fg_module = FortiGateModule(self.fg_auth.session)
        # FortiSwitch and FortiAP modules would be initialized similarly
        # self.fs_module = FortiSwitchModule(self.fg_auth.session)
        # self.fa_module = FortiAPModule(self.fg_auth.session)
        
        log.info("✓ Authentication successful")
    
    async def step2_discover_infrastructure(self):
        """Step 2: Discover FortiGate, FortiSwitch, and FortiAP devices"""
        log.info("Step 2: Discovering infrastructure devices...")
        
        # Add FortiGate itself
        fortigate_device = NetworkDevice(
            id='fortigate-primary',
            name=self.fortigate_host,
            type='fortigate',
            ip=self.fortigate_host,
            status='online',
            vendor='Fortinet',
            model='FortiGate'
        )
        self.devices.append(fortigate_device)
        log.info(f"Added FortiGate: {fortigate_device.name}")
        
        # Discover FortiSwitch devices
        try:
            switches = self.fg_module.get_fortiswitches()
            if switches and 'results' in switches:
                for switch in switches['results']:
                    switch_device = NetworkDevice(
                        id=f"fortiswitch-{switch.get('serial', 'unknown')}",
                        name=switch.get('name', 'FortiSwitch'),
                        type='fortiswitch',
                        ip=switch.get('ip', None),
                        mac=switch.get('mac', None),
                        vendor='Fortinet',
                        model=switch.get('model', 'FortiSwitch'),
                        status=switch.get('status', 'unknown'),
                        connected_to='fortigate-primary'
                    )
                    self.devices.append(switch_device)
                    log.info(f"Added FortiSwitch: {switch_device.name}")
        except Exception as e:
            log.warning(f"Failed to discover FortiSwitch devices: {e}")
        
        # Discover FortiAP devices
        try:
            aps = self.fg_module.get_fortiaps()
            if aps and 'results' in aps:
                for ap in aps['results']:
                    ap_device = NetworkDevice(
                        id=f"fortiap-{ap.get('serial', 'unknown')}",
                        name=ap.get('name', 'FortiAP'),
                        type='fortiap',
                        ip=ap.get('ip', None),
                        mac=ap.get('mac', None),
                        vendor='Fortinet',
                        model=ap.get('model', 'FortiAP'),
                        status=ap.get('status', 'unknown'),
                        connected_to='fortigate-primary'
                    )
                    self.devices.append(ap_device)
                    log.info(f"Added FortiAP: {ap_device.name}")
        except Exception as e:
            log.warning(f"Failed to discover FortiAP devices: {e}")
        
        log.info(f"✓ Discovered {len(self.devices)} infrastructure devices")
    
    async def step3_collect_clients(self):
        """Step 3: Collect all connected client devices"""
        log.info("Step 3: Collecting connected clients...")
        
        client_count = 0
        
        # Get WiFi clients from FortiAPs
        try:
            clients = self.fg_module.get_connected_clients()
            if clients and 'results' in clients:
                for client in clients['results']:
                    client_device = NetworkDevice(
                        id=f"client-{client.get('mac', 'unknown').replace(':', '-')}",
                        name=client.get('hostname', client.get('mac', 'Unknown Client')),
                        type='client',
                        ip=client.get('ip', None),
                        mac=client.get('mac', None),
                        vlan=client.get('vlan', None),
                        status='online',
                        connected_to=client.get('ap', 'fortigate-primary'),
                        interface=client.get('ssid', None)
                    )
                    self.devices.append(client_device)
                    client_count += 1
        except Exception as e:
            log.warning(f"Failed to collect WiFi clients: {e}")
        
        # TODO: Get wired clients from FortiSwitch devices
        # This would involve querying each FortiSwitch for connected devices
        
        log.info(f"✓ Collected {client_count} connected clients")
    
    async def step4_identify_devices(self):
        """Step 4: Identify all devices by MAC address and assign types"""
        log.info("Step 4: Identifying devices by MAC address...")
        
        identified_count = 0
        
        for device in self.devices:
            if not device.mac:
                log.debug(f"Device {device.name} has no MAC address, skipping identification")
                continue
            
            # Use device_mac_matcher to identify device
            context = {
                'hostname': device.name,
                'ip': device.ip,
                'type': device.type
            }
            
            device_info: DeviceInfo = self.device_matcher.match_mac_to_model(
                device.mac,
                additional_context=context
            )
            
            # Update device with identification results
            if not device.vendor:
                device.vendor = device_info.vendor
            
            device.device_type = device_info.device_type
            device.confidence = device_info.confidence
            device.pos_system = device_info.pos_system
            device.model_3d = device_info.model_path
            
            # Store additional metadata
            device.metadata = device_info.details
            
            identified_count += 1
            log.debug(f"Identified {device.name}: {device.device_type} ({device.confidence} confidence)")
        
        log.info(f"✓ Identified {identified_count} devices")
    
    async def step5_generate_svg_icons(self):
        """Step 5: Generate or assign SVG icons for each device (with VSS support)"""
        log.info("Step 5: Generating SVG icons...")
        
        # If VSS file provided, extract icons first
        if self.use_vss_icons:
            log.info("Extracting icons from VSS file...")
            try:
                device_dicts = [d.to_dict() for d in self.devices]
                updated_devices, vss_info = extract_and_integrate_vss_icons(
                    vss_path=self.vss_file_path,
                    device_list=device_dicts,
                    output_dir=str(self.svg_output_dir)
                )
                
                # Update device objects with VSS icons
                for i, device_dict in enumerate(updated_devices):
                    if i < len(self.devices):
                        self.devices[i].icon_svg = device_dict.get('icon_svg')
                        if 'icon_source' in device_dict:
                            if not self.devices[i].metadata:
                                self.devices[i].metadata = {}
                            self.devices[i].metadata['icon_source'] = device_dict['icon_source']
                
                log.info(f"✓ VSS extraction complete: {vss_info.get('icon_count', 0)} icons")
            except Exception as e:
                log.warning(f"VSS extraction failed, falling back to generated icons: {e}")
                self.use_vss_icons = False
        
        # Generate/assign icons for devices without VSS icons
        svg_count = 0
        for device in self.devices:
            if not device.icon_svg:
                # Generate SVG path based on device type
                svg_filename = self._generate_svg_filename(device)
                svg_path = self.svg_output_dir / svg_filename
                
                # Check if SVG already exists, if not create it
                if not svg_path.exists():
                    svg_content = self._create_device_svg(device)
                    svg_path.write_text(svg_content, encoding='utf-8')
                    log.debug(f"Created SVG: {svg_path}")
                
                # Assign SVG path to device
                device.icon_svg = f"/realistic_device_svgs/{svg_filename}"
            
            svg_count += 1
        
        log.info(f"✓ Generated/assigned {svg_count} SVG icons")
    
    def _generate_svg_filename(self, device: NetworkDevice) -> str:
        """Generate standardized SVG filename for device using manufacturer map"""
        return self._get_device_icon_name(device)

    def _get_device_icon_name(self, device: NetworkDevice) -> str:
        """Map device to appropriate icon filename"""
        vendor = (device.vendor or 'generic').lower()
        device_type = (device.device_type or device.type or 'generic').lower()
        
        # Check manufacturer map
        if vendor in MANUFACTURER_ICON_MAP:
            vendor_map = MANUFACTURER_ICON_MAP[vendor]
            if isinstance(vendor_map, dict):
                # Try exact match
                if device_type in vendor_map:
                    return vendor_map[device_type]
                # Try partial match
                for key, icon in vendor_map.items():
                    if key in device_type:
                        return icon
            elif isinstance(vendor_map, str):
                return vendor_map
        
        # Fallback based on device type
        if 'firewall' in device_type or 'gateway' in device_type:
            return 'firewall_generic.svg'
        elif 'switch' in device_type:
            return 'switch_generic.svg'
        elif 'access_point' in device_type or 'ap' in device_type:
            return 'access_point_generic.svg'
        elif 'printer' in device_type:
            return 'printer_generic.svg'
        elif 'phone' in device_type:
            return 'phone_generic.svg'
        elif 'camera' in device_type:
            return 'camera_generic.svg'
        elif 'smartphone' in device_type or 'mobile' in device_type:
            return 'smartphone_generic.svg'
        elif 'workstation' in device_type or 'laptop' in device_type:
            return 'workstation_generic.svg'
            
        return 'device_unknown.svg'
    
    def _create_device_svg(self, device: NetworkDevice) -> str:
        """Create SVG icon for device based on its type"""
        # Map device types to icon styles
        icon_config = self._get_icon_config(device)
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
    <title>{device.name}</title>
    <desc>Device: {device.device_type or device.type} - Vendor: {device.vendor or 'Unknown'}</desc>
    
    <!-- Background -->
    <rect x="4" y="4" width="120" height="120" rx="8" 
          fill="{icon_config['bg_color']}" 
          stroke="{icon_config['border_color']}" stroke-width="2"/>
    
    <!-- Icon shape -->
    {icon_config['shape_svg']}
    
    <!-- Status indicator -->
    <circle cx="110" cy="18" r="8" 
            fill="{icon_config['status_color']}" 
            stroke="white" stroke-width="2"/>
    
    <!-- Device label -->
    <text x="64" y="115" text-anchor="middle" 
          font-family="Arial, sans-serif" font-size="10" fill="white">
        {device.type.upper()}
    </text>
</svg>'''
        
        return svg_content
    
    def _get_icon_config(self, device: NetworkDevice) -> Dict[str, str]:
        """Get icon configuration based on device type"""
        device_type = (device.device_type or device.type or 'generic').lower()
        
        # Status color
        status_color = '#00ff00' if device.status == 'online' else '#ff0000'
        
        # Default config
        bg_color = '#6c757d'
        border_color = '#5a6268'
        shape_svg = '''
            <rect x="25" y="40" width="78" height="48" rx="4" fill="#404040"/>
            <rect x="30" y="45" width="68" height="35" fill="#c0c0c0"/>
        '''

        if 'fortigate' in device_type or 'firewall' in device_type:
            bg_color = '#dc3545'
            border_color = '#c82333'
            shape_svg = '''
                <rect x="20" y="40" width="88" height="48" rx="4" fill="#8b0000"/>
                <rect x="25" y="45" width="78" height="8" fill="#ff6b6b"/>
                <rect x="25" y="58" width="78" height="8" fill="#ff6b6b"/>
                <rect x="25" y="71" width="78" height="8" fill="#ff6b6b"/>
            '''
        elif 'fortiswitch' in device_type or 'switch' in device_type:
            bg_color = '#28a745'
            border_color = '#218838'
            shape_svg = '''
                <rect x="15" y="45" width="98" height="38" rx="4" fill="#006400"/>
                <circle cx="25" cy="64" r="4" fill="#00ff00"/>
                <circle cx="40" cy="64" r="4" fill="#00ff00"/>
                <circle cx="55" cy="64" r="4" fill="#00ff00"/>
                <circle cx="70" cy="64" r="4" fill="#00ff00"/>
                <circle cx="85" cy="64" r="4" fill="#00ff00"/>
                <circle cx="100" cy="64" r="4" fill="#00ff00"/>
            '''
        elif 'fortiap' in device_type or 'access_point' in device_type or 'wifi' in device_type:
            bg_color = '#ffc107'
            border_color = '#e0a800'
            shape_svg = '''
                <circle cx="64" cy="64" r="30" fill="#cc8800"/>
                <path d="M 64 44 Q 44 44 34 54" stroke="#fff" stroke-width="4" fill="none"/>
                <path d="M 64 44 Q 84 44 94 54" stroke="#fff" stroke-width="4" fill="none"/>
                <path d="M 64 54 Q 49 54 42 61" stroke="#fff" stroke-width="3" fill="none"/>
                <path d="M 64 54 Q 79 54 86 61" stroke="#fff" stroke-width="3" fill="none"/>
            '''
        elif 'printer' in device_type:
            bg_color = '#17a2b8'
            border_color = '#138496'
            shape_svg = '''
                <rect x="34" y="40" width="60" height="40" fill="#e0e0e0"/>
                <rect x="44" y="30" width="40" height="10" fill="#fff"/>
                <rect x="44" y="80" width="40" height="15" fill="#fff" stroke="#999"/>
                <line x1="49" y1="85" x2="79" y2="85" stroke="#000" stroke-width="1"/>
                <line x1="49" y1="90" x2="79" y2="90" stroke="#000" stroke-width="1"/>
            '''
        elif 'smartphone' in device_type or 'mobile' in device_type:
            bg_color = '#6610f2'
            border_color = '#520dc2'
            shape_svg = '''
                <rect x="44" y="24" width="40" height="80" rx="4" fill="#333"/>
                <rect x="46" y="30" width="36" height="60" fill="#000"/>
                <circle cx="64" cy="98" r="3" fill="#555"/>
            '''
        elif 'workstation' in device_type or 'laptop' in device_type:
            bg_color = '#007bff'
            border_color = '#0062cc'
            shape_svg = '''
                <rect x="24" y="30" width="80" height="50" rx="2" fill="#333"/>
                <rect x="28" y="34" width="72" height="42" fill="#000"/>
                <polygon points="24,80 104,80 114,95 14,95" fill="#555"/>
            '''

        return {
            'bg_color': bg_color,
            'border_color': border_color,
            'status_color': status_color,
            'shape_svg': shape_svg
        }
    
    async def step6_build_connections(self):
        """Step 6: Build network topology connections"""
        log.info("Step 6: Building network connections...")
        
        connection_count = 0
        
        for device in self.devices:
            if device.connected_to:
                connection = NetworkConnection(
                    id=f"conn-{device.id}",
                    from_device=device.connected_to,
                    to_device=device.id,
                    from_port=None,  # Could be enhanced with actual port information
                    to_port=device.port,
                    status='up' if device.status == 'online' else 'down',
                    vlan=device.vlan
                )
                self.connections.append(connection)
                connection_count += 1
        
        log.info(f"✓ Built {connection_count} connections")
    
    async def step7_export_visualizations(self) -> Dict[str, Any]:
        """Step 7: Export to visualization formats"""
        log.info("Step 7: Exporting to visualization formats...")
        
        # Create Babylon.js format
        babylon_data = self._export_babylon_format()
        
        # Create DrawIO format  
        drawio_data = self._export_drawio_format()
        
        # Save to files
        output_dir = Path('output/topology')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        babylon_path = output_dir / f'babylon_topology_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        drawio_path = output_dir / f'drawio_topology_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        babylon_path.write_text(json.dumps(babylon_data, indent=2), encoding='utf-8')
        drawio_path.write_text(json.dumps(drawio_data, indent=2), encoding='utf-8')
        
        log.info(f"✓ Exported Babylon.js format: {babylon_path}")
        log.info(f"✓ Exported DrawIO format: {drawio_path}")
        
        return {
            'devices': [d.to_dict() for d in self.devices],
            'connections': [c.to_dict() for c in self.connections],
            'export_paths': {
                'babylon': str(babylon_path),
                'drawio': str(drawio_path)
            },
            'summary': {
                'total_devices': len(self.devices),
                'total_connections': len(self.connections),
                'device_types': self._count_device_types()
            }
        }
    
    def _export_babylon_format(self) -> Dict[str, Any]:
        """Export topology in Babylon.js 3D viewer format"""
        models = []
        
        for i, device in enumerate(self.devices):
            # Calculate position in 3D space
            position = self._calculate_device_position(device, i)
            
            model = {
                'id': device.id,
                'name': device.name,
                'type': device.type,
                'vendor': device.vendor,
                'model': device.model or device.type,
                'icon_svg': device.icon_svg,
                'ip': device.ip,
                'mac': device.mac,
                'vlan': device.vlan,
                'status': device.status,
                'position': position
            }
            models.append(model)
        
        connections = []
        for conn in self.connections:
            connections.append({
                'id': conn.id,
                'from': conn.from_device,
                'to': conn.to_device,
                'status': conn.status,
                'protocol': conn.protocol,
                'bandwidth': conn.bandwidth,
                'vlan': conn.vlan
            })
        
        return {
            'models': models,
            'connections': connections,
            'metadata': {
                'generated': datetime.now().isoformat(),
                'total_devices': len(models),
                'total_connections': len(connections)
            }
        }
    
    def _export_drawio_format(self) -> Dict[str, Any]:
        """Export topology in DrawIO format"""
        nodes = []
        edges = []
        
        for i, device in enumerate(self.devices):
            node = {
                'id': device.id,
                'label': device.name,
                'type': device.type,
                'vendor': device.vendor,
                'ip': device.ip,
                'mac': device.mac,
                'icon': device.icon_svg,
                'x': i * 150,  # Simple horizontal layout
                'y': 100 if device.type == 'fortigate' else 300,
                'width': 120,
                'height': 80
            }
            nodes.append(node)
        
        for conn in self.connections:
            edge = {
                'id': conn.id,
                'source': conn.from_device,
                'target': conn.to_device,
                'label': conn.vlan or '',
                'style': 'solid' if conn.status == 'up' else 'dashed'
            }
            edges.append(edge)
        
        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'generated': datetime.now().isoformat()
            }
        }
    
    def _calculate_device_position(self, device: NetworkDevice, index: int) -> Dict[str, float]:
        """Calculate 3D position for device in Babylon.js scene"""
        # Simple grid layout - can be enhanced with force-directed or hierarchical layout
        devices_per_row = 5
        spacing = 5.0
        
        row = index // devices_per_row
        col = index % devices_per_row
        
        # Core infrastructure in center
        if device.type == 'fortigate':
            return {'x': 0, 'y': 0, 'z': 0}
        elif device.type == 'fortiswitch':
            return {'x': col * spacing - 10, 'y': 0, 'z': -5}
        elif device.type == 'fortiap':
            return {'x': col * spacing - 10, 'y': 0, 'z': 5}
        else:  # clients
            return {
                'x': col * spacing - 10,
                'y': 0,
                'z': row * spacing - 10
            }
    
    def _count_device_types(self) -> Dict[str, int]:
        """Count devices by type"""
        counts = {}
        for device in self.devices:
            device_type = device.device_type or device.type
            counts[device_type] = counts.get(device_type, 0) + 1
        return counts


# CLI usage example
async def main():
    """Example usage of the workflow"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Configuration from environment
    fortigate_host = os.getenv('FORTIGATE_HOST', '192.168.1.99')
    fortigate_token = os.getenv('FORTIGATE_TOKEN', 'your-api-token')
    ca_cert_path = os.getenv('CA_CERT_PATH')
    
    # Initialize workflow
    workflow = NetworkTopologyWorkflow(
        fortigate_host=fortigate_host,
        fortigate_token=fortigate_token,
        verify_ssl=False,
        ca_cert_path=ca_cert_path
    )
    
    # Execute complete workflow
    result = await workflow.execute_workflow()
    
    # Print summary
    print("\n=== Workflow Results ===")
    print(f"Total Devices: {result['summary']['total_devices']}")
    print(f"Total Connections: {result['summary']['total_connections']}")
    print("\nDevice Types:")
    for device_type, count in result['summary']['device_types'].items():
        print(f"  {device_type}: {count}")
    print(f"\nExport Paths:")
    print(f"  Babylon.js: {result['export_paths']['babylon']}")
    print(f"  DrawIO: {result['export_paths']['drawio']}")


if __name__ == '__main__':
    asyncio.run(main())
