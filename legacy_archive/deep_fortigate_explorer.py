#!/usr/bin/env python3
"""
Deep FortiGate Explorer - Navigate all GUI sections and test comprehensive API endpoints
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time
import logging

async def explore_all_fortigate_sections():
    """Navigate every possible section to find all connected devices"""
    
    fortigate_url = "https://192.168.0.254:10443"
    username = "admin"
    password = "!cg@RW%G@o"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        try:
            print(f"🔐 Logging into {fortigate_url}")
            await page.goto(fortigate_url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Login
            await page.fill('input[name="username"], input[id="username"]', username)
            await page.fill('input[name="password"], input[id="password"]', password)
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_timeout(3000)
            
            if "login" in page.url.lower():
                print("❌ Login failed")
                return
            
            print("✅ Login successful!")
            
            # Define all sections to explore
            sections_to_explore = [
                # WiFi & Switch Controller sections
                "WiFi & Switch Controller",
                "Managed FortiSwitches", 
                "Managed FortiAPs",
                "FortiSwitch Views",
                "FortiAP Views",
                "WiFi & Switch Controller > FortiSwitch",
                "WiFi & Switch Controller > FortiAP",
                
                # Monitor sections
                "Monitor",
                "Monitor > WiFi & Switch",
                "Monitor > System",
                "Monitor > Firewall",
                "Monitor > Network",
                "Monitor > Device",
                
                # System sections  
                "System",
                "System > Network",
                "System > Interfaces",
                "System > DHCP",
                "System > DNS",
                
                # Network sections
                "Network",
                "Network > Interfaces", 
                "Network > Switch Controller",
                "Network > Wireless Controller",
                
                # Device specific sections
                "Device",
                "Device List",
                "Device Inventory",
                "Topology",
                "Network Map",
                
                # Dashboard widgets
                "Dashboard",
                "System Resources",
                "Security Fabric",
                "Threat Intelligence"
            ]
            
            discovered_devices = {
                'switches': [],
                'aps': [],
                'other_devices': []
            }
            
            for section in sections_to_explore:
                try:
                    print(f"\n🔍 Exploring: {section}")
                    
                    # Try to navigate to section
                    if ">" in section:
                        # Nested menu
                        parts = section.split(" > ")
                        await page.click(f':has-text("{parts[0]}")')
                        await page.wait_for_timeout(1000)
                        await page.click(f':has-text("{parts[1]}")')
                    else:
                        # Top-level menu
                        await page.click(f':has-text("{section}")')
                    
                    await page.wait_for_timeout(2000)
                    
                    # Take screenshot
                    safe_name = section.replace(" > ", "_").replace(" ", "_").lower()
                    await page.screenshot(path=f"exploration_{safe_name}.png")
                    
                    # Look for device tables and lists
                    devices = await extract_devices_from_page(page, section)
                    
                    if devices['switches']:
                        discovered_devices['switches'].extend(devices['switches'])
                        print(f"  🔌 Found {len(devices['switches'])} switches")
                    
                    if devices['aps']:
                        discovered_devices['aps'].extend(devices['aps'])
                        print(f"  📶 Found {len(devices['aps'])} APs")
                    
                    if devices['other_devices']:
                        discovered_devices['other_devices'].extend(devices['other_devices'])
                        print(f"  📱 Found {len(devices['other_devices'])} other devices")
                    
                    # Go back to main dashboard
                    await page.goto(fortigate_url)
                    await page.wait_for_timeout(1000)
                    
                except Exception as e:
                    print(f"  ⚠️ Could not explore {section}: {e}")
                    # Try to go back to main page
                    await page.goto(fortigate_url)
                    await page.wait_for_timeout(1000)
                    continue
            
            # Summary of discoveries
            print(f"\n🎯 EXPLORATION SUMMARY:")
            print(f"  🔌 Switches: {len(discovered_devices['switches'])}")
            print(f"  📶 APs: {len(discovered_devices['aps'])}")
            print(f"  📱 Other Devices: {len(discovered_devices['other_devices'])}")
            
            # Save discoveries
            with open("fortigate_discoveries.json", "w") as f:
                json.dump(discovered_devices, f, indent=2)
            
            print(f"\n📄 Detailed discoveries saved to fortigate_discoveries.json")
            
            # Print device details
            for category, devices in discovered_devices.items():
                if devices:
                    print(f"\n{category.upper()}:")
                    for device in devices:
                        print(f"  - {device}")
            
        except Exception as e:
            print(f"❌ Exploration error: {e}")
            await page.screenshot(path="exploration_error.png")
            
        finally:
            await browser.close()

async def extract_devices_from_page(page, section_name):
    """Extract device information from current page"""
    devices = {'switches': [], 'aps': [], 'other_devices': []}
    
    try:
        # Method 1: Look for device tables
        table_data = await page.evaluate("""
            () => {
                const results = [];
                const tables = document.querySelectorAll('table');
                
                for (let table of tables) {
                    const rows = table.querySelectorAll('tr');
                    const tableData = [];
                    
                    for (let row of rows) {
                        const cells = row.querySelectorAll('td, th');
                        if (cells.length > 1) {
                            const rowData = [];
                            for (let cell of cells) {
                                rowData.push(cell.textContent.trim());
                            }
                            tableData.push(rowData);
                        }
                    }
                    
                    if (tableData.length > 0) {
                        results.push({
                            type: 'table',
                            data: tableData
                        });
                    }
                }
                
                return results;
            }
        """)
        
        # Analyze table data for devices
        for table in table_data:
            for row in table['data']:
                row_text = ' '.join(row).lower()
                
                # Check for switches
                if any(keyword in row_text for keyword in ['switch', 'fortiswitch', 'fsw', 'fs-']):
                    device_info = {
                        'section': section_name,
                        'data': row,
                        'type': 'switch',
                        'name': row[0] if row else 'Unknown Switch'
                    }
                    devices['switches'].append(device_info)
                
                # Check for APs
                elif any(keyword in row_text for keyword in ['ap', 'fortiap', 'fap', 'wifi', 'wireless']):
                    device_info = {
                        'section': section_name,
                        'data': row,
                        'type': 'ap', 
                        'name': row[0] if row else 'Unknown AP'
                    }
                    devices['aps'].append(device_info)
                
                # Check for other network devices
                elif any(keyword in row_text for keyword in ['device', 'client', 'host', 'station']):
                    device_info = {
                        'section': section_name,
                        'data': row,
                        'type': 'other',
                        'name': row[0] if row else 'Unknown Device'
                    }
                    devices['other_devices'].append(device_info)
        
        # Method 2: Look for device cards/panels
        card_data = await page.evaluate("""
            () => {
                const results = [];
                const cards = document.querySelectorAll('[class*="device"], [class*="card"], [class*="panel"], [class*="item"]');
                
                for (let card of cards) {
                    const text = card.textContent || card.innerText;
                    if (text && text.length > 10 && text.length < 500) {
                        results.push(text.trim());
                    }
                }
                
                return results;
            }
        """)
        
        # Analyze card data for devices
        for card_text in card_data:
            card_lower = card_text.lower()
            
            if any(keyword in card_lower for keyword in ['switch', 'fortiswitch', 'fsw']):
                if not any(d['name'] == card_text[:50] for d in devices['switches']):
                    devices['switches'].append({
                        'section': section_name,
                        'data': [card_text],
                        'type': 'switch',
                        'name': card_text[:50]
                    })
            
            elif any(keyword in card_lower for keyword in ['ap', 'fortiap', 'fap', 'wifi']):
                if not any(d['name'] == card_text[:50] for d in devices['aps']):
                    devices['aps'].append({
                        'section': section_name,
                        'data': [card_text],
                        'type': 'ap',
                        'name': card_text[:50]
                    })
        
        # Method 3: Look for specific device indicators
        device_indicators = await page.evaluate("""
            () => {
                const indicators = [];
                
                // Look for device count badges, status indicators, etc.
                const elements = document.querySelectorAll('*');
                
                for (let el of elements) {
                    const text = el.textContent || el.innerText;
                    if (text && (
                        text.includes('Switch') || 
                        text.includes('AP') || 
                        text.includes('Forti') ||
                        text.includes('device') ||
                        text.includes('client')
                    )) {
                        indicators.push({
                            tag: el.tagName,
                            class: el.className,
                            text: text.trim(),
                            id: el.id
                        });
                    }
                }
                
                return indicators;
            }
        """)
        
        # Save indicators for analysis
        if device_indicators:
            print(f"    📍 Found {len(device_indicators)} device indicators")
            
    except Exception as e:
        print(f"    ⚠️ Error extracting devices: {e}")
    
    return devices

if __name__ == "__main__":
    asyncio.run(explore_all_fortigate_sections())
