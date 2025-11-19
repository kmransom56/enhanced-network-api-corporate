
import requests
import json
from .fortimanager_auth import FortiManagerAuth
from .config import MerakiConfig

class DeviceCollector:
    """Collects connected device information from various network sources."""

    def __init__(self, fortimanager_auth: FortiManagerAuth, meraki_config: MerakiConfig = None):
        self.fm_auth = fortimanager_auth
        self.meraki_config = meraki_config

    def _fm_request(self, method, endpoint, payload=None):
        """Makes an authenticated request to the FortiManager API."""
        if not self.fm_auth.is_logged_in:
            print("Error: Not logged into FortiManager.")
            return None

        url = f"https://{self.fm_auth.host}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        # FortiManager uses a JSON-RPC like structure
        rpc_payload = {
            "id": 1,
            "method": method,
            "params": [
                {
                    "url": endpoint,
                    "data": payload if payload else {}
                }
            ]
        }

        try:
            response = self.fm_auth.session.post(url, data=json.dumps(rpc_payload), headers=headers, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"FortiManager API request failed: {e}")
            return None

    def _meraki_request(self, endpoint):
        """Makes a request to the Meraki Dashboard API."""
        if not self.meraki_config or not self.meraki_config.api_key:
            print("Error: Meraki API key not configured.")
            return None

        url = f"https://api.meraki.com/api/v1/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.meraki_config.api_key}",
            "Accept": "application/json"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Meraki API request failed: {e}")
            return None

    def get_sonic_devices(self):
        """Gets connected devices for the Sonic environment (all Fortinet)."""
        print("Fetching devices for Sonic (FortiGate, FortiSwitch, FortiAP)...")
        # This is a placeholder for the actual FortiManager API calls
        # to get connected clients from managed devices.
        # The exact endpoints need to be identified from detailed FortiManager documentation.
        
        # Example of what the calls might look like:
        # fortigates = self._fm_request("get", "/dvmdb/device/fortigate")
        # clients = []
        # for fg in fortigates.get('result', [{}])[0].get('data', []):
        #     cli_output = self._fm_request("exec", f"/sys/proxy/json/{fg['name']}/api/v2/monitor/user/device/select")
        #     clients.extend(cli_output)
        
        return [{"source": "FortiManager", "device": "sonic_placeholder_device", "ip": "192.168.1.100"}]

    def get_arbys_bww_devices(self, network_id):
        """Gets connected devices for Arby's/BWW (FortiGate/AP + Meraki Switch)."""
        print(f"Fetching devices for network {network_id} (FortiGate/AP + Meraki Switch)...")
        
        fortinet_devices = [{"source": "FortiManager", "device": "arbys_bww_placeholder_fg_client", "ip": "10.0.0.50"}]
        
        print("Fetching Meraki switch clients...")
        meraki_clients = self._meraki_request(f"networks/{network_id}/clients")
        
        if meraki_clients:
            for client in meraki_clients:
                fortinet_devices.append({
                    "source": "Meraki",
                    "device": client.get('description', client.get('mac')),
                    "ip": client.get('ip')
                })
                
        return fortinet_devices
