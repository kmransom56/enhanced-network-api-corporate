#!/usr/bin/env python3
"""
Generates a network map data file (network_map.json)
"""

import json
from pathlib import Path
import logging
from typing import Dict, List, Any

# Assuming the script is run from the project root
from fortigate import FortiGateModule
from device_mac_matcher import DeviceModelMatcher
from fortigate_auth import FortiGateSession
from config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_network_map():
    """Fetches device data and generates the network map."""
    fg_config = config.local_fortigate

    with FortiGateSession(fg_config) as session:
        session.host = fg_config.host # Add host to session for use in FortiGateModule
        fortigate_module = FortiGateModule(session)
        device_matcher = DeviceModelMatcher()

        nodes = []
        edges = []

        # 1. Add the FortiGate itself
        nodes.append({
            "id": "Local-FortiGate",
            "label": "Local-FortiGate",
            "type": "FortiGate",
            "icon": "realistic_device_svgs/FortiGate.svg",
            "model": "realistic_3d_models/models/FortiGate.obj" # Placeholder
        })

        # 2. Fetch FortiSwitch devices
        fortiswitches = fortigate_module.get_fortiswitches().get("results", [])
        for fs in fortiswitches:
            nodes.append({
                "id": fs["switch-id"],
                "label": fs["switch-id"],
                "type": "FortiSwitch",
                "icon": "realistic_device_svgs/FortiSwitch.svg",
                "model": "realistic_3d_models/models/FortiSwitch.obj" # Placeholder
            })
            edges.append({"from": "Local-FortiGate", "to": fs["switch-id"]})

        # 3. Fetch FortiAP devices
        fortiaps = fortigate_module.get_fortiaps().get("results", [])
        for fap in fortiaps:
            nodes.append({
                "id": fap["name"],
                "label": fap["name"],
                "type": "FortiAP",
                "icon": "realistic_device_svgs/FortiAP.svg",
                "model": "realistic_3d_models/models/FortiAP.obj" # Placeholder
            })
            if fortiswitches:
                edges.append({"from": fortiswitches[0]["switch-id"], "to": fap["name"]})

        # 4. Fetch connected clients
        clients = fortigate_module.get_connected_clients().get("results", [])
        for client in clients:
            device_info = device_matcher.match_mac_to_model(client["mac"], {"hostname": client.get("hostname", client["mac"])})
            client_id = client.get("hostname", client["mac"])
            nodes.append({
                "id": client_id,
                "label": client_id,
                "type": device_info.device_type,
                "icon": f"realistic_device_svgs/{device_info.vendor}.svg", # Placeholder
                "model": device_info.model_path
            })
            # Connect clients to the first AP for simplicity
            if fortiaps:
                edges.append({"from": fortiaps[0]["name"], "to": client_id})

        # 3. Fetch FortiAP devices
        fortiaps = fortigate_module.get_fortiaps().get("results", [])
        for fap in fortiaps:
            nodes.append({
                "id": fap["name"],
                "label": fap["name"],
                "type": "FortiAP",
                "icon": "realistic_device_svgs/FortiAP.svg",
                "model": "realistic_3d_models/models/FortiAP.obj" # Placeholder
            })
            if fortiswitches:
                edges.append({"from": fortiswitches[0]["switch-id"], "to": fap["name"]})

        # 4. Fetch connected clients
        clients = fortigate_module.get_connected_clients().get("results", [])
        for client in clients:
            device_info = device_matcher.match_mac_to_model(client["mac"], {"hostname": client.get("hostname", client["mac"])})
            client_id = client.get("hostname", client["mac"])
            nodes.append({
                "id": client_id,
                "label": client_id,
                "type": device_info.device_type,
                "icon": f"realistic_device_svgs/{device_info.vendor}.svg", # Placeholder
                "model": device_info.model_path
            })
            # Connect clients to the first AP for simplicity
            if fortiaps:
                edges.append({"from": fortiaps[0]["name"], "to": client_id})

        # 5. Create the network map data structure
        network_map = {
            "nodes": nodes,
            "edges": edges
        }

        # 6. Save to a file
        output_path = Path("network_map.json")
        output_path.write_text(json.dumps(network_map, indent=2))
        logger.info(f"Network map data saved to {output_path}")

if __name__ == "__main__":
    generate_network_map()
