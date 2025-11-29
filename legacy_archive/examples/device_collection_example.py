
import os
from enhanced_network_api.config import config
from enhanced_network_api.fortimanager_auth import FortiManagerAuth
from enhanced_network_api.device_collector import DeviceCollector

def main():
    """Demonstrates the use of the FortiManager authentication and device collector modules."""

    print("--- FortiManager and Meraki Device Collection Demo ---")

    # --- Environment Setup ---
    # In a real scenario, you would set these environment variables.
    # For this demo, we'll set them if they are not already present.
    os.environ.setdefault("ARBYS_FM_HOST", "fortimanager.arbys.com")
    os.environ.setdefault("ARBYS_FM_USER", "api-user")
    os.environ.setdefault("ARBYS_FM_PASS", "your-password")
    os.environ.setdefault("MERAKI_API_KEY", "your-meraki-api-key")
    
    # This would be the specific Meraki network ID for the Arby's environment
    arbys_meraki_network_id = "L_123456789012345678"

    print(f"\nConnecting to Arby's environment at {config.arbys.host}...")

    # Using the context manager for automatic login/logout
    with FortiManagerAuth(config.arbys) as fm_auth:
        if fm_auth.is_logged_in:
            
            # Initialize the device collector
            collector = DeviceCollector(fm_auth, config.meraki)

            # Get devices from the mixed Arby's environment
            devices = collector.get_arbys_bww_devices(arbys_meraki_network_id)

            print("\n--- Connected Devices Found ---")
            for device in devices:
                print(f"  Source: {device['source']}, Device: {device['device']}, IP: {device['ip']}")
            print("-----------------------------\n")

if __name__ == "__main__":
    main()
