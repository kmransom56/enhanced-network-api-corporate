#!/usr/bin/env python3
"""
Complete FortiGate Device Discovery
Uses working endpoints to find all connected devices
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any

async def complete_fortigate_discovery():
    """Complete discovery using working endpoints"""
    
    base_url = "https://192.168.0.254:10443"
    api_token = "7H8p0ykg0pc3szHxHcQ80xd5p798yh"
    
    # Working endpoints from our discovery
    endpoints = [
        "/api/v2/monitor/system/status",
        "/api/v2/monitor/system/resource/usage", 
        "/api/v2/monitor/system/interface",
        "/api/v2/cmdb/system/global",
        "/api/v2/cmdb/system/interface",
        "/api/v2/cmdb/switch-controller/managed-switch",
        "/api/v2/monitor/license/status",
    ]
    
    # Additional endpoints to try for AP discovery
    additional_endpoints = [
        # Try different AP endpoint patterns
        "/api/v2/monitor/wireless-controller/managed-ap",
        "/api/v2/monitor/wifi/managed-ap",
        "/api/v2/cmdb/wireless-controller/managed-ap",
        "/api/v2/cmdb/wifi/managed-ap",
        
        # Client/device discovery
        "/api/v2/monitor/user/device",
        "/api/v2/monitor/dhcp/server/lease",
        
        # Interface details (might show connected devices)
        "/api/v2/monitor/interface/vlan",
    ]
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    discovered_devices = {
        'gateways': [],
        'switches': [],
        'aps': [],
        'clients': [],
        'interfaces': []
    }
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=15)
    ) as session:
        
        print(f"🔍 Complete FortiGate Discovery")
        print(f"🌐 Base URL: {base_url}")
        
        # Test working endpoints first
        for endpoint in endpoints + additional_endpoints:
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.get(url, headers=headers) as response:
                    print(f"[{response.status:3d}] {endpoint[:50]:<50} ", end="")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse different endpoint types
                        if endpoint == "/api/v2/monitor/system/status":
                            gateway = parse_gateway(data)
                            if gateway:
                                discovered_devices['gateways'].append(gateway)
                                print(f"✅ GATEWAY: {gateway['name']}")
                        
                        elif endpoint == "/api/v2/cmdb/switch-controller/managed-switch":
                            switches = parse_switches(data)
                            discovered_devices['switches'].extend(switches)
                            print(f"✅ SWITCHES: {len(switches)} found")
                            for switch in switches:
                                print(f"    🔌 {switch['name']} ({switch['model']})")
                        
                        elif endpoint == "/api/v2/monitor/system/interface":
                            interfaces = parse_interfaces(data)
                            discovered_devices['interfaces'].extend(interfaces)
                            print(f"✅ INTERFACES: {len(interfaces)} found")
                        
                        elif endpoint == "/api/v2/monitor/license/status":
                            # Check for wireless/AP licenses
                            licenses = parse_licenses(data)
                            if licenses.get('wireless'):
                                print(f"✅ LICENSES: Wireless controller available")
                            else:
                                print(f"✅ LICENSES: No wireless controller license")
                        
                        elif any(keyword in endpoint for keyword in ['ap', 'wifi', 'wireless']):
                            aps = parse_aps(data)
                            if aps:
                                discovered_devices['aps'].extend(aps)
                                print(f"✅ APs: {len(aps)} found")
                                for ap in aps:
                                    print(f"    📶 {ap['name']} ({ap['model']})")
                            else:
                                print("✅ APs: None found")
                        
                        elif any(keyword in endpoint for keyword in ['client', 'user', 'dhcp']):
                            clients = parse_clients(data)
                            if clients:
                                discovered_devices['clients'].extend(clients)
                                print(f"✅ CLIENTS: {len(clients)} found")
                            else:
                                print("✅ CLIENTS: None found")
                        
                        else:
                            print(f"✅ OK ({len(str(data))} bytes)")
                    
                    else:
                        print(f"❌ ERROR {response.status}")
                        
            except Exception as e:
                print(f"❌ EXCEPTION: {str(e)[:30]}")
    
    # Summary
    print(f"\n🎯 COMPLETE DISCOVERY SUMMARY:")
    print(f"  📡 Gateways: {len(discovered_devices['gateways'])}")
    print(f"  🔌 Switches: {len(discovered_devices['switches'])}")
    print(f"  📶 APs: {len(discovered_devices['aps'])}")
    print(f"  👥 Clients: {len(discovered_devices['clients'])}")
    print(f"  🔌 Interfaces: {len(discovered_devices['interfaces'])}")
    
    # Detailed device information
    if discovered_devices['gateways']:
        print(f"\n📡 GATEWAY DETAILS:")
        for gateway in discovered_devices['gateways']:
            print(f"  🏢 {gateway['name']} ({gateway['model']})")
            print(f"     IP: {gateway['ip']}")
            print(f"     Serial: {gateway['serial']}")
            print(f"     Version: {gateway['version']}")
    
    if discovered_devices['switches']:
        print(f"\n🔌 SWITCH DETAILS:")
        for switch in discovered_devices['switches']:
            print(f"  🔌 {switch['name']} ({switch['model']})")
            print(f"     Serial: {switch['serial']}")
            print(f"     IP: {switch['ip']}")
            print(f"     Status: {switch['status']}")
            print(f"     Profile: {switch.get('profile', 'N/A')}")
    
    if discovered_devices['aps']:
        print(f"\n📶 AP DETAILS:")
        for ap in discovered_devices['aps']:
            print(f"  📶 {ap['name']} ({ap['model']})")
            print(f"     Serial: {ap['serial']}")
            print(f"     IP: {ap['ip']}")
            print(f"     Status: {ap['status']}")
    
    if discovered_devices['clients']:
        print(f"\n👥 CLIENT DETAILS:")
        for client in discovered_devices['clients'][:5]:  # Show first 5
            print(f"  👤 {client['name']} ({client.get('ip', 'N/A')})")
    
    # Save complete results
    with open("complete_fortigate_discovery.json", "w") as f:
        json.dump(discovered_devices, f, indent=2)
    
    print(f"\n📄 Complete results saved to complete_fortigate_discovery.json")
    
    return discovered_devices

def parse_gateway(data: Dict) -> Dict:
    """Parse gateway information from system status"""
    try:
        results = data.get('results', {})
        return {
            'id': f"fg-{results.get('serial', 'unknown')}",
            'name': results.get('hostname', 'FortiGate'),
            'ip': '192.168.0.254',
            'model': results.get('model', 'FortiGate'),
            'serial': results.get('serial', ''),
            'version': results.get('version', ''),
            'status': 'online',
            'type': 'fortigate'
        }
    except:
        return None

def parse_switches(data: Dict) -> List[Dict]:
    """Parse switch information from managed-switch endpoint"""
    switches = []
    try:
        results = data.get('results', [])
        for switch in results:
            switches.append({
                'id': f"fsw-{switch.get('switch-id', switch.get('sn', 'unknown'))}",
                'name': switch.get('switch-id', 'Unknown Switch'),
                'serial': switch.get('sn', ''),
                'model': 'FortiSwitch',  # Model not in response, would need additional query
                'ip': '',  # IP not in this response
                'status': 'online',  # Assume online if in managed list
                'profile': switch.get('switch-profile', 'default'),
                'access_profile': switch.get('access-profile', 'default'),
                'description': switch.get('description', ''),
                'type': 'fortiswitch',
                'raw_data': switch
            })
    except Exception as e:
        print(f"Error parsing switches: {e}")
    
    return switches

def parse_aps(data: Dict) -> List[Dict]:
    """Parse AP information from managed-ap endpoint"""
    aps = []
    try:
        results = data.get('results', data.get('data', []))
        for ap in results:
            aps.append({
                'id': f"fap-{ap.get('wtp-id', ap.get('serial', ap.get('name', 'unknown')))}",
                'name': ap.get('name', 'Unknown AP'),
                'serial': ap.get('serial', ''),
                'model': ap.get('model', 'FortiAP'),
                'ip': ap.get('ip', ''),
                'status': ap.get('status', 'unknown'),
                'type': 'fortiap',
                'raw_data': ap
            })
    except:
        pass
    
    return aps

def parse_clients(data: Dict) -> List[Dict]:
    """Parse client information"""
    clients = []
    try:
        results = data.get('results', data.get('data', []))
        for client in results:
            clients.append({
                'id': f"client-{client.get('mac', client.get('ip', 'unknown'))}",
                'name': client.get('hostname', client.get('name', 'Unknown Client')),
                'ip': client.get('ip', ''),
                'mac': client.get('mac', ''),
                'type': 'client',
                'raw_data': client
            })
    except:
        pass
    
    return clients

def parse_interfaces(data: Dict) -> List[Dict]:
    """Parse interface information"""
    interfaces = []
    try:
        results = data.get('results', data.get('data', []))
        for interface in results:
            interfaces.append({
                'name': interface.get('name', 'Unknown'),
                'ip': interface.get('ip', ''),
                'status': interface.get('status', 'unknown'),
                'type': interface.get('type', 'unknown'),
                'raw_data': interface
            })
    except:
        pass
    
    return interfaces

def parse_licenses(data: Dict) -> Dict:
    """Parse license information"""
    licenses = {}
    try:
        results = data.get('results', {})
        # Look for wireless controller license
        for license_entry in results:
            if 'wireless' in str(license_entry).lower():
                licenses['wireless'] = True
                break
    except:
        pass
    
    return licenses

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(complete_fortigate_discovery())
