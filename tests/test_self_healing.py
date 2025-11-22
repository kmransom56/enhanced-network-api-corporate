"""
Self-healing functionality tests for Enhanced Network API
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from src.enhanced_network_api.platform_web_api_fastapi import app


@pytest.mark.self_healing
@pytest.mark.asyncio
async def test_fortinet_mcp_bridge_recovery():
    """Test automatic recovery of Fortinet MCP bridge connection."""
    
    # Mock the requests.post to simulate bridge failure and recovery
    with patch('requests.post') as mock_post:
        # First call fails (bridge down)
        mock_post.side_effect = [
            MagicMock(status_code=503, text="Service Unavailable"),
            MagicMock(status_code=200, json=lambda: {
                "content": [{"type": "text", "text": '{"devices": [], "links": []}'}],
                "isError": False
            })
        ]
        
        # Test the _call_fortinet_tool function with retry logic
        from src.enhanced_network_api.platform_web_api_fastapi import _call_fortinet_tool
        from fastapi import HTTPException
        
        # First call should handle the error gracefully
        with pytest.raises(HTTPException) as exc_info:
            _call_fortinet_tool("discover_fortinet_topology")
        assert exc_info.value.status_code == 503
        
        # Second call should succeed
        result2 = _call_fortinet_tool("discover_fortinet_topology")
        assert isinstance(result2, dict)
        assert result2.get("devices") == []
        assert result2.get("links") == []


@pytest.mark.self_healing
@pytest.mark.asyncio
async def test_topology_data_integrity_check():
    """Test topology data integrity validation and self-healing."""
    
    # Mock corrupted topology data
    corrupted_data = {
        "devices": [
            {"id": None, "type": "fortigate", "name": "Invalid Gateway"},
            {"id": "segment-1", "type": "network", "ip": "invalid_ip"},
        ],
        "links": [
            {"source_id": "missing", "target_id": "also_missing"},
            {"source_id": "segment-1", "target_id": "missing"},
        ],
    }
    
    # Test data validation and healing
    def validate_and_heal_topology(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and heal topology data."""
        healed_devices = []
        for device in data.get("devices", []):
            device_id = device.get("id")
            device_type = device.get("type")
            if not device_id or not device_type:
                continue

            healed_device = dict(device)
            if device_type == "network":
                ip = healed_device.get("ip", "")
                if not ip or " " not in ip:
                    healed_device["ip"] = "0.0.0.0 0.0.0.0"
            healed_devices.append(healed_device)

        valid_ids = {device["id"] for device in healed_devices}
        healed_links = [
            link
            for link in data.get("links", [])
            if link.get("source_id") in valid_ids and link.get("target_id") in valid_ids
        ]

        return {"devices": healed_devices, "links": healed_links}
    
    # Test the healing function
    healed_data = validate_and_heal_topology(corrupted_data)
    
    # Verify healing worked
    assert len(healed_data["devices"]) == 1  # Invalid gateway removed
    healed_segment = healed_data["devices"][0]
    assert healed_segment["id"] == "segment-1"
    assert healed_segment["ip"] == "0.0.0.0 0.0.0.0"
    assert len(healed_data["links"]) == 0  # Invalid links removed


@pytest.mark.self_healing
@pytest.mark.asyncio
async def test_circuit_breaker_pattern():
    """Test circuit breaker pattern for external service calls."""
    
    class CircuitBreaker:
        """Simple circuit breaker implementation for testing."""
        
        def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
            self.failure_threshold = failure_threshold
            self.recovery_timeout = recovery_timeout
            self.failure_count = 0
            self.last_failure_time = None
            self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        async def call(self, func, *args, **kwargs):
            """Execute function with circuit breaker protection."""
            if self.state == "OPEN":
                if asyncio.get_event_loop().time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = asyncio.get_event_loop().time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                
                raise e
    
    # Test circuit breaker functionality
    circuit_breaker = CircuitBreaker(failure_threshold=2)
    
    call_count = 0
    
    async def failing_function():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise Exception("Simulated failure")
        return "success"
    
    # First two calls should fail
    with pytest.raises(Exception):
        await circuit_breaker.call(failing_function)
    
    with pytest.raises(Exception):
        await circuit_breaker.call(failing_function)
    
    # Circuit should now be OPEN
    assert circuit_breaker.state == "OPEN"
    
    # Call should fail immediately without executing the function
    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        await circuit_breaker.call(failing_function)


@pytest.mark.self_healing
@pytest.mark.asyncio
async def test_health_monitoring_and_auto_recovery():
    """Test health monitoring and automatic recovery mechanisms."""
    
    class HealthMonitor:
        """Health monitoring system for testing."""
        
        def __init__(self):
            self.services = {
                "fortinet_mcp": {"status": "unknown", "last_check": 0, "failures": 0},
                "web_api": {"status": "unknown", "last_check": 0, "failures": 0},
                "database": {"status": "unknown", "last_check": 0, "failures": 0}
            }
            self.max_failures = 3
        
        async def check_service_health(self, service_name: str) -> bool:
            """Check health of a specific service."""
            # Simulate health check
            import random
            is_healthy = random.random() > 0.3  # 70% chance of being healthy
            
            service = self.services[service_name]
            if is_healthy:
                service["status"] = "healthy"
                service["failures"] = 0
            else:
                service["failures"] += 1
                if service["failures"] >= self.max_failures:
                    service["status"] = "unhealthy"
                else:
                    service["status"] = "degraded"
            
            service["last_check"] = asyncio.get_event_loop().time()
            return is_healthy
        
        async def attempt_recovery(self, service_name: str) -> bool:
            """Attempt to recover a failed service."""
            # Simulate recovery attempt
            await asyncio.sleep(0.1)  # Simulate recovery time
            
            # Reset failure count and mark as healthy
            self.services[service_name]["failures"] = 0
            self.services[service_name]["status"] = "healthy"
            
            return True
        
        async def monitor_and_heal(self):
            """Monitor all services and attempt recovery for failed ones."""
            for service_name in self.services:
                await self.check_service_health(service_name)
                
                # Attempt recovery for unhealthy services
                if self.services[service_name]["status"] == "unhealthy":
                    print(f"Attempting recovery for {service_name}...")
                    await self.attempt_recovery(service_name)
    
    # Test health monitoring
    monitor = HealthMonitor()
    
    # Simulate service checks and recovery
    await monitor.monitor_and_heal()
    
    # Verify all services are monitored
    assert all(service["last_check"] > 0 for service in monitor.services.values())


@pytest.mark.self_healing
@pytest.mark.asyncio
async def test_cache_invalidation_and_refresh():
    """Test cache invalidation and refresh mechanisms."""
    
    class TopologyCache:
        """Topology cache with invalidation support."""
        
        def __init__(self, ttl: int = 300):  # 5 minutes TTL
            self.cache = {}
            self.timestamps = {}
            self.ttl = ttl
        
        def get(self, key: str) -> Any:
            """Get value from cache if valid."""
            current_time = asyncio.get_event_loop().time()
            
            if (key in self.cache and 
                key in self.timestamps and 
                current_time - self.timestamps[key] < self.ttl):
                return self.cache[key]
            
            return None
        
        def set(self, key: str, value: Any):
            """Set value in cache with timestamp."""
            self.cache[key] = value
            self.timestamps[key] = asyncio.get_event_loop().time()
        
        def invalidate(self, key: str = None):
            """Invalidate cache entry or entire cache."""
            if key:
                self.cache.pop(key, None)
                self.timestamps.pop(key, None)
            else:
                self.cache.clear()
                self.timestamps.clear()
        
        def is_expired(self, key: str) -> bool:
            """Check if cache entry is expired."""
            current_time = asyncio.get_event_loop().time()
            return (key not in self.timestamps or 
                   current_time - self.timestamps[key] >= self.ttl)
    
    # Test cache functionality
    cache = TopologyCache(ttl=1)  # 1 second TTL for testing
    
    # Test cache miss
    assert cache.get("test_key") is None
    
    # Test cache set and get
    test_data = {"nodes": [], "links": []}
    cache.set("test_key", test_data)
    assert cache.get("test_key") == test_data
    
    # Test cache expiration
    await asyncio.sleep(1.1)
    assert cache.get("test_key") is None
    assert cache.is_expired("test_key")
    
    # Test cache invalidation
    cache.set("test_key2", test_data)
    cache.invalidate("test_key2")
    assert cache.get("test_key2") is None
    
    # Test full cache clear
    cache.set("test_key3", test_data)
    cache.invalidate()
    assert len(cache.cache) == 0


@pytest.mark.self_healing
@pytest.mark.asyncio
async def test_graceful_degradation():
    """Test graceful degradation when services are unavailable."""
    
    class ServiceManager:
        """Service manager with graceful degradation."""
        
        def __init__(self):
            self.services = {
                "fortinet_mcp": {"available": True, "fallback": True, "simulate_failure": False},
                "meraki_mcp": {"available": True, "fallback": False},
                "database": {"available": True, "fallback": True}
            }
        
        async def get_topology_data(self) -> Dict[str, Any]:
            """Get topology data with graceful degradation."""
            result = {
                "devices": [],
                "degraded_services": []
            }
            
            # Try Fortinet MCP first
            if self.services["fortinet_mcp"]["available"]:
                try:
                    if self.services["fortinet_mcp"].get("simulate_failure"):
                        raise Exception("Simulated Fortinet failure")
                    result["devices"].append({"id": "fg-test", "type": "fortigate", "name": "Test Gateway"})
                except Exception as e:
                    print(f"Fortinet MCP failed: {e}")
                    if self.services["fortinet_mcp"]["fallback"]:
                        result["devices"].append({"id": "fg-cached", "type": "fortigate", "name": "Cached Gateway"})
                        result["degraded_services"].append("fortinet_mcp")
                    self.services["fortinet_mcp"]["available"] = False
            
            # Try Meraki MCP
            if self.services["meraki_mcp"]["available"]:
                try:
                    # Simulate Meraki data fetch
                    result["devices"].append({"id": "meraki-client", "type": "client", "name": "Meraki Client"})
                except Exception as e:
                    print(f"Meraki MCP failed: {e}")
                    if self.services["meraki_mcp"]["fallback"]:
                        result["devices"].append({"id": "fallback-client", "type": "client", "name": "Fallback Client"})
                        result["degraded_services"].append("meraki_mcp")
                    self.services["meraki_mcp"]["available"] = False
            
            return result
    
    # Test graceful degradation
    manager = ServiceManager()
    
    # Simulate service failure
    manager.services["fortinet_mcp"]["simulate_failure"] = True
    
    # Get topology with degradation
    result = await manager.get_topology_data()
    
    # Verify fallback data is used
    fortigate_devices = [d for d in result["devices"] if d.get("type") == "fortigate"]
    assert fortigate_devices
    assert "fortinet_mcp" in result["degraded_services"]
    assert fortigate_devices[0]["id"] == "fg-cached"


@pytest.mark.self_healing
@pytest.mark.integration
async def test_end_to_end_self_healing_workflow():
    """Test end-to-end self-healing workflow."""
    
    # This test simulates a complete self-healing scenario:
    # 1. Service failure detection
    # 2. Automatic retry with exponential backoff
    # 3. Circuit breaker activation
    # 4. Graceful degradation
    # 5. Service recovery and normalization
    
    class SelfHealingSystem:
        """Complete self-healing system for testing."""
        
        def __init__(self):
            self.retry_count = 0
            self.max_retries = 3
            self.circuit_breaker_open = False
            self.degraded_mode = False
        
        async def fetch_topology_with_healing(self) -> Dict[str, Any]:
            """Fetch topology with complete self-healing logic."""
            
            # Exponential backoff retry
            for attempt in range(self.max_retries):
                try:
                    # Simulate API call
                    if self.retry_count < 2:  # Fail first 2 attempts
                        self.retry_count += 1
                        raise Exception(f"Service unavailable (attempt {attempt + 1})")
                    
                    # Success on third attempt
                    return {
                        "devices": [{"id": "fg-recovered", "type": "fortigate", "name": "Recovered Gateway"}],
                        "links": [],
                        "healing_info": {
                            "retry_attempts": attempt + 1,
                            "recovered": True
                        }
                    }
                
                except Exception:
                    if attempt < self.max_retries - 1:
                        # Exponential backoff
                        backoff_time = 2 ** attempt
                        await asyncio.sleep(backoff_time)
                    else:
                        # All retries failed, activate circuit breaker
                        self.circuit_breaker_open = True
                        self.degraded_mode = True

                        return {
                            "devices": [
                                {"id": "fg-degraded", "type": "fortigate", "name": "Degraded Gateway"}
                            ],
                            "links": [],
                            "healing_info": {
                                "retry_attempts": self.max_retries,
                                "recovered": False,
                                "degraded_mode": True,
                                "circuit_breaker_open": True
                            }
                        }
    
    # Test the self-healing system
    healing_system = SelfHealingSystem()
    
    # Fetch topology with healing
    result = await healing_system.fetch_topology_with_healing()
    
    # Verify healing logic worked
    assert "healing_info" in result
    assert result["healing_info"]["retry_attempts"] <= 3
    fortigate_devices = [d for d in result.get("devices", []) if d.get("type") == "fortigate"]
    assert fortigate_devices, "Expected fortigate device data even in degraded mode"
    
    if healing_system.degraded_mode:
        assert result["healing_info"]["degraded_mode"] is True
        assert fortigate_devices[0]["id"] == "fg-degraded"
    else:
        assert result["healing_info"]["recovered"] is True
        assert fortigate_devices[0]["id"] == "fg-recovered"
