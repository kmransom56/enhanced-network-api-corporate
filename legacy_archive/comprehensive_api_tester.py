#!/usr/bin/env python3
"""
Comprehensive FortiGate API Endpoint Tester
Tests all possible endpoints for device discovery
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any

async def test_all_fortigate_endpoints():
    """Test comprehensive list of FortiGate API endpoints"""
    
    base_url = "https://192.168.0.254:10443"
    api_token = "7H8p0ykg0pc3szHxHcQ80xd5p798yh"
    
    # Comprehensive endpoint list for FortiOS 7.6.4
    endpoints = [
        # System endpoints
        "/api/v2/monitor/system/status",
        "/api/v2/monitor/system/resource/usage",
        "/api/v2/monitor/system/interface",
        "/api/v2/cmdb/system/global",
        
        # Switch Controller endpoints (all variations)
        "/api/v2/monitor/switch-controller/managed-switch",
        "/api/v2/monitor/switch-controller/managed-switches", 
        "/api/v2/monitor/switch-controller/switch-status",
        "/api/v2/monitor/switch/managed-switch",
        "/api/v2/monitor/switch/managed-switches",
        "/api/v2/cmdb/switch-controller/managed-switch",
        "/api/v2/cmdb/switch-controller/managed-switches",
        "/api/v2/cmdb/switch/managed-switch",
        "/api/v2/cmdb/switch/managed-switches",
        "/api/v2/monitor/switch-controller/status",
        "/api/v2/monitor/switch-controller/fortiswitch",
        
        # Wireless Controller endpoints (all variations)
        "/api/v2/monitor/wireless-controller/managed-ap",
        "/api/v2/monitor/wireless-controller/managed-aps",
        "/api/v2/monitor/wireless-controller/ap-status",
        "/api/v2/monitor/wifi/managed-ap",
        "/api/v2/monitor/wifi/managed-aps",
        "/api/v2/monitor/wifi/ap-status",
        "/api/v2/monitor/wireless/managed-ap",
        "/api/v2/monitor/wireless/managed-aps",
        "/api/v2/cmdb/wireless-controller/managed-ap",
        "/api/v2/cmdb/wireless-controller/managed-aps",
        "/api/v2/cmdb/wifi/managed-ap", 
        "/api/v2/cmdb/wifi/managed-aps",
        "/api/v2/cmdb/wireless/managed-ap",
        "/api/v2/cmdb/wireless/managed-aps",
        "/api/v2/monitor/wireless-controller/access-point",
        "/api/v2/monitor/wireless-controller/access-points",
        
        # Device inventory endpoints
        "/api/v2/monitor/device/inventory",
        "/api/v2/monitor/device/list",
        "/api/v2/monitor/device/connected",
        "/api/v2/monitor/device/clients",
        "/api/v2/monitor/endpoint/list",
        "/api/v2/monitor/endpoint/clients",
        
        # Network topology endpoints
        "/api/v2/monitor/network/topology",
        "/api/v2/monitor/network/map",
        "/api/v2/monitor/network/connections",
        "/api/v2/monitor/topology/map",
        "/api/v2/monitor/topology/devices",
        
        # DHCP and client endpoints
        "/api/v2/monitor/dhcp/server/lease",
        "/api/v2/monitor/dhcp/lease",
        "/api/v2/monitor/client/list",
        "/api/v2/monitor/client/connected",
        
        # Interface and VLAN endpoints
        "/api/v2/monitor/interface/vlan",
        "/api/v2/monitor/vlan/available",
        "/api/v2/cmdb/system/interface",
        "/api/v2/cmdb/system/vlan",
        
        # FortiLink specific endpoints
        "/api/v2/monitor/fortilink/status",
        "/api/v2/monitor/fortilink/switches",
        "/api/v2/monitor/fortilink/devices",
        
        # Alternative endpoint patterns
        "/api/v2/cmdb/switch.controller/managed-switch",
        "/api/v2/cmdb/wireless.controller/managed-ap",
        "/api/v2/monitor/switch.controller/managed-switch",
        "/api/v2/monitor/wireless.controller/managed-ap",
        
        # Legacy endpoints
        "/api/v1/monitor/switch-controller/managed-switch",
        "/api/v1/monitor/wireless-controller/managed-ap",
        "/api/v1/cmdb/switch-controller/managed-switch",
        "/api/v1/cmdb/wireless-controller/managed-ap",
    ]
    
    results = {
        'working_endpoints': [],
        'switch_endpoints': [],
        'ap_endpoints': [],
        'device_endpoints': [],
        'errors': []
    }
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=15)
    ) as session:
        
        print(f"🔍 Testing {len(endpoints)} FortiGate API endpoints...")
        print(f"🌐 Base URL: {base_url}")
        
        for i, endpoint in enumerate(endpoints, 1):
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.get(url, headers=headers) as response:
                    status = response.status
                    content_type = response.headers.get('content-type', '')
                    
                    print(f"[{i:3d}/{len(endpoints)}] {status:3d} {endpoint[:50]:<50} ", end="")
                    
                    if status == 200:
                        try:
                            data = await response.json()
                            
                            # Check if it contains device data
                            data_str = json.dumps(data, casefold=True)
                            has_switches = any(keyword in data_str for keyword in ['switch', 'fortiswitch', 'fsw'])
                            has_aps = any(keyword in data_str for keyword in ['ap', 'fortiap', 'fap', 'wifi'])
                            has_devices = any(keyword in data_str for keyword in ['device', 'client', 'endpoint'])
                            
                            results['working_endpoints'].append({
                                'endpoint': endpoint,
                                'status': status,
                                'data': data,
                                'has_switches': has_switches,
                                'has_aps': has_aps,
                                'has_devices': has_devices
                            })
                            
                            if has_switches:
                                results['switch_endpoints'].append(endpoint)
                                print(f"✅ SWITCHES ({len(str(data))} bytes)")
                            elif has_aps:
                                results['ap_endpoints'].append(endpoint)
                                print(f"✅ APs ({len(str(data))} bytes)")
                            elif has_devices:
                                results['device_endpoints'].append(endpoint)
                                print(f"✅ DEVICES ({len(str(data))} bytes)")
                            else:
                                print(f"✅ OK ({len(str(data))} bytes)")
                                
                        except json.JSONDecodeError:
                            # Try text response
                            text = await response.text()
                            print(f"✅ TEXT ({len(text)} chars)")
                            
                    elif status == 401:
                        print("❌ UNAUTHORIZED")
                    elif status == 403:
                        print("❌ FORBIDDEN")
                    elif status == 404:
                        print("❌ NOT FOUND")
                    elif status == 400:
                        print("❌ BAD REQUEST")
                    else:
                        print(f"❌ ERROR {status}")
                        
                        # Log error for debugging
                        try:
                            error_text = await response.text()
                            results['errors'].append({
                                'endpoint': endpoint,
                                'status': status,
                                'error': error_text[:200]
                            })
                        except:
                            pass
                        
            except asyncio.TimeoutError:
                print(f"⏰ TIMEOUT")
            except Exception as e:
                print(f"❌ EXCEPTION: {str(e)[:30]}")
                results['errors'].append({
                    'endpoint': endpoint,
                    'error': str(e)
                })
    
    # Summary
    print(f"\n🎯 API DISCOVERY SUMMARY:")
    print(f"  ✅ Working endpoints: {len(results['working_endpoints'])}")
    print(f"  🔌 Switch endpoints: {len(results['switch_endpoints'])}")
    print(f"  📶 AP endpoints: {len(results['ap_endpoints'])}")
    print(f"  📱 Device endpoints: {len(results['device_endpoints'])}")
    print(f"  ❌ Errors: {len(results['errors'])}")
    
    # Show promising endpoints
    if results['switch_endpoints']:
        print(f"\n🔌 PROMISING SWITCH ENDPOINTS:")
        for endpoint in results['switch_endpoints']:
            print(f"  {endpoint}")
    
    if results['ap_endpoints']:
        print(f"\n📶 PROMISING AP ENDPOINTS:")
        for endpoint in results['ap_endpoints']:
            print(f"  {endpoint}")
    
    if results['device_endpoints']:
        print(f"\n📱 PROMISING DEVICE ENDPOINTS:")
        for endpoint in results['device_endpoints']:
            print(f"  {endpoint}")
    
    # Save detailed results
    with open("fortigate_api_discovery.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to fortigate_api_discovery.json")
    
    # Show sample data from working endpoints
    print(f"\n📊 SAMPLE DATA FROM WORKING ENDPOINTS:")
    for result in results['working_endpoints'][:5]:  # Show first 5
        if result['has_switches'] or result['has_aps'] or result['has_devices']:
            print(f"\n🔍 {result['endpoint']}:")
            try:
                # Extract sample device data
                data = result['data']
                if isinstance(data, dict):
                    if 'data' in data and isinstance(data['data'], list):
                        sample_devices = data['data'][:2]  # Show first 2 devices
                        for device in sample_devices:
                            print(f"  📋 {str(device)[:100]}...")
                    elif isinstance(data, list):
                        sample_devices = data[:2]
                        for device in sample_devices:
                            print(f"  📋 {str(device)[:100]}...")
            except:
                pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    asyncio.run(test_all_fortigate_endpoints())
