#!/usr/bin/env python3
"""
Debug initApp function
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_init_app():
    """Debug why initApp is not working"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Console logging
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"{msg.type}: {msg.text}")
            print(f"📋 {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
        
        # Navigate to the main page
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        print("🔍 Debugging initApp Function")
        print("=" * 50)
        
        # Check if window.initApp exists
        init_app_exists = await page.evaluate("""
            () => {
                return typeof window.initApp === 'function';
            }
        """)
        
        print(f"window.initApp exists: {init_app_exists}")
        
        # Check if window.dependenciesLoaded is true
        dependencies_loaded = await page.evaluate("""
            () => {
                return window.dependenciesLoaded === true;
            }
        """)
        
        print(f"window.dependenciesLoaded: {dependencies_loaded}")
        
        # Check if THREE.js is loaded
        three_loaded = await page.evaluate("""
            () => {
                return typeof window.THREE !== 'undefined';
            }
        """)
        
        print(f"THREE.js loaded: {three_loaded}")
        
        # Check canvas element
        canvas_exists = await page.evaluate("""
            () => {
                const canvas = document.getElementById('topology-canvas');
                return !!canvas;
            }
        """)
        
        print(f"Canvas element exists: {canvas_exists}")
        
        # Try to manually call initApp
        print("\n🔧 Attempting manual initApp call...")
        try:
            init_result = await page.evaluate("""
                () => {
                    if (window.initApp) {
                        try {
                            window.initApp();
                            return 'initApp called successfully';
                        } catch (error) {
                            return 'initApp error: ' + error.message;
                        }
                    } else {
                        return 'initApp not available';
                    }
                }
            """)
            
            print(f"Manual initApp result: {init_result}")
            
        except Exception as e:
            print(f"Error calling initApp: {e}")
        
        # Check if scene was created after manual init
        await asyncio.sleep(2)
        
        scene_exists = await page.evaluate("""
            () => {
                return !!window.scene;
            }
        """)
        
        print(f"Scene exists after init: {scene_exists}")
        
        if scene_exists:
            scene_objects = await page.evaluate("""
                () => {
                    return window.scene.children.length;
                }
            """)
            
            print(f"Scene objects count: {scene_objects}")
        
        # Try loading topology after manual init
        print("\n🔥 Testing Load Fortinet after manual init...")
        load_fortinet = page.locator("button:has-text('🔥 Load Fortinet')")
        if await load_fortinet.count() > 0:
            await load_fortinet.click()
            await asyncio.sleep(3)
            
            # Check scene objects after loading
            scene_objects = await page.evaluate("""
                () => {
                    return window.scene ? window.scene.children.length : 0;
                }
            """)
            
            print(f"Scene objects after loading: {scene_objects}")
        
        print("\n🔍 Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_init_app())
