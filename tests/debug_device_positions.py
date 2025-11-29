#!/usr/bin/env python3
"""
Debug device positions and visibility
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_device_positions():
    """Debug why devices might not be visible"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        # Console logging
        def handle_console(msg):
            if "device" in msg.text.lower() or "mesh" in msg.text.lower() or "position" in msg.text.lower():
                print(f"📋 {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
        
        # Navigate to the main page
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        print("🎯 Debugging Device Positions and Visibility")
        print("=" * 50)
        
        # Load Demo Mode
        demo_button = page.locator("button:has-text('🎭 Demo Mode')")
        if await demo_button.count() > 0:
            await demo_button.click()
            await asyncio.sleep(3)
            
            # Check scene state
            scene_state = await page.evaluate("""
                () => {
                    if (!window.scene) return 'No scene';
                    
                    const devices = window.scene.children.filter(obj => obj.userData.type);
                    const deviceInfo = devices.map((device, index) => ({
                        index: index,
                        name: device.name || device.userData.name || 'unnamed',
                        type: device.userData.type || 'unknown',
                        position: {
                            x: device.position.x.toFixed(2),
                            y: device.position.y.toFixed(2), 
                            z: device.position.z.toFixed(2)
                        },
                        visible: device.visible,
                        geometry: !!device.geometry,
                        material: !!device.material
                    }));
                    
                    return {
                        totalObjects: window.scene.children.length,
                        deviceCount: devices.length,
                        devices: deviceInfo,
                        camera: {
                            position: {
                                x: window.camera.position.x.toFixed(2),
                                y: window.camera.position.y.toFixed(2),
                                z: window.camera.position.z.toFixed(2)
                            },
                            fov: window.camera.fov,
                            near: window.camera.near,
                            far: window.camera.far
                        },
                        renderer: {
                            size: window.renderer.getSize ? window.renderer.getSize() : 'unknown',
                            renderCalls: window.renderer.info ? window.renderer.info.render.calls : 0
                        }
                    };
                }
            """)
            
            print("🎯 Scene State:")
            print(f"   Total objects: {scene_state['totalObjects']}")
            print(f"   Device count: {scene_state['deviceCount']}")
            print(f"   Camera position: ({scene_state['camera']['position']['x']}, {scene_state['camera']['position']['y']}, {scene_state['camera']['position']['z']})")
            print(f"   Camera FOV: {scene_state['camera']['fov']}")
            print(f"   Render calls: {scene_state['renderer']['renderCalls']}")
            
            print(f"\n📦 Device Details:")
            for device in scene_state['devices']:
                print(f"   Device {device['index']}: {device['type']} '{device['name']}'")
                print(f"      Position: ({device['position']['x']}, {device['position']['y']}, {device['position']['z']})")
                print(f"      Visible: {device['visible']}, Geometry: {device['geometry']}, Material: {device['material']}")
            
            # Check if devices are in camera view
            print(f"\n📷 Camera Visibility Check:")
            visibility_check = await page.evaluate("""
                () => {
                    if (!window.scene || !window.camera || !window.renderer) return 'Missing components';
                    
                    const devices = window.scene.children.filter(obj => obj.userData.type);
                    const camera = window.camera;
                    
                    // Simple frustum check
                    const frustum = new THREE.Frustum();
                    const cameraMatrix = new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
                    frustum.setFromProjectionMatrix(cameraMatrix);
                    
                    const visibilityResults = devices.map(device => {
                        const inFrustum = frustum.intersectsObject(device);
                        const distance = camera.position.distanceTo(device.position);
                        
                        return {
                            name: device.name || device.userData.name || 'unnamed',
                            inFrustum: inFrustum,
                            distance: distance.toFixed(2),
                            tooFar: distance > camera.far,
                            tooNear: distance < camera.near
                        };
                    });
                    
                    return visibilityResults;
                }
            """)
            
            for result in visibility_check:
                print(f"   {result['name']}: In View: {result['inFrustum']}, Distance: {result['distance']}")
                if result['tooFar']:
                    print(f"      ⚠️  Too far from camera (>{result['distance']} > {scene_state['camera']['far']})")
                if result['tooNear']:
                    print(f"      ⚠️  Too close to camera (<{result['distance']} < {scene_state['camera']['near']})")
            
            # Try to move camera to see devices
            print(f"\n🔧 Adjusting camera to view devices...")
            camera_adjust = await page.evaluate("""
                () => {
                    const devices = window.scene.children.filter(obj => obj.userData.type);
                    if (devices.length === 0) return 'No devices to focus on';
                    
                    // Calculate bounding box of all devices
                    const box = new THREE.Box3();
                    devices.forEach(device => {
                        box.expandByObject(device);
                    });
                    
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());
                    
                    // Position camera to see all devices
                    const maxDim = Math.max(size.x, size.y, size.z);
                    const distance = maxDim * 3;
                    
                    window.camera.position.set(center.x + distance, center.y + distance/2, center.z + distance);
                    window.camera.lookAt(center);
                    
                    // Update controls if available
                    if (window.controls) {
                        window.controls.target.copy(center);
                        window.controls.update();
                    }
                    
                    return {
                        newCameraPosition: {
                            x: window.camera.position.x.toFixed(2),
                            y: window.camera.position.y.toFixed(2),
                            z: window.camera.position.z.toFixed(2)
                        },
                        deviceCenter: {
                            x: center.x.toFixed(2),
                            y: center.y.toFixed(2),
                            z: center.z.toFixed(2)
                        },
                        sceneSize: {
                            x: size.x.toFixed(2),
                            y: size.y.toFixed(2),
                            z: size.z.toFixed(2)
                        }
                    };
                }
            """)
            
            if isinstance(camera_adjust, dict):
                print(f"   Camera moved to: ({camera_adjust['newCameraPosition']['x']}, {camera_adjust['newCameraPosition']['y']}, {camera_adjust['newCameraPosition']['z']})")
                print(f"   Device center: ({camera_adjust['deviceCenter']['x']}, {camera_adjust['deviceCenter']['y']}, {camera_adjust['deviceCenter']['z']})")
                print(f"   Scene size: ({camera_adjust['sceneSize']['x']}, {camera_adjust['sceneSize']['y']}, {camera_adjust['sceneSize']['z']})")
                
                # Force a render
                await page.evaluate("() => window.renderer.render(window.scene, window.camera)");
                
                await asyncio.sleep(2)
            else:
                print(f"   Camera adjustment failed: {camera_adjust}")
            
            # Take screenshot
            await page.screenshot(path="test_screenshots/device_positions_debug.png")
            print(f"\n📸 Screenshot saved: test_screenshots/device_positions_debug.png")
            
        else:
            print("❌ Demo Mode button not found")
        
        print("\n🔍 Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_device_positions())
