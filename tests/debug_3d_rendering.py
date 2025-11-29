#!/usr/bin/env python3
"""
Debug 3D rendering issues
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_3d_rendering():
    """Debug why the 3D scene might not be visible"""
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
        
        print("🔍 Debugging 3D Rendering Issues")
        print("=" * 50)
        
        # Check canvas element
        canvas = page.locator("#topology-canvas")
        if await canvas.count() > 0:
            print("✅ Canvas element found")
            
            # Check canvas properties
            canvas_visible = await canvas.is_visible()
            canvas_size = await canvas.bounding_box()
            
            print(f"   Canvas visible: {canvas_visible}")
            if canvas_size:
                print(f"   Canvas size: {canvas_size['width']}x{canvas_size['height']}")
            else:
                print("   Canvas size: Not available")
        else:
            print("❌ Canvas element not found")
            return
        
        # Test Load Fortinet
        print("\n🔥 Testing Load Fortinet...")
        load_fortinet = page.locator("button:has-text('🔥 Load Fortinet')")
        if await load_fortinet.count() > 0:
            await load_fortinet.click()
            await asyncio.sleep(3)
            
            # Check Three.js objects
            three_objects = await page.evaluate("""
                () => {
                    if (window.scene) {
                        return window.scene.children.length;
                    }
                    return 0;
                }
            """)
            
            print(f"   Three.js objects in scene: {three_objects}")
            
            # Check if renderer is working
            renderer_info = await page.evaluate("""
                () => {
                    if (window.renderer) {
                        return {
                            domElement: !!window.renderer.domElement,
                            context: !!window.renderer.getContext(),
                            size: window.renderer.getSize ? window.renderer.getSize() : 'unknown'
                        };
                    }
                    return null;
                }
            """)
            
            print(f"   Renderer info: {renderer_info}")
            
            # Check camera position
            camera_info = await page.evaluate("""
                () => {
                    if (window.camera) {
                        return {
                            position: {
                                x: window.camera.position.x,
                                y: window.camera.position.y,
                                z: window.camera.position.z
                            }
                        };
                    }
                    return null;
                }
            """)
            
            print(f"   Camera position: {camera_info}")
            
        else:
            print("❌ Load Fortinet button not found")
        
        # Test Demo Mode
        print("\n🎭 Testing Demo Mode...")
        demo_button = page.locator("button:has-text('🎭 Demo Mode')")
        if await demo_button.count() > 0:
            await demo_button.click()
            await asyncio.sleep(3)
            
            # Check Three.js objects after demo
            three_objects = await page.evaluate("""
                () => {
                    if (window.scene) {
                        return window.scene.children.length;
                    }
                    return 0;
                }
            """)
            
            print(f"   Three.js objects after demo: {three_objects}")
            
            # Check for device meshes
            device_meshes = await page.evaluate("""
                () => {
                    if (window.scene) {
                        return window.scene.children.filter(obj => obj.userData.type).length;
                    }
                    return 0;
                }
            """)
            
            print(f"   Device meshes: {device_meshes}")
            
        else:
            print("❌ Demo Mode button not found")
        
        # Take screenshot
        await page.screenshot(path="test_screenshots/debug_3d_state.png")
        print("\n📸 Screenshot saved")
        
        # Check for any WebGL errors
        webgl_errors = [msg for msg in console_messages if "webgl" in msg.lower() or "context" in msg.lower()]
        if webgl_errors:
            print(f"\n⚠️  WebGL-related issues:")
            for error in webgl_errors:
                print(f"   {error}")
        
        # Check for Three.js errors
        threejs_errors = [msg for msg in console_messages if "three" in msg.lower() or "renderer" in msg.lower()]
        if threejs_errors:
            print(f"\n⚠️  Three.js-related issues:")
            for error in threejs_errors:
                print(f"   {error}")
        
        print("\n🔍 Keeping browser open for 10 seconds for manual inspection...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_3d_rendering())
