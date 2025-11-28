#!/usr/bin/env python3
"""MAC address to 3D model matcher utility."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


class DeviceModelMatcher:
    def __init__(self, oui_lookup: Dict[str, Dict[str, str]], model_library: Dict[str, str]):
        self.oui_lookup = oui_lookup
        self.model_library = model_library

    @classmethod
    def from_files(cls, oui_path: Path, models_path: Path) -> "DeviceModelMatcher":
        oui_lookup = json.loads(oui_path.read_text())
        model_library = json.loads(models_path.read_text())
        return cls(oui_lookup, model_library)

    def match(self, mac: str, hostname: str | None = None) -> Dict[str, Any]:
        oui = ':'.join(mac.upper().split(':')[:3])
        vendor_info = self.oui_lookup.get(oui, {})
        vendor = vendor_info.get('vendor', 'Unknown')

        device_type = self._classify(vendor, hostname)
        key = f"{vendor} {device_type}".strip()
        model_path = self.model_library.get(key) or self._fallback_model(device_type)

        return {
            'mac_address': mac,
            'vendor': vendor,
            'device_type': device_type,
            'model_path': model_path,
        }

    def _classify(self, vendor: str, hostname: str | None) -> str:
        patterns = {
            'cisco meraki': {
                'MR': 'Wireless Access Point',
                'MS': 'Switch',
                'MX': 'Security Appliance',
                'MV': 'Camera',
            },
            'fortinet': {
                'FAP': 'Wireless Access Point',
                'FSW': 'Switch',
                'FG': 'Firewall',
            },
        }

        vendor_lower = vendor.lower()
        for key, mapping in patterns.items():
            if key in vendor_lower and hostname:
                for prefix, device_type in mapping.items():
                    if prefix.lower() in hostname.lower():
                        return device_type

        if 'meraki' in vendor_lower:
            return 'Meraki Device'
        if 'fortinet' in vendor_lower:
            return 'Fortinet Device'
        return 'Unknown Device'

    def _fallback_model(self, device_type: str) -> str:
        generic = {
            'Wireless Access Point': 'models/generic_ap.obj',
            'Switch': 'models/generic_switch.obj',
            'Security Appliance': 'models/generic_firewall.obj',
            'Firewall': 'models/generic_firewall.obj',
            'Camera': 'models/generic_camera.obj',
        }
        return generic.get(device_type, 'models/generic_device.obj')


def main() -> None:
    parser = argparse.ArgumentParser(description="Match discovered MACs to 3D models")
    parser.add_argument('macs', help='JSON file with discovered devices')
    parser.add_argument('--oui', type=Path, default=Path('data/oui/lookup.json'))
    parser.add_argument('--models', type=Path, default=Path('data/models/model_library.json'))
    parser.add_argument('--out', type=Path, default=Path('output/device_model_mapping.json'))
    args = parser.parse_args()

    matcher = DeviceModelMatcher.from_files(args.oui, args.models)
    devices: List[Dict[str, Any]] = json.loads(Path(args.macs).read_text())
    results = [matcher.match(device['mac'], device.get('hostname')) for device in devices]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(f"Wrote mapping for {len(results)} devices -> {args.out}")


if __name__ == '__main__':
    main()
