
class FortiAPModule:
    """Module for managing FortiAP access points."""

    def __init__(self, session):
        self.session = session

    def get_aps(self, adom="root"):
        """Retrieves all FortiAP devices."""
        params = [{
            "url": f"/dvmdb/adom/{adom}/device",
            "filter": ["platform_str", "==", "FortiAP"]
        }]
        return self.session.post("get", params)

    def get_ap_status(self, adom="root", ap_name=None):
        """Retrieves the status of a specific or all FortiAPs."""
        url = f"/dvm/adom/{adom}/ap/status"
        if ap_name:
            url += f"/{ap_name}"
        
        params = [{"url": url}]
        return self.session.post("get", params)
