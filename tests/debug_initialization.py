#!/usr/bin/env python3
"""
Debug why initApp is not being called
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_initialization():
    """Debug why initApp is not being called"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Console logging
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"{msg.type}: {msg.text}")
            if "init" in msg.text.lower() or "app" in msg.text.lower():
                print(f"🔧 {msg.type}: {msg.text}")
            elif msg.type == "error":
                print(f"❌ {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
        
        # Navigate to the main page
        print("🔍 Debugging Initialization Issues")
        print("=" * 50)
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        # Wait a bit for initialization
        await asyncio.sleep(3)
        
        # Check if initApp was called
        init_app_called = any("initApp" in msg for msg in console_messages)
        print(f"\n📋 initApp called: {init_app_called}")
        
        # Check if window.initApp exists
        init_app_exists = await page.evaluate("""
            () => {
                return typeof window.initApp === 'function';
            }
        """)
        
        print(f"📋 window.initApp exists: {init_app_exists}")
        
        # Check if dependenciesLoaded is true
        dependencies_loaded = await page.evaluate("""
            () => {
                return window.dependenciesLoaded === true;
            }
        """)
        
        print(f"📋 dependenciesLoaded: {dependencies_loaded}")
        
        # Check if scene was initialized
        scene_exists = await page.evaluate("""
            () => {
                return !!window.scene;
            }
        """)
        
        print(f"📋 window.scene exists: {scene_exists}")
        
        # Check if initializeVisualization was called
        init_viz_called = any("initializeVisualization" in msg for msg in console_messages)
        print(f"📋 initializeVisualization called: {init_viz_called}")
        
        # Try to manually call initializeVisualization
        print("\n🔧 Attempting manual initialization...")
        try:
            manual_init = await page.evaluate("""
                () => {
                    if (window.initializeVisualization) {
                        window.initializeVisualization();
                        return 'initializeVisualization called';
                    } else if (window.initApp) {
                        window.initApp();
                        return 'initApp called';
                    } else {
                        return 'No initialization function available';
                    }
                }
            """)
            
            print(f"   Manual init result: {manual_init}")
            
            # Wait for initialization to complete
            await asyncio.sleep(3)
            
            # Check if scene exists after manual init
            scene_after_init = await page.evaluate("""
                () => {
                    return !!window.scene;
                }
            """)
            
            print(f"   Scene exists after manual init: {scene_after_init}")
            
            if scene_after_init:
                # Check Three.js objects
                three_objects = await page.evaluate("""
                    () => {
                        if (window.scene) {
                            return window.scene.children.length;
                        }
                        return 0;
                    }
                """)
                
                print(f"   Three.js objects: {three_objects}")
                
        except Exception as e:
            print(f"   Manual init failed: {e}")
        
        # Check for any initialization errors
        init_errors = [msg for msg in console_messages if "init" in msg.lower() and "error" in msg.lower()]
        if init_errors:
            print(f"\n⚠️  Initialization errors:")
            for error in init_errors:
                print(f"   {error}")
        
        print("\n🔍 Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_initialization())
