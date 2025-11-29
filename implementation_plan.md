# Implementation Plan - Code Efficiency Improvements

The goal is to improve the efficiency of the `enhanced-network-api` by optimizing JSON processing and data transformation functions.

## User Review Required

> [!IMPORTANT]
> This plan introduces a new dependency: `orjson`. It is a fast JSON library for Python.
> Please ensure that `orjson` can be installed in your environment.

## Proposed Changes

### Dependencies

#### [MODIFY] [requirements.txt](file:///home/keith/enhanced-network-api-corporate/requirements.txt)
- Add `orjson` to the requirements.

### Codebase Optimizations

#### [MODIFY] [src/enhanced_network_api/platform_web_api_fastapi.py](file:///home/keith/enhanced-network-api-corporate/src/enhanced_network_api/platform_web_api_fastapi.py)
- Import `orjson`.
- Replace `json.dumps` and `json.loads` with `orjson.dumps` and `orjson.loads` where appropriate.
- Optimize `_normalize_scene_compute` to use list comprehensions and reduce dictionary lookups.
- Optimize `_scene_to_lab_format` similarly.
- Optimize `FortinetMCPClient` caching to avoid sorting arguments on every call if possible, or use a faster key generation method.

#### [MODIFY] [src/enhanced_network_api/shared/topology_workflow.py](file:///home/keith/enhanced-network-api-corporate/src/enhanced_network_api/shared/topology_workflow.py)
- Import `orjson`.
- Replace `json` operations with `orjson` for faster payload processing.

#### [MODIFY] [src/enhanced_network_api/network_topology_workflow.py](file:///home/keith/enhanced-network-api-corporate/src/enhanced_network_api/network_topology_workflow.py)
- Import `orjson`.
- Replace `json.dumps` with `orjson.dumps` in `step7_export_visualizations`.
- Parallelize `step4_identify_devices` using `asyncio.gather` and `asyncio.to_thread` to prevent blocking on OUI lookups.
- Parallelize `step5_generate_svg_icons` using `asyncio.to_thread` for file I/O.
- Add `MANUFACTURER_ICON_MAP` constant with mappings for Fortinet, Cisco, Printers, Mobile, etc.
- [x] **Manufacturer-to-Icon Mapping**:
    - [x] Define `MANUFACTURER_ICON_MAP` in `network_topology_workflow.py`.
    - [x] Update `_generate_svg_filename` and `_get_icon_config` to use the map.
- [x] **SSL Certificate Support**:
    - [x] Update `FortiGateAuth` to accept custom CA certificate path.
    - [x] Update `NetworkTopologyWorkflow` to pass CA certificate path.

#### [MODIFY] [src/enhanced_network_api/device_mac_matcher.py](file:///home/keith/enhanced-network-api-corporate/src/enhanced_network_api/device_mac_matcher.py)
- Implement `_lookup_maclookup_app` using `https://api.maclookup.app/v2/macs/{mac}/company/name`.
- Implement `_lookup_macvendors_com` using `https://macvendors.com/api/{mac}`.
- Update `lookup` method to implement a fallback strategy: Local DB -> macaddress.io (if key) -> maclookup.app -> macvendors.com.
- Ensure proper error handling and timeout management for these external calls.
- Add `DEVICE_TYPES` and `OUI_DEVICE_TYPES` constants as provided.
- Enhance `DeviceClassifier.classify_device` to implement the "Advanced Classification" logic:
    - Use OUI-based type lookup.
    - Use vendor name keyword matching (Polycom, Cisco, HP, etc.).
    - Use metadata (hostname, model) for context-aware classification (e.g., iPhone in hostname).
    - Support Fortinet specific model detection from metadata.



## Verification Plan

### Automated Tests
- Run `tests/benchmark_efficiency.py` (after updating it to use the new code) to verify performance improvements.
- Run existing tests to ensure no regressions.

### Manual Verification
- Verify that the API endpoints return correct JSON responses.
