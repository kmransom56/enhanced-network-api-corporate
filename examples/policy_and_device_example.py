
import os
import json
from enhanced_network_api import (
    config,
    FortiManagerSession,
    DeviceRetrievalModule,
    FirewallPolicyModule,
)

def main():
    """
    Demonstrates the use of the new FortiManager modules for retrieving
    firewall policies and device information.
    """

    print("--- FortiManager Policy and Device Retrieval Demo ---")

    # --- Environment Setup ---
    os.environ.setdefault("SONIC_FM_HOST", "fortimanager.sonic.com")
    os.environ.setdefault("SONIC_FM_USER", "api-user")
    os.environ.setdefault("SONIC_FM_PASS", "your-password")

    print(f"\nConnecting to Sonic environment at {config.sonic.host}...")

    try:
        # Use the session context manager for automatic login/logout
        with FortiManagerSession(config.sonic) as fm_session:
            
            # Initialize the required modules with the session
            device_module = DeviceRetrievalModule(fm_session)
            policy_module = FirewallPolicyModule(fm_session)

            # --- Retrieve and Display Firewall Policies ---
            print("\n--- Retrieving Firewall Policy Packages ---")
            packages = policy_module.get_policy_packages()
            print(json.dumps(packages, indent=2))

            # Assuming a package named 'default' exists
            print("\n--- Retrieving Firewall Policies from 'default' package ---")
            policies = policy_module.get_firewall_policies(package_name="default")
            print(json.dumps(policies, indent=2))


            # --- Retrieve and Display Devices ---
            print("\n--- Retrieving All Devices ---")
            all_devices = device_module.get_all_devices()
            print(json.dumps(all_devices, indent=2))
            
            print("\n--- Retrieving FortiGates ---")
            fortigates = device_module.get_fortigates()
            print(json.dumps(fortigates, indent=2))


    except ConnectionError as e:
        print(f"\nConnection failed: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
