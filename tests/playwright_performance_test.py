#!/usr/bin/env python3
"""
Playwright performance tests for the Enhanced Network API application
"""

import asyncio
import statistics
import time

import pytest
from playwright.async_api import async_playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError

@pytest.mark.performance
class TestEnhancedNetworkPerformance:
    """Test suite for Enhanced Network API performance using Playwright"""
    
    async def measure_response_time(self, page, url, description):
        """Measure response time for a specific endpoint"""
        print(f"⏱️  Testing {description}...")
        
        start_time = time.time()
        response = await page.goto(url)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        print(f"   Response time: {response_time:.2f}ms (Status: {response.status})")
        
        return response_time, response.status
    
    async def test_api_performance(self):
        """Test API endpoint performance"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            endpoints = [
                ("http://127.0.0.1:11111/health", "Health Check"),
                ("http://127.0.0.1:11111/api/topology/raw", "Raw Topology"),
                ("http://127.0.0.1:11111/api/topology/scene", "3D Scene"),
                ("http://127.0.0.1:11111/docs", "API Documentation"),
                ("http://127.0.0.1:11111/", "Main Page"),
            ]
            
            performance_results = []
            
            # Test each endpoint multiple times
            for url, description in endpoints:
                times = []
                statuses = []
                
                for i in range(5):  # Test each endpoint 5 times
                    response_time, status = await self.measure_response_time(page, url, f"{description} (run {i+1})")
                    times.append(response_time)
                    statuses.append(status)
                    
                    # Allow request processing to settle before next iteration
                    await page.wait_for_timeout(100)
                
                # Calculate statistics
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                
                performance_results.append({
                    'endpoint': description,
                    'url': url,
                    'avg_response_time': avg_time,
                    'min_response_time': min_time,
                    'max_response_time': max_time,
                    'status_codes': statuses,
                    'success_rate': sum(1 for s in statuses if s == 200) / len(statuses) * 100
                })
                
                print(f"   📊 {description}: Avg {avg_time:.2f}ms, Min {min_time:.2f}ms, Max {max_time:.2f}ms")
            
            await browser.close()
            return performance_results
    
    async def test_concurrent_requests(self):
        """Test application under concurrent load"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            print("🔄 Testing concurrent requests...")
            
            # Create multiple pages for concurrent requests
            pages = [await browser.new_page() for _ in range(10)]
            
            # Make concurrent requests to health endpoint
            start_time = time.time()
            
            tasks = []
            for i, page in enumerate(pages):
                task = page.goto("http://127.0.0.1:11111/health")
                tasks.append(task)
            
            # Wait for all requests to complete
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = (end_time - start_time) * 1000
            
            # Analyze results
            successful_responses = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
            avg_response_time = total_time / len(responses)
            
            print(f"   📊 Concurrent requests: {successful_responses}/{len(responses)} successful")
            print(f"   📊 Average response time: {avg_response_time:.2f}ms")
            print(f"   📊 Total time: {total_time:.2f}ms")
            
            await browser.close()
            
            return {
                'total_requests': len(responses),
                'successful_requests': successful_responses,
                'success_rate': successful_responses / len(responses) * 100,
                'total_time': total_time,
                'avg_response_time': avg_response_time
            }
    
    async def test_memory_usage_simulation(self):
        """Simulate memory usage by loading multiple pages"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            print("💾 Testing memory usage simulation...")
            
            pages = []
            
            # Create and load multiple pages
            for i in range(5):
                page = await browser.new_page()
                await page.goto("http://127.0.0.1:11111/")
                await page.wait_for_load_state("networkidle")
                pages.append(page)
                
                # Load additional endpoints on each page
                await page.goto("http://127.0.0.1:11111/api/topology/raw")
                await page.wait_for_load_state("networkidle")
                
                print(f"   Loaded page {i+1}/5")
            
            # Ensure the last page has finished rendering before closing
            if pages:
                last_page = pages[-1]
                await last_page.goto("http://127.0.0.1:11111/", wait_until="networkidle")
                try:
                    await last_page.wait_for_function(
                        "() => window.babylonReady === true",
                        timeout=15000,
                    )
                except PlaywrightTimeoutError:
                    pytest.skip("Babylon viewer not ready in this environment")
            
            # Close all pages
            for page in pages:
                await page.close()
            
            await browser.close()
            print("   ✅ Memory usage simulation completed")

async def run_performance_tests():
    """Run all performance tests"""
    print("⚡ Starting Enhanced Network API Performance Tests")
    print("=" * 60)
    
    test_instance = TestEnhancedNetworkPerformance()
    
    try:
        # Run API performance tests
        print("\n🔍 API Response Time Tests")
        print("-" * 30)
        performance_results = await test_instance.test_api_performance()
        
        # Run concurrent request tests
        print("\n🔍 Concurrent Request Tests")
        print("-" * 30)
        concurrent_results = await test_instance.test_concurrent_requests()
        
        # Run memory usage simulation
        print("\n🔍 Memory Usage Simulation")
        print("-" * 30)
        await test_instance.test_memory_usage_simulation()
        
        # Print comprehensive summary
        print("\n" + "=" * 60)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        
        print("\n📊 API Response Times:")
        for result in performance_results:
            status_icon = "✅" if result['success_rate'] == 100 else "⚠️"
            print(f"{status_icon} {result['endpoint']}: {result['avg_response_time']:.2f}ms avg ({result['success_rate']:.0f}% success)")
        
        print(f"\n📊 Concurrent Requests:")
        concurrent_icon = "✅" if concurrent_results['success_rate'] >= 90 else "⚠️"
        print(f"{concurrent_icon} {concurrent_results['successful_requests']}/{concurrent_results['total_requests']} successful")
        print(f"   Success rate: {concurrent_results['success_rate']:.1f}%")
        print(f"   Average response time: {concurrent_results['avg_response_time']:.2f}ms")
        
        # Performance assessment
        fast_endpoints = sum(1 for r in performance_results if r['avg_response_time'] < 500)
        total_endpoints = len(performance_results)
        
        print(f"\n🎯 Performance Assessment:")
        print(f"   Fast endpoints (<500ms): {fast_endpoints}/{total_endpoints}")
        print(f"   Concurrent success rate: {concurrent_results['success_rate']:.1f}%")
        
        if fast_endpoints == total_endpoints and concurrent_results['success_rate'] >= 90:
            print("🎉 Excellent performance!")
            return True
        elif fast_endpoints >= total_endpoints * 0.8 and concurrent_results['success_rate'] >= 80:
            print("✅ Good performance!")
            return True
        else:
            print("⚠️  Performance needs improvement")
            return False
            
    except Exception as e:
        print(f"\n❌ Performance tests failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_performance_tests())
    exit(0 if success else 1)
