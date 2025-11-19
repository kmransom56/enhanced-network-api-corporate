
class FortiSwitchModule:
    """Module for managing FortiSwitch devices."""

    def __init__(self, session):
        self.session = session

    def get_switches(self, adom="root"):
        """Retrieves all FortiSwitch devices."""
        params = [{
            "url": f"/dvmdb/adom/{adom}/device",
            "filter": ["platform_str", "==", "FortiSwitch"]
        }]
        return self.session.post("get", params)

    def get_managed_switches(self, fortigate_name, adom="root"):
        """Retrieves switches managed by a specific FortiGate."""
        params = [{
            "url": f"/pm/config/adom/{adom}/device/{fortigate_name}/switch-controller/managed-switch"
        }]
        return self.session.post("get", params)
