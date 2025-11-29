#!/usr/bin/env python3
"""
Test script to access FortiGate web GUI using Playwright
to discover managed devices (FortiSwitch, FortiAPs) through the web interface
"""

import asyncio
from playwright.async_api import async_playwright
import os

async def access_fortigate_gui():
    """Access FortiGate web GUI and discover managed devices"""
    
    fortigate_url = "https://192.168.0.254:10443"
    
    async with async_playwright() as p:
        # Launch browser with SSL verification disabled
        browser = await p.chromium.launch(
            headless=False,  # Show browser for debugging
        )
        
        # Create context with SSL verification disabled
        context = await browser.new_context(
            ignore_https_errors=True
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to FortiGate login page
            print(f"Navigating to {fortigate_url}")
            await page.goto(fortigate_url, timeout=30000)
            
            # Wait for page to load
            await page.wait_for_load_state('networkidle')
            
            # Take screenshot of login page
            await page.screenshot(path="fortigate_login.png")
            print("Login page screenshot saved as fortigate_login.png")
            
            # Check if we're on login page or already logged in
            page_content = await page.content()
            
            if "login" in page_content.lower() or "username" in page_content.lower():
                print("Detected login page")
                
                # Try known FortiGate credentials (correct one first)
                credentials_to_try = [
                    {"username": "admin", "password": "!cg@RW%G@o"},
                    {"username": "admin", "password": ""},
                    {"username": "admin", "password": "admin"},
                    {"username": "admin", "password": "password"},
                    {"username": "admin", "password": "fortinet"},
                ]
                
                for creds in credentials_to_try:
                    print(f"Trying credentials: {creds['username']} / {'*' * len(creds['password'])}")
                    
                    try:
                        # Fill username
                        await page.fill('input[name="username"], input[id="username"], input[type="text"]', creds['username'], timeout=5000)
                        
                        # Fill password
                        await page.fill('input[name="password"], input[id="password"], input[type="password"]', creds['password'], timeout=5000)
                        
                        # Try multiple login button selectors
                        login_selectors = [
                            'input[type="submit"]',
                            'button[type="submit"]',
                            'button:has-text("Login")',
                            'button:has-text("Log In")',
                            'button:has-text("Sign in")',
                            '.login-button',
                            '#login-button',
                            'form button'
                        ]
                        
                        login_clicked = False
                        for selector in login_selectors:
                            try:
                                await page.click(selector, timeout=2000)
                                login_clicked = True
                                print(f"Clicked login button with selector: {selector}")
                                break
                            except:
                                continue
                        
                        if not login_clicked:
                            print("Could not find login button, trying to press Enter")
                            await page.press('input[name="password"], input[id="password"], input[type="password"]', 'Enter')
                        
                        # Wait for navigation
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        
                        # Check if login was successful
                        current_url = page.url
                        if "login" not in current_url.lower():
                            print(f"✅ Login successful! Current URL: {current_url}")
                            break
                        else:
                            print("❌ Login failed")
                            await page.goto(fortigate_url, timeout=10000)  # Go back to login page
                            
                    except Exception as e:
                        print(f"Error with credentials {creds['username']}: {e}")
                        await page.goto(fortigate_url, timeout=10000)  # Go back to login page
                
            else:
                print("Already logged in or different page detected")
            
            # Take screenshot after login attempt
            await page.screenshot(path="fortigate_after_login.png")
            print("After login screenshot saved as fortigate_after_login.png")
            
            # Look for device information
            print("Searching for device information...")
            
            # Look for navigation menus that might contain device info
            device_menu_selectors = [
                'a:has-text("Switch")',
                'a:has-text("WiFi")', 
                'a:has-text("Wireless")',
                'a:has-text("Device")',
                'a:has-text("FortiSwitch")',
                'a:has-text("FortiAP")',
                'a:has-text("Network")',
                'a:has-text("Topology")',
                'a:has-text("Monitor")'
            ]
            
            for selector in device_menu_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        print(f"Found menu item: {selector}")
                        await element.click()
                        await page.wait_for_load_state('networkidle', timeout=5000)
                        
                        # Take screenshot of this page
                        page_name = selector.replace('a:has-text("', '').replace('")', '').replace(' ', '_')
                        await page.screenshot(path=f"fortigate_{page_name.lower()}.png")
                        print(f"Screenshot saved as fortigate_{page_name.lower()}.png")
                        
                        # Look for device lists on this page
                        device_info = await page.evaluate("""
                            () => {
                                // Look for device tables or lists
                                const tables = document.querySelectorAll('table');
                                const deviceData = [];
                                
                                tables.forEach(table => {
                                    const rows = table.querySelectorAll('tr');
                                    rows.forEach(row => {
                                        const cells = row.querySelectorAll('td');
                                        if (cells.length > 2) {
                                            const rowData = Array.from(cells).map(cell => cell.textContent.trim());
                                            if (rowData.some(cell => cell.toLowerCase().includes('switch') || 
                                                             cell.toLowerCase().includes('ap') || 
                                                             cell.toLowerCase().includes('forti'))) {
                                                deviceData.push(rowData);
                                            }
                                        }
                                    });
                                });
                                
                                return deviceData;
                            }
                        """)
                        
                        if device_info:
                            print(f"Found device information on {page_name}:")
                            for device in device_info[:5]:  # Show first 5 devices
                                print(f"  {device}")
                        
                        break  # Found device info, stop searching
                        
                except Exception as e:
                    continue  # Try next selector
            
            # Finally, take a screenshot of the current state
            await page.screenshot(path="fortigate_final.png")
            print("Final screenshot saved as fortigate_final.png")
            
        except Exception as e:
            print(f"Error accessing FortiGate GUI: {e}")
            await page.screenshot(path="fortigate_error.png")
            
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(access_fortigate_gui())
