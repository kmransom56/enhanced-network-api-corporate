import pyFortiManagerAPI # Note the capitalization
import json
import requests
import ssl
import sys

# --- Configuration ---
FMG_HOST = "192.168.0.254"       # Replace with your FortiManager IP/FQDN
FMG_USER = "admin"          # Replace with your API username
FMG_PASS = "!cg@RW%G@o"     # Replace with your password
ADOM_NAME = "root"             # Replace with your ADOM name

# Disable SSL warnings if verify=False is used
requests.packages.urllib3.disable_warnings() 

try:
    # 1. Initialize the FortiManager Client
    print("Attempting to connect and log in...")
    # This automatically performs the JSON-RPC login
    fmg_client = pyFortiManagerAPI.FortiManager(
        host=FMG_HOST,
        username=FMG_USER,
        password=FMG_PASS,
        adom=ADOM_NAME,
        verify=False  # Only use False for self-signed certificates
    )

    # 2. GET THE LIST OF MANAGED DEVICES (Using the correct method)
    print(f"Fetching device list for ADOM: {ADOM_NAME}...")
    devices_response = fmg_client.get_all_device() 

    # 3. Process and Extract Data
    if devices_response.get('status', {}).get('code') == 0:
        print(f"✅ Successfully retrieved {len(devices_response.get('data', []))} devices.")
        # ... your visualization data processing goes here ...
        
    else:
        print("\n--- API Error ---")
        print(f"Error fetching devices: {devices_response}")

except Exception as e:
    # This will catch connection errors, authentication failures, etc.
    print(f"\nAn error occurred: {type(e).__name__}: {e}")

finally:
    # 4. Logout (Crucial for session-based authentication)
    # The 'pyFortiManagerAPI' library has a 'logout' method.
    if 'fmg_client' in locals() and hasattr(fmg_client, 'logout'):
        try:
            fmg_client.logout()
            print("\nSuccessfully logged out.")
        except Exception:
            pass 
