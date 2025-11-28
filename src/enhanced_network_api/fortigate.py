
class FortiGateModule:
    """Module for managing FortiGate devices."""

    def __init__(self, session):
        self.session = session
        self.base_url = f"https://{session.host}"

    def get_fortiswitches(self):
        """Retrieves all FortiSwitch devices."""
        url = f"{self.base_url}/api/v2/monitor/switch-controller/managed-switch/status"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_fortiaps(self):
        """Retrieves all FortiAP devices."""
        url = f"{self.base_url}/api/v2/monitor/wifi/managed_ap"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_connected_clients(self):
        """Retrieves all connected clients."""
        url = f"{self.base_url}/api/v2/monitor/wifi/client"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
