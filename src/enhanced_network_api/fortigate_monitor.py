import requests
import time
import logging
from typing import Optional, Union

logger = logging.getLogger(__name__)

class FortiGateMonitor:
    """Comprehensive FortiGate monitoring interface.
    
    Provides easy access to 40+ FortiGate monitoring endpoints including:
    - WiFi clients, SSIDs, radios, neighbors
    - Switch controller clients, ports, status, VLANs, PoE
    - Routing, ARP, DHCP, OSPF, BGP
    - LLDP, interfaces
    - System status, CPU, memory, performance
    - Firewall sessions, policy hits
    - Logs (event, traffic)
    - Device inventory
    - Diagnostics (ping, traceroute)
    """
    def __init__(self, host: str, token: str, ca_bundle: Optional[Union[bool, str]] = None, port: int = 10443):
        """Initialize FortiGateMonitor.
        
        Args:
            host: FortiGate hostname or IP address
            token: API token for authentication
            ca_bundle: SSL certificate bundle path (str) or verify flag (bool). 
                      If None, defaults to False (skip verification).
            port: FortiGate API port (default: 10443)
        """
        self.base = f"https://{host}:{port}/api/v2"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        # Handle ca_bundle: can be bool, str (path), or None
        if ca_bundle is None:
            self.verify = False
        elif isinstance(ca_bundle, bool):
            self.verify = ca_bundle
        else:
            # Assume it's a path to CA bundle
            self.verify = ca_bundle
        
        # Disable SSL warnings if verification is disabled
        if not self.verify:
            try:
                requests.packages.urllib3.disable_warnings(
                    requests.packages.urllib3.exceptions.InsecureRequestWarning
                )
            except AttributeError:
                pass

    def _get(self, path: str, params: Optional[dict] = None):
        """Internal method to make GET requests to FortiGate API.
        
        Args:
            path: API endpoint path (relative to /api/v2)
            params: Optional query parameters
            
        Returns:
            JSON response data or error dict
        """
        url = f"{self.base}/{path}"
        try:
            r = requests.get(url, headers=self.headers, verify=self.verify, params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"FortiGateMonitor API call failed for {path}: {e}")
            return {"error": str(e), "endpoint": path}
        except Exception as e:
            logger.error(f"Unexpected error in FortiGateMonitor._get({path}): {e}")
            return {"error": str(e), "endpoint": path}

    # ====================
    # WIFI
    # ====================
    def wifi_clients(self): return self._get("monitor/wifi/client")
    def wifi_ssids(self): return self._get("monitor/wifi/ssid")
    def wifi_radios(self): return self._get("monitor/wifi/radio")
    def wifi_neighbors(self): return self._get("monitor/wifi/neighbor")
    def wifi_manufacturer(self): return self._get("monitor/wifi/manufacturer")
    def wifi_reputation(self): return self._get("monitor/wifi/reputation")
    def wifi_channels(self): return self._get("monitor/wifi/channel")

    # ====================
    # SWITCH CONTROLLER
    # ====================
    def switch_clients(self): return self._get("monitor/switch-controller/managed-switch/clients")
    def switch_ports(self): return self._get("monitor/switch-controller/managed-switch/ports")
    def switch_status(self): return self._get("monitor/switch-controller/managed-switch/status")
    def switch_vlans(self): return self._get("monitor/switch-controller/managed-switch/vlan")
    def switch_poe(self): return self._get("monitor/switch-controller/managed-switch/poe")

    # ====================
    # ROUTING / ARP / DHCP
    # ====================
    def arp_table(self): return self._get("monitor/system/arp")
    def dhcp(self): return self._get("monitor/router/dhcp/lease")
    def routing_ipv4(self): return self._get("monitor/router/ipv4")
    def routing_neighbors(self): return self._get("monitor/router/neighbor")
    def ospf(self): return self._get("monitor/router/ospf")
    def bgp(self): return self._get("monitor/router/bgp")
    def nexthop(self): return self._get("monitor/router/nexthop")

    # ====================
    # LLDP / INTERFACES
    # ====================
    def lldp(self): return self._get("monitor/lldp/neighbor")
    def interfaces(self): return self._get("monitor/system/interface")

    # ====================
    # SYSTEM INFO
    # ====================
    def system_status(self): return self._get("monitor/system/status")
    def cpu(self): return self._get("monitor/system/resource/cpu")
    def memory(self): return self._get("monitor/system/resource/memory")
    def performance(self): return self._get("monitor/system/performance")
    def disk(self): return self._get("monitor/system/disk")
    def lograte(self): return self._get("monitor/system/lograte")
    def sessions(self): return self._get("monitor/system/session")

    # ====================
    # FIREWALL / SECURITY
    # ====================
    def fw_policy_hits(self): return self._get("monitor/router/firewall-policy-hitcount")
    def fw_sessions(self): return self._get("monitor/router/firewall")
    def multicas(self): return self._get("monitor/router/multicast")

    # ====================
    # LOGS
    # ====================
    def event_logs(self): return self._get("monitor/log/event")
    def traffic_logs(self): return self._get("monitor/log/traffic")

    # ====================
    # DEVICE INVENTORY
    # ====================
    def device_inventory(self): return self._get("monitor/user/device/query")

    # ====================
    # PING / TRACE
    # ====================
    def ping(self, host="8.8.8.8", count=5): return self._get(f"monitor/system/diagnose?ping={host}&count={count}")
    def trace(self, host="8.8.8.8"): return self._get(f"monitor/system/diagnose?traceroute={host}")

    # ====================
    # FULL DATASET
    # ====================
    def build_dataset(self):
        return {
            "timestamp": int(time.time()),

            # WiFi
            "wifi_clients": self.wifi_clients(),
            "wifi_ssids": self.wifi_ssids(),
            "wifi_radios": self.wifi_radios(),
            "wifi_neighbors": self.wifi_neighbors(),
            "wifi_manufacturer": self.wifi_manufacturer(),
            "wifi_reputation": self.wifi_reputation(),
            "wifi_channels": self.wifi_channels(),

            # Switch
            "switch_clients": self.switch_clients(),
            "switch_ports": self.switch_ports(),
            "switch_status": self.switch_status(),
            "switch_vlans": self.switch_vlans(),
            "switch_poe": self.switch_poe(),

            # Routing
            "arp_table": self.arp_table(),
            "dhcp": self.dhcp(),
            "routing_ipv4": self.routing_ipv4(),
            "routing_neighbors": self.routing_neighbors(),
            "ospf": self.ospf(),
            "bgp": self.bgp(),
            "nexthop": self.nexthop(),

            # LLDP / Interfaces
            "lldp": self.lldp(),
            "interfaces": self.interfaces(),

            # System
            "system_status": self.system_status(),
            "cpu": self.cpu(),
            "memory": self.memory(),
            "performance": self.performance(),
            "disk": self.disk(),
            "lograte": self.lograte(),
            "sessions": self.sessions(),

            # Firewall / Security
            "fw_policy_hits": self.fw_policy_hits(),
            "fw_sessions": self.fw_sessions(),
            "multicast": self.multicas(),

            # Logs
            "event_logs": self.event_logs(),
            "traffic_logs": self.traffic_logs(),

            # Inventory
            "device_inventory": self.device_inventory(),

            # Diagnostics
            "ping_google": self.ping(),
            "trace_google": self.trace()
        }
