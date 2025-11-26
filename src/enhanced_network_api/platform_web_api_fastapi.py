#!/usr/bin/env python3
"""
AI Research Platform Web API (FastAPI)
Provides web-accessible endpoints for platform discovery and interaction
Integrates Fortinet LLM, MCP servers, and 2D/3D visualization
"""

import asyncio
import hashlib
import html
import json
import logging
import os
import subprocess
import sys
import time
from collections import OrderedDict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple
from urllib.parse import unquote

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import new API endpoints
HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE))
PROJECT_ROOT = HERE.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"

_DEFAULT_VLLM_BASE_URL = "http://127.0.0.1:8000/v1"
_DEFAULT_VLLM_MODEL = "codellama-7b_fortinet_meraki_20251107_185952"

logger = logging.getLogger(__name__)

from api.endpoints.smart_analysis import router as smart_analysis_router
from api.endpoints.meraki_mcp import router as meraki_router
from api.endpoints.fortinet_llm import router as fortinet_llm_router
from device_mac_matcher import create_device_matching_api
from visio_icon_extractor import create_icon_extraction_api
from restaurant_icon_downloader import create_restaurant_icon_api
from src.enhanced_network_api.shared import topology_workflow
from fortigate_docs_search import search_docs, warm_index


class PerformanceRecorder:
    """Collect recent runtime samples for expensive code paths."""

    def __init__(self, max_samples: int = 64) -> None:
        self._max_samples = max_samples
        self._samples: Dict[str, Deque[Dict[str, float]]] = {}

    def record(self, name: str, duration: float) -> None:
        bucket = self._samples.setdefault(name, deque(maxlen=self._max_samples))
        bucket.append({"duration": duration, "timestamp": time.time()})

    def summary(self) -> Dict[str, Dict[str, float]]:
        metrics: Dict[str, Dict[str, float]] = {}
        for name, samples in self._samples.items():
            if not samples:
                continue
            durations = [entry["duration"] for entry in samples]
            metrics[name] = {
                "count": len(durations),
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "last": durations[-1],
            }
        return metrics

    def reset(self) -> None:
        self._samples.clear()


@contextmanager
def _profile_section(name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        PERF_RECORDER.record(name, time.perf_counter() - start)


app = FastAPI(title="Enhanced Network API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = HERE / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

PERF_RECORDER = PerformanceRecorder()
app.state.performance = PERF_RECORDER

_PLATFORM_DATA_CACHE: Dict[str, Any] = {"mtime": None, "data": None}
_SERVICE_CLIENT_LOCK = asyncio.Lock()
_SERVICE_HTTP_CLIENT: Optional[httpx.AsyncClient] = None
_SERVICE_CLIENT_LOOP: Optional[asyncio.AbstractEventLoop] = None
_VLLM_CLIENT_LOCK = asyncio.Lock()
_VLLM_CLIENT: Optional[httpx.AsyncClient] = None
_VLLM_CLIENT_BASE: Optional[str] = None
_DOCS_INDEX_TASK: Optional[asyncio.Task] = None
_SCENE_CACHE: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
_SCENE_CACHE_MAX = 8


class FortiManagerCredentialsModel(BaseModel):
    host: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    adom: Optional[str] = "root"


class MerakiCredentialsModel(BaseModel):
    api_key: Optional[str] = None
    organization_id: Optional[str] = None
    network_id: Optional[str] = None
    base_url: Optional[str] = None


class FortiGateCredentialsModel(BaseModel):
    host: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: Optional[bool] = False
    wifi_host: Optional[str] = None
    wifi_token: Optional[str] = None


class DocsQARequest(BaseModel):
    question: str


class AutomatedTopologyRequest(BaseModel):
    fortigate_json: Optional[str] = None
    fortimanager_json: Optional[str] = None
    meraki_json: Optional[str] = None
    output_dir: Optional[str] = None
    json_name: Optional[str] = None
    graphml_name: Optional[str] = None
    drawio_name: Optional[str] = None
    write_files: bool = False
    use_samples: bool = True
    fortigate_credentials: Optional[FortiGateCredentialsModel] = None
    fortimanager_credentials: Optional[FortiManagerCredentialsModel] = None
    meraki_credentials: Optional[MerakiCredentialsModel] = None


class AutomatedDiagramRequest(BaseModel):
    layout: Optional[str] = "hierarchical"
    group_by: Optional[str] = "type"
    show_details: bool = True
    color_code: bool = True
    refresh_topology: bool = False
    write_file: bool = False
    output_dir: Optional[str] = None
    filename: str = "mcp_topology.drawio"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off", ""}


def _path_from_env(env_var: str, default: Path) -> Path:
    value = os.getenv(env_var)
    if value:
        return Path(value).expanduser()
    return default


AI_PLATFORM_ROOT = _path_from_env("AI_PLATFORM_ROOT", Path.home() / "cagent")
AI_PLATFORM_BINARY = _path_from_env("AI_PLATFORM_BINARY", AI_PLATFORM_ROOT / "ai-platform")
DISCOVERY_DIR = _path_from_env(
    "PLATFORM_DISCOVERY_DIR", AI_PLATFORM_ROOT / "platform_discovery"
)


def _clear_platform_data_cache() -> None:
    """Reset cached platform discovery data (used in tests and reload events)."""
    global _PLATFORM_DATA_CACHE
    _PLATFORM_DATA_CACHE = {"mtime": None, "data": None}



def _get_platform_file() -> Path:
    """Return the path to the discovery output file."""
    return DISCOVERY_DIR / "platform_map.json"



def _platform_file_mtime(path: Path) -> Optional[float]:
    try:
        return path.stat().st_mtime
    except OSError:
        return None

def _render_markdown_doc(filename: str, *, title: str) -> HTMLResponse:
    doc_path = DOCS_DIR / filename
    try:
        with doc_path.open("r", encoding="utf-8") as stream:
            content = stream.read()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Documentation '{filename}' not found") from exc

    escaped = html.escape(content)
    html_body = (
        "<html><head><title>{title}</title></head>"
        "<body style='font-family: monospace; padding: 24px; background: #101522; color: #f0f4ff;'>"
        "<h1>{title}</h1>"
        "<pre style='white-space: pre-wrap; line-height: 1.4;'>{content}</pre>"
        "</body></html>"
    ).format(title=html.escape(title), content=escaped)
    return HTMLResponse(content=html_body)


def _fortigate_docs_root() -> Path:
    return DOCS_DIR / "fortigate-api"


def _vllm_base_url() -> str:
    return os.getenv("VLLM_BASE_URL", _DEFAULT_VLLM_BASE_URL).rstrip("/")


def _vllm_model_name() -> str:
    return os.getenv("VLLM_MODEL_NAME", _DEFAULT_VLLM_MODEL)



@lru_cache(maxsize=32)
def _load_static_html(filename: str) -> str:
    path = STATIC_DIR / filename
    return path.read_text(encoding="utf-8")


def _static_missing_page(title: str, message: str) -> HTMLResponse:
    content = (
        "<html>"
        "<head><title>{title}</title></head>"
        "<body>"
        "<h1>{title}</h1>"
        "<p>{message}</p>"
        "<p><a href=\"/\">Back to Main</a></p>"
        "</body>"
        "</html>"
    ).format(title=title, message=message)
    return HTMLResponse(content=content, status_code=404)


def _serve_static_html(filename: str, *, missing_title: str, missing_message: str) -> HTMLResponse:
    try:
        return HTMLResponse(content=_load_static_html(filename))
    except FileNotFoundError:
        return _static_missing_page(missing_title, missing_message)

# Include API routers
app.include_router(fortinet_llm_router, prefix="/api/fortinet-llm", tags=["Fortinet LLM"])
app.include_router(meraki_router, prefix="/api/meraki-mcp", tags=["Meraki MCP"])
app.include_router(smart_analysis_router, prefix="/api/smart-analysis", tags=["Smart Analysis"])

# Add device matching, icon extraction, and restaurant icon APIs
create_device_matching_api(app)
create_icon_extraction_api(app)
create_restaurant_icon_api(app)

# Utility functions

def run_discovery():
    if not AI_PLATFORM_BINARY.is_file():
        print(f"Discovery binary not found at {AI_PLATFORM_BINARY}")
        return False
    result = None
    try:
        with _profile_section("run_discovery"):
            result = subprocess.run(
                [str(AI_PLATFORM_BINARY), "discover"],
                capture_output=True,
                text=True,
                cwd=str(AI_PLATFORM_ROOT),
                check=False,
            )
        return result.returncode == 0
    except FileNotFoundError as exc:
        print(f"Discovery binary not found: {exc}")
        return False
    except Exception as exc:
        print(f"Discovery error: {exc}")
        return False


def load_platform_data(refresh: bool = False):
    global _PLATFORM_DATA_CACHE
    platform_file = _get_platform_file()
    if not platform_file.exists():
        _clear_platform_data_cache()
        return None
    cache = _PLATFORM_DATA_CACHE
    mtime = _platform_file_mtime(platform_file)
    cached_mtime = cache.get("mtime")
    cached_data = cache.get("data")
    if not refresh and cached_mtime == mtime and cached_data is not None:
        return cached_data
    try:
        with _profile_section("load_platform_data"):
            with platform_file.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
        _PLATFORM_DATA_CACHE = {"mtime": mtime, "data": data}
        return data
    except Exception as exc:
        print(f"Error loading platform data: {exc}")
        return None


async def _get_service_http_client() -> httpx.AsyncClient:
    """Reuse a single AsyncClient for platform service proxying."""
    global _SERVICE_HTTP_CLIENT, _SERVICE_CLIENT_LOOP
    current_loop = asyncio.get_running_loop()
    async with _SERVICE_CLIENT_LOCK:
        if _SERVICE_HTTP_CLIENT and _SERVICE_CLIENT_LOOP is current_loop:
            return _SERVICE_HTTP_CLIENT

        if _SERVICE_HTTP_CLIENT:
            try:
                await _SERVICE_HTTP_CLIENT.aclose()
            except RuntimeError:
                pass

        _SERVICE_HTTP_CLIENT = httpx.AsyncClient(timeout=10.0)
        _SERVICE_CLIENT_LOOP = current_loop
        return _SERVICE_HTTP_CLIENT


async def _get_vllm_client() -> httpx.AsyncClient:
    """Reuse a single AsyncClient when contacting the vLLM server."""
    global _VLLM_CLIENT, _VLLM_CLIENT_BASE
    base_url = _vllm_base_url()
    async with _VLLM_CLIENT_LOCK:
        if _VLLM_CLIENT and _VLLM_CLIENT_BASE == base_url:
            return _VLLM_CLIENT
        if _VLLM_CLIENT:
            try:
                await _VLLM_CLIENT.aclose()
            except RuntimeError:
                pass
        _VLLM_CLIENT = httpx.AsyncClient(base_url=base_url, timeout=60.0)
        _VLLM_CLIENT_BASE = base_url
        return _VLLM_CLIENT


def _build_services_index(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    services: List[Dict[str, Any]] = []
    service_mapping = data.get("service_mapping", {})
    categories = data.get("categories", {})
    category_icons = {
        "ai_interfaces": "🤖",
        "databases": "🗄️",
        "monitoring": "📊",
        "automation": "⚙️",
        "mcp_services": "🔧",
        "development": "💻",
    }
    service_id = 1
    for category, containers in categories.items():
        category_name = category.replace("_", " ").title()
        icon = category_icons.get(category, "📦")
        for container in containers:
            port = None
            container_info = None
            for p, info in service_mapping.items():
                if info.get("container") == container:
                    port = p
                    container_info = info
                    break
            if port:
                services.append(
                    {
                        "id": service_id,
                        "name": container,
                        "category": category_name,
                        "icon": icon,
                        "port": port,
                        "url": f"http://localhost:{port}" if port else None,
                        "accessible": port is not None,
                        "status": container_info.get("status") if container_info else "unknown",
                        "image": container_info.get("image") if container_info else "unknown",
                    }
                )
                service_id += 1
    return services


# API Endpoints

@app.post("/api/platform/service/{service_id}/call")
async def call_service(service_id: int, request: Request):
    data = load_platform_data()
    if not data:
        raise HTTPException(status_code=404, detail="Platform not discovered")
    services = _build_services_index(data)
    if not (1 <= service_id <= len(services)):
        raise HTTPException(status_code=400, detail="Invalid service ID")
    service = services[service_id - 1]
    url = f"http://localhost:{service['port']}"
    payload = await request.json()
    method = payload.get('method', 'GET').upper()
    path_suffix = payload.get('path', '/')
    body = payload.get('body', None)
    headers = payload.get('headers', {})
    full_url = url + path_suffix if path_suffix.startswith('/') else url + '/' + path_suffix
    try:
        client = await _get_service_http_client()
        with _profile_section("call_service_request"):
            resp = await client.request(method, full_url, headers=headers, content=body)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return JSONResponse({
        "status_code": resp.status_code,
        "headers": dict(resp.headers),
        "body": resp.text,
        "url": full_url
    })

@app.get("/api/platform/status")
async def platform_status():
    data = load_platform_data()
    if not data:
        return JSONResponse({
            "status": "not_discovered",
            "message": "Platform not yet discovered. Run discovery first."
        })
    return JSONResponse({
        "status": "active",
        "discovery_time": data.get("discovery_time"),
        "containers": len(data.get("docker_containers", {})),
        "open_ports": len(data.get("discovered_ports", {})),
        "categories": {k: len(v) for k, v in data.get("categories", {}).items()}
    })

@app.post("/api/platform/discover")
async def discover_platform():
    success = await asyncio.to_thread(run_discovery)
    if not success:
        raise HTTPException(status_code=500, detail="Discovery failed")

    _clear_platform_data_cache()
    data = await asyncio.to_thread(load_platform_data, True)
    response_payload = {
        "status": "success",
        "message": "Platform discovery completed",
        "data": data
    }

    if _env_bool("AUTO_DRAWIO_EXPORT", False):
        try:
            asyncio.create_task(_auto_drawio_export_after_discovery())
        except RuntimeError as exc:  # pragma: no cover - loop closed
            logger.warning("Unable to schedule DrawIO export task: %s", exc)

    return JSONResponse(response_payload)

@app.post("/mcp/export_topology_json")
async def mcp_export_topology_json(request: Request):
    """MCP bridge endpoint for topology JSON export"""
    try:
        payload = await request.json()
        include_health = payload.get("include_health", False)
        format_type = payload.get("format", "standard")
        export_data = await _call_fortinet_tool_async(
            "export_topology_json",
            {"include_health": include_health, "format": format_type},
        )
        return JSONResponse(export_data)

    except Exception as e:
        print(f"Export exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _extract_diagram_xml(payload: Dict[str, Any]) -> str:
    """Normalize diagram responses from the Fortinet MCP bridge."""
    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail="Invalid response from Fortinet MCP bridge")

    for key in ("diagram_xml", "diagram", "content"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    raise HTTPException(status_code=502, detail="Fortinet MCP bridge did not return DrawIO XML")


async def _generate_drawio_via_mcp(
    params: AutomatedDiagramRequest,
) -> Dict[str, Any]:
    """Call MCP tools to build DrawIO output and optionally persist it."""
    if params.refresh_topology:
        await _call_fortinet_tool_async("collect_topology", {"refresh": True})

    diagram_payload = await _call_fortinet_tool_async(
        "generate_drawio_diagram",
        {
            "layout": params.layout,
            "group_by": params.group_by,
            "show_details": params.show_details,
            "color_code": params.color_code,
        },
    )

    diagram_xml = _extract_diagram_xml(diagram_payload)
    extras = {k: v for k, v in diagram_payload.items() if k not in {"content", "diagram_xml"}}
    artifacts: Optional[Dict[str, str]] = None

    if params.write_file:
        filename = params.filename or "mcp_topology.drawio"
        if any(sep in filename for sep in ("/", "\\")) or filename.startswith(".."):
            raise HTTPException(status_code=400, detail="Invalid DrawIO filename")

        target_dir = (
            Path(params.output_dir).expanduser()
            if params.output_dir
            else topology_workflow.DEFAULT_OUTPUT_DIR
        )
        try:
            target_dir = target_dir.resolve()
            target_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover - filesystem issues
            raise HTTPException(status_code=500, detail=f"Failed to prepare output directory: {exc}") from exc

        drawio_path = target_dir / filename
        drawio_path.write_text(diagram_xml, encoding="utf-8")
        artifacts = {"drawio_path": str(drawio_path)}

    response_payload: Dict[str, Any] = {
        "diagram_xml": diagram_xml,
        "layout": params.layout,
        "group_by": params.group_by,
        "show_details": params.show_details,
        "color_code": params.color_code,
    }

    if extras:
        response_payload["metadata"] = extras
    if artifacts:
        response_payload["artifacts"] = artifacts

    return response_payload


@app.post("/mcp/generate_drawio_diagram")
async def mcp_generate_drawio_diagram(payload: AutomatedDiagramRequest):
    """Generate a DrawIO diagram through the Fortinet MCP bridge."""
    try:
        result = await _generate_drawio_via_mcp(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DrawIO diagram generation failed: {exc}") from exc
    return JSONResponse(result)


@app.post("/api/topology/automated/drawio")
async def generate_automated_drawio(payload: AutomatedDiagramRequest):
    """API surface for Smart Tools to generate DrawIO diagrams via MCP."""
    result = await _generate_drawio_via_mcp(payload)
    return JSONResponse(result)


def _auto_drawio_request() -> AutomatedDiagramRequest:
    return AutomatedDiagramRequest(
        layout=os.getenv("AUTO_DRAWIO_LAYOUT") or "hierarchical",
        group_by=os.getenv("AUTO_DRAWIO_GROUP_BY") or "type",
        show_details=_env_bool("AUTO_DRAWIO_DETAILS", True),
        color_code=_env_bool("AUTO_DRAWIO_COLOR", True),
        refresh_topology=_env_bool("AUTO_DRAWIO_REFRESH", True),
        write_file=_env_bool("AUTO_DRAWIO_WRITE_FILE", True),
        output_dir=os.getenv("AUTO_DRAWIO_OUTPUT_DIR"),
        filename=os.getenv("AUTO_DRAWIO_FILENAME") or "mcp_topology.drawio",
    )


async def _auto_drawio_export_after_discovery() -> None:
    try:
        await _generate_drawio_via_mcp(_auto_drawio_request())
        logger.info("Automated DrawIO export completed after discovery.")
    except Exception as exc:  # pragma: no cover - best-effort logging
        logger.warning("Automated DrawIO export failed: %s", exc)


@app.post("/mcp/discover_fortinet_topology")
async def mcp_discover_fortinet_topology(request: Request):
    """MCP bridge endpoint for Fortinet topology discovery"""
    try:
        payload = await request.json()
        device_ip = payload.get('device_ip', '192.168.0.254')
        username = payload.get('username', 'admin')
        password = payload.get('password', '')
        include_performance = payload.get('include_performance', True)
        refresh_cache = payload.get('refresh_cache', False)
        result = await _call_fortinet_tool_async(
            "discover_fortinet_topology",
            {
                "device_ip": device_ip,
                "username": username,
                "password": password,
                "include_performance": include_performance,
                "refresh_cache": refresh_cache,
            },
        )
        return JSONResponse(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platform/services")
async def list_services():
    data = load_platform_data()
    if not data:
        raise HTTPException(status_code=404, detail="Platform not discovered")
    services = _build_services_index(data)
    categories = sorted({service["category"] for service in services})
    return JSONResponse({
        "services": services,
        "categories": categories,
    })

@app.post("/api/platform/service/{service_id}/open")
async def open_service(service_id: int):
    data = load_platform_data()
    if not data:
        raise HTTPException(status_code=404, detail="Platform not discovered")
    services = _build_services_index(data)
    if not (1 <= service_id <= len(services)):
        raise HTTPException(status_code=400, detail="Invalid service ID")
    service = services[service_id - 1]
    url = f"http://localhost:{service['port']}"
    return JSONResponse({
        "name": service["name"],
        "url": url,
        "action": f"window.open('{url}', '_blank')",
    })


@app.post("/api/topology/automated")
async def run_automated_topology_workflow(request: AutomatedTopologyRequest):
    """Generate a combined FortiManager + Meraki topology snapshot."""

    def _execute_workflow():
        output_dir = Path(request.output_dir).expanduser() if request.output_dir else None
        fg_creds = (
            topology_workflow.FortiGateCredentials(
                **request.fortigate_credentials.dict(exclude_none=True)
            )
            if request.fortigate_credentials
            else None
        )
        fm_creds = (
            topology_workflow.FortiManagerCredentials(
                **request.fortimanager_credentials.dict(exclude_none=True)
            )
            if request.fortimanager_credentials
            else None
        )
        meraki_creds = (
            topology_workflow.MerakiCredentials(
                **request.meraki_credentials.dict(exclude_none=True)
            )
            if request.meraki_credentials
            else None
        )
        return topology_workflow.generate_artifacts(
            fortigate_json=request.fortigate_json,
            fortimanager_json=request.fortimanager_json,
            meraki_json=request.meraki_json,
            fortigate_credentials=fg_creds,
            fortimanager_credentials=fm_creds,
            meraki_credentials=meraki_creds,
            use_samples=request.use_samples,
            output_dir=output_dir,
            json_name=request.json_name or "combined_topology.json",
            graphml_name=request.graphml_name or "combined_topology.graphml",
            drawio_name=request.drawio_name,
            write_files=request.write_files,
        )

    try:
        result = await asyncio.to_thread(_execute_workflow)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    topology = result["topology"]
    summary = topology.get("metadata", {})
    response_payload = {
        "topology": topology,
        "summary": {
            "node_count": summary.get("node_count", len(topology.get("nodes", []))),
            "link_count": summary.get("link_count", len(topology.get("links", []))),
            "fortimanager_device_count": summary.get("fortimanager_device_count", 0),
            "meraki_device_count": summary.get("meraki_device_count", 0),
        },
        "artifacts": result.get("artifacts"),
        "sources": result.get("sources"),
    }

    return JSONResponse(response_payload)


@app.get("/api/topology/automated/artifacts")
async def list_automated_topology_artifacts():
    """List generated automated topology artefacts on disk."""
    artifacts = topology_workflow.list_artifacts()
    return JSONResponse({"artifacts": artifacts})


@app.get("/api/topology/automated/artifacts/{artifact_name}")
async def fetch_automated_topology_artifact(artifact_name: str):
    """Download a generated topology artefact."""
    safe_name = unquote(artifact_name)
    if any(sep in safe_name for sep in ("/", "\\")) or ".." in safe_name:
        raise HTTPException(status_code=400, detail="Invalid artifact name")

    target_dir = topology_workflow.DEFAULT_OUTPUT_DIR.resolve()
    candidate = (target_dir / safe_name).resolve()
    if not candidate.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    suffix = candidate.suffix.lower()
    media_type = "application/octet-stream"
    if suffix == ".json":
        media_type = "application/json"
    elif suffix == ".graphml":
        media_type = "application/graphml+xml"
    elif suffix in {".xml", ".drawio"}:
        media_type = "application/xml"

    return FileResponse(candidate, media_type=media_type, filename=candidate.name)

@app.get("/smart-tools", response_class=HTMLResponse)
async def smart_tools():
    """Serve the smart analysis tools interface"""
    return _serve_static_html(
        "smart-tools.html",
        missing_title="Smart Analysis Tools",
        missing_message="Tools interface not found. Check static files.",
    )

@app.get("/automated-topology", response_class=HTMLResponse)
async def automated_topology_docs():
    """Serve the automated topology documentation overview."""
    return _serve_static_html(
        "automated_topology.html",
        missing_title="Automated Topology Documentation",
        missing_message="Automated topology workflow page not found. Regenerate static assets.",
    )


@app.get("/docs/automated-topology", response_class=HTMLResponse)
async def automated_topology_markdown():
    """Render the automated topology Markdown documentation."""
    return _render_markdown_doc("AUTOMATED_TOPOLOGY_DIAGRAMS.md", title="Automated Topology Diagrams")


@app.get("/docs/search")
async def search_fortigate_docs(q: str, limit: int = 10):
    """Search the local FortiGate API documentation scraped into docs/fortigate-api.

    Returns a lightweight list of matches (title, path, snippet) for use by UI and agents.
    """
    root = _fortigate_docs_root()
    if not root.exists():
        raise HTTPException(status_code=404, detail="FortiGate docs not available on disk")

    results = search_docs(root, q, limit=limit)
    return JSONResponse({"query": q, "results": results})


@app.post("/docs/qa")
async def fortigate_docs_qa(payload: DocsQARequest):
    """Answer a question using local FortiGate API documentation and the local vLLM model.

    This endpoint performs a simple retrieval over the scraped docs, then calls the
    OpenAI-compatible vLLM server configured via VLLM_BASE_URL / VLLM_MODEL_NAME.
    """
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty")

    root = _fortigate_docs_root()
    if not root.exists():
        raise HTTPException(status_code=404, detail="FortiGate docs not available on disk")

    # Retrieve context from local docs
    hits = search_docs(root, question, limit=5)
    if not hits:
        raise HTTPException(status_code=404, detail="No relevant documentation found for question")

    context_blocks = []
    for h in hits:
        context_blocks.append(f"SOURCE: {h['path']}\n{h['snippet']}")
    context = "\n\n".join(context_blocks)

    system_prompt = (
        "You are a FortiGate API assistant. Use ONLY the provided documentation context "
        "to answer the user's question. If the answer is not clearly present, say that "
        "the documentation excerpt does not contain enough information."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "Documentation context:\n\n" f"{context}" "\n\nQuestion: " f"{question}"
            ),
        },
    ]

    base_url = _vllm_base_url()
    model_name = _vllm_model_name()

    try:
        client = await _get_vllm_client()
        resp = await client.post(
            "/chat/completions",
            json={
                "model": model_name,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1024,
            },
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Error contacting vLLM server: {exc}") from exc

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"vLLM server returned HTTP {resp.status_code}: {resp.text}",
        )

    data = resp.json()
    choices = data.get("choices") or []
    if not choices:
        raise HTTPException(status_code=500, detail="vLLM server returned no choices")

    answer = choices[0].get("message", {}).get("content", "").strip()
    return JSONResponse({"question": question, "answer": answer, "sources": hits})


@app.get("/2d-topology-enhanced", response_class=HTMLResponse)
async def topology_2d_enhanced():
    """Serve the enhanced 2D topology interface"""
    return _serve_static_html(
        "2d_topology_enhanced.html",
        missing_title="Enhanced 2D Topology Not Found",
        missing_message="Test file not found. Check static files.",
    )

_SAMPLE_SCENE = {
    "nodes": [
        {
            "id": "fg-core",
            "name": "FortiGate Core",
            "hostname": "fg-core",
            "type": "fortigate",
            "role": "gateway",
            "ip": "192.168.0.254",
            "model": "FortiGate_600E",
            "serial": "FGT61FTK20020975",
            "status": "active",
            "position": {"x": 0, "y": 0, "z": 0},
        },
        {
            "id": "switch-edge",
            "name": "Edge Switch",
            "hostname": "fsw-edge",
            "type": "fortiswitch",
            "role": "switch",
            "ip": "10.255.1.2",
            "model": "FortiSwitch_124F",
            "serial": "FSW24F3Z21001234",
            "status": "active",
            "position": {"x": -14, "y": 0, "z": 6},
        },
        {
            "id": "ap-lobby",
            "name": "Lobby AP",
            "hostname": "fap-lobby",
            "type": "fortiap",
            "role": "access_point",
            "ip": "192.168.1.3",
            "model": "FortiAP_432F",
            "serial": "FAP432F321X5909876",
            "status": "active",
            "position": {"x": 11, "y": 0, "z": -4},
        },
        {
            "id": "client-pos",
            "name": "POS Terminal",
            "hostname": "pos-01",
            "type": "client",
            "role": "client",
            "ip": "192.168.2.45",
            "model": "Windows",
            "status": "active",
            "connection_type": "ethernet",
            "position": {"x": -8, "y": 0, "z": 18},
        },
        {
            "id": "client-handheld",
            "name": "Handheld Scanner",
            "hostname": "scanner-07",
            "type": "client",
            "role": "client",
            "ip": "192.168.2.86",
            "model": "Android",
            "status": "active",
            "connection_type": "wifi",
            "ssid": "NET_INT_SSID",
            "position": {"x": 16, "y": 0, "z": -12},
        },
    ],
    "links": [
        {
            "from": "fg-core",
            "to": "switch-edge",
            "type": "fortilink",
            "status": "active",
            "ports": ["port1", "port1"],
        },
        {
            "from": "switch-edge",
            "to": "ap-lobby",
            "type": "wired",
            "status": "active",
            "ports": ["port5", "port1"],
        },
        {
            "from": "switch-edge",
            "to": "client-pos",
            "type": "wired",
            "status": "active",
            "ports": ["port7", "eth0"],
        },
        {
            "from": "ap-lobby",
            "to": "client-handheld",
            "type": "wifi",
            "status": "active",
            "ports": ["wifi1", "wifi"],
        },
    ],
}


def _normalize_scene(topology: Any) -> Dict[str, Any]:
    with _profile_section("normalize_scene"):
        if isinstance(topology, str):
            try:
                data = json.loads(topology)
            except json.JSONDecodeError:
                data = {}
        elif isinstance(topology, dict):
            data = topology
        else:
            data = {}

        signature = _topology_signature(data)
        cached = _SCENE_CACHE.get(signature)
        if cached is not None:
            return cached

        scene = _normalize_scene_compute(data)
        _SCENE_CACHE[signature] = scene
        while len(_SCENE_CACHE) > _SCENE_CACHE_MAX:
            _SCENE_CACHE.popitem(last=False)
        return scene


def _enhance_scene_with_models(scene: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance topology scene with device model matching and 3D model paths."""
    from device_mac_matcher import DeviceModelMatcher
    
    matcher = DeviceModelMatcher()
    enhanced_scene = scene.copy()
    
    # Enhance nodes with device model information
    for node in enhanced_scene.get("nodes", []):
        # Try to extract MAC address from node metadata
        mac_address = None
        if "mac" in node:
            mac_address = node["mac"]
        elif "hostname" in node and ":" in node["hostname"]:
            # Some devices might have MAC in hostname
            potential_mac = node["hostname"]
            if len(potential_mac.split(":")) == 6:
                mac_address = potential_mac
        
        # Add device model information if MAC is available
        if mac_address:
            try:
                device_info = matcher.match_mac_to_model(mac_address, {"hostname": node.get("hostname")})
                node.update({
                    "device_vendor": device_info.vendor,
                    "device_model": device_info.model_path,
                    "device_confidence": device_info.confidence,
                    "device_type": device_info.device_type,
                    "pos_system": device_info.pos_system
                })
            except Exception as e:
                log.warning(f"Failed to match device for MAC {mac_address}: {e}")
        
        # Add fallback model paths based on device type
        if "device_model" not in node:
            device_type = node.get("type", "unknown").lower()
            if "fortigate" in device_type:
                node["device_model"] = "/static/3d-models/fortigate.obj"
            elif "fortiswitch" in device_type:
                node["device_model"] = "/static/3d-models/fortiswitch.obj"
            elif "fortiap" in device_type or "wireless" in device_type:
                node["device_model"] = "/static/3d-models/fortiap.obj"
            elif "network" in device_type:
                node["device_model"] = "/static/3d-models/network.obj"
            else:
                node["device_model"] = "/static/3d-models/generic_device.obj"
    
    return enhanced_scene


def _normalize_scene_compute(data: Dict[str, Any]) -> Dict[str, Any]:
    devices = []
    for key in ("devices", "nodes"):
        value = data.get(key)
        if isinstance(value, list):
            devices = value
            break

    nodes: List[Dict[str, Any]] = []
    for device in devices:
        if not isinstance(device, dict):
            continue
        node_id = device.get("id") or device.get("name")
        if not node_id:
            continue
        node_type = device.get("type") or device.get("role") or "device"
        node = {"id": node_id, "name": device.get("name") or node_id, "type": node_type}
        for key in (
            "hostname",
            "role",
            "ip",
            "model",
            "serial",
            "status",
            "position",
            "mac",
            "firmware",
            "os",
            "ssid",
            "connection_type",
        ):
            value = device.get(key)
            if value is not None:
                node[key] = value
        nodes.append(node)

    links_source = data.get("links") or data.get("edges") or []
    normalized_links: List[Dict[str, Any]] = []
    if isinstance(links_source, list):
        for link in links_source:
            if not isinstance(link, dict):
                continue
            source = link.get("from") or link.get("source") or link.get("source_id")
            target = link.get("to") or link.get("target") or link.get("target_id")
            if not (source and target):
                continue
            normalized = {"from": source, "to": target}
            for key in ("type", "status", "description"):
                value = link.get(key)
                if value is not None:
                    normalized[key] = value
            ports = link.get("ports") or link.get("interfaces")
            if ports:
                normalized["ports"] = ports
            normalized_links.append(normalized)

    return {"nodes": nodes, "links": normalized_links}


def _json_default(value: Any) -> Any:
    if isinstance(value, (set, tuple)):
        return list(value)
    return str(value)


def _topology_signature(topology: Dict[str, Any]) -> str:
    try:
        serialized = json.dumps(topology, sort_keys=True, default=_json_default)
    except TypeError:
        serialized = json.dumps(str(topology), sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@app.get("/babylon-test", response_class=HTMLResponse)
async def babylon_test():
    """Serve the Babylon.js test interface"""
    return _serve_static_html(
        "babylon_test.html",
        missing_title="Babylon.js Test Not Found",
        missing_message="Test file not found. Check static files.",
    )

@app.get("/echarts-gl-test", response_class=HTMLResponse)
async def echarts_gl_test():
    """Serve the ECharts-GL test interface"""
    return _serve_static_html(
        "echarts_gl_test.html",
        missing_title="ECharts-GL Test Not Found",
        missing_message="Test file not found. Check static files.",
    )

@app.get("/iconlab", response_class=HTMLResponse)
async def iconlab_portal():
    """Serve the IconLab restaurant technology device recognition portal"""
    return FileResponse(
        PROJECT_ROOT / "iconlab.html",
        media_type="text/html"
    )

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main visualization interface"""
    return _serve_static_html(
        "babylon_topology.html",
        missing_title="Enhanced Network API",
        missing_message="Topology interface not found. Check static files.",
    )


# ==================== FORTINET TOPOLOGY ENDPOINTS (via HTTP MCP bridge) ====================

_DEFAULT_FORTINET_MCP_HTTP_URL = "http://127.0.0.1:9001"
_CACHEABLE_TOOLS = {"discover_fortinet_topology", "export_topology_json"}
_FORTINET_CLIENT_LOCK = asyncio.Lock()
_FORTINET_CLIENT: Optional["FortinetMCPClient"] = None


def _fortinet_mcp_http_url() -> str:
    """Resolve Fortinet MCP bridge URL from environment each call."""
    return os.getenv("FORTINET_MCP_HTTP_URL", _DEFAULT_FORTINET_MCP_HTTP_URL)


def _fortinet_credentials() -> Dict[str, Any]:
    """Collect FortiGate credentials from environment for MCP calls."""
    primary_entry = os.getenv("FORTIGATE_HOSTS", "").split(",")[0].strip() or os.getenv(
        "FORTIGATE_HOST", "192.168.0.254"
    )
    host_only, sep, port = primary_entry.partition(":")
    if not host_only:
        host_only = "192.168.0.254"
    primary_ip = host_only

    username = (
        os.getenv("FORTIGATE_USERNAME")
        or os.getenv("FORTIMANAGER_USERNAME")
        or os.getenv("FORTIGATE_USER")
        or "admin"
    )
    token_key_candidates = [
        f"FORTIGATE_{primary_entry.replace('.', '_').replace('-', '_').replace(':', '_')}_TOKEN",
        f"FORTIGATE_{host_only.replace('.', '_').replace('-', '_')}_TOKEN",
        "FORTIGATE_TOKEN",
    ]
    password = (
        next((os.getenv(key) for key in token_key_candidates if os.getenv(key)), None)
        or os.getenv("FORTIGATE_PASSWORD")
        or os.getenv("FORTIMANAGER_PASSWORD")
        or ""
    )
    device_ip = primary_ip
    return {
        "device_ip": device_ip,
        "username": username,
        "password": password,
    }


@dataclass
class FortinetMCPClient:
    """Lightweight Fortinet MCP bridge client with response caching."""

    url: str
    credentials: Dict[str, Any]
    cache_ttl: float = 10.0
    session: httpx.AsyncClient = field(default_factory=httpx.AsyncClient)
    cache: Dict[Tuple[str, Tuple[Tuple[str, Any], ...]], Tuple[float, Dict[str, Any]]] = field(default_factory=dict)
    cache_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    loop: asyncio.AbstractEventLoop = field(default_factory=asyncio.get_running_loop)

    async def close(self) -> None:
        await self.session.aclose()

    def _normalized_arguments(self, arguments: Dict[str, Any]) -> Tuple[Tuple[str, Any], ...]:
        return tuple(sorted((k, v) for k, v in arguments.items() if k != "password"))

    async def call(self, tool_name: str, extra_arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        arguments: Dict[str, Any] = {**self.credentials}
        if extra_arguments:
            arguments.update(extra_arguments)

        use_cache = (
            tool_name in _CACHEABLE_TOOLS
            and not bool(arguments.get("refresh_cache"))
        )
        cache_key: Optional[Tuple[str, Tuple[Tuple[str, Any], ...]]] = None

        if use_cache:
            cache_key = (tool_name, self._normalized_arguments(arguments))
            async with self.cache_lock:
                cached = self.cache.get(cache_key)
                if cached and (time.monotonic() - cached[0]) < self.cache_ttl:
                    return cached[1]

        try:
            resp = await self.session.post(
                "/mcp/call-tool",
                json={"name": tool_name, "arguments": arguments},
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Error contacting Fortinet MCP bridge: {exc}") from exc

        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Fortinet MCP bridge returned HTTP {resp.status_code}: {resp.text}",
            )

        data = resp.json()
        if data.get("isError"):
            raise HTTPException(status_code=500, detail=data)

        content_list = data.get("content") or []
        if content_list and isinstance(content_list, list):
            first = content_list[0]
            text_value = first.get("text") if isinstance(first, dict) else str(first)
            try:
                parsed = json.loads(text_value or "{}")
            except json.JSONDecodeError:
                parsed = {"content": text_value}
        else:
            parsed = data

        if use_cache and cache_key:
            async with self.cache_lock:
                self.cache[cache_key] = (time.monotonic(), parsed)

        return parsed


async def _get_fortinet_client() -> FortinetMCPClient:
    """Return a cached Fortinet MCP client instance keyed by URL and credentials."""
    global _FORTINET_CLIENT
    credentials = _fortinet_credentials()
    url = _fortinet_mcp_http_url()
    current_loop = asyncio.get_running_loop()

    async with _FORTINET_CLIENT_LOCK:
        if (
            _FORTINET_CLIENT
            and _FORTINET_CLIENT.url == url
            and _FORTINET_CLIENT.credentials == credentials
            and _FORTINET_CLIENT.loop is current_loop
        ):
            return _FORTINET_CLIENT

        if _FORTINET_CLIENT:
            try:
                await _FORTINET_CLIENT.close()
            except RuntimeError:
                # Original event loop already closed; ignore cleanup failure.
                pass

        _FORTINET_CLIENT = FortinetMCPClient(
            url=url,
            credentials=credentials,
            session=httpx.AsyncClient(base_url=url, timeout=15.0),
            loop=current_loop,
        )
        return _FORTINET_CLIENT


async def _call_fortinet_tool_async(tool_name: str, extra_arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call the Fortinet HTTP MCP bridge and return decoded JSON payload."""
    client = await _get_fortinet_client()
    return await client.call(tool_name, extra_arguments)


def _call_fortinet_tool(tool_name: str, extra_arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Synchronous helper primarily for legacy utilities and tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_call_fortinet_tool_async(tool_name, extra_arguments))
    else:
        raise RuntimeError(
            "Cannot call synchronous _call_fortinet_tool from within an active event loop. "
            "Use 'await _call_fortinet_tool_async(...)' instead."
        )


@app.get("/api/topology/raw")
async def get_topology_raw():
    """Return raw Fortinet topology JSON from discover_fortinet_topology tool."""
    data = await _call_fortinet_tool_async("discover_fortinet_topology")
    return JSONResponse(data)


@app.get("/api/topology/scene")
async def get_topology_scene():
    """Return normalized 3D scene JSON sourced from the Fortinet MCP bridge."""
    try:
        topology = await _call_fortinet_tool_async("discover_fortinet_topology")
    except HTTPException as exc:
        if exc.status_code in {502, 503}:
            return JSONResponse(_SAMPLE_SCENE)
        raise
    except Exception:
        return JSONResponse(_SAMPLE_SCENE)

    scene = await asyncio.to_thread(_normalize_scene, topology)
    if not scene["nodes"]:
        return JSONResponse(_SAMPLE_SCENE)
    return JSONResponse(scene)

@app.get("/api/topology/scene-enhanced")
async def get_topology_scene_enhanced():
    """Return enhanced 3D scene with device model matching and 3D model paths."""
    try:
        topology = await _call_fortinet_tool_async("discover_fortinet_topology")
    except HTTPException as exc:
        if exc.status_code in {502, 503}:
            return JSONResponse(_enhance_scene_with_models(_SAMPLE_SCENE))
        raise
    except Exception:
        return JSONResponse(_enhance_scene_with_models(_SAMPLE_SCENE))

    scene = await asyncio.to_thread(_normalize_scene, topology)
    if not scene["nodes"]:
        return JSONResponse(_enhance_scene_with_models(_SAMPLE_SCENE))
    
    enhanced_scene = await asyncio.to_thread(_enhance_scene_with_models, scene)
    return JSONResponse(enhanced_scene)

@app.get("/api/performance/metrics")
async def performance_metrics():
    """Expose recent performance samples for monitoring and tests."""
    return JSONResponse({"metrics": PERF_RECORDER.summary()})


@app.on_event("startup")
async def startup_event() -> None:
    """Kick off background initialization tasks (e.g., documentation warmup)."""
    global _DOCS_INDEX_TASK
    root = _fortigate_docs_root()
    if not root.exists():
        return

    async def _warm():
        try:
            await asyncio.to_thread(warm_index, root)
        except Exception as exc:  # pragma: no cover - best-effort
            logger.warning("Failed to warm FortiGate docs index: %s", exc)

    _DOCS_INDEX_TASK = asyncio.create_task(_warm())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Gracefully close pooled HTTP clients when FastAPI stops."""
    global _FORTINET_CLIENT, _SERVICE_HTTP_CLIENT, _SERVICE_CLIENT_LOOP, _VLLM_CLIENT, _VLLM_CLIENT_BASE, _DOCS_INDEX_TASK
    if _DOCS_INDEX_TASK and not _DOCS_INDEX_TASK.done():
        _DOCS_INDEX_TASK.cancel()
    _DOCS_INDEX_TASK = None
    if _FORTINET_CLIENT:
        try:
            await _FORTINET_CLIENT.close()
        finally:
            _FORTINET_CLIENT = None
    if _SERVICE_HTTP_CLIENT:
        try:
            await _SERVICE_HTTP_CLIENT.aclose()
        finally:
            _SERVICE_HTTP_CLIENT = None
            _SERVICE_CLIENT_LOOP = None
    if _VLLM_CLIENT:
        try:
            await _VLLM_CLIENT.aclose()
        finally:
            _VLLM_CLIENT = None
            _VLLM_CLIENT_BASE = None


def get_performance_metrics() -> Dict[str, Dict[str, float]]:
    """Helper used by tests and scripts to inspect recorded metrics."""
    return PERF_RECORDER.summary()



# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and self-healing."""
    try:
        # Basic health check
        from datetime import datetime
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "api": {"status": "online", "response_time": "fast"},
                "mcp_bridge": {"status": "unknown", "response_time": None},
                "topology_endpoints": {"status": "online", "response_time": "fast"}
            },
            "metrics": {
                "uptime": "unknown",
                "memory_usage": "unknown",
                "cpu_usage": "unknown",
                "active_connections": 0
            },
            "version": "2.0.0"
        }
        
        return JSONResponse(content=health_data, status_code=200)
        
    except Exception as e:
        from datetime import datetime
        error_data = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "services": {},
            "metrics": {}
        }
        return JSONResponse(content=error_data, status_code=503)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11111)

