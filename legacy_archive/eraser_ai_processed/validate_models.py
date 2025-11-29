# 3D Model Validation Script
# Generated on: 2025-11-21 14:40:36

import json
import os
from pathlib import Path

def validate_glb_model(model_path):
    """Validate GLB model format and structure"""
    print(f"Validating {model_path}...")
    
    if not os.path.exists(model_path):
        print(f"  ❌ Model file not found")
        return False
    
    # Check file size (should be reasonable for web deployment)
    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    if size_mb > 50:  # Warn if too large
        print(f"  ⚠️ Large model size: {size_mb:.1f}MB")
    else:
        print(f"  ✅ Model size: {size_mb:.1f}MB")
    
    # Basic GLB validation (check for GLTF magic bytes)
    with open(model_path, 'rb') as f:
        header = f.read(4)
        if header == b'glTF':
            print(f"  ✅ Valid GLB format")
        else:
            print(f"  ❌ Invalid GLB format")
            return False
    
    return True

# Models to validate
models = [
    "FortiGate.glb",
    "FortiSwitch.glb", 
    "FortinetAP.glb"
]

print("🔍 Validating 3D Models...")
valid_count = 0

for model in models:
    if validate_glb_model(model):
        valid_count += 1

print(f"\n📊 Validation Summary: {valid_count}/{len(models)} models valid")

if valid_count == len(models):
    print("🎉 All models ready for deployment!")
else:
    print("⚠️ Some models need attention")
