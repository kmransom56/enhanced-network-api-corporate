#!/usr/bin/env python3
"""
Test script to validate GitHub Actions workflow syntax
"""

import yaml
import json
from pathlib import Path

def validate_workflow(workflow_path):
    """Validate a GitHub Actions workflow file."""
    try:
        with open(workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        print(f"✅ {workflow_path.name} - Valid YAML syntax")
        
        # Check for common issues
        issues = []
        
        # Check env section
        if 'env' in workflow:
            for key, value in workflow['env'].items():
                if isinstance(value, str) and ('${{' in value and 'secrets.' in value):
                    issues.append(f"Direct secret access in env: {key}")
        
        # Check jobs
        if 'jobs' in workflow:
            for job_name, job in workflow['jobs'].items():
                if 'steps' in job:
                    for step in job['steps']:
                        if 'if' in step:
                            if 'secrets.' in step['if']:
                                issues.append(f"Direct secret access in if condition: {step.get('name', 'unnamed')}")
        
        if issues:
            print(f"⚠️  Issues found in {workflow_path.name}:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print(f"✅ {workflow_path.name} - No syntax issues found")
        
        return len(issues) == 0
        
    except yaml.YAMLError as e:
        print(f"❌ {workflow_path.name} - YAML syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ {workflow_path.name} - Error: {e}")
        return False

def main():
    """Validate all workflow files."""
    print("🔍 Validating GitHub Actions Workflows")
    print("=" * 50)
    
    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        print("❌ .github/workflows directory not found")
        return
    
    workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
    
    if not workflow_files:
        print("❌ No workflow files found")
        return
    
    all_valid = True
    for workflow_file in workflow_files:
        valid = validate_workflow(workflow_file)
        all_valid = all_valid and valid
    
    print("=" * 50)
    if all_valid:
        print("🎉 All workflows are valid!")
    else:
        print("⚠️  Some workflows have issues")
    
    return all_valid

if __name__ == "__main__":
    main()
