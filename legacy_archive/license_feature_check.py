#!/usr/bin/env python3
"""
Check FortiGate licenses and features to understand AP availability
"""

import asyncio
import aiohttp
import json
import logging

async def check_licenses_and_features():
    """Check what licenses and features are available"""
    
    base_url = "https://192.168.0.254:10443"
    api_token = "f5q7tgy9tznpHwqxc5fmHtz01nh5Q0"
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # License and feature endpoints
    endpoints_to_check = [
        "/api/v2/monitor/license/status",
        "/api/v2/monitor/license/vdom",
        "/api/v2/monitor/feature/select",
        "/api/v2/monitor/feature/status", 
        "/api/v2/cmdb/system/global",
        "/api/v2/cmdb/system/feature-display",
        "/api/v2/cmdb/system/setting",
    ]
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=15)
    ) as session:
        
        print(f"🔍 Checking FortiGate licenses and features...")
        print(f"🌐 Base URL: {base_url}")
        
        for endpoint in endpoints_to_check:
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.get(url, headers=headers) as response:
                    print(f"\n[{response.status:3d}] {endpoint}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Look for wireless/AP related licenses
                        data_str = json.dumps(data).lower()
                        has_wireless = any(keyword in data_str for keyword in ['wireless', 'wifi', 'ap', 'fortiap'])
                        
                        if has_wireless:
                            print(f"  ✅ Contains wireless/AP info")
                            
                            # Show relevant parts
                            results = data.get('results', data.get('data', []))
                            if isinstance(results, list):
                                for item in results:
                                    item_str = json.dumps(item).lower()
                                    if any(keyword in item_str for keyword in ['wireless', 'wifi', 'ap', 'fortiap']):
                                        print(f"    📋 {str(item)[:100]}...")
                        else:
                            print(f"  ✅ OK (no wireless info)")
                            
                            # Still show basic structure
                            if 'results' in data:
                                print(f"    📊 Results count: {len(data['results'])}")
                            elif 'data' in data:
                                print(f"    📊 Data count: {len(data['data'])}")
                        
                    else:
                        print(f"  ❌ Error {response.status}")
                        
            except Exception as e:
                print(f"  ❌ Exception: {str(e)[:30]}")

async def check_system_settings():
    """Check system settings for wireless controller"""
    
    base_url = "https://192.168.0.254:10443"
    api_token = "f5q7tgy9tznpHwqxc5fmHtz01nh5Q0"
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # System settings that might show wireless controller status
    settings_endpoints = [
        "/api/v2/cmdb/wireless-controller/status",
        "/api/v2/cmdb/wifi/status", 
        "/api/v2/cmdb/switch-controller/status",
        "/api/v2/cmdb/system/interface",
        "/api/v2/monitor/system/interface",
    ]
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=15)
    ) as session:
        
        print(f"\n🔧 Checking system settings...")
        
        for endpoint in settings_endpoints:
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.get(url, headers=headers) as response:
                    print(f"\n[{response.status:3d}] {endpoint}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Look for wireless controller settings
                        results = data.get('results', data.get('data', []))
                        if isinstance(results, list):
                            for item in results:
                                item_str = json.dumps(item).lower()
                                if any(keyword in item_str for keyword in ['wireless', 'wifi', 'ap', 'controller']):
                                    print(f"  📋 {str(item)[:120]}...")
                        
                        # Check if wireless controller is enabled
                        if 'status' in data:
                            status = data.get('status', '')
                            print(f"  📊 Status: {status}")
                        
                    else:
                        print(f"  ❌ Error {response.status}")
                        
            except Exception as e:
                print(f"  ❌ Exception: {str(e)[:30]}")

async def try_direct_gui_navigation():
    """Try to navigate directly to known GUI pages"""
    
    base_url = "https://192.168.0.254:10443"
    
    # Known GUI page patterns
    gui_pages = [
        "/ng/wifi-switch-controller",
        "/ng/wireless-controller", 
        "/ng/switch-controller",
        "/ng/wifi",
        "/ng/fortiap",
        "/ng/fortiswitch",
        "/p/wifi-switch-controller",
        "/p/wireless-controller",
        "/p/switch-controller",
        "/p/fortiap",
        "/p/fortiswitch",
        "/wifi-switch-controller",
        "/wireless-controller",
        "/switch-controller",
        "/fortiap",
        "/fortiswitch",
    ]
    
    print(f"\n🌐 Testing direct GUI page access...")
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=10)
    ) as session:
        
        for page in gui_pages:
            url = f"{base_url}{page}"
            
            try:
                async with session.get(url) as response:
                    print(f"[{response.status:3d}] {page}")
                    
                    if response.status == 200:
                        content = await response.text()
                        content_lower = content.lower()
                        
                        # Look for device indicators
                        has_ap = any(keyword in content_lower for keyword in ['fortiap', 'ap device', 'managed ap'])
                        has_switch = any(keyword in content_lower for keyword in ['fortiswitch', 'switch device', 'managed switch'])
                        
                        if has_ap or has_switch:
                            device_types = []
                            if has_ap: device_types.append("AP")
                            if has_switch: device_types.append("Switch")
                            print(f"  ✅ Contains {'/'.join(device_types)} info")
                        
                        # Look for device counts
                        import re
                        ap_matches = re.findall(r'(\d+)\s*(?:ap|fortiap)', content_lower)
                        switch_matches = re.findall(r'(\d+)\s*(?:switch|fortiswitch)', content_lower)
                        
                        if ap_matches:
                            print(f"  📊 AP count indicators: {ap_matches}")
                        if switch_matches:
                            print(f"  🔌 Switch count indicators: {switch_matches}")
                    
                    elif response.status == 302:
                        # Redirect - might need login
                        print(f"  🔄 Redirect (needs login)")
                    else:
                        print(f"  ❌ Error {response.status}")
                        
            except Exception as e:
                print(f"  ❌ Exception: {str(e)[:30]}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    
    print("🔍 FortiGate License and Feature Analysis")
    print("=" * 50)
    
    asyncio.run(check_licenses_and_features())
    asyncio.run(check_system_settings()) 
    asyncio.run(try_direct_gui_navigation())
