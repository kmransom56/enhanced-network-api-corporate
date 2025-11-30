# FortiGate Monitor Integration

## Overview

The `fortigate_monitor.py` module has been integrated into the Enhanced Network API, providing comprehensive access to 40+ FortiGate monitoring endpoints through a clean, simple interface.

## What Was Integrated

### 1. Enhanced FortiGateMonitor Class
- **Location**: `src/enhanced_network_api/fortigate_monitor.py`
- **Improvements**:
  - Better type hints and documentation
  - Improved SSL certificate handling (supports bool or path)
  - Better error handling and logging
  - Support for query parameters

### 2. New FastAPI Endpoints

All new endpoints use the `FortiGateDirectRequest` model for credentials and are available at `/api/fortigate/monitor/*`:

#### WiFi Monitoring
- `POST /api/fortigate/monitor/wifi/clients` - WiFi clients
- `POST /api/fortigate/monitor/wifi/ssids` - WiFi SSIDs

#### Switch Monitoring
- `POST /api/fortigate/monitor/switch/clients` - Switch clients
- `POST /api/fortigate/monitor/switch/status` - Switch status

#### System Monitoring
- `POST /api/fortigate/monitor/system/cpu` - CPU usage
- `POST /api/fortigate/monitor/system/memory` - Memory usage
- `POST /api/fortigate/monitor/system/sessions` - Active sessions

#### Routing Monitoring
- `POST /api/fortigate/monitor/routing/arp` - ARP table
- `POST /api/fortigate/monitor/routing/dhcp` - DHCP leases

#### Interface Monitoring
- `POST /api/fortigate/monitor/interfaces` - System interfaces

#### Complete Dataset
- `POST /api/fortigate/monitor/full-dataset` - Complete monitoring snapshot (all endpoints)

### 3. Helper Function
- `_create_fortigate_monitor()` - Creates a `FortiGateMonitor` instance from credentials or environment variables
- Uses the same credential resolution logic as `_create_fortigate_collector()`
- Supports host-specific tokens (e.g., `FORTIGATE_192_168_0_254_TOKEN`)

## Usage Examples

### Using Environment Variables
```bash
export FORTIGATE_HOST=192.168.0.254
export FORTIGATE_TOKEN=your_token_here

curl -X POST http://localhost:11111/api/fortigate/monitor/wifi/clients \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Using Request Credentials
```bash
curl -X POST http://localhost:11111/api/fortigate/monitor/system/cpu \
  -H "Content-Type: application/json" \
  -d '{
    "credentials": {
      "host": "192.168.0.254",
      "token": "your_token_here"
    }
  }'
```

### Getting Full Dataset
```bash
curl -X POST http://localhost:11111/api/fortigate/monitor/full-dataset \
  -H "Content-Type: application/json" \
  -d '{
    "credentials": {
      "host": "192.168.0.254",
      "token": "your_token_here"
    }
  }'
```

## Available Monitoring Methods

The `FortiGateMonitor` class provides access to:

### WiFi (7 methods)
- `wifi_clients()` - Connected WiFi clients
- `wifi_ssids()` - Configured SSIDs
- `wifi_radios()` - Radio information
- `wifi_neighbors()` - Neighbor APs
- `wifi_manufacturer()` - Manufacturer data
- `wifi_reputation()` - Reputation scores
- `wifi_channels()` - Channel information

### Switch Controller (5 methods)
- `switch_clients()` - Connected switch clients
- `switch_ports()` - Port status
- `switch_status()` - Switch status
- `switch_vlans()` - VLAN information
- `switch_poe()` - PoE status

### Routing (7 methods)
- `arp_table()` - ARP table
- `dhcp()` - DHCP leases
- `routing_ipv4()` - IPv4 routes
- `routing_neighbors()` - Neighbor information
- `ospf()` - OSPF data
- `bgp()` - BGP data
- `nexthop()` - Next hop information

### LLDP / Interfaces (2 methods)
- `lldp()` - LLDP neighbors
- `interfaces()` - System interfaces

### System Info (7 methods)
- `system_status()` - System status
- `cpu()` - CPU usage
- `memory()` - Memory usage
- `performance()` - Performance metrics
- `disk()` - Disk usage
- `lograte()` - Log rate
- `sessions()` - Active sessions

### Firewall / Security (3 methods)
- `fw_policy_hits()` - Policy hit counts
- `fw_sessions()` - Firewall sessions
- `multicas()` - Multicast data

### Logs (2 methods)
- `event_logs()` - Event logs
- `traffic_logs()` - Traffic logs

### Device Inventory (1 method)
- `device_inventory()` - Device inventory

### Diagnostics (2 methods)
- `ping(host, count)` - Ping test
- `trace(host)` - Traceroute test

## Benefits

1. **Comprehensive Coverage**: Access to 40+ monitoring endpoints
2. **Simplified Code**: Clean, method-based interface
3. **Easy Maintenance**: Single point for API changes
4. **Better Error Handling**: Centralized error management
5. **Dataset Building**: `build_dataset()` for complete snapshots
6. **Consistent API**: Same credential handling as existing endpoints

## Future Enhancements

- Add caching for frequently accessed data
- Add rate limiting for `build_dataset()` endpoint
- Add WebSocket support for real-time monitoring
- Add filtering and pagination for large datasets
- Integrate with existing topology collector for enhanced data collection

## Notes

- All endpoints require authentication via API token
- SSL verification can be disabled for self-signed certificates
- The `full-dataset` endpoint may take significant time to complete
- Error responses include the endpoint path for debugging

