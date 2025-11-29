#!/usr/bin/env python3
"""
Alternative API Discovery - Try different endpoint patterns and authentication
"""

import asyncio
import aiohttp
import json
import logging

async def discover_alternative_endpoints():
    """Try alternative endpoint patterns for FortiAP discovery"""
    
    base_url = "https://192.168.0.254:10443"
    api_token = "f5q7tgy9tznpHwqxc5fmHtz01nh5Q0"
    
    # Alternative endpoint patterns based on FortiOS documentation
    alternative_endpoints = [
        # Monitor endpoints with different patterns
        "/api/v2/monitor/wifi/access-point",
        "/api/v2/monitor/wifi/access-points", 
        "/api/v2/monitor/wifi/ap",
        "/api/v2/monitor/wifi/aps",
        "/api/v2/monitor/wifi/managed-ap",
        "/api/v2/monitor/wifi/managed-aps",
        "/api/v2/monitor/wifi/fortiap",
        "/api/v2/monitor/wifi/fortiaps",
        "/api/v2/monitor/wifi-controller/ap",
        "/api/v2/monitor/wifi-controller/aps",
        "/api/v2/monitor/wifi-controller/managed-ap",
        "/api/v2/monitor/wifi-controller/managed-aps",
        "/api/v2/monitor/wifi-controller/access-point",
        "/api/v2/monitor/wifi-controller/access-points",
        
        # Wireless controller patterns
        "/api/v2/monitor/wireless/access-point",
        "/api/v2/monitor/wireless/access-points",
        "/api/v2/monitor/wireless/ap",
        "/api/v2/monitor/wireless/aps",
        "/api/v2/monitor/wireless/managed-ap",
        "/api/v2/monitor/wireless/managed-aps",
        "/api/v2/monitor/wireless/fortiap",
        "/api/v2/monitor/wireless/fortiaps",
        "/api/v2/monitor/wireless-controller/ap",
        "/api/v2/monitor/wireless-controller/aps",
        "/api/v2/monitor/wireless-controller/managed-ap",
        "/api/v2/monitor/wireless-controller/managed-aps",
        
        # CMDB endpoints
        "/api/v2/cmdb/wifi/access-point",
        "/api/v2/cmdb/wifi/access-points",
        "/api/v2/cmdb/wifi/ap",
        "/api/v2/cmdb/wifi/aps",
        "/api/v2/cmdb/wifi/managed-ap",
        "/api/v2/cmdb/wifi/managed-aps",
        "/api/v2/cmdb/wifi/fortiap",
        "/api/v2/cmdb/wifi/fortiaps",
        "/api/v2/cmdb/wifi-controller/ap",
        "/api/v2/cmdb/wifi-controller/aps",
        "/api/v2/cmdb/wifi-controller/managed-ap",
        "/api/v2/cmdb/wifi-controller/managed-aps",
        "/api/v2/cmdb/wifi-controller/access-point",
        "/api/v2/cmdb/wifi-controller/access-points",
        
        # Wireless controller CMDB
        "/api/v2/cmdb/wireless/access-point",
        "/api/v2/cmdb/wireless/access-points",
        "/api/v2/cmdb/wireless/ap",
        "/api/v2/cmdb/wireless/aps",
        "/api/v2/cmdb/wireless/managed-ap",
        "/api/v2/cmdb/wireless/managed-aps",
        "/api/v2/cmdb/wireless/fortiap",
        "/api/v2/cmdb/wireless/fortiaps",
        "/api/v2/cmdb/wireless-controller/ap",
        "/api/v2/cmdb/wireless-controller/aps",
        "/api/v2/cmdb/wireless-controller/managed-ap",
        "/api/v2/cmdb/wireless-controller/managed-aps",
        
        # Status and monitoring endpoints
        "/api/v2/monitor/wifi/status",
        "/api/v2/monitor/wifi/ap-status",
        "/api/v2/monitor/wifi/fortiap-status",
        "/api/v2/monitor/wireless/status",
        "/api/v2/monitor/wireless/ap-status",
        "/api/v2/monitor/wireless/fortiap-status",
        "/api/v2/monitor/wifi-controller/status",
        "/api/v2/monitor/wireless-controller/status",
        
        # Device inventory endpoints
        "/api/v2/monitor/device/wifi",
        "/api/v2/monitor/device/wireless",
        "/api/v2/monitor/device/fortiap",
        "/api/v2/monitor/device/access-point",
        "/api/v2/monitor/device/inventory/wifi",
        "/api/v2/monitor/device/inventory/wireless",
        
        # Client/endpoint endpoints
        "/api/v2/monitor/client/wifi",
        "/api/v2/monitor/client/wireless",
        "/api/v2/monitor/endpoint/wifi",
        "/api/v2/monitor/endpoint/wireless",
        "/api/v2/monitor/endpoint/access-point",
        
        # Alternative patterns
        "/api/v2/monitor/ap",
        "/api/v2/monitor/aps",
        "/api/v2/monitor/access-point",
        "/api/v2/monitor/access-points",
        "/api/v2/monitor/fortiap",
        "/api/v2/monitor/fortiaps",
        "/api/v2/cmdb/ap",
        "/api/v2/cmdb/aps",
        "/api/v2/cmdb/access-point",
        "/api/v2/cmdb/access-points",
        "/api/v2/cmdb/fortiap",
        "/api/v2/cmdb/fortiaps",
        
        # Legacy API v1 patterns
        "/api/v1/monitor/wifi/ap",
        "/api/v1/monitor/wifi/aps",
        "/api/v1/monitor/wireless/ap",
        "/api/v1/monitor/wireless/aps",
        "/api/v1/cmdb/wifi/ap",
        "/api/v1/cmdb/wifi/aps",
        "/api/v1/cmdb/wireless/ap",
        "/api/v1/cmdb/wireless/aps",
    ]
    
    # Test with Bearer token authentication
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    working_endpoints = []
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=10)
    ) as session:
        
        print(f"🔍 Testing {len(alternative_endpoints)} alternative AP endpoints...")
        print(f"🌐 Base URL: {base_url}")
        
        for i, endpoint in enumerate(alternative_endpoints, 1):
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.get(url, headers=headers) as response:
                    status = response.status
                    
                    print(f"[{i:3d}/{len(alternative_endpoints)}] {status:3d} {endpoint[:50]:<50} ", end="")
                    
                    if status == 200:
                        try:
                            data = await response.json()
                            
                            # Check for AP data
                            data_str = json.dumps(data).lower()
                            has_aps = any(keyword in data_str for keyword in ['ap', 'fortiap', 'wifi', 'wireless', 'access point'])
                            
                            device_count = 0
                            if 'data' in data and isinstance(data['data'], list):
                                device_count = len(data['data'])
                            elif 'results' in data and isinstance(data['results'], list):
                                device_count = len(data['results'])
                            
                            working_endpoints.append({
                                'endpoint': endpoint,
                                'status': status,
                                'data': data,
                                'device_count': device_count,
                                'has_aps': has_aps
                            })
                            
                            if has_aps and device_count > 0:
                                print(f"✅ APs ({device_count} devices)")
                            elif has_aps:
                                print(f"✅ AP-related (no devices)")
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
                        
            except asyncio.TimeoutError:
                print(f"⏰ TIMEOUT")
            except Exception as e:
                print(f"❌ EXCEPTION: {str(e)[:30]}")
    
    # Summary
    print(f"\n🎯 ALTERNATIVE ENDPOINT DISCOVERY SUMMARY:")
    print(f"  ✅ Working endpoints: {len(working_endpoints)}")
    
    # Show endpoints with APs
    ap_endpoints = [ep for ep in working_endpoints if ep['has_aps'] and ep['device_count'] > 0]
    if ap_endpoints:
        print(f"\n📶 ENDPOINTS WITH ACTUAL APs:")
        for ep in ap_endpoints:
            print(f"  🔌 {ep['endpoint']}: {ep['device_count']} devices")
            
            # Show sample AP data
            try:
                data = ep['data']
                devices = data.get('data', data.get('results', []))
                for device in devices[:2]:  # Show first 2
                    print(f"    📋 {str(device)[:100]}...")
            except:
                pass
    
    # Show all working endpoints
    print(f"\n📋 ALL WORKING ENDPOINTS:")
    for ep in working_endpoints:
        status_info = f"({ep['device_count']} devices)" if ep['device_count'] > 0 else "(no devices)"
        if ep['has_aps']:
            status_info += " 📶"
        print(f"  ✅ {ep['endpoint']} {status_info}")
    
    # Save results
    with open("alternative_ap_discovery.json", "w") as f:
        json.dump(working_endpoints, f, indent=2)
    
    print(f"\n📄 Results saved to alternative_ap_discovery.json")
    
    return working_endpoints

async def try_session_based_discovery():
    """Try session-based authentication for AP endpoints"""
    
    base_url = "https://192.168.0.254:10443"
    username = "admin"
    password = "!cg@RW%G@o"
    
    # Test endpoints that might work with session auth
    session_endpoints = [
        "/api/v2/monitor/wifi/ap",
        "/api/v2/monitor/wireless/ap",
        "/api/v2/monitor/fortiap",
        "/api/v2/monitor/access-point",
        "/api/v2/monitor/device/inventory",
    ]
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=15)
    ) as session:
        
        print(f"\n🔐 Trying session-based authentication...")
        
        # Login to get session
        login_data = {
            'username': username,
            'password': password,
            'ajax': '1'
        }
        
        try:
            async with session.post(f"{base_url}/logincheck", data=login_data) as response:
                if response.status == 200:
                    print("✅ Session login successful")
                    
                    # Test endpoints with session
                    for endpoint in session_endpoints:
                        url = f"{base_url}{endpoint}"
                        
                        try:
                            async with session.get(url) as response:
                                print(f"[{response.status:3d}] {endpoint}")
                                
                                if response.status == 200:
                                    data = await response.json()
                                    data_str = json.dumps(data).lower()
                                    has_aps = any(keyword in data_str for keyword in ['ap', 'fortiap', 'wifi'])
                                    
                                    if has_aps:
                                        device_count = len(data.get('data', data.get('results', [])))
                                        print(f"    ✅ Found {device_count} APs!")
                                        
                                        # Show sample data
                                        devices = data.get('data', data.get('results', []))
                                        for device in devices[:2]:
                                            print(f"      📋 {str(device)[:80]}...")
                                else:
                                    print(f"    ❌ Error {response.status}")
                                    
                        except Exception as e:
                            print(f"    ❌ Exception: {str(e)[:30]}")
                else:
                    print(f"❌ Session login failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Session login exception: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    
    print("🔍 Alternative FortiAP API Discovery")
    print("=" * 50)
    
    # Try alternative endpoints
    asyncio.run(discover_alternative_endpoints())
    
    # Try session-based auth
    asyncio.run(try_session_based_discovery())
