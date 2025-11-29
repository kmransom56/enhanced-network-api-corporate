#!/usr/bin/env python3
"""
Analyze GUI pages to find actual AP information
"""

import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup

async def analyze_gui_pages():
    """Analyze GUI pages for device information"""
    
    base_url = "https://192.168.0.254:10443"
    
    # GUI pages that might contain AP info
    gui_pages = [
        ("/ng/wifi-switch-controller", "WiFi & Switch Controller Main"),
        ("/ng/wireless-controller", "Wireless Controller"),
        ("/ng/fortiap", "FortiAP Management"),
        ("/p/fortiap", "FortiAP Details"),
        ("/ng/switch-controller", "Switch Controller"),
        ("/ng/fortiswitch", "FortiSwitch Management"),
    ]
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=15)
    ) as session:
        
        print(f"🌐 Analyzing GUI pages for device information...")
        
        for page_url, page_name in gui_pages:
            url = f"{base_url}{page_url}"
            
            try:
                async with session.get(url) as response:
                    print(f"\n[{response.status:3d}] {page_name}")
                    
                    if response.status == 200:
                        content = await response.text()
                        
                        # Look for device counts
                        ap_counts = re.findall(r'(\d+)\s*(?:AP|FortiAP|Access Point)', content, re.IGNORECASE)
                        switch_counts = re.findall(r'(\d+)\s*(?:Switch|FortiSwitch)', content, re.IGNORECASE)
                        
                        if ap_counts:
                            print(f"  📶 AP count indicators: {ap_counts}")
                        if switch_counts:
                            print(f"  🔌 Switch count indicators: {switch_counts}")
                        
                        # Look for device status indicators
                        device_patterns = [
                            r'(\d+)\s*online',
                            r'(\d+)\s*connected', 
                            r'(\d+)\s*active',
                            r'(\d+)\s*up',
                        ]
                        
                        for pattern in device_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                print(f"  📊 Device status: {pattern} -> {matches}")
                        
                        # Look for specific device information
                        device_info_patterns = [
                            r'FortiAP.*?([A-Z0-9]{8,})',
                            r'Serial[:\s]*([A-Z0-9]{8,})',
                            r'Model[:\s]*([A-Z0-9\-]+)',
                            r'IP[:\s]*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
                        ]
                        
                        device_details = []
                        for pattern in device_info_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                device_details.extend(matches)
                        
                        if device_details:
                            print(f"  📋 Device details found: {device_details[:10]}")  # Show first 10
                        
                        # Parse HTML structure for device tables
                        try:
                            soup = BeautifulSoup(content, 'html.parser')
                            
                            # Look for tables with device information
                            tables = soup.find_all('table')
                            for i, table in enumerate(tables):
                                rows = table.find_all('tr')
                                if len(rows) > 1:  # Has header + data
                                    print(f"  📊 Table {i+1}: {len(rows)} rows")
                                    
                                    # Look for device info in table cells
                                    for j, row in enumerate(rows[:3]):  # Check first 3 rows
                                        cells = row.find_all(['td', 'th'])
                                        cell_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                                        
                                        if any(keyword in cell_text.lower() for keyword in ['fortiap', 'ap', 'switch', 'serial']):
                                            print(f"    Row {j+1}: {cell_text[:80]}...")
                        
                        except Exception as e:
                            print(f"    ⚠️ HTML parsing error: {e}")
                        
                        # Look for JavaScript data that might contain device info
                        js_patterns = [
                            r'data[:\s]*{([^}]+AP[^}]+)}',
                            r'devices[:\s]*\[([^\]]+AP[^\]]+)\]',
                            r'apList[:\s]*\[([^\]]+)\]',
                            r'switchList[:\s]*\[([^\]]+)\]',
                        ]
                        
                        for pattern in js_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                            if matches:
                                print(f"  📜 JavaScript data found: {len(matches)} matches")
                                for match in matches[:2]:  # Show first 2
                                    print(f"    {match[:100]}...")
                    
                    else:
                        print(f"  ❌ Error {response.status}")
                        
            except Exception as e:
                print(f"  ❌ Exception: {str(e)[:30]}")

async def try_api_with_different_auth():
    """Try API calls with different authentication methods"""
    
    base_url = "https://192.168.0.254:10443"
    api_token = "f5q7tgy9tznpHwqxc5fmHtz01nh5Q0"
    
    # Try different authentication headers
    auth_methods = [
        {'Authorization': f'Bearer {api_token}'},
        {'X-Api-Key': api_token},
        {'Authorization': api_token},
        {'Authorization': f'Token {api_token}'},
    ]
    
    # Endpoints that might work with different auth
    endpoints = [
        "/api/v2/monitor/wireless-controller/ap",
        "/api/v2/monitor/wifi-controller/ap", 
        "/api/v2/monitor/fortiap",
        "/api/v2/monitor/device/list",
        "/api/v2/monitor/endpoint/list",
    ]
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=10)
    ) as session:
        
        print(f"\n🔑 Trying different authentication methods...")
        
        for auth_headers in auth_methods:
            auth_name = list(auth_headers.keys())[0]
            print(f"\n🔐 Using {auth_name}:")
            
            for endpoint in endpoints:
                url = f"{base_url}{endpoint}"
                
                try:
                    async with session.get(url, headers=auth_headers) as response:
                        print(f"  [{response.status:3d}] {endpoint}")
                        
                        if response.status == 200:
                            data = await response.json()
                            data_str = str(data).lower()
                            
                            if any(keyword in data_str for keyword in ['ap', 'fortiap', 'wifi']):
                                device_count = len(data.get('data', data.get('results', [])))
                                print(f"    ✅ SUCCESS! Found {device_count} devices")
                                
                                # Show sample data
                                devices = data.get('data', data.get('results', []))
                                for device in devices[:2]:
                                    print(f"      📋 {str(device)[:80]}...")
                        
                except Exception as e:
                    print(f"    ❌ Exception: {str(e)[:30]}")

async def check_dhcp_clients():
    """Check DHCP clients which might show connected APs"""
    
    base_url = "https://192.168.0.254:10443"
    api_token = "f5q7tgy9tznpHwqxc5fmHtz01nh5Q0"
    
    headers = {'Authorization': f'Bearer {api_token}'}
    
    # DHCP and client endpoints
    client_endpoints = [
        "/api/v2/monitor/dhcp/server/lease",
        "/api/v2/monitor/client/list",
        "/api/v2/monitor/endpoint/list",
        "/api/v2/monitor/user/device",
        "/api/v2/monitor/system/arp-table",
    ]
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
        timeout=aiohttp.ClientTimeout(total=15)
    ) as session:
        
        print(f"\n👥 Checking DHCP clients and endpoints...")
        
        for endpoint in client_endpoints:
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.get(url, headers=headers) as response:
                    print(f"[{response.status:3d}] {endpoint}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Look for AP-like devices in client list
                        results = data.get('results', data.get('data', []))
                        if isinstance(results, list):
                            ap_devices = []
                            for item in results:
                                item_str = json.dumps(item).lower()
                                if any(keyword in item_str for keyword in ['fortiap', 'ap', 'wifi', 'wireless']):
                                    ap_devices.append(item)
                            
                            if ap_devices:
                                print(f"  ✅ Found {len(ap_devices)} AP-like devices")
                                for device in ap_devices[:3]:
                                    print(f"    📋 {str(device)[:100]}...")
                            else:
                                print(f"  📊 {len(results)} total clients (no APs)")
                    
                    else:
                        print(f"  ❌ Error {response.status}")
                        
            except Exception as e:
                print(f"  ❌ Exception: {str(e)[:30]}")

if __name__ == "__main__":
    asyncio.run(analyze_gui_pages())
    asyncio.run(try_api_with_different_auth())
    asyncio.run(check_dhcp_clients())
