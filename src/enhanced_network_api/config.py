
import os

class FortiManagerConfig:
    """Configuration for a single FortiManager instance."""
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

class MerakiConfig:
    """Configuration for the Meraki Dashboard API."""
    def __init__(self, api_key):
        self.api_key = api_key

class NetworkEnvironments:
    """Manages configurations for all network environments."""
    def __init__(self):
        self.arbys = FortiManagerConfig(
            host=os.getenv("ARBYS_FM_HOST"),
            username=os.getenv("ARBYS_FM_USER"),
            password=os.getenv("ARBYS_FM_PASS")
        )
        self.bww = FortiManagerConfig(
            host=os.getenv("BWW_FM_HOST"),
            username=os.getenv("BWW_FM_USER"),
            password=os.getenv("BWW_FM_PASS")
        )
        self.sonic = FortiManagerConfig(
            host=os.getenv("SONIC_FM_HOST"),
            username=os.getenv("SONIC_FM_USER"),
            password=os.getenv("SONIC_FM_PASS")
        )
        self.meraki = MerakiConfig(
            api_key=os.getenv("MERAKI_API_KEY")
        )

# Global instance for easy access
config = NetworkEnvironments()
