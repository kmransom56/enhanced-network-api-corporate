"""
Fortinet LLM Integration Endpoints
Custom LLM model integration for Fortinet device analysis and troubleshooting
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuration - customize these for your LLM setup
FORTINET_LLM_CONFIG = {
    "base_url": "http://localhost:11434",  # Ollama default
    "model": "fortinet-custom",           # Your custom model name
    "timeout": 30.0,
    "max_tokens": 2048
}

class ChatRequest(BaseModel):
    prompt: str
    context: Optional[str] = "general"
    device_type: Optional[str] = None
    temperature: float = 0.7

class ChatResponse(BaseModel):
    response: str
    model: str
    context: str
    recommendations: List[Dict[str, Any]] = []
    analysis: Dict[str, Any] = {}

class TroubleshootingRequest(BaseModel):
    device_id: str
    device_type: str
    issue: str
    device_data: Dict[str, Any]
    topology_context: Optional[Dict[str, Any]] = {}

@router.post("/chat", response_model=ChatResponse)
async def chat_with_fortinet_llm(request: ChatRequest):
    """
    Chat with the custom Fortinet LLM model
    """
    try:
        async with httpx.AsyncClient(timeout=FORTINET_LLM_CONFIG["timeout"]) as client:
            # Prepare the prompt with Fortinet context
            system_prompt = build_system_prompt(request.context, request.device_type)
            full_prompt = f"{system_prompt}\n\nUser: {request.prompt}\n\nAssistant:"

            # Call Ollama API (adjust for your LLM backend)
            payload = {
                "model": FORTINET_LLM_CONFIG["model"],
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": FORTINET_LLM_CONFIG["max_tokens"]
                }
            }

            response = await client.post(
                f"{FORTINET_LLM_CONFIG['base_url']}/api/generate",
                json=payload
            )
            response.raise_for_status()

            result = response.json()
            
            # Parse the response and extract recommendations
            llm_response = result.get("response", "")
            recommendations = extract_recommendations(llm_response)
            analysis = parse_analysis(llm_response)

            return ChatResponse(
                response=llm_response,
                model=FORTINET_LLM_CONFIG["model"],
                context=request.context or "general",
                recommendations=recommendations,
                analysis=analysis
            )

    except httpx.HTTPError as e:
        logger.error(f"LLM HTTP error: {e}")
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        logger.error(f"LLM error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM processing error: {e}")

@router.post("/troubleshoot", response_model=ChatResponse)
async def troubleshoot_with_llm(request: TroubleshootingRequest):
    """
    Use Fortinet LLM for device troubleshooting
    """
    try:
        # Build comprehensive troubleshooting prompt
        prompt = build_troubleshooting_prompt(
            request.device_id,
            request.device_type,
            request.issue,
            request.device_data,
            request.topology_context
        )

        chat_request = ChatRequest(
            prompt=prompt,
            context="troubleshooting",
            device_type=request.device_type,
            temperature=0.3  # Lower temperature for more consistent troubleshooting
        )

        return await chat_with_fortinet_llm(chat_request)

    except Exception as e:
        logger.error(f"Troubleshooting error: {e}")
        raise HTTPException(status_code=500, detail=f"Troubleshooting failed: {e}")

@router.get("/models")
async def list_available_models():
    """
    List available Fortinet LLM models
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{FORTINET_LLM_CONFIG['base_url']}/api/tags")
            response.raise_for_status()
            
            models = response.json().get("models", [])
            fortinet_models = [
                model for model in models 
                if "fortinet" in model.get("name", "").lower()
            ]

            return {
                "available_models": fortinet_models,
                "current_model": FORTINET_LLM_CONFIG["model"],
                "base_url": FORTINET_LLM_CONFIG["base_url"]
            }

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        return {
            "available_models": [],
            "error": str(e)
        }

@router.get("/health")
async def health_check():
    """
    Check if Fortinet LLM service is healthy
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{FORTINET_LLM_CONFIG['base_url']}/api/tags")
            response.raise_for_status()
            
            return {
                "status": "healthy",
                "model": FORTINET_LLM_CONFIG["model"],
                "base_url": FORTINET_LLM_CONFIG["base_url"]
            }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Helper functions

def build_system_prompt(context: str, device_type: str) -> str:
    """
    Build system prompt based on context and device type
    """
    base_prompt = """You are an expert Fortinet network security engineer with deep knowledge of:
- FortiGate firewalls and security policies
- FortiSwitch network management
- FortiAP wireless systems
- FortiAnalyzer logging and reporting
- FortiManager centralized management
- Network troubleshooting best practices
- Security incident response procedures

Always provide:
1. Clear, actionable recommendations
2. Security-first considerations
3. Step-by-step troubleshooting procedures
4. References to Fortinet documentation when relevant"""

    context_prompts = {
        "troubleshooting": """
Focus on systematic troubleshooting:
- Identify symptoms and possible causes
- Provide diagnostic commands
- Suggest remediation steps
- Include preventive measures""",
        
        "configuration": """
Focus on configuration best practices:
- Security policy recommendations
- Network segmentation advice
- Performance optimization
- Compliance considerations""",
        
        "security": """
Focus on security analysis:
- Threat assessment
- Incident response procedures
- Hardening recommendations
- Monitoring and alerting"""
    }

    device_prompts = {
        "fortigate": """
FortiGate-specific considerations:
- Firewall policies and NAT rules
- VPN configurations
- IPS/AV profiles
- Traffic shaping
- HA cluster management""",
        
        "fortiswitch": """
FortiSwitch-specific considerations:
- VLAN configuration
- Port security settings
- Spanning Tree Protocol
- Link aggregation
- PoE configuration""",
        
        "fortiap": """
FortiAP-specific considerations:
- WiFi channel planning
- SSID configuration
- Client roaming
- RF optimization
- Access control"""
    }

    system_prompt = base_prompt
    
    if context in context_prompts:
        system_prompt += "\n\n" + context_prompts[context]
    
    if device_type in device_prompts:
        system_prompt += "\n\n" + device_prompts[device_type]

    return system_prompt

def build_troubleshooting_prompt(
    device_id: str,
    device_type: str,
    issue: str,
    device_data: Dict[str, Any],
    topology_context: Dict[str, Any]
) -> str:
    """
    Build comprehensive troubleshooting prompt
    """
    prompt = f"""
Device Information:
- ID: {device_id}
- Type: {device_type}
- Issue: {issue}

Device Data:
{format_device_data(device_data)}

Network Context:
{format_topology_context(topology_context)}

Please analyze this issue and provide:
1. **Root Cause Analysis**: What is the most likely cause?
2. **Immediate Actions**: What should be done right now?
3. **Diagnostic Commands**: Specific commands to run for verification
4. **Long-term Fixes**: Permanent solutions to prevent recurrence
5. **Impact Assessment**: How this affects other systems
6. **Preventive Measures**: Ongoing monitoring and maintenance

Format your response with clear headings and actionable steps.
"""
    
    return prompt

def format_device_data(device_data: Dict[str, Any]) -> str:
    """
    Format device data for LLM consumption
    """
    if not device_data:
        return "No device data available"
    
    formatted = []
    for key, value in device_data.items():
        if isinstance(value, dict):
            formatted.append(f"- {key}: {format_device_data(value)}")
        elif isinstance(value, list):
            formatted.append(f"- {key}: {', '.join(str(v) for v in value[:5])}{'...' if len(value) > 5 else ''}")
        else:
            formatted.append(f"- {key}: {value}")
    
    return "\n".join(formatted)

def format_topology_context(topology_context: Dict[str, Any]) -> str:
    """
    Format topology context for LLM consumption
    """
    if not topology_context:
        return "No topology context available"
    
    context_parts = []
    
    if "nodes" in topology_context:
        context_parts.append(f"Connected Devices ({len(topology_context['nodes'])}):")
        for node in topology_context["nodes"][:10]:  # Limit to first 10
            context_parts.append(f"- {node.get('id', 'unknown')} ({node.get('type', 'unknown')})")
    
    if "links" in topology_context:
        context_parts.append(f"Network Links: {len(topology_context['links'])} connections")
    
    return "\n".join(context_parts)

def extract_recommendations(llm_response: str) -> List[Dict[str, Any]]:
    """
    Extract structured recommendations from LLM response
    """
    recommendations = []
    
    # Simple parsing - look for numbered lists or bullet points
    lines = llm_response.split('\n')
    current_rec = None
    
    for line in lines:
        line = line.strip()
        
        # Look for recommendation patterns
        if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '-', '*')):
            if current_rec:
                recommendations.append(current_rec)
            
            current_rec = {
                "action": line.lstrip('123456.-* '),
                "priority": "medium",
                "automated": False
            }
        elif current_rec and line:
            # Continuation of current recommendation
            current_rec["action"] += " " + line
    
    if current_rec:
        recommendations.append(current_rec)
    
    # Try to extract priority information
    for rec in recommendations:
        action_lower = rec["action"].lower()
        if any(word in action_lower for word in ["critical", "urgent", "immediate"]):
            rec["priority"] = "critical"
        elif any(word in action_lower for word in ["high", "important"]):
            rec["priority"] = "high"
        elif any(word in action_lower for word in ["low", "minor"]):
            rec["priority"] = "low"
        
        # Check for automatable actions
        if any(word in action_lower for word in ["check", "verify", "monitor", "run"]):
            rec["automated"] = True
    
    return recommendations

def parse_analysis(llm_response: str) -> Dict[str, Any]:
    """
    Parse analysis from LLM response
    """
    analysis = {
        "root_cause": None,
        "impact": None,
        "urgency": "medium"
    }
    
    response_lower = llm_response.lower()
    
    # Extract root cause
    if "root cause" in response_lower:
        lines = llm_response.split('\n')
        for i, line in enumerate(lines):
            if "root cause" in line.lower():
                # Take the next line or two as the root cause
                if i + 1 < len(lines):
                    analysis["root_cause"] = lines[i + 1].strip()
                break
    
    # Extract urgency
    if any(word in response_lower for word in ["critical", "urgent", "emergency"]):
        analysis["urgency"] = "critical"
    elif any(word in response_lower for word in ["high", "important"]):
        analysis["urgency"] = "high"
    elif any(word in response_lower for word in ["low", "minor"]):
        analysis["urgency"] = "low"
    
    return analysis
