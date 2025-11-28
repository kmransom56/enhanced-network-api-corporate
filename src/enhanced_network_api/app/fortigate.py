"""
Module for interacting with FortiGate and FortiManager devices.
"""

import requests
import json

class FortiGateManager:
    """
    Manages interactions with FortiGate and FortiManager devices.
    """

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.session_key = None
        self.session = None

    def login(self):
        """
        Logs into FortiManager and retrieves a session key.
        """
        if not self.host or not self.username or not self.password:
            print("Error: FortiManager host, username, or password not configured.")
            return False

        url = f"https://{self.host}/jsonrpc"
        payload = {
            "id": 1,
            "method": "exec",
            "params": [
                {
                    "data": {
                        "user": self.username,
                        "passwd": self.password
                    },
                    "url": "/sys/login/user"
                }
            ]
        }

        try:
            self.session = requests.Session()
            response = self.session.post(url, data=json.dumps(payload), verify=False)
            response.raise_for_status()
            result = response.json()

            if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
                self.session_key = result.get("session")
                print(f"Successfully logged into {self.host}")
                return True
            else:
                print(f"Failed to log in to {self.host}: {result.get('result', [{}])[0].get('status')}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to {self.host}: {e}")
            return False

    def get_connected_devices(self):
        """
        Gets connected devices from FortiManager.
        """
        if not self.session_key:
            print("Error: Not logged into FortiManager.")
            return None

        # This is a placeholder for the actual FortiManager API calls
        # to get connected clients from managed devices.
        # The exact endpoints need to be identified from detailed FortiManager documentation.
        return [{"source": "FortiManager", "device": "placeholder_device", "ip": "192.168.1.100"}]

    def fetch_topology(self):
        """
        Fetch live topology data from FortiGate using fortiosapi.
        """
        if not self.session_key:
            print("Error: Not logged into FortiManager.")
            return None

        # This is a placeholder for the actual FortiManager API calls
        # to get the topology.
        # The exact endpoints need to be identified from detailed FortiManager documentation.
        return {
            "nodes": [
                {
                    "id": "fgt-192-168-0-254",
                    "name": "FortiGate",
                    "type": "fortigate",
                    "ip": "192.168.0.254",
                    "model": "unknown",
                    "status": "active",
                    "role": "firewall",
                }
            ],
            "links": [],
            "source": "fortiosapi",
            "timestamp": "2023-10-27T12:00:00Z",
        }

    def generate_drawio_xml(self, topology_data, layout="hierarchical"):
        """
        Generate DrawIO XML from topology data.
        """
        nodes = topology_data.get("nodes", [])
        links = topology_data.get("links", [])

        if not nodes:
            return "<?xml version=\"1.0\" encoding=\"UTF-8\"?><mxfile><diagram><mxGraphModel><root><mxCell id=\"0\" /><mxCell id=\"1\" parent=\"0\" /><mxCell id=\"2\" value=\"No topology data available\" style=\"text;html=1;\" vertex=\"1\" parent=\"1\"><mxGeometry x=\"400\" y=\"350\" width=\"300\" height=\"60\" as=\"geometry\" /></mxCell></root></mxGraphModel></diagram></mxfile>"

        xml_template = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><mxfile><diagram><mxGraphModel><root><mxCell id=\"0\" /><mxCell id=\"1\" parent=\"0\" />{}</root></mxGraphModel></diagram></mxfile>"
        cells = []
        cell_id = 2

        positions = self._calculate_positions(nodes, layout)

        for node in nodes:
            pos = positions.get(node["id"], {"x": 100, "y": 100})
            style = self._device_style(node)
            label = node.get("name", "Device")
            label += f"\\n{node.get('ip', 'N/A')}\\n{node.get('model', node.get('type', ''))}"

            cell_xml = f"<mxCell id=\"{cell_id}\" value=\"{label}\" style=\"{style}\" vertex=\"1\" parent=\"1\"><mxGeometry x=\"{pos['x']}\" y=\"{pos['y']}\" width=\"120\" height=\"60\" as=\"geometry\" /></mxCell>"
            cells.append(cell_xml)
            node["_cell_id"] = cell_id
            cell_id += 1

        for link in links:
            src_id = link.get("source")
            tgt_id = link.get("target")
            src = next((n for n in nodes if n["id"] == src_id), None)
            tgt = next((n for n in nodes if n["id"] == tgt_id), None)
            if not src or not tgt:
                continue

            style = self._link_style(link)
            cell_xml = f"<mxCell id=\"{cell_id}\" style=\"{style}\" edge=\"1\" parent=\"1\" source=\"{src['_cell_id']}\" target=\"{tgt['_cell_id']}\"><mxGeometry width=\"50\" height=\"50\" relative=\"1\" as=\"geometry\" /></mxCell>"
            cells.append(cell_xml)
            cell_id += 1

        return xml_template.format("".join(cells))

    def _calculate_positions(self, nodes, layout):
        positions = {}
        if layout == "hierarchical":
            layers = {"fortigate": 0, "interface": 1}
            layer_nodes = {}
            for n in nodes:
                layer = layers.get(n.get("type", "interface"), 2)
                layer_nodes.setdefault(layer, []).append(n)
            for layer, items in layer_nodes.items():
                x_start = 100
                y = 100 + layer * 150
                spacing = 220
                for i, n in enumerate(items):
                    positions[n["id"]] = {"x": x_start + i * spacing, "y": y}
        else:
            for i, n in enumerate(nodes):
                positions[n["id"]] = {"x": 100 + (i % 4) * 220, "y": 100 + (i // 4) * 150}
        return positions

    def _device_style(self, node):
        ntype = node.get("type", "interface")
        status = node.get("status", "active")
        base_styles = {
            "fortigate": "shape=cloud;whiteSpace=wrap;html=1;fillColor=#1ba1e2;strokeColor=#006EAF;fontColor=#ffffff;",
            "interface": "shape=rectangle;whiteSpace=wrap;html=1;fillColor=#60a917;strokeColor=#2D7600;fontColor=#ffffff;",
        }
        style = base_styles.get(ntype, base_styles["interface"])
        if status != "active":
            style = style.replace("fillColor=#", "fillColor=#dc3545;")
        return style

    def _link_style(self, link):
        ltype = link.get("type", "internal")
        styles = {"internal": "strokeColor=#6c757d;strokeWidth=2;endArrow=none;startArrow=none;"}
        return styles.get(ltype, styles["internal"])
