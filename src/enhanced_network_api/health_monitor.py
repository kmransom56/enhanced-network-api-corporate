"""
Self-Healing Health Monitor for Enhanced Network API
Provides continuous monitoring, automatic recovery, and health reporting
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Individual service health data."""
    name: str
    status: HealthStatus
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0
    last_success: Optional[datetime] = None


@dataclass
class SystemHealth:
    """Overall system health data."""
    status: HealthStatus
    timestamp: datetime
    services: Dict[str, ServiceHealth]
    metrics: Dict[str, Any]
    uptime: float
    recovery_actions: List[str]


class CircuitBreaker:
    """Circuit breaker for service calls."""
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if time.time() - (self.last_failure_time or 0) > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker moving to HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("Circuit breaker closed after successful call")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise e


class HealthMonitor:
    """Main health monitoring system."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.start_time = time.time()
        self.services: Dict[str, ServiceHealth] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.recovery_actions: List[str] = []
        self.health_history: List[SystemHealth] = []
        
        # Configuration
        self.api_base_url = self.config.get("api_base_url", "http://127.0.0.1:11111")
        self.mcp_bridge_url = self.config.get("mcp_bridge_url", "http://127.0.0.1:9001")
        self.check_interval = self.config.get("check_interval", 30)
        self.timeout = self.config.get("timeout", 30)
        self.max_failures = self.config.get("max_failures", 3)
        
        # Initialize circuit breakers
        self._init_circuit_breakers()
    
    def _init_circuit_breakers(self):
        """Initialize circuit breakers for critical services."""
        critical_services = ["api", "mcp_bridge", "topology_raw", "topology_scene"]
        for service in critical_services:
            self.circuit_breakers[service] = CircuitBreaker(
                failure_threshold=self.max_failures,
                recovery_timeout=60
            )
    
    async def check_service_health(self, service_name: str, endpoint: str = None) -> ServiceHealth:
        """Check health of a specific service."""
        service = self.services.get(service_name, ServiceHealth(
            name=service_name,
            status=HealthStatus.UNKNOWN
        ))
        
        start_time = time.time()
        
        try:
            if service_name == "api":
                await self._check_api_health()
            elif service_name == "mcp_bridge":
                await self._check_mcp_bridge_health()
            elif service_name == "topology_raw":
                await self._check_topology_raw_health()
            elif service_name == "topology_scene":
                await self._check_topology_scene_health()
            else:
                await self._check_generic_endpoint_health(endpoint)
            
            response_time = (time.time() - start_time) * 1000
            service.status = HealthStatus.HEALTHY
            service.response_time = response_time
            service.last_check = datetime.utcnow()
            service.consecutive_failures = 0
            service.last_success = datetime.utcnow()
            service.error_message = None
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            service.status = HealthStatus.UNHEALTHY
            service.response_time = response_time
            service.last_check = datetime.utcnow()
            service.consecutive_failures += 1
            service.error_message = str(e)
            
            logger.warning(f"Service {service_name} health check failed: {e}")
        
        self.services[service_name] = service
        return service
    
    async def _check_api_health(self):
        """Check main API health."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_base_url}/", timeout=self.timeout) as response:
                response.raise_for_status()
    
    async def _check_mcp_bridge_health(self):
        """Check MCP bridge health."""
        async with aiohttp.ClientSession() as session:
            payload = {"name": "test_health", "arguments": {}}
            async with session.post(
                f"{self.mcp_bridge_url}/mcp/call-tool",
                json=payload,
                timeout=self.timeout
            ) as response:
                response.raise_for_status()
    
    async def _check_topology_raw_health(self):
        """Check raw topology endpoint health."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_base_url}/api/topology/raw", timeout=self.timeout) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Validate response structure
                required_keys = ["gateways", "switches", "aps", "clients", "links"]
                missing_keys = [key for key in required_keys if key not in data]
                if missing_keys:
                    raise ValueError(f"Missing required keys: {missing_keys}")
    
    async def _check_topology_scene_health(self):
        """Check 3D scene topology endpoint health."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_base_url}/api/topology/scene", timeout=self.timeout) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Validate response structure
                required_keys = ["nodes", "links", "triageHints"]
                missing_keys = [key for key in required_keys if key not in data]
                if missing_keys:
                    raise ValueError(f"Missing required keys: {missing_keys}")
    
    async def _check_generic_endpoint_health(self, endpoint: str):
        """Check generic endpoint health."""
        if not endpoint:
            raise ValueError("Endpoint not specified")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, timeout=self.timeout) as response:
                response.raise_for_status()
    
    async def run_health_checks(self) -> SystemHealth:
        """Run all health checks and return system health."""
        logger.info("Running comprehensive health checks...")
        
        # Check all services
        services_to_check = [
            ("api", None),
            ("mcp_bridge", None),
            ("topology_raw", None),
            ("topology_scene", None)
        ]
        
        tasks = []
        for service_name, endpoint in services_to_check:
            circuit_breaker = self.circuit_breakers.get(service_name)
            if circuit_breaker:
                task = circuit_breaker.call(
                    self.check_service_health, service_name, endpoint
                )
            else:
                task = self.check_service_health(service_name, endpoint)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Health check failed: {result}")
        
        # Calculate overall system health
        system_health = self._calculate_system_health()
        
        # Store health history
        self.health_history.append(system_health)
        
        # Keep only last 100 entries
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]
        
        return system_health
    
    def _calculate_system_health(self) -> SystemHealth:
        """Calculate overall system health."""
        healthy_count = sum(1 for s in self.services.values() if s.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for s in self.services.values() if s.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for s in self.services.values() if s.status == HealthStatus.UNHEALTHY)
        total_count = len(self.services)
        
        if total_count == 0:
            overall_status = HealthStatus.UNKNOWN
        elif unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Calculate metrics
        uptime = time.time() - self.start_time
        avg_response_time = None
        if self.services:
            response_times = [s.response_time for s in self.services.values() if s.response_time is not None]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        metrics = {
            "service_count": total_count,
            "healthy_count": healthy_count,
            "degraded_count": degraded_count,
            "unhealthy_count": unhealthy_count,
            "avg_response_time": avg_response_time,
            "circuit_breakers_open": sum(1 for cb in self.circuit_breakers.values() if cb.state == "OPEN")
        }
        
        return SystemHealth(
            status=overall_status,
            timestamp=datetime.utcnow(),
            services=dict(self.services),
            metrics=metrics,
            uptime=uptime,
            recovery_actions=list(self.recovery_actions)
        )
    
    async def attempt_recovery(self, service_name: str) -> bool:
        """Attempt to recover a failed service."""
        logger.info(f"Attempting recovery for service: {service_name}")
        
        recovery_action = f"Recovery attempt for {service_name}"
        self.recovery_actions.append(f"{recovery_action} - {datetime.utcnow().isoformat()}")
        
        try:
            if service_name == "api":
                await self._recover_api_service()
            elif service_name == "mcp_bridge":
                await self._recover_mcp_bridge()
            elif service_name in ["topology_raw", "topology_scene"]:
                await self._recover_topology_service()
            
            # Wait a moment for recovery to take effect
            await asyncio.sleep(2)
            
            # Verify recovery
            await self.check_service_health(service_name)
            service = self.services.get(service_name)
            
            if service and service.status == HealthStatus.HEALTHY:
                logger.info(f"Successfully recovered service: {service_name}")
                self.recovery_actions.append(f"Successfully recovered {service_name}")
                return True
            else:
                logger.warning(f"Recovery failed for service: {service_name}")
                return False
                
        except Exception as e:
            logger.error(f"Recovery attempt failed for {service_name}: {e}")
            self.recovery_actions.append(f"Recovery failed for {service_name}: {e}")
            return False
    
    async def _recover_api_service(self):
        """Attempt to recover API service."""
        # In a real implementation, this might restart the service
        logger.info("Attempting API service recovery...")
        # For now, just wait a moment
        await asyncio.sleep(1)
    
    async def _recover_mcp_bridge(self):
        """Attempt to recover MCP bridge."""
        # In a real implementation, this might restart the MCP bridge
        logger.info("Attempting MCP bridge recovery...")
        # For now, just wait a moment
        await asyncio.sleep(1)
    
    async def _recover_topology_service(self):
        """Attempt to recover topology service."""
        # Clear any caches that might be causing issues
        logger.info("Attempting topology service recovery...")
        await asyncio.sleep(1)
    
    async def auto_heal(self) -> Dict[str, Any]:
        """Run automatic healing process."""
        logger.info("Starting automatic healing process...")
        
        system_health = await self.run_health_checks()
        healing_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "initial_status": system_health.status.value,
            "services_healed": [],
            "services_failed": [],
            "recovery_attempts": 0
        }
        
        # Attempt recovery for unhealthy services
        for service_name, service in system_health.services.items():
            if service.status == HealthStatus.UNHEALTHY:
                healing_results["recovery_attempts"] += 1
                
                if await self.attempt_recovery(service_name):
                    healing_results["services_healed"].append(service_name)
                else:
                    healing_results["services_failed"].append(service_name)
        
        # Final health check
        final_health = await self.run_health_checks()
        healing_results["final_status"] = final_health.status.value
        healing_results["success"] = final_health.status == HealthStatus.HEALTHY
        
        logger.info(f"Auto-healing completed: {healing_results}")
        return healing_results
    
    async def start_monitoring(self):
        """Start continuous monitoring."""
        logger.info(f"Starting health monitoring with {self.check_interval}s interval")
        
        while True:
            try:
                system_health = await self.run_health_checks()
                
                # Log health status
                logger.info(f"System health: {system_health.status.value} - "
                          f"Services: {system_health.metrics['healthy_count']}/{system_health.metrics['service_count']} healthy")
                
                # Auto-heal if needed
                if system_health.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]:
                    logger.info("System health degraded, attempting auto-healing...")
                    await self.auto_heal()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.check_interval)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary."""
        if not self.health_history:
            return {"status": "unknown", "message": "No health data available"}
        
        latest_health = self.health_history[-1]
        
        return {
            "status": latest_health.status.value,
            "timestamp": latest_health.timestamp.isoformat(),
            "uptime": latest_health.uptime,
            "services": {
                name: {
                    "status": service.status.value,
                    "response_time": service.response_time,
                    "consecutive_failures": service.consecutive_failures,
                    "last_success": service.last_success.isoformat() if service.last_success else None
                }
                for name, service in latest_health.services.items()
            },
            "metrics": latest_health.metrics,
            "recovery_actions": latest_health.recovery_actions[-10:],  # Last 10 actions
            "health_trend": self._calculate_health_trend()
        }
    
    def _calculate_health_trend(self) -> str:
        """Calculate health trend over time."""
        if len(self.health_history) < 2:
            return "insufficient_data"
        
        recent = self.health_history[-10:]  # Last 10 checks
        healthy_count = sum(1 for h in recent if h.status == HealthStatus.HEALTHY)
        
        if healthy_count >= 8:  # 80% or more healthy
            return "improving"
        elif healthy_count >= 5:  # 50-80% healthy
            return "stable"
        else:
            return "degrading"


# CLI interface
async def main():
    """Main CLI interface for health monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Network API Health Monitor")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--check-once", action="store_true", help="Run health check once and exit")
    parser.add_argument("--auto-heal", action="store_true", help="Run auto-healing")
    parser.add_argument("--monitor", action="store_true", help="Start continuous monitoring")
    parser.add_argument("--api-url", default="http://127.0.0.1:11111", help="API base URL")
    parser.add_argument("--mcp-url", default="http://127.0.0.1:9001", help="MCP bridge URL")
    
    args = parser.parse_args()
    
    # Configuration
    config = {
        "api_base_url": args.api_url,
        "mcp_bridge_url": args.mcp_url,
        "check_interval": 30,
        "timeout": 30,
        "max_failures": 3
    }
    
    if args.config:
        try:
            with open(args.config, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
    
    # Initialize health monitor
    monitor = HealthMonitor(config)
    
    if args.check_once:
        # Run single health check
        health = await monitor.run_health_checks()
        print(json.dumps(monitor.get_health_summary(), indent=2))
        
    elif args.auto_heal:
        # Run auto-healing
        results = await monitor.auto_heal()
        print(json.dumps(results, indent=2))
        
    elif args.monitor:
        # Start continuous monitoring
        await monitor.start_monitoring()
        
    else:
        # Default: show health summary
        health = await monitor.run_health_checks()
        summary = monitor.get_health_summary()
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
