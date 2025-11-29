#!/usr/bin/env python3
"""
Debug WebGL context issues
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_webgl():
    """Debug why WebGL context is not available"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        # Console logging
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"{msg.type}: {msg.text}")
            if "webgl" in msg.text.lower() or "gl" in msg.text.lower():
                print(f"🎮 {msg.type}: {msg.text}")
            elif msg.type == "error":
                print(f"❌ {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
        
        # Navigate to the main page
        print("🎮 Debugging WebGL Context Issues")
        print("=" * 50)
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        # Check WebGL capabilities
        webgl_info = await page.evaluate("""
            () => {
                const canvas = document.getElementById('topology-canvas');
                if (!canvas) return { error: 'Canvas not found' };
                
                const info = {
                    canvasElement: !!canvas,
                    canvasSize: { width: canvas.width, height: canvas.height },
                    clientSize: { width: canvas.clientWidth, height: canvas.clientHeight }
                };
                
                // Try different WebGL context types
                const contexts = ['webgl2', 'webgl', 'experimental-webgl'];
                let workingContext = null;
                
                contexts.forEach(contextType => {
                    try {
                        const gl = canvas.getContext(contextType);
                        if (gl) {
                            workingContext = contextType;
                            info[contextType] = {
                                available: true,
                                version: gl.getParameter(gl.VERSION),
                                vendor: gl.getParameter(gl.VENDOR),
                                renderer: gl.getParameter(gl.RENDERER)
                            };
                        } else {
                            info[contextType] = { available: false };
                        }
                    } catch (error) {
                        info[contextType] = { available: false, error: error.message };
                    }
                });
                
                // Check browser WebGL support
                info.browserSupport = {
                    webgl2Supported: !!window.WebGL2RenderingContext,
                    webglSupported: !!window.WebGLRenderingContext
                };
                
                // Force a specific context creation
                try {
                    const forcedGl = canvas.getContext('webgl', {
                        alpha: false,
                        antialias: true,
                        preserveDrawingBuffer: true
                    });
                    info.forcedWebGL = !!forcedGl;
                } catch (error) {
                    info.forcedWebGL = false;
                    info.forcedError = error.message;
                }
                
                return info;
            }
        """)
        
        print("📊 WebGL Information:")
        for key, value in webgl_info.items():
            print(f"   {key}: {value}")
        
        # Try to manually create a WebGL context and render something simple
        print(f"\n🔧 Attempting manual WebGL setup...")
        manual_webgl = await page.evaluate("""
            () => {
                try {
                    const canvas = document.getElementById('topology-canvas');
                    
                    // Set canvas size explicitly
                    canvas.width = canvas.clientWidth;
                    canvas.height = canvas.clientHeight;
                    
                    // Try to create WebGL context with specific options
                    const gl = canvas.getContext('webgl', {
                        alpha: false,
                        antialias: true,
                        preserveDrawingBuffer: true,
                        premultipliedAlpha: false
                    });
                    
                    if (!gl) {
                        return 'Failed to create WebGL context';
                    }
                    
                    // Clear to a visible color (red) to test
                    gl.clearColor(1.0, 0.0, 0.0, 1.0);
                    gl.clear(gl.COLOR_BUFFER_BIT);
                    
                    // Try to read back the color to verify it worked
                    const pixels = new Uint8Array(4);
                    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
                    
                    const isRed = pixels[0] > 200 && pixels[1] < 50 && pixels[2] < 50;
                    
                    return isRed ? 'WebGL working (red test successful)' : 'WebGL created but rendering failed';
                } catch (error) {
                    return 'Manual WebGL setup failed: ' + error.message;
                }
            }
        """)
        
        print(f"   Manual WebGL: {manual_webgl}")
        
        # Check if Three.js renderer is using the correct canvas
        print(f"\n🎯 Checking Three.js renderer...")
        threejs_renderer = await page.evaluate("""
            () => {
                if (!window.renderer) return 'No Three.js renderer';
                
                const renderer = window.renderer;
                const canvas = renderer.domElement;
                
                return {
                    rendererType: renderer.type || 'unknown',
                    canvasElement: !!canvas,
                    canvasId: canvas.id || 'no-id',
                    canvasSize: { width: canvas.width, height: canvas.height },
                    context: !!renderer.getContext(),
                    rendering: renderer.info ? {
                        calls: renderer.info.render.calls,
                        triangles: renderer.info.render.triangles,
                        points: renderer.info.render.points,
                        lines: renderer.info.render.lines
                    } : 'no info'
                };
            }
        """)
        
        print(f"   Three.js Renderer: {threejs_renderer}")
        
        # Try to force Three.js to render
        print(f"\n🔧 Forcing Three.js render...")
        force_render = await page.evaluate("""
            () => {
                try {
                    if (!window.scene || !window.camera || !window.renderer) {
                        return 'Three.js not initialized';
                    }
                    
                    // Force a render
                    window.renderer.render(window.scene, window.camera);
                    
                    // Check if renderer has been called
                    const info = window.renderer.info;
                    if (info) {
                        return {
                            rendered: true,
                            renderCalls: info.render.calls,
                            geometries: info.memory.geometries,
                            textures: info.memory.textures
                        };
                    }
                    
                    return 'Rendered but no info available';
                } catch (error) {
                    return 'Force render failed: ' + error.message;
                }
            }
        """)
        
        print(f"   Force render: {force_render}")
        
        # Take screenshot after manual attempts
        await page.screenshot(path="test_screenshots/webgl_debug.png")
        print(f"\n📸 Screenshot saved: test_screenshots/webgl_debug.png")
        
        print("\n🔍 Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_webgl())
