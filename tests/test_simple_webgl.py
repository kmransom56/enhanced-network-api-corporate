#!/usr/bin/env python3
"""
Test simple WebGL rendering
"""

import asyncio
from playwright.async_api import async_playwright

async def test_simple_webgl():
    """Test if we can create a simple WebGL scene"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        # Console logging
        def handle_console(msg):
            if "webgl" in msg.text.lower() or "error" in msg.text.lower():
                print(f"📋 {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
        
        # Navigate to the main page
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        print("🎮 Testing Simple WebGL Rendering")
        print("=" * 50)
        
        # Try to create a completely new Three.js scene
        simple_test = await page.evaluate("""
            () => {
                try {
                    // Get canvas
                    let canvas = document.getElementById('topology-canvas') || document.getElementById('test-webgl-canvas');
                    if (!canvas) {
                        canvas = document.createElement('canvas');
                        canvas.id = 'test-webgl-canvas';
                        canvas.width = 800;
                        canvas.height = 600;
                        canvas.style.width = '800px';
                        canvas.style.height = '600px';
                        document.body.appendChild(canvas);
                    }
                    
                    // Clear any existing Three.js stuff
                    if (window.renderer) {
                        window.renderer.dispose();
                    }
                    
                    // Create a fresh WebGL renderer
                    const renderer = new THREE.WebGLRenderer({ 
                        canvas: canvas,
                        antialias: true,
                        alpha: false
                    });
                    
                    renderer.setSize(canvas.clientWidth, canvas.clientHeight);
                    renderer.setClearColor(0x0000ff, 1.0); // Blue background
                    
                    // Create scene
                    const scene = new THREE.Scene();
                    
                    // Create camera
                    const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
                    camera.position.z = 5;
                    
                    // Create a simple red cube
                    const geometry = new THREE.BoxGeometry(2, 2, 2);
                    const material = new THREE.MeshBasicMaterial({ color: 0xff0000 });
                    const cube = new THREE.Mesh(geometry, material);
                    scene.add(cube);
                    
                    // Add some lighting
                    const light = new THREE.DirectionalLight(0xffffff, 1);
                    light.position.set(1, 1, 1);
                    scene.add(light);
                    
                    // Render the scene
                    renderer.render(scene, camera);
                    
                    // Store for debugging
                    window.testRenderer = renderer;
                    window.testScene = scene;
                    window.testCamera = camera;
                    window.testCube = cube;
                    
                    return 'Simple WebGL test successful - should see blue background with red cube';
                } catch (error) {
                    return 'Simple WebGL test failed: ' + error.message;
                }
            }
        """)
        
        print(f"🎯 Simple Test Result: {simple_test}")
        
        # Check if anything is visible
        await asyncio.sleep(2)
        
        # Take screenshot
        await page.screenshot(path="test_screenshots/simple_webgl_test.png")
        print("📸 Screenshot saved: test_screenshots/simple_webgl_test.png")
        
        # Check what's actually in the canvas
        canvas_check = await page.evaluate("""
            () => {
                const canvas = document.getElementById('topology-canvas') || document.getElementById('test-webgl-canvas');
                if (!canvas) {
                    return 'Canvas not found for inspection';
                }
                const ctx = canvas.getContext('2d'); // Try 2D context to see what's there
                
                if (ctx) {
                    // Get a pixel from the center
                    const pixel = ctx.getImageData(canvas.width/2, canvas.height/2, 1, 1).data;
                    return {
                        centerPixel: [pixel[0], pixel[1], pixel[2], pixel[3]],
                        canvasSize: { width: canvas.width, height: canvas.height }
                    };
                }
                
                return 'No 2D context available';
            }
        """)
        
        print(f"🎨 Canvas Check: {canvas_check}")
        
        print("\n🔍 Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_simple_webgl())
