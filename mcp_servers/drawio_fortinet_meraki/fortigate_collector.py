#!/usr/bin/env python3
"""
FortiGate-specific topology collector for MCP integration
Works with your existing FortiGate at 192.168.0.254
"""

import asyncio
import json
import logging
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

@dataclass
class FortiGateDevice:
    """Represents a FortiGate device and its configuration"""
    id: str
    name: str
    model: str
    serial: str
    ip: str
    status: str
    version: str
    interfaces: List[Dict]
    vips: List[Dict]
    firewall_policies: int
    cpu_usage: float
    memory_usage: float
    connections: int

@dataclass
class FortiGateInterface:
    """Network interface configuration"""
    name: str
    ip: str
    netmask: str
    status: str
    speed: str
    mtu: int
    connected_devices: List[str]

class FortiGateTopologyCollector:
    """Collects topology data directly from FortiGate API"""
    
    def __init__(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        token: Optional[str] = None,
        port: int = 10443,
        verify_ssl: bool = False,
    ):
        self.host = host
        self.username = username
        self.password = password
        self.api_token = token
        self.port = port
        self.verify_ssl = verify_ssl
        self.base_url = f"https://{host}:{port}/api/v2/"
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self._warned_endpoints = set()
        
        # Disable SSL warnings for self-signed certs
        if not verify_ssl:
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        
    async def authenticate(self) -> bool:
        """Authenticate with FortiGate API using token or session credentials."""
        status_url = urljoin(self.base_url, "monitor/system/status")
        params = {'vdom': 'root'}

        try:
            # Attempt API token authentication first (Bearer and X-API-Key)
            if self.api_token:
                bearer_headers = {
                    'Authorization': f'Bearer {self.api_token}',
                    'Content-Type': 'application/json',
                }
                response = self.session.get(
                    status_url,
                    headers=bearer_headers,
                    params=params,
                    timeout=10,
                )
                if response.status_code == 200:
                    logger.info("✅ Authenticated with FortiGate using Bearer token")
                    self.session.headers.update(bearer_headers)
                    return True

                alt_headers = {
                    'X-API-Key': self.api_token,
                    'Content-Type': 'application/json',
                }
                response = self.session.get(
                    status_url,
                    headers=alt_headers,
                    params=params,
                    timeout=10,
                )
                if response.status_code == 200:
                    logger.info("✅ Authenticated with FortiGate using X-API-Key header")
                    self.session.headers.update(alt_headers)
                    return True

            # Fall back to session-based authentication if a password is provided
            if self.password:
                if self._session_login():
                    logger.info("✅ Authenticated with FortiGate using session login")
                    return True

            logger.error("❌ FortiGate authentication failed: token and session methods exhausted")
            return False

        except Exception as exc:
            logger.error(f"❌ Authentication error: {exc}")
            return False
    
    def _extract_csrf(self) -> Optional[str]:
        for cookie in self.session.cookies:
            name = cookie.name.lower()
            if name.startswith("ccsrf") or name == "csrftoken":
                value = cookie.value.strip('"')
                if value:
                    return value
        return None

    def _session_login(self) -> bool:
        login_base = f"https://{self.host}:{self.port}"
        try:
            self.session.get(f"{login_base}/login", timeout=10)
        except requests.RequestException as exc:
            logger.error(f"Session login initial GET failed: {exc}")
            return False

        json_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Referer": f"{login_base}/login",
        }
        payload = {"username": self.username, "password": self.password}

        try:
            response = self.session.post(
                f"{login_base}/api/v2/authentication",
                json=payload,
                headers=json_headers,
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error(f"Session authentication POST failed: {exc}")
            return False

        csrf = self._extract_csrf()
        if not csrf:
            set_cookie = response.headers.get("Set-Cookie", "")
            for part in set_cookie.split(";"):
                if "ccsrf" in part.lower():
                    _, _, value = part.partition("=")
                    csrf = value.strip().strip('"')
                    if csrf:
                        break

        if not csrf:
            logger.error("Session authentication succeeded but CSRF token could not be determined")
            return False

        self.session.headers.update(
            {
                "X-CSRFTOKEN": csrf,
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/plain, */*",
            }
        )
        return True

    def _log_warning_once(self, endpoint: str, message: str):
        """Log a warning only the first time it occurs for an endpoint."""
        if endpoint not in self._warned_endpoints:
            logger.warning(message)
            self._warned_endpoints.add(endpoint)

    async def get_system_status(self) -> Dict[str, Any]:
        """Get FortiGate system status"""
        try:
            url = urljoin(self.base_url, "monitor/system/status")
            response = self.session.get(url, params={"vdom": "root"}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results')
                if isinstance(results, list) and results:
                    return results[0]
                return data
            else:
                self._log_warning_once(
                    "system_status",
                    f"FortiGate rejected system status request ({response.status_code})"
                )
                return {}
                
        except Exception as e:
            self._log_warning_once("system_status_error", f"Error getting system status: {e}")
            return {}
    
    async def get_interfaces(self) -> List[Dict[str, Any]]:
        """Get network interface configuration"""
        try:
            url = urljoin(self.base_url, "cmdb/system/interface")
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                interfaces = data.get('results', [])
                
                # Filter out internal interfaces
                active_interfaces = []
                for iface in interfaces:
                    if iface.get('status') == 'up' and not iface.get('alias', '').startswith('internal'):
                        active_interfaces.append({
                            'name': iface.get('name', ''),
                            'ip': iface.get('ip', ''),
                            'netmask': iface.get('subnet', ''),
                            'status': iface.get('status', 'unknown'),
                            'speed': iface.get('speed', ''),
                            'mtu': iface.get('mtu', 1500),
                            'type': iface.get('type', 'physical')
                        })
                
                return active_interfaces
            else:
                logger.error(f"Failed to get interfaces: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting interfaces: {e}")
            return []
    
    async def get_vip_configuration(self) -> List[Dict[str, Any]]:
        """Get VIP (Virtual IP) configuration"""
        try:
            url = urljoin(self.base_url, "cmdb/firewall/vip")
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            else:
                logger.error(f"Failed to get VIPs: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting VIPs: {e}")
            return []
    
    async def get_firewall_policies_count(self) -> int:
        """Get count of firewall policies"""
        try:
            url = urljoin(self.base_url, "cmdb/firewall/policy")
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return len(data.get('results', []))
            else:
                logger.error(f"Failed to get firewall policies: {response.status_code}")
                return 0
                
        except Exception as e:
            logger.error(f"Error getting firewall policies: {e}")
            return 0
    
    async def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics (CPU, memory, connections)"""
        try:
            # Get system resource usage
            url = urljoin(self.base_url, "monitor/system/resource/usage")
            response = self.session.get(url, params={"vdom": "root"}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', {})

                def current_value(section, default=0.0):
                    if isinstance(section, list) and section:
                        current = section[0].get('current')
                        if current is not None:
                            try:
                                return float(current)
                            except (TypeError, ValueError):
                                return default
                    return default

                cpu_usage = current_value(results.get('cpu'))
                memory_usage = current_value(results.get('mem'))
                session_current = current_value(results.get('session'), default=0.0)

                return {
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'connections': int(session_current)
                }
            
            self._log_warning_once(
                "performance_metrics",
                f"FortiGate rejected performance metrics request ({response.status_code})"
            )
            return {'cpu_usage': 0.0, 'memory_usage': 0.0, 'connections': 0}
            
        except Exception as e:
            self._log_warning_once("performance_metrics_error", f"Error getting performance metrics: {e}")
            return {'cpu_usage': 0.0, 'memory_usage': 0.0, 'connections': 0}
    
    async def collect_topology(self) -> Dict[str, Any]:
        """Collect complete FortiGate topology"""
        logger.info(f"f0df0d Collecting FortiGate topology from {self.host}")
        
        # Authenticate
        if not await self.authenticate():
            # Do not return demo data here; surface a hard error so callers can react properly.
            raise RuntimeError(
                "FortiGate authentication failed: token and session methods exhausted. "
                "Check FORTIGATE_TOKEN / FORTIGATE_PASSWORD and FORTIGATE_HOST(S)."
            )
        
        # Collect all data
        system_status = await self.get_system_status()
        interfaces = await self.get_interfaces()
        vips = await self.get_vip_configuration()
        policy_count = await self.get_firewall_policies_count()
        performance = await self.get_performance_metrics()
        
        # Create FortiGate device
        fortigate_device = {
            "id": f"fg-{self.host.replace('.', '-')}",
            "name": f"FortiGate-{self.host}",
            "type": "fortigate",
            "ip": self.host,
            "status": "active" if system_status else "unknown",
            "model": system_status.get('model', 'Unknown'),
            "serial": system_status.get('serial', 'Unknown'),
            "version": system_status.get('version', 'Unknown'),
            "interfaces": interfaces,
            "vips": vips,
            "firewall_policies": policy_count,
            "cpu_usage": performance.get('cpu_usage', 0),
            "memory_usage": performance.get('memory_usage', 0),
            "connections": performance.get('connections', 0),
            "site": "Main"
        }
        
        # Create network topology
        devices = [fortigate_device]
        links = []
        
        # Create links for each interface
        for iface in interfaces:
            if iface['status'] == 'up' and iface['ip']:
                # Create a "network" device for each subnet
                network_id = f"network-{iface['name'].lower()}"
                network_device = {
                    "id": network_id,
                    "name": f"{iface['name']} Network",
                    "type": "network",
                    "ip": iface['ip'],
                    "status": "active",
                    "subnet": iface['netmask'],
                    "site": "Main"
                }
                devices.append(network_device)
                
                # Create link between FortiGate and network
                link = {
                    "source_id": fortigate_device["id"],
                    "target_id": network_id,
                    "source_interface": iface['name'],
                    "target_interface": "network",
                    "link_type": "physical",
                    "bandwidth": iface.get('speed', 'Unknown'),
                    "status": "active"
                }
                links.append(link)
        
        # Add VIPs as service endpoints
        for vip in vips[:5]:  # Limit to first 5 VIPs
            vip_device = {
                "id": f"vip-{vip.get('name', 'unknown').lower().replace(' ', '-')}",
                "name": f"VIP: {vip.get('name', 'Unknown')}",
                "type": "vip",
                "ip": vip.get('extip', ''),
                "status": "active",
                "service": vip.get('service', []),
                "site": "Main"
            }
            devices.append(vip_device)
            
            # Link VIP to external interface (usually wan1)
            link = {
                "source_id": network_id if 'network-wan1' in locals() else fortigate_device["id"],
                "target_id": vip_device["id"],
                "link_type": "service",
                "bandwidth": "VIP",
                "status": "active"
            }
            links.append(link)
        
        topology = {
            "devices": devices,
            "links": links,
            "timestamp": asyncio.get_event_loop().time(),
            "total_devices": len(devices),
            "total_links": len(links),
            "source": "fortigate_direct_api"
        }
        
        logger.info(f"✅ Collected FortiGate topology: {topology['total_devices']} devices, {topology['total_links']} links")
        return topology
    
    def get_demo_topology(self) -> Dict[str, Any]:
        """Fallback demo topology when API fails"""
        return {
            "devices": [
                {
                    "id": "fg-192-168-0-254",
                    "name": "FortiGate-Main",
                    "type": "fortigate",
                    "ip": "192.168.0.254",
                    "status": "active",
                    "model": "FG600E",
                    "serial": "FG600E321X5901234",
                    "version": "v7.4.0",
                    "interfaces": [
                        {"name": "wan1", "ip": "203.0.113.1", "status": "up", "speed": "1Gbps"},
                        {"name": "lan1", "ip": "192.168.0.254", "status": "up", "speed": "1Gbps"},
                        {"name": "dmz", "ip": "10.0.0.254", "status": "up", "speed": "1Gbps"}
                    ],
                    "firewall_policies": 25,
                    "cpu_usage": 15.2,
                    "memory_usage": 42.8,
                    "connections": 1250,
                    "site": "Main"
                },
                {
                    "id": "network-lan1",
                    "name": "LAN Network",
                    "type": "network",
                    "ip": "192.168.0.0/24",
                    "status": "active",
                    "site": "Main"
                },
                {
                    "id": "network-wan1",
                    "name": "WAN Network", 
                    "type": "network",
                    "ip": "203.0.113.0/24",
                    "status": "active",
                    "site": "Main"
                }
            ],
            "links": [
                {
                    "source_id": "fg-192-168-0-254",
                    "target_id": "network-lan1",
                    "source_interface": "lan1",
                    "target_interface": "network",
                    "link_type": "physical",
                    "bandwidth": "1Gbps",
                    "status": "active"
                },
                {
                    "source_id": "fg-192-168-0-254", 
                    "target_id": "network-wan1",
                    "source_interface": "wan1",
                    "target_interface": "network",
                    "link_type": "physical",
                    "bandwidth": "1Gbps",
                    "status": "active"
                }
            ],
            "timestamp": asyncio.get_event_loop().time(),
            "total_devices": 3,
            "total_links": 2,
            "source": "fortigate_demo"
        }

# Test function
async def test_fortigate_collector():
    """Test the FortiGate collector"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    collector = FortiGateTopologyCollector(
        host=os.getenv("FORTIMANAGER_HOST", "192.168.0.254"),
        username=os.getenv("FORTIMANAGER_USERNAME", "admin"),
        password=os.getenv("FORTIMANAGER_PASSWORD", ""),
        verify_ssl=False
    )
    
    topology = await collector.collect_topology()
    
    print("🎯 FortiGate Topology Test Results:")
    print(f"   📊 Devices: {topology['total_devices']}")
    print(f"   🔗 Links: {topology['total_links']}")
    print(f"   📡 Source: {topology['source']}")
    
    if topology['devices']:
        main_device = topology['devices'][0]
        if main_device['type'] == 'fortigate':
            print(f"   🔥 FortiGate: {main_device['name']}")
            print(f"   💻 Model: {main_device.get('model', 'Unknown')}")
            print(f"   📈 CPU: {main_device.get('cpu_usage', 0)}%")
            print(f"   🧠 Memory: {main_device.get('memory_usage', 0)}%")
            print(f"   🔌 Interfaces: {len(main_device.get('interfaces', []))}")
    
    return topology

if __name__ == "__main__":
    asyncio.run(test_fortigate_collector())
