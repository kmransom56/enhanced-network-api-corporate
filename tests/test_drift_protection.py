#!/usr/bin/env python3
"""
Drift Protection Test Suite
Prevents regression and configuration drift
"""

import asyncio
import aiohttp
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any

class DriftProtectionTests:
    """Automated tests to prevent configuration drift"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:11111"
        self.test_results = []
        
    async def run_all_tests(self) -> bool:
        """Run all drift protection tests"""
        print("🛡️  Running drift protection tests...")
        
        tests = [
            self._test_api_endpoints,
            self._test_static_pages,
            self._test_mcp_integration,
            self._test_topology_data,
            self._test_javascript_integrity
        ]
        
        all_passed = True
        for test in tests:
            try:
                result = await test()
                self.test_results.append(result)
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ Test failed: {e}")
                all_passed = False
        
        return all_passed
    
    async def _test_api_endpoints(self) -> bool:
        """Test critical API endpoints"""
        endpoints = [
            "/api/topology/scene",
            "/health",
            "/"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status != 200:
                            print(f"❌ Endpoint {endpoint} returned {response.status}")
                            return False
                except Exception as e:
                    print(f"❌ Endpoint {endpoint} failed: {e}")
                    return False
        
        print("✅ API endpoints OK")
        return True
    
    async def _test_static_pages(self) -> bool:
        """Test static HTML pages"""
        pages = [
            "/",
            "/2d-topology-enhanced",
            "/babylon-test"
        ]
        
        async with aiohttp.ClientSession() as session:
            for page in pages:
                try:
                    async with session.get(f"{self.base_url}{page}") as response:
                        content = await response.text()
                        
                        # Check for critical elements
                        if page == "/" and "loadFortinetTopology" not in content:
                            print(f"❌ Main page missing critical functions")
                            return False
                        elif page == "/2d-topology-enhanced" and "Enhanced2DTopology" not in content:
                            print(f"❌ 2D page missing critical functions")
                            return False
                            
                except Exception as e:
                    print(f"❌ Page {page} failed: {e}")
                    return False
        
        print("✅ Static pages OK")
        return True
    
    async def _test_mcp_integration(self) -> bool:
        """Test MCP-style integration.

        Primary check: FortiOS-backed DrawIO endpoint (/mcp/generate_drawio_diagram).
        Secondary check: legacy Fortinet MCP bridge (/mcp/discover_fortinet_topology) is
        treated as *optional* and will only emit a warning if it fails.
        """

        async with aiohttp.ClientSession() as session:
            # Primary: DrawIO generation using live FortiGate topology
            try:
                async with session.post(
                    f"{self.base_url}/mcp/generate_drawio_diagram",
                    json={"layout": "hierarchical"},
                ) as response:
                    if response.status != 200:
                        print(f"❌ DrawIO MCP endpoint returned {response.status}")
                        return False

                    data = await response.json()
                    if not isinstance(data, dict) or "content" not in data:
                        print("❌ DrawIO MCP response format invalid")
                        return False

                    xml_text = data.get("content", [{}])[0].get("text", "")
                    if not xml_text.startswith("<?xml"):
                        print("❌ DrawIO MCP did not return XML")
                        return False

            except Exception as e:
                print(f"❌ DrawIO MCP integration failed: {e}")
                return False

            # Secondary: legacy MCP bridge via /mcp/discover_fortinet_topology
            # This is best-effort only and will *not* fail drift protection.
            mcp_data = {
                "device_ip": "192.168.0.254",
                "username": "admin",
                "include_performance": False,
            }

            try:
                async with session.post(
                    f"{self.base_url}/mcp/discover_fortinet_topology",
                    json=mcp_data,
                ) as response:
                    if response.status != 200:
                        print(f"⚠️  Legacy MCP bridge returned {response.status} (non-fatal)")
                    else:
                        data = await response.json()
                        if not isinstance(data, dict) or "content" not in data:
                            print("⚠️  Legacy MCP bridge response format invalid (non-fatal)")
            except Exception as e:
                print(f"⚠️  Legacy MCP bridge check failed (non-fatal): {e}")

        print("✅ MCP integration OK (FortiOS-backed DrawIO primary)")
        return True
    
    async def _test_topology_data(self) -> bool:
        """Test topology data structure"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/api/topology/scene") as response:
                    data = await response.json()
                    
                    # Validate structure
                    if not isinstance(data, dict):
                        print("❌ Topology data not a dict")
                        return False
                    
                    if "nodes" not in data or "links" not in data:
                        print("❌ Topology missing nodes/links")
                        return False
                    
                    if not isinstance(data["nodes"], list) or len(data["nodes"]) == 0:
                        print("❌ Topology nodes invalid")
                        return False
                    
                    # Check first node structure
                    node = data["nodes"][0]
                    required_fields = ["id", "name", "type", "status"]
                    for field in required_fields:
                        if field not in node:
                            print(f"❌ Node missing field: {field}")
                            return False

                    # Drift guard: assert presence of critical FortiGate nodes
                    # If any of these disappear from discovery, fail the drift test.
                    critical_ids = {
                        "fg-192.168.0.254",  # FortiGate
                        "fs-10.255.1.2",     # FortiSwitch
                        "ap-192.168.1.3",    # Primary FortiAP
                    }

                    present_ids = {n.get("id") for n in data["nodes"] if n.get("id")}
                    missing = [cid for cid in critical_ids if cid not in present_ids]
                    if missing:
                        print(f"❌ Critical topology nodes missing: {', '.join(missing)}")
                        return False
                
            except Exception as e:
                print(f"❌ Topology data test failed: {e}")
                return False
        
        print("✅ Topology data OK")
        return True
    
    async def _test_javascript_integrity(self) -> bool:
        """Test JavaScript file integrity"""
        critical_functions = [
            "loadFortinetTopology",
            "renderTopology", 
            "convertMCPToTopologyFormat",
            "addEventListener"
        ]
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/") as response:
                    content = await response.text()
                    
                    for func in critical_functions:
                        if func not in content:
                            print(f"❌ Missing JavaScript function: {func}")
                            return False
                    
            except Exception as e:
                print(f"❌ JavaScript integrity test failed: {e}")
                return False
        
        print("✅ JavaScript integrity OK")
        return True

async def main():
    """Run drift protection tests"""
    tests = DriftProtectionTests()
    
    if await tests.run_all_tests():
        print("\n🎉 All drift protection tests passed!")
        return True
    else:
        print("\n❌ Drift protection tests failed!")
        print("Configuration drift detected - review test results.")
        return False

if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
