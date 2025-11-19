
class FirewallPolicyModule:
    """Module for managing firewall policies in FortiManager."""

    def __init__(self, session):
        self.session = session

    def get_policy_packages(self, adom="root"):
        """Retrieves all policy packages."""
        params = [{
            "url": f"/pm/pkg/adom/{adom}"
        }]
        return self.session.post("get", params)

    def get_firewall_policies(self, adom="root", package_name="default"):
        """Retrieves firewall policies from a specific package."""
        params = [{
            "url": f"/pm/config/adom/{adom}/pkg/{package_name}/firewall/policy"
        }]
        return self.session.post("get", params)
