#!/usr/bin/env python3
"""
Debug why the page is still blank
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_blank_page():
    """Debug why the page appears blank"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        # Console logging
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"{msg.type}: {msg.text}")
            if msg.type == "error":
                print(f"❌ ERROR: {msg.text}")
            elif "init" in msg.text.lower() or "scene" in msg.text.lower():
                print(f"🔧 {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
        
        # Navigate to the main page
        print("🔍 Debugging Blank Page Issue")
        print("=" * 50)
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        print("📄 Page loaded, checking what's visible...")
        
        # Check if canvas is visible and what it contains
        canvas = page.locator("#topology-canvas")
        if await canvas.count() > 0:
            canvas_visible = await canvas.is_visible()
            canvas_size = await canvas.bounding_box()
            
            print(f"   Canvas element: {'VISIBLE' if canvas_visible else 'HIDDEN'}")
            if canvas_size:
                print(f"   Canvas size: {canvas_size['width']}x{canvas_size['height']}")
            
            # Check canvas content (what's actually rendered)
            canvas_content = await page.evaluate("""
                () => {
                    const canvas = document.getElementById('topology-canvas');
                    if (!canvas) return 'Canvas not found';
                    
                    // Check if WebGL context exists
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (!gl) return 'No WebGL context';
                    
                    // Check if anything is drawn (read pixels)
                    const pixels = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
                    gl.readPixels(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
                    
                    // Check if pixels are all the background color (0x0e1116)
                    let hasContent = false;
                    for (let i = 0; i < pixels.length; i += 4) {
                        // Check if pixel is not the background color (dark gray)
                        if (pixels[i] !== 14 || pixels[i+1] !== 17 || pixels[i+2] !== 22) {
                            hasContent = true;
                            break;
                        }
                    }
                    
                    return hasContent ? 'HAS CONTENT' : 'BLANK (background only)';
                }
            """)
            
            print(f"   Canvas content: {canvas_content}")
        else:
            print("   Canvas element: NOT FOUND")
        
        # Check if Three.js is actually working
        threejs_status = await page.evaluate("""
            () => {
                const checks = {
                    threeLoaded: typeof THREE !== 'undefined',
                    sceneExists: !!window.scene,
                    cameraExists: !!window.camera,
                    rendererExists: !!window.renderer,
                    sceneChildren: window.scene ? window.scene.children.length : 0,
                    deviceMeshes: window.scene ? window.scene.children.filter(obj => obj.userData.type).length : 0
                };
                
                return checks;
            }
        """)
        
        print(f"\n🎯 Three.js Status:")
        for key, value in threejs_status.items():
            print(f"   {key}: {value}")
        
        # Try to manually render something to test if Three.js works
        print(f"\n🔧 Testing Three.js rendering capability...")
        render_test = await page.evaluate("""
            () => {
                try {
                    if (!window.scene || !window.camera || !window.renderer) {
                        return 'Three.js not properly initialized';
                    }
                    
                    // Add a simple test cube
                    const geometry = new THREE.BoxGeometry(10, 10, 10);
                    const material = new THREE.MeshBasicMaterial({ color: 0xff0000 });
                    const cube = new THREE.Mesh(geometry, material);
                    cube.position.set(0, 5, 0);
                    
                    window.scene.add(cube);
                    
                    // Render the scene
                    window.renderer.render(window.scene, window.camera);
                    
                    return 'Test cube added and rendered';
                } catch (error) {
                    return 'Render test failed: ' + error.message;
                }
            }
        """)
        
        print(f"   Render test: {render_test}")
        
        # Check the canvas again after render test
        if await canvas.count() > 0:
            canvas_after_test = await page.evaluate("""
                () => {
                    const canvas = document.getElementById('topology-canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (!gl) return 'No WebGL context';
                    
                    const pixels = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
                    gl.readPixels(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
                    
                    let hasContent = false;
                    for (let i = 0; i < pixels.length; i += 4) {
                        if (pixels[i] !== 14 || pixels[i+1] !== 17 || pixels[i+2] !== 22) {
                            hasContent = true;
                            break;
                        }
                    }
                    
                    return hasContent ? 'HAS CONTENT' : 'STILL BLANK';
                }
            """)
            
            print(f"   Canvas after test: {canvas_after_test}")
        
        # Take a screenshot to see what's actually visible
        await page.screenshot(path="test_screenshots/blank_page_debug.png")
        print(f"\n📸 Screenshot saved: test_screenshots/blank_page_debug.png")
        
        # Try clicking Demo Mode button and see what happens
        print(f"\n🎭 Testing Demo Mode button...")
        demo_button = page.locator("button:has-text('🎭 Demo Mode')")
        if await demo_button.count() > 0:
            console_messages.clear()
            await demo_button.click()
            await asyncio.sleep(3)
            
            # Check if any devices were actually added
            devices_after_demo = await page.evaluate("""
                () => {
                    return window.scene ? window.scene.children.filter(obj => obj.userData.type).length : 0;
                }
            """)
            
            print(f"   Devices after Demo Mode: {devices_after_demo}")
            
            # Check canvas content again
            if await canvas.count() > 0:
                canvas_after_demo = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('topology-canvas');
                        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                        if (!gl) return 'No WebGL context';
                        
                        const pixels = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
                        gl.readPixels(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
                        
                        let hasContent = false;
                        for (let i = 0; i < pixels.length; i += 4) {
                            if (pixels[i] !== 14 || pixels[i+1] !== 17 || pixels[i+2] !== 22) {
                                hasContent = true;
                                break;
                            }
                        }
                        
                        return hasContent ? 'HAS CONTENT' : 'STILL BLANK';
                    }
                """)
                
                print(f"   Canvas after Demo Mode: {canvas_after_demo}")
        else:
            print("   Demo Mode button not found")
        
        print("\n🔍 Keeping browser open for 10 seconds for manual inspection...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_blank_page())
