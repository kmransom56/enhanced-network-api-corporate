import requests

class FortiGateSession:
    """Manages an authenticated session for making API calls to a FortiGate."""

    def __init__(self, config):
        self.host = config.host
        self.api_key = config.api_key
        self.session = None

    def __enter__(self):
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
        self.session.verify = False
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
