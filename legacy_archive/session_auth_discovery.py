#!/usr/bin/env python3
"""
Session-based FortiGate API Discovery
"""

import asyncio
import aiohttp
import json
import logging

async def login_and_discover():
    """Login to FortiGate and discover devices using session cookies"""
    
    base_url = "https://192.168.0.254:10443"
    username = "admin"
    password = "!cg@RW%G@o"
    
    # Test endpoints
    endpoints = [
        "/api/v2/monitor/system/status",
        "/api/v2/monitor/switch-controller/managed-switch",
        "/api/v2/monitor/wireless-controller/managed-ap",
        "/api/v2/cmdb/switch-controller/managed-switch", 
        "/api/v2/cmdb/wireless-controller/managed-ap",
        "/api/v2/monitor/device/inventory",
        "/api/v2/monitor/client/list",
        "/api/v2/monitor/dhcp/server/lease",
    ]
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=15)
    ) as session:
        
        print(f"🔐 Attempting session login to {base_url}")
        
        # Step 1: Login and get session cookies
        login_data = {
            'username': username,
            'password': password,
            'ajax': '1'
        }
        
        try:
            async with session.post(f"{base_url}/logincheck", data=login_data) as response:
                print(f"Login response: {response.status}")
                
                if response.status == 200:
                    # Extract cookies
                    cookies = {}
                    for cookie in session.cookie_jar:
                        cookies[cookie.key] = cookie.value
                    
                    print(f"✅ Session login successful, got {len(cookies)} cookies")
                    print(f"🍪 Cookies: {list(cookies.keys())}")
                    
                    # Step 2: Test endpoints with session cookies
                    results = []
                    
                    for endpoint in endpoints:
                        url = f"{base_url}{endpoint}"
                        
                        try:
                            async with session.get(url, cookies=cookies) as response:
                                print(f"[{response.status:3d}] {endpoint[:50]:<50} ", end="")
                                
                                if response.status == 200:
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
                                        
                                        results.append({
                                            'endpoint': endpoint,
                                            'status': response.status,
                                            'data': data,
                                            'device_count': device_count,
                                            'has_switches': has_switches,
                                            'has_aps': has_aps,
                                            'has_devices': has_devices
                                        })
                                        
                                        if device_count > 0:
                                            device_types = []
                                            if has_switches: device_types.append("SWITCH")
                                            if has_aps: device_types.append("AP") 
                                            if has_devices: device_types.append("DEVICE")
                                            print(f"✅ {device_count} devices ({', '.join(device_types)})")
                                        else:
                                            print("✅ OK (no devices)")
                                            
                                    except json.JSONDecodeError:
                                        text = await response.text()
                                        print(f"✅ TEXT ({len(text)} chars)")
                                        
                                elif response.status == 401:
                                    print("❌ UNAUTHORIZED")
                                elif response.status == 403:
                                    print("❌ FORBIDDEN")
                                elif response.status == 404:
                                    print("❌ NOT FOUND")
                                else:
                                    print(f"❌ ERROR {response.status}")
                                    
                        except Exception as e:
                            print(f"❌ EXCEPTION: {str(e)[:30]}")
                    
                    # Summary
                    print(f"\n🎯 SESSION DISCOVERY SUMMARY:")
                    working_with_devices = [r for r in results if r['device_count'] > 0]
                    print(f"  ✅ Working endpoints: {len(results)}")
                    print(f"  🔌 Endpoints with devices: {len(working_with_devices)}")
                    
                    if working_with_devices:
                        print(f"\n🔍 ENDPOINTS WITH DEVICES:")
                        for result in working_with_devices:
                            device_types = []
                            if result['has_switches']: device_types.append("SWITCH")
                            if result['has_aps']: device_types.append("AP")
                            if result['has_devices']: device_types.append("DEVICE")
                            
                            print(f"  🔌 {result['endpoint']}: {result['device_count']} devices ({', '.join(device_types)})")
                            
                            # Show sample devices
                            try:
                                if 'data' in result['data'] and isinstance(result['data']['data'], list):
                                    for device in result['data']['data'][:3]:
                                        print(f"    📋 {str(device)[:100]}...")
                            except:
                                pass
                    
                    # Save results
                    with open("fortigate_session_discovery.json", "w") as f:
                        json.dump({
                            'cookies': cookies,
                            'results': results
                        }, f, indent=2)
                    
                    print(f"\n📄 Results saved to fortigate_session_discovery.json")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Login failed: {response.status}")
                    print(f"Error: {error_text[:200]}")
                    
        except Exception as e:
            print(f"❌ Login exception: {e}")

async def try_token_auth():
    """Try different token authentication methods"""
    
    base_url = "https://192.168.0.254:10443"
    api_token = "f5q7tgy9tznpHwqxc5fmHtz01nh5Q0"
    
    # Different header combinations to try
    auth_methods = [
        {'Authorization': f'Bearer {api_token}'},
        {'X-Api-Key': api_token},
        {'Authorization': api_token},
        {'token': api_token},
        {'api-token': api_token},
        {'access-token': api_token},
        {'Authorization': f'Token {api_token}'},
        {'Authorization': f'JWT {api_token}'},
        {'Authorization': f'ApiKey {api_token}'},
    ]
    
    test_endpoint = "/api/v2/monitor/system/status"
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=10)
    ) as session:
        
        print(f"\n🔑 Testing {len(auth_methods)} authentication methods...")
        
        for i, headers in enumerate(auth_methods, 1):
            url = f"{base_url}{test_endpoint}"
            
            try:
                async with session.get(url, headers=headers) as response:
                    print(f"[{i:2d}/{len(auth_methods)}] {response.status:3d} {list(headers.keys())[0]}: {list(headers.values())[0][:20]}...", end="")
                    
                    if response.status == 200:
                        print(" ✅ SUCCESS!")
                        return headers
                    elif response.status == 401:
                        print(" ❌ UNAUTHORIZED")
                    elif response.status == 403:
                        print(" ❌ FORBIDDEN")
                    else:
                        print(f" ❌ ERROR {response.status}")
                        
            except Exception as e:
                print(f" ❌ EXCEPTION: {str(e)[:30]}")
    
    return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    
    print("🔍 FortiGate Session Authentication Discovery")
    print("=" * 50)
    
    # Try token auth first
    asyncio.run(try_token_auth())
    
    # Then try session auth
    asyncio.run(login_and_discover())
