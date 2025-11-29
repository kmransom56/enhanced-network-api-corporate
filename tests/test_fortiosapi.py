#!/usr/bin/env python3
"""
Test script to connect to FortiGate using fortiosapi and get topology data
"""

import fortiosapi
import json
import ssl
import sys

def test_fortigate_connection():
    """Test connection to FortiGate and get system information"""
    
    # Configuration from your .env file
    FGT_HOST = "192.168.0.254"
    FGT_PORT = "10443"
    FGT_USERNAME = "!cg@RW%G@o"
    FGT_TOKEN = "679Nf51c76p7z1Qq6sqhhz8nghmnpN"
    
    try:
        print("🔍 Testing FortiOS API connection...")
        
        # Initialize FortiOSAPI
        fgt = fortiosapi.FortiOSAPI()
        
        # Use token-based authentication (more reliable)
        print(f"📡 Connecting to {FGT_HOST}:{FGT_PORT}...")
        fgt.tokenlogin(
            host=f"{FGT_HOST}:{FGT_PORT}",
            apitoken=FGT_TOKEN,
            verify=False,  # For self-signed certs
            timeout=10
        )
        
        print("✅ Successfully connected to FortiGate!")
        
        # Test basic system info
        print("\n📊 Getting system information...")
        system_info = fgt.get('system', 'status')
        print(f"System Status: {system_info.get('results', {}).get('status', 'Unknown')}")
        print(f"Hostname: {system_info.get('results', {}).get('hostname', 'Unknown')}")
        print(f"Serial: {system_info.get('results', {}).get('serial', 'Unknown')}")
        print(f"Version: {system_info.get('results', {}).get('version', 'Unknown')}")
        
        # Get interface information for topology
        print("\n🌐 Getting interface information...")
        interfaces = fgt.get('system', 'interface')
        interface_list = interfaces.get('results', [])
        print(f"Found {len(interface_list)} interfaces")
        
        # Get DHCP clients for device discovery
        print("\n📱 Getting DHCP client information...")
        try:
            dhcp_clients = fgt.monitor('system', 'dhcp', 'client')
            client_list = dhcp_clients.get('results', [])
            print(f"Found {len(client_list)} DHCP clients")
            
            # Show first few clients
            for i, client in enumerate(client_list[:3]):
                print(f"  Client {i+1}: {client.get('hostname', 'Unknown')} - {client.get('ip', 'Unknown')}")
        except Exception as e:
            print(f"DHCP client query failed: {e}")
        
        # Get wireless APs if available
        print("\n📡 Getting wireless AP information...")
        try:
            wireless_aps = fgt.monitor('wireless', 'ap', 'status')
            ap_list = wireless_aps.get('results', [])
            print(f"Found {len(ap_list)} wireless APs")
            
            # Show AP details
            for i, ap in enumerate(ap_list[:3]):
                print(f"  AP {i+1}: {ap.get('name', 'Unknown')} - {ap.get('serial', 'Unknown')}")
        except Exception as e:
            print(f"Wireless AP query failed: {e}")
        
        # Get switch controller info if available
        print("\n🔗 Getting switch controller information...")
        try:
            switch_info = fgt.get('switch-controller', 'managed-switches')
            switch_list = switch_info.get('results', [])
            print(f"Found {len(switch_list)} managed switches")
            
            # Show switch details
            for i, switch in enumerate(switch_list[:3]):
                print(f"  Switch {i+1}: {switch.get('name', 'Unknown')} - {switch.get('ip', 'Unknown')}")
        except Exception as e:
            print(f"Switch controller query failed: {e}")
        
        # Create topology data structure
        topology_data = {
            "nodes": [],
            "links": [],
            "timestamp": "2025-11-22T15:36:00Z",
            "source": "fortiosapi"
        }
        
        # Add FortiGate as central node
        fgt_node = {
            "id": f"fgt-{FGT_HOST.replace('.', '-')}",
            "name": f"FortiGate-{system_info.get('results', {}).get('hostname', 'Unknown')}",
            "type": "fortigate",
            "ip": FGT_HOST,
            "model": system_info.get('results', {}).get('version', 'Unknown'),
            "status": "active",
            "role": "firewall"
        }
        topology_data["nodes"].append(fgt_node)
        
        # Add interfaces as connection points
        for interface in interface_list:
            if interface.get('alias') and interface.get('ip'):
                interface_node = {
                    "id": f"if-{interface.get('alias', 'unknown').replace(' ', '-')}",
                    "name": interface.get('alias', 'Unknown'),
                    "type": "interface",
                    "ip": interface.get('ip'),
                    "model": "Interface",
                    "status": "active" if interface.get('status') == 'up' else "inactive"
                }
                topology_data["nodes"].append(interface_node)
                
                # Link interface to FortiGate
                topology_data["links"].append({
                    "source": fgt_node["id"],
                    "target": interface_node["id"],
                    "type": "internal",
                    "status": "active" if interface.get('status') == 'up' else "inactive"
                })
        
        print(f"\n🎯 Generated topology with {len(topology_data['nodes'])} nodes and {len(topology_data['links'])} links")
        
        # Save topology data
        with open('/home/keith/enhanced-network-api-corporate/fortigate_topology.json', 'w') as f:
            json.dump(topology_data, f, indent=2)
        
        print("💾 Topology data saved to fortigate_topology.json")
        
        return topology_data
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return None
        
    finally:
        # Logout
        try:
            if 'fgt' in locals():
                fgt.logout()
                print("🔐 Logged out successfully")
        except Exception:
            pass

if __name__ == "__main__":
    print("🚀 Starting FortiGate Topology Discovery Test")
    print("=" * 50)
    
    topology = test_fortigate_connection()
    
    if topology:
        print("\n✅ Test completed successfully!")
        print(f"📊 Found {len(topology['nodes'])} devices")
        print(f"🔗 Found {len(topology['links'])} connections")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
