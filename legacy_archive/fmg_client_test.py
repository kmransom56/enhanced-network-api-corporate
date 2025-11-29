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
    
    # We will assume the host and port format is correct as the script didn't crash on login.
    fgt_client.tokenlogin(
        host=FGT_HOST,
        apitoken=FGT_TOKEN,
        vdom=VDOM_NAME,
        verify=False 
    )
    print("✅ Login successful.")
    
    # 2. Get Real-time System Status (Monitor part of API)
    print("\nFetching system status (hostname, version)...")
    status_response = fgt_client.monitor(path="system", name="status", vdom=VDOM_NAME)
    
    if status_response and status_response.get('status', 1) == 0:
        hostname = status_response['results'].get('hostname', 'N/A')
        version = status_response['results'].get('version', 'N/A')
        print(f"✅ Status Retrieved: Hostname='{hostname}', Version='{version}'")
        
    else:
        # Print the full response if the status code indicates an error
        print(f"❌ ERROR: Status fetch failed. Response:\n{json.dumps(status_response, indent=4)}")


    # 3. Get Interface Configuration (CMDB part of API)
    print("\nFetching configured interfaces...")
    interfaces_response = fgt_client.get(path="system", name="interface", vdom=VDOM_NAME)

    if interfaces_response and interfaces_response.get('status', 1) == 0:
        results = interfaces_response.get('results', [])
        print(f"✅ Found {len(results)} interfaces.")
        
        # Extracting interface names and IPs for network visualization
        network_segments = []
        for interface in results:
            network_segments.append({
                "name": interface.get('name'),
                "ip": interface.get('ip'),
                "vdom": interface.get('vdom'),
                # Add other useful data like 'status' or 'role' here
            })
        
        print("\n--- Interface Data Sample ---")
        print(json.dumps(network_segments[:3], indent=4)) # Print first 3 entries for quick check
        
    else:
        # Print the full response if the status code indicates an error
        print(f"❌ ERROR: Interface fetch failed. Response:\n{json.dumps(interfaces_response, indent=4)}")
        
except fortiosapi.LoginError as e:
    print(f"\n❌ Authentication Error: {e}")
except Exception as e:
    print(f"\n❌ An unexpected error occurred: {type(e).__name__}: {e}")
    
finally:
    # 4. Logout (Release resources)
    if 'fgt_client' in locals():
        try:
            fgt_client.logout()
            print("\nSuccessfully logged out.")
        except Exception:
            pass
