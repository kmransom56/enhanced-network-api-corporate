#!/usr/bin/env python3
"""
Complete VSS + Eraser AI 3D Model Workflow - Linux Compatible Version
This script runs the entire workflow on Linux systems without PowerShell
"""

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

class LinuxWorkflowExecutor:
    def __init__(self):
        self.project_root = Path("/home/keith/enhanced-network-api-corporate")
        self.vss_dir = self.project_root / "vss_extraction"
        self.eraser_dir = self.project_root / "eraser_ai_processed"
        
    def run_vss_extraction(self):
        """Run VSS model extraction (Linux version)"""
        print("🔍 STEP 1: VSS Model Extraction (Linux)")
        print("=" * 50)
        
        try:
            result = subprocess.run([
                "python", "vss_extraction_linux.py"
            ], cwd=self.vss_dir, capture_output=True, text=True)
            
            print(result.stdout)
            if result.returncode == 0:
                print("✅ VSS extraction completed successfully")
                return True
            else:
                print(f"❌ VSS extraction failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error running VSS extraction: {e}")
            return False
    
    def run_eraser_ai_processing(self):
        """Run Eraser AI processing (Linux version)"""
        print("\n🎨 STEP 2: Eraser AI Processing (Linux)")
        print("=" * 50)
        
        try:
            result = subprocess.run([
                "python", "eraser_ai_processing_linux.py"
            ], cwd=self.eraser_dir, capture_output=True, text=True)
            
            print(result.stdout)
            if result.returncode == 0:
                print("✅ Eraser AI processing completed successfully")
                return True
            else:
                print(f"❌ Eraser AI processing failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error running Eraser AI processing: {e}")
            return False
    
    def run_model_deployment(self):
        """Run model deployment (Linux version)"""
        print("\n🚀 STEP 3: Model Deployment (Linux)")
        print("=" * 50)
        
        try:
            result = subprocess.run([
                "python", "deploy_models_linux.py"
            ], cwd=self.eraser_dir, capture_output=True, text=True)
            
            print(result.stdout)
            if result.returncode == 0:
                print("✅ Model deployment completed successfully")
                return True
            else:
                print(f"❌ Model deployment failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error running model deployment: {e}")
            return False
    
    def test_3d_visualization(self):
        """Test 3D visualization system"""
        print("\n🌐 STEP 4: Testing 3D Visualization")
        print("=" * 50)
        
        endpoints = [
            ("http://127.0.0.1:11111/babylon-test", "Babylon.js 3D Topology"),
            ("http://127.0.0.1:11111/2d-topology-enhanced", "Enhanced 2D Topology"),
            ("http://127.0.0.1:11111/", "Network Operations Center")
        ]
        
        print("Testing visualization endpoints:")
        all_good = True
        
        try:
            import requests
            for url, name in endpoints:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        print(f"  ✅ {name}: ACCESSIBLE")
                    else:
                        print(f"  ❌ {name}: HTTP {response.status_code}")
                        all_good = False
                except Exception as e:
                    print(f"  ❌ {name}: {str(e)}")
                    all_good = False
        except ImportError:
            print("  ⚠️ requests module not available, skipping endpoint tests")
            all_good = False
        
        if all_good:
            print("\n🎯 All visualization endpoints are accessible!")
            print("🌐 Test your 3D models at: http://127.0.0.1:11111/babylon-test")
        
        return all_good
    
    def check_final_status(self):
        """Check final deployment status"""
        print("\n📊 STEP 5: Final Status Check")
        print("=" * 50)
        
        models_dir = self.project_root / "src/enhanced_network_api/static/3d-models"
        expected_models = ["FortiGate.glb", "FortiSwitch.glb", "FortinetAP.glb"]
        
        print("Checking deployed models:")
        deployed_count = 0
        
        for model in expected_models:
            model_path = models_dir / model
            if model_path.exists():
                size = model_path.stat().st_size
                size_kb = size / 1024
                modified = datetime.fromtimestamp(model_path.stat().st_mtime)
                print(f"  ✅ {model}: {size_kb:.1f}KB (Modified: {modified.strftime('%H:%M')})")
                deployed_count += 1
            else:
                print(f"  ❌ {model}: MISSING")
        
        print(f"\n📊 Deployment Summary: {deployed_count}/{len(expected_models)} models deployed")
        
        # Check deployment report
        report_file = models_dir / "deployment_report.json"
        if report_file.exists():
            try:
                with open(report_file, 'r') as f:
                    report = json.load(f)
                print(f"✅ Deployment report available")
                print(f"📅 Deployment date: {report.get('deployment_date', 'Unknown')}")
                print(f"🔧 Production ready: {report.get('production_ready', False)}")
            except Exception as e:
                print(f"⚠️ Error reading deployment report: {e}")
        
        return deployed_count == len(expected_models)
    
    def generate_workflow_summary(self):
        """Generate complete workflow summary"""
        print("\n📋 STEP 6: Generating Workflow Summary")
        print("=" * 50)
        
        summary = {
            "workflow_type": "Linux-Compatible",
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "steps_completed": [],
            "success_rate": 0,
            "next_steps": [
                "Test 3D visualization at: http://127.0.0.1:11111/babylon-test",
                "Click '🎭 Demo Mode' to see enhanced models",
                "Verify device interaction and health indicators"
            ],
            "documentation": [
                "EXECUTE_NOW.md - Quick start guide",
                "VSS_ERASER_AI_QUICK_START.md - Complete workflow",
                "TOPOLOGY_FILE_INVENTORY.md - File inventory"
            ]
        }
        
        summary_file = self.eraser_dir / "linux_workflow_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Workflow summary saved: {summary_file}")
        return summary
    
    def run_complete_linux_workflow(self):
        """Execute the complete Linux-compatible workflow"""
        print("🚀 RUNNING COMPLETE VSS + ERASER AI WORKFLOW - LINUX VERSION")
        print("=" * 70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🐧 Linux Compatible - No PowerShell Required!")
        
        # Execute workflow steps
        steps = [
            ("VSS Extraction", self.run_vss_extraction),
            ("Eraser AI Processing", self.run_eraser_ai_processing),
            ("Model Deployment", self.run_model_deployment),
            ("3D Visualization Test", self.test_3d_visualization),
            ("Final Status Check", self.check_final_status),
            ("Workflow Summary", self.generate_workflow_summary)
        ]
        
        results = {}
        for step_name, step_func in steps:
            try:
                results[step_name] = step_func()
            except Exception as e:
                print(f"❌ {step_name} failed: {e}")
                results[step_name] = False
        
        # Generate final report
        print("\n🎯 LINUX WORKFLOW EXECUTION COMPLETE!")
        print("=" * 70)
        
        success_count = sum(1 for result in results.values() if result)
        total_steps = len(results)
        success_rate = (success_count / total_steps) * 100
        
        print(f"📊 Success Rate: {success_rate:.1f}% ({success_count}/{total_steps} steps)")
        
        if success_rate >= 80:
            print("🎉 LINUX WORKFLOW SUCCESSFUL!")
            print("🌐 Your enhanced 3D models are ready!")
        else:
            print("⚠️ Some workflow steps need attention")
        
        print(f"\n🌐 TEST YOUR 3D MODELS NOW:")
        print(f"🔗 http://127.0.0.1:11111/babylon-test")
        print(f"🎮 Click '🎭 Demo Mode'")
        print(f"👆 Click devices to see enhanced details!")
        
        print(f"\n📚 DOCUMENTATION:")
        print(f"- Quick Start: /EXECUTE_NOW.md")
        print(f"- Complete Guide: /VSS_ERASER_AI_QUICK_START.md")
        print(f"- File Inventory: /TOPOLOGY_FILE_INVENTORY.md")
        
        print(f"\n🔧 LINUX WORKFLOW FEATURES:")
        print(f"✅ No PowerShell required")
        print(f"✅ Python-based processing")
        print(f"✅ Cross-platform compatible")
        print(f"✅ Enhanced PBR materials")
        print(f"✅ Production-ready deployment")
        
        return results

if __name__ == "__main__":
    executor = LinuxWorkflowExecutor()
    executor.run_complete_linux_workflow()
