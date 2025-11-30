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
import orjson
import os
import subprocess
import sys
import time
from collections import OrderedDict, deque, defaultdict
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
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Load environment variables from .env file early
try:
    from dotenv import load_dotenv
    # Try multiple locations for .env file
    env_paths = [
        Path("/app/.env"),  # Docker container location
        Path(".env"),  # Current directory
        Path(__file__).parent.parent.parent / ".env",  # Project root
        Path(__file__).parent.parent.parent / "corporate.env",  # Alternative name
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=False)  # Don't override existing env vars
            logger = logging.getLogger(__name__)
            logger.info(f"✅ Loaded environment from {env_path}")
            break
    else:
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️  No .env file found in: {env_paths}")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("python-dotenv not installed, using system environment only")

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
from device_mac_matcher import create_device_matching_api, DeviceModelMatcher
from visio_icon_extractor import create_icon_extraction_api
from restaurant_icon_downloader import create_restaurant_icon_api
from src.enhanced_network_api.shared import topology_workflow
from src.enhanced_network_api.layout_network_tree import calculate_network_tree_layout
from fortigate_docs_search import search_docs, warm_index
from mcp_servers.drawio_fortinet_meraki.fortigate_collector import (
    FortiGateTopologyCollector,
)
from mcp_servers.drawio_fortinet_meraki.api_documentation import IntelligentAPIMCP
from mcp_servers.drawio_fortinet_meraki.fortinet_integration import (
    DrawIOFortinetIntegration,
)
from graphml_parser import parse_graphml_topology


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
app.mount("/network-map-files", StaticFiles(directory=HERE), name="network-map-files")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Mount additional static directories for generated / vendor 2D and 3D assets
app.mount("/extracted_icons", StaticFiles(directory=str(PROJECT_ROOT / "extracted_icons")), name="extracted_icons")
app.mount("/lab_3d_models", StaticFiles(directory=str(PROJECT_ROOT / "lab_3d_models")), name="lab_3d_models")
app.mount("/realistic_device_svgs", StaticFiles(directory=str(PROJECT_ROOT / "realistic_device_svgs")), name="realistic_device_svgs")
app.mount("/realistic_3d_models", StaticFiles(directory=str(PROJECT_ROOT / "realistic_3d_models")), name="realistic_3d_models")
# Vendor stencil-derived models (VSS → GLTF) live under vss_extraction/vss_exports
app.mount("/vss_extraction", StaticFiles(directory=str(PROJECT_ROOT / "vss_extraction")), name="vss_extraction")

PERF_RECORDER = PerformanceRecorder()
app.state.performance = PERF_RECORDER

_PLATFORM_DATA_CACHE: Dict[str, Any] = {"mtime": None, "data": None}
_SERVICE_CLIENT_LOCK = asyncio.Lock()
_SERVICE_HTTP_CLIENT: Optional[httpx.AsyncClient] = None
_SERVICE_CLIENT_LOOP: Optional[asyncio.AbstractEventLoop] = None
_VLLM_CLIENT_LOCK = asyncio.Lock()
_VLLM_CLIENT: Optional[httpx.AsyncClient] = None
_VLLM_CLIENT_BASE: Optional[str] = None

# Optional manifest describing SVG→3D models generated by svg_to_3d.py
_ICON_MANIFEST_PATH = PROJECT_ROOT / "lab_3d_models" / "manifest.json"
_ICON_MODELS: Optional[List[Dict[str, Any]]] = None
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


class FortiGateDirectRequest(BaseModel):
    """Request envelope for direct FortiGate API calls via FortiGateTopologyCollector."""

    credentials: Optional[FortiGateCredentialsModel] = None


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


class IntelligentAPIDocsQuery(BaseModel):
    """Request model for intelligent API documentation queries."""

    query: str
    device_type: Optional[str] = "fortigate"


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


def _create_fortigate_collector(
    creds: Optional[FortiGateCredentialsModel],
) -> FortiGateTopologyCollector:
    """Instantiate a FortiGateTopologyCollector from request credentials or environment.

    This reuses the same environment variables used by the MCP tooling so that a
    "clone → run" setup can talk to the FortiGate at 192.168.0.254 without
    additional configuration, while still allowing per-request overrides.
    """

    # Extract host from creds or environment (FIXED: was using FORTIMANAGER_HOST)
    host = (
        creds.host if creds and creds.host 
        else os.getenv("FORTIGATE_HOST") or os.getenv("FORTIGATE_HOSTS", "192.168.0.254").split(",")[0].strip()
    )
    # Remove port if present (FortiGateTopologyCollector adds it)
    if ":" in host:
        host = host.split(":")[0]
    
    username = (
        creds.username
        if creds and creds.username
        else os.getenv("FORTIGATE_USERNAME") or os.getenv("FORTIGATE_USER", "admin")
    )
    password = (
        creds.password
        if creds and creds.password is not None
        else os.getenv("FORTIGATE_PASSWORD") or ""
    )
    # Get token - check host-specific token first, then generic token
    token = None
    if creds and creds.token:
        token = creds.token
    else:
        # Try host-specific token first (e.g., FORTIGATE_192_168_0_254_TOKEN)
        host_clean = host.replace(".", "_").replace("-", "_").replace(":", "_")
        host_token_var = f"FORTIGATE_{host_clean}_TOKEN"
        token = (
            os.getenv(host_token_var) or
            os.getenv("FORTIGATE_TOKEN") or
            os.getenv("FORTIGATE_API_TOKEN")
        )
    verify_ssl = (
        creds.verify_ssl
        if creds and creds.verify_ssl is not None
        else _env_bool("FORTIGATE_VERIFY_SSL", False)
    )
    wifi_host = (
        creds.wifi_host if creds and creds.wifi_host 
        else os.getenv("FORTIGATE_WIFI_HOST")
    )
    wifi_token = (
        creds.wifi_token if creds and creds.wifi_token
        else os.getenv("FORTIGATE_WIFI_TOKEN")
    )

    # Build collector with only available parameters (wifi_host/wifi_token may not be supported in old code)
    collector_kwargs = {
        "host": host,
        "username": username,
        "password": None if token else password,
        "token": token,
        "verify_ssl": bool(verify_ssl),
    }
    # Only add wifi_host/wifi_token if the collector supports them (check by inspecting __init__ signature)
    import inspect
    init_sig = inspect.signature(FortiGateTopologyCollector.__init__)
    if "wifi_host" in init_sig.parameters:
        collector_kwargs["wifi_host"] = wifi_host
    if "wifi_token" in init_sig.parameters:
        collector_kwargs["wifi_token"] = wifi_token
    
    return FortiGateTopologyCollector(**collector_kwargs)


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

    auto_drawio_flag = os.getenv("AUTO_DRAWIO_EXPORT", "").strip().lower()
    if auto_drawio_flag in {"1", "true", "yes", "on"}:
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
        if export_data.get("topology") is None and "topology" in export_data:
            fallback = _fallback_topology_copy()
            export_data["topology"] = fallback
        elif "topology" not in export_data:
            # If the MCP response already returned nodes/links directly (as in unit tests), respect it.
            if "nodes" not in export_data and "links" not in export_data:
                fallback = _fallback_topology_copy()
                export_data["topology"] = fallback
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


@app.get("/api-endpoints", response_class=HTMLResponse)
async def api_endpoints_overview():
    """Serve a minimal documentation page listing key API endpoints."""
    return _serve_static_html(
        "api_endpoints.html",
        missing_title="Enhanced Network API &mdash; Endpoints",
        missing_message="API endpoints documentation page not found. Check static files.",
    )


@app.get("/api-endpoints/auto", response_class=HTMLResponse)
async def api_endpoints_auto():
    """Auto-generated endpoint list built from FastAPI's app.routes.

    This is a simple HTML table view over the current route configuration so that
    the documentation stays in sync as new routers and endpoints are added.
    """

    rows = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = sorted(m for m in route.methods or [] if m not in {"HEAD", "OPTIONS"})
            method_str = ", ".join(methods)
            summary = route.summary or route.name or ""
            rows.append(
                {
                    "path": route.path,
                    "methods": method_str,
                    "summary": summary,
                }
            )

    rows.sort(key=lambda r: r["path"])

    row_html = []
    for r in rows:
        row_html.append(
            "<tr>"
            f"<td><code>{html.escape(r['methods'])}</code></td>"
            f"<td><code>{html.escape(r['path'])}</code></td>"
            f"<td>{html.escape(r['summary'])}</td>"
            "</tr>"
        )

    body = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Enhanced Network API — Auto Endpoints</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#020617; color:#e5e7eb; margin:0; padding:24px; }
    h1 { font-size:24px; margin-bottom:8px; color:#93c5fd; }
    p { margin:4px 0 16px 0; color:#9ca3af; font-size:13px; }
    table { width:100%; border-collapse: collapse; font-size:13px; }
    th, td { border-bottom:1px solid rgba(55,65,81,0.8); padding:6px 8px; text-align:left; }
    th { background:#020617; color:#d1d5db; font-weight:600; }
    code { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; }
    tr:hover { background:rgba(15,23,42,0.8); }
  </style>
</head>
<body>
  <h1>Enhanced Network API — Auto Endpoint Listing</h1>
  <p>This table is generated from <code>app.routes</code> at runtime, so it always reflects
  the current FastAPI configuration (including router-based endpoints).</p>
  <table>
    <thead>
      <tr><th style=\"width:110px;\">Methods</th><th>Path</th><th>Summary / Name</th></tr>
    </thead>
    <tbody>
""" + "".join(row_html) + """
    </tbody>
  </table>
</body>
</html>"""

    return HTMLResponse(content=body)


@app.get("/3d-lab", response_class=HTMLResponse)
async def three_d_lab_viewer():
    """Serve the 3D Network Topology Lab Babylon viewer.

    This page is designed to consume the /api/topology/babylon-lab-format endpoint, which
    adapts the Enhanced Network API topology scene into the JSON format used by the
    standalone 3d-network-topology-lab project.
    """
    return _serve_static_html(
        "babylon_lab_view.html",
        missing_title="3D Network Topology Lab",
        missing_message="3D lab viewer not found. Check static files.",
    )

@app.get("/2d-svg", response_class=HTMLResponse)
async def two_d_svg_topology():
    """Serve the 2D SVG topology viewer.

    This page provides a 2D network diagram view using vis.js with the option
    to display SVG icons generated from Visio stencils.
    """
    return _serve_static_html(
        "svg_topology_view.html",
        missing_title="2D SVG Topology View",
        missing_message="2D SVG viewer not found. Check static files.",
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

_FALLBACK_TOPOLOGY = {
    "devices": [
        {
            "id": "fg-192.168.0.254",
            "name": "FortiGate-192.168.0.254",
            "type": "fortigate",
            "role": "gateway",
            "model": "FortiGate_600E",
            "serial": "FGT61FTK20020975",
            "ip": "192.168.0.254",
            "status": "active",
            "site": "Main",
            "interfaces": [
                {"name": "port1", "ip": "192.168.0.254", "status": "up", "speed": "1 Gbps"},
                {"name": "port2", "ip": "10.255.1.1", "status": "up", "speed": "1 Gbps"},
            ],
            "firewall_policies": 24,
            "cpu_usage": 22.5,
            "memory_usage": 48.2,
            "connections": 812,
        },
        {
            "id": "network-lan",
            "name": "LAN Segment",
            "type": "network",
            "ip": "10.255.1.0/24",
            "status": "active",
            "site": "Main",
        },
        {
            "id": "fsw-edge",
            "name": "Edge Switch",
            "type": "fortiswitch",
            "model": "FortiSwitch_124F",
            "serial": "FSW24F3Z21001234",
            "ip": "10.255.1.2",
            "status": "active",
            "site": "Main",
            "total_ports": 48,
            "poe_ports": 24,
        },
        {
            "id": "fap-lobby",
            "name": "Lobby AP",
            "type": "fortiap",
            "model": "FortiAP_432F",
            "serial": "FAP432F321X5909876",
            "ip": "10.255.10.10",
            "status": "active",
            "site": "Main",
        },
    ],
    "links": [
        {
            "source_id": "fg-192.168.0.254",
            "target_id": "network-lan",
            "source_interface": "port2",
            "target_interface": "network",
            "link_type": "physical",
            "status": "active",
            "bandwidth": "1 Gbps",
        },
        {
            "source_id": "fg-192.168.0.254",
            "target_id": "fsw-edge",
            "source_interface": "port1",
            "target_interface": "port1",
            "link_type": "fortilink",
            "status": "active",
            "bandwidth": "1 Gbps",
        },
        {
            "source_id": "fsw-edge",
            "target_id": "fap-lobby",
            "source_interface": "port5",
            "target_interface": "eth0",
            "link_type": "wired",
            "status": "active",
            "bandwidth": "1 Gbps",
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


def _load_icon_models() -> List[Dict[str, Any]]:
    """Load SVG→3D icon manifest generated by svg_to_3d.py (if present)."""
    global _ICON_MODELS
    if _ICON_MODELS is not None:
        return _ICON_MODELS

    if not _ICON_MANIFEST_PATH.exists():
        _ICON_MODELS = []
        return _ICON_MODELS

    try:
        with _ICON_MANIFEST_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        _ICON_MODELS = data.get("models") or []
    except Exception as exc:  # pragma: no cover - best-effort
        logger.warning("Failed to load icon manifest %s: %s", _ICON_MANIFEST_PATH, exc)
        _ICON_MODELS = []
    return _ICON_MODELS


def _select_icon_model_for_type(device_type_str: str) -> Optional[str]:
    """Return a /lab_3d_models/ OBJ path for the given device type, if available.

    This prefers models categorized as firewall/switch/access_point, or whose
    names/tags clearly indicate FortiGate/FortiSwitch/FortiAP, but will fall
    back gracefully if the manifest is missing or incomplete.
    """
    models = _load_icon_models()
    if not models:
        return None

    dt = (device_type_str or "").lower()
    preferred_categories: List[str] = []
    if "fortigate" in dt or "firewall" in dt or "gateway" in dt:
        preferred_categories = ["firewall", "security"]
    elif "fortiswitch" in dt or "switch" in dt:
        preferred_categories = ["switch"]
    elif "fortiap" in dt or "access_point" in dt or "wifi" in dt or dt == "ap":
        preferred_categories = ["access_point"]

    def _matches(model: Dict[str, Any]) -> bool:
        cat = (model.get("category") or "").lower()
        name = (model.get("name") or "").lower()
        tags = [str(t).lower() for t in (model.get("tags") or [])]

        if preferred_categories and cat in preferred_categories:
            return True

        # Fortinet-specific name heuristics
        if "fortigate" in dt and ("fortigate" in name or "fg" in name):
            return True
        if "fortiswitch" in dt and ("fortiswitch" in name or "fs" in name):
            return True
        if "fortiap" in dt and ("fortiap" in name or "ap" in name):
            return True

        # Generic Fortinet tag match
        if any("fortinet" in t for t in tags) or "fortinet" in name:
            return True
        return False

    # Only consider entries that have an OBJ path
    candidates = [m for m in models if m.get("objPath")]
    for model in candidates:
        if _matches(model):
            obj_rel = model["objPath"]
            return f"/lab_3d_models/{obj_rel}"

    return None


def _enhance_scene_with_models(scene: Dict[str, Any]) -> Dict[str, Any]:
    from device_mac_matcher import DeviceModelMatcher
    
    matcher = DeviceModelMatcher()
    enhanced_scene = scene.copy()
    
    # Enhance nodes with device model and icon information
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
                logger.warning("Failed to match device for MAC %s: %s", mac_address, e)
        
        # Prefer Fortinet SVG→3D OBJ models (lab_3d_models/manifest.json) and VSS icons
        device_type_str = (node.get("type") or "").lower()
        icon_base = "/extracted_icons/lab_vss_svgs"

        # First try OBJ models produced from SVG icons
        obj_model = _select_icon_model_for_type(device_type_str)
        if obj_model:
            node["device_model"] = obj_model

        # Ensure Fortinet-specific GLTF + SVG icon as a fallback
        if "fortigate" in device_type_str:
            node.setdefault("device_model", "/vss_extraction/vss_exports/FortiGate_600E.gltf")
            node.setdefault("icon_svg", f"{icon_base}/shape_001___PF.svg")
        elif "fortiswitch" in device_type_str:
            node.setdefault("device_model", "/vss_extraction/vss_exports/FortiSwitch_148E.gltf")
            # Representative FortiSwitch SVG extracted from the stencil set
            node.setdefault("icon_svg", f"{icon_base}/shape_004_SE_W_7.svg")
        elif "fortiap" in device_type_str or "wireless" in device_type_str:
            node.setdefault("device_model", "/vss_extraction/vss_exports/FortiAP_432F.gltf")
            # Representative FortiAP SVG extracted from the stencil set
            node.setdefault("icon_svg", f"{icon_base}/shape_007_c__f.svg")
        
        # Normalize device types - convert various client/endpoint types to "client"
        if any(keyword in device_type_str for keyword in ["mobile device", "kitchen display", "randomized mac", "endpoint", "device"]) and not any(keyword in device_type_str for keyword in ["fortigate", "fortiswitch", "fortiap", "switch", "ap", "router"]):
            node["type"] = "client"
            device_type_str = "client"
        
        # Add 3D models and SVG icons for endpoint/client devices
        if "client" in device_type_str or "endpoint" in device_type_str or "device" in device_type_str:
            connection_type = (node.get("connection_type") or "").lower()
            # Use appropriate model and SVG icon based on device type
            if "laptop" in device_type_str or "computer" in device_type_str or connection_type == "ethernet":
                node.setdefault("device_model", "/realistic_3d_models/models/Laptop.obj")
                # Use laptop SVG icon from VSS if available, otherwise fallback
                node.setdefault("icon_svg", f"{icon_base}/shape_027__-3_.svg")  # Laptop icon
            elif "phone" in device_type_str or "mobile" in device_type_str or connection_type == "wifi":
                node.setdefault("device_model", "/realistic_3d_models/models/Smartphone.obj")
                # Use smartphone/mobile SVG icon from VSS if available
                node.setdefault("icon_svg", f"{icon_base}/shape_027__-3_.svg")  # Mobile device icon
            else:
                # Default endpoint model
                node.setdefault("device_model", "/realistic_3d_models/models/Laptop.obj")
                node.setdefault("icon_svg", f"{icon_base}/shape_027__-3_.svg")  # Generic endpoint icon
        
        # Add fallback model paths based on device type when no specific model is known
        if "device_model" not in node:
            device_type = node.get("type", "unknown").lower()
            if "network" in device_type:
                node["device_model"] = "/static/3d-models/network.obj"
            else:
                node["device_model"] = "/static/3d-models/generic_device.obj"
    _apply_hierarchical_layout(enhanced_scene)
    return enhanced_scene


def _apply_hierarchical_layout(scene: Dict[str, Any], layout_type: str = "network_tree") -> None:
    """Apply a hierarchical, link-aware layout to the normalized scene.

    Devices are arranged in a tree structure matching the network topology diagram:
    - Internet (top center)
    - Fortigate (center, below Internet)
    - FortiSwitch (left) and Wireless AP (right)
    - End devices (below their parent)
    
    Args:
        scene: Scene dictionary with nodes and links
        layout_type: Layout algorithm to use ("network_tree" or "hierarchical")
    """
    if layout_type == "network_tree":
        nodes = scene.get("nodes", [])
        links = scene.get("links", [])
        if nodes:
            positioned_nodes = calculate_network_tree_layout(nodes, links)
            # Update scene with positioned nodes
            scene["nodes"] = positioned_nodes
        return

    nodes = scene.get("nodes", [])
    links = scene.get("links", [])
    if not nodes:
        return

    layers: Dict[str, List[Dict[str, Any]]] = {
        "internet": [],
        "fortigate": [],
        "fortiswitch": [],
        "fortiap": [],
        "endpoint": [],
        "other": [],
    }

    node_by_id: Dict[str, Dict[str, Any]] = {}
    layer_for_id: Dict[str, str] = {}

    for node in nodes:
        node_id = node.get("id") or node.get("name")
        if not node_id:
            continue
        node_by_id[node_id] = node

        t = (node.get("type") or node.get("role") or "").lower()
        if "fortigate" in t:
            layer_name = "fortigate"
        elif "fortiswitch" in t or t == "network":
            layer_name = "fortiswitch"
        elif "fortiap" in t or "access_point" in t or t == "ap":
            layer_name = "fortiap"
        elif "internet" in t or "wan" in t:
            layer_name = "internet"
        elif t in {"client", "endpoint", "device"} or node.get("connection_type") in ("ethernet", "wifi"):
            layer_name = "endpoint"
        else:
            layer_name = "other"

        layers[layer_name].append(node)
        layer_for_id[node_id] = layer_name

    # Layer ordering for parent/child inference from links
    layer_order: Dict[str, int] = {
        "internet": 0,
        "fortigate": 1,
        "fortiswitch": 2,
        "fortiap": 3,
        "endpoint": 4,
        "other": 2,
    }

    # Build a simple parent → children map using links and layer ordering
    children_by_parent: Dict[str, List[str]] = defaultdict(list)
    child_ids: set = set()

    for link in links or []:
        if not isinstance(link, dict):
            continue
        src = link.get("from") or link.get("source") or link.get("source_id")
        dst = link.get("to") or link.get("target") or link.get("target_id")
        if not src or not dst:
            continue
        if src not in layer_for_id or dst not in layer_for_id:
            continue

        src_layer = layer_for_id[src]
        dst_layer = layer_for_id[dst]
        src_ord = layer_order.get(src_layer, 2)
        dst_ord = layer_order.get(dst_layer, 2)
        if src_ord == dst_ord:
            # Same layer; skip for hierarchical parent/child
            continue

        if src_ord < dst_ord:
            parent, child = src, dst
        else:
            parent, child = dst, src

        if child not in children_by_parent[parent]:
            children_by_parent[parent].append(child)
            child_ids.add(child)

    # Determine root nodes (no parent) in layer order
    roots: List[str] = []
    for lname in ("internet", "fortigate", "fortiswitch", "fortiap", "endpoint", "other"):
        for node in layers[lname]:
            nid = node.get("id") or node.get("name")
            if nid and nid not in child_ids and nid not in roots:
                roots.append(nid)
    if not roots:
        roots = list(node_by_id.keys())

    # Assign X coordinates with a simple tidy-tree style layout
    spacing = 4.5
    leaf_index = 0
    x_coords: Dict[str, float] = {}

    def layout_subtree(node_id: str) -> float:
        nonlocal leaf_index
        children = children_by_parent.get(node_id, [])
        if not children:
            x = leaf_index * spacing
            leaf_index += 1
        else:
            xs: List[float] = []
            for child in children:
                xs.append(layout_subtree(child))
            x = sum(xs) / len(xs)
        x_coords[node_id] = x
        return x

    for root in roots:
        if root not in x_coords:
            layout_subtree(root)

    if not x_coords:
        return

    # Center the layout around X=0
    min_x = min(x_coords.values())
    max_x = max(x_coords.values())
    center = (min_x + max_x) / 2.0

    # Arrange layers as horizontal rows (Z) with slight Y offsets so the
    # scene is not perfectly flat.
    z_by_layer = {
        "internet": -16.0,
        "fortigate": -8.0,
        "fortiswitch": 0.0,
        "fortiap": 8.0,
        "endpoint": 16.0,
        "other": 0.0,
    }

    y_by_layer = {
        "internet": 3.0,
        "fortigate": 2.7,
        "fortiswitch": 2.4,
        "fortiap": 2.1,
        "endpoint": 1.8,
        "other": 2.0,
    }

    # Apply final positions per node
    for node_id, node in node_by_id.items():
        base_x = x_coords.get(node_id, 0.0) - center
        layer_name = layer_for_id.get(node_id, "other")
        z = z_by_layer.get(layer_name, 0.0)
        y = y_by_layer.get(layer_name, 2.0)
        pos = node.get("position") or {}
        pos["x"] = base_x
        pos["y"] = y
        pos["z"] = z
        node["position"] = pos


def _normalize_scene_compute(data: Dict[str, Any]) -> Dict[str, Any]:
    devices = data.get("devices") or data.get("nodes") or []
    if not isinstance(devices, list):
        devices = []

    nodes = [
        {
            "id": (node_id := device.get("id") or device.get("name")),
            "name": device.get("name") or node_id,
            "type": device.get("type") or device.get("role") or "device",
            **{
                k: v
                for k in (
                    "hostname", "role", "ip", "model", "serial", "status",
                    "position", "mac", "firmware", "os", "ssid", "connection_type"
                )
                if (v := device.get(k)) is not None
            }
        }
        for device in devices
        if isinstance(device, dict) and (device.get("id") or device.get("name"))
    ]

    links_source = data.get("links") or data.get("edges") or []
    normalized_links = []
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
                if (val := link.get(key)) is not None:
                    normalized[key] = val
            
            if (ports := link.get("ports") or link.get("interfaces")):
                normalized["ports"] = ports
            normalized_links.append(normalized)

    return {"nodes": nodes, "links": normalized_links}


def _json_default(value: Any) -> Any:
    if isinstance(value, (set, tuple)):
        return list(value)
    return str(value)


def _topology_signature(topology: Dict[str, Any]) -> str:
    try:
        serialized = orjson.dumps(topology, option=orjson.OPT_SORT_KEYS)
    except TypeError:
        serialized = orjson.dumps(str(topology), option=orjson.OPT_SORT_KEYS)
    return hashlib.sha256(serialized).hexdigest()


@app.get("/babylon-test", response_class=HTMLResponse)
async def babylon_test():
    """Serve the Babylon.js test interface"""
    redirect_markup = (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='UTF-8'/>"
        "<meta http-equiv='refresh' content='0; url=/'/>"
        "<title>Babylon.js Topology Test</title>"
        "<style>body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;"
        "font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#020617;color:#f8fafc;}"
        ".msg{text-align:center;} .msg a{color:#93c5fd;text-decoration:none;}</style>"
        "</head><body><div class='msg'><h1>Redirecting to Babylon Topology Viewer</h1>"
        "<p>If you are not redirected automatically, <a href='/'>click here</a>.</p>"
        "</div></body></html>"
    )
    return HTMLResponse(content=redirect_markup)

@app.get("/echarts-gl-test", response_class=HTMLResponse)
async def echarts_gl_test():
    """Serve the ECharts-GL test interface"""
    redirect_markup = (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='UTF-8'/>"
        "<meta http-equiv='refresh' content='0; url=/static/echarts_gl_demo.html'/>"
        "<title>ECharts-GL Topology Test</title>"
        "<style>body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;"
        "font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;}"
        ".msg{text-align:center;} .msg a{color:#facc15;text-decoration:none;}</style>"
        "</head><body><div class='msg'><h1>Redirecting to ECharts-GL Demo</h1>"
        "<p>If you are not redirected automatically, <a href='/static/echarts_gl_demo.html'>click here</a>.</p>"
        "</div></body></html>"
    )
    return HTMLResponse(content=redirect_markup)

@app.get("/iconlab", response_class=HTMLResponse)
async def iconlab_portal():
    """Serve the IconLab restaurant technology device recognition portal"""
    return FileResponse(
        PROJECT_ROOT / "iconlab.html",
        media_type="text/html"
    )

@app.get("/network-map", response_class=HTMLResponse)
async def network_map():
    """Serve the 3D network map."""
    return FileResponse(HERE / "network_map_3d.html")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main visualization interface"""
    redirect_markup = (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='UTF-8'/>"
        "<meta http-equiv='refresh' content='0; url=/static/babylon_topology.html'/>"
        "<title>Enhanced Network API</title>"
        "<style>body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;"
        "font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0b1324;color:#f1f5f9;}"
        ".msg{text-align:center;} .msg a{color:#60a5fa;text-decoration:none;}</style>"
        "</head><body><div class='msg'><h1>Loading Enhanced Network Topology Interface</h1>"
        "<p>If the viewer does not load automatically, <a href='/static/babylon_topology.html'>click here</a>.</p>"
        "</div></body></html>"
    )
    return HTMLResponse(content=redirect_markup)


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
    ca_path: Optional[str] = None
    session: httpx.AsyncClient = field(init=False)
    cache: Dict[Tuple[str, Tuple[Tuple[str, Any], ...]], Tuple[float, Dict[str, Any]]] = field(default_factory=dict)
    cache_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    loop: asyncio.AbstractEventLoop = field(default_factory=asyncio.get_running_loop)

    def __post_init__(self):
        verify = self.ca_path if self.ca_path else False
        self.session = httpx.AsyncClient(base_url=self.url, verify=verify)

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
                content=orjson.dumps({"name": tool_name, "arguments": arguments}),
                headers={"Content-Type": "application/json"},
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Error contacting Fortinet MCP bridge: {exc}") from exc

        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Fortinet MCP bridge returned HTTP {resp.status_code}: {resp.text}",
            )

        try:
            data = orjson.loads(resp.content)
        except orjson.JSONDecodeError:
            data = resp.json()

        if data.get("isError"):
            # Extract a human-readable error message from the MCP response
            message: Optional[str] = None
            content_list = data.get("content") or data.get("contents") or []
            if isinstance(content_list, list) and content_list:
                first = content_list[0]
                if isinstance(first, dict) and "text" in first:
                    message = str(first.get("text"))
            if not message:
                message = "MCP bridge reported an error while calling Fortinet tools"
            # Use 502 Bad Gateway to clearly indicate bridge/collector-level failure
            raise HTTPException(status_code=502, detail=message)

        content_list = data.get("content") or []
        if content_list and isinstance(content_list, list):
            first = content_list[0]
            text_value = first.get("text") if isinstance(first, dict) else str(first)
            try:
                parsed = orjson.loads(text_value or "{}")
            except orjson.JSONDecodeError:
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
            ca_path=os.getenv("CA_CERT_PATH"),
            loop=current_loop,
        )
        return _FORTINET_CLIENT


async def _call_fortinet_tool_async(tool_name: str, extra_arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call the Fortinet HTTP MCP bridge and return decoded JSON payload."""
    client = await _get_fortinet_client()
    return await client.call(tool_name, extra_arguments)


def _fallback_topology_copy() -> Dict[str, Any]:
    data = orjson.loads(orjson.dumps(_FALLBACK_TOPOLOGY))
    metadata = data.setdefault("metadata", {})
    metadata.setdefault("source", "fallback")
    return data


async def _load_topology_raw_with_fallback() -> Dict[str, Any]:
    try:
        return await _call_fortinet_tool_async("discover_fortinet_topology")
    except HTTPException as http_exc:
        if http_exc.status_code not in {502, 503, 504}:
            raise
        logger.warning(
            "discover_fortinet_topology returned HTTP %s: %s; using fallback topology.",
            http_exc.status_code,
            http_exc.detail,
        )
    except Exception as exc:  # pragma: no cover - defensive path
        logger.warning("discover_fortinet_topology failed: %s; using fallback topology.", exc)
    return _fallback_topology_copy()


async def _load_scene_with_fallback() -> Dict[str, Any]:
    # 1. Try GraphML topology
    graphml_path = PROJECT_ROOT / "data/generated/combined_topology.graphml"
    if graphml_path.exists():
        try:
            logger.info(f"Loading topology from GraphML: {graphml_path}")
            scene = await asyncio.to_thread(parse_graphml_topology, str(graphml_path))
            if scene.get("nodes"):
                scene.setdefault("metadata", {})["source"] = "graphml"
                
                # Attempt to enrich with live connected devices from FortiGate
                try:
                    # Collect credentials from environment
                    creds_dict = _fortinet_credentials()
                    # Convert dict to FortiGateCredentialsModel
                    creds = FortiGateCredentialsModel(
                        host=f"{creds_dict.get('device_ip', '192.168.0.254')}:10443",
                        username=creds_dict.get('username', 'admin'),
                        password=creds_dict.get('password'),  # May contain token
                    )
                    collector = _create_fortigate_collector(creds)
                    if collector:
                        logger.info("Fetching live connected devices from FortiGate...")
                        if await collector.authenticate():
                            live_devices = await collector.get_connected_devices()
                            if live_devices:
                                logger.info(f"Found {len(live_devices)} connected devices")
                                # Merge live devices into scene
                                nodes = scene.get("nodes", [])
                                links = scene.get("links", [])
                                
                                # Find a suitable uplink (switch or firewall)
                                uplink_id = None
                                for n in nodes:
                                    dtype = (n.get("type") or "").lower()
                                    if "switch" in dtype:
                                        uplink_id = n["id"]
                                        break
                                if not uplink_id:
                                    for n in nodes:
                                        dtype = (n.get("type") or "").lower()
                                        if "fortigate" in dtype or "firewall" in dtype:
                                            uplink_id = n["id"]
                                            break
                                
                                if uplink_id:
                                    # Initialize matcher
                                    matcher = DeviceModelMatcher()
                                    
                                    for dev in live_devices:
                                        dev_id = f"dev-{dev.get('mac', 'unknown').replace(':', '')}"
                                        # Avoid duplicates
                                        if any(n["id"] == dev_id for n in nodes):
                                            continue
                                            
                                        # Match device to get type and model
                                        mac = dev.get("mac", "")
                                        host = dev.get("host") or dev.get("hostname") or dev.get("name") or ""
                                        match_info = matcher.match_mac_to_model(mac, {"hostname": host})
                                        
                                        # Preserve all device fields, especially connection_type, ssid, ap_name, os
                                        node_data = {
                                            "id": dev_id,
                                            "name": host or mac or "Unknown Device",
                                            "type": match_info.device_type,
                                            "ip": dev.get("ip"),
                                            "mac": mac,
                                            "vendor": match_info.vendor,
                                            "os": dev.get("os") or dev.get("os_name") or dev.get("software_os"),
                                            "status": dev.get("status", "online"),
                                            "model_path": match_info.model_path,
                                            "pos_system": match_info.pos_system,
                                            # Preserve connection metadata
                                            "connection_type": dev.get("connection_type"),
                                            "ssid": dev.get("ssid"),
                                            "ap_name": dev.get("ap_name"),
                                            "ap_sn": dev.get("ap_sn") or dev.get("wtp_id"),
                                            "switch_sn": dev.get("switch_sn"),
                                            "port": dev.get("port"),
                                            "vlan": dev.get("vlan"),
                                        }
                                        # Remove None values to keep the data clean
                                        node_data = {k: v for k, v in node_data.items() if v is not None}
                                        nodes.append(node_data)
                                        links.append({
                                            "from": uplink_id,
                                            "to": dev_id,
                                            "status": "active"
                                        })
                                        
                                scene["nodes"] = nodes
                                scene["links"] = links
                except Exception as e:
                    logger.warning(f"Failed to enrich topology with live devices: {e}")

                return scene
        except Exception as e:
            logger.error(f"Failed to load GraphML topology: {e}")

    # 2. Try JSON topology
    json_path = PROJECT_ROOT / "data/generated/combined_topology.json"
    if json_path.exists():
        try:
            logger.info(f"Loading topology from JSON: {json_path}")
            content = await asyncio.to_thread(json_path.read_text)
            scene = orjson.loads(content)
            if scene.get("nodes"):
                scene.setdefault("metadata", {})["source"] = "json"
                
                # Attempt to enrich with live connected devices from FortiGate
                try:
                    # Collect credentials from environment
                    creds_dict = _fortinet_credentials()
                    # Convert dict to FortiGateCredentialsModel
                    creds = FortiGateCredentialsModel(
                        host=f"{creds_dict.get('device_ip', '192.168.0.254')}:10443",
                        username=creds_dict.get('username', 'admin'),
                        password=creds_dict.get('password'),  # May contain token
                    )
                    collector = _create_fortigate_collector(creds)
                    if collector:
                        logger.info("Fetching live connected devices from FortiGate...")
                        if await collector.authenticate():
                            live_devices = await collector.get_connected_devices()
                            if live_devices:
                                logger.info(f"Found {len(live_devices)} connected devices")
                                # Merge live devices into scene
                                nodes = scene.get("nodes", [])
                                links = scene.get("links", [])
                                
                                # Find a suitable uplink (switch or firewall)
                                uplink_id = None
                                for n in nodes:
                                    dtype = (n.get("type") or "").lower()
                                    if "switch" in dtype:
                                        uplink_id = n["id"]
                                        break
                                if not uplink_id:
                                    for n in nodes:
                                        dtype = (n.get("type") or "").lower()
                                        if "fortigate" in dtype or "firewall" in dtype:
                                            uplink_id = n["id"]
                                            break
                                
                                if uplink_id:
                                    # Initialize matcher
                                    matcher = DeviceModelMatcher()
                                    
                                    for dev in live_devices:
                                        dev_id = f"dev-{dev.get('mac', 'unknown').replace(':', '')}"
                                        # Avoid duplicates
                                        if any(n["id"] == dev_id for n in nodes):
                                            continue
                                            
                                        # Match device to get type and model
                                        mac = dev.get("mac", "")
                                        host = dev.get("host") or dev.get("hostname") or dev.get("name") or ""
                                        match_info = matcher.match_mac_to_model(mac, {"hostname": host})
                                        
                                        # Preserve all device fields, especially connection_type, ssid, ap_name, os
                                        node_data = {
                                            "id": dev_id,
                                            "name": host or mac or "Unknown Device",
                                            "type": match_info.device_type,
                                            "ip": dev.get("ip"),
                                            "mac": mac,
                                            "vendor": match_info.vendor,
                                            "os": dev.get("os") or dev.get("os_name") or dev.get("software_os"),
                                            "status": dev.get("status", "online"),
                                            "model_path": match_info.model_path,
                                            "pos_system": match_info.pos_system,
                                            # Preserve connection metadata
                                            "connection_type": dev.get("connection_type"),
                                            "ssid": dev.get("ssid"),
                                            "ap_name": dev.get("ap_name"),
                                            "ap_sn": dev.get("ap_sn") or dev.get("wtp_id"),
                                            "switch_sn": dev.get("switch_sn"),
                                            "port": dev.get("port"),
                                            "vlan": dev.get("vlan"),
                                        }
                                        # Remove None values to keep the data clean
                                        node_data = {k: v for k, v in node_data.items() if v is not None}
                                        nodes.append(node_data)
                                        links.append({
                                            "from": uplink_id,
                                            "to": dev_id,
                                            "status": "active"
                                        })
                                        
                                scene["nodes"] = nodes
                                scene["links"] = links
                except Exception as e:
                    logger.warning(f"Failed to enrich topology with live devices: {e}")

                return scene
        except Exception as e:
            logger.error(f"Failed to load JSON topology: {e}")

    # 3. Fallback to discovery / sample
    topology = await _load_topology_raw_with_fallback()
    if (topology.get("metadata") or {}).get("source") == "fallback":
        scene = orjson.loads(orjson.dumps(_SAMPLE_SCENE))
        scene.setdefault("metadata", {})["source"] = "fallback"
        return scene
    scene = await asyncio.to_thread(_normalize_scene, topology)
    if not scene.get("nodes"):
        return _SAMPLE_SCENE
    return scene


def _call_fortinet_tool(tool_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Synchronous helper primarily for legacy utilities and tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_call_fortinet_tool_async(tool_name, params))
    else:
        raise RuntimeError(
            "Cannot call synchronous _call_fortinet_tool from within an active event loop. "
            "Use 'await _call_fortinet_tool_async(...)' instead."
        )
def _scene_to_lab_format(scene: Dict[str, Any]) -> Dict[str, Any]:
    """Convert normalized scene {"nodes","links"} to lab-style {"models","connections"} format.
    
    This matches the structure used in 3d-network-topology-lab/babylon_topology.json.
    Implements a hierarchical layout: Firewall -> Switch -> AP -> Clients.
    """
    nodes = scene.get("nodes") or []
    links = scene.get("links") or []

    # 1. Filter out interface/port nodes to clean up the view
    # Keep only physical devices (fortigate, fortiswitch, fortiap, etc.)
    device_nodes = []
    for n in nodes:
        dtype = (n.get("type") or "").lower()
        if dtype not in ("interface", "vlan", "tunnel", "vap-switch", "aggregate", "physical", "hard-switch"):
            device_nodes.append(n)
    
    # If we filtered everything (unlikely), revert to showing everything
    if not device_nodes and nodes:
        device_nodes = nodes

    # 2. Group by hierarchy tier
    tier_1 = [] # Firewalls / Gateways
    tier_2 = [] # Switches
    tier_3 = [] # Access Points
    tier_4 = [] # Clients / Others

    for node in device_nodes:
        dtype = (node.get("type") or "").lower()
        model = (node.get("model") or "").lower()
        role = (node.get("role") or "").lower()
        
        # Explicitly check for client/endpoint types
        if "fortigate" in dtype or "firewall" in dtype or "gateway" in dtype:
            tier_1.append(node)
        elif "fortiswitch" in dtype or ("switch" in dtype and "ap" not in dtype):
            tier_2.append(node)
        elif "fortiap" in dtype or "access_point" in dtype or "ap" in dtype:
            tier_3.append(node)
        elif "client" in dtype or "endpoint" in dtype or "device" in dtype or role in ("client", "endpoint"):
            # Explicitly include client/endpoint devices in tier_4
            tier_4.append(node)
        else:
            # Default to tier_4 for unknown devices (likely endpoints)
            tier_4.append(node)

    # 3. Assign Positions (Hierarchical Layout)
    # Y-axis represents tier level (Higher Y = Higher in hierarchy)
    # X-axis spreads devices within the tier
    
    models = []
    
    def layout_tier(tier_nodes, y_level, z_offset=0):
        count = len(tier_nodes)
        if count == 0:
            return
        
        # Spread width based on count
        spacing = 6.0
        start_x = -((count - 1) * spacing) / 2
        
        for i, node in enumerate(tier_nodes):
            node_id = node.get("id")
            
            # Use existing position if available and valid
            pos = node.get("position") or {}
            if pos.get("x") is not None and pos.get("y") is not None:
                x, y, z = pos["x"], pos["y"], pos["z"]
            else:
                x = start_x + (i * spacing)
                y = y_level
                z = z_offset
            
            device_type = (
                node.get("device_type")
                or node.get("type")
                or node.get("role")
                or "endpoint"
            )

            model_entry = {
                "id": node_id,
                "name": node.get("name") or node.get("hostname") or node_id,
                "type": device_type,
                "model": node.get("model_path") or node.get("device_model") or node.get("model"),
                "icon_svg": node.get("icon_svg"),  # Include SVG icon path for 3D extrusion
                "position": {"x": x, "y": y, "z": z},
                "status": node.get("status", "online"),
                "ip": node.get("ip"),
                "mac": node.get("mac"),
                "serial": node.get("serial"),
                "vendor": node.get("vendor"),
                "os": node.get("os"),  # Operating system
                "connection_type": node.get("connection_type"),  # wifi or ethernet
                "ssid": node.get("ssid"),  # WiFi SSID if applicable
                "ap_name": node.get("ap_name"),  # Associated AP name
                "ap_sn": node.get("ap_sn"),  # Associated AP serial number
            }
            models.append(model_entry)

    # Execute layout
    # Tier 1 (Firewall): Y = 10
    layout_tier(tier_1, 10.0)
    
    # Tier 2 (Switch): Y = 5
    layout_tier(tier_2, 5.0)
    
    # Tier 3 (AP): Y = 0
    layout_tier(tier_3, 0.0)
    
    # Tier 4 (Clients): Y = -5
    layout_tier(tier_4, -5.0)

    # 4. Process Connections
    # Only keep connections where both endpoints are in our filtered device list
    valid_ids = {m["id"] for m in models}
    connections = []
    
    # Heuristic: Find the primary switch to visually attach APs to
    # This matches the user's expected "Fortinet Network Topology" hierarchy
    primary_switch_id = None
    for m in models:
        if "switch" in (m.get("type") or "").lower():
            primary_switch_id = m["id"]
            break
            
    for link in links:
        src = link.get("from") or link.get("source")
        dst = link.get("to") or link.get("target")
        
        if src in valid_ids and dst in valid_ids:
            conn = {
                "from": src,
                "to": dst,
                "status": link.get("status", "active"),
            }
            connections.append(conn)

    return {"models": models, "connections": connections}


@app.get("/api/topology/raw")
async def get_topology_raw():
    """Return raw Fortinet topology JSON from discover_fortinet_topology tool."""
    data = await _load_topology_raw_with_fallback()
    return JSONResponse(data)


@app.get("/api/topology/scene")
async def get_topology_scene():
    """Return normalized 3D scene JSON sourced from the Fortinet MCP bridge."""
    scene = await _load_scene_with_fallback()
    return JSONResponse(scene)

@app.get("/api/topology/scene-enhanced")
async def get_topology_scene_enhanced():
    """Return enhanced 3D scene with device model matching and 3D model paths."""
    scene = await _load_scene_with_fallback()

    enhanced_scene = await asyncio.to_thread(_enhance_scene_with_models, scene)
    return JSONResponse(enhanced_scene)

@app.get("/api/topology/babylon-lab-format")
async def get_topology_babylon_lab_format():
    """Return topology in 3d-network-topology-lab JSON format (models/connections).

    This endpoint adapts the normalized scene used by the main Babylon viewer into the
    structure expected by the standalone 3D Network Topology Lab so that both tools can
    share the same discovery and MCP pipeline.
    """
    scene = await _load_scene_with_fallback()

    # Reuse the same enhancement pipeline used by /api/topology/scene-enhanced so that
    # lab-format models have VSS-derived / matcher-derived 3D model paths.
    enhanced_scene = await asyncio.to_thread(_enhance_scene_with_models, scene)
    lab_payload = await asyncio.to_thread(_scene_to_lab_format, enhanced_scene)
    return JSONResponse(lab_payload)


@app.post("/api/fortigate/topology-direct")
async def fortigate_topology_direct(request: FortiGateDirectRequest):
    """Collect FortiGate topology directly via FortiGateTopologyCollector.

    This bypasses the MCP bridge and talks to the FortiGate API using either
    per-request credentials or environment variables (FORTIMANAGER_HOST, etc.).
    """

    collector = _create_fortigate_collector(request.credentials)
    # Inject CA cert path if available
    ca_cert = os.getenv("CA_CERT_PATH")
    if ca_cert and hasattr(collector, "ca_cert_path"):
        collector.ca_cert_path = ca_cert
    
    topology = await collector.collect_topology()
    devices = topology.get("devices") or []
    if not devices:
        raise HTTPException(status_code=502, detail="No devices returned from FortiGate topology collector")
    return JSONResponse(topology)


@app.post("/api/fortigate/system-status")
async def fortigate_system_status(request: FortiGateDirectRequest):
    """Return FortiGate system status via direct API call."""

    collector = _create_fortigate_collector(request.credentials)
    if not await collector.authenticate():
        raise HTTPException(status_code=502, detail="FortiGate authentication failed")
    status = await collector.get_system_status()
    if not status:
        raise HTTPException(status_code=502, detail="FortiGate system status unavailable")
    return JSONResponse(status)


@app.post("/api/fortigate/firewall-policies")
async def fortigate_firewall_policies_summary(request: FortiGateDirectRequest):
    """Return a summary count of firewall policies on the FortiGate."""

    collector = _create_fortigate_collector(request.credentials)
    if not await collector.authenticate():
        raise HTTPException(status_code=502, detail="FortiGate authentication failed")
    count = await collector.get_firewall_policies_count()
    return JSONResponse({"policy_count": count})


@app.post("/api/fortigate/assets")
async def fortigate_assets(request: FortiGateDirectRequest):
    """Return endpoint/asset devices from FortiGate (Assets dashboard data).
    
    This endpoint provides the same data shown in the FortiGate Assets dashboard:
    - Device list with OS, IP addresses, status
    - Software OS distribution
    - Vulnerability levels
    - Online status
    """
    import requests
    from urllib.parse import urljoin
    
    base_url = request.credentials.host
    if "://" not in base_url:
        base_url = f"https://{base_url}"
    if not base_url.endswith("/api/v2"):
        base_url = urljoin(base_url, "/api/v2")
    
    headers = {"Content-Type": "application/json"}
    if request.credentials.token:
        headers["Authorization"] = f"Bearer {request.credentials.token}"
    
    session = requests.Session()
    session.verify = request.credentials.verify_ssl if hasattr(request.credentials, 'verify_ssl') else False
    
    # Try endpoints in order: wireless clients, switch clients, then user device endpoints
    endpoints_to_try = [
        "/monitor/wifi/client",  # Wireless clients (matches WiFi client table in web UI)
        "/monitor/user/device/select",
        "/monitor/user/device/query",
        "/monitor/endpoint-control/registered_ems",
    ]
    
    assets_data = None
    endpoint_used = None
    for endpoint in endpoints_to_try:
        try:
            url = urljoin(base_url, endpoint)
            logger.info(f"Trying FortiGate endpoint: {endpoint}")
            response = session.get(url, headers=headers, params={"vdom": "root"}, timeout=10)
            logger.info(f"Response status for {endpoint}: {response.status_code}")
            if response.status_code == 200:
                try:
                    assets_data = response.json()
                    results = assets_data.get("results") or assets_data.get("data") or []
                    if isinstance(results, dict):
                        results = results.get("entries", [])
                    if isinstance(results, list) and len(results) > 0:
                        logger.info(f"✅ Successfully fetched {len(results)} devices from {endpoint}")
                        endpoint_used = endpoint  # Track which endpoint succeeded
                        break
                    else:
                        logger.debug(f"Endpoint {endpoint} returned empty results")
                except Exception as json_err:
                    logger.warning(f"Failed to parse JSON from {endpoint}: {json_err}")
            else:
                logger.debug(f"Endpoint {endpoint} returned HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            logger.debug(f"Failed to fetch from {endpoint}: {e}")
            continue
    
    if not assets_data:
        raise HTTPException(
            status_code=404,
            detail="Assets/endpoint data not available. Endpoints tried: " + ", ".join(endpoints_to_try)
        )
    
    # Normalize the response format
    results = assets_data.get("results") or assets_data.get("data") or []
    if isinstance(results, dict):
        results = results.get("entries", [])
    if not isinstance(results, list):
        results = []
    
    return JSONResponse({
        "assets": results,
        "count": len(results),
        "endpoint_used": endpoint_used
    })


@app.post("/api/topology/drawio-xml", response_class=PlainTextResponse)
async def topology_drawio_xml(request: AutomatedDiagramRequest):
    """Generate a DrawIO XML diagram for the current Fortinet topology.

    Uses DrawIOFortinetIntegration, which currently bridges to the existing Fortinet
    MCP server format and produces a .drawio-compatible diagram.
    """

    integration = DrawIOFortinetIntegration()
    result = await integration.collect_and_generate(layout=request.layout or "hierarchical")
    xml_text: str = result.get("drawio_xml", "")
    if not xml_text:
        raise HTTPException(status_code=500, detail="DrawIO XML generation failed")
    # PlainTextResponse with XML media type so browsers/editors treat it as XML
    return PlainTextResponse(xml_text, media_type="application/xml; charset=utf-8")


@app.post("/api/topology/drawio-3d-scene")
async def topology_drawio_3d_scene(request: AutomatedDiagramRequest):
    """Generate 3D scene JSON derived from DrawIO-compatible topology."""

    integration = DrawIOFortinetIntegration()
    result = await integration.collect_and_generate(layout=request.layout or "hierarchical")
    scene = result.get("scene_data") or {}
    if not scene.get("nodes") and not scene.get("links"):
        raise HTTPException(status_code=500, detail="3D scene generation failed")
    return JSONResponse(scene)


@app.post("/api/intelligent-api/query")
async def intelligent_api_query(request: IntelligentAPIDocsQuery):
    """Query FortiGate/Meraki API documentation with natural language.

    This endpoint wraps the IntelligentAPIMCP documentation search capabilities and
    returns the top matching endpoints and their descriptions. It does *not* invoke
    any external LLMs, so it is safe to call without additional configuration.
    """

    api_mcp = IntelligentAPIMCP()
    docs = await api_mcp.query_api_documentation(request.query, device_type=request.device_type or "fortigate")
    return JSONResponse(docs)


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
        except RuntimeError as exc:  # pragma: no cover - best-effort cleanup
            logger.debug("Ignoring event loop error while closing Fortinet client: %s", exc)
        finally:
            _FORTINET_CLIENT = None
    if _SERVICE_HTTP_CLIENT:
        try:
            await _SERVICE_HTTP_CLIENT.aclose()
        except RuntimeError as exc:  # pragma: no cover - best-effort cleanup
            logger.debug("Ignoring event loop error while closing service client: %s", exc)
        finally:
            _SERVICE_HTTP_CLIENT = None
            _SERVICE_CLIENT_LOOP = None
    if _VLLM_CLIENT:
        try:
            await _VLLM_CLIENT.aclose()
        except RuntimeError as exc:  # pragma: no cover - best-effort cleanup
            logger.debug("Ignoring event loop error while closing vLLM client: %s", exc)
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

