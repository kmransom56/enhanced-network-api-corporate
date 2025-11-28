#!/usr/bin/env python3
"""
Check for JavaScript syntax errors
"""

import asyncio
from playwright.async_api import async_playwright

async def check_js_syntax():
    """Check for JavaScript syntax errors in app.js"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Console logging with all messages
        console_messages = []
        def handle_console(msg):
            console_messages.append({
                'type': msg.type,
                'text': msg.text,
                'location': msg.location
            })
            print(f"📋 [{msg.type}] {msg.text}")
            if msg.location:
                print(f"   📍 Line {msg.location['lineNumber']}: {msg.location['url']}")
        
        page.on("console", handle_console)
        
        # Listen for page errors (syntax errors, etc.)
        page.on("pageerror", lambda error: print(f"🚨 PAGE ERROR: {error}"))
        
        # Navigate to the main page
        print("🔍 Checking JavaScript Syntax Errors")
        print("=" * 50)
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        # Wait for any delayed script execution
        await asyncio.sleep(3)
        
        # Check for syntax errors
        syntax_errors = [msg for msg in console_messages if msg['type'] == 'error' and ('syntax' in msg['text'].lower() or 'unexpected' in msg['text'].lower())]
        
        if syntax_errors:
            print(f"\n❌ Found {len(syntax_errors)} syntax errors:")
            for i, error in enumerate(syntax_errors):
                print(f"\n   Syntax Error {i+1}:")
                print(f"   Message: {error['text']}")
                if error['location']:
                    print(f"   Location: {error['location']['url']}:{error['location']['lineNumber']}")
        else:
            print(f"\n✅ No syntax errors detected")
        
        # Check for any JavaScript errors
        js_errors = [msg for msg in console_messages if msg['type'] == 'error']
        
        if js_errors:
            print(f"\n⚠️  Found {len(js_errors)} JavaScript errors:")
            for i, error in enumerate(js_errors[:5]):  # Show first 5
                print(f"\n   Error {i+1}:")
                print(f"   Message: {error['text']}")
                if error['location']:
                    print(f"   Location: {error['location']['url']}:{error['location']['lineNumber']}")
        else:
            print(f"\n✅ No JavaScript errors detected")
        
        # Try to manually load app.js to check for syntax issues
        print(f"\n🔧 Testing app.js syntax...")
        try:
            app_js_content = await page.evaluate("""
                () => {
                    return fetch('/static/app.js')
                        .then(response => response.text())
                        .then(content => {
                            try {
                                // Try to parse/validate the content
                                const lines = content.split('\n');
                                return {
                                    totalLines: lines.length,
                                    firstLine: lines[0],
                                    lastLine: lines[lines.length - 1],
                                    hasInitApp: content.includes('window.initApp'),
                                    hasCanvas: content.includes('topology-canvas'),
                                    length: content.length
                                };
                            } catch (e) {
                                return { error: 'Failed to parse content: ' + e.message };
                            }
                        })
                        .catch(error => ({ error: 'Failed to fetch: ' + error.message }));
                }
            """)
            
            print(f"   app.js analysis:")
            print(f"      Total lines: {app_js_content.get('totalLines', 'unknown')}")
            print(f"      Length: {app_js_content.get('length', 'unknown')} chars")
            print(f"      Has window.initApp: {app_js_content.get('hasInitApp', 'unknown')}")
            print(f"      Has topology-canvas: {app_js_content.get('hasCanvas', 'unknown')}")
            
            if 'error' in app_js_content:
                print(f"      Error: {app_js_content['error']}")
            
        except Exception as e:
            print(f"   Failed to analyze app.js: {e}")
        
        print("\n🔍 Keeping browser open for 5 seconds...")
        await asyncio.sleep(5)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_js_syntax())
