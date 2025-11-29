#!/usr/bin/env python3
"""
Debug why Demo Mode only loads 1 device instead of 6
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_demo_loading():
    """Debug Demo Mode device loading"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        # Console logging
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"{msg.type}: {msg.text}")
            if "demo" in msg.text.lower() or "device" in msg.text.lower() or "loaded" in msg.text.lower():
                print(f"📋 {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
        
        # Navigate to the main page
        await page.goto("http://127.0.0.1:11111/")
        await page.wait_for_load_state("networkidle")
        
        print("🎭 Debugging Demo Mode Loading")
        print("=" * 50)
        
        # Clear scene first
        await page.evaluate("() => { if (window.clearScene) window.clearScene(); }")
        await asyncio.sleep(1)
        
        # Click Demo Mode button
        demo_button = page.locator("button:has-text('🎭 Demo Mode')")
        if await demo_button.count() > 0:
            console_messages.clear()
            await demo_button.click()
            await asyncio.sleep(5)
            
            # Check what Demo Mode actually loaded
            demo_data = await page.evaluate("""
                () => {
                    // Check if demo topology data was processed
                    const demoMessages = Array.from(console.messages || []).filter(msg => 
                        msg.text && msg.text.includes('Demo topology loaded')
                    );
                    
                    // Check current scene state
                    const devices = window.scene ? window.scene.children.filter(obj => obj.userData.type) : [];
                    
                    // Check if loadFortinetTopologyScene was called and with what data
                    return {
                        demoMessagesFound: demoMessages.length,
                        currentDeviceCount: devices.length,
                        currentDevices: devices.map(d => ({
                            name: d.name || d.userData.name,
                            type: d.userData.type,
                            position: { x: d.position.x, y: d.position.y, z: d.position.z }
                        })),
                        windowSceneExists: !!window.scene,
                        windowMeshesCount: window.meshes ? Object.keys(window.meshes).length : 0,
                        windowMeshesKeys: window.meshes ? Object.keys(window.meshes) : []
                    };
                }
            """)
            
            print(f"🎯 Demo Mode Results:")
            print(f"   Demo messages found: {demo_data['demoMessagesFound']}")
            print(f"   Current device count: {demo_data['currentDeviceCount']}")
            print(f"   Window meshes count: {demo_data['windowMeshesCount']}")
            print(f"   Window meshes keys: {demo_data['windowMeshesKeys']}")
            
            print(f"\n📦 Current devices in scene:")
            for device in demo_data['currentDevices']:
                print(f"   {device['type']} '{device['name']}' at ({device['position']['x']}, {device['position']['y']}, {device['position']['z']})")
            
            # Check if Demo Mode is calling the wrong function
            console_analysis = await page.evaluate("""
                () => {
                    // Look for specific console patterns
                    const patterns = {
                        loadFortinetCalled: console.messages.some(msg => msg.text && msg.text.includes('Loading Fortinet topology scene')),
                        demoTopologyLoaded: console.messages.some(msg => msg.text && msg.text.includes('Demo topology loaded')),
                        deviceCountLoaded: console.messages.some(msg => msg.text && msg.text.includes('6 devices'))
                    };
                    
                    return patterns;
                }
            """)
            
            print(f"\n🔍 Console Analysis:")
            print(f"   loadFortinetCalled: {console_analysis['loadFortinetCalled']}")
            print(f"   demoTopologyLoaded: {console_analysis['demoTopologyLoaded']}")
            print(f"   deviceCountLoaded: {console_analysis['deviceCountLoaded']}")
            
            # Check if the Demo Mode button is calling the wrong function
            button_function = await page.evaluate("""
                () => {
                    const demoButton = document.querySelector('button:has-text("🎭 Demo Mode")');
                    if (!demoButton) return 'Button not found';
                    
                    const onclick = demoButton.getAttribute('onclick');
                    const eventListeners = demoButton.onclick ? 'has onclick' : 'no onclick';
                    
                    return {
                        onclick: onclick,
                        hasEventListeners: eventListeners,
                        buttonText: demoButton.textContent
                    };
                }
            """)
            
            print(f"\n🔘 Demo Button Analysis:")
            print(f"   Button text: {button_function['buttonText']}")
            print(f"   OnClick: {button_function['onclick']}")
            print(f"   Event listeners: {button_function['hasEventListeners']}")
            
            # Try to manually call Demo Mode
            print(f"\n🔧 Testing manual Demo Mode call...")
            manual_demo = await page.evaluate("""
                () => {
                    try {
                        // Look for demo topology data
                        if (typeof loadDemoTopology === 'function') {
                            loadDemoTopology();
                            return 'loadDemoTopology() called';
                        } else if (typeof window.loadDemoTopology === 'function') {
                            window.loadDemoTopology();
                            return 'window.loadDemoTopology() called';
                        } else {
                            return 'No loadDemoTopology function found';
                        }
                    } catch (error) {
                        return 'Manual demo failed: ' + error.message;
                    }
                }
            """)
            
            print(f"   Manual demo result: {manual_demo}")
            await asyncio.sleep(3)
            
            # Check device count after manual demo
            after_manual = await page.evaluate("""
                () => {
                    const devices = window.scene ? window.scene.children.filter(obj => obj.userData.type) : [];
                    return {
                        deviceCount: devices.length,
                        devices: devices.map(d => ({
                            name: d.name || d.userData.name,
                            type: d.userData.type
                        }))
                    };
                }
            """)
            
            print(f"   Devices after manual demo: {after_manual['deviceCount']}")
            for device in after_manual['devices']:
                print(f"      {device['type']} '{device['name']}'")
            
        else:
            print("❌ Demo Mode button not found")
        
        print("\n🔍 Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_demo_loading())
