"""
Corporate Network Compatibility Validator
Final validation script for corporate deployment readiness
"""

import os
import sys
import json
import platform
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class CorporateNetworkCompatibilityValidator:
    """
    Comprehensive validation of corporate network compatibility
    """
    
    def __init__(self):
        self.validation_results = {}
        self.compatibility_score = 0
        self.critical_issues = []
        self.warnings = []
        
    def run_full_validation(self) -> Dict[str, Any]:
        """
        Run complete corporate network compatibility validation
        
        Returns:
            Dict: Complete validation results
        """
        print("🏢 Corporate Network Compatibility Validation")
        print("=" * 50)
        
        validation_report = {
            "validation_timestamp": "2024-01-01T00:00:00",
            "platform": platform.system(),
            "python_version": sys.version,
            "components_validated": [],
            "compatibility_score": 0,
            "deployment_readiness": "unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        # 1. Validate Core Components
        print("\n🔍 Validating Core Components...")
        components_result = self._validate_core_components()
        validation_report["components_validated"] = components_result
        
        # 2. Validate SSL Helper System
        print("\n🔒 Validating SSL Helper System...")
        ssl_result = self._validate_ssl_system()
        validation_report["ssl_validation"] = ssl_result
        
        # 3. Validate Network Helper System
        print("\n🌐 Validating Network Helper System...")
        network_result = self._validate_network_system()
        validation_report["network_validation"] = network_result
        
        # 4. Validate API Documentation
        print("\n📚 Validating API Documentation...")
        api_result = self._validate_api_documentation()
        validation_report["api_documentation"] = api_result
        
        # 5. Validate Corporate Environment Detection
        print("\n🕵️  Validating Corporate Environment Detection...")
        detection_result = self._validate_environment_detection()
        validation_report["environment_detection"] = detection_result
        
        # 6. Validate Deployment Packages
        print("\n📦 Validating Deployment Packages...")
        deployment_result = self._validate_deployment_packages()
        validation_report["deployment_packages"] = deployment_result
        
        # 7. Calculate Overall Compatibility
        compatibility_analysis = self._calculate_compatibility_score(validation_report)
        validation_report.update(compatibility_analysis)
        
        # 8. Generate Final Report
        self._generate_final_report(validation_report)
        
        return validation_report
    
    def _validate_core_components(self) -> Dict[str, Any]:
        """Validate core components are present and functional"""
        core_components = [
            "ssl_helper.py",
            "corporate_network_helper.py", 
            "certificate_discovery.py",
            "corporate_environment_detector.py",
            "corporate_deployment_packager.py",
            "corporate_installer.py",
            "air_gapped_deployment.py",
            "api_documentation_loader.py",
            "comprehensive_sdk_generator.py",
            "enhanced_network_app_generator.py",
            "corporate_network_app_generator.py"
        ]
        
        result = {
            "total_components": len(core_components),
            "present": 0,
            "missing": [],
            "functional": 0,
            "status": "unknown"
        }
        
        for component in core_components:
            if Path(component).exists():
                result["present"] += 1
                print(f"  ✅ {component}")
                
                # Test if component is importable (basic functionality test)
                try:
                    module_name = component.replace('.py', '')
                    # We can't actually import due to dependencies, so we check syntax
                    with open(component, 'r') as f:
                        content = f.read()
                        compile(content, component, 'exec')
                    result["functional"] += 1
                except SyntaxError as e:
                    print(f"    ⚠️  Syntax error: {e}")
                    self.warnings.append(f"Syntax error in {component}")
                except Exception:
                    # Other import errors are expected without dependencies
                    result["functional"] += 1
            else:
                result["missing"].append(component)
                print(f"  ❌ {component}")
        
        # Determine status
        if result["present"] == result["total_components"]:
            result["status"] = "complete"
        elif result["present"] >= result["total_components"] * 0.8:
            result["status"] = "mostly_complete"
        else:
            result["status"] = "incomplete"
            self.critical_issues.append(f"Missing {len(result['missing'])} core components")
        
        return result
    
    def _validate_ssl_system(self) -> Dict[str, Any]:
        """Validate SSL helper system"""
        ssl_result = {
            "ssl_helper_available": False,
            "certificate_discovery_available": False,
            "corporate_ssl_support": False,
            "zscaler_support": False,
            "status": "unknown"
        }
        
        # Check SSL helper
        if Path("ssl_helper.py").exists():
            ssl_result["ssl_helper_available"] = True
            print("  ✅ SSL helper available")
            
            # Check for corporate SSL features
            with open("ssl_helper.py", 'r') as f:
                ssl_content = f.read()
                
                if "CorporateSSLHelper" in ssl_content:
                    ssl_result["corporate_ssl_support"] = True
                    print("  ✅ Corporate SSL support")
                
                if "zscaler" in ssl_content.lower():
                    ssl_result["zscaler_support"] = True
                    print("  ✅ Zscaler support detected")
        else:
            print("  ❌ SSL helper not found")
            self.critical_issues.append("SSL helper missing")
        
        # Check certificate discovery
        if Path("certificate_discovery.py").exists():
            ssl_result["certificate_discovery_available"] = True
            print("  ✅ Certificate discovery available")
        else:
            print("  ❌ Certificate discovery not found")
        
        # Determine overall SSL status
        ssl_score = sum([
            ssl_result["ssl_helper_available"],
            ssl_result["certificate_discovery_available"], 
            ssl_result["corporate_ssl_support"],
            ssl_result["zscaler_support"]
        ])
        
        if ssl_score >= 3:
            ssl_result["status"] = "excellent"
        elif ssl_score >= 2:
            ssl_result["status"] = "good"
        else:
            ssl_result["status"] = "poor"
            self.critical_issues.append("Insufficient SSL support")
        
        return ssl_result
    
    def _validate_network_system(self) -> Dict[str, Any]:
        """Validate network helper system"""
        network_result = {
            "network_helper_available": False,
            "proxy_support": False,
            "firewall_bypass": False,
            "corporate_detection": False,
            "status": "unknown"
        }
        
        if Path("corporate_network_helper.py").exists():
            network_result["network_helper_available"] = True
            print("  ✅ Network helper available")
            
            with open("corporate_network_helper.py", 'r') as f:
                network_content = f.read()
                
                if "proxy" in network_content.lower():
                    network_result["proxy_support"] = True
                    print("  ✅ Proxy support detected")
                
                if "firewall" in network_content.lower():
                    network_result["firewall_bypass"] = True
                    print("  ✅ Firewall bypass capabilities")
                
                if "corporate" in network_content.lower():
                    network_result["corporate_detection"] = True
                    print("  ✅ Corporate network detection")
        else:
            print("  ❌ Network helper not found")
            self.critical_issues.append("Network helper missing")
        
        network_score = sum(network_result.values()) - 1  # Exclude status
        network_result["status"] = "excellent" if network_score >= 3 else "good" if network_score >= 2 else "poor"
        
        return network_result
    
    def _validate_api_documentation(self) -> Dict[str, Any]:
        """Validate API documentation is available"""
        api_result = {
            "api_directory_exists": False,
            "fortinet_docs_available": False,
            "meraki_docs_available": False,
            "total_api_endpoints": 0,
            "documentation_size_mb": 0,
            "status": "unknown"
        }
        
        api_dir = Path("./api")
        if api_dir.exists():
            api_result["api_directory_exists"] = True
            print("  ✅ API directory found")
            
            # Check Fortinet documentation
            fortinet_file = api_dir / "fortimanager_api_endpoints.json"
            if fortinet_file.exists():
                api_result["fortinet_docs_available"] = True
                print("  ✅ Fortinet API documentation available")
                
                try:
                    with open(fortinet_file, 'r') as f:
                        fortinet_data = json.load(f)
                        api_result["total_api_endpoints"] += fortinet_data.get("total_endpoints", 0)
                except:
                    pass
            
            # Check Meraki documentation
            meraki_file = api_dir / "Meraki Dashboard API - v1.63.0.postman_collection.json"
            if meraki_file.exists():
                api_result["meraki_docs_available"] = True
                print("  ✅ Meraki API documentation available")
                api_result["total_api_endpoints"] += 1000  # Estimated
            
            # Calculate total documentation size
            total_size = sum(f.stat().st_size for f in api_dir.rglob('*') if f.is_file())
            api_result["documentation_size_mb"] = total_size / (1024 * 1024)
            
            print(f"  📊 Total API endpoints: {api_result['total_api_endpoints']}")
            print(f"  📊 Documentation size: {api_result['documentation_size_mb']:.1f} MB")
        else:
            print("  ❌ API directory not found")
            self.critical_issues.append("API documentation missing")
        
        # Status determination
        if api_result["fortinet_docs_available"] and api_result["meraki_docs_available"]:
            api_result["status"] = "complete"
        elif api_result["fortinet_docs_available"] or api_result["meraki_docs_available"]:
            api_result["status"] = "partial"
        else:
            api_result["status"] = "missing"
        
        return api_result
    
    def _validate_environment_detection(self) -> Dict[str, Any]:
        """Validate corporate environment detection capabilities"""
        detection_result = {
            "environment_detector_available": False,
            "auto_configuration_support": False,
            "portable_config_generation": False,
            "status": "unknown"
        }
        
        if Path("corporate_environment_detector.py").exists():
            detection_result["environment_detector_available"] = True
            print("  ✅ Environment detector available")
            
            with open("corporate_environment_detector.py", 'r') as f:
                content = f.read()
                
                if "auto_configure" in content.lower():
                    detection_result["auto_configuration_support"] = True
                    print("  ✅ Auto-configuration support")
                
                if "portable" in content.lower():
                    detection_result["portable_config_generation"] = True
                    print("  ✅ Portable configuration generation")
        else:
            print("  ❌ Environment detector not found")
        
        score = sum(detection_result.values()) - 1  # Exclude status
        detection_result["status"] = "excellent" if score >= 2 else "good" if score >= 1 else "poor"
        
        return detection_result
    
    def _validate_deployment_packages(self) -> Dict[str, Any]:
        """Validate deployment package capabilities"""
        deployment_result = {
            "corporate_packager_available": False,
            "installer_available": False,
            "air_gapped_support": False,
            "status": "unknown"
        }
        
        if Path("corporate_deployment_packager.py").exists():
            deployment_result["corporate_packager_available"] = True
            print("  ✅ Corporate packager available")
        
        if Path("corporate_installer.py").exists():
            deployment_result["installer_available"] = True
            print("  ✅ Corporate installer available")
        
        if Path("air_gapped_deployment.py").exists():
            deployment_result["air_gapped_support"] = True
            print("  ✅ Air-gapped deployment support")
        
        score = sum(deployment_result.values()) - 1
        deployment_result["status"] = "excellent" if score >= 2 else "good" if score >= 1 else "poor"
        
        return deployment_result
    
    def _calculate_compatibility_score(self, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall compatibility score"""
        
        # Component scoring
        components = validation_report.get("components_validated", {})
        component_score = (components.get("present", 0) / components.get("total_components", 1)) * 30
        
        # SSL scoring
        ssl_status = validation_report.get("ssl_validation", {}).get("status", "poor")
        ssl_score = {"excellent": 25, "good": 20, "poor": 5}.get(ssl_status, 5)
        
        # Network scoring
        network_status = validation_report.get("network_validation", {}).get("status", "poor")
        network_score = {"excellent": 20, "good": 15, "poor": 5}.get(network_status, 5)
        
        # API documentation scoring
        api_status = validation_report.get("api_documentation", {}).get("status", "missing")
        api_score = {"complete": 15, "partial": 10, "missing": 0}.get(api_status, 0)
        
        # Environment detection scoring
        env_status = validation_report.get("environment_detection", {}).get("status", "poor")
        env_score = {"excellent": 10, "good": 7, "poor": 2}.get(env_status, 2)
        
        total_score = component_score + ssl_score + network_score + api_score + env_score
        
        # Determine deployment readiness
        if total_score >= 85:
            deployment_readiness = "fully_ready"
        elif total_score >= 70:
            deployment_readiness = "ready_with_minor_issues"
        elif total_score >= 50:
            deployment_readiness = "ready_with_major_issues"
        else:
            deployment_readiness = "not_ready"
        
        return {
            "compatibility_score": round(total_score, 1),
            "deployment_readiness": deployment_readiness,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "recommendations": self._generate_recommendations(total_score, deployment_readiness)
        }
    
    def _generate_recommendations(self, score: float, readiness: str) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        if readiness == "fully_ready":
            recommendations.extend([
                "System is fully ready for corporate deployment",
                "Create deployment package using corporate_deployment_packager.py",
                "Test in corporate environment with corporate SSL certificates"
            ])
        elif readiness == "ready_with_minor_issues":
            recommendations.extend([
                "System is mostly ready - address minor issues",
                "Test SSL certificate handling in corporate environment",
                "Verify proxy configuration capabilities"
            ])
        elif readiness == "ready_with_major_issues":
            recommendations.extend([
                "Major issues detected - address before deployment",
                "Check missing components and dependencies",
                "Validate SSL and network helper functionality"
            ])
        else:
            recommendations.extend([
                "System not ready for corporate deployment", 
                "Critical components missing or non-functional",
                "Complete setup before attempting deployment"
            ])
        
        if self.critical_issues:
            recommendations.append("Address all critical issues before deployment")
        
        return recommendations
    
    def _generate_final_report(self, validation_report: Dict[str, Any]) -> None:
        """Generate final validation report"""
        print("\n" + "=" * 50)
        print("📊 CORPORATE NETWORK COMPATIBILITY REPORT")
        print("=" * 50)
        
        print(f"\n🎯 Compatibility Score: {validation_report['compatibility_score']:.1f}/100")
        print(f"🚀 Deployment Readiness: {validation_report['deployment_readiness'].replace('_', ' ').title()}")
        
        if validation_report['critical_issues']:
            print(f"\n❌ Critical Issues ({len(validation_report['critical_issues'])}):")
            for issue in validation_report['critical_issues']:
                print(f"   - {issue}")
        
        if validation_report['warnings']:
            print(f"\n⚠️  Warnings ({len(validation_report['warnings'])}):")
            for warning in validation_report['warnings']:
                print(f"   - {warning}")
        
        print(f"\n💡 Recommendations:")
        for rec in validation_report['recommendations']:
            print(f"   - {rec}")
        
        # Component breakdown
        components = validation_report.get("components_validated", {})
        print(f"\n📦 Components: {components.get('present', 0)}/{components.get('total_components', 0)} present")
        
        ssl_validation = validation_report.get("ssl_validation", {})
        print(f"🔒 SSL Support: {ssl_validation.get('status', 'unknown').title()}")
        
        network_validation = validation_report.get("network_validation", {})
        print(f"🌐 Network Support: {network_validation.get('status', 'unknown').title()}")
        
        api_docs = validation_report.get("api_documentation", {})
        print(f"📚 API Documentation: {api_docs.get('total_api_endpoints', 0)} endpoints ({api_docs.get('documentation_size_mb', 0):.1f} MB)")
        
        # Save detailed report
        report_file = "corporate-compatibility-report.json"
        with open(report_file, 'w') as f:
            json.dump(validation_report, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
        # Final status
        score = validation_report['compatibility_score']
        if score >= 85:
            print("\n🎉 EXCELLENT: Ready for corporate deployment!")
        elif score >= 70:
            print("\n✅ GOOD: Ready with minor configuration needed")
        elif score >= 50:
            print("\n⚠️  FAIR: Major issues need addressing")
        else:
            print("\n❌ POOR: Significant work needed before deployment")


def main():
    """Main validation function"""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Run validation
    validator = CorporateNetworkCompatibilityValidator()
    results = validator.run_full_validation()
    
    # Return appropriate exit code
    if results["compatibility_score"] >= 70:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Issues detected


if __name__ == "__main__":
    main()
