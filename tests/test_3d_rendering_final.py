#!/usr/bin/env python3
"""
Final verification that 3D rendering is working
"""

import asyncio
from playwright.async_api import async_playwright

async def test_3d_rendering_final():
    """Final test to verify 3D rendering is working"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Console logging
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"{msg.type}: {msg.text}")
            if msg.type in ["error", "warning"]:
                print(f"⚠️  {msg.type.upper()}: {msg.text}")
            elif "success" in msg.text.lower() or "loaded" in msg.text.lower():
                print(f"✅ {msg.text}")
        
        page.on("console", handle_console)
        
        # Navigate to the main page
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        print("🎯 Final 3D Rendering Verification")
        print("=" * 50)
        
        # Test Demo Mode (which has the most devices)
        print("\n🎭 Loading Demo Mode for 3D verification...")
        three_objects = None
        demo_button = page.locator("button:has-text('🎭 Demo Mode')")
        if await demo_button.count() > 0:
            await demo_button.click()
            await asyncio.sleep(5)
            
            # Check Three.js objects
            three_objects = await page.evaluate("""
                () => {
                    if (window.scene) {
                        return {
                            total_objects: window.scene.children.length,
                            device_meshes: window.scene.children.filter(obj => obj.userData.type).length,
                            camera_position: {
                                x: window.camera.position.x,
                                y: window.camera.position.y,
                                z: window.camera.position.z
                            },
                            renderer_working: !!window.renderer
                        };
                    }
                    return null;
                }
            """)
            
            if three_objects:
                print(f"   🎯 Three.js Scene Status:")
                print(f"      Total objects: {three_objects['total_objects']}")
                print(f"      Device meshes: {three_objects['device_meshes']}")
                print(f"      Camera position: ({three_objects['camera_position']['x']}, {three_objects['camera_position']['y']}, {three_objects['camera_position']['z']})")
                print(f"      Renderer working: {three_objects['renderer_working']}")
                
                if three_objects['device_meshes'] > 0:
                    print(f"\n   ✅ SUCCESS: {three_objects['device_meshes']} 3D devices rendered!")
                    print(f"   🎨 The 3D topology should be visible in the browser canvas.")
                else:
                    print(f"\n   ❌ ISSUE: No device meshes found in scene")
            else:
                print(f"   ❌ ISSUE: Three.js scene not initialized")
        else:
            print("   ❌ Demo Mode button not found")
        
        # Take a screenshot to verify visual output
        await page.screenshot(path="test_screenshots/final_3d_verification.png")
        print(f"\n   📸 Screenshot saved: test_screenshots/final_3d_verification.png")
        
        # Test Load Fortinet as well
        print("\n🔥 Testing Load Fortinet...")
        load_fortinet = page.locator("button:has-text('🔥 Load Fortinet')")
        if await load_fortinet.count() > 0:
            await load_fortinet.click()
            await asyncio.sleep(3)
            
            fortinet_objects = await page.evaluate("""
                () => {
                    if (window.scene) {
                        return window.scene.children.filter(obj => obj.userData.type).length;
                    }
                    return 0;
                }
            """)
            
            print(f"   📊 Fortinet devices rendered: {fortinet_objects}")
        
        print("\n🔍 Final Status:")
        if three_objects and three_objects.get('device_meshes', 0) > 0:
            print("   ✅ 3D RENDERING IS WORKING!")
            print("   ✅ Page should NOT be blank")
            print("   ✅ Devices should be visible in the canvas")
        else:
            print("   ❌ 3D rendering issues detected")
        
        print("\n🔍 Keeping browser open for 10 seconds for manual inspection...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_3d_rendering_final())
