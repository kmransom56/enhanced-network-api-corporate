#!/usr/bin/env python3
"""
Debug JavaScript runtime errors
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_js_errors():
    """Debug JavaScript runtime errors in app.js"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Console logging with more detail
        console_messages = []
        def handle_console(msg):
            console_messages.append({
                'type': msg.type,
                'text': msg.text,
                'location': msg.location
            })
            print(f"📋 [{msg.type}] {msg.text}")
            if msg.location:
                print(f"   📍 {msg.location['url']}:{msg.location['lineNumber']}")
        
        page.on("console", handle_console)
        
        # Also listen for page errors
        page.on("pageerror", lambda error: print(f"🚨 PAGE ERROR: {error}"))
        
        # Navigate to the main page
        print("🔍 Debugging JavaScript Runtime Errors")
        print("=" * 50)
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        # Wait a bit more for any delayed script execution
        await asyncio.sleep(3)
        
        # Check for errors in console
        error_messages = [msg for msg in console_messages if msg['type'] == 'error']
        
        if error_messages:
            print(f"\n❌ Found {len(error_messages)} JavaScript errors:")
            for i, error in enumerate(error_messages):
                print(f"\n   Error {i+1}:")
                print(f"   Message: {error['text']}")
                if error['location']:
                    print(f"   Location: {error['location']['url']}:{error['location']['lineNumber']}")
        else:
            print("\n✅ No JavaScript errors detected in console")
        
        # Try to execute a simple test to see if JavaScript is working
        print("\n🧪 Testing JavaScript execution...")
        try:
            test_result = await page.evaluate("""
                () => {
                    // Simple test to see if JavaScript evaluation works
                    return 'JavaScript is working: ' + (2 + 2);
                }
            """)
            print(f"   JavaScript test result: {test_result}")
        except Exception as e:
            print(f"   JavaScript evaluation failed: {e}")
        
        # Try to manually execute parts of app.js
        print("\n🔧 Attempting to manually execute initApp...")
        try:
            # First, let's try to check if the canvas element exists
            canvas_check = await page.evaluate("""
                () => {
                    const canvas = document.getElementById('topology-canvas');
                    if (!canvas) {
                        return 'Canvas not found';
                    }
                    return 'Canvas found, ready for Three.js';
                }
            """)
            print(f"   Canvas check: {canvas_check}")
            
            # Try to manually create a simple Three.js scene
            three_test = await page.evaluate("""
                () => {
                    try {
                        if (typeof THREE === 'undefined') {
                            return 'THREE.js not loaded';
                        }
                        
                        const canvas = document.getElementById('topology-canvas');
                        if (!canvas) {
                            return 'Canvas not found';
                        }
                        
                        // Simple Three.js test
                        const scene = new THREE.Scene();
                        const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
                        const renderer = new THREE.WebGLRenderer({ canvas: canvas });
                        
                        renderer.setSize(canvas.clientWidth, canvas.clientHeight);
                        renderer.render(scene, camera);
                        
                        return 'Three.js test successful';
                    } catch (error) {
                        return 'Three.js test failed: ' + error.message;
                    }
                }
            """)
            print(f"   Three.js test: {three_test}")
            
        except Exception as e:
            print(f"   Manual execution failed: {e}")
        
        # Try to check if there are any syntax errors in app.js
        print("\n📝 Checking app.js syntax...")
        try:
            syntax_check = await page.evaluate("""
                () => {
                    try {
                        // Try to parse app.js content
                        fetch('/static/app.js')
                            .then(response => response.text())
                            .then(content => {
                                // Try to eval the content (this might reveal syntax errors)
                                try {
                                    eval(content);
                                    return 'app.js syntax appears valid';
                                } catch (syntaxError) {
                                    return 'Syntax error in app.js: ' + syntaxError.message;
                                }
                            })
                            .catch(error => 'Failed to fetch app.js: ' + error.message);
                        
                        return 'Checking syntax...';
                    } catch (error) {
                        return 'Syntax check failed: ' + error.message;
                    }
                }
            """)
            print(f"   Syntax check: {syntax_check}")
            
        except Exception as e:
            print(f"   Syntax check failed: {e}")
        
        print("\n🔍 Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_js_errors())
