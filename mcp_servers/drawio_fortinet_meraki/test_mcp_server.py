#!/usr/bin/env python3
"""
Test script for DrawIO Fortinet/Meraki MCP Server
"""

import asyncio
import json
import logging
from mcp_servers.drawio_fortinet_meraki.mcp_server import DrawIOMCPServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_topology_collection():
    """Test topology collection functionality"""
    print("🧪 Testing Topology Collection...")
    
    server = DrawIOMCPServer()
    await server.initialize_topology_collector()
    
    # Test collect_topology
    result = await server.collect_topology({"refresh": True})
    
    if result.isError:
        print(f"❌ Topology collection failed: {result.content[0].text}")
        return False
    
    print("✅ Topology collection successful")
    topology_data = json.loads(result.content[0].text)
    print(f"   📊 Found {topology_data['total_devices']} devices")
    print(f"   🔗 Found {topology_data['total_links']} links")
    
    return True

async def test_diagram_generation():
    """Test diagram generation"""
    print("\n🧪 Testing Diagram Generation...")
    
    server = DrawIOMCPServer()
    await server.initialize_topology_collector()
    
    # First collect topology
    await server.collect_topology({"refresh": True})
    
    # Test different layouts
    layouts = ["hierarchical", "circular", "force-directed"]
    
    for layout in layouts:
        print(f"   🎨 Testing {layout} layout...")
        
        result = await server.generate_drawio_diagram({
            "layout": layout,
            "group_by": "type",
            "show_details": True,
            "color_code": True
        })
        
        if result.isError:
            print(f"❌ Diagram generation failed for {layout}: {result.content[0].text}")
            return False
        
        print(f"   ✅ {layout} diagram generated successfully")
    
    return True

async def test_topology_summary():
    """Test topology summary"""
    print("\n🧪 Testing Topology Summary...")
    
    server = DrawIOMCPServer()
    await server.initialize_topology_collector()
    
    result = await server.get_topology_summary({})
    
    if result.isError:
        print(f"❌ Summary generation failed: {result.content[0].text}")
        return False
    
    summary = json.loads(result.content[0].text)
    print("✅ Summary generated successfully")
    print(f"   📈 Total devices: {summary['total_devices']}")
    print(f"   🔗 Total links: {summary['total_links']}")
    print(f"   🏢 Sites: {', '.join(summary['sites'])}")
    
    return True

async def test_export_functionality():
    """Test export functionality"""
    print("\n🧪 Testing Export Functionality...")
    
    server = DrawIOMCPServer()
    await server.initialize_topology_collector()
    
    # Test JSON export
    result = await server.export_topology_json({
        "include_health": False,
        "format": "json"
    })
    
    if result.isError:
        print(f"❌ JSON export failed: {result.content[0].text}")
        return False
    
    print("✅ JSON export successful")
    
    # Test CSV export
    result = await server.export_topology_json({
        "include_health": False,
        "format": "csv"
    })
    
    if result.isError:
        print(f"❌ CSV export failed: {result.content[0].text}")
        return False
    
    print("✅ CSV export successful")
    
    return True

async def test_demo_mode():
    """Test demo mode without real APIs"""
    print("\n🧪 Testing Demo Mode...")
    
    # Create server without API configuration
    server = DrawIOMCPServer()
    # Don't initialize topology collector to trigger demo mode
    
    result = await server.collect_topology({"refresh": True})
    
    if result.isError:
        print(f"❌ Demo mode failed: {result.content[0].text}")
        return False
    
    topology_data = json.loads(result.content[0].text)
    print("✅ Demo mode working")
    print(f"   📊 Demo topology: {topology_data['total_devices']} devices")
    
    # Test diagram generation with demo data
    result = await server.generate_drawio_diagram({
        "layout": "hierarchical",
        "group_by": "type"
    })
    
    if result.isError:
        print(f"❌ Demo diagram generation failed: {result.content[0].text}")
        return False
    
    print("✅ Demo diagram generated")
    
    return True

async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting DrawIO MCP Server Tests\n")
    
    tests = [
        test_demo_mode,
        test_topology_collection,
        test_diagram_generation,
        test_topology_summary,
        test_export_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
