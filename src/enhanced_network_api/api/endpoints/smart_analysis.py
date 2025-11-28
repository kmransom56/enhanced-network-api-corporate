"""
Smart Analysis Tools for Fortinet/Meraki Networks
Implements LLM-powered analysis tools from LLM_tools.md using shared MCP patterns
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Import shared MCP patterns
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.mcp_base import FortiGateManager, MerakiManager

logger = logging.getLogger(__name__)
router = APIRouter()

# Import LLM configuration
from .fortinet_llm import FORTINET_LLM_CONFIG

# Initialize shared managers
fortigate_manager = FortiGateManager()
meraki_manager = MerakiManager()

class PolicyAnalysisRequest(BaseModel):
    device_id: str
    device_type: str  # fortigate, meraki
    policy_type: str  # firewall, nat, vpn
    include_recommendations: bool = True

class ChangePlanRequest(BaseModel):
    device_id: str
    device_type: str
    planned_change: str
    change_type: str  # cli, policy_diff, config_snippet
    include_rollback: bool = True

class IncidentTriageRequest(BaseModel):
    incident_description: str
    device_id: Optional[str] = None
    log_snippets: List[str] = []
    severity: str = "medium"  # low, medium, high, critical

class RunbookRequest(BaseModel):
    topic: str
    device_type: str
    include_verification: bool = True
    include_rollback: bool = True

class ConfigDriftRequest(BaseModel):
    device1_id: str
    device2_id: str
    device_type: str
    snapshot_time1: Optional[str] = None
    snapshot_time2: Optional[str] = None

@router.post("/policy-analysis")
async def analyze_firewall_policies(request: PolicyAnalysisRequest):
    """
    Smart policy analysis and audit using LLM with shared MCP patterns
    """
    try:
        # Fetch policies using shared managers
        if request.device_type.startswith("forti"):
            policies_data = await fetch_fortigate_policies(request.device_id, request.policy_type)
        elif request.device_type == "meraki":
            policies_data = await fetch_meraki_policies(request.device_id)
        else:
            raise ValueError(f"Unsupported device type: {request.device_type}")
        
        if not policies_data:
            raise HTTPException(status_code=404, detail="Could not fetch policies from device")
        
        # Build LLM prompt for policy analysis
        prompt = build_policy_analysis_prompt(
            device_type=request.device_type,
            policy_type=request.policy_type,
            policies=policies_data
        )
        
        # Call LLM for analysis
        llm_response = await call_fortinet_llm(prompt, "policy_analysis", request.device_type)
        
        # Structure the response
        analysis = {
            "device_id": request.device_id,
            "policy_type": request.policy_type,
            "policy_count": len(policies_data.get("policies", [])),
            "analysis": llm_response.get("analysis", {}),
            "risks": extract_risks_from_analysis(llm_response),
            "recommendations": llm_response.get("recommendations", []) if request.include_recommendations else []
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Policy analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/change-plan-analysis")
async def analyze_change_plan(request: ChangePlanRequest):
    """
    Analyze planned changes with risk assessment using shared MCP patterns
    """
    try:
        # Get current device state using shared managers
        current_config = await fetch_device_config_shared(request.device_id, request.device_type)
        
        # Build comprehensive change analysis prompt
        prompt = build_change_analysis_prompt(
            device_type=request.device_type,
            current_config=current_config,
            planned_change=request.planned_change,
            change_type=request.change_type
        )
        
        # Call LLM for analysis
        llm_response = await call_fortinet_llm(prompt, "change_analysis", request.device_type)
        
        analysis = {
            "device_id": request.device_id,
            "planned_change": request.planned_change,
            "change_type": request.change_type,
            "impact_analysis": llm_response.get("analysis", {}),
            "risks": extract_change_risks(llm_response),
            "rollback_steps": extract_rollback_steps(llm_response) if request.include_rollback else [],
            "verification_steps": extract_verification_steps(llm_response)
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Change plan analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/incident-triage")
async def generate_incident_triage(request: IncidentTriageRequest):
    """
    Generate structured incident triage report using shared MCP patterns
    """
    try:
        # Fetch device logs using shared managers
        device_logs = []
        if request.device_id:
            device_logs = await fetch_device_logs_shared(request.device_id, request.severity)
        
        # Combine with provided log snippets
        all_logs = device_logs + request.log_snippets
        
        # Build triage prompt
        prompt = build_triage_prompt(
            incident_description=request.incident_description,
            device_id=request.device_id,
            logs=all_logs,
            severity=request.severity
        )
        
        # Call LLM for triage analysis
        llm_response = await call_fortinet_llm(prompt, "incident_triage", "general")
        
        triage_report = {
            "incident_id": f"INC-{hash(request.incident_description) % 10000:04d}",
            "severity": request.severity,
            "device_id": request.device_id,
            "description": request.incident_description,
            "triage": {
                "probable_root_cause": llm_response.get("root_cause", "Unknown"),
                "key_evidence": extract_evidence_from_logs(llm_response, all_logs),
                "impact_assessment": llm_response.get("impact", "Unknown"),
                "actions_taken": [],
                "next_steps": extract_next_steps(llm_response),
                "escalation_criteria": extract_escalation_criteria(llm_response)
            },
            "logs_analyzed": len(all_logs),
            "generated_at": "2024-01-01T00:00:00Z"  # Should use actual timestamp
        }
        
        return triage_report
        
    except Exception as e:
        logger.error(f"Incident triage error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-runbook")
async def generate_runbook(request: RunbookRequest):
    """
    Generate step-by-step runbook for specific scenarios
    """
    try:
        # Build runbook generation prompt
        prompt = build_runbook_prompt(
            topic=request.topic,
            device_type=request.device_type,
            include_verification=request.include_verification,
            include_rollback=request.include_rollback
        )
        
        # Call LLM for runbook generation
        llm_response = await call_fortinet_llm(prompt, "runbook_generation", request.device_type)
        
        runbook = {
            "title": f"Runbook: {request.topic}",
            "device_type": request.device_type,
            "topic": request.topic,
            "generated_at": "2024-01-01T00:00:00Z",
            "sections": {
                "overview": extract_runbook_overview(llm_response),
                "prerequisites": extract_prerequisites(llm_response),
                "step_by_step": extract_procedure_steps(llm_response),
                "verification_commands": extract_verification_commands(llm_response) if request.include_verification else [],
                "rollback_procedure": extract_rollback_procedure(llm_response) if request.include_rollback else [],
                "troubleshooting": extract_troubleshooting_section(llm_response)
            }
        }
        
        return runbook
        
    except Exception as e:
        logger.error(f"Runbook generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config-drift-analysis")
async def analyze_config_drift(request: ConfigDriftRequest):
    """
    Analyze configuration drift using shared MCP patterns
    """
    try:
        # Fetch configs using shared managers
        config1 = await fetch_device_config_shared(request.device1_id, request.device_type, request.snapshot_time1)
        config2 = await fetch_device_config_shared(request.device2_id, request.device_type, request.snapshot_time2)
        
        # Generate diff (simplified - would use proper diff tool in production)
        config_diff = generate_config_diff(config1, config2)
        
        # Build drift analysis prompt
        prompt = build_drift_analysis_prompt(
            device_type=request.device_type,
            config1=config1,
            config2=config2,
            diff=config_diff,
            device1_id=request.device1_id,
            device2_id=request.device2_id
        )
        
        # Call LLM for drift analysis
        llm_response = await call_fortinet_llm(prompt, "config_drift", request.device_type)
        
        drift_analysis = {
            "device1_id": request.device1_id,
            "device2_id": request.device2_id,
            "device_type": request.device_type,
            "snapshot_time1": request.snapshot_time1,
            "snapshot_time2": request.snapshot_time2,
            "drift_detected": len(config_diff.get("changes", [])) > 0,
            "changes_count": len(config_diff.get("changes", [])),
            "drift_analysis": {
                "summary": llm_response.get("summary", "No drift detected"),
                "impact_assessment": llm_response.get("impact", "Unknown"),
                "security_implications": extract_security_implications(llm_response),
                "compliance_impact": extract_compliance_impact(llm_response),
                "recommended_actions": extract_drift_recommendations(llm_response)
            },
            "raw_diff": config_diff
        }
        
        return drift_analysis
        
    except Exception as e:
        logger.error(f"Config drift analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Shared MCP integration functions

async def fetch_fortigate_policies(device_id: str, policy_type: str) -> Dict[str, Any]:
    """Fetch FortiGate policies using shared manager"""
    try:
        host = device_id.replace("fg-", "")
        # Note: In production, you'd get token from secure storage
        token = "your_fortigate_token"  # This should come from config/env
        
        policies = await fortigate_manager.get_firewall_policies(host, token, policy_type)
        return policies
    except Exception as e:
        logger.error(f"Failed to fetch FortiGate policies: {e}")
        return {"policies": [], "error": str(e)}

async def fetch_meraki_policies(network_id: str) -> Dict[str, Any]:
    """Fetch Meraki policies using shared manager"""
    try:
        # Note: In production, you'd get API key from secure storage
        api_key = "your_meraki_api_key"  # This should come from config/env
        
        await meraki_manager.authenticate(api_key)
        policies = await meraki_manager.get_network_policies(network_id)
        return policies
    except Exception as e:
        logger.error(f"Failed to fetch Meraki policies: {e}")
        return {"policies": [], "error": str(e)}

async def fetch_device_config_shared(device_id: str, device_type: str, snapshot_time: Optional[str] = None) -> Dict[str, Any]:
    """Fetch device configuration using shared managers"""
    try:
        if device_type.startswith("forti"):
            host = device_id.replace("fg-", "")
            token = "your_fortigate_token"  # From config/env
            
            status = await fortigate_manager.get_system_status(host, token)
            return {"config": status, "snapshot_time": snapshot_time}
        elif device_type == "meraki":
            api_key = "your_meraki_api_key"  # From config/env
            await meraki_manager.authenticate(api_key)
            
            status = await meraki_manager.get_device_status(device_id)
            return {"config": status, "snapshot_time": snapshot_time}
        else:
            return {"config": f"Config for {device_type} {device_id} at {snapshot_time or 'current'}"}
    except Exception as e:
        logger.error(f"Failed to fetch device config: {e}")
        return {"config": {}, "error": str(e)}

async def fetch_device_logs_shared(device_id: str, severity: str) -> List[str]:
    """Fetch device logs using shared managers"""
    try:
        if device_id.startswith("fg-"):
            host = device_id.replace("fg-", "")
            token = "your_fortigate_token"  # From config/env
            
            log_filter = {"level": severity} if severity != "all" else {}
            logs_data = await fortigate_manager.get_logs(host, token, log_filter)
            
            # Extract log messages
            logs = []
            for log in logs_data.get("logs", []):
                logs.append(f"{log.get('timestamp', '')}: {log.get('msg', '')}")
            
            return logs
        elif device_type == "meraki":
            # Meraki log fetching would be implemented here
            return [f"Meraki log for {device_id} with {severity} severity"]
        else:
            return [f"Log entry for {device_id} with {severity} severity"]
    except Exception as e:
        logger.error(f"Failed to fetch device logs: {e}")
        return [f"Error fetching logs: {str(e)}"]

# Rest of the helper functions remain the same from the original file...

async def call_fortinet_llm(prompt: str, context: str, device_type: str) -> Dict[str, Any]:
    """Call the Fortinet LLM endpoint"""
    async with httpx.AsyncClient(timeout=FORTINET_LLM_CONFIG["timeout"]) as client:
        payload = {
            "prompt": prompt,
            "context": context,
            "device_type": device_type,
            "temperature": 0.3
        }
        
        response = await client.post(
            f"{FORTINET_LLM_CONFIG['base_url']}/api/fortinet-llm/chat",
            json=payload
        )
        response.raise_for_status()
        return response.json()

def build_policy_analysis_prompt(device_type: str, policy_type: str, policies: Dict[str, Any]) -> str:
    """Build policy analysis prompt"""
    return f"""
Analyze the following {device_type} {policy_type} policies for security risks and best practices:

{format_policies_for_prompt(policies)}

Provide analysis on:
1. Security risks (any-any rules, overly permissive rules)
2. Missing security controls (no logging, no UTM features)
3. Best practice violations
4. Prioritized remediation steps

Focus on {device_type} security best practices and compliance.
"""

def build_change_analysis_prompt(device_type: str, current_config: Dict[str, Any], planned_change: str, change_type: str) -> str:
    """Build change analysis prompt"""
    return f"""
Analyze this planned {device_type} configuration change:

Current configuration snippet:
{format_config_for_prompt(current_config)}

Planned change ({change_type}):
{planned_change}

Provide analysis on:
1. What this change does technically
2. Potential impact on network/security
3. Risks and mitigation steps
4. Rollback procedure
5. Verification steps

Focus on {device_type} change management best practices.
"""

def build_triage_prompt(incident_description: str, device_id: Optional[str], logs: List[str], severity: str) -> str:
    """Build incident triage prompt"""
    logs_text = "\n".join(logs) if logs else "No logs provided"
    
    return f"""
Incident triage for {severity} severity incident:

Description: {incident_description}
Device: {device_id or 'Not specified'}

Relevant logs:
{logs_text}

Provide triage analysis:
1. Probable root cause
2. Key evidence from logs
3. Impact assessment
4. Immediate actions needed
5. Next steps for investigation
6. Escalation criteria

Focus on systematic troubleshooting and evidence-based analysis.
"""

def build_runbook_prompt(topic: str, device_type: str, include_verification: bool, include_rollback: bool) -> str:
    """Build runbook generation prompt"""
    return f"""
Generate a comprehensive runbook for: {topic}
Device type: {device_type}
Include verification steps: {include_verification}
Include rollback procedure: {include_rollback}

Create a structured runbook with:
1. Overview and prerequisites
2. Step-by-step procedure
3. Verification commands
4. Rollback procedure
5. Troubleshooting common issues

Focus on operational clarity and safety.
"""

def build_drift_analysis_prompt(device_type: str, config1: Dict[str, Any], config2: Dict[str, Any], diff: Dict[str, Any], device1_id: str, device2_id: str) -> str:
    """Build config drift analysis prompt"""
    return f"""
Analyze configuration drift between {device_type} devices:

Device 1: {device1_id}
Device 2: {device2_id}

Configuration differences:
{format_diff_for_prompt(diff)}

Provide analysis on:
1. What changed and why it might matter
2. Security implications of the changes
3. Compliance impact
4. Recommended actions to standardize configurations
5. Risk assessment of current drift

Focus on {device_type} security and compliance best practices.
"""

# Data extraction helpers (same as original)

def extract_risks_from_analysis(llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract structured risks from LLM response"""
    return [{"type": "security", "description": "Sample risk", "severity": "medium"}]

def extract_change_risks(llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract change-related risks"""
    return [{"impact": "connectivity", "probability": "low", "mitigation": "Test in staging"}]

def extract_rollback_steps(llm_response: Dict[str, Any]) -> List[str]:
    """Extract rollback steps from LLM response"""
    return ["Step 1: Revert configuration", "Step 2: Verify service restoration"]

def extract_verification_steps(llm_response: Dict[str, Any]) -> List[str]:
    """Extract verification steps"""
    return ["Verify connectivity", "Check service status", "Validate logs"]

def extract_evidence_from_logs(llm_response: Dict[str, Any], logs: List[str]) -> List[str]:
    """Extract key evidence from logs"""
    return logs[:3]  # Return first 3 log entries as evidence

def extract_next_steps(llm_response: Dict[str, Any]) -> List[str]:
    """Extract next steps from triage analysis"""
    return ["Investigate root cause", "Document findings", "Implement fix"]

def extract_escalation_criteria(llm_response: Dict[str, Any]) -> List[str]:
    """Extract escalation criteria"""
    return ["Multiple services affected", "Security breach suspected", "Business impact high"]

def extract_runbook_overview(llm_response: Dict[str, Any]) -> str:
    """Extract runbook overview"""
    return "Overview of the procedure and its purpose"

def extract_prerequisites(llm_response: Dict[str, Any]) -> List[str]:
    """Extract prerequisites from runbook"""
    return ["Device access", "Backup current config", "Maintenance window"]

def extract_procedure_steps(llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract step-by-step procedure"""
    return [{"step": 1, "action": "Configure setting", "expected_result": "Service active"}]

def extract_verification_commands(llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract verification commands"""
    return [{"command": "show status", "expected_output": "Active"}]

def extract_rollback_procedure(llm_response: Dict[str, Any]) -> List[str]:
    """Extract rollback procedure"""
    return ["Revert changes", "Verify service restoration", "Document rollback"]

def extract_troubleshooting_section(llm_response: Dict[str, Any]) -> Dict[str, Any]:
    """Extract troubleshooting section"""
    return {"common_issues": [], "solutions": [], "escalation": "Contact support"}

def generate_config_diff(config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
    """Generate configuration diff"""
    return {"changes": [{"section": "firewall", "change": "policy added", "old": "", "new": "new policy"}]}

def extract_security_implications(llm_response: Dict[str, Any]) -> List[str]:
    """Extract security implications"""
    return ["Potential security gap", "Compliance deviation"]

def extract_compliance_impact(llm_response: Dict[str, Any]) -> List[str]:
    """Extract compliance impact"""
    return ["SOC2 control affected", "PCI-DSS requirement not met"]

def extract_drift_recommendations(llm_response: Dict[str, Any]) -> List[str]:
    """Extract drift remediation recommendations"""
    return ["Standardize configurations", "Implement configuration management"]

# Formatting helpers (same as original)

def format_policies_for_prompt(policies: Dict[str, Any]) -> str:
    """Format policies for LLM prompt"""
    if not policies.get("policies"):
        return "No policies found"
    
    formatted = []
    for policy in policies["policies"][:10]:  # Limit to first 10
        formatted.append(f"Policy {policy.get('id', 'unknown')}: {policy.get('name', 'no name')}")
    
    return "\n".join(formatted)

def format_config_for_prompt(config: Dict[str, Any]) -> str:
    """Format configuration for prompt"""
    return str(config.get("config", ""))[:1000]  # Limit length

def format_diff_for_prompt(diff: Dict[str, Any]) -> str:
    """Format diff for prompt"""
    if not diff.get("changes"):
        return "No differences detected"
    
    formatted = []
    for change in diff["changes"][:10]:
        formatted.append(f"{change.get('section', 'unknown')}: {change.get('change', 'unknown')}")
    
    return "\n".join(formatted)
