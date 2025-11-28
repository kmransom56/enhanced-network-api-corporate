#!/usr/bin/env python3
"""
Actually verify what's visible in the browser - no more console message assumptions
"""

import asyncio
from playwright.async_api import async_playwright

async def verify_visual_output():
    """Check what's actually visible in the canvas"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Navigate to the main page
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        print("🔍 VERIFYING ACTUAL VISUAL OUTPUT")
        print("=" * 50)
        
        # Take initial screenshot
        await page.screenshot(path="test_screenshots/before_loading.png")
        print("📸 Screenshot: test_screenshots/before_loading.png")
        
        # Load Fortinet topology
        load_fortinet = page.locator("button:has-text('🔥 Load Fortinet')")
        if await load_fortinet.count() > 0:
            print("\n🔥 Loading Fortinet topology...")
            await load_fortinet.click()
            await asyncio.sleep(3)
            
            # Take screenshot after loading
            await page.screenshot(path="test_screenshots/after_fortinet.png")
            print("📸 Screenshot: test_screenshots/after_fortinet.png")
            
            # Check what's actually in the canvas pixel by pixel
            canvas_analysis = await page.evaluate("""
                () => {
                    const canvas = document.getElementById('topology-canvas');
                    if (!canvas) return 'No canvas found';
                    
                    // Get WebGL context
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (!gl) return 'No WebGL context';
                    
                    // Read pixels from center area
                    const centerX = Math.floor(canvas.width / 2);
                    const centerY = Math.floor(canvas.height / 2);
                    const sampleSize = 50;
                    
                    const pixels = new Uint8Array(sampleSize * sampleSize * 4);
                    gl.readPixels(
                        centerX - sampleSize/2, 
                        centerY - sampleSize/2, 
                        sampleSize, 
                        sampleSize, 
                        gl.RGBA, 
                        gl.UNSIGNED_BYTE, 
                        pixels
                    );
                    
                    // Analyze pixels
                    let nonBackgroundPixels = 0;
                    let backgroundColors = { dark: 0, other: 0 };
                    let colorSamples = [];
                    
                    for (let i = 0; i < pixels.length; i += 4) {
                        const r = pixels[i];
                        const g = pixels[i+1];
                        const b = pixels[i+2];
                        const a = pixels[i+3];
                        
                        // Check if it's not the background color (0x0e1116 = RGB: 14, 17, 22)
                        if (r !== 14 || g !== 17 || b !== 22) {
                            nonBackgroundPixels++;
                            if (colorSamples.length < 10) {
                                colorSamples.push({r, g, b, a});
                            }
                        } else {
                            backgroundColors.dark++;
                        }
                    }
                    
                    return {
                        canvasSize: { width: canvas.width, height: canvas.height },
                        totalPixels: sampleSize * sampleSize,
                        nonBackgroundPixels: nonBackgroundPixels,
                        backgroundPixels: backgroundColors.dark,
                        hasContent: nonBackgroundPixels > 100,
                        contentPercentage: ((nonBackgroundPixels / (sampleSize * sampleSize)) * 100).toFixed(1),
                        colorSamples: colorSamples,
                        devices: window.scene ? window.scene.children.filter(obj => obj.userData.type).length : 0
                    };
                }
            """)
            
            print(f"\n📊 Canvas Analysis:")
            if isinstance(canvas_analysis, str):
                print(f"   Error: {canvas_analysis}")
            else:
                print(f"   Canvas size: {canvas_analysis['canvasSize']['width']}x{canvas_analysis['canvasSize']['height']}")
                print(f"   Devices in scene: {canvas_analysis['devices']}")
                print(f"   Non-background pixels: {canvas_analysis['nonBackgroundPixels']}/{canvas_analysis['totalPixels']}")
                print(f"   Content percentage: {canvas_analysis['contentPercentage']}%")
                print(f"   Has visible content: {canvas_analysis['hasContent']}")
                
                if canvas_analysis['colorSamples'].length > 0:
                    print(f"   Sample colors found:")
                    for i, color in enumerate(canvas_analysis['colorSamples'][:5]):
                        print(f"      Color {i+1}: RGB({color['r']}, {color['g']}, {color['b']}) Alpha: {color['a']}")
            
            # Check if devices are actually positioned correctly
            device_positions = await page.evaluate("""
                () => {
                    if (!window.scene) return 'No scene';
                    
                    const devices = window.scene.children.filter(obj => obj.userData.type);
                    const camera = window.camera;
                    
                    return devices.map(device => ({
                        name: device.name || device.userData.name,
                        type: device.userData.type,
                        position: { x: device.position.x, y: device.position.y, z: device.position.z },
                        visible: device.visible,
                        distanceFromCamera: camera.position.distanceTo(device.position),
                        inFrustum: (() => {
                            const frustum = new THREE.Frustum();
                            const cameraMatrix = new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
                            frustum.setFromProjectionMatrix(cameraMatrix);
                            return frustum.intersectsObject(device);
                        })()
                    }));
                }
            """)
            
            print(f"\n📍 Device Positions:")
            for device in device_positions:
                print(f"   {device['type']} '{device['name']}':")
                print(f"      Position: ({device['position']['x']}, {device['position']['y']}, {device['position']['z']})")
                print(f"      Visible: {device['visible']}")
                print(f"      In camera view: {device['inFrustum']}")
                print(f"      Distance from camera: {device['distanceFromCamera']:.1f}")
            
            # Try Demo Mode as well
            print(f"\n🎭 Testing Demo Mode...")
            demo_button = page.locator("button:has-text('🎭 Demo Mode')")
            if await demo_button.count() > 0:
                await demo_button.click()
                await asyncio.sleep(3)
                
                await page.screenshot(path="test_screenshots/after_demo.png")
                print("📸 Screenshot: test_screenshots/after_demo.png")
                
                # Quick check if more content appears
                demo_analysis = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('topology-canvas');
                        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                        if (!gl) return 'No WebGL';
                        
                        const pixels = new Uint8Array(100 * 100 * 4);
                        gl.readPixels(canvas.width/2 - 50, canvas.height/2 - 50, 100, 100, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
                        
                        let nonBackground = 0;
                        for (let i = 0; i < pixels.length; i += 4) {
                            if (pixels[i] !== 14 || pixels[i+1] !== 17 || pixels[i+2] !== 22) {
                                nonBackground++;
                            }
                        }
                        
                        return {
                            devices: window.scene ? window.scene.children.filter(obj => obj.userData.type).length : 0,
                            nonBackgroundPixels: nonBackground,
                            hasContent: nonBackground > 200
                        };
                    }
                """)
                
                print(f"   Demo mode devices: {demo_analysis['devices']}")
                print(f"   Non-background pixels: {demo_analysis['nonBackgroundPixels']}")
                print(f"   Has visible content: {demo_analysis['hasContent']}")
        
        print(f"\n🔍 Keeping browser open for 15 seconds for manual inspection...")
        print(f"   Check the screenshots in test_screenshots/ folder")
        await asyncio.sleep(15)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_visual_output())
