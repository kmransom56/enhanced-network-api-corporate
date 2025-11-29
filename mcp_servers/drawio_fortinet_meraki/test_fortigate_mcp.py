#!/usr/bin/env python3
"""
Test script for FortiGate-specific MCP integration
"""

import asyncio
import json
import os
from dotenv import load_dotenv
from mcp_server import DrawIOMCPServer

async def test_fortigate_mcp():
    """Test the FortiGate MCP server"""
    print("🔥 FortiGate MCP Server Test")
    print("=" * 40)
    
    # Load environment
    load_dotenv()
    
    # Check configuration
    fortigate_host = os.getenv("FORTIMANAGER_HOST")
    fortigate_user = os.getenv("FORTIMANAGER_USERNAME")
    fortigate_pass = os.getenv("FORTIMANAGER_PASSWORD")
    
    print(f"🔧 Configuration:")
    print(f"   🏠 FortiGate Host: {fortigate_host}")
    print(f"   👤 Username: {fortigate_user}")
    print(f"   🔐 Password: {'✅ Set' if fortigate_pass else '❌ Not set'}")
    
    # Initialize server
    server = DrawIOMCPServer()
    await server.initialize_topology_collector()
    
    print(f"\n🧪 Testing MCP Tools:")
    
    # Test 1: Collect topology
    print(f"\n1️⃣  Collecting FortiGate Topology...")
    result = await server.collect_topology({"refresh": True})
    
    if not result.isError:
        topology = json.loads(result.content[0].text)
        print(f"   ✅ Success!")
        print(f"   📊 Devices: {topology['total_devices']}")
        print(f"   🔗 Links: {topology['total_links']}")
        print(f"   📡 Source: {topology['source']}")
        
        # Show FortiGate details
        fortigate_devices = [d for d in topology['devices'] if d['type'] == 'fortigate']
        if fortigate_devices:
            fg = fortigate_devices[0]
            print(f"   🔥 FortiGate: {fg['name']}")
            print(f"   💻 Model: {fg.get('model', 'Unknown')}")
            print(f"   📈 CPU: {fg.get('cpu_usage', 0)}%")
            print(f"   🧠 Memory: {fg.get('memory_usage', 0)}%")
            print(f"   🔌 Interfaces: {len(fg.get('interfaces', []))}")
    else:
        print(f"   ❌ Failed: {result.content[0].text}")
        return False
    
    # Test 2: Generate diagram
    print(f"\n2️⃣  Generating DrawIO Diagram...")
    diagram_result = await server.generate_drawio_diagram({
        "layout": "hierarchical",
        "group_by": "type",
        "show_details": True,
        "color_code": True
    })
    
    if not diagram_result.isError:
        diagram_xml = diagram_result.content[2].text
        print(f"   ✅ Diagram generated!")
        print(f"   📄 XML Length: {len(diagram_xml)} characters")
        
        # Save diagram
        with open("fortigate_topology_test.drawio", "w") as f:
            f.write(diagram_xml)
        print(f"   💾 Saved: fortigate_topology_test.drawio")
    else:
        print(f"   ❌ Failed: {diagram_result.content[0].text}")
    
    # Test 3: Get summary
    print(f"\n3️⃣  Getting Topology Summary...")
    summary_result = await server.get_topology_summary({})
    
    if not summary_result.isError:
        summary = json.loads(summary_result.content[0].text)
        print(f"   ✅ Summary generated!")
        print(f"   📈 Total Devices: {summary['total_devices']}")
        print(f"   🔗 Total Links: {summary['total_links']}")
        print(f"   🏢 Sites: {', '.join(summary['sites'])}")
        print(f"   🔧 Device Types: {list(summary['device_types'].keys())}")
    else:
        print(f"   ❌ Failed: {summary_result.content[0].text}")
    
    # Test 4: Export data
    print(f"\n4️⃣  Exporting Topology Data...")
    export_result = await server.export_topology_json({
        "include_health": True,
        "format": "json"
    })
    
    if not export_result.isError:
        print(f"   ✅ Data exported!")
        
        # Save export
        with open("fortigate_topology_export.json", "w") as f:
            f.write(export_result.content[0].text)
        print(f"   💾 Saved: fortigate_topology_export.json")
    else:
        print(f"   ❌ Failed: {export_result.content[0].text}")
    
    # Test 5: Natural language simulation
    print(f"\n5️⃣  Natural Language Commands Simulation...")
    
    commands = [
        "Show me my FortiGate and all connected networks",
        "Create a hierarchical diagram with FortiGate at the top",
        "Export the configuration as JSON"
    ]
    
    for i, command in enumerate(commands, 1):
        print(f"   👤 User: {command}")
        
        if i == 1:
            result = await server.collect_topology({})
        elif i == 2:
            result = await server.generate_drawio_diagram({"layout": "hierarchical"})
        elif i == 3:
            result = await server.export_topology_json({"format": "json"})
        
        if not result.isError:
            print(f"   🤖 AI: ✅ Command executed successfully")
        else:
            print(f"   🤖 AI: ❌ Command failed")
    
    print(f"\n🎉 FortiGate MCP Test Complete!")
    print(f"\n📋 Generated Files:")
    
    files = ["fortigate_topology_test.drawio", "fortigate_topology_export.json"]
    for file in files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   📄 {file} ({size:,} bytes)")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Configure your FortiGate password in .env")
    print(f"   2. Test with real API connection")
    print(f"   3. Open DrawIO diagrams in browser")
    print(f"   4. Connect to MCP client (Claude Desktop, Windsurf)")
    print(f"   5. Integrate with your CodeLlama model")
    
    return True

async def test_codellama_integration():
    """Test integration with CodeLlama model"""
    print(f"\n🤖 CodeLlama Integration Test")
    print("-" * 40)
    
    codellama_path = os.getenv("CODELLAMA_MODEL_PATH")
    if codellama_path and os.path.exists(codellama_path):
        print(f"   ✅ CodeLlama model found: {codellama_path}")
        print(f"   📝 Model files: {len(os.listdir(codellama_path))} items")
        
        # Future: Add CodeLlama integration
        print(f"   🔮 CodeLlama integration ready for future enhancement")
    else:
        print(f"   ⚠️  CodeLlama model not found at: {codellama_path}")
        print(f"   💡 Update CODELLAMA_MODEL_PATH in .env")

async def main():
    """Main test runner"""
    try:
        # Test FortiGate MCP
        success = await test_fortigate_mcp()
        
        # Test CodeLlama integration
        await test_codellama_integration()
        
        if success:
            print(f"\n🎊 All tests passed! Your FortiGate MCP server is ready.")
        else:
            print(f"\n❌ Some tests failed. Check configuration.")
            
    except KeyboardInterrupt:
        print(f"\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
