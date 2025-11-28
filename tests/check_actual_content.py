#!/usr/bin/env python3
"""
Check what's actually visible in the browser canvas
"""

import asyncio
from playwright.async_api import async_playwright

async def check_actual_content():
    """Check actual canvas content"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Navigate to the main page
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        print("🔍 CHECKING ACTUAL CANVAS CONTENT")
        print("=" * 50)
        
        # Load Fortinet topology
        load_fortinet = page.locator("button:has-text('🔥 Load Fortinet')")
        if await load_fortinet.count() > 0:
            await load_fortinet.click()
            await asyncio.sleep(3)
            
            # Analyze what's actually in the canvas
            canvas_analysis = await page.evaluate("""
                () => {
                    const canvas = document.getElementById('topology-canvas');
                    if (!canvas) return 'No canvas';
                    
                    // Try to get WebGL context
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (!gl) return 'No WebGL context';
                    
                    // Read pixels from the center area
                    const centerX = Math.floor(canvas.width / 2);
                    const centerY = Math.floor(canvas.height / 2);
                    const sampleSize = 100;
                    
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
                    
                    // Analyze the pixels
                    let backgroundPixels = 0;
                    let contentPixels = 0;
                    let colorCounts = {};
                    let sampleColors = [];
                    
                    for (let i = 0; i < pixels.length; i += 4) {
                        const r = pixels[i];
                        const g = pixels[i+1];
                        const b = pixels[i+2];
                        const a = pixels[i+3];
                        
                        // Check if it's background (dark color around RGB 14, 17, 22)
                        if (r < 30 && g < 30 && b < 30) {
                            backgroundPixels++;
                        } else if (a > 0) {
                            contentPixels++;
                            const colorKey = `${r},${g},${b}`;
                            colorCounts[colorKey] = (colorCounts[colorKey] || 0) + 1;
                            
                            if (sampleColors.length < 10) {
                                sampleColors.push({r, g, b, a});
                            }
                        }
                    }
                    
                    // Get device info
                    const devices = window.scene ? window.scene.children.filter(obj => obj.userData.type) : [];
                    
                    return {
                        canvasSize: { width: canvas.width, height: canvas.height },
                        totalPixels: sampleSize * sampleSize,
                        backgroundPixels: backgroundPixels,
                        contentPixels: contentPixels,
                        contentPercentage: ((contentPixels / (sampleSize * sampleSize)) * 100).toFixed(1),
                        hasContent: contentPixels > 50,
                        sampleColors: sampleColors,
                        colorCounts: Object.entries(colorCounts).slice(0, 5).map(([color, count]) => ({color, count})),
                        deviceCount: devices.length,
                        devicePositions: devices.map(d => ({
                            name: d.name || d.userData.name,
                            type: d.userData.type,
                            position: { x: d.position.x, y: d.position.y, z: d.position.z },
                            visible: d.visible
                        }))
                    };
                }
            """)
            
            print("📊 CANVAS ANALYSIS:")
            if isinstance(canvas_analysis, str):
                print(f"   Error: {canvas_analysis}")
            else:
                print(f"   Canvas size: {canvas_analysis['canvasSize']['width']}x{canvas_analysis['canvasSize']['height']}")
                print(f"   Devices in scene: {canvas_analysis['deviceCount']}")
                print(f"   Content pixels: {canvas_analysis['contentPixels']}/{canvas_analysis['totalPixels']}")
                print(f"   Content percentage: {canvas_analysis['contentPercentage']}%")
                print(f"   Has visible content: {canvas_analysis['hasContent']}")
                
                if canvas_analysis['devicePositions']:
                    print(f"\n📍 Device Positions:")
                    for device in canvas_analysis['devicePositions']:
                        print(f"   {device['type']} '{device['name']}' at ({device['position']['x']}, {device['position']['y']}, {device['position']['z']}) - Visible: {device['visible']}")
                
                if canvas_analysis['sampleColors']:
                    print(f"\n🎨 Sample Colors Found:")
                    for i, color in enumerate(canvas_analysis['sampleColors'][:5]):
                        print(f"   Color {i+1}: RGB({color['r']}, {color['g']}, {color['b']}) Alpha: {color['a']}")
                
                if canvas_analysis['colorCounts']:
                    print(f"\n🔢 Most Common Colors:")
                    for color_info in canvas_analysis['colorCounts']:
                        print(f"   RGB({color_info['color']}): {color_info['count']} pixels")
                
                # Verdict
                print(f"\n🎯 VERDICT:")
                if canvas_analysis['hasContent']:
                    print(f"   ✅ CONTENT IS VISIBLE - You should see devices!")
                else:
                    print(f"   ❌ NO CONTENT VISIBLE - Canvas appears empty")
                    if canvas_analysis['deviceCount'] > 0:
                        print(f"   ⚠️  Devices loaded but not rendering -可能是位置或材质问题")
                    else:
                        print(f"   ⚠️  No devices loaded")
        
        # Take final screenshot
        await page.screenshot(path="test_screenshots/final_content_check.png")
        print(f"\n📸 Final screenshot: test_screenshots/final_content_check.png")
        
        print("\n🔍 Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_actual_content())
