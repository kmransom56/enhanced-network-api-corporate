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

class FortiGateAuth:
    """Authentication handler for FortiGate API"""
    
    def __init__(self, host: str, api_token: str, verify_ssl: bool = False, ca_cert: str = None):
        self.host = host
        self.api_token = api_token
        self.verify_ssl = verify_ssl
        self.ca_cert = ca_cert
        self.session = None
        
    def login(self) -> bool:
        """Initialize session with API token"""
        try:
            self.session = requests.Session()
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            })
            
            if self.ca_cert:
                self.session.verify = self.ca_cert
            else:
                self.session.verify = self.verify_ssl
            
            #Verify connectivity (optional, but good practice)
            url = f"https://{self.host}/api/v2/monitor/system/status"
            resp = self.session.get(url, timeout=5)
            return resp.status_code == 200
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False