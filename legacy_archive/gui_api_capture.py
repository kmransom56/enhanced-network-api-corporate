#!/usr/bin/env python3
"""
Navigate WiFi & Switch Controller pages and capture API requests
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time

async def capture_wifi_switch_api_requests():
    """Navigate WiFi & Switch Controller pages and capture API calls"""
    
    fortigate_url = "https://192.168.0.254:10443"
    username = "admin"
    password = "!cg@RW%G@o"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(ignore_https_errors=True)
        
        # Enable request interception
        page = await context.new_page()
        
        captured_requests = []
        
        async def log_request(request):
            """Capture API requests"""
            url = request.url
            if '/api/' in url and any(keyword in url.lower() for keyword in ['ap', 'wifi', 'switch', 'wireless', 'device']):
                captured_requests.append({
                    'url': url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data
                })
                print(f"🔍 API Request: {request.method} {url}")
        
        page.on("request", log_request)
        
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
            
            # Navigate to WiFi & Switch Controller
            print(f"\n🔍 Navigating to WiFi & Switch Controller...")
            try:
                await page.click(':has-text("WiFi & Switch Controller")')
                await page.wait_for_timeout(3000)
                await page.screenshot(path="wifi_switch_main.png")
                
                # Look for sub-menu items
                menu_items = [
                    "Managed FortiSwitches",
                    "Managed FortiAPs", 
                    "FortiSwitch",
                    "FortiAP",
                    "Switch Controller",
                    "Wireless Controller",
                    "AP Management",
                    "Switch Management"
                ]
                
                for menu_item in menu_items:
                    try:
                        print(f"🔍 Clicking: {menu_item}")
                        await page.click(f':has-text("{menu_item}")')
                        await page.wait_for_timeout(3000)
                        await page.screenshot(path=f"menu_{menu_item.replace(' ', '_').lower()}.png")
                        
                        # Look for device tables/lists
                        await page.wait_for_load_state('networkidle')
                        
                        # Try to find device counts or tables
                        device_info = await page.evaluate("""
                            () => {
                                const results = [];
                                
                                // Look for tables
                                const tables = document.querySelectorAll('table');
                                for (let table of tables) {
                                    const rows = table.querySelectorAll('tr');
                                    if (rows.length > 1) {
                                        results.push({
                                            type: 'table',
                                            rowCount: rows.length - 1,
                                            html: table.outerHTML.substring(0, 1000)
                                        });
                                    }
                                }
                                
                                // Look for device cards/panels
                                const cards = document.querySelectorAll('[class*="device"], [class*="card"], [class*="panel"]');
                                if (cards.length > 0) {
                                    results.push({
                                        type: 'cards',
                                        count: cards.length
                                    });
                                }
                                
                                // Look for device count badges
                                const badges = document.querySelectorAll('*');
                                let deviceCount = 0;
                                for (let badge of badges) {
                                    const text = badge.textContent || badge.innerText;
                                    if (text && (text.includes('AP') || text.includes('Switch') || text.includes('Device'))) {
                                        const numbers = text.match(/\\d+/);
                                        if (numbers) {
                                            deviceCount += parseInt(numbers[0]);
                                        }
                                    }
                                }
                                
                                if (deviceCount > 0) {
                                    results.push({
                                        type: 'device_count',
                                        count: deviceCount
                                    });
                                }
                                
                                return results;
                            }
                        """)
                        
                        if device_info:
                            print(f"  📊 Found: {device_info}")
                        
                        # Go back to main WiFi & Switch Controller page
                        await page.goto(f"{fortigate_url}/ng")
                        await page.wait_for_timeout(2000)
                        
                    except Exception as e:
                        print(f"  ⚠️ Could not access {menu_item}: {e}")
                        continue
                
            except Exception as e:
                print(f"❌ Could not navigate WiFi & Switch Controller: {e}")
            
            # Try direct URLs for common pages
            direct_urls = [
                f"{fortigate_url}/ng/wifi-switch-controller",
                f"{fortigate_url}/ng/switch-controller",
                f"{fortigate_url}/ng/wireless-controller", 
                f"{fortigate_url}/ng/fortiswitch",
                f"{fortigate_url}/ng/fortiap",
                f"{fortigate_url}/p/fortiswitch",
                f"{fortigate_url}/p/fortiap",
                f"{fortigate_url}/wifi-switch-controller",
                f"{fortigate_url}/switch-controller",
                f"{fortigate_url}/wireless-controller"
            ]
            
            print(f"\n🔍 Trying direct URLs...")
            for url in direct_urls:
                try:
                    print(f"  🌐 {url}")
                    await page.goto(url)
                    await page.wait_for_timeout(2000)
                    
                    # Check if page loaded successfully
                    if "login" not in page.url.lower():
                        await page.screenshot(path=f"direct_{url.split('/')[-1]}.png")
                        
                        # Look for page content
                        page_content = await page.evaluate("""
                            () => {
                                const title = document.title;
                                const headings = document.querySelectorAll('h1, h2, h3');
                                const headingTexts = Array.from(headings).map(h => h.textContent.trim()).filter(t => t);
                                
                                // Look for device indicators
                                const deviceIndicators = document.querySelectorAll('*');
                                let apCount = 0, switchCount = 0;
                                
                                for (let el of deviceIndicators) {
                                    const text = el.textContent || el.innerText;
                                    if (text.includes('AP') || text.includes('FortiAP')) {
                                        const numbers = text.match(/\\d+/);
                                        if (numbers) apCount += parseInt(numbers[0]);
                                    }
                                    if (text.includes('Switch') || text.includes('FortiSwitch')) {
                                        const numbers = text.match(/\\d+/);
                                        if (numbers) switchCount += parseInt(numbers[0]);
                                    }
                                }
                                
                                return {
                                    title,
                                    headings: headingTexts,
                                    apCount,
                                    switchCount
                                };
                            }
                        """)
                        
                        print(f"    📄 {page_content['title']}")
                        if page_content['apCount'] > 0 or page_content['switchCount'] > 0:
                            print(f"    🔍 Devices found: APs={page_content['apCount']}, Switches={page_content['switchCount']}")
                        
                except Exception as e:
                    print(f"    ⚠️ Error: {e}")
            
            # Summary of captured API requests
            print(f"\n🎯 CAPTURED API REQUESTS:")
            for i, req in enumerate(captured_requests, 1):
                print(f"\n[{i}] {req['method']} {req['url']}")
                if req['post_data']:
                    print(f"    Data: {req['post_data'][:100]}...")
            
            # Save captured requests
            with open("captured_api_requests.json", "w") as f:
                json.dump(captured_requests, f, indent=2)
            
            print(f"\n📄 Captured {len(captured_requests)} API requests to captured_api_requests.json")
            
        except Exception as e:
            print(f"❌ Navigation error: {e}")
            await page.screenshot(path="navigation_error.png")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_wifi_switch_api_requests())
