#!/usr/bin/env python3
"""
Application Health Check Script
Tests all critical endpoints and functionality
"""

import asyncio
import httpx
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

@dataclass
class HealthResult:
    endpoint: str
    status: str  # "healthy", "warning", "unhealthy"
    response_time: float
    details: str

class HealthChecker:
    """Comprehensive health checking for the application"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:11111"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def check_all(self) -> List[HealthResult]:
        """Run all health checks"""
        results = []
        
        # 1. Basic health endpoint
        results.append(await self.check_health_endpoint())
        
        # 2. Main application
        results.append(await self.check_main_page())
        
        # 3. API endpoints
        results.append(await self.check_topology_api())
        results.append(await self.check_smart_tools_page())
        
        # 4. Static assets
        results.append(await self.check_static_assets())
        
        # 5. Configuration endpoints
        results.append(await self.check_config_endpoints())
        
        # 6. LLM integration (if configured)
        results.append(await self.check_llm_integration())
        
        return results
    
    async def check_health_endpoint(self) -> HealthResult:
        """Check /health endpoint"""
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    details = f"Status: {data.get('status', 'unknown')}"
                    return HealthResult("/health", "healthy", response_time, details)
                except:
                    return HealthResult("/health", "healthy", response_time, "Response OK")
            else:
                return HealthResult("/health", "unhealthy", response_time, f"HTTP {response.status_code}")
        except Exception as e:
            response_time = time.time() - start_time
            return HealthResult("/health", "unhealthy", response_time, str(e))
    
    async def check_main_page(self) -> HealthResult:
        """Check main page loads"""
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                if "visualization" in response.text.lower() or "network" in response.text.lower():
                    return HealthResult("/", "healthy", response_time, "Main page loads")
                else:
                    return HealthResult("/", "warning", response_time, "Page loads but content may be incomplete")
            else:
                return HealthResult("/", "unhealthy", response_time, f"HTTP {response.status_code}")
        except Exception as e:
            response_time = time.time() - start_time
            return HealthResult("/", "unhealthy", response_time, str(e))
    
    async def check_topology_api(self) -> HealthResult:
        """Check topology API endpoint"""
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/topology/scene")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "nodes" in data or "links" in data:
                        node_count = len(data.get("nodes", []))
                        link_count = len(data.get("links", []))
                        return HealthResult("/api/topology/scene", "healthy", response_time, f"Scene with {node_count} nodes, {link_count} links")
                    else:
                        return HealthResult("/api/topology/scene", "warning", response_time, "Response format unexpected")
                except:
                    return HealthResult("/api/topology/scene", "warning", response_time, "Response not valid JSON")
            else:
                return HealthResult("/api/topology/scene", "unhealthy", response_time, f"HTTP {response.status_code}")
        except Exception as e:
            response_time = time.time() - start_time
            return HealthResult("/api/topology/scene", "unhealthy", response_time, str(e))
    
    async def check_smart_tools_page(self) -> HealthResult:
        """Check smart tools page"""
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/smart-tools")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                if "smart tools" in response.text.lower() or "analysis" in response.text.lower():
                    return HealthResult("/smart-tools", "healthy", response_time, "Smart tools page loads")
                else:
                    return HealthResult("/smart-tools", "warning", response_time, "Page loads but content may be incomplete")
            else:
                return HealthResult("/smart-tools", "unhealthy", response_time, f"HTTP {response.status_code}")
        except Exception as e:
            response_time = time.time() - start_time
            return HealthResult("/smart-tools", "unhealthy", response_time, str(e))
    
    async def check_static_assets(self) -> HealthResult:
        """Check static assets are accessible"""
        start_time = time.time()
        try:
            # Check JavaScript files
            js_files = ["/static/app.js", "/static/troubleshooting.js"]
            missing_files = []
            
            for js_file in js_files:
                response = await self.client.get(f"{self.base_url}{js_file}")
                if response.status_code != 200:
                    missing_files.append(js_file)
            
            # Check CSS files
            css_files = ["/static/visualization.css"]
            for css_file in css_files:
                response = await self.client.get(f"{self.base_url}{css_file}")
                if response.status_code != 200:
                    missing_files.append(css_file)
            
            response_time = time.time() - start_time
            
            if not missing_files:
                return HealthResult("static_assets", "healthy", response_time, "All static assets accessible")
            else:
                return HealthResult("static_assets", "warning", response_time, f"Missing: {', '.join(missing_files)}")
        except Exception as e:
            response_time = time.time() - start_time
            return HealthResult("static_assets", "unhealthy", response_time, str(e))
    
    async def check_config_endpoints(self) -> HealthResult:
        """Check configuration endpoints"""
        start_time = time.time()
        try:
            # Test API docs endpoint
            response = await self.client.get(f"{self.base_url}/docs")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return HealthResult("/docs", "healthy", response_time, "API documentation accessible")
            else:
                return HealthResult("/docs", "unhealthy", response_time, f"HTTP {response.status_code}")
        except Exception as e:
            response_time = time.time() - start_time
            return HealthResult("/docs", "unhealthy", response_time, str(e))
    
    async def check_llm_integration(self) -> HealthResult:
        """Check LLM integration (if configured)"""
        start_time = time.time()
        try:
            # Try to access FortiNet LLM endpoint
            response = await self.client.get(f"{self.base_url}/api/fortinet-llm/status")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return HealthResult("llm_integration", "healthy", response_time, "LLM integration working")
            elif response.status_code == 404:
                return HealthResult("llm_integration", "warning", response_time, "LLM endpoint not configured")
            else:
                return HealthResult("llm_integration", "unhealthy", response_time, f"HTTP {response.status_code}")
        except Exception as e:
            response_time = time.time() - start_time
            return HealthResult("llm_integration", "warning", response_time, f"LLM check failed: {str(e)[:50]}")
    
    def generate_report(self, results: List[HealthResult]) -> str:
        """Generate health check report"""
        report = []
        report.append("Application Health Check Report")
        report.append("=" * 35)
        report.append("")
        
        # Overall status
        healthy_count = sum(1 for r in results if r.status == "healthy")
        warning_count = sum(1 for r in results if r.status == "warning")
        unhealthy_count = sum(1 for r in results if r.status == "unhealthy")
        
        if unhealthy_count == 0:
            report.append("🎉 OVERALL STATUS: HEALTHY")
        elif unhealthy_count <= 2:
            report.append("⚠️  OVERALL STATUS: DEGRADED")
        else:
            report.append("❌ OVERALL STATUS: UNHEALTHY")
        
        report.append(f"  Healthy: {healthy_count}")
        report.append(f"  Warnings: {warning_count}")
        report.append(f"  Unhealthy: {unhealthy_count}")
        report.append("")
        
        # Detailed results
        report.append("Detailed Results:")
        report.append("-" * 20)
        
        for result in results:
            status_icon = {
                "healthy": "✅",
                "warning": "⚠️ ",
                "unhealthy": "❌"
            }.get(result.status, "❓")
            
            report.append(f"{status_icon} {result.endpoint}")
            report.append(f"   Status: {result.status}")
            report.append(f"   Response Time: {result.response_time:.3f}s")
            report.append(f"   Details: {result.details}")
            report.append("")
        
        # Recommendations
        report.append("Recommendations:")
        report.append("-" * 20)
        
        if unhealthy_count == 0:
            if warning_count == 0:
                report.append("✅ Everything looks great!")
            else:
                report.append("🔍 Review warnings and address if needed")
        else:
            report.append("🛑 Fix unhealthy endpoints before deployment")
            report.append("🔍 Check application logs for detailed errors")
        
        report.append("")
        report.append(f"Checked at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(report)

async def main():
    """Main health check function"""
    print("Application Health Check")
    print("======================")
    print()
    
    # Check if application is running
    base_url = "http://127.0.0.1:11111"
    
    try:
        async with HealthChecker(base_url) as checker:
            results = await checker.check_all()
            report = checker.generate_report(results)
            print(report)
            
            # Determine exit code
            unhealthy_count = sum(1 for r in results if r.status == "unhealthy")
            sys.exit(0 if unhealthy_count == 0 else 1)
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        print()
        print("Make sure the application is running:")
        print("  python src/enhanced_network_api/platform_web_api_fastapi.py")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
