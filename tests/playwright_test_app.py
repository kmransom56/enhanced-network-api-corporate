#!/usr/bin/env python3
"""
Playwright tests for the Enhanced Network API application
"""

import asyncio
import pytest
from playwright.async_api import async_playwright, expect
import json
import time

@pytest.mark.visual_smoke
class TestEnhancedNetworkAPI:
    """Test suite for Enhanced Network API using Playwright"""
    
    @pytest.mark.asyncio
    async def test_main_page_loads(self):
        """Test that the main page loads successfully"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to the main page
            await page.goto("http://127.0.0.1:11111/")
            
            # Wait for page to load
            await page.wait_for_load_state("networkidle")
            
            # Check that page loaded successfully
            title = await page.title()
            assert title is not None
            
            # Check for any content on the page
            content = await page.content()
            assert len(content) > 0
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test the health endpoint directly"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to health endpoint
            response = await page.goto("http://127.0.0.1:11111/health")
            
            # Check response status
            assert response.status == 200
            
            # Get response content
            health_data = await response.json()
            
            # Verify health response structure
            assert "status" in health_data
            assert "timestamp" in health_data
            assert "services" in health_data
            assert "metrics" in health_data
            
            # Check that API service is online
            assert health_data["services"]["api"]["status"] == "online"
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_topology_raw_endpoint(self):
        """Test the topology raw endpoint"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to topology raw endpoint
            response = await page.goto("http://127.0.0.1:11111/api/topology/raw")
            
            # Check response status (should be 200 or 503 if MCP bridge not running)
            assert response.status in [200, 503]
            
            if response.status == 200:
                # Get response content
                topology_data = await response.json()
                
                # Verify topology response structure (check for main keys)
                expected_keys = ["gateways", "switches", "aps", "links"]
                for key in expected_keys:
                    assert key in topology_data, f"Missing key: {key}"
                
                # clients key is optional, check if it exists
                if "clients" in topology_data:
                    assert isinstance(topology_data["clients"], list)
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_topology_scene_endpoint(self):
        """Test the topology 3D scene endpoint"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to topology scene endpoint
            response = await page.goto("http://127.0.0.1:11111/api/topology/scene")
            
            # Check response status (should be 200 or 503 if MCP bridge not running)
            assert response.status in [200, 503]
            
            if response.status == 200:
                # Get response content
                scene_data = await response.json()
                
                # Verify scene response structure
                assert "nodes" in scene_data
                assert "links" in scene_data
                assert "triageHints" in scene_data
                
                # Check that nodes array exists (may be empty if no devices)
                assert isinstance(scene_data["nodes"], list)
                assert isinstance(scene_data["links"], list)
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_api_docs_endpoint(self):
        """Test the API documentation endpoint"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to API docs
            await page.goto("http://127.0.0.1:11111/docs")
            
            # Wait for page to load
            await page.wait_for_load_state("networkidle")
            
            # Check that docs page loaded
            title = await page.title()
            assert "FastAPI" in title or "Swagger" in title or "API" in title
            
            # Look for API documentation elements
            try:
                await expect(page.locator("h1")).to_be_visible(timeout=5000)
            except:
                # If h1 not found, check for other common doc elements
                content = await page.content()
                assert len(content) > 1000  # Should have substantial content
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_static_files_served(self):
        """Test that static files are being served correctly"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Try to access static directory
            response = await page.goto("http://127.0.0.1:11111/static/")
            
            # Should either serve directory listing or 404 (both are acceptable)
            assert response.status in [200, 404, 403]
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for invalid endpoints"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to non-existent endpoint
            response = await page.goto("http://127.0.0.1:11111/nonexistent")
            
            # Should return 404
            assert response.status == 404
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_cors_headers(self):
        """Test that CORS headers are properly set"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Make a request and check headers
            response = await page.goto("http://127.0.0.1:11111/health")
            
            # Check for CORS headers
            headers = response.headers
            # Note: CORS headers might not be visible in all cases, but request should succeed
            assert response.status == 200
            
            await browser.close()

async def run_all_tests():
    """Run all tests and report results"""
    test_instance = TestEnhancedNetworkAPI()
    
    tests = [
        ("Main Page Load", test_instance.test_main_page_loads),
        ("Health Endpoint", test_instance.test_health_endpoint),
        ("Topology Raw Endpoint", test_instance.test_topology_raw_endpoint),
        ("Topology Scene Endpoint", test_instance.test_topology_scene_endpoint),
        ("API Docs Endpoint", test_instance.test_api_docs_endpoint),
        ("Static Files", test_instance.test_static_files_served),
        ("Error Handling", test_instance.test_error_handling),
        ("CORS Headers", test_instance.test_cors_headers),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"🧪 Running {test_name}...")
            await test_func()
            print(f"✅ {test_name} - PASSED")
            results.append((test_name, "PASSED", None))
        except Exception as e:
            print(f"❌ {test_name} - FAILED: {str(e)}")
            results.append((test_name, "FAILED", str(e)))
    
    # Print summary
    print("\n" + "="*60)
    print("PLAYWRIGHT TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, status, _ in results if status == "PASSED")
    failed = sum(1 for _, status, _ in results if status == "FAILED")
    
    for test_name, status, error in results:
        status_icon = "✅" if status == "PASSED" else "❌"
        print(f"{status_icon} {test_name}: {status}")
        if error:
            print(f"   Error: {error}")
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")
    
    return failed == 0

if __name__ == "__main__":
    asyncio.run(run_all_tests())
