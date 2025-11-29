#!/usr/bin/env python3
"""
Simple test for MAC address API
"""

import os
import sys
sys.path.insert(0, '/home/keith/enhanced-network-api-corporate/src/enhanced_network_api')

# Set environment variables
os.environ['MACADDRESS_IO_API_KEY'] = 'at_ZQ2hTICmKjG8Pwgy3z6p2jvxB7Ky4'

try:
    from device_mac_matcher import DeviceModelMatcher
    print("✅ Import successful")
    
    matcher = DeviceModelMatcher()
    print("✅ Initialization successful")
    
    # Test a simple lookup
    result = matcher.match_mac_to_model("00:0C:F1:12:34:56")
    print(f"✅ Lookup successful: {result.vendor} - {result.device_type}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
