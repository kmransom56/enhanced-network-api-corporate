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
        wifi_host: Optional[str] = None,
        wifi_token: Optional[str] = None,
    ):
        self.host = host
        self.username = username
        self.password = password
        self.api_token = token
        self.port = port
        self.verify_ssl = verify_ssl
        self.wifi_host = wifi_host
        self.wifi_token = wifi_token
        self.base_url = f"https://{host}:{port}/api/v2/"
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self._warned_endpoints = set()
        self._use_query_token = False  # Track if we need to use access_token query param
        
        # Disable SSL warnings for self-signed certs
        if not verify_ssl:
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        
    async def authenticate(self) -> bool:
        """Authenticate with FortiGate API using token or session credentials."""
        status_url = urljoin(self.base_url, "monitor/system/status")
        params = {'vdom': 'root'}

        try:
            # Attempt API token authentication first (try multiple formats)
            if self.api_token:
                # Try 1: Standard Bearer token
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

                # Try 2: Bearer with FG_API_KEY= prefix
                if not self.api_token.startswith('FG_API_KEY='):
                    bearer_headers_fg = {
                        'Authorization': f'Bearer FG_API_KEY={self.api_token}',
                        'Content-Type': 'application/json',
                    }
                    response = self.session.get(
                        status_url,
                        headers=bearer_headers_fg,
                        params=params,
                        timeout=10,
                    )
                    if response.status_code == 200:
                        logger.info("✅ Authenticated with FortiGate using Bearer FG_API_KEY token")
                        self.session.headers.update(bearer_headers_fg)
                        return True

                # Try 3: X-API-Key header
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
                
                # Try 4: Access token as query parameter
                params_with_token = params.copy()
                params_with_token['access_token'] = self.api_token
                response = self.session.get(
                    status_url,
                    headers={'Content-Type': 'application/json'},
                    params=params_with_token,
                    timeout=10,
                )
                if response.status_code == 200:
                    logger.info("✅ Authenticated with FortiGate using access_token query parameter")
                    # Store token for future requests
                    self.session.headers.update({'Content-Type': 'application/json'})
                    # Note: We'll need to add access_token to each request
                    self._use_query_token = True
                    return True

            # Fall back to session-based authentication if a password is provided
            if self.password:
                if self._session_login():
                    # Even if CSRF token extraction failed, try to continue - some endpoints work without it
                    csrf = self._extract_csrf()
                    if csrf:
                        self.session.headers.update({"X-CSRFTOKEN": csrf})
                        logger.info("✅ Authenticated with FortiGate using session login (with CSRF token)")
                    else:
                        logger.warning("⚠️  Session login succeeded but CSRF token not found - continuing anyway")
                        logger.info("✅ Authenticated with FortiGate using session login (no CSRF token)")
                    return True

            logger.error("❌ FortiGate authentication failed: token and session methods exhausted")
            return False

        except Exception as exc:
            logger.error(f"❌ Authentication error: {exc}")
            return False
    
    def _extract_csrf(self) -> Optional[str]:
        """Extract CSRF token from cookies or response headers"""
        # Try cookies first
        for cookie in self.session.cookies:
            name = cookie.name.lower()
            if name.startswith("ccsrf") or name == "csrftoken" or "csrf" in name:
                value = cookie.value.strip('"').strip("'")
                if value:
                    logger.debug(f"Found CSRF token in cookie: {name}")
                    return value
        
        # Try response headers if available
        if hasattr(self.session, 'last_response') and self.session.last_response:
            csrf_header = self.session.last_response.headers.get('X-CSRFTOKEN') or \
                         self.session.last_response.headers.get('X-CSRFToken') or \
                         self.session.last_response.headers.get('Csrf-Token')
            if csrf_header:
                logger.debug("Found CSRF token in response header")
                return csrf_header
        
        logger.warning("CSRF token not found in cookies or headers")
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

        # Store response for CSRF extraction
        self.session.last_response = response
        
        csrf = self._extract_csrf()
        if not csrf:
            # Try Set-Cookie header as fallback
            set_cookie = response.headers.get("Set-Cookie", "")
            for part in set_cookie.split(";"):
                if "ccsrf" in part.lower() or "csrf" in part.lower():
                    _, _, value = part.partition("=")
                    csrf = value.strip().strip('"').strip("'")
                    if csrf:
                        logger.debug("Found CSRF token in Set-Cookie header")
                        break

        # Update session headers - include CSRF if found, but continue even without it
        headers_to_update = {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
        }
        if csrf:
            headers_to_update["X-CSRFTOKEN"] = csrf
            logger.debug("CSRF token added to session headers")
        else:
            logger.warning("⚠️  CSRF token not found, but continuing - some endpoints may work without it")
        
        self.session.headers.update(headers_to_update)
        return True  # Return True even without CSRF - let the API calls determine if it's needed

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

    async def get_connected_devices(self) -> List[Dict[str, Any]]:
        """Get list of connected devices (users/hosts) from multiple API endpoints.
        
        Tries endpoints in this order:
        1. Wireless clients: /api/v2/monitor/wifi/client (for devices connected to FortiAPs)
        2. Switch clients: /api/v2/monitor/switch-controller/managed-switch/clients (for wired devices)
        3. User device endpoints: /api/v2/monitor/user/device/query, /select, /registered_ems
        """
        # Ensure we're authenticated before making requests
        if not await self.authenticate():
            logger.error("Cannot fetch connected devices: authentication failed")
            return []
        
        devices: List[Dict[str, Any]] = []
        
        logger.info("Fetching connected devices from FortiGate API endpoints...")
        
        # 1. Try wireless clients endpoint (matches the WiFi client table in web UI)
        try:
            url = urljoin(self.base_url, "monitor/wifi/client")
            logger.info(f"Trying endpoint: /api/v2/monitor/wifi/client")
            params = {"vdom": "root"}
            # Add access_token to query if that's how we authenticated
            if self._use_query_token and self.api_token:
                params["access_token"] = self.api_token
            response = self.session.get(url, params=params, timeout=10)
            
            # If we get 401, try to re-authenticate and retry once
            if response.status_code == 401:
                logger.warning("Got 401 from wifi/client, attempting re-authentication...")
                if await self.authenticate():
                    response = self.session.get(url, params={"vdom": "root"}, timeout=10)
                else:
                    logger.error("Re-authentication failed, skipping wifi/client endpoint")
            
            logger.info(f"Response status: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.debug(f"Response data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                    results = data.get('results') or data.get('data') or []
                    if isinstance(results, dict):
                        results = results.get("entries", [])
                    if isinstance(results, list):
                        logger.info(f"Found {len(results)} wireless clients from wifi/client endpoint")
                        if len(results) > 0:
                            logger.info(f"Sample client keys: {list(results[0].keys())[:10] if results else 'N/A'}")
                            # Normalize wireless client data
                            for client in results:
                                # Extract name - prefer hostname, then host, then device, fallback to MAC
                                client_name = (
                                    client.get("hostname") or 
                                    client.get("host") or 
                                    client.get("device") or 
                                    client.get("mac") or 
                                    f"wifi-client-{len(devices)}"
                                )
                                devices.append({
                                    "id": client.get("mac") or client.get("ip") or f"wifi-{len(devices)}",
                                    "name": client_name,
                                    "type": "client",
                                    "os": client.get("os") or "Unknown",
                                    "ip": client.get("ip"),
                                    "mac": client.get("mac"),
                                    "status": "online",
                                    "connection_type": "wifi",
                                    "ssid": client.get("ssid"),
                                    "ap_sn": client.get("wtp_id") or client.get("ap_sn"),
                                    "ap_name": client.get("wtp_name") or client.get("fortiap") or client.get("ap"),
                                })
                        else:
                            logger.debug("wifi/client endpoint returned empty list")
                    else:
                        logger.debug(f"wifi/client endpoint returned non-list data: {type(results)}")
                except Exception as json_err:
                    logger.warning(f"Failed to parse JSON from wifi/client: {json_err}, response text: {response.text[:200]}")
            else:
                logger.warning(f"wifi/client endpoint returned HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            logger.warning(f"❌ Failed to fetch from wifi/client: {e}")
        
        # 2. Try switch controller clients endpoint (for wired devices on FortiSwitch)
        try:
            # First get list of managed switches
            switch_url = urljoin(self.base_url, "monitor/switch-controller/managed-switch/status")
            switch_response = self.session.get(switch_url, params={"vdom": "root"}, timeout=10)
            
            if switch_response.status_code == 200:
                switch_data = switch_response.json()
                switches = switch_data.get('results') or switch_data.get('data') or []
                if isinstance(switches, dict):
                    switches = switches.get("entries", [])
                
                # For each switch, try to get connected clients
                for switch in switches[:5]:  # Limit to first 5 switches to avoid too many requests
                    switch_id = switch.get("switch-id") or switch.get("id") or switch.get("serial")
                    if not switch_id:
                        continue
                    
                    try:
                        # Try switch clients endpoint
                        clients_url = urljoin(self.base_url, f"monitor/switch-controller/managed-switch/clients")
                        clients_response = self.session.get(clients_url, params={"switch_id": switch_id, "vdom": "root"}, timeout=10)
                        
                        if clients_response.status_code == 200:
                            clients_data = clients_response.json()
                            clients = clients_data.get('results') or clients_data.get('data') or []
                            if isinstance(clients, dict):
                                clients = clients.get("entries", [])
                            if isinstance(clients, list) and len(clients) > 0:
                                logger.info(f"✅ Found {len(clients)} wired clients on switch {switch_id}")
                                for client in clients:
                                    devices.append({
                                        "id": client.get("mac") or client.get("ip") or f"switch-{len(devices)}",
                                        "name": client.get("device") or client.get("hostname") or client.get("mac"),
                                        "type": "client",
                                        "os": client.get("os") or client.get("software_os") or "Unknown",
                                        "ip": client.get("ip") or client.get("address"),
                                        "mac": client.get("mac"),
                                        "status": client.get("status") or "online",
                                        "connection_type": "ethernet",
                                        "switch_id": switch_id,
                                        "switch_name": switch.get("name") or switch_id,
                                        "port": client.get("port"),
                                        "vlan": client.get("vlan"),
                                    })
                    except Exception as e:
                        logger.debug(f"Could not get clients for switch {switch_id}: {e}")
        except Exception as e:
            logger.warning(f"❌ Failed to fetch from switch-controller: {e}")
        
        # 3. Try user device endpoints (Assets dashboard endpoints)
        endpoints_to_try = [
            ("monitor/user/device/query", "device/query"),
            ("monitor/user/device/select", "device/select"),
            ("monitor/endpoint-control/registered_ems", "registered_ems"),
        ]
        
        for endpoint_path, endpoint_name in endpoints_to_try:
            try:
                url = urljoin(self.base_url, endpoint_path)
                logger.info(f"Trying endpoint: /api/v2/{endpoint_path}")
                params = {"vdom": "root"}
                # Add access_token to query if that's how we authenticated
                if self._use_query_token and self.api_token:
                    params["access_token"] = self.api_token
                response = self.session.get(url, params=params, timeout=10)
                
                logger.info(f"Response status for {endpoint_name}: {response.status_code}")
                
                # If we get 401, try to re-authenticate and retry once
                if response.status_code == 401:
                    logger.warning(f"Got 401 from {endpoint_name}, attempting re-authentication...")
                    if await self.authenticate():
                        response = self.session.get(url, params={"vdom": "root"}, timeout=10)
                        logger.info(f"Retry response status for {endpoint_name}: {response.status_code}")
                    else:
                        logger.error(f"Re-authentication failed, skipping {endpoint_name}")
                        continue
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.debug(f"Response from {endpoint_name} keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                        results = data.get('results') or data.get('data') or []
                        if isinstance(results, dict):
                            results = results.get("entries", [])
                        if isinstance(results, list):
                            logger.info(f"Found {len(results)} devices from {endpoint_name} endpoint")
                            if len(results) > 0:
                                logger.info(f"Sample device keys: {list(results[0].keys())[:15] if results else 'N/A'}")
                                # Normalize and add devices (avoid duplicates by MAC)
                                existing_macs = {d.get("mac") for d in devices if d.get("mac")}
                                for device in results:
                                    mac = device.get("mac")
                                    if mac and mac not in existing_macs:
                                        # Extract name - prefer name, then hostname, then host, then device, fallback to MAC
                                        device_name = (
                                            device.get("name") or 
                                            device.get("hostname") or 
                                            device.get("host") or 
                                            device.get("device") or 
                                            mac or 
                                            f"device-{len(devices)}"
                                        )
                                        devices.append({
                                            "id": mac or device.get("ip") or device.get("name") or f"device-{len(devices)}",
                                            "name": device_name,
                                            "type": "client",
                                            "os": device.get("os") or device.get("os-type") or device.get("software_os") or "Unknown",
                                            "ip": device.get("ip") or device.get("address"),
                                            "mac": mac,
                                            "status": device.get("status") or "online",
                                            "connection_type": "wifi" if device.get("ssid") else "ethernet",
                                            "ssid": device.get("ssid"),
                                            "ap_sn": device.get("ap_sn") or device.get("wtp_id"),
                                            "ap_name": device.get("wtp_name") or device.get("ap"),
                                            "switch_sn": device.get("switch_sn"),
                                            "port": device.get("port"),
                                            "vulnerabilities": device.get("vulnerabilities", 0),
                                        })
                                        existing_macs.add(mac)
                            else:
                                logger.debug(f"Endpoint {endpoint_name} returned empty list")
                        else:
                            logger.debug(f"Endpoint {endpoint_name} returned non-list data: {type(results)}")
                    except Exception as json_err:
                        logger.warning(f"Failed to parse JSON from {endpoint_name}: {json_err}, response: {response.text[:200]}")
                else:
                    logger.warning(f"Endpoint {endpoint_name} returned HTTP {response.status_code}: {response.text[:200]}")
            except Exception as e:
                logger.warning(f"Failed to fetch from {endpoint_name}: {e}")
                continue
        
        if not devices:
            logger.warning("⚠️  No connected devices found from any FortiGate endpoint")
        else:
            logger.info(f"✅ Total connected devices found: {len(devices)}")
        
        return devices
    
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
