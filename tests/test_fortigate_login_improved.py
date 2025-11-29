#!/usr/bin/env python3
"""
Improved FortiGate web GUI login and navigation script
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time

async def login_and_explore_fortigate():
    """Login to FortiGate and explore available device information"""
    
    fortigate_url = "https://192.168.0.254:10443"
    username = "admin"
    password = "!cg@RW%G@o"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        try:
            print(f"Navigating to {fortigate_url}")
            await page.goto(fortigate_url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Take screenshot of login page
            await page.screenshot(path="01_fortigate_login_page.png")
            print("Login page screenshot saved")
            
            # Wait for login form to be ready
            await page.wait_for_timeout(2000)
            
            # Try to fill login form with multiple selectors
            try:
                # Username field
                username_selectors = [
                    'input[name="username"]',
                    'input[id="username"]',
                    'input[type="text"]',
                    'input[placeholder*="user"]',
                    'input[placeholder*="name"]'
                ]
                
                username_filled = False
                for selector in username_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=2000)
                        await page.fill(selector, username)
                        username_filled = True
                        print(f"Filled username with selector: {selector}")
                        break
                    except:
                        continue
                
                if not username_filled:
                    print("Could not find username field")
                    return
                
                # Password field
                password_selectors = [
                    'input[name="password"]',
                    'input[id="password"]',
                    'input[type="password"]',
                    'input[placeholder*="pass"]'
                ]
                
                password_filled = False
                for selector in password_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=2000)
                        await page.fill(selector, password)
                        password_filled = True
                        print(f"Filled password with selector: {selector}")
                        break
                    except:
                        continue
                
                if not password_filled:
                    print("Could not find password field")
                    return
                
                # Submit login
                await page.wait_for_timeout(1000)
                
                # Try multiple login methods
                login_success = False
                
                # Method 1: Click login button
                login_button_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Log In")',
                    'button:has-text("Sign in")',
                    '.login-btn',
                    '#login-btn'
                ]
                
                for selector in login_button_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        print(f"Clicked login button: {selector}")
                        login_success = True
                        break
                    except:
                        continue
                
                # Method 2: Press Enter in password field
                if not login_success:
                    try:
                        await page.press('input[type="password"]', 'Enter')
                        print("Pressed Enter in password field")
                        login_success = True
                    except:
                        pass
                
                # Method 3: Submit form
                if not login_success:
                    try:
                        await page.evaluate('document.querySelector("form").submit()')
                        print("Submitted form")
                        login_success = True
                    except:
                        pass
                
                # Wait for navigation after login
                await page.wait_for_timeout(5000)
                
                # Check if login was successful
                current_url = page.url
                print(f"Current URL after login attempt: {current_url}")
                
                if "login" not in current_url.lower():
                    print("✅ Login successful!")
                    await page.screenshot(path="02_fortigate_after_login.png")
                    
                    # Explore the interface
                    await explore_fortigate_interface(page)
                    
                else:
                    print("❌ Login failed - still on login page")
                    await page.screenshot(path="02_fortigate_login_failed.png")
                    
            except Exception as e:
                print(f"Login error: {e}")
                await page.screenshot(path="02_fortigate_login_error.png")
                
        except Exception as e:
            print(f"Navigation error: {e}")
            
        finally:
            await browser.close()

async def explore_fortigate_interface(page):
    """Explore FortiGate interface to find device information"""
    
    print("Exploring FortiGate interface...")
    
    # Wait for page to fully load
    await page.wait_for_timeout(3000)
    
    # Take screenshot of main dashboard
    await page.screenshot(path="03_fortigate_dashboard.png")
    print("Dashboard screenshot saved")
    
    # Look for navigation menus
    menu_items_to_explore = [
        "Switch",
        "WiFi", 
        "Wireless",
        "Device",
        "FortiSwitch",
        "FortiAP",
        "Network",
        "Topology",
        "Monitor",
        "System"
    ]
    
    for menu_text in menu_items_to_explore:
        try:
            # Look for menu item
            menu_selector = f':has-text("{menu_text}")'
            elements = await page.query_selector_all(menu_selector)
            
            for element in elements:
                try:
                    text = await element.text_content()
                    if text and menu_text.lower() in text.lower():
                        print(f"Found menu item: {text.strip()}")
                        
                        # Click on it
                        await element.click()
                        await page.wait_for_timeout(2000)
                        
                        # Take screenshot
                        safe_filename = menu_text.replace(" ", "_").lower()
                        await page.screenshot(path=f"04_{safe_filename}_page.png")
                        print(f"Screenshot saved: {safe_filename}_page.png")
                        
                        # Look for device lists or tables
                        await look_for_device_info(page, menu_text)
                        
                        # Go back
                        await page.go_back()
                        await page.wait_for_timeout(1000)
                        break
                        
                except Exception as e:
                    print(f"Error exploring {menu_text}: {e}")
                    continue
                    
        except Exception as e:
            continue
    
    # Look for any device-related information on current page
    await look_for_device_info(page, "dashboard")

async def look_for_device_info(page, context):
    """Look for device information on the current page"""
    
    try:
        # Look for tables that might contain device information
        tables = await page.query_selector_all('table')
        
        device_found = False
        for i, table in enumerate(tables):
            try:
                # Get table content
                rows = await table.query_selector_all('tr')
                
                device_rows = []
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    if len(cells) > 2:
                        cell_texts = []
                        for cell in cells:
                            text = await cell.text_content()
                            if text:
                                cell_texts.append(text.strip())
                        
                        # Check if this looks like device information
                        row_text = ' '.join(cell_texts).lower()
                        if any(keyword in row_text for keyword in ['switch', 'ap', 'forti', 'device', '192.168']):
                            device_rows.append(cell_texts)
                            device_found = True
                
                if device_rows:
                    print(f"Found device information in {context} table {i}:")
                    for row in device_rows[:5]:  # Show first 5 rows
                        print(f"  {row}")
                    
                    # Save table content
                    with open(f"device_info_{context.lower()}.json", "w") as f:
                        json.dump(device_rows, f, indent=2)
                        
            except Exception as e:
                continue
        
        # Also look for any device-related cards or panels
        device_cards = await page.query_selector_all('[class*="device"], [class*="switch"], [class*="ap"], [class*="forti"]')
        
        for card in device_cards:
            try:
                text = await card.text_content()
                if text and any(keyword in text.lower() for keyword in ['switch', 'ap', 'forti', 'device']):
                    print(f"Found device card in {context}: {text.strip()[:100]}")
            except:
                continue
                
        if not device_found:
            print(f"No device information found in {context}")
            
    except Exception as e:
        print(f"Error looking for device info in {context}: {e}")

if __name__ == "__main__":
    asyncio.run(login_and_explore_fortigate())
