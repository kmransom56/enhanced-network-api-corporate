#!/usr/bin/env python3
"""
Complete workflow demo for DrawIO Fortinet/Meraki MCP integration
"""

import asyncio
import json
import time
from pathlib import Path
from mcp_server import DrawIOMCPServer
from fortinet_integration import DrawIOFortinetIntegration

class DrawIOMCPDemo:
    """Complete demo showing all MCP capabilities"""
    
    def __init__(self):
        self.server = DrawIOMCPServer()
        self.integration = DrawIOFortinetIntegration()
        
    async def run_complete_demo(self):
        """Run the complete workflow demo"""
        print("🎯 DrawIO Fortinet/Meraki MCP - Complete Workflow Demo")
        print("=" * 60)
        
        # Step 1: Initialize
        print("\n📋 Step 1: Initializing MCP Server...")
        await self.server.initialize_topology_collector()
        print("✅ MCP Server initialized")
        
        # Step 2: Collect topology
        print("\n🔍 Step 2: Collecting Network Topology...")
        start_time = time.time()
        
        topology_result = await self.server.collect_topology({"refresh": True})
        topology_data = json.loads(topology_result.content[0].text)
        
        elapsed = time.time() - start_time
        print(f"✅ Topology collected in {elapsed:.2f}s")
        print(f"   📊 Devices: {topology_data['total_devices']}")
        print(f"   🔗 Links: {topology_data['total_links']}")
        
        # Step 3: Generate different diagram layouts
        print("\n🎨 Step 3: Generating Diagram Layouts...")
        
        layouts = ["hierarchical", "circular", "force-directed"]
        diagram_files = []
        
        for layout in layouts:
            print(f"   📐 Generating {layout} layout...")
            
            diagram_result = await self.server.generate_drawio_diagram({
                "layout": layout,
                "group_by": "type",
                "show_details": True,
                "color_code": True
            })
            
            if not diagram_result.isError:
                # Save diagram
                filename = f"network_topology_{layout}.drawio"
                with open(filename, "w") as f:
                    f.write(diagram_result.content[2].text)
                diagram_files.append(filename)
                print(f"     ✅ Saved {filename}")
            else:
                print(f"     ❌ Failed: {diagram_result.content[0].text}")
        
        # Step 4: Get topology summary
        print("\n📈 Step 4: Generating Topology Summary...")
        summary_result = await self.server.get_topology_summary({})
        summary = json.loads(summary_result.content[0].text)
        
        print("✅ Topology Summary:")
        print(f"   🏢 Sites: {', '.join(summary['sites'])}")
        print(f"   🔧 Device Types: {list(summary['device_types'].keys())}")
        
        # Step 5: Export data
        print("\n💾 Step 5: Exporting Data...")
        
        formats = ["json", "csv"]
        export_files = []
        
        for format_type in formats:
            export_result = await self.server.export_topology_json({
                "include_health": False,
                "format": format_type
            })
            
            if not export_result.isError:
                filename = f"network_topology.{format_type}"
                with open(filename, "w") as f:
                    f.write(export_result.content[0].text)
                export_files.append(filename)
                print(f"   ✅ Exported {filename}")
        
        # Step 6: Integration with Fortinet MCP
        print("\n🔗 Step 6: Fortinet MCP Integration...")
        
        try:
            integration_result = await self.integration.collect_and_generate("hierarchical")
            
            # Save integrated results
            with open("fortinet_scene.json", "w") as f:
                json.dump(integration_result["scene_data"], f, indent=2)
            
            with open("fortinet_integrated.drawio", "w") as f:
                f.write(integration_result["drawio_xml"])
            
            print("✅ Fortinet integration completed")
            print(f"   📄 3D Scene: fortinet_scene.json")
            print(f"   🎨 DrawIO: fortinet_integrated.drawio")
            
        except Exception as e:
            print(f"⚠️  Fortinet integration failed: {e}")
        
        # Step 7: Performance metrics
        print("\n📊 Step 7: Performance Metrics...")
        
        # Test multiple operations
        operations = 10
        start_time = time.time()
        
        for i in range(operations):
            await self.server.collect_topology({"refresh": False})
        
        total_time = time.time() - start_time
        avg_time = total_time / operations
        
        print(f"✅ Performance Test ({operations} operations):")
        print(f"   ⏱️  Total Time: {total_time:.2f}s")
        print(f"   📈 Average: {avg_time:.3f}s per operation")
        print(f"   🚀 Operations/sec: {operations/total_time:.1f}")
        
        # Step 8: Summary
        print("\n🎉 Demo Complete!")
        print("=" * 60)
        print("Generated Files:")
        
        all_files = diagram_files + export_files
        if all_files:
            for file in all_files:
                size = Path(file).stat().st_size
                print(f"   📄 {file} ({size:,} bytes)")
        
        print(f"\n📈 Results Summary:")
        print(f"   🔍 Devices Discovered: {topology_data['total_devices']}")
        print(f"   🔗 Links Found: {topology_data['total_links']}")
        print(f"   🎨 Diagram Layouts: {len(diagram_files)}")
        print(f"   💾 Export Formats: {len(export_files)}")
        print(f"   ⚡ Avg Response Time: {avg_time:.3f}s")
        
        # Step 9: Next steps
        print(f"\n🚀 Next Steps:")
        print(f"   1. Open DrawIO diagrams in your browser")
        print(f"   2. Configure real API credentials in .env")
        print(f"   3. Test with MCP client (Claude Desktop, Windsurf)")
        print(f"   4. Integrate with your 3D topology viewer")
        print(f"   5. Set up CI/CD automation")
        
        return True
    
    async def test_natural_language_workflow(self):
        """Demo natural language workflow"""
        print("\n🗣️  Natural Language Workflow Demo")
        print("-" * 40)
        
        # Simulate natural language requests
        requests = [
            {
                "request": "Show me my network topology with all devices",
                "tools": ["collect_topology"],
                "params": {"refresh": True}
            },
            {
                "request": "Create a hierarchical diagram grouped by device type",
                "tools": ["generate_drawio_diagram"],
                "params": {"layout": "hierarchical", "group_by": "type"}
            },
            {
                "request": "Export the data as JSON for my automation scripts",
                "tools": ["export_topology_json"],
                "params": {"format": "json"}
            },
            {
                "request": "Give me a summary of my network devices",
                "tools": ["get_topology_summary"],
                "params": {}
            }
        ]
        
        for i, req in enumerate(requests, 1):
            print(f"\n👤 User: {req['request']}")
            print(f"🤖 AI: Executing {', '.join(req['tools'])}...")
            
            start_time = time.time()
            
            # Execute the requested tools
            for tool in req["tools"]:
                if tool == "collect_topology":
                    result = await self.server.collect_topology(req["params"])
                elif tool == "generate_drawio_diagram":
                    result = await self.server.generate_drawio_diagram(req["params"])
                elif tool == "export_topology_json":
                    result = await self.server.export_topology_json(req["params"])
                elif tool == "get_topology_summary":
                    result = await self.server.get_topology_summary(req["params"])
                
                elapsed = time.time() - start_time
                
                if result.isError:
                    print(f"   ❌ Error: {result.content[0].text}")
                else:
                    print(f"   ✅ Completed in {elapsed:.2f}s")
                    
                    # Show brief result
                    if tool == "collect_topology":
                        data = json.loads(result.content[0].text)
                        print(f"   📊 Found {data['total_devices']} devices")
                    elif tool == "generate_drawio_diagram":
                        print(f"   🎨 Diagram generated ({len(result.content[2].text)} chars)")
                    elif tool == "export_topology_json":
                        print(f"   💾 Data exported")
                    elif tool == "get_topology_summary":
                        summary = json.loads(result.content[0].text)
                        print(f"   📈 {summary['total_devices']} devices, {summary['total_links']} links")
    
    async def test_real_time_updates(self):
        """Demo real-time topology monitoring"""
        print("\n⏱️  Real-time Monitoring Demo")
        print("-" * 40)
        
        print("🔄 Starting continuous monitoring (simulated)...")
        
        # Simulate network changes
        changes = [
            {"action": "device_added", "device": "New-FortiGate-02"},
            {"action": "device_down", "device": "AP-Floor1"},
            {"action": "link_added", "source": "FG-001", "target": "New-FortiGate-02"},
            {"action": "device_up", "device": "AP-Floor1"}
        ]
        
        for i, change in enumerate(changes, 1):
            print(f"\n📡 Change {i}: {change['action']}")
            
            # Collect updated topology
            result = await self.server.collect_topology({"refresh": True})
            
            if not result.isError:
                topology = json.loads(result.content[0].text)
                
                # Generate updated diagram
                diagram_result = await self.server.generate_drawio_diagram({
                    "layout": "hierarchical",
                    "color_code": True
                })
                
                if not diagram_result.isError:
                    filename = f"topology_update_{i}.drawio"
                    with open(filename, "w") as f:
                        f.write(diagram_result.content[2].text)
                    print(f"   ✅ Updated diagram saved: {filename}")
                else:
                    print(f"   ❌ Diagram update failed")
            
            # Simulate time delay
            await asyncio.sleep(1)
        
        print("\n🎯 Real-time monitoring demo completed")

async def main():
    """Main demo entry point"""
    demo = DrawIOMCPDemo()
    
    try:
        # Run complete workflow demo
        await demo.run_complete_demo()
        
        # Run natural language workflow
        await demo.test_natural_language_workflow()
        
        # Run real-time monitoring demo
        await demo.test_real_time_updates()
        
        print("\n🎊 All demos completed successfully!")
        print("\n📚 Next Steps:")
        print("1. Review generated files")
        print("2. Open DrawIO diagrams in browser")
        print("3. Configure real API credentials")
        print("4. Test with MCP client applications")
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
