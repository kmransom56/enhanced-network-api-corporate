#!/usr/bin/env python3
"""
MAC Address to Device Type Matching
Implements OUI lookup and device classification for Enhanced Network API
"""

import json
import re
import csv
import requests
import os
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
import logging

log = logging.getLogger(__name__)

@dataclass
class DeviceInfo:
    mac_address: str
    vendor: str
    device_type: str
    confidence: str
    model_path: Optional[str] = None
    pos_system: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class OUILookup:
    """Enhanced OUI database with macaddress.io API integration"""
    
    def __init__(self, oui_csv_path: Optional[str] = None):
        self.oui_dict: Dict[str, Dict[str, str]] = {}
        self.macaddress_io_api_key = os.getenv('MACADDRESS_IO_API_KEY')
        self.macaddress_io_base_url = os.getenv('MACADDRESS_IO_BASE_URL', 'https://api.macaddress.io/v1')
        
        if oui_csv_path and Path(oui_csv_path).exists():
            self.load_oui_csv(oui_csv_path)
        else:
            log.warning("OUI database not found, using built-in vendor mappings")
            self._load_builtin_ouis()
    
    def lookup(self, mac_address: str) -> Dict[str, str]:
        """Lookup vendor information for a MAC address with macaddress.io API fallback"""
        # Normalize MAC address
        mac_clean = mac_address.replace(':', '').replace('-', '').replace('.', '').upper()
        
        # Extract OUI (first 6 hex digits)
        if len(mac_clean) < 6:
            return {'vendor': 'Invalid MAC', 'address': ''}
        
        oui = ':'.join([mac_clean[i:i+2] for i in range(0, 6, 2)])
        
        # First try local database
        local_result = self.oui_dict.get(oui)
        if local_result:
            return local_result
        
        # If not found locally and API key is available, use macaddress.io
        if self.macaddress_io_api_key:
            return self._lookup_macaddress_io(mac_address)
        
        # Return unknown if no API key
        return {'vendor': 'Unknown', 'address': ''}
    
    def _lookup_macaddress_io(self, mac_address: str) -> Dict[str, str]:
        """Lookup MAC address using macaddress.io API as described in iconlab.md"""
        try:
            url = f"{self.macaddress_io_base_url}"
            params = {
                'apiKey': self.macaddress_io_api_key,
                'output': 'json',
                'search': mac_address
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse macaddress.io response
            vendor_details = data.get('vendorDetails', {})
            
            return {
                'vendor': vendor_details.get('companyName', 'Unknown'),
                'address': vendor_details.get('companyAddress', ''),
                'country': vendor_details.get('countryCode', ''),
                'is_private': vendor_details.get('isPrivate', False),
                'is_random': vendor_details.get('isRandom', False),
                'type': vendor_details.get('type', 'Unknown'),
                'block': vendor_details.get('block', ''),
                'block_details': vendor_details.get('blockDetails', {})
            }
            
        except Exception as e:
            log.error(f"macaddress.io API lookup failed for {mac_address}: {e}")
            return {'vendor': 'Unknown', 'address': ''}
    
    def lookup_detailed(self, mac_address: str) -> Dict[str, Any]:
        """Get detailed MAC address information using macaddress.io API"""
        if not self.macaddress_io_api_key:
            log.warning("No MACADDRESS_IO_API_KEY configured, using basic lookup")
            return self.lookup(mac_address)
        
        return self._lookup_macaddress_io(mac_address)
    
    def _load_builtin_ouis(self):
        """Load common vendor OUIs for network and restaurant equipment"""
        builtin_ouis = {
            # Restaurant Technology OUIs
            "00:0C:F1": {"vendor": "Ingenico", "address": "Paris, France"},
            "00:1D:6A": {"vendor": "Ingenico (Clover)", "address": "Paris, France"},
            "AC:BC:32": {"vendor": "Square (Block)", "address": "San Francisco, CA"},
            "44:38:39": {"vendor": "Square", "address": "San Francisco, CA"},
            "68:DB:CA": {"vendor": "Square", "address": "San Francisco, CA"},
            "B8:27:EB": {"vendor": "Raspberry Pi Foundation", "address": "Cambridge, UK"},
            "DC:A6:32": {"vendor": "Raspberry Pi Trading", "address": "Cambridge, UK"},
            "00:0D:93": {"vendor": "NCR Corporation", "address": "Atlanta, GA"},
            "00:40:AA": {"vendor": "NCR Corporation", "address": "Atlanta, GA"},
            "08:94:7C": {"vendor": "NCR Corporation", "address": "Atlanta, GA"},
            "00:0C:29": {"vendor": "VMware", "address": "Palo Alto, CA"},
            "00:50:56": {"vendor": "VMware", "address": "Palo Alto, CA"},
            "28:CF:E9": {"vendor": "Apple", "address": "Cupertino, CA"},
            "40:A6:D9": {"vendor": "Apple", "address": "Cupertino, CA"},
            "A4:C1:2D": {"vendor": "Google", "address": "Mountain View, CA"},
            # Network Equipment
            "F0:9F:C2": {"vendor": "Cisco Meraki", "address": "San Francisco, CA"},
            "90:6C:AC": {"vendor": "Fortinet", "address": "Sunnyvale, CA"},
            "40:4D:55": {"vendor": "Clover Mini", "address": "Paris, France"},
            "68:72:51": {"vendor": "Clover Flex", "address": "Paris, France"},
            "E8:9F:6D": {"vendor": "Toast", "address": "Boston, MA"},
            "34:98:B5": {"vendor": "Toast", "address": "Boston, MA"},
            "18:B4:30": {"vendor": "Square", "address": "San Francisco, CA"},
        }
        self.oui_dict = {k.upper(): v for k, v in builtin_ouis.items()}
    
    def load_oui_csv(self, csv_path: str):
        """Load OUI database from IEEE CSV file"""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'Assignment' in row and 'Organization Name' in row:
                        oui = row['Assignment'].replace('-', ':').upper()
                        vendor = row['Organization Name'].strip()
                        address = row.get('Organization Address', '').strip()
                        self.oui_dict[oui] = {
                            'vendor': vendor,
                            'address': address
                        }
            log.info(f"Loaded {len(self.oui_dict)} OUI entries")
        except Exception as e:
            log.error(f"Failed to load OUI database: {e}")
            self._load_builtin_ouis()

class DeviceClassifier:
    """Classify devices based on vendor and context"""
    
    def __init__(self):
        self.device_classifications = {
            'cisco meraki': {
                'mr': 'Wireless Access Point',
                'ms': 'Switch',
                'mx': 'Security Appliance/Firewall',
                'mv': 'Security Camera',
                'mt': 'IoT Sensor',
                'mg': 'Cellular Gateway'
            },
            'fortinet': {
                'fortigate': 'Firewall/UTM',
                'fortiap': 'Wireless Access Point',
                'fortiswitch': 'Switch',
                'fortianalyzer': 'Log Management',
                'fortimanager': 'Management Platform'
            },
            'apple': {
                'ipad': 'Tablet',
                'iphone': 'Smartphone',
                'macbook': 'Laptop',
                'apple tv': 'Media Device'
            },
            'vmware': {
                'esx': 'Virtualization Host',
                'vm': 'Virtual Machine'
            }
        }
        
        # Restaurant technology vendor OUIs - PRIMARY FOCUS
        self.restaurant_tech_ouis = {
            'Clover (Ingenico)': ['00:0C:F1', '00:1D:6A'],
            'Square (Block Inc)': ['AC:BC:32', 'C4:AD:34', '18:B4:30'],
            'Toast': ['B8:27:EB', 'DC:A6:32'],  # Raspberry Pi-based
            'NCR Aloha': ['00:0D:93', '00:40:AA', '08:94:7C'],
            'Micros (Oracle)': ['00:0C:29', '00:50:56'],
            'Revel Systems': ['iPad-based'],  # Uses Apple MACs
            'Lightspeed': ['Varies'],
            'ShopKeep': ['iPad-based'],
            'Vend': ['Varies'],
            'Loyverse': ['Android/iOS'],
            'TouchBistro': ['iPad-based'],
            'Upserve': ['iPad-based'],
            'Toast 2.0': ['E8:9F:6D', '34:98:B5'],
            'Square Terminal': ['44:38:39', '68:DB:CA'],
            'Clover Mini': ['40:4D:55'],
            'Clover Flex': ['68:72:51']
        }
        
        # Restaurant device type classifications
        self.restaurant_device_types = {
            'pos_register': {
                'keywords': ['register', 'pos', 'terminal', 'cash'],
                'ouis': ['00:0C:F1', '00:1D:6A', 'AC:BC:32', '44:38:39', '68:DB:CA', '40:4D:55'],
                'model': '/static/3d-models/pos_register.obj'
            },
            'pos_tablet': {
                'keywords': ['tablet', 'ipad', 'order', 'mobile'],
                'ouis': ['28:CF:E9', '40:A6:D9', 'A4:C1:2D'],  # Apple OUIs
                'model': '/static/3d-models/pos_tablet.obj'
            },
            'kitchen_display': {
                'keywords': ['kitchen', 'kds', 'display', 'monitor'],
                'ouis': ['B8:27:EB', 'DC:A6:32'],  # Raspberry Pi
                'model': '/static/3d-models/kitchen_display.obj'
            },
            'digital_menu': {
                'keywords': ['menu', 'display', 'digital', 'board'],
                'ouis': ['B8:27:EB', '00:0D:93'],  # Raspberry Pi, NCR
                'model': '/static/3d-models/digital_menu.obj'
            },
            'kitchen_printer': {
                'keywords': ['printer', 'kitchen', 'receipt'],
                'ouis': ['00:0D:93', '00:40:AA'],  # NCR, Epson
                'model': '/static/3d-models/kitchen_printer.obj'
            },
            'payment_terminal': {
                'keywords': ['payment', 'credit', 'terminal'],
                'ouis': ['00:0C:F1', '68:72:51'],  # Ingenico/Clover
                'model': '/static/3d-models/payment_terminal.obj'
            }
        }
    
    def classify_device(self, mac: str, vendor: str, context: Optional[Dict] = None) -> str:
        """Classify device type based on MAC, vendor, and optional context - FOCUSED ON RESTAURANT TECH"""
        vendor_lower = vendor.lower()
        
        # PRIORITY 1: Restaurant device classification
        device_type = self._classify_restaurant_device(mac, vendor, context)
        if device_type != 'Unknown Restaurant Device':
            return device_type
        
        # PRIORITY 2: Check for specific device patterns (fallback for network equipment)
        for vendor_key, devices in self.device_classifications.items():
            if vendor_key in vendor_lower:
                # If additional context available (hostname, etc.)
                if context and 'hostname' in context:
                    hostname = context['hostname']
                    for device_prefix, device_type in devices.items():
                        if device_prefix.lower() in hostname.lower():
                            return device_type
                
                # Default classification based on vendor
                return f"{vendor} Device"
        
        # Generic classification based on OUI patterns
        if self._detect_random_mac(mac):
            return 'Mobile Device (Randomized MAC)'
        
        return 'Unknown Device'
    
    def _classify_restaurant_device(self, mac: str, vendor: str, context: Optional[Dict] = None) -> str:
        """Classify restaurant technology devices specifically"""
        vendor_lower = vendor.lower()
        hostname = context.get('hostname', '').lower() if context else ''
        
        # Check each restaurant device type
        for device_type, config in self.restaurant_device_types.items():
            # Check if MAC matches known OUIs for this device type
            mac_prefix = mac.upper()[:8]  # First 4 hex pairs
            for oui in config['ouis']:
                if mac.upper().startswith(oui):
                    # Verify with hostname keywords if available
                    if hostname:
                        if any(keyword in hostname for keyword in config['keywords']):
                            return self._format_device_type(device_type)
                    else:
                        return self._format_device_type(device_type)
            
            # Check hostname keywords even if MAC doesn't match (for iPads, etc.)
            if hostname and any(keyword in hostname for keyword in config['keywords']):
                return self._format_device_type(device_type)
        
        # Special POS system detection
        pos_system = self.identify_pos_device(mac, OUILookup(), context)
        if pos_system:
            return 'POS Terminal'
        
        return 'Unknown Restaurant Device'
    
    def _format_device_type(self, device_type: str) -> str:
        """Format device type for display"""
        type_map = {
            'pos_register': 'POS Register/Cash Terminal',
            'pos_tablet': 'POS Tablet/Tabletop Ordering',
            'kitchen_display': 'Kitchen Display Unit (KDS)',
            'digital_menu': 'Digital Menu Board',
            'kitchen_printer': 'Kitchen/Receipt Printer',
            'payment_terminal': 'Payment Terminal'
        }
        return type_map.get(device_type, device_type.replace('_', ' ').title())
    
    def identify_pos_device(self, mac: str, oui_lookup: OUILookup, context: Optional[Dict] = None) -> Optional[str]:
        """Identify POS system from MAC address"""
        vendor_info = oui_lookup.lookup(mac)
        vendor = vendor_info['vendor']
        
        # Check against known POS vendors
        for pos_system, oui_list in self.restaurant_tech_ouis.items():
            if oui_list == ['iPad-based']:
                if 'apple' in vendor.lower():
                    return pos_system
            elif oui_list == ['Varies']:
                # Heuristic detection for systems that use various hardware
                if any(keyword in vendor.lower() for keyword in ['android', 'tablet', 'pos']):
                    return pos_system
            else:
                if any(mac.upper().startswith(oui) for oui in oui_list):
                    return pos_system
        
        # Heuristic detection
        if 'apple' in vendor.lower():
            return 'iPad-based POS (Square/Toast/Revel)'
        
        if 'raspberry' in vendor.lower():
            return 'Embedded POS System'
        
        return None
    
    def _detect_random_mac(self, mac: str) -> str:
        """Detect if MAC uses privacy randomization"""
        mac_clean = mac.replace(':', '').replace('-', '')
        if len(mac_clean) < 2:
            return 'static_mac'
        second_char = mac_clean[1].upper()
        
        # Locally administered bit check
        if second_char in ['2', '6', 'A', 'E']:
            return 'random_mac'
        return 'static_mac'

class DeviceModelMatcher:
    """Match devices to 3D models based on MAC and classification - Following iconlab.md architecture"""
    
    def __init__(self, model_library_path: Optional[str] = None, oui_database_path: Optional[str] = None):
        self.oui_dict = self.load_oui_database(oui_database_path)
        self.model_library = self.load_model_library(model_library_path)
        self.oui_lookup = OUILookup(oui_database_path)
        self.classifier = DeviceClassifier()
    
    def load_oui_database(self, path: Optional[str]) -> Dict[str, Dict[str, str]]:
        """Load pre-built OUI lookup as described in iconlab.md"""
        if path and Path(path).exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                log.error(f"Failed to load OUI database from {path}: {e}")
        
        # Return empty dict if no file, will use API lookup
        return {}
    
    def load_model_library(self, path: Optional[str]) -> Dict[str, str]:
        """
        Load mapping of vendor/device to 3D model file
        Format from iconlab.md:
        {
            "Cisco Meraki MR46": "models/meraki_mr46.obj",
            "Fortinet FortiGate 60F": "models/fortigate_60f.obj",
            "Square POS Terminal": "models/square_terminal.obj"
        }
        """
        # Restaurant Technology Devices (Primary Focus) - following iconlab.md format
        default_models = {
            # Restaurant POS Systems
            "Ingenico POS Terminal": "/static/3d-models/pos_register.obj",
            "Square POS Terminal": "/static/3d-models/square_terminal.obj",
            "Toast POS Terminal": "/static/3d-models/toast_pos.obj",
            "NCR POS Terminal": "/static/3d-models/ncr_pos.obj",
            "Micros POS Terminal": "/static/3d-models/micros_pos.obj",
            "Clover POS Terminal": "/static/3d-models/clover_pos.obj",
            
            # Restaurant Device Types
            "POS Register/Cash Terminal": "/static/3d-models/pos_register.obj",
            "POS Tablet/Tabletop Ordering": "/static/3d-models/pos_tablet.obj",
            "Kitchen Display Unit (KDS)": "/static/3d-models/kitchen_display.obj",
            "Digital Menu Board": "/static/3d-models/digital_menu.obj",
            "Kitchen/Receipt Printer": "/static/3d-models/kitchen_printer.obj",
            "Payment Terminal": "/static/3d-models/payment_terminal.obj",
            
            # Generic restaurant devices
            "Apple iPad": "/static/3d-models/pos_tablet.obj",
            "Raspberry Pi": "/static/3d-models/kitchen_display.obj",
            
            # Network equipment (secondary - for restaurant infrastructure)
            "Cisco Meraki Wireless Access Point": "/static/3d-models/meraki_ap.obj",
            "Cisco Meraki Switch": "/static/3d-models/switch.obj",
            "Cisco Meraki Security Appliance/Firewall": "/static/3d-models/firewall.obj",
            "Fortinet Firewall/UTM": "/static/3d-models/firewall.obj",
            "Fortinet Wireless Access Point": "/static/3d-models/ap.obj",
            "Fortinet Switch": "/static/3d-models/switch.obj",
            
            # Generic models for fallback
            "Wireless Access Point": "/static/3d-models/generic_ap.obj",
            "Firewall/UTM": "/static/3d-models/generic_firewall.obj",
            "Switch": "/static/3d-models/generic_switch.obj",
            "POS Terminal": "/static/3d-models/generic_pos.obj",
            "Camera": "/static/3d-models/generic_camera.obj",
            "Generic Device": "/static/3d-models/generic_device.obj"
        }
        
        if path and Path(path).exists():
            try:
                with open(path, 'r') as f:
                    custom_models = json.load(f)
                    default_models.update(custom_models)
                    log.info(f"Loaded custom model library: {len(custom_models)} entries")
            except Exception as e:
                log.warning(f"Failed to load custom model library: {e}")
        
        return default_models
    
    def match_mac_to_model(self, mac_address: str, additional_context: Optional[Dict] = None) -> DeviceInfo:
        """
        Given MAC address, return vendor, device type, and 3D model path
        Following iconlab.md architecture exactly
        """
        # Step 1: Lookup vendor from MAC
        vendor_info = self.oui_lookup.lookup(mac_address)
        vendor = vendor_info.get('vendor', 'Unknown')
        
        # Step 2: Classify device type
        device_type = self.classifier.classify_device(mac_address, vendor, additional_context)
        
        # Step 3: Match to 3D model following iconlab.md logic
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
        
        confidence = 'high' if model_path in self.model_library.values() else 'low'
        
        # Check for POS system
        pos_system = self.classifier.identify_pos_device(mac_address, self.oui_lookup, additional_context)
        
        details = {
            'oui_info': vendor_info,
            'pos_system': pos_system,
            'random_mac': self.classifier._detect_random_mac(mac_address) == 'random_mac',
            'model_key': model_key,
            'lookup_method': 'macaddress.io' if self.oui_lookup.macaddress_io_api_key else 'local'
        }
        
        return DeviceInfo(
            mac_address=mac_address,
            vendor=vendor,
            device_type=device_type,
            confidence=confidence,
            model_path=model_path,
            pos_system=pos_system,
            details=details
        )
    
    def get_generic_model(self, device_type: str) -> str:
        """Return generic 3D model based on device category - from iconlab.md"""
        generic_models = {
            'Wireless Access Point': '/static/3d-models/generic_ap.obj',
            'Firewall/UTM': '/static/3d-models/generic_firewall.obj',
            'Switch': '/static/3d-models/generic_switch.obj',
            'POS Terminal': '/static/3d-models/generic_pos.obj',
            'POS Register/Cash Terminal': '/static/3d-models/generic_pos.obj',
            'POS Tablet/Tabletop Ordering': '/static/3d-models/generic_pos.obj',
            'Kitchen Display Unit (KDS)': '/static/3d-models/generic_device.obj',
            'Digital Menu Board': '/static/3d-models/generic_device.obj',
            'Kitchen/Receipt Printer': '/static/3d-models/generic_device.obj',
            'Payment Terminal': '/static/3d-models/generic_device.obj',
            'Camera': '/static/3d-models/generic_camera.obj'
        }
        return generic_models.get(device_type, '/static/3d-models/generic_device.obj')
    
    def bulk_match(self, mac_addresses: List[str], context_map: Optional[Dict[str, Dict]] = None) -> List[DeviceInfo]:
        """Match multiple MAC addresses to models - from iconlab.md usage example"""
        results = []
        for mac in mac_addresses:
            context = context_map.get(mac) if context_map else None
            device_info = self.match_mac_to_model(mac, context)
            results.append(device_info)
        return results

# API integration functions
def create_device_matching_api(app):
    """Create FastAPI endpoints for device matching"""
    from fastapi import HTTPException
    from pydantic import BaseModel
    
    class MACMatchRequest(BaseModel):
        mac_addresses: List[str]
        context: Optional[Dict[str, Dict]] = None
    
    class MACMatchResponse(BaseModel):
        matches: List[DeviceInfo]
        total: int
    
    matcher = DeviceModelMatcher()
    
    @app.post("/api/devices/match-macs", response_model=MACMatchResponse)
    async def match_mac_addresses(request: MACMatchRequest):
        """Match MAC addresses to device types and 3D models"""
        try:
            matches = matcher.bulk_match(request.mac_addresses, request.context)
            return MACMatchResponse(matches=matches, total=len(matches))
        except Exception as e:
            log.error(f"MAC matching error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/devices/lookup/{mac_address}")
    async def lookup_single_mac(mac_address: str):
        """Lookup single MAC address"""
        try:
            device_info = matcher.match_mac_to_model(mac_address)
            return device_info
        except Exception as e:
            log.error(f"MAC lookup error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

if __name__ == "__main__":
    # Demo usage - following iconlab.md usage example
    matcher = DeviceModelMatcher()
    
    # Discover devices on network (example MAC addresses from iconlab.md)
    discovered_devices = [
        {'mac': 'F0:9F:C2:12:34:56', 'hostname': 'MR46-Office'},
        {'mac': '90:6C:AC:98:76:54', 'hostname': 'FortiGate-60F'},
        {'mac': 'AC:BC:32:11:22:33', 'hostname': 'Square-Terminal-01'},
        {'mac': '00:0C:F1:12:34:56', 'hostname': 'Clover-Station-01'},
        {'mac': 'B8:27:EB:98:76:54', 'hostname': 'Toast-KDS-01'}
    ]
    
    # Match each device to 3D model
    matched_devices = []
    for device in discovered_devices:
        match = matcher.match_mac_to_model(
            device['mac'],
            additional_context={'hostname': device['hostname']}
        )
        matched_devices.append(match)
        
        print(f"MAC: {match.mac_address}")
        print(f"Vendor: {match.vendor}")
        print(f"Device: {match.device_type}")
        print(f"3D Model: {match.model_path}")
        print(f"Confidence: {match.confidence}")
        if match.pos_system:
            print(f"POS System: {match.pos_system}")
        print("---")
    
    # Export mapping for use in visualization tools
    with open('device_3d_mapping.json', 'w') as f:
        json.dump([vars(device) for device in matched_devices], f, indent=2)
    
    print(f"Exported {len(matched_devices)} device mappings to device_3d_mapping.json")
