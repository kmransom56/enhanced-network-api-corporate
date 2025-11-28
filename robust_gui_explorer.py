#!/usr/bin/env python3
"""
Robust GUI Explorer - Navigate and capture API requests with better login handling
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time

async def robust_gui_explorer():
    """Navigate GUI and capture API requests with improved login handling"""
    
    fortigate_url = "https://192.168.0.254:10443"
    username = "admin"
    password = "!cg@RW%G@o"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=800)
        context = await browser.new_context(ignore_https_errors=True)
        
        # Enable request interception
        page = await context.new_page()
        
        captured_requests = []
        
        async def log_request(request):
            """Capture API requests"""
            url = request.url
            if '/api/' in url and any(keyword in url.lower() for keyword in ['ap', 'wifi', 'switch', 'wireless', 'device', 'forti']):
                captured_requests.append({
                    'url': url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data,
                    'timestamp': time.time()
                })
                print(f"🔍 API: {request.method} {url}")
        
        page.on("request", log_request)
        
        try:
            print(f"🔐 Logging into {fortigate_url}")
            await page.goto(fortigate_url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Wait a bit for the page to fully load
            await page.wait_for_timeout(2000)
            
            # Try multiple selectors for login fields
            username_selectors = [
                'input[name="username"]',
                'input[id="username"]',
                'input[placeholder*="user"]',
                'input[type="text"]'
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[id="password"]',
                'input[placeholder*="pass"]',
                'input[type="password"]'
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        await element.fill(username)
                        username_filled = True
                        print(f"✅ Filled username with selector: {selector}")
                        break
                except:
                    continue
            
            if not username_filled:
                print("❌ Could not find username field")
                return
            
            password_filled = False
            for selector in password_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        await element.fill(password)
                        password_filled = True
                        print(f"✅ Filled password with selector: {selector}")
                        break
                except:
                    continue
            
            if not password_filled:
                print("❌ Could not find password field")
                return
            
            # Try to submit login
            login_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Log in")',
                'button:has-text("Sign in")',
                '.login-button',
                '#login'
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        await element.click()
                        login_clicked = True
                        print(f"✅ Clicked login with selector: {selector}")
                        break
                except:
                    continue
            
            if not login_clicked:
                print("⚠️ Could not find login button, trying Enter key")
                await page.press('input[name="password"], input[id="password"]', 'Enter')
            
            # Wait for login to complete
            await page.wait_for_timeout(5000)
            
            if "login" in page.url.lower():
                print("❌ Login failed")
                await page.screenshot(path="login_failed.png")
                return
            
            print("✅ Login successful!")
            await page.screenshot(path="login_success.png")
            
            # Navigate and explore
            await explore_wifi_switch_pages(page, fortigate_url, captured_requests)
            
        except Exception as e:
            print(f"❌ Navigation error: {e}")
            await page.screenshot(path="exploration_error.png")
            
        finally:
            await browser.close()

async def explore_wifi_switch_pages(page, base_url, captured_requests):
    """Explore WiFi & Switch Controller pages"""
    
    print(f"\n🔍 Exploring WiFi & Switch Controller pages...")
    
    # Define pages to explore
    pages_to_explore = [
        {
            'name': 'WiFi & Switch Controller Main',
            'selectors': [':has-text("WiFi & Switch Controller")'],
            'screenshot': 'wifi_switch_main'
        },
        {
            'name': 'Managed FortiSwitches',
            'selectors': [':has-text("Managed FortiSwitches")', ':has-text("FortiSwitch")'],
            'screenshot': 'managed_switches'
        },
        {
            'name': 'Managed FortiAPs', 
            'selectors': [':has-text("Managed FortiAPs")', ':has-text("FortiAP")'],
            'screenshot': 'managed_aps'
        },
        {
            'name': 'Switch Controller',
            'selectors': [':has-text("Switch Controller")'],
            'screenshot': 'switch_controller'
        },
        {
            'name': 'Wireless Controller',
            'selectors': [':has-text("Wireless Controller")'],
            'screenshot': 'wireless_controller'
        }
    ]
    
    for page_info in pages_to_explore:
        print(f"\n🔍 Exploring: {page_info['name']}")
        
        # Try different selectors
        navigated = False
        for selector in page_info['selectors']:
            try:
                await page.click(selector)
                await page.wait_for_timeout(3000)
                navigated = True
                print(f"  ✅ Navigated with selector: {selector}")
                break
            except:
                continue
        
        if not navigated:
            print(f"  ⚠️ Could not navigate to {page_info['name']}")
            continue
        
        # Take screenshot
        await page.screenshot(path=f"{page_info['screenshot']}.png")
        
        # Wait for API calls to complete
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
        
        # Look for device information
        device_info = await extract_device_info(page)
        if device_info:
            print(f"  📊 Device info: {device_info}")
        
        # Try to find and click on device details
        await explore_device_details(page)
        
        # Go back to main page
        await page.goto(f"{base_url}/ng")
        await page.wait_for_timeout(2000)

async def extract_device_info(page):
    """Extract device information from current page"""
    try:
        return await page.evaluate("""
            () => {
                const results = {
                    tables: [],
                    cards: [],
                    device_counts: {},
                    text_content: []
                };
                
                // Look for tables
                const tables = document.querySelectorAll('table');
                for (let table of tables) {
                    const rows = table.querySelectorAll('tr');
                    if (rows.length > 1) {
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
                        results.tables.push(tableData);
                    }
                }
                
                // Look for device counts
                const allElements = document.querySelectorAll('*');
                for (let el of allElements) {
                    const text = el.textContent || el.innerText;
                    if (text) {
                        // Look for AP counts
                        if (text.includes('AP') || text.includes('FortiAP')) {
                            const numbers = text.match(/(\\d+)\\s*(AP|FortiAP)/i);
                            if (numbers) {
                                results.device_counts.ap = parseInt(numbers[1]);
                            }
                        }
                        
                        // Look for Switch counts
                        if (text.includes('Switch') || text.includes('FortiSwitch')) {
                            const numbers = text.match(/(\\d+)\\s*(Switch|FortiSwitch)/i);
                            if (numbers) {
                                results.device_counts.switch = parseInt(numbers[1]);
                            }
                        }
                        
                        // Look for device status indicators
                        if (text.includes('online') || text.includes('connected') || text.includes('up')) {
                            const deviceKeywords = ['AP', 'FortiAP', 'Switch', 'FortiSwitch', 'device'];
                            for (let keyword of deviceKeywords) {
                                if (text.includes(keyword)) {
                                    results.text_content.push(text.trim());
                                    break;
                                }
                            }
                        }
                    }
                }
                
                return results;
            }
        """)
    except Exception as e:
        print(f"    ⚠️ Error extracting device info: {e}")
        return None

async def explore_device_details(page):
    """Try to click on device details to trigger more API calls"""
    try:
        # Look for clickable device elements
        clickable_elements = await page.evaluate("""
            () => {
                const elements = [];
                
                // Look for table rows that might be devices
                const rows = document.querySelectorAll('tr');
                for (let row of rows) {
                    const text = row.textContent || row.innerText;
                    if (text && (
                        text.includes('AP') || 
                        text.includes('FortiAP') || 
                        text.includes('Switch') || 
                        text.includes('FortiSwitch')
                    )) {
                        elements.push({
                            selector: 'tr',
                            text: text.trim().substring(0, 50),
                            clickable: row.style.cursor === 'pointer' || row.onclick !== null
                        });
                    }
                }
                
                // Look for cards or panels
                const cards = document.querySelectorAll('[class*="card"], [class*="panel"], [class*="device"]');
                for (let card of cards) {
                    const text = card.textContent || card.innerText;
                    if (text && (
                        text.includes('AP') || 
                        text.includes('FortiAP') || 
                        text.includes('Switch') || 
                        text.includes('FortiSwitch')
                    )) {
                        elements.push({
                            selector: '[class*="card"], [class*="panel"], [class*="device"]',
                            text: text.trim().substring(0, 50),
                            clickable: card.style.cursor === 'pointer' || card.onclick !== null
                        });
                    }
                }
                
                return elements;
            }
        """)
        
        # Try to click on first few clickable elements
        for i, element in enumerate(clickable_elements[:3]):  # Try first 3
            if element['clickable']:
                try:
                    print(f"    🔍 Clicking device: {element['text']}")
                    await page.click(element['selector'])
                    await page.wait_for_timeout(2000)
                    await page.screenshot(path=f"device_detail_{i}.png")
                    
                    # Go back
                    await page.go_back()
                    await page.wait_for_timeout(1000)
                except:
                    continue
    
    except Exception as e:
        print(f"    ⚠️ Error exploring device details: {e}")

if __name__ == "__main__":
    asyncio.run(robust_gui_explorer())
