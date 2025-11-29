#!/usr/bin/env python3
"""
FastAPI endpoints for Network Topology Workflow
Provides REST API interface for the complete 2D/3D network mapping workflow
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime
import logging

from ..network_topology_workflow import NetworkTopologyWorkflow, NetworkDevice, NetworkConnection

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/topology", tags=["topology"])


class WorkflowConfig(BaseModel):
    """Configuration for topology workflow execution"""
    fortigate_host: str = Field(..., description="FortiGate hostname or IP")
    fortigate_token: str = Field(..., description="FortiGate API token")
    verify_ssl: bool = Field(False, description="Verify SSL certificates")
    oui_database_path: Optional[str] = Field(None, description="Path to OUI database")
    model_library_path: Optional[str] = Field(None, description="Path to 3D model library")
    svg_output_dir: str = Field("realistic_device_svgs", description="Output directory for SVG icons")
    ca_cert_path: Optional[str] = Field(None, description="Path to custom CA certificate")


class WorkflowResult(BaseModel):
    """Result from workflow execution"""
    status: str
    devices: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    export_paths: Dict[str, str]
    summary: Dict[str, Any]
    timestamp: str
    error: Optional[str] = None


class BabylonLabFormat(BaseModel):
    """Babylon.js lab format for 3D visualization"""
    models: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    metadata: Dict[str, Any]


# In-memory storage for workflow results (in production, use Redis or database)
workflow_cache: Dict[str, WorkflowResult] = {}
workflow_jobs: Dict[str, str] = {}


@router.post("/execute-workflow", response_model=Dict[str, str])
async def execute_topology_workflow(
    config: WorkflowConfig,
    background_tasks: BackgroundTasks
):
    """
    Execute the complete network topology workflow
    
    This endpoint initiates the workflow in the background and returns a job ID.
    Use the /workflow-status/{job_id} endpoint to check progress.
    
    Workflow steps:
    1. Authenticate to FortiGate
    2. Discover infrastructure devices
    3. Collect connected clients  
    4. Identify devices by MAC
    5. Generate SVG icons
    6. Build topology connections
    7. Export to visualization formats
    """
    try:
        job_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow_jobs[job_id] = "running"
        
        # Start workflow in background
        background_tasks.add_task(
            run_workflow_background,
            job_id,
            config
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": "Workflow execution started. Use /workflow-status/{job_id} to check progress."
        }
        
    except Exception as e:
        log.error(f"Failed to start workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def run_workflow_background(job_id: str, config: WorkflowConfig):
    """Execute workflow in background task"""
    try:
        workflow = NetworkTopologyWorkflow(
            fortigate_host=config.fortigate_host,
            fortigate_token=config.fortigate_token,
            oui_database_path=config.oui_database_path,
            model_library_path=config.model_library_path,
            svg_output_dir=config.svg_output_dir,
            verify_ssl=config.verify_ssl,
            ca_cert_path=config.ca_cert_path
        )
        
        result = await workflow.execute_workflow()
        
        # Store result
        workflow_cache[job_id] = WorkflowResult(
            status="completed",
            devices=result['devices'],
            connections=result['connections'],
            export_paths=result['export_paths'],
            summary=result['summary'],
            timestamp=datetime.now().isoformat()
        )
        workflow_jobs[job_id] = "completed"
        
    except Exception as e:
        log.error(f"Workflow {job_id} failed: {e}", exc_info=True)
        workflow_cache[job_id] = WorkflowResult(
            status="failed",
            devices=[],
            connections=[],
            export_paths={},
            summary={},
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )
        workflow_jobs[job_id] = "failed"


@router.get("/workflow-status/{job_id}")
async def get_workflow_status(job_id: str):
    """
    Get status of a workflow job
    
    Returns the current status and results if completed.
    """
    if job_id not in workflow_jobs:
        raise HTTPException(status_code=404, detail="Job ID not found")
    
    status = workflow_jobs[job_id]
    
    if status == "running":
        return {
            "job_id": job_id,
            "status": "running",
            "message": "Workflow is still executing"
        }
    
    if job_id in workflow_cache:
        return workflow_cache[job_id]
    
    raise HTTPException(status_code=500, detail="Job status inconsistent")


@router.get("/babylon-lab-format", response_model=BabylonLabFormat)
async def get_babylon_lab_format(
    fortigate_host: Optional[str] = Query(None, description="FortiGate host (if not using cached data)"),
    fortigate_token: Optional[str] = Query(None, description="FortiGate token (if not using cached data)"),
    use_cache: bool = Query(True, description="Use cached topology data if available"),
    ca_cert_path: Optional[str] = Query(None, description="Path to custom CA certificate")
):
    """
    Get topology data in Babylon.js lab format for 3D visualization
    
    This endpoint is called by babylon_lab_view.html to load the 3D scene.
    If use_cache=True and data exists, returns cached data.
    Otherwise, executes a quick workflow to fetch fresh data.
    """
    try:
        # Check for most recent cached data
        if use_cache and workflow_cache:
            latest_job = max(workflow_cache.keys())
            result = workflow_cache[latest_job]
            
            if result.status == "completed":
                return _convert_to_babylon_format(result.devices, result.connections)
        
        # If no cache or cache disabled, run quick workflow
        if fortigate_host and fortigate_token:
            workflow = NetworkTopologyWorkflow(
                fortigate_host=fortigate_host,
                fortigate_token=fortigate_token,
                verify_ssl=False,
                ca_cert_path=ca_cert_path
            )
            
            result = await workflow.execute_workflow()
            
            return _convert_to_babylon_format(result['devices'], result['connections'])
        
        # No cache and no credentials provided - return demo data
        return _get_demo_babylon_data()
        
    except Exception as e:
        log.error(f"Failed to get Babylon format: {e}", exc_info=True)
        # Return demo data on error so the 3D viewer still works
        return _get_demo_babylon_data()


def _convert_to_babylon_format(devices: List[Dict], connections: List[Dict]) -> BabylonLabFormat:
    """Convert workflow devices/connections to Babylon.js format"""
    models = []
    
    for i, device in enumerate(devices):
        # Calculate position if not present
        position = device.get('position') or _calculate_position(device, i)
        
        models.append({
            'id': device['id'],
            'name': device['name'],
            'type': device['type'],
            'vendor': device.get('vendor'),
            'model': device.get('model') or device['type'],
            'icon_svg': device.get('icon_svg'),
            'ip': device.get('ip'),
            'mac': device.get('mac'),
            'vlan': device.get('vlan'),
            'status': device.get('status', 'online'),
            'position': position
        })
    
    babylon_connections = []
    for conn in connections:
        babylon_connections.append({
            'id': conn['id'],
            'from': conn['from_device'],
            'to': conn['to_device'],
            'status': conn.get('status', 'up'),
            'protocol': conn.get('protocol'),
            'bandwidth': conn.get('bandwidth'),
            'vlan': conn.get('vlan')
        })
    
    return BabylonLabFormat(
        models=models,
        connections=babylon_connections,
        metadata={
            'generated': datetime.now().isoformat(),
            'total_devices': len(models),
            'total_connections': len(babylon_connections)
        }
    )


def _calculate_position(device: Dict, index: int) -> Dict[str, float]:
    """Calculate 3D position for device"""
    devices_per_row = 5
    spacing = 5.0
    
    row = index // devices_per_row
    col = index % devices_per_row
    
    device_type = device.get('type', '').lower()
    
    if 'fortigate' in device_type:
        return {'x': 0, 'y': 0, 'z': 0}
    elif 'fortiswitch' in device_type:
        return {'x': col * spacing - 10, 'y': 0, 'z': -5}
    elif 'fortiap' in device_type:
        return {'x': col * spacing - 10, 'y': 0, 'z': 5}
    else:
        return {
            'x': col * spacing - 10,
            'y': 0,
            'z': row * spacing - 10
        }


def _get_demo_babylon_data() -> BabylonLabFormat:
    """Return demo data for Babylon.js viewer"""
    return BabylonLabFormat(
        models=[
            {
                'id': 'fortigate-demo',
                'name': 'FortiGate-Primary',
                'type': 'fortigate',
                'vendor': 'Fortinet',
                'model': 'FortiGate-60F',
                'icon_svg': '/realistic_device_svgs/fortinet_fortigate.svg',
                'ip': '192.168.1.99',
                'mac': '90:6C:AC:12:34:56',
                'status': 'online',
                'position': {'x': 0, 'y': 0, 'z': 0}
            },
            {
                'id': 'fortiswitch-demo',
                'name': 'FortiSwitch-01',
                'type': 'fortiswitch',
                'vendor': 'Fortinet',
                'model': 'FortiSwitch-124F',
                'icon_svg': '/realistic_device_svgs/fortinet_fortiswitch.svg',
                'ip': '192.168.1.10',
                'mac': '90:6C:AC:23:45:67',
                'status': 'online',
                'position': {'x': -5, 'y': 0, 'z': -5}
            },
            {
                'id': 'fortiap-demo',
                'name': 'FortiAP-01',
                'type': 'fortiap',
                'vendor': 'Fortinet',
                'model': 'FortiAP-431F',
                'icon_svg': '/realistic_device_svgs/fortinet_fortiap.svg',
                'ip': '192.168.1.20',
                'mac': '90:6C:AC:34:56:78',
                'status': 'online',
                'position': {'x': 5, 'y': 0, 'z': 5}
            },
            {
                'id': 'client-pos',
                'name': 'POS-Terminal-01',
                'type': 'client',
                'vendor': 'Square',
                'model': 'Square Terminal',
                'icon_svg': '/realistic_device_svgs/square_pos_terminal.svg',
                'ip': '192.168.1.100',
                'mac': 'AC:BC:32:11:22:33',
                'status': 'online',
                'position': {'x': -8, 'y': 0, 'z': 8}
            }
        ],
        connections=[
            {
                'id': 'conn-fg-fs',
                'from': 'fortigate-demo',
                'to': 'fortiswitch-demo',
                'status': 'up',
                'protocol': 'ethernet',
                'bandwidth': '1Gbps'
            },
            {
                'id': 'conn-fg-fa',
                'from': 'fortigate-demo',
                'to': 'fortiap-demo',
                'status': 'up',
                'protocol': 'ethernet',
                'bandwidth': '1Gbps'
            },
            {
                'id': 'conn-fa-client',
                'from': 'fortiap-demo',
                'to': 'client-pos',
                'status': 'up',
                'protocol': 'wifi',
                'bandwidth': '100Mbps'
            }
        ],
        metadata={
            'generated': datetime.now().isoformat(),
            'total_devices': 4,
            'total_connections': 3,
            'is_demo': True
        }
    )


@router.get("/devices", response_model=List[Dict[str, Any]])
async def get_devices(job_id: Optional[str] = Query(None, description="Workflow job ID")):
    """
    Get list of discovered devices
    
    If job_id is provided, returns devices from that workflow execution.
    Otherwise, returns devices from the most recent workflow.
    """
    if job_id:
        if job_id not in workflow_cache:
            raise HTTPException(status_code=404, detail="Job ID not found")
        return workflow_cache[job_id].devices
    
    if not workflow_cache:
        raise HTTPException(status_code=404, detail="No workflow data available")
    
    latest_job = max(workflow_cache.keys())
    return workflow_cache[latest_job].devices


@router.get("/connections", response_model=List[Dict[str, Any]])
async def get_connections(job_id: Optional[str] = Query(None, description="Workflow job ID")):
    """
    Get list of device connections
    
    If job_id is provided, returns connections from that workflow execution.
    Otherwise, returns connections from the most recent workflow.
    """
    if job_id:
        if job_id not in workflow_cache:
            raise HTTPException(status_code=404, detail="Job ID not found")
        return workflow_cache[job_id].connections
    
    if not workflow_cache:
        raise HTTPException(status_code=404, detail="No workflow data available")
    
    latest_job = max(workflow_cache.keys())
    return workflow_cache[latest_job].connections


@router.get("/summary", response_model=Dict[str, Any])
async def get_topology_summary(job_id: Optional[str] = Query(None, description="Workflow job ID")):
    """
    Get topology summary statistics
    
    Returns counts and breakdown of devices by type.
    """
    if job_id:
        if job_id not in workflow_cache:
            raise HTTPException(status_code=404, detail="Job ID not found")
        result = workflow_cache[job_id]
    else:
        if not workflow_cache:
            raise HTTPException(status_code=404, detail="No workflow data available")
        latest_job = max(workflow_cache.keys())
        result = workflow_cache[latest_job]
    
    return {
        'summary': result.summary,
        'timestamp': result.timestamp,
        'status': result.status
    }


@router.delete("/cache/{job_id}")
async def clear_workflow_cache(job_id: str):
    """
    Clear cached workflow data for a specific job
    """
    if job_id not in workflow_cache:
        raise HTTPException(status_code=404, detail="Job ID not found")
    
    del workflow_cache[job_id]
    if job_id in workflow_jobs:
        del workflow_jobs[job_id]
    
    return {"message": f"Cache cleared for job {job_id}"}


@router.delete("/cache")
async def clear_all_workflow_cache():
    """
    Clear all cached workflow data
    """
    workflow_cache.clear()
    workflow_jobs.clear()
    
    return {"message": "All workflow cache cleared"}
