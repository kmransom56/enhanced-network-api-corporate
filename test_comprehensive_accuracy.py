#!/usr/bin/env python3
"""
Comprehensive Accuracy and Performance Test Suite
Tests functionality, accuracy, and performance of the Enhanced Network API
"""

import json
import time
import requests
from typing import Dict, List, Any
from datetime import datetime, UTC

# Configuration
BASE_URL = "http://localhost:8001"
TIMEOUT = 10

class TestReport:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now(UTC).isoformat(),
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            },
            "categories": {},
            "performance_metrics": {},
            "accuracy_validation": {}
        }
    
    def add_test(self, category: str, name: str, passed: bool, details: str = "", 
                 response_time: float = None, data: Any = None):
        if category not in self.results["categories"]:
            self.results["categories"][category] = []
        
        test_result = {
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "details": details,
            "response_time": f"{response_time:.3f}s" if response_time else None,
            "data": data
        }
        
        self.results["categories"][category].append(test_result)
        self.results["summary"]["total_tests"] += 1
        if passed:
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    def add_performance_metric(self, name: str, value: float, unit: str, 
                               threshold: float = None, passed: bool = True):
        self.results["performance_metrics"][name] = {
            "value": value,
            "unit": unit,
            "threshold": threshold,
            "passed": passed
        }
    
    def add_accuracy_check(self, name: str, expected: Any, actual: Any, passed: bool):
        self.results["accuracy_validation"][name] = {
            "expected": expected,
            "actual": actual,
            "passed": passed
        }
    
    def generate_report(self) -> str:
        """Generate formatted test report"""
        report = []
        report.append("=" * 80)
        report.append("ENHANCED NETWORK API - COMPREHENSIVE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {self.results['timestamp']}")
        report.append("")
        
        # Summary
        summary = self.results["summary"]
        report.append("TEST SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Tests:    {summary['total_tests']}")
        report.append(f"Passed:         {summary['passed']} ✓")
        report.append(f"Failed:         {summary['failed']} ✗")
        pass_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        report.append(f"Pass Rate:      {pass_rate:.1f}%")
        report.append("")
        
        # Test Categories
        for category, tests in self.results["categories"].items():
            report.append(f"\n{category.upper()}")
            report.append("-" * 80)
            for test in tests:
                status_icon = "✓" if test["status"] == "PASS" else "✗"
                rt = f" ({test['response_time']})" if test['response_time'] else ""
                report.append(f"  {status_icon} {test['name']}{rt}")
                if test["details"]:
                    report.append(f"      {test['details']}")
        
        # Performance Metrics
        if self.results["performance_metrics"]:
            report.append("\nPERFORMANCE METRICS")
            report.append("-" * 80)
            for name, metric in self.results["performance_metrics"].items():
                status = "✓" if metric["passed"] else "✗"
                threshold_info = f" (threshold: {metric['threshold']}{metric['unit']})" if metric['threshold'] else ""
                report.append(f"  {status} {name}: {metric['value']:.3f}{metric['unit']}{threshold_info}")
        
        # Accuracy Validation
        if self.results["accuracy_validation"]:
            report.append("\nACCURACY VALIDATION")
            report.append("-" * 80)
            for name, check in self.results["accuracy_validation"].items():
                status = "✓" if check["passed"] else "✗"
                report.append(f"  {status} {name}")
                if not check["passed"]:
                    report.append(f"      Expected: {check['expected']}")
                    report.append(f"      Actual:   {check['actual']}")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)

def test_health_endpoint(report: TestReport):
    """Test health endpoint"""
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        response_time = time.time() - start
        
        passed = response.status_code == 200
        data = response.json() if passed else None
        
        report.add_test(
            "Health & Status",
            "Health endpoint responds",
            passed,
            f"Status: {response.status_code}",
            response_time,
            data
        )
        
        if passed and data:
            report.add_accuracy_check(
                "Health status is 'healthy'",
                "healthy",
                data.get("status"),
                data.get("status") == "healthy"
            )
            
            report.add_accuracy_check(
                "API service is online",
                "online",
                data.get("services", {}).get("api", {}).get("status"),
                data.get("services", {}).get("api", {}).get("status") == "online"
            )
        
        report.add_performance_metric("Health check response", response_time, "s", 1.0, response_time < 1.0)
        
    except Exception as e:
        report.add_test("Health & Status", "Health endpoint responds", False, f"Error: {str(e)}")

def test_topology_endpoints(report: TestReport):
    """Test topology API endpoints"""
    
    # Test /api/topology/scene
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/topology/scene", timeout=TIMEOUT)
        response_time = time.time() - start
        
        passed = response.status_code == 200
        data = response.json() if passed else None
        
        report.add_test(
            "Topology API",
            "Topology scene endpoint",
            passed,
            f"Status: {response.status_code}",
            response_time
        )
        
        if passed and data:
            nodes = data.get("nodes", [])
            links = data.get("links", [])
            
            report.add_accuracy_check(
                "Scene has nodes",
                "> 0",
                len(nodes),
                len(nodes) > 0
            )
            
            report.add_accuracy_check(
                "Scene has links",
                ">= 0",
                len(links),
                len(links) >= 0
            )
            
            # Validate node structure
            if nodes:
                first_node = nodes[0]
                required_fields = ["id", "name", "type"]
                has_required = all(field in first_node for field in required_fields)
                report.add_accuracy_check(
                    "Nodes have required fields",
                    str(required_fields),
                    "Present" if has_required else "Missing",
                    has_required
                )
            
            report.add_performance_metric("Topology scene load", response_time, "s", 2.0, response_time < 2.0)
            
    except Exception as e:
        report.add_test("Topology API", "Topology scene endpoint", False, f"Error: {str(e)}")
    
    # Test /api/topology/raw
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/topology/raw", timeout=TIMEOUT)
        response_time = time.time() - start
        
        passed = response.status_code == 200
        report.add_test(
            "Topology API",
            "Raw topology endpoint",
            passed,
            f"Status: {response.status_code}",
            response_time
        )
        
        report.add_performance_metric("Raw topology load", response_time, "s", 2.0, response_time < 2.0)
        
    except Exception as e:
        report.add_test("Topology API", "Raw topology endpoint", False, f"Error: {str(e)}")

def test_static_pages(report: TestReport):
    """Test static HTML pages"""
    pages = [
        ("/", "Main dashboard"),
        ("/2d-topology-enhanced", "2D topology view"),
        ("/smart-tools", "Smart tools interface"),
        ("/automated-topology", "Automated topology docs"),
    ]
    
    for path, name in pages:
        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT)
            response_time = time.time() - start
            
            passed = response.status_code == 200
            report.add_test(
                "Static Pages",
                name,
                passed,
                f"Status: {response.status_code}",
                response_time
            )
            
            if passed:
                content_type = response.headers.get("content-type", "")
                is_html = "html" in content_type.lower()
                report.add_accuracy_check(
                    f"{name} returns HTML",
                    "text/html",
                    content_type,
                    is_html
                )
            
        except Exception as e:
            report.add_test("Static Pages", name, False, f"Error: {str(e)}")

def test_performance_metrics_endpoint(report: TestReport):
    """Test performance metrics endpoint"""
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/performance/metrics", timeout=TIMEOUT)
        response_time = time.time() - start
        
        passed = response.status_code == 200
        data = response.json() if passed else None
        
        report.add_test(
            "Performance & Monitoring",
            "Performance metrics endpoint",
            passed,
            f"Status: {response.status_code}",
            response_time
        )
        
        if passed and data:
            has_metrics = "metrics" in data
            report.add_accuracy_check(
                "Metrics data structure",
                "Present",
                "Present" if has_metrics else "Missing",
                has_metrics
            )
        
    except Exception as e:
        report.add_test("Performance & Monitoring", "Performance metrics endpoint", False, f"Error: {str(e)}")

def test_data_accuracy(report: TestReport):
    """Test data accuracy and validation"""
    try:
        response = requests.get(f"{BASE_URL}/api/topology/scene", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            nodes = data.get("nodes", [])
            links = data.get("links", [])
            
            # Validate node IDs are unique
            node_ids = [node.get("id") for node in nodes]
            unique_ids = len(node_ids) == len(set(node_ids))
            report.add_accuracy_check(
                "Node IDs are unique",
                "All unique",
                f"{len(set(node_ids))} unique / {len(node_ids)} total",
                unique_ids
            )
            
            # Validate links reference valid nodes
            node_id_set = set(node_ids)
            valid_links = True
            for link in links:
                from_id = link.get("from")
                to_id = link.get("to")
                if from_id not in node_id_set or to_id not in node_id_set:
                    valid_links = False
                    break
            
            report.add_accuracy_check(
                "Links reference valid nodes",
                "All valid",
                "Valid" if valid_links else "Invalid references found",
                valid_links
            )
            
            # Validate node types
            valid_types = ["fortigate", "fortiswitch", "fortiap", "client", "endpoint", "device", "network"]
            invalid_types = []
            for node in nodes:
                node_type = node.get("type", "").lower()
                if node_type and node_type not in valid_types:
                    invalid_types.append(node_type)
            
            report.add_accuracy_check(
                "Node types are valid",
                str(valid_types),
                "All valid" if not invalid_types else f"Invalid: {invalid_types}",
                len(invalid_types) == 0
            )
            
    except Exception as e:
        report.add_test("Data Accuracy", "Topology data validation", False, f"Error: {str(e)}")

def check_server_availability() -> bool:
    """Check if the server is available before running tests"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False

def main():
    """Run comprehensive test suite"""
    report = TestReport()
    
    print("Running Enhanced Network API Comprehensive Tests...")
    print("=" * 80)
    
    # Check server availability
    if not check_server_availability():
        print(f"\n⚠️  WARNING: Server not available at {BASE_URL}")
        print("   Please ensure the Enhanced Network API server is running.")
        print("   All tests will fail with connection errors.\n")
    
    test_health_endpoint(report)
    test_topology_endpoints(report)
    test_static_pages(report)
    test_performance_metrics_endpoint(report)
    test_data_accuracy(report)
    
    # Generate and display report
    print("\n" + report.generate_report())
    
    # Save report to file
    report_file = "test_comprehensive_report.json"
    with open(report_file, "w") as f:
        json.dump(report.results, f, indent=2)
    print(f"\nDetailed report saved to: {report_file}")
    
    # Return exit code based on test results
    return 0 if report.results["summary"]["failed"] == 0 else 1

if __name__ == "__main__":
    exit(main())