#!/usr/bin/env python3
"""
Pre-commit Hook - Prevents Code Drift
Runs before every git commit
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run command and return success"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        if result.returncode != 0:
            print(f"❌ Failed: {description}")
            print(f"Error: {result.stderr}")
            return False
        print(f"✅ Passed: {description}")
        return True
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    """Pre-commit validation"""
    print("🛡️  Pre-commit drift protection checks...")
    
    checks = [
        ("python config_validator.py", "Configuration validation"),
        ("python startup_health_check.py", "Startup health check"),
        ("python test_drift_protection.py", "Drift protection tests"),
        ("python -m py_compile src/enhanced_network_api/platform_web_api_fastapi.py", "FastAPI syntax check"),
        ("python -m py_compile mcp_servers/drawio_fortinet_meraki/mcp_server.py", "MCP server syntax check")
    ]
    
    all_passed = True
    for cmd, desc in checks:
        if not run_command(cmd, desc):
            all_passed = False
    
    if all_passed:
        print("\n✅ All pre-commit checks passed! Commit allowed.")
        sys.exit(0)
    else:
        print("\n❌ Pre-commit checks failed! Commit blocked.")
        print("Fix issues before committing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
