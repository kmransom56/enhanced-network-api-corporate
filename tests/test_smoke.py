"""
Smoke tests for Enhanced Network API CI/CD pipeline
"""

import pytest
import requests
import time
from typing import Dict, Any


@pytest.mark.smoke
class TestSmokeTests:
    """Critical smoke tests for CI/CD pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup smoke test environment."""
        self.base_url = "http://127.0.0.1:11111"
        self.timeout = 30
    
    def test_main_page_loads(self):
        """Test that main page loads successfully."""
        try:
            response = requests.get(f"{self.base_url}/", timeout=self.timeout)
            assert response.status_code == 200
            content_lower = response.text.lower()
            assert "fortinet" in content_lower or "topology" in content_lower
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Main page failed to load: {e}")
    
    def test_api_docs_accessible(self):
        """Test that API documentation is accessible."""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=self.timeout)
            assert response.status_code == 200
            body = response.text
            assert "Swagger UI" in body or "swagger-ui" in body.lower()
            assert "openapi.json" in body
        except requests.exceptions.RequestException as e:
            pytest.fail(f"API docs not accessible: {e}")
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert data["status"] in ["healthy", "degraded", "unhealthy"]
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Health endpoint not accessible: {e}")
    
    def test_topology_raw_endpoint_responds(self):
        """Test that raw topology endpoint responds (even with errors)."""
        try:
            response = requests.get(f"{self.base_url}/api/topology/raw", timeout=self.timeout)
            
            # Should respond with either success or error, but not timeout
            assert response.status_code in [200, 500, 502, 503]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                # Should have expected structure even if empty
                assert "devices" in data
                assert "links" in data
            else:
                # Error responses should have error information
                data = response.json()
                assert "error" in data or "detail" in data
        except requests.exceptions.Timeout:
            pytest.fail("Topology raw endpoint timed out")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Topology raw endpoint not accessible: {e}")
    
    def test_topology_scene_endpoint_responds(self):
        """Test that 3D scene topology endpoint responds."""
        try:
            response = requests.get(f"{self.base_url}/api/topology/scene", timeout=self.timeout)
            
            # Should respond with either success or error, but not timeout
            assert response.status_code in [200, 500, 502, 503]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                # Should have expected 3D scene structure
                assert "nodes" in data
                assert "links" in data
                if "triageHints" in data:
                    assert isinstance(data["triageHints"], list)
            else:
                # Error responses should have error information
                data = response.json()
                assert "error" in data or "detail" in data
        except requests.exceptions.Timeout:
            pytest.fail("Topology scene endpoint timed out")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Topology scene endpoint not accessible: {e}")
    
    def test_static_files_served(self):
        """Test that static files are served correctly."""
        static_files = [
            "/static/app.js",
            "/static/noc-styles.css",
            "/static/fortinet-icons/FortiGate.svg"
        ]
        
        for file_path in static_files:
            try:
                response = requests.get(f"{self.base_url}{file_path}", timeout=self.timeout)
                # Some static files might not exist, but should return 404, not timeout
                assert response.status_code in [200, 404]
            except requests.exceptions.Timeout:
                pytest.fail(f"Static file {file_path} timed out")
            except requests.exceptions.RequestException as e:
                pytest.fail(f"Static file {file_path} not accessible: {e}")
    
    def test_mcp_bridge_connectivity(self):
        """Test MCP bridge connectivity."""
        try:
            # Test MCP bridge directly
            bridge_url = "http://127.0.0.1:9001/mcp/call-tool"
            payload = {"name": "discover_fortinet_topology", "arguments": {}}
            
            response = requests.post(bridge_url, json=payload, timeout=10)
            
            # Should respond with either success or error, but not timeout
            assert response.status_code in [200, 502, 503]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                assert "content" in data or "isError" in data
        except requests.exceptions.Timeout:
            pytest.fail("MCP bridge connection timed out")
        except requests.exceptions.ConnectionError:
            # MCP bridge might be down, which is acceptable for smoke tests
            pytest.skip("MCP bridge not running")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"MCP bridge not accessible: {e}")
    
    def test_critical_response_times(self):
        """Test that critical endpoints respond within acceptable time."""
        endpoints = [
            ("/", "Main page"),
            ("/api/topology/raw", "Raw topology"),
            ("/api/topology/scene", "3D scene")
        ]
        
        for endpoint, name in endpoints:
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                response_time = (time.time() - start_time) * 1000
                
                # Critical endpoints should respond within 10 seconds
                assert response_time < 10000, f"{name} took {response_time:.0f}ms (limit: 10000ms)"
                assert response.status_code in [200, 500, 502, 503]
                
                print(f"✅ {name}: {response_time:.0f}ms")
                
            except requests.exceptions.Timeout:
                pytest.fail(f"{name} timed out")
            except requests.exceptions.RequestException as e:
                pytest.fail(f"{name} not accessible: {e}")
    
    def test_error_handling_graceful(self):
        """Test that errors are handled gracefully."""
        # Test invalid endpoint
        try:
            response = requests.get(f"{self.base_url}/api/invalid-endpoint", timeout=self.timeout)
            assert response.status_code == 404
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Invalid endpoint test failed: {e}")
        
        # Test invalid method
        try:
            response = requests.delete(f"{self.base_url}/api/topology/raw", timeout=self.timeout)
            assert response.status_code in [405, 404]
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Invalid method test failed: {e}")
    
    def test_concurrent_requests_handling(self):
        """Test that the application handles concurrent requests."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = requests.get(f"{self.base_url}/", timeout=10)
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")
        
        # Make 5 concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        error_count = 0
        
        while not results.empty():
            result = results.get()
            if result == 200:
                success_count += 1
            else:
                error_count += 1
        
        # At least 3 out of 5 requests should succeed
        assert success_count >= 3, f"Too many failures: {error_count}/5"
        print(f"✅ Concurrent requests: {success_count}/5 successful")


@pytest.mark.smoke
@pytest.mark.integration
class TestSmokeIntegration:
    """Integration smoke tests."""
    
    def test_end_to_end_topology_flow(self):
        """Test complete topology discovery flow."""
        base_url = "http://127.0.0.1:11111"
        timeout = 30
        
        try:
            # Step 1: Get raw topology
            response = requests.get(f"{base_url}/api/topology/raw", timeout=timeout)
            assert response.status_code in [200, 500, 502, 503]
            
            if response.status_code == 200:
                raw_data = response.json()
                assert isinstance(raw_data, dict)
                
                # Step 2: Get 3D scene
                response = requests.get(f"{base_url}/api/topology/scene", timeout=timeout)
                assert response.status_code in [200, 500, 502, 503]
                
                if response.status_code == 200:
                    scene_data = response.json()
                    assert isinstance(scene_data, dict)
                    assert "nodes" in scene_data
                    assert "links" in scene_data
                    
                    print(f"✅ End-to-end flow successful: {len(scene_data['nodes'])} nodes")
                else:
                    print("⚠️ 3D scene failed, but raw topology succeeded")
            else:
                print("⚠️ Topology endpoints not healthy, but application is running")
                
        except requests.exceptions.RequestException as e:
            pytest.fail(f"End-to-end flow failed: {e}")
    
    def test_mcp_to_api_integration(self):
        """Test MCP bridge to API integration."""
        try:
            # Test MCP bridge
            bridge_url = "http://127.0.0.1:9001/mcp/call-tool"
            payload = {"name": "discover_fortinet_topology", "arguments": {}}
            
            response = requests.post(bridge_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                # Test API endpoint
                api_response = requests.get("http://127.0.0.1:11111/api/topology/raw", timeout=10)
                
                # Both should be accessible
                assert api_response.status_code in [200, 500, 502, 503]
                print("✅ MCP to API integration working")
            else:
                pytest.skip("MCP bridge not available for integration test")
                
        except requests.exceptions.ConnectionError:
            pytest.skip("MCP bridge not running")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"MCP to API integration failed: {e}")


@pytest.mark.smoke
@pytest.mark.self_healing
class TestSmokeSelfHealing:
    """Self-healing smoke tests."""
    
    def test_basic_error_recovery(self):
        """Test basic error recovery mechanisms."""
        base_url = "http://127.0.0.1:11111"
        
        try:
            # Test that application recovers from invalid requests
            for _ in range(3):
                response = requests.get(f"{base_url}/api/invalid", timeout=10)
                assert response.status_code == 404
            
            # Application should still be responsive
            response = requests.get(f"{base_url}/", timeout=10)
            assert response.status_code == 200
            
            print("✅ Basic error recovery working")
            
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Error recovery test failed: {e}")
    
    def test_timeout_handling(self):
        """Test timeout handling."""
        base_url = "http://127.0.0.1:11111"
        
        try:
            # Test with very short timeout to verify timeout handling
            response = requests.get(f"{base_url}/api/topology/raw", timeout=1)
            # Should either succeed quickly or timeout gracefully
            assert response.status_code in [200, 500, 502, 503] or response.elapsed.total_seconds() < 2
            
        except requests.exceptions.Timeout:
            # Timeout is acceptable
            print("✅ Timeout handling working")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Timeout handling test failed: {e}")
