import fortiosapi
import json
import requests

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings() 

# --- Configuration (Use Token Authentication) ---
FGT_HOST = "192.168.0.254:10443"
FGT_TOKEN = "7H8p0ykg0pc3szHxHcQ80xd5p798yh"
VDOM_NAME = "root"             

try:
    # 1. Initialize and Login using Token Authentication
    fgt_client = fortiosapi.FortiOSAPI()
    print(f"Connecting to {FGT_HOST} with token...")
    
    # tokenlogin automatically handles session creation/cookies
    fgt_client.tokenlogin(
        host=FGT_HOST,
        apitoken=FGT_TOKEN,
        vdom=VDOM_NAME,
        verify=False # Set to True if using a valid, trusted SSL certificate
    )

    # 2. Get Real-time System Status (Monitor part of API)
    print("\nFetching system status (hostname, version)...")
    status_response = fgt_client.monitor(path="system", name="status", vdom=VDOM_NAME)
    
    print("\nRaw System Status Response:")
    print(json.dumps(status_response, indent=4))  # Print the entire response to debug

    if status_response and status_response.get('status', 1) == 0:
        hostname = status_response['results'].get('hostname', 'N/A')
        version = status_response['results'].get('version', 'N/A')
        print(f"Status Retrieved: Hostname='{hostname}', Version='{version}'")
    else:
        print("Failed to retrieve system status or no results found.")

    # 3. Get Interface Configuration (CMDB part of API)
    print("\nFetching configured interfaces...")
    interfaces_response = fgt_client.get(path="system", name="interface", vdom=VDOM_NAME)
    
    print("\nRaw Interfaces Response:")
    print(json.dumps(interfaces_response, indent=4))  # Print the entire response to debug

    if interfaces_response and interfaces_response.get('status', 1) == 0:
        print(f"Found {len(interfaces_response['results'])} interfaces.")
        
        # Example: Extracting interface names and IPs for network visualization
        network_segments = []
        for interface in interfaces_response['results']:
            network_segments.append({
                "name": interface.get('name'),
                "ip": interface.get('ip'),
                "vdom": interface.get('vdom'),
            })
        print(json.dumps(network_segments[:3], indent=4)) # Print first 3 entries
        # Use interface data to draw network lines/boundaries on your map.
        
except fortiosapi.LoginError as e:
    print(f"\nAuthentication Error: {e}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
    
finally:
    # 4. Logout (Release resources)
    if 'fgt_client' in locals():
        try:
            fgt_client.logout()
            print("\nSuccessfully logged out.")
        except Exception:
            pass



