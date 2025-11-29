#!/usr/bin/env python3
"""
Debug app.js loading issues
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_app_js_loading():
    """Debug why app.js is not loading properly"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Console logging
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"{msg.type}: {msg.text}")
            if msg.type == "error":
                print(f"❌ ERROR: {msg.text}")
            else:
                print(f"📋 {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
        
        # Monitor network requests
        network_requests = []
        def handle_request(request):
            network_requests.append(f"Request: {request.url}")
            if "app.js" in request.url:
                print(f"🌐 Loading: {request.url}")
        
        def handle_response(response):
            if "app.js" in response.url:
                status = response.status
                print(f"📦 Response: {response.url} - Status: {status}")
                if status != 200:
                    print(f"❌ Failed to load app.js - Status {status}")
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        # Navigate to the main page
        print("🔍 Debugging app.js Loading")
        print("=" * 50)
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        # Check if app.js was loaded
        app_js_loaded = await page.evaluate("""
            () => {
                // Check if any global variables from app.js exist
                return typeof window.initApp === 'function' || 
                       typeof window.loadFortinetTopologyScene === 'function' ||
                       typeof window.clearScene === 'function';
            }
        """)
        
        print(f"app.js functions available: {app_js_loaded}")
        
        # Check for script loading errors
        script_errors = [msg for msg in console_messages if "script" in msg.lower() or "syntax" in msg.lower()]
        if script_errors:
            print(f"\n⚠️  Script-related errors:")
            for error in script_errors:
                print(f"   {error}")
        
        # Try to manually load app.js
        print("\n🔧 Attempting to manually load app.js...")
        try:
            manual_load = await page.evaluate("""
                () => {
                    const script = document.createElement('script');
                    script.src = '/static/app.js';
                    script.onload = () => 'app.js loaded successfully';
                    script.onerror = (error) => 'app.js load error: ' + error;
                    document.head.appendChild(script);
                    return 'Loading app.js...';
                }
            """)
            
            print(f"Manual load result: {manual_load}")
            await asyncio.sleep(3)
            
            # Check again if functions are available
            functions_available = await page.evaluate("""
                () => {
                    return {
                        initApp: typeof window.initApp === 'function',
                        loadFortinetTopologyScene: typeof window.loadFortinetTopologyScene === 'function',
                        clearScene: typeof window.clearScene === 'function'
                    };
                }
            """)
            
            print(f"Functions after manual load: {functions_available}")
            
        except Exception as e:
            print(f"Error manually loading app.js: {e}")
        
        # Check app.js content
        print("\n📄 Checking app.js content...")
        try:
            app_js_response = await page.goto("http://127.0.0.1:11111/static/app.js")
            if app_js_response:
                content = await app_js_response.text()
                print(f"app.js size: {len(content)} characters")
                print(f"app.js first 100 chars: {content[:100]}...")
                
                # Check for window.initApp in the content
                if "window.initApp" in content:
                    print("✅ window.initApp found in app.js content")
                else:
                    print("❌ window.initApp NOT found in app.js content")
            else:
                print("❌ Failed to fetch app.js content")
                
        except Exception as e:
            print(f"Error checking app.js content: {e}")
        
        print("\n🔍 Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_app_js_loading())
