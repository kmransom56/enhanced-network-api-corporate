#!/usr/bin/env python3
"""
Test the complete FortiGate topology with client devices
"""

import json
import requests
import time

def test_topology_endpoints():
    """Test both raw and scene topology endpoints"""
    
    base_url = "http://127.0.0.1:11111"
    
    print("🔍 Testing FortiGate Topology Endpoints with Client Devices...")
    
    # Test raw topology
    print("\n📊 Testing /api/topology/raw...")
    try:
        response = requests.get(f"{base_url}/api/topology/raw", timeout=30)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"  ✅ Raw Topology Success!")
            print(f"  📡 Gateways: {len(data.get('gateways', []))}")
            print(f"  🔌 Switches: {len(data.get('switches', []))}")
            print(f"  📶 APs: {len(data.get('aps', []))}")
            print(f"  👥 Clients: {len(data.get('clients', []))}")
            print(f"  🔗 Links: {len(data.get('links', []))}")
            
            # Show device breakdown
            clients = data.get('clients', [])
            if clients:
                client_types = {}
                for client in clients:
                    device_type = client.get('device_type', 'unknown')
                    client_types[device_type] = client_types.get(device_type, 0) + 1
                
                print(f"\n  👥 Client Breakdown:")
                for device_type, count in sorted(client_types.items()):
                    print(f"    📱 {device_type}: {count} devices")
            
            # Save raw topology
            with open('test_raw_topology.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  💾 Saved to test_raw_topology.json")
            
        else:
            print(f"  ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")
    
    # Test 3D scene topology
    print("\n🎮 Testing /api/topology/scene...")
    try:
        response = requests.get(f"{base_url}/api/topology/scene", timeout=30)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"  ✅ 3D Scene Success!")
            print(f"  🎯 Nodes: {len(data.get('nodes', []))}")
            print(f"  🔗 Links: {len(data.get('links', []))}")
            
            # Show node breakdown by type
            nodes = data.get('nodes', [])
            if nodes:
                node_types = {}
                for node in nodes:
                    node_type = node.get('type', 'unknown')
                    node_types[node_type] = node_types.get(node_type, 0) + 1
                
                print(f"\n  🎯 Node Breakdown:")
                for node_type, count in sorted(node_types.items()):
                    print(f"    📦 {node_type}: {count} nodes")
            
            # Show sample nodes
            print(f"\n  📦 Sample Nodes:")
            for node in nodes[:5]:
                name = node.get('name', 'Unknown')
                node_type = node.get('type', 'unknown')
                role = node.get('role', 'unknown')
                print(f"    📦 {name} ({node_type}) - {role}")
            
            # Save scene topology
            with open('test_scene_topology.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  💾 Saved to test_scene_topology.json")
            
        else:
            print(f"  ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")
    
    print(f"\n🌐 Test completed!")
    print(f"📱 Check the web UI at: http://127.0.0.1:11111/")
    print(f"🔄 Click 'Load Fortinet Topology' to see the complete network with clients!")

if __name__ == "__main__":
    test_topology_endpoints()
