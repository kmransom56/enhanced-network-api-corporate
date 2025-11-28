
import json
import time
import random
import string
from typing import Any, Dict, List, Optional
from collections import defaultdict

# Mocking necessary imports/globals
logger = None

def _normalize_scene_compute(data: Dict[str, Any]) -> Dict[str, Any]:
    devices = []
    for key in ("devices", "nodes"):
        value = data.get(key)
        if isinstance(value, list):
            devices = value
            break

    nodes: List[Dict[str, Any]] = []
    for device in devices:
        if not isinstance(device, dict):
            continue
        node_id = device.get("id") or device.get("name")
        if not node_id:
            continue
        node_type = device.get("type") or device.get("role") or "device"
        node = {"id": node_id, "name": device.get("name") or node_id, "type": node_type}
        for key in (
            "hostname",
            "role",
            "ip",
            "model",
            "serial",
            "status",
            "position",
            "mac",
            "firmware",
            "os",
            "ssid",
            "connection_type",
        ):
            value = device.get(key)
            if value is not None:
                node[key] = value
        nodes.append(node)

    links_source = data.get("links") or data.get("edges") or []
    normalized_links: List[Dict[str, Any]] = []
    if isinstance(links_source, list):
        for link in links_source:
            if not isinstance(link, dict):
                continue
            source = link.get("from") or link.get("source") or link.get("source_id")
            target = link.get("to") or link.get("target") or link.get("target_id")
            if not (source and target):
                continue
            normalized = {"from": source, "to": target}
            for key in ("type", "status", "description"):
                value = link.get(key)
                if value is not None:
                    normalized[key] = value
            ports = link.get("ports") or link.get("interfaces")
            if ports:
                normalized["ports"] = ports
            normalized_links.append(normalized)

    return {"nodes": nodes, "links": normalized_links}

def _scene_to_lab_format(scene: Dict[str, Any]) -> Dict[str, Any]:
    nodes = scene.get("nodes") or []
    links = scene.get("links") or []

    models: List[Dict[str, Any]] = []
    for idx, node in enumerate(nodes):
        node_id = node.get("id") or f"node-{idx}"

        pos = node.get("position") or {}
        x = pos.get("x")
        y = pos.get("y")
        z = pos.get("z")
        if x is None or y is None or z is None:
            x = (idx % 5) * 4 - 8
            y = 2
            z = (idx // 5) * 4 - 8

        device_type = (
            node.get("device_type")
            or node.get("type")
            or node.get("role")
            or "endpoint"
        )

        model_entry: Dict[str, Any] = {
            "id": node_id,
            "name": node.get("name") or node.get("hostname") or node_id,
            "type": device_type,
            "model": node.get("device_model") or node.get("model"),
            "position": {"x": x, "y": y, "z": z},
            "status": node.get("status", "online"),
            "ip": node.get("ip"),
            "mac": node.get("mac"),
            "serial": node.get("serial"),
        }

        if "cpu" in node:
            model_entry["cpu_usage"] = node.get("cpu")
        if "memory" in node:
            model_entry["memory_usage"] = node.get("memory")
        if "throughput" in node:
            model_entry["throughput"] = node.get("throughput")

        if "device_vendor" in node:
            model_entry["vendor"] = node.get("device_vendor")
        if "pos_system" in node:
            model_entry["pos_system"] = node.get("pos_system")
        if "vlan" in node:
            model_entry["vlan"] = node.get("vlan")
        if "icon_svg" in node:
            model_entry["icon_svg"] = node.get("icon_svg")

        models.append(model_entry)

    connections: List[Dict[str, Any]] = []
    for link in links:
        src = link.get("from") or link.get("source")
        dst = link.get("to") or link.get("target")
        if not src or not dst:
            continue

        conn: Dict[str, Any] = {
            "from": src,
            "to": dst,
            "status": link.get("status", "active"),
        }

        if "protocol" in link:
            conn["protocol"] = link.get("protocol")
        if "bandwidth" in link:
            conn["bandwidth"] = link.get("bandwidth")
        if "vlan" in link:
            conn["vlan"] = link.get("vlan")
        if "poe" in link:
            conn["poe"] = link.get("poe")

        connections.append(conn)

    return {"models": models, "connections": connections}

def generate_data(num_devices=1000, num_links=2000):
    devices = []
    for i in range(num_devices):
        devices.append({
            "id": f"device-{i}",
            "name": f"Device {i}",
            "type": random.choice(["fortigate", "switch", "ap", "endpoint"]),
            "ip": f"192.168.1.{i % 255}",
            "status": "online",
            "cpu": random.randint(0, 100),
            "memory": random.randint(0, 100),
        })
    
    links = []
    for i in range(num_links):
        links.append({
            "source": f"device-{random.randint(0, num_devices-1)}",
            "target": f"device-{random.randint(0, num_devices-1)}",
            "type": "ethernet",
            "status": "active"
        })
    
    return {"devices": devices, "links": links}

def benchmark():
    data = generate_data(num_devices=5000, num_links=10000)
    
    print(f"Benchmarking with {len(data['devices'])} devices and {len(data['links'])} links...")

    # Benchmark _normalize_scene_compute
    start = time.time()
    normalized = _normalize_scene_compute(data)
    end = time.time()
    print(f"_normalize_scene_compute: {end - start:.4f} seconds")

    # Benchmark _scene_to_lab_format
    start = time.time()
    _scene_to_lab_format(normalized)
    end = time.time()
    print(f"_scene_to_lab_format: {end - start:.4f} seconds")

    # Benchmark JSON serialization
    start = time.time()
    json_str = json.dumps(normalized)
    end = time.time()
    print(f"json.dumps: {end - start:.4f} seconds")

    start = time.time()
    json.loads(json_str)
    end = time.time()
    print(f"json.loads: {end - start:.4f} seconds")

    try:
        import orjson
        start = time.time()
        orjson_bytes = orjson.dumps(normalized)
        end = time.time()
        print(f"orjson.dumps: {end - start:.4f} seconds")

        start = time.time()
        orjson.loads(orjson_bytes)
        end = time.time()
        print(f"orjson.loads: {end - start:.4f} seconds")
    except ImportError:
        print("orjson not installed")

if __name__ == "__main__":
    benchmark()
