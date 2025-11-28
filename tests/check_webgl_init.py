#!/usr/bin/env python3
"""
Check WebGL initialization messages
"""

import asyncio
from playwright.async_api import async_playwright

async def check_webgl_init():
    """Check WebGL initialization process"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Console logging
        def handle_console(msg):
            if "webgl" in msg.text.lower() or "renderer" in msg.text.lower() or "context" in msg.text.lower() or "error" in msg.text.lower():
                print(f"📋 {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
        
        # Navigate to the main page
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        print("🔍 Checking WebGL Initialization")
        print("=" * 50)
        
        # Wait for initialization
        await asyncio.sleep(3)
        
        # Check WebGL status
        webgl_status = await page.evaluate("""
            () => {
                const checks = {
                    webglSupported: !!window.WebGLRenderingContext,
                    webgl2Supported: !!window.WebGL2RenderingContext,
                    threeLoaded: typeof THREE !== 'undefined',
                    rendererExists: !!window.renderer,
                    sceneExists: !!window.scene,
                    cameraExists: !!window.camera,
                    rendererContext: window.renderer ? !!window.renderer.getContext() : false
                };
                
                // Test WebGL context creation directly
                const canvas = document.getElementById('topology-canvas');
                if (canvas) {
                    try {
                        const testContext = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                        checks.directWebGL = !!testContext;
                        if (testContext) {
                            checks.webglVersion = testContext.getParameter(testContext.VERSION);
                            checks.webglVendor = testContext.getParameter(testContext.VENDOR);
                            checks.webGLRenderer = testContext.getParameter(testContext.RENDERER);
                        }
                    } catch (error) {
                        checks.directWebGLError = error.message;
                    }
                }
                
                return checks;
            }
        """)
        
        print("📊 WebGL Status:")
        for key, value in webgl_status.items():
            print(f"   {key}: {value}")
        
        # Try to manually create a simple WebGL scene
        print(f"\n🔧 Testing manual WebGL scene...")
        manual_test = await page.evaluate("""
            () => {
                try {
                    const canvas = document.getElementById('topology-canvas');
                    
                    // Create a simple WebGL context manually
                    const gl = canvas.getContext('webgl', {
                        alpha: false,
                        antialias: false,
                        preserveDrawingBuffer: true
                    });
                    
                    if (!gl) {
                        return 'Failed to create WebGL context manually';
                    }
                    
                    // Clear to red to verify it works
                    gl.clearColor(1.0, 0.0, 0.0, 1.0);
                    gl.clear(gl.COLOR_BUFFER_BIT);
                    
                    // Read a pixel to verify
                    const pixels = new Uint8Array(4);
                    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
                    
                    const isRed = pixels[0] > 200 && pixels[1] < 50 && pixels[2] < 50;
                    
                    return {
                        success: true,
                        contextCreated: true,
                        redTest: isRed,
                        pixelData: Array.from(pixels),
                        glVersion: gl.getParameter(gl.VERSION)
                    };
                } catch (error) {
                    return {
                        success: false,
                        error: error.message
                    };
                }
            }
        """)
        
        print(f"   Manual WebGL test: {manual_test}")
        
        # Take screenshot to see if red appears
        await page.screenshot(path="test_screenshots/webgl_manual_test.png")
        print("📸 Screenshot: test_screenshots/webgl_manual_test.png")
        
        print("\n🔍 Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_webgl_init())
