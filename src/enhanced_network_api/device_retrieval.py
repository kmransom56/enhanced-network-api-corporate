
class DeviceRetrievalModule:
    """Module for retrieving device information from FortiManager."""

    def __init__(self, session):
        self.session = session

    def get_all_devices(self, adom="root"):
        """Retrieves all registered devices."""
        params = [{
            "url": f"/dvmdb/adom/{adom}/device"
        }]
        return self.session.post("get", params)

    def get_fortigates(self, adom="root"):
        """Retrieves all FortiGate devices."""
        params = [{
            "url": f"/dvmdb/adom/{adom}/device",
            "filter": ["platform_str", "==", "FortiGate"]
        }]
        return self.session.post("get", params)
