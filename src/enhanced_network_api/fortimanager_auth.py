import requests
import json

class FortiManagerAuth:
    """Handles session-based authentication for FortiManager using JSON-RPC."""

    def __init__(self, config):
        self.host = config.host
        self.username = config.username
        self.password = config.password
        self.session_key = None

    def login(self):
        """Logs into FortiManager and retrieves a session key."""
        if not self.host or not self.username or not self.password:
            print("Error: FortiManager host, username, or password not configured.")
            return False

        url = f"https://{self.host}/jsonrpc"
        payload = {
            "id": 1,
            "method": "exec",
            "params": [
                {
                    "data": {
                        "user": self.username,
                        "passwd": self.password
                    },
                    "url": "/sys/login/user"
                }
            ]
        }

        try:
            # Using a temporary session to login
            with requests.Session() as s:
                response = s.post(url, data=json.dumps(payload), verify=False)
                response.raise_for_status()
                result = response.json()

                if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
                    self.session_key = result.get("session")
                    print(f"Successfully logged into {self.host}")
                    return True
                else:
                    print(f"Failed to log in to {self.host}: {result.get('result', [{}])[0].get('status')}")
                    return False
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to {self.host}: {e}")
            return False

    def logout(self):
        """Logs out of FortiManager."""
        if not self.session_key:
            return

        url = f"https://{self.host}/jsonrpc"
        payload = {
            "id": 1,
            "method": "exec",
            "params": [{"url": "/sys/logout"}],
            "session": self.session_key
        }
        try:
            requests.post(url, data=json.dumps(payload), verify=False)
            print(f"Successfully logged out from {self.host}")
        except requests.exceptions.RequestException as e:
            print(f"Error logging out from {self.host}: {e}")
        finally:
            self.session_key = None

class FortiManagerSession:
    """Manages an authenticated session for making API calls to FortiManager."""

    def __init__(self, config):
        self.auth = FortiManagerAuth(config)
        self.session = None

    def __enter__(self):
        if self.auth.login():
            self.session = requests.Session()
            self.session.headers.update({"Content-Type": "application/json"})
            return self
        raise ConnectionError("Failed to authenticate with FortiManager")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
        self.auth.logout()

    def post(self, method, params):
        """Sends a POST request to the FortiManager JSON-RPC endpoint."""
        if not self.session:
            raise ConnectionError("Session not established.")
            
        url = f"https://{self.auth.host}/jsonrpc"
        payload = {
            "id": 1,
            "method": method,
            "params": params,
            "session": self.auth.session_key
        }
        response = self.session.post(url, data=json.dumps(payload), verify=False)
        response.raise_for_status()
        return response.json()