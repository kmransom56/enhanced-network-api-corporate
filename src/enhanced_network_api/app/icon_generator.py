"""
Module for generating 2D icons based on MAC addresses.
"""

import os
import logging
from typing import Dict, Optional

log = logging.getLogger(__name__)

class IconGenerator:
    """
    Generates 2D icons based on MAC addresses.
    """

    def __init__(self, oui_csv_path: Optional[str] = None):
        self.oui_lookup = OUILookup(oui_csv_path)
        self.classifier = DeviceClassifier()

    def generate_icon(self, mac_address: str, additional_context: Optional[Dict] = None):
        """
        Generates an icon for a given MAC address.
        """
        vendor_info = self.oui_lookup.lookup(mac_address)
        vendor = vendor_info.get('vendor', 'Unknown')
        device_type = self.classifier.classify_device(mac_address, vendor, additional_context)

        # This is a placeholder for the actual icon generation logic.
        # In a real application, this would involve creating an SVG or PNG image.
        return {
            "mac_address": mac_address,
            "vendor": vendor,
            "device_type": device_type,
            "icon_data": f"<svg>...</svg>"  # Placeholder for SVG data
        }

class OUILookup:
    """
    Enhanced OUI database with macaddress.io API integration
    """
    def __init__(self, oui_csv_path: Optional[str] = None):
        self.oui_dict: Dict[str, Dict[str, str]] = {}
        self.macaddress_io_api_key = os.getenv('MACADDRESS_IO_API_KEY')
        self.macaddress_io_base_url = os.getenv('MACADDRESS_IO_BASE_URL', 'https://api.macaddress.io/v1')
        self._load_builtin_ouis()

    def lookup(self, mac_address: str) -> Dict[str, str]:
        """
        Lookup vendor information for a MAC address
        """
        mac_clean = mac_address.replace(':', '').replace('-', '').replace('.', '').upper()
        if len(mac_clean) < 6:
            return {'vendor': 'Invalid MAC', 'address': ''}
        oui = ':'.join([mac_clean[i:i+2] for i in range(0, 6, 2)])
        return self.oui_dict.get(oui, {'vendor': 'Unknown', 'address': ''})

    def _load_builtin_ouis(self):
        """
        Load common vendor OUIs for network and restaurant equipment
        """
        builtin_ouis = {
            "00:0C:F1": {"vendor": "Ingenico", "address": "Paris, France"},
            "F0:9F:C2": {"vendor": "Cisco Meraki", "address": "San Francisco, CA"},
            "90:6C:AC": {"vendor": "Fortinet", "address": "Sunnyvale, CA"},
        }
        self.oui_dict = {k.upper(): v for k, v in builtin_ouis.items()}

class DeviceClassifier:
    """
    Classify devices based on vendor and context
    """
    def classify_device(self, mac: str, vendor: str, context: Optional[Dict] = None) -> str:
        """
        Classify device type based on MAC, vendor, and optional context
        """
        vendor_lower = vendor.lower()
        if "fortinet" in vendor_lower:
            return "Fortinet Device"
        elif "cisco meraki" in vendor_lower:
            return "Meraki Device"
        elif "ingenico" in vendor_lower:
            return "Ingenico Device"
        return "Unknown Device"
