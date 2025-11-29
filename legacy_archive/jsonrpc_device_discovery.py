#!/usr/bin/env python3
"""
JSON-RPC FortiGate Device Discovery - Test all possible endpoints
"""

import asyncio
import aiohttp
import json
import logging

async def test_jsonrpc_endpoints():
    """Test JSON-RPC endpoints for device discovery"""
    
    base_url = "https://192.168.0.254:10443"
    api_token = "f5q7tgy9tznpHwqxc5fmHtz01nh5Q0"
    
    # Comprehensive JSON-RPC endpoint list
    endpoints = [
        # System endpoints
        "/sys/status",
        "/sys/info", 
        "/sys/resource/usage",
        "/sys/interface",
        
        # Switch Controller endpoints
        "/switch-controller/managed-switch",
        "/switch-controller/managed-switches",
        "/switch-controller/status",
        "/switch-controller/switch-status",
        "/switch-controller/fortiswitch",
        "/switch/managed-switch",
        "/switch/managed-switches",
        "/switch/status",
        
        # Wireless Controller endpoints
        "/wireless-controller/managed-ap",
        "/wireless-controller/managed-aps", 
        "/wireless-controller/ap-status",
        "/wireless-controller/access-point",
        "/wireless-controller/access-points",
        "/wifi/managed-ap",
        "/wifi/managed-aps",
        "/wifi/ap-status",
        "/wireless/managed-ap",
        "/wireless/managed-aps",
        
        # Device endpoints
        "/device/inventory",
        "/device/list",
        "/device/connected",
        "/device/clients",
        "/endpoint/list",
        "/endpoint/clients",
        "/client/list",
        "/client/connected",
        
        # Network endpoints
        "/network/interface",
        "/network/topology",
        "/network/map",
        "/network/connections",
        "/topology/map",
        "/topology/devices",
        
        # DHCP endpoints
        "/dhcp/server/lease",
        "/dhcp/lease",
        
        # VLAN endpoints
        "/interface/vlan",
        "/vlan/available",
        
        # FortiLink endpoints
        "/fortilink/status",
        "/fortilink/switches",
        "/fortilink/devices",
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
        timeout=aiohttp.ClientTimeout(total=10)
    ) as session:
        
        print(f"🔍 Testing {len(endpoints)} JSON-RPC endpoints...")
        print(f"🌐 Base URL: {base_url}")
        
        for i, endpoint in enumerate(endpoints, 1):
            url = f"{base_url}/api/v2/monitor"
            
            # JSON-RPC payload
            payload = {
                "jsonrpc": "2.0",
                "method": "get",
                "params": [{
                    "url": endpoint
                }],
                "id": i
            }
            
            try:
                async with session.post(url, headers=headers, json=payload) as response:
                    status = response.status
                    
                    print(f"[{i:3d}/{len(endpoints)}] {status:3d} {endpoint[:40]:<40} ", end="")
                    
                    if status == 200:
                        try:
                            data = await response.json()
                            
                            # Check for JSON-RPC response structure
                            if 'result' in data and len(data['result']) > 0:
                                result_data = data['result'][0]
                                
                                # Check if it contains device data
                                data_str = json.dumps(result_data, casefold=True).lower()
                                has_switches = any(keyword in data_str for keyword in ['switch', 'fortiswitch', 'fsw'])
                                has_aps = any(keyword in data_str for keyword in ['ap', 'fortiap', 'fap', 'wifi'])
                                has_devices = any(keyword in data_str for keyword in ['device', 'client', 'endpoint'])
                                
                                device_count = 0
                                if 'data' in result_data and isinstance(result_data['data'], list):
                                    device_count = len(result_data['data'])
                                
                                results['working_endpoints'].append({
                                    'endpoint': endpoint,
                                    'status': status,
                                    'data': result_data,
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
                                    print(f"✅ OK (no devices)")
                            else:
                                print(f"✅ OK (no data)")
                                
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
    print(f"\n🎯 JSON-RPC DISCOVERY SUMMARY:")
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
    
    # Save results
    with open("fortigate_jsonrpc_discovery.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to fortigate_jsonrpc_discovery.json")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(test_jsonrpc_endpoints())
