# 3D Model Deployment Script
# Generated on: 2025-11-21 14:40:36

import shutil
import os
from pathlib import Path

# Deployment configuration
source_dir = Path("/home/keith/enhanced-network-api-corporate/eraser_ai_processed/eraser_ai_output")
target_dir = Path("/home/keith/enhanced-network-api-corporate/src/enhanced_network_api/static/3d-models")
backup_dir = Path("/home/keith/enhanced-network-api-corporate/src/enhanced_network_api/static/3d-models/backup")

# Models to deploy
models = {
    "FortiGate_600E_enhanced.glb": "FortiGate.glb",
    "FortiSwitch_148E_enhanced.glb": "FortiSwitch.glb",
    "FortiAP_432F_enhanced.glb": "FortinetAP.glb"
}

print("🚀 Deploying VSS + Eraser AI enhanced models...")

# Create backup of existing models
if target_dir.exists():
    print("📦 Creating backup of existing models...")
    backup_dir.mkdir(exist_ok=True)
    for model_file in target_dir.glob("*.glb"):
        shutil.copy2(model_file, backup_dir / model_file.name)
        print(f"  ✅ Backed up: {model_file.name}")

# Deploy enhanced models
deployed_count = 0
for source_name, target_name in models.items():
    source_path = source_dir / source_name
    target_path = target_dir / target_name
    
    if source_path.exists():
        shutil.copy2(source_path, target_path)
        print(f"  ✅ Deployed: {target_name}")
        deployed_count += 1
    else:
        print(f"  ❌ Source not found: {source_name}")

print(f"\n🎯 Deployment Summary: {deployed_count}/{len(models)} models deployed")

if deployed_count == len(models):
    print("🎉 All models deployed successfully!")
    print("🌐 Test your 3D topology at: http://127.0.0.1:11111/babylon-test")
else:
    print("⚠️ Some models failed to deploy")
