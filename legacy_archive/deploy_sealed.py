#!/usr/bin/env python3
"""
Sealed Deployment Script
Validates everything before starting the application
"""

import os
import sys
import subprocess
import time
from pathlib import Path

class SealedDeployment:
    """Validated deployment with drift protection"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        
    def deploy(self) -> bool:
        """Run sealed deployment process"""
        print("🚀 Starting sealed deployment...")
        print("=" * 60)
        
        # Step 1: Environment validation
        if not self._validate_environment():
            return False
        
        # Step 2: Configuration validation
        if not self._validate_configuration():
            return False
        
        # Step 3: Syntax validation
        if not self._validate_syntax():
            return False
        
        # Step 4: Start services
        if not self._start_services():
            return False
        
        # Step 5: Post-start validation
        if not self._validate_running_system():
            return False
        
        print("\n🎉 Sealed deployment successful!")
        print("Application is running with drift protection enabled.")
        return True
    
    def _validate_environment(self) -> bool:
        """Validate deployment environment"""
        print("\n🔍 Step 1: Environment validation...")
        
        # Check Python
        version = sys.version_info
        if version.major != 3 or version.minor < 8:
            print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
            return False
        
        # Check virtual environment
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("⚠️  Not in virtual environment - recommended")
        
        # Check critical files
        critical_files = [
            "requirements.locked.txt",
            "config_validator.py",
            "startup_health_check.py",
            "test_drift_protection.py"
        ]
        
        for file_path in critical_files:
            if not (self.base_dir / file_path).exists():
                print(f"❌ Missing drift protection file: {file_path}")
                return False
        
        print("✅ Environment validation passed")
        return True
    
    def _validate_configuration(self) -> bool:
        """Validate all configurations"""
        print("\n🔍 Step 2: Configuration validation...")
        
        result = subprocess.run(
            ["python", "config_validator.py"],
            capture_output=True, text=True,
            cwd=self.base_dir
        )
        
        if result.returncode != 0:
            print("❌ Configuration validation failed:")
            print(result.stdout)
            print(result.stderr)
            return False
        
        print("✅ Configuration validation passed")
        return True
    
    def _validate_syntax(self) -> bool:
        """Validate Python syntax"""
        print("\n🔍 Step 3: Syntax validation...")
        
        python_files = [
            "src/enhanced_network_api/platform_web_api_fastapi.py",
            "mcp_servers/drawio_fortinet_meraki/mcp_server.py"
        ]
        
        for py_file in python_files:
            full_path = self.base_dir / py_file
            result = subprocess.run(
                ["python", "-m", "py_compile", str(full_path)],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Syntax error in {py_file}:")
                print(result.stderr)
                return False
        
        print("✅ Syntax validation passed")
        return True
    
    def _start_services(self) -> bool:
        """Start application services"""
        print("\n🔍 Step 4: Starting services...")
        
        # Kill existing services
        subprocess.run("pkill -f platform_web_api_fastapi.py", shell=True)
        time.sleep(2)
        
        # Start FastAPI service
        venv_python = self.base_dir / ".venv" / "bin" / "python"
        cmd = f"cd src/enhanced_network_api && {venv_python} platform_web_api_fastapi.py"
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=self.base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for startup
        time.sleep(3)
        
        # Check if process is running
        if process.poll() is not None:
            print("❌ FastAPI service failed to start")
            stdout, stderr = process.communicate()
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return False
        
        print("✅ Services started successfully")
        return True
    
    def _validate_running_system(self) -> bool:
        """Validate running system"""
        print("\n🔍 Step 5: Post-start validation...")
        
        # Run health check
        result = subprocess.run(
            ["python", "test_drift_protection.py"],
            capture_output=True, text=True,
            cwd=self.base_dir
        )
        
        if result.returncode != 0:
            print("❌ Running system validation failed:")
            print(result.stdout)
            print(result.stderr)
            return False
        
        print("✅ Running system validation passed")
        return True

def main():
    """Run sealed deployment"""
    deployment = SealedDeployment()
    
    if deployment.deploy():
        print("\n" + "=" * 60)
        print("🎯 DEPLOYMENT SUMMARY")
        print("=" * 60)
        print("✅ Application deployed successfully")
        print("✅ Drift protection enabled")
        print("✅ All validations passed")
        print("\n📱 Access URLs:")
        print("   • Main 3D: http://127.0.0.1:11111/")
        print("   • 2D Topology: http://127.0.0.1:11111/2d-topology-enhanced")
        print("   • API Data: http://127.0.0.1:11111/api/topology/scene")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n❌ Deployment failed! Fix issues and retry.")
        sys.exit(1)

if __name__ == "__main__":
    main()
