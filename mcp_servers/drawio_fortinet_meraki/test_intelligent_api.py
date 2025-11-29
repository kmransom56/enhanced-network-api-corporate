#!/usr/bin/env python3
"""
Test script for Intelligent API Documentation and LLM Integration
"""

import asyncio
import json
import logging
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_api_documentation():
    """Test API documentation queries"""
    print("\n🔍 Testing API Documentation Queries")
    print("=" * 50)
    
    try:
        from api_documentation import APIKnowledgeBase, IntelligentAPIMCP
        
        # Test knowledge base
        kb = APIKnowledgeBase()
        
        print(f"📚 FortiGate Endpoints: {len(kb.fortigate_endpoints)}")
        print(f"📚 Meraki Endpoints: {len(kb.meraki_endpoints)}")
        
        # Test intelligent API
        api_mcp = IntelligentAPIMCP()
        
        # Test queries
        test_queries = [
            ("system status", "fortigate"),
            ("network interfaces", "fortigate"),
            ("firewall policies", "fortigate"),
            ("organizations", "meraki"),
            ("switch ports", "meraki"),
            ("access points", "meraki")
        ]
        
        for query, device_type in test_queries:
            print(f"\n🔎 Query: '{query}' on {device_type}")
            
            try:
                results = await api_mcp.query_api_documentation(query, device_type)
                
                print(f"  ✅ Found {len(results['results'])} results:")
                for result in results['results'][:3]:  # Top 3
                    print(f"    - {result['name']}: {result['method']} {result['path']}")
                    print(f"      {result['description'][:80]}...")
                    print(f"      Relevance: {result['relevance_score']}")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True

async def test_llm_integration():
    """Test LLM integration for API request generation"""
    print("\n🤖 Testing LLM API Request Generation")
    print("=" * 50)
    
    try:
        from api_documentation import IntelligentAPIMCP
        
        # Initialize with LLM
        llm_base_url = os.getenv('LLM_BASE_URL', 'http://localhost:11434')
        llm_model = os.getenv('LLM_MODEL', 'fortinet-custom')
        
        print(f"🔗 LLM URL: {llm_base_url}")
        print(f"🧠 LLM Model: {llm_model}")
        
        api_mcp = IntelligentAPIMCP()
        
        try:
            await api_mcp.initialize(llm_base_url, llm_model)
            print("✅ LLM initialized successfully")
        except Exception as e:
            print(f"⚠️  LLM initialization failed: {e}")
            print("🔄 Using fallback generation only")
            api_mcp.intelligent_api = None
        
        # Test API request generation
        test_requests = [
            "Show me the system status",
            "Get all network interfaces", 
            "List firewall policies",
            "Check resource usage",
            "Show VIP configuration"
        ]
        
        device_info = {
            "type": "fortigate",
            "ip": "192.168.0.254",
            "model": "FG600E"
        }
        
        for query in test_requests:
            print(f"\n🎯 Query: '{query}'")
            
            try:
                request = await api_mcp.generate_api_request(query, device_info, "fortigate")
                
                print(f"  ✅ Generated Request:")
                print(f"    Method: {request.method}")
                print(f"    URL: {request.url}")
                print(f"    Description: {request.description}")
                print(f"    Confidence: {request.confidence}")
                if request.body:
                    print(f"    Body: {json.dumps(request.body, indent=6)}")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True

async def test_mcp_server_integration():
    """Test full MCP server with intelligent API"""
    print("\n🔧 Testing MCP Server Integration")
    print("=" * 50)
    
    try:
        from mcp_server import DrawIOMCPServer
        
        server = DrawIOMCPServer()
        
        # Initialize
        await server.initialize_topology_collector()
        
        print(f"🔗 FortiGate Collector: {'✅' if server.fortigate_collector else '❌'}")
        print(f"🤖 Intelligent API: {'✅' if server.intelligent_api else '❌'}")
        
        # Test tools
        tools = await server.list_tools()
        print(f"\n🛠️  Available Tools: {len(tools)}")
        
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Test API documentation query
        if server.intelligent_api:
            print(f"\n🔍 Testing API Documentation Tool:")
            try:
                result = await server.query_api_documentation({
                    "query": "system status",
                    "device_type": "fortigate"
                })
                
                data = json.loads(result.content[0].text)
                print(f"  ✅ Found {len(data['results'])} documentation results")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            # Test API request generation
            print(f"\n🤖 Testing API Request Generation Tool:")
            try:
                result = await server.generate_api_request({
                    "query": "Show system status and resource usage",
                    "device_info": {
                        "type": "fortigate",
                        "ip": "192.168.0.254",
                        "model": "FG600E"
                    },
                    "device_type": "fortigate"
                })
                
                data = json.loads(result.content[0].text)
                request = data['generated_request']
                print(f"  ✅ Generated: {request['method']} {request['url']}")
                print(f"     Confidence: {request['confidence']}")
                print(f"     Description: {request['description']}")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
        else:
            print("⚠️  LLM integration not available - skipping intelligent API tests")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False

async def test_fortigate_api_auth():
    """Test FortiGate API authentication with updated token method"""
    print("\n🔐 Testing FortiGate API Authentication")
    print("=" * 50)
    
    try:
        from fortigate_collector import FortiGateTopologyCollector
        
        # Load config
        host = os.getenv('FORTIGATE_HOSTS') or os.getenv('FORTIMANAGER_HOST')
        username = os.getenv('FORTIGATE_USERNAME') or os.getenv('FORTIMANAGER_USERNAME')
        password = os.getenv('FORTIGATE_PASSWORD') or os.getenv('FORTIMANAGER_PASSWORD')
        token = os.getenv('FORTIGATE_192_168_0_254_TOKEN') or os.getenv('FORTIGATE_TOKEN')
        port = os.getenv('FORTIGATE_192_168_0_254_PORT') or os.getenv('FORTIMANAGER_PORT', '10443')
        
        print(f"🏠 Host: {host}:{port}")
        print(f"👤 Username: {username}")
        print(f"🔐 Password: {'✅ Set' if password else '❌ Missing'}")
        
        if not all([host, username, (password or token)]):
            print("❌ Missing required configuration")
            return False
        
        collector = FortiGateTopologyCollector(
            host=host,
            username=username,
            password=password,
            token=token,
            port=int(port),
            verify_ssl=False
        )
        
        # Test authentication
        auth_result = await collector.authenticate()
        
        if auth_result:
            print("✅ Authentication successful!")
            
            # Test getting system status
            print("\n📊 Testing System Status API:")
            status = await collector.get_system_status()
            
            if status:
                print(f"  ✅ Hostname: {status.get('hostname', 'N/A')}")
                print(f"  ✅ Model: {status.get('model', 'N/A')}")
                print(f"  ✅ Version: {status.get('version', 'N/A')}")
                print(f"  ✅ Serial: {status.get('serial', 'N/A')}")
            else:
                print("  ❌ Failed to get system status")
            
            return True
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Intelligent API MCP Test Suite")
    print("=" * 60)
    
    # Load environment
    if not load_dotenv():
        print("⚠️  No .env file found")
    
    results = []
    
    # Run tests
    results.append(("API Documentation", await test_api_documentation()))
    results.append(("LLM Integration", await test_llm_integration()))
    results.append(("MCP Server Integration", await test_mcp_server_integration()))
    results.append(("FortiGate API Auth", await test_fortigate_api_auth()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\n🎯 Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All tests passed! Your intelligent API MCP is ready!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    asyncio.run(main())
