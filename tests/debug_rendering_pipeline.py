#!/usr/bin/env python3
"""
Debug the complete rendering pipeline
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_rendering_pipeline():
    """Debug the complete rendering pipeline"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        # Console logging
        def handle_console(msg):
            if "render" in msg.text.lower() or "device" in msg.text.lower() or "scene" in msg.text.lower() or "error" in msg.text.lower():
                print(f"📋 {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
        
        # Navigate to the main page
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        print("🔍 Debugging Complete Rendering Pipeline")
        print("=" * 50)
        
        # Load Fortinet topology
        load_fortinet = page.locator("button:has-text('🔥 Load Fortinet')")
        if await load_fortinet.count() > 0:
            await load_fortinet.click()
            await asyncio.sleep(3)
            
            # Check complete rendering state
            rendering_state = await page.evaluate("""
                () => {
                    if (!window.renderer || !window.scene || !window.camera) {
                        return 'Missing rendering components';
                    }
                    
                    const renderer = window.renderer;
                    const scene = window.scene;
                    const camera = window.camera;
                    
                    // Check scene contents
                    const allObjects = scene.children;
                    const devices = allObjects.filter(obj => obj.userData.type);
                    const lights = allObjects.filter(obj => obj.isLight);
                    const grids = allObjects.filter(obj => obj.isGridHelper);
                    
                    // Check camera
                    const cameraInfo = {
                        position: camera.position,
                        rotation: camera.rotation,
                        fov: camera.fov,
                        near: camera.near,
                        far: camera.far,
                        aspect: camera.aspect
                    };
                    
                    // Check renderer
                    const rendererInfo = {
                        size: renderer.getSize(),
                        domElement: !!renderer.domElement,
                        context: !!renderer.getContext(),
                        info: renderer.info ? {
                            render: {
                                calls: renderer.info.render.calls,
                                triangles: renderer.info.render.triangles,
                                points: renderer.info.render.points,
                                lines: renderer.info.render.lines
                            },
                            memory: {
                                geometries: renderer.info.memory.geometries,
                                textures: renderer.info.memory.textures
                            }
                        } : 'no info'
                    };
                    
                    // Check device materials and visibility
                    const deviceDetails = devices.map(device => ({
                        name: device.name || device.userData.name,
                        type: device.userData.type,
                        visible: device.visible,
                        position: device.position,
                        hasGeometry: !!device.geometry,
                        hasMaterial: !!device.material,
                        materialType: device.material ? device.material.type : 'none',
                        hasTexture: device.material && device.material.map ? true : false,
                        materialColor: device.material && device.material.color ? 
                            `RGB(${Math.floor(device.material.color.r * 255)}, ${Math.floor(device.material.color.g * 255)}, ${Math.floor(device.material.color.b * 255)})` : 'none'
                    }));
                    
                    return {
                        sceneStats: {
                            totalObjects: allObjects.length,
                            devices: devices.length,
                            lights: lights.length,
                            grids: grids.length
                        },
                        cameraInfo,
                        rendererInfo,
                        deviceDetails,
                        lastRenderCall: renderer.info ? renderer.info.render.calls : 0
                    };
                }
            """)
            
            print("📊 Rendering Pipeline State:")
            if isinstance(rendering_state, str):
                print(f"   Error: {rendering_state}")
            else:
                print(f"   Scene: {rendering_state['sceneStats']['totalObjects']} objects ({rendering_state['sceneStats']['devices']} devices, {rendering_state['sceneStats']['lights']} lights)")
                print(f"   Camera: Position ({rendering_state['cameraInfo']['position']['x']}, {rendering_state['cameraInfo']['position']['y']}, {rendering_state['cameraInfo']['position']['z']})")
                print(f"   Renderer: {rendering_state['rendererInfo']['size']['width']}x{rendering_state['rendererInfo']['size']['height']}")
                print(f"   Render calls: {rendering_state['lastRenderCall']}")
                
                print(f"\n📦 Device Details:")
                for device in rendering_state['deviceDetails']:
                    print(f"   {device['type']} '{device['name']}':")
                    print(f"      Position: ({device['position']['x']}, {device['position']['y']}, {device['position']['z']})")
                    print(f"      Visible: {device['visible']}")
                    print(f"      Material: {device['materialType']}")
                    print(f"      Has texture: {device['hasTexture']}")
                    print(f"      Color: {device['materialColor']}")
                
                # Force a render and check if anything changes
                print(f"\n🔧 Forcing manual render...")
                render_result = await page.evaluate("""
                    () => {
                        try {
                            const beforeCalls = window.renderer.info.render.calls;
                            
                            // Force render
                            window.renderer.render(window.scene, window.camera);
                            
                            const afterCalls = window.renderer.info.render.calls;
                            
                            return {
                                success: true,
                                beforeCalls: beforeCalls,
                                afterCalls: afterCalls,
                                renderDelta: afterCalls - beforeCalls
                            };
                        } catch (error) {
                            return {
                                success: false,
                                error: error.message
                            };
                        }
                    }
                """)
                
                print(f"   Manual render: {render_result}")
                
                # Check if devices are in camera frustum
                print(f"\n📷 Camera Frustum Check:")
                frustum_check = await page.evaluate("""
                    () => {
                        const devices = window.scene.children.filter(obj => obj.userData.type);
                        const camera = window.camera;
                        
                        const frustum = new THREE.Frustum();
                        const cameraMatrix = new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
                        frustum.setFromProjectionMatrix(cameraMatrix);
                        
                        return devices.map(device => ({
                            name: device.name || device.userData.name,
                            type: device.userData.type,
                            inFrustum: frustum.intersectsObject(device),
                            distance: camera.position.distanceTo(device.position),
                            bounds: (() => {
                                const box = new THREE.Box3().setFromObject(device);
                                return {
                                    center: box.getCenter(new THREE.Vector3()),
                                    size: box.getSize(new THREE.Vector3())
                                };
                            })()
                        }));
                    }
                """)
                
                for device in frustum_check:
                    print(f"   {device['type']} '{device['name']}':")
                    print(f"      In camera view: {device['inFrustum']}")
                    print(f"      Distance: {device['distance']:.1f}")
                    print(f"      Bounds: center({device['bounds']['center']['x']}, {device['bounds']['center']['y']}, {device['bounds']['center']['z']}) size({device['bounds']['size']['x']}, {device['bounds']['size']['y']}, {device['bounds']['size']['z']})")
        
        # Take screenshot
        await page.screenshot(path="test_screenshots/rendering_pipeline_debug.png")
        print(f"\n📸 Screenshot: test_screenshots/rendering_pipeline_debug.png")
        
        print("\n🔍 Keeping browser open for 15 seconds...")
        await asyncio.sleep(15)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_rendering_pipeline())
