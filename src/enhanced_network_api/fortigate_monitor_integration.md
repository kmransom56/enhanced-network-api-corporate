# FortiGate Monitor Integration Plan

## Overview
The `fortigate_monitor.py` module provides a comprehensive, easy-to-use interface to FortiGate monitoring endpoints. This document outlines the integration strategy.

## Current State
- `fortigate_monitor.py` exists but is not currently used
- Existing endpoints use direct API calls or `FortiGateTopologyCollector`
- Some monitoring endpoints exist but are limited

## Integration Options

### Option 1: Enhance Existing Endpoints (Recommended)
- Integrate `FortiGateMonitor` into `FortiGateTopologyCollector`
- Add monitoring methods to existing collector
- Maintain backward compatibility

### Option 2: Create New Monitoring Endpoints
- Add `/api/fortigate/monitor/*` endpoints
- Use `FortiGateMonitor` directly in FastAPI
- Provide comprehensive monitoring API

### Option 3: Hybrid Approach
- Use `FortiGateMonitor` for new monitoring endpoints
- Keep existing topology endpoints as-is
- Gradually migrate to unified interface

## Recommended Implementation

### Phase 1: Create Monitoring Endpoints
Add new FastAPI endpoints that use `FortiGateMonitor`:
- `/api/fortigate/monitor/wifi/*` - WiFi monitoring
- `/api/fortigate/monitor/switch/*` - Switch monitoring
- `/api/fortigate/monitor/system/*` - System monitoring
- `/api/fortigate/monitor/routing/*` - Routing monitoring
- `/api/fortigate/monitor/full-dataset` - Complete dataset

### Phase 2: Enhance Topology Collector
- Add `FortiGateMonitor` as optional dependency
- Use it for enhanced data collection
- Maintain existing API compatibility

### Phase 3: Unified Interface
- Create unified monitoring service
- Consolidate all monitoring endpoints
- Provide consistent API structure

## Benefits
1. **Comprehensive Coverage**: Access to 40+ monitoring endpoints
2. **Simplified Code**: Clean, method-based interface
3. **Easy Maintenance**: Single point for API changes
4. **Better Error Handling**: Centralized error management
5. **Dataset Building**: `build_dataset()` for complete snapshots

## Implementation Notes
- Handle authentication (token vs session)
- Support SSL verification configuration
- Add proper error handling and logging
- Consider rate limiting for `build_dataset()`
- Add caching for frequently accessed data

