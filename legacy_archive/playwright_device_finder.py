#!/usr/bin/env python3
"""
Use Playwright to find actual AP devices on the GUI pages
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time

async def find_ap_devices_via_gui():
    """Navigate GUI pages with Playwright to find AP devices"""
    
    fortigate_url = "https://192.168.0.254:10443"
    username = "admin"
    password = "!cg@RW%G@o"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        captured_api_calls = []
        
        async def capture_api_calls(request):
            """Capture API calls that might contain device data"""
            url = request.url
            if '/api/' in url and any(keyword in url.lower() for keyword in ['ap', 'wifi', 'wireless', 'device', 'switch']):
                captured_api_calls.append({
                    'url': url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data,
                    'timestamp': time.time()
                })
                print(f"🔍 API: {request.method} {url}")
        
        page.on("request", capture_api_calls)
        
        try:
            print(f"🔐 Logging into {fortigate_url}")
            await page.goto(fortigate_url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Login with multiple selectors
            await page.fill('input[name="username"], input[id="username"], input[type="text"]', username)
            await page.fill('input[name="password"], input[id="password"], input[type="password"]', password)
            
            # Try to click login button
            login_selectors = [
                'button[type="submit"]',
                'input[type="submit"]', 
                'button:has-text("Login")',
                'button:has-text("Log in")'
            ]
            
            for selector in login_selectors:
                try:
                    await page.click(selector, timeout=2000)
                    break
                except:
                    continue
            
            await page.wait_for_timeout(5000)
            
            if "login" in page.url.lower():
                print("❌ Login failed")
                return
            
            print("✅ Login successful!")
            
            # Navigate to specific pages and wait for content
            pages_to_check = [
                {
                    'name': 'FortiAP Management',
                    'url': f'{fortigate_url}/ng/fortiap',
                    'selectors': [
                        'table',
                        '[class*="device"]',
                        '[class*="ap"]',
                        '[class*="card"]',
                        '[data-device-type="ap"]'
                    ]
                },
                {
                    'name': 'Wireless Controller', 
                    'url': f'{fortigate_url}/ng/wireless-controller',
                    'selectors': [
                        'table',
                        '[class*="device"]',
                        '[class*="ap"]',
                        '[class*="card"]',
                        '[class*="managed"]'
                    ]
                },
                {
                    'name': 'WiFi & Switch Controller',
                    'url': f'{fortigate_url}/ng/wifi-switch-controller',
                    'selectors': [
                        'table',
                        '[class*="device"]',
                        '[class*="ap"]',
                        '[class*="switch"]',
                        '[class*="card"]'
                    ]
                }
            ]
            
            all_devices = []
            
            for page_info in pages_to_check:
                print(f"\n🔍 Checking {page_info['name']}...")
                
                try:
                    await page.goto(page_info['url'])
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(3000)  # Wait for JavaScript to load
                    
                    # Take screenshot
                    await page.screenshot(path=f"page_{page_info['name'].replace(' ', '_').lower()}.png")
                    
                    # Look for device information
                    devices = await extract_devices_from_page(page, page_info['selectors'])
                    if devices:
                        print(f"  ✅ Found {len(devices)} devices")
                        all_devices.extend(devices)
                        
                        for device in devices[:3]:  # Show first 3
                            print(f"    📋 {device}")
                    else:
                        print(f"  📊 No devices found in initial content")
                        
                        # Try to wait longer and look for dynamic loading
                        await page.wait_for_timeout(5000)
                        devices = await extract_devices_from_page(page, page_info['selectors'])
                        if devices:
                            print(f"  ✅ Found {len(devices)} devices after waiting")
                            all_devices.extend(devices)
                
                except Exception as e:
                    print(f"  ❌ Error accessing {page_info['name']}: {e}")
            
            # Summary of found devices
            if all_devices:
                print(f"\n🎯 DEVICES FOUND:")
                for device in all_devices:
                    print(f"  📋 {device}")
            else:
                print(f"\n📊 No devices found on any page")
            
            # Show captured API calls
            print(f"\n🔍 CAPTURED API CALLS: {len(captured_api_calls)}")
            for call in captured_api_calls:
                print(f"  {call['method']} {call['url']}")
            
            # Try to click on device elements to trigger more API calls
            await try_click_device_elements(page)
            
            # Final API call summary
            print(f"\n🎯 FINAL API CALLS: {len(captured_api_calls)}")
            unique_endpoints = set(call['url'] for call in captured_api_calls)
            for endpoint in sorted(unique_endpoints):
                print(f"  {endpoint}")
            
            # Save results
            with open("gui_device_discovery.json", "w") as f:
                json.dump({
                    'devices': all_devices,
                    'api_calls': captured_api_calls,
                    'unique_endpoints': list(unique_endpoints)
                }, f, indent=2)
            
            print(f"\n📄 Results saved to gui_device_discovery.json")
            
        except Exception as e:
            print(f"❌ Navigation error: {e}")
            await page.screenshot(path="navigation_error.png")
            
        finally:
            await browser.close()

async def extract_devices_from_page(page, selectors):
    """Extract device information from page using various selectors"""
    devices = []
    
    for selector in selectors:
        try:
            elements = await page.query_selector_all(selector)
            
            for element in elements:
                device_info = await element.evaluate("""
                    (el) => {
                        const text = el.textContent || el.innerText || '';
                        const hasDeviceInfo = text && (
                            text.includes('FortiAP') || 
                            text.includes('AP') || 
                            text.includes('FortiSwitch') ||
                            text.includes('Switch') ||
                            text.includes('Serial') ||
                            text.includes('Model') ||
                            text.includes('IP')
                        );
                        
                        if (hasDeviceInfo) {
                            return {
                                text: text.trim().substring(0, 200),
                                tagName: el.tagName,
                                className: el.className,
                                id: el.id
                            };
                        }
                        return null;
                    }
                """)
                
                if device_info:
                    devices.append(device_info)
        
        except Exception as e:
            continue
    
    # Remove duplicates
    unique_devices = []
    seen_texts = set()
    for device in devices:
        if device['text'] not in seen_texts:
            unique_devices.append(device)
            seen_texts.add(device['text'])
    
    return unique_devices

async def try_click_device_elements(page):
    """Try to click on device elements to trigger more API calls"""
    try:
        # Look for clickable device elements
        clickable_selectors = [
            'tr:has-text("FortiAP")',
            'tr:has-text("AP")',
            '[class*="device"]',
            '[class*="ap"]',
            'button:has-text("Details")',
            'a:has-text("View")',
            '[onclick*="device"]',
            '[onclick*="ap"]'
        ]
        
        for selector in clickable_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"🔍 Found {len(elements)} clickable elements with {selector}")
                    
                    # Click first few elements
                    for i, element in enumerate(elements[:3]):
                        try:
                            await element.click()
                            await page.wait_for_timeout(2000)
                            await page.screenshot(path=f"clicked_device_{i}.png")
                            
                            # Go back
                            await page.go_back()
                            await page.wait_for_timeout(1000)
                        except:
                            continue
                    
                    break  # Stop after finding clickable elements
            
            except Exception as e:
                continue
    
    except Exception as e:
        print(f"❌ Error clicking device elements: {e}")

if __name__ == "__main__":
    asyncio.run(find_ap_devices_via_gui())
