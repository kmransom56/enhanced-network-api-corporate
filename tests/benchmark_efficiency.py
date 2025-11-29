
import json
import time
import random
import string
from typing import Any, Dict, List, Optional
from collections import defaultdict

# Mocking necessary imports/globals
logger = None

import sys
from pathlib import Path

# Add src and project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from enhanced_network_api.platform_web_api_fastapi import (
    _normalize_scene_compute,
    _scene_to_lab_format,
)

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
