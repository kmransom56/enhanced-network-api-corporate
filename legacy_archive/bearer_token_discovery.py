#!/usr/bin/env python3
"""
Bearer Token FortiGate API Discovery
"""

import asyncio
import aiohttp
import json
import logging

async def test_bearer_token_endpoints():
    """Test all endpoints with working Bearer token"""
    
    base_url = "https://192.168.0.254:10443"
    api_token = "f5q7tgy9tznpHwqxc5fmHtz01nh5Q0"
    
    # Comprehensive endpoint list
    endpoints = [
        # System endpoints (we know this works)
        "/api/v2/monitor/system/status",
        "/api/v2/monitor/system/resource/usage",
        "/api/v2/monitor/system/interface",
        "/api/v2/monitor/system/hardware-status",
        "/api/v2/cmdb/system/global",
        "/api/v2/cmdb/system/interface",
        
        # Switch Controller endpoints
        "/api/v2/monitor/switch-controller/managed-switch",
        "/api/v2/monitor/switch-controller/managed-switches",
        "/api/v2/monitor/switch-controller/status",
        "/api/v2/monitor/switch-controller/switch-status",
        "/api/v2/monitor/switch/managed-switch",
        "/api/v2/monitor/switch/managed-switches",
        "/api/v2/monitor/switch/status",
        "/api/v2/cmdb/switch-controller/managed-switch",
        "/api/v2/cmdb/switch-controller/managed-switches",
        "/api/v2/cmdb/switch/managed-switch",
        "/api/v2/cmdb/switch/managed-switches",
        
        # Wireless Controller endpoints
        "/api/v2/monitor/wireless-controller/managed-ap",
        "/api/v2/monitor/wireless-controller/managed-aps",
        "/api/v2/monitor/wireless-controller/ap-status",
        "/api/v2/monitor/wireless-controller/access-point",
        "/api/v2/monitor/wireless-controller/access-points",
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
        
        # Device and client endpoints
        "/api/v2/monitor/device/inventory",
        "/api/v2/monitor/device/list",
        "/api/v2/monitor/device/connected",
        "/api/v2/monitor/device/clients",
        "/api/v2/monitor/endpoint/list",
        "/api/v2/monitor/endpoint/clients",
        "/api/v2/monitor/client/list",
        "/api/v2/monitor/client/connected",
        "/api/v2/monitor/user/device",
        
        # Network endpoints
        "/api/v2/monitor/network/interface",
        "/api/v2/monitor/network/topology",
        "/api/v2/monitor/network/map",
        "/api/v2/monitor/network/connections",
        "/api/v2/monitor/topology/map",
        "/api/v2/monitor/topology/devices",
        
        # DHCP endpoints
        "/api/v2/monitor/dhcp/server/lease",
        "/api/v2/monitor/dhcp/lease",
        "/api/v2/monitor/dhcp/server",
        
        # VLAN endpoints
        "/api/v2/monitor/interface/vlan",
        "/api/v2/monitor/vlan/available",
        "/api/v2/cmdb/system/vlan",
        
        # FortiLink endpoints
        "/api/v2/monitor/fortilink/status",
        "/api/v2/monitor/fortilink/switches",
        "/api/v2/monitor/fortilink/devices",
        
        # Log and traffic endpoints
        "/api/v2/monitor/log/traffic",
        "/api/v2/monitor/log/event",
        "/api/v2/monitor/traffic/select",
        
        # License and feature endpoints
        "/api/v2/monitor/license/status",
        "/api/v2/monitor/feature/select",
        
        # Alternative endpoint patterns
        "/api/v2/monitor/system/status/summary",
        "/api/v2/monitor/system/fortiguard",
        "/api/v2/monitor/fortiswitch",
        "/api/v2/monitor/fortiap",
        "/api/v2/monitor/wifi",
        "/api/v2/monitor/switch",
    ]
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    results = {
        'working_endpoints': [],
        'switch_endpoints': [],
        'ap_endpoints': [],
        'device_endpoints': [],
        'errors': []
    }
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=10)
    ) as session:
        
        print(f"🔑 Testing {len(endpoints)} endpoints with Bearer token...")
        print(f"🌐 Base URL: {base_url}")
        
        for i, endpoint in enumerate(endpoints, 1):
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.get(url, headers=headers) as response:
                    status = response.status
                    
                    print(f"[{i:3d}/{len(endpoints)}] {status:3d} {endpoint[:50]:<50} ", end="")
                    
                    if status == 200:
                        try:
                            data = await response.json()
                            
                            # Check for device data
                            data_str = json.dumps(data).lower()
                            has_switches = any(keyword in data_str for keyword in ['switch', 'fortiswitch', 'fsw'])
                            has_aps = any(keyword in data_str for keyword in ['ap', 'fortiap', 'fap', 'wifi'])
                            has_devices = any(keyword in data_str for keyword in ['device', 'client', 'endpoint'])
                            
                            device_count = 0
                            if 'data' in data and isinstance(data['data'], list):
                                device_count = len(data['data'])
                            
                            results['working_endpoints'].append({
                                'endpoint': endpoint,
                                'status': status,
                                'data': data,
                                'device_count': device_count,
                                'has_switches': has_switches,
                                'has_aps': has_aps,
                                'has_devices': has_devices
                            })
                            
                            if has_switches:
                                results['switch_endpoints'].append(endpoint)
                                print(f"✅ SWITCHES ({device_count} devices)")
                            elif has_aps:
                                results['ap_endpoints'].append(endpoint)
                                print(f"✅ APs ({device_count} devices)")
                            elif has_devices:
                                results['device_endpoints'].append(endpoint)
                                print(f"✅ DEVICES ({device_count} devices)")
                            else:
                                print(f"✅ OK ({len(str(data))} bytes)")
                                
                        except json.JSONDecodeError:
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
                        
                        # Log error
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
    print(f"\n🎯 BEARER TOKEN DISCOVERY SUMMARY:")
    print(f"  ✅ Working endpoints: {len(results['working_endpoints'])}")
    print(f"  🔌 Switch endpoints: {len(results['switch_endpoints'])}")
    print(f"  📶 AP endpoints: {len(results['ap_endpoints'])}")
    print(f"  📱 Device endpoints: {len(results['device_endpoints'])}")
    print(f"  ❌ Errors: {len(results['errors'])}")
    
    # Show promising endpoints with device counts
    print(f"\n🔍 ENDPOINTS WITH DEVICES:")
    for result in results['working_endpoints']:
        if result['device_count'] > 0:
            device_type = []
            if result['has_switches']: device_type.append("SWITCH")
            if result['has_aps']: device_type.append("AP")
            if result['has_devices']: device_type.append("DEVICE")
            
            print(f"  🔌 {result['endpoint']}: {result['device_count']} devices ({', '.join(device_type)})")
            
            # Show sample device data
            try:
                if 'data' in result['data'] and isinstance(result['data']['data'], list):
                    for device in result['data']['data'][:2]:  # Show first 2
                        print(f"    📋 {str(device)[:80]}...")
            except:
                pass
    
    # Show all working endpoints for reference
    print(f"\n📋 ALL WORKING ENDPOINTS:")
    for result in results['working_endpoints']:
        status_info = f"({result['device_count']} devices)" if result['device_count'] > 0 else "(no devices)"
        print(f"  ✅ {result['endpoint']} {status_info}")
    
    # Save results
    with open("fortigate_bearer_discovery.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to fortigate_bearer_discovery.json")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(test_bearer_token_endpoints())
