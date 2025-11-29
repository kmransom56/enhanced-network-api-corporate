#!/usr/bin/env python3
"""
Debug why device-specific icons are not loading
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_icon_loading():
    """Debug icon loading issues"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        # Console logging
        def handle_console(msg):
            if "icon" in msg.text.lower() or "billboard" in msg.text.lower() or "svg" in msg.text.lower() or "fallback" in msg.text.lower():
                print(f"📋 {msg.type}: {msg.text}")
            elif msg.type == "error":
                print(f"❌ {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
        
        # Navigate to the main page
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        print("🎯 Debugging Icon Loading Issues")
        print("=" * 50)
        
        # Check which icon files are available
        icon_check = await page.evaluate("""
            () => {
                const iconPaths = [
                    '/static/fortinet-icons/FortiGate.svg',
                    '/static/fortinet-icons/FortiSwitch.svg', 
                    '/static/fortinet-icons/FortiAP.svg'
                ];
                
                const results = {};
                
                iconPaths.forEach(path => {
                    results[path] = {
                        exists: false,
                        error: null
                    };
                });
                
                return results;
            }
        """)
        
        print("🔍 Icon File Check:")
        for path, result in icon_check.items():
            print(f"   {path}: {result}")
        
        # Test icon loading manually
        print(f"\n🔧 Testing Manual Icon Loading...")
        manual_test = await page.evaluate("""
            () => {
                try {
                    // Test loading a FortiGate icon
                    const iconUrl = '/static/fortinet-icons/FortiGate.svg';
                    
                    return fetch(iconUrl)
                        .then(response => {
                            if (response.ok) {
                                return response.text().then(content => {
                                    return {
                                        status: 'success',
                                        url: iconUrl,
                                        size: content.length,
                                        isSvg: content.includes('<svg')
                                    };
                                });
                            } else {
                                return {
                                    status: 'failed',
                                    url: iconUrl,
                                    error: `HTTP ${response.status}`
                                };
                            }
                        })
                        .catch(error => ({
                            status: 'error',
                            url: iconUrl,
                            error: error.message
                        }));
                } catch (error) {
                    return {
                        status: 'exception',
                        error: error.message
                    };
                }
            }
        """)
        
        print(f"   Manual icon test: {manual_test}")
        
        # Check what createDeviceMesh is trying to do
        print(f"\n🔍 Checking createDeviceMesh function...")
        mesh_function_check = await page.evaluate("""
            () => {
                if (typeof window.createDeviceMesh === 'function') {
                    return 'createDeviceMesh function available';
                } else {
                    return 'createDeviceMesh function NOT available';
                }
            }
        """)
        
        print(f"   Function availability: {mesh_function_check}")
        
        # Test creating a device with icon
        print(f"\n🎭 Testing Device Creation with Icons...")
        device_test = await page.evaluate("""
            () => {
                try {
                    // Clear scene first
                    if (window.clearScene) {
                        window.clearScene();
                    }
                    
                    // Create a FortiGate device
                    return window.createDeviceMesh('fortigate', 'test-fortigate')
                        .then(mesh => {
                            if (mesh) {
                                return {
                                    success: true,
                                    hasGeometry: !!mesh.geometry,
                                    hasMaterial: !!mesh.material,
                                    hasTexture: mesh.material && mesh.material.map ? true : false,
                                    position: {
                                        x: mesh.position.x,
                                        y: mesh.position.y,
                                        z: mesh.position.z
                                    },
                                    userData: mesh.userData
                                };
                            } else {
                                return { success: false, error: 'No mesh returned' };
                            }
                        })
                        .catch(error => ({
                            success: false,
                            error: error.message
                        }));
                } catch (error) {
                    return {
                        success: false,
                        error: error.message
                    };
                }
            }
        """)
        
        print(f"   Device creation test: {device_test}")
        
        # Load real Fortinet topology to see what happens
        print(f"\n🔥 Testing Real Fortinet Topology...")
        load_fortinet = page.locator("button:has-text('🔥 Load Fortinet')")
        if await load_fortinet.count() > 0:
            await load_fortinet.click()
            await asyncio.sleep(3)
            
            # Check what devices were created
            real_topology = await page.evaluate("""
                () => {
                    const devices = window.scene ? window.scene.children.filter(obj => obj.userData.type) : [];
                    
                    return {
                        deviceCount: devices.length,
                        devices: devices.map(device => ({
                            name: device.name || device.userData.name,
                            type: device.userData.type,
                            hasGeometry: !!device.geometry,
                            hasMaterial: !!device.material,
                            hasTexture: device.material && device.material.map ? true : false,
                            materialType: device.material ? device.material.type : 'none',
                            position: {
                                x: device.position.x,
                                y: device.position.y,
                                z: device.position.z
                            }
                        }))
                    };
                }
            """)
            
            print(f"   Real topology results:")
            print(f"      Device count: {real_topology['deviceCount']}")
            for device in real_topology['devices']:
                print(f"      {device['type']} '{device['name']}':")
                print(f"         Geometry: {device['hasGeometry']}")
                print(f"         Material: {device['materialType']}")
                print(f"         Texture: {device['hasTexture']}")
                print(f"         Position: ({device['position']['x']}, {device['position']['y']}, {device['position']['z']})")
        
        # Take screenshot
        await page.screenshot(path="test_screenshots/icon_loading_debug.png")
        print(f"\n📸 Screenshot saved: test_screenshots/icon_loading_debug.png")
        
        print("\n🔍 Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_icon_loading())
