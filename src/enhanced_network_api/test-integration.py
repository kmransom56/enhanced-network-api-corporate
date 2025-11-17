#!/usr/bin/env python3
"""
Integration Test Suite for AI Research Platform + cagent
Tests all components of the integration
"""

import json
import time
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Tuple


class IntegrationTester:
    """Test suite for platform integration"""
    
    def __init__(self):
        self.mcp_url = "http://127.0.0.1:9000"
        self.registry_path = Path("platform_discovery/platform_map.json")
        self.results: List[Tuple[str, bool, str]] = []
    
    def log(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append((test_name, passed, message))
        print(f"{status} - {test_name}")
        if message:
            print(f"       {message}")
    
    def test_discovery_output(self) -> bool:
        """Test 1: Service discovery created registry"""
        print("\n📋 Test 1: Service Discovery Output")
        
        if not self.registry_path.exists():
            self.log("Registry File Exists", False, f"File not found: {self.registry_path}")
            return False
        
        self.log("Registry File Exists", True)
        
        try:
            with open(self.registry_path) as f:
                platform_map = json.load(f)
            
            services = platform_map.get('service_mapping', {})
            categories = platform_map.get('categories', {})
            
            if not services:
                self.log("Services Discovered", False, "No services in registry")
                return False
            
            self.log("Services Discovered", True, f"Found {len(services)} services")
            
            if not categories:
                self.log("Services Categorized", False, "No categories found")
                return False
            
            total_categorized = sum(len(items) for items in categories.values())
            self.log("Services Categorized", True, f"{total_categorized} services categorized")
            
            return True
            
        except json.JSONDecodeError as e:
            self.log("Registry Valid JSON", False, str(e))
            return False
        except Exception as e:
            self.log("Registry Readable", False, str(e))
            return False
    
    def test_mcp_server(self) -> bool:
        """Test 2: MCP server is running and responding"""
        print("\n🚀 Test 2: MCP Server Status")
        
        try:
            # Health check
            response = requests.get(f"{self.mcp_url}/health", timeout=5)
            
            if response.status_code != 200:
                self.log("MCP Server Health", False, f"Status code: {response.status_code}")
                return False
            
            self.log("MCP Server Health", True)
            
            health_data = response.json()
            services_loaded = health_data.get('services_loaded', 0)
            
            if services_loaded == 0:
                self.log("Services Loaded", False, "No services loaded by MCP server")
                return False
            
            self.log("Services Loaded", True, f"{services_loaded} services loaded")
            
            return True
            
        except requests.RequestException as e:
            self.log("MCP Server Running", False, f"Cannot connect: {e}")
            print("\n💡 Hint: Start MCP server with:")
            print("   python3 ai-platform-mcp-server.py --port 9000")
            return False
    
    def test_mcp_tools(self) -> bool:
        """Test 3: MCP tools endpoint"""
        print("\n🔧 Test 3: MCP Tools")
        
        try:
            response = requests.get(f"{self.mcp_url}/mcp/tools", timeout=5)
            
            if response.status_code != 200:
                self.log("Tools Endpoint", False, f"Status code: {response.status_code}")
                return False
            
            self.log("Tools Endpoint", True)
            
            tools_data = response.json()
            tools = tools_data.get('tools', [])
            
            if not tools:
                self.log("Tools Available", False, "No tools registered")
                return False
            
            self.log("Tools Available", True, f"{len(tools)} tools registered")
            
            # Check expected tools
            expected_tools = [
                'platform_health_check',
                'list_services',
                'get_service_info',
                'query_service',
                'batch_query_services'
            ]
            
            tool_names = [tool['name'] for tool in tools]
            
            for expected in expected_tools:
                if expected in tool_names:
                    self.log(f"Tool: {expected}", True)
                else:
                    self.log(f"Tool: {expected}", False, "Not found")
            
            return True
            
        except Exception as e:
            self.log("Tools Endpoint", False, str(e))
            return False
    
    def test_tool_execution(self) -> bool:
        """Test 4: Execute MCP tools"""
        print("\n⚙️  Test 4: Tool Execution")
        
        try:
            # Test platform_health_check
            response = requests.post(
                f"{self.mcp_url}/mcp/call-tool",
                json={
                    "name": "platform_health_check",
                    "arguments": {}
                },
                timeout=30
            )
            
            if response.status_code != 200:
                self.log("platform_health_check", False, f"Status: {response.status_code}")
            else:
                result = response.json()
                if result.get('isError'):
                    self.log("platform_health_check", False, "Tool returned error")
                else:
                    self.log("platform_health_check", True)
            
            # Test list_services
            response = requests.post(
                f"{self.mcp_url}/mcp/call-tool",
                json={
                    "name": "list_services",
                    "arguments": {}
                },
                timeout=10
            )
            
            if response.status_code != 200:
                self.log("list_services", False, f"Status: {response.status_code}")
            else:
                result = response.json()
                if result.get('isError'):
                    self.log("list_services", False, "Tool returned error")
                else:
                    self.log("list_services", True)
                    content = json.loads(result['content'][0]['text'])
                    total = content.get('total_services', 0)
                    print(f"       Found {total} total services")
            
            return True
            
        except Exception as e:
            self.log("Tool Execution", False, str(e))
            return False
    
    def test_cagent_config(self) -> bool:
        """Test 5: cagent configuration files"""
        print("\n📝 Test 5: cagent Configuration")
        
        config_file = Path("ai-platform-integrated.yaml")
        
        if not config_file.exists():
            self.log("Config File Exists", False, str(config_file))
            print("\n💡 Hint: Generate config with:")
            print("   python3 ai-platform-tools-generator.py")
            return False
        
        self.log("Config File Exists", True)
        
        try:
            with open(config_file) as f:
                content = f.read()
            
            # Check for key components
            checks = [
                ("agents:", "Agents defined"),
                ("models:", "Models defined"),
                ("mcp_servers:", "MCP servers configured"),
                ("ai-research-platform", "Platform MCP referenced")
            ]
            
            for search_term, description in checks:
                if search_term in content:
                    self.log(description, True)
                else:
                    self.log(description, False, f"Missing: {search_term}")
            
            return True
            
        except Exception as e:
            self.log("Config Readable", False, str(e))
            return False
    
    def test_cagent_execution(self) -> bool:
        """Test 6: cagent can execute with config"""
        print("\n🤖 Test 6: cagent Execution")
        
        config_file = "ai-platform-integrated.yaml"
        
        if not Path(config_file).exists():
            self.log("cagent Execution", False, "Config file missing")
            return False
        
        try:
            # Simple test query
            result = subprocess.run(
                ['cagent', 'exec', config_file, 'List available services'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log("cagent Execution", True)
                
                # Check if output contains expected content
                output = result.stdout.lower()
                if 'service' in output or 'port' in output:
                    self.log("cagent Output Valid", True)
                else:
                    self.log("cagent Output Valid", False, "No service data in output")
                
                return True
            else:
                self.log("cagent Execution", False, f"Exit code: {result.returncode}")
                if result.stderr:
                    print(f"       Error: {result.stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("cagent Execution", False, "Timeout (>60s)")
            return False
        except FileNotFoundError:
            self.log("cagent Command", False, "cagent not found in PATH")
            print("\n💡 Hint: Install cagent from https://github.com/docker/cagent")
            return False
        except Exception as e:
            self.log("cagent Execution", False, str(e))
            return False
    
    def test_service_wrappers(self) -> bool:
        """Test 7: Service wrappers generated"""
        print("\n📦 Test 7: Service Wrappers")
        
        wrappers_dir = Path("service_wrappers")
        
        if not wrappers_dir.exists():
            self.log("Wrappers Directory", False, "Not generated")
            print("\n💡 Hint: Generate wrappers with:")
            print("   python3 ai-platform-tools-generator.py --wrappers")
            return False
        
        self.log("Wrappers Directory", True)
        
        wrapper_files = list(wrappers_dir.glob("*_wrapper.py"))
        
        if not wrapper_files:
            self.log("Wrapper Files", False, "No wrappers generated")
            return False
        
        self.log("Wrapper Files", True, f"{len(wrapper_files)} wrappers found")
        
        # Test if wrappers are valid Python
        valid_count = 0
        for wrapper in wrapper_files[:3]:  # Test first 3
            try:
                with open(wrapper) as f:
                    compile(f.read(), str(wrapper), 'exec')
                valid_count += 1
            except SyntaxError:
                pass
        
        if valid_count > 0:
            self.log("Wrapper Syntax Valid", True, f"{valid_count} wrappers validated")
        else:
            self.log("Wrapper Syntax Valid", False)
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for _, p, _ in self.results if p)
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        
        if failed > 0:
            print(f"\n⚠️  Failed Tests:")
            for name, passed, message in self.results:
                if not passed:
                    print(f"   • {name}")
                    if message:
                        print(f"     {message}")
        
        print("\n" + "="*60)
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED! Integration is working perfectly.")
            print("\n🚀 Next Steps:")
            print("   • Run: cagent run ai-platform-integrated.yaml")
            print("   • Try: cagent exec ai-platform-integrated.yaml \"Check platform health\"")
        else:
            print(f"⚠️  {failed} test(s) failed. Review errors above.")
            print("\n🔧 Troubleshooting:")
            print("   • Run: ./setup-integration.sh setup")
            print("   • Check: tail -f mcp-server.log")
            print("   • Verify: docker ps")
        
        return failed == 0


def main():
    """Run all integration tests"""
    print("🧪 AI Research Platform + cagent Integration Tests")
    print("="*60)
    
    tester = IntegrationTester()
    
    # Run all tests
    tests = [
        tester.test_discovery_output,
        tester.test_mcp_server,
        tester.test_mcp_tools,
        tester.test_tool_execution,
        tester.test_cagent_config,
        tester.test_cagent_execution,
        tester.test_service_wrappers
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"\n❌ Test exception: {e}")
    
    # Print summary
    success = tester.print_summary()
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())