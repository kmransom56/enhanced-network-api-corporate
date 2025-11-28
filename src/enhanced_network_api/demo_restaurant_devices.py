#!/usr/bin/env python3
"""
Demo script for restaurant device recognition
Test MAC address matching for restaurant technology devices
"""

import json
from device_mac_matcher import DeviceModelMatcher

def demo_restaurant_device_recognition():
    """Demonstrate restaurant device recognition with real MAC addresses"""
    
    print("🍽️  Restaurant Technology Device Recognition Demo")
    print("=" * 50)
    
    # Initialize the matcher
    matcher = DeviceModelMatcher()
    
    # Test MAC addresses from restaurant technology devices
    test_devices = [
        {
            "mac": "00:0C:F1:12:34:56",
            "hostname": "Clover-Station-01",
            "description": "Clover POS Register"
        },
        {
            "mac": "AC:BC:32:AB:CD:EF", 
            "hostname": "Square-Terminal-01",
            "description": "Square Payment Terminal"
        },
        {
            "mac": "B8:27:EB:98:76:54",
            "hostname": "Toast-KDS-01", 
            "description": "Toast Kitchen Display System"
        },
        {
            "mac": "28:CF:E9:12:34:56",
            "hostname": "iPad-Table-01",
            "description": "iPad POS Tablet"
        },
        {
            "mac": "00:0D:93:AB:CD:EF",
            "hostname": "NCR-Printer-01",
            "description": "NCR Kitchen Printer"
        },
        {
            "mac": "44:38:39:12:34:56",
            "hostname": "Square-Register-01",
            "description": "Square Register"
        },
        {
            "mac": "40:4D:55:AB:CD:EF",
            "hostname": "Clover-Mini-01",
            "description": "Clover Mini POS"
        },
        {
            "mac": "68:72:51:12:34:56",
            "hostname": "Clover-Flex-01",
            "description": "Clover Flex Payment"
        },
        {
            "mac": "DC:A6:32:98:76:54",
            "hostname": "Digital-Menu-01",
            "description": "Digital Menu Board"
        },
        {
            "mac": "90:6C:AC:12:34:56",
            "hostname": "FortiGate-WiFi",
            "description": "Network Firewall (Restaurant WiFi)"
        }
    ]
    
    print(f"Testing {len(test_devices)} devices...\n")
    
    results = []
    for device in test_devices:
        context = {"hostname": device["hostname"]}
        device_info = matcher.match_mac_to_model(device["mac"], context)
        
        results.append({
            "mac": device["mac"],
            "hostname": device["hostname"],
            "description": device["description"],
            "detected_vendor": device_info.vendor,
            "detected_type": device_info.device_type,
            "pos_system": device_info.pos_system,
            "model_path": device_info.model_path,
            "confidence": device_info.confidence
        })
        
        print(f"🔍 {device['description']}")
        print(f"   MAC: {device['mac']}")
        print(f"   Hostname: {device['hostname']}")
        print(f"   ✅ Detected: {device_info.vendor} - {device_info.device_type}")
        if device_info.pos_system:
            print(f"   💳 POS System: {device_info.pos_system}")
        print(f"   📦 3D Model: {device_info.model_path}")
        print(f"   🎯 Confidence: {device_info.confidence}")
        print("-" * 40)
    
    # Save results
    with open("restaurant_device_demo_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Results saved to restaurant_device_demo_results.json")
    print(f"📈 Successfully identified {len([r for r in results if r['confidence'] == 'high'])} devices with high confidence")
    
    # Summary by device type
    device_types = {}
    for result in results:
        device_type = result["detected_type"]
        device_types[device_type] = device_types.get(device_type, 0) + 1
    
    print(f"\n📋 Device Type Summary:")
    for device_type, count in device_types.items():
        print(f"   {device_type}: {count}")

def demo_restaurant_icons():
    """Demonstrate restaurant icon library"""
    print("\n🎨 Restaurant Icon Library Demo")
    print("=" * 30)
    
    try:
        from restaurant_icon_downloader import RestaurantIconDownloader
        
        downloader = RestaurantIconDownloader()
        icons = downloader.download_all_icons()
        
        print(f"📦 Generated {len(icons)} restaurant icons:")
        
        # Group by device type
        by_type = {}
        for icon in icons:
            device_type = icon.device_type
            if device_type not in by_type:
                by_type[device_type] = []
            by_type[device_type].append(icon)
        
        for device_type, type_icons in by_type.items():
            print(f"\n  {device_type.replace('_', ' ').title()}:")
            for icon in type_icons:
                print(f"    - {icon.name}")
                if icon.svg_path:
                    print(f"      📄 SVG: {icon.svg_path}")
                if icon.pos_system:
                    print(f"      💳 POS: {icon.pos_system}")
        
    except Exception as e:
        print(f"❌ Icon demo failed: {e}")

if __name__ == "__main__":
    demo_restaurant_device_recognition()
    demo_restaurant_icons()
    
    print("\n🎉 Restaurant Technology Demo Complete!")
    print("\nNext steps:")
    print("1. Start the API: /home/keith/cagent/run-enhanced-network-api.sh api")
    print("2. Test endpoints:")
    print("   - GET /api/devices/lookup/{mac_address}")
    print("   - POST /api/devices/match-macs")
    print("   - GET /api/icons/restaurant")
    print("3. View 3D topology: http://127.0.0.1:11111/static/babylon_topology.html")
