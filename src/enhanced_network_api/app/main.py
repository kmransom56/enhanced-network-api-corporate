"""
Main application file for the Enhanced Network API.

This application queries FortiGate devices, generates 2D icons based on MAC addresses,
and exports the icons to a format compatible with Babylon.js for 3D rendering.
"""

import argparse

from .fortigate import FortiGateManager
from .icon_generator import IconGenerator
from .babylon_exporter import BabylonExporter

def main():
    """
    Main function for the Enhanced Network API.
    """
    parser = argparse.ArgumentParser(description="Enhanced Network API")
    parser.add_argument("--host", default="192.168.0.254:10443", help="FortiGate host")
    parser.add_argument("--username", default="admin", help="FortiGate username")
    parser.add_argument("--password", required=True, help="FortiGate password")
    args = parser.parse_args()

    print("Starting the Enhanced Network API workflow...")

    # Initialize the managers
    fortigate_manager = FortiGateManager(host=args.host, username=args.username, password=args.password)
    icon_generator = IconGenerator()
    babylon_exporter = BabylonExporter()

    # Login to FortiGate
    if fortigate_manager.login():
        # Get connected devices
        devices = fortigate_manager.get_connected_devices()

        # Generate icons
        icons = [icon_generator.generate_icon(device["mac"]) for device in devices]

        # Export to Babylon.js
        babylon_exporter.export_to_babylon(icons)

        # Logout from FortiGate
        fortigate_manager.logout()

    print("Enhanced Network API workflow finished.")

if __name__ == "__main__":
    main()
