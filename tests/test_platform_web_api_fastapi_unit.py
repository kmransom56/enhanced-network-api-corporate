import asyncio
import importlib
import json
from collections import deque
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

import httpx
import pytest
import requests
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.testclient import TestClient

import src.enhanced_network_api.platform_web_api_fastapi as api
from src.enhanced_network_api import fortigate_docs_search as docs_search
from src.enhanced_network_api.shared import topology_workflow


@pytest.fixture(autouse=True)
def restore_static_dir(monkeypatch, tmp_path):
    original_static = api.STATIC_DIR
    api._load_static_html.cache_clear()
    api._clear_platform_data_cache()
    api._SERVICE_HTTP_CLIENT = None
    api._SERVICE_CLIENT_LOOP = None
    api.PERF_RECORDER.reset()
    monkeypatch.setattr(api, "STATIC_DIR", tmp_path)
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_fortigate_payload",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_fortimanager_payload",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        api.topology_workflow,
        "_fetch_fortigate_payload",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        api.topology_workflow,
        "_fetch_fortimanager_payload",
        lambda *args, **kwargs: None,
    )
    yield tmp_path
    api._load_static_html.cache_clear()
    api._clear_platform_data_cache()
    api._SERVICE_HTTP_CLIENT = None
    api._SERVICE_CLIENT_LOOP = None
    api.PERF_RECORDER.reset()
    monkeypatch.setattr(api, "STATIC_DIR", original_static)


def test_serve_static_html_success(tmp_path):
    page = tmp_path / "smart-tools.html"
    page.write_text("<html>ok</html>", encoding="utf-8")
    response = api._serve_static_html(
        "smart-tools.html",
        missing_title="X",
        missing_message="Y",
    )
    assert response.status_code == 200
    assert b"ok" in response.body


def test_serve_static_html_missing():
    response = api._serve_static_html(
        "missing.html",
        missing_title="Missing",
        missing_message="Not found",
    )
    assert response.status_code == 404
    body = response.body.decode()
    assert "Missing" in body and "Not found" in body


def test_run_discovery_missing_binary(monkeypatch, tmp_path):
    missing_bin = tmp_path / "ai-platform"
    monkeypatch.setattr(api, "AI_PLATFORM_BINARY", missing_bin)
    assert api.run_discovery() is False


def test_run_discovery_success(monkeypatch, tmp_path):
    fake_bin = tmp_path / "ai-platform"
    fake_bin.write_text("#!/bin/bash\n", encoding="utf-8")
    calls: Dict[str, Any] = {}

    class FakeResult:
        returncode = 0

    def fake_run(cmd, capture_output, text, cwd, check):
        calls["cmd"] = cmd
        calls["cwd"] = cwd
        return FakeResult()

    monkeypatch.setattr(api, "AI_PLATFORM_BINARY", fake_bin)
    monkeypatch.setattr(api, "AI_PLATFORM_ROOT", tmp_path)
    monkeypatch.setattr(api.subprocess, "run", fake_run)
    assert api.run_discovery() is True
    assert fake_bin.as_posix() in calls["cmd"][0]
    assert calls["cwd"] == str(tmp_path)


def test_run_discovery_file_not_found(monkeypatch, tmp_path):
    fake_bin = tmp_path / "ai-platform"
    fake_bin.write_text("", encoding="utf-8")

    def fake_run(*args, **kwargs):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(api, "AI_PLATFORM_BINARY", fake_bin)
    monkeypatch.setattr(api, "AI_PLATFORM_ROOT", tmp_path)
    monkeypatch.setattr(api.subprocess, "run", fake_run)
    assert api.run_discovery() is False


def test_run_discovery_generic_exception(monkeypatch, tmp_path):
    fake_bin = tmp_path / "ai-platform"
    fake_bin.write_text("", encoding="utf-8")

    def fake_run(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(api, "AI_PLATFORM_BINARY", fake_bin)
    monkeypatch.setattr(api, "AI_PLATFORM_ROOT", tmp_path)
    monkeypatch.setattr(api.subprocess, "run", fake_run)
    assert api.run_discovery() is False


def test_load_platform_data_success(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "DISCOVERY_DIR", tmp_path)
    data_path = tmp_path / "platform_map.json"
    data_path.write_text(json.dumps({"value": 1}), encoding="utf-8")
    assert api.load_platform_data() == {"value": 1}


def test_load_platform_data_invalid(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(api, "DISCOVERY_DIR", tmp_path)
    data_path = tmp_path / "platform_map.json"
    data_path.write_text("{invalid", encoding="utf-8")
    assert api.load_platform_data() is None
    assert "Error loading platform data" in capsys.readouterr().out


def test_platform_file_mtime_missing(tmp_path):
    missing = tmp_path / "nope.json"
    assert api._platform_file_mtime(missing) is None


def test_load_platform_data_cache_hit(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "DISCOVERY_DIR", tmp_path)
    data_path = tmp_path / "platform_map.json"
    data_path.write_text(json.dumps({"value": 1}), encoding="utf-8")
    api._clear_platform_data_cache()
    api.load_platform_data()
    mtime = api._platform_file_mtime(data_path)
    api._PLATFORM_DATA_CACHE = {"mtime": mtime, "data": {"cached": True}}
    cached = api.load_platform_data()
    assert cached == {"cached": True}


def test_platform_static_endpoints(tmp_path):
    (tmp_path / "smart-tools.html").write_text("smart", encoding="utf-8")
    (tmp_path / "2d_topology_enhanced.html").write_text("2d", encoding="utf-8")
    (tmp_path / "babylon_test.html").write_text("babylon", encoding="utf-8")
    (tmp_path / "echarts_gl_test.html").write_text("echarts", encoding="utf-8")
    (tmp_path / "automated_topology.html").write_text("auto", encoding="utf-8")

    client = TestClient(api.app)
    assert client.get("/smart-tools").status_code == 200
    assert client.get("/automated-topology").status_code == 200
    assert client.get("/2d-topology-enhanced").status_code == 200
    assert client.get("/babylon-test").status_code == 200
    assert client.get("/echarts-gl-test").status_code == 200
    assert client.get("/").status_code == 200


def test_automated_topology_doc_route():
    client = TestClient(api.app)
    response = client.get("/docs/automated-topology")
    assert response.status_code == 200
    assert "Automated Topology Diagrams" in response.text


def test_docs_search_missing(tmp_path, monkeypatch):
    client = TestClient(api.app)
    monkeypatch.setattr(api, "_fortigate_docs_root", lambda: tmp_path / "missing")
    resp = client.get("/docs/search", params={"q": "vpn"})
    assert resp.status_code == 404


def test_docs_search_success(tmp_path, monkeypatch):
    client = TestClient(api.app)
    monkeypatch.setattr(api, "_fortigate_docs_root", lambda: tmp_path)
    monkeypatch.setattr(
        api,
        "search_docs",
        lambda root, query, limit=10: [
            {"title": "Doc", "path": "doc1", "snippet": "desc"}
        ],
    )
    resp = client.get("/docs/search", params={"q": "vpn", "limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "vpn"
    assert data["results"][0]["path"] == "doc1"


def test_docs_qa_empty_question():
    client = TestClient(api.app)
    resp = client.post("/docs/qa", json={"question": "   "})
    assert resp.status_code == 400


def test_docs_qa_success(monkeypatch, tmp_path):
    client = TestClient(api.app)
    monkeypatch.setattr(api, "_fortigate_docs_root", lambda: tmp_path)
    monkeypatch.setattr(
        api,
        "search_docs",
        lambda root, query, limit=5: [
            {"title": "Doc", "path": "doc1", "snippet": "desc"}
        ],
    )

    class FakeResponse:
        status_code = 200
        text = "OK"

        def json(self):
            return {"choices": [{"message": {"content": "Answer"}}]}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse()

        async def aclose(self):
            return None

    async def fake_get_vllm_client():
        return FakeAsyncClient()

    monkeypatch.setattr(api, "_get_vllm_client", fake_get_vllm_client)
    resp = client.post("/docs/qa", json={"question": "What is status?"})
    assert resp.status_code == 200
    assert resp.json()["answer"] == "Answer"


def test_docs_qa_missing_docs(monkeypatch, tmp_path):
    client = TestClient(api.app)
    monkeypatch.setattr(api, "_fortigate_docs_root", lambda: tmp_path / "missing")
    resp = client.post("/docs/qa", json={"question": "status"})
    assert resp.status_code == 404


def test_docs_qa_no_hits(monkeypatch, tmp_path):
    client = TestClient(api.app)
    monkeypatch.setattr(api, "_fortigate_docs_root", lambda: tmp_path)
    monkeypatch.setattr(api, "search_docs", lambda *args, **kwargs: [])
    resp = client.post("/docs/qa", json={"question": "status"})
    assert resp.status_code == 404


def test_docs_qa_vllm_request_error(monkeypatch, tmp_path):
    client = TestClient(api.app)
    monkeypatch.setattr(api, "_fortigate_docs_root", lambda: tmp_path)
    monkeypatch.setattr(
        api,
        "search_docs",
        lambda *args, **kwargs: [{"title": "Doc", "path": "doc1", "snippet": "desc"}],
    )

    class ErrorClient:
        def __init__(self, *args, **kwargs):
            self._request = httpx.Request("POST", "http://vllm/chat/completions")

        async def post(self, *args, **kwargs):
            raise httpx.RequestError("boom", request=self._request)

        async def aclose(self):
            return None

    async def fake_get_vllm_client():
        return ErrorClient()

    monkeypatch.setattr(api, "_get_vllm_client", fake_get_vllm_client)
    resp = client.post("/docs/qa", json={"question": "status"})
    assert resp.status_code == 502


def test_docs_qa_vllm_bad_status(monkeypatch, tmp_path):
    client = TestClient(api.app)
    monkeypatch.setattr(api, "_fortigate_docs_root", lambda: tmp_path)
    monkeypatch.setattr(
        api,
        "search_docs",
        lambda *args, **kwargs: [{"title": "Doc", "path": "doc1", "snippet": "desc"}],
    )

    class BadResponse:
        status_code = 500
        text = "fail"

        def json(self):
            return {}

    class BadClient:
        def __init__(self, *args, **kwargs):
            pass

        async def post(self, *args, **kwargs):
            return BadResponse()

        async def aclose(self):
            return None

    async def fake_get_vllm_client():
        return BadClient()

    monkeypatch.setattr(api, "_get_vllm_client", fake_get_vllm_client)
    resp = client.post("/docs/qa", json={"question": "status"})
    assert resp.status_code == 500


def test_docs_qa_vllm_no_choices(monkeypatch, tmp_path):
    client = TestClient(api.app)
    monkeypatch.setattr(api, "_fortigate_docs_root", lambda: tmp_path)
    monkeypatch.setattr(
        api,
        "search_docs",
        lambda *args, **kwargs: [{"title": "Doc", "path": "doc1", "snippet": "desc"}],
    )

    class EmptyResponse:
        status_code = 200
        text = "OK"

        def json(self):
            return {"choices": []}

    class EmptyClient:
        def __init__(self, *args, **kwargs):
            pass

        async def post(self, *args, **kwargs):
            return EmptyResponse()

        async def aclose(self):
            return None

    async def fake_get_vllm_client():
        return EmptyClient()

    monkeypatch.setattr(api, "_get_vllm_client", fake_get_vllm_client)
    resp = client.post("/docs/qa", json={"question": "status"})
    assert resp.status_code == 500


def test_docs_helper_functions(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "DOCS_DIR", tmp_path)
    root = api._fortigate_docs_root()
    assert root == tmp_path / "fortigate-api"
    monkeypatch.setenv("VLLM_BASE_URL", "http://localhost:1234/")
    monkeypatch.setenv("VLLM_MODEL_NAME", "lite-model")
    assert api._vllm_base_url() == "http://localhost:1234"
    assert api._vllm_model_name() == "lite-model"


def test_fortigate_docs_warm_index(tmp_path):
    root = tmp_path / "fortigate-api"
    root.mkdir()
    (root / "sample.html").write_text("<html><body>FortiLink reference</body></html>", encoding="utf-8")
    docs_search.warm_index(root)
    results = docs_search.search_docs(root, "FortiLink", limit=1)
    assert results and results[0]["title"]
    cache_file = root / ".cache" / "fortigate_docs_index.json"
    assert cache_file.exists()


def test_fortigate_docs_search_uses_persisted_index(tmp_path, monkeypatch):
    root = tmp_path / "fortigate-api"
    root.mkdir()
    (root / "doc.html").write_text("<html><body>FortiLink docs</body></html>", encoding="utf-8")
    docs_search.warm_index(root)
    docs_search._cached_index.cache_clear()
    docs_search._TREE_MTIME_CACHE.clear()

    def boom(*args, **kwargs):
        raise AssertionError("Should not rebuild index when persisted cache available")

    monkeypatch.setattr(docs_search, "_build_index", boom)
    results = docs_search.search_docs(root, "FortiLink", limit=1)
    assert results


@pytest.mark.asyncio
async def test_get_vllm_client_reuse(monkeypatch):
    created = []

    class StubClient:
        def __init__(self, base_url=None, timeout=None, raise_on_close=False):
            self.base_url = base_url
            self.timeout = timeout
            self.closed = False
            self.raise_on_close = raise_on_close
            created.append(self)

        async def post(self, *args, **kwargs):
            raise AssertionError("post should not be called in this test")

        async def aclose(self):
            self.closed = True
            if self.raise_on_close:
                raise RuntimeError("loop closed")

    monkeypatch.setenv("VLLM_BASE_URL", "http://localhost:8123")
    monkeypatch.setattr(api.httpx, "AsyncClient", lambda base_url, timeout: StubClient(base_url, timeout))
    api._VLLM_CLIENT = None
    api._VLLM_CLIENT_BASE = None

    client_first = await api._get_vllm_client()
    client_second = await api._get_vllm_client()
    assert client_first is client_second
    assert client_first.base_url == "http://localhost:8123"

    # Change base URL and ensure old client is closed
    monkeypatch.setenv("VLLM_BASE_URL", "http://localhost:9000")
    client_first.raise_on_close = True
    client_third = await api._get_vllm_client()
    assert client_third is not client_first
    assert client_first.closed is True


@pytest.mark.asyncio
async def test_startup_event_warm_index(monkeypatch, tmp_path):
    root = tmp_path / "fortigate-api"
    root.mkdir()
    called = {"count": 0}

    def fake_warm_index(target_root):
        assert target_root == root
        called["count"] += 1

    async def fake_to_thread(func, *args, **kwargs):
        func(*args, **kwargs)

    monkeypatch.setattr(api, "_fortigate_docs_root", lambda: root)
    monkeypatch.setattr(api, "warm_index", fake_warm_index)
    monkeypatch.setattr(api.asyncio, "to_thread", fake_to_thread)

    api._DOCS_INDEX_TASK = None
    await api.startup_event()
    assert api._DOCS_INDEX_TASK is not None
    await api._DOCS_INDEX_TASK
    assert called["count"] == 1
    api._DOCS_INDEX_TASK = None


@pytest.mark.asyncio
async def test_startup_event_skips_missing_docs(monkeypatch):
    monkeypatch.setattr(api, "_fortigate_docs_root", lambda: Path("missing-docs-root"))
    api._DOCS_INDEX_TASK = None
    await api.startup_event()
    assert api._DOCS_INDEX_TASK is None


def test_normalize_scene_caching(monkeypatch):
    payload = {
        "nodes": [
            {"id": "A", "name": "NodeA", "type": "switch"},
        ],
        "links": [],
        "metadata": {"tags": {"core", "edge"}, "details": object()},
    }

    api._SCENE_CACHE.clear()
    first = api._normalize_scene(payload)
    second = api._normalize_scene(payload)
    assert first is second
    assert "nodes" in first and first["nodes"][0]["id"] == "A"
    assert api._topology_signature({"metadata": {object(): 1}}) != ""


def test_fortigate_env_credentials_port(monkeypatch):
    monkeypatch.delenv("FORTIGATE_HOSTS", raising=False)
    monkeypatch.setenv("FORTIGATE_HOST", "192.168.0.254")
    monkeypatch.setenv("FORTIGATE_PORT", "10443")
    monkeypatch.setenv("FORTIGATE_TOKEN", "tok")
    monkeypatch.setenv("FORTIGATE_WIFI_HOST", "wifi.example.com:10443")
    monkeypatch.setenv("FORTIGATE_WIFI_TOKEN", "wifiTok")
    creds = topology_workflow._fortigate_env_credentials(None)
    assert creds is not None
    assert creds.host == "192.168.0.254:10443"
    assert creds.token == "tok"
    assert creds.wifi_host == "wifi.example.com:10443"
    assert creds.wifi_token == "wifiTok"


def test_fortigate_env_credentials_host_specific_port(monkeypatch):
    monkeypatch.delenv("FORTIGATE_HOSTS", raising=False)
    monkeypatch.delenv("FORTIGATE_PORT", raising=False)
    monkeypatch.setenv("FORTIGATE_HOST", "192.168.0.254")
    monkeypatch.setenv("FORTIGATE_192_168_0_254_PORT", "10443")
    monkeypatch.setenv("FORTIGATE_192_168_0_254_TOKEN", "tok")
    creds = topology_workflow._fortigate_env_credentials(None)
    assert creds is not None
    assert creds.host == "192.168.0.254:10443"
    assert creds.token == "tok"


def test_fortigate_session_login_success():
    class FakeResponse:
        def __init__(self, status_code=200, text="{}", headers=None):
            self.status_code = status_code
            self.text = text
            self._headers = headers or {}
            self.cookies = requests.cookies.RequestsCookieJar()

        def raise_for_status(self):
            return None

        @property
        def headers(self):
            return self._headers

    class FakeSession:
        def __init__(self):
            self.cookies = requests.cookies.RequestsCookieJar()
            self.calls = []
            self.headers = {}

        def get(self, url, timeout=None):
            self.calls.append(("get", url))
            return FakeResponse()

        def post(self, url, json=None, headers=None, data=None, timeout=None):
            self.calls.append(("post", url, json, data, headers))
            if url.endswith("/api/v2/authentication"):
                response = FakeResponse(
                    status_code=200,
                    text='{"authenticated": true}',
                    headers={
                        "set-cookie": "session_key=abc; path=/; HttpOnly\nccsrf_token=csrf-token; path=/",
                    },
                )
                self.cookies.set("session_key", "abc")
                self.cookies.set("ccsrf_token", "csrf-token")
                return response
            raise AssertionError(f"Unexpected POST {url}")

    session = FakeSession()
    creds = topology_workflow.FortiGateCredentials(
        host="fg.example.com:10443",
        username="admin",
        password="secret",
    )
    csrf = topology_workflow._fortigate_session_login(
        session,
        "https://fg.example.com:10443",
        creds,
    )
    assert csrf == "csrf-token"
    # Ensure modern JSON login path was used.
    _, url, json_body, _, headers = session.calls[-1]
    assert url.endswith("/api/v2/authentication")
    assert json_body == {"username": "admin", "password": "secret"}
    assert headers["Content-Type"] == "application/json"
    assert session.headers["X-CSRFTOKEN"] == "csrf-token"
    assert session.headers["X-Requested-With"] == "XMLHttpRequest"


def test_fortigate_session_login_legacy(monkeypatch):
    class FakeResponse:
        def __init__(self, status_code=200, text="1", headers=None):
            self.status_code = status_code
            self.text = text
            self.headers = headers or {}
            self.cookies = requests.cookies.RequestsCookieJar()

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"{self.status_code}")

    class FakeSession:
        def __init__(self):
            self.cookies = requests.cookies.RequestsCookieJar()
            self.calls = []
            self.headers = {}

        def get(self, url, timeout=None):
            self.calls.append(("get", url))
            return FakeResponse()

        def post(self, url, json=None, data=None, headers=None, timeout=None):
            self.calls.append(("post", url, json, data, headers))
            if url.endswith("/api/v2/authentication"):
                raise requests.RequestException("modern auth unavailable")
            if url.endswith("/logincheck"):
                response = FakeResponse()
                self.cookies.set("ccsrftoken", '"legacy-token"')
                return response
            raise AssertionError(f"Unexpected POST {url}")

    session = FakeSession()
    creds = topology_workflow.FortiGateCredentials(
        host="fg.example.com:10443",
        username="admin",
        password="secret",
    )
    csrf = topology_workflow._fortigate_session_login(session, "https://fg.example.com:10443", creds)
    assert csrf == "legacy-token"
    assert session.headers["X-CSRFTOKEN"] == "legacy-token"


def test_fetch_fortigate_payload_session_login(monkeypatch):
    reloaded = importlib.reload(topology_workflow)
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_fortigate_payload",
        reloaded._fetch_fortigate_payload,
        raising=False,
    )
    monkeypatch.setattr(
        api.topology_workflow,
        "_fetch_fortigate_payload",
        reloaded._fetch_fortigate_payload,
        raising=False,
    )

    class FakeResponse:
        def __init__(self, status_code, payload=None):
            self.status_code = status_code
            self._payload = payload or {}
            self.cookies = requests.cookies.RequestsCookieJar()

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"{self.status_code}")

        def json(self):
            return self._payload

    class FakeSession:
        def __init__(self):
            self.verify = False
            self.auth = None
            self.cookies = {}
            self.authenticated = False
            self.headers_seen = []
            self.headers = {}

        def get(self, url, headers=None, timeout=None):
            self.headers_seen.append(headers or {})
            path = urlparse(url).path
            if not self.authenticated:
                return FakeResponse(401)
            if path == "/api/v2/monitor/system/status":
                return FakeResponse(
                    200,
                    {"serial": "FG1", "results": {"hostname": "FGT", "management-ip": "192.168.0.254"}},
                )
            if path == "/api/v2/cmdb/system/interface":
                return FakeResponse(
                    200,
                    {"results": [{"name": "port1", "ip": "192.168.0.1"}]},
                )
            if path == "/api/v2/cmdb/switch-controller/managed-switch":
                return FakeResponse(
                    200,
                    {"results": [{"name": "Switch1", "serial": "SW1"}]},
                )
            if path == "/api/v2/monitor/wifi/managed-ap":
                return FakeResponse(404)
            if path == "/api/v2/cmdb/wireless-controller/wtp":
                return FakeResponse(
                    200,
                    {"results": [{"name": "AP1", "serial": "AP1"}]},
                )
            return FakeResponse(200, {})

        def post(self, url, data=None, timeout=None):
            self.authenticated = True
            self.cookies["ccsrftoken"] = '"token123"'
            return FakeResponse(200, {})

    fake_session = FakeSession()
    def fake_api_session(base, creds):
        fake_session.authenticated = True
        fake_session.headers.update({"X-CSRFTOKEN": "token123"})
        return fake_session

    monkeypatch.setattr(
        topology_workflow,
        "_fortigate_api_session",
        fake_api_session,
    )
    monkeypatch.setattr(
        topology_workflow.requests,
        "Session",
        lambda: fake_session,
    )

    creds = topology_workflow.FortiGateCredentials(
        host="192.168.0.254:10443",
        username="admin",
        password="secret",
    )
    payload = topology_workflow._fetch_fortigate_payload(creds)
    assert payload is not None
    data, source = payload
    assert source == "fortigate:192.168.0.254:10443"
    device_ids = {item["id"] for item in data["fabric_devices"]}
    assert {"FG1", "port-port1", "switch-Switch1", "ap-AP1"}.issubset(device_ids)
    assert any("X-CSRFTOKEN" in headers for headers in fake_session.headers_seen)


def test_fetch_wifi_override_session_login(monkeypatch):
    class FakeResponse:
        def __init__(self, status_code, payload=None):
            self.status_code = status_code
            self._payload = payload or {}
            self.cookies = requests.cookies.RequestsCookieJar()

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"{self.status_code}")

        def json(self):
            return self._payload

    class FakeSession:
        def __init__(self):
            self.verify = False
            self.cookies = {}
            self.authenticated = False
            self.calls = []
            self.headers = {}

        def get(self, url, headers=None, timeout=None):
            self.calls.append(("get", url, headers))
            if not self.authenticated:
                return FakeResponse(401)
            return FakeResponse(
                200,
                {"results": [{"name": "AP-01", "serial": "AP01"}]},
            )

        def post(self, url, data=None, timeout=None):
            self.calls.append(("post", url, data))
            self.authenticated = True
            self.cookies["ccsrftoken"] = '"wifi-token"'
            return FakeResponse(200, {})

    sessions: list[FakeSession] = []

    def session_factory():
        session = FakeSession()
        sessions.append(session)
        return session

    monkeypatch.setattr(topology_workflow.requests, "Session", session_factory)
    def fake_api_session(base, creds):
        session = sessions[-1]
        session.authenticated = True
        session.headers.update({"X-CSRFTOKEN": "wifi-token"})
        return session

    monkeypatch.setattr(
        topology_workflow,
        "_fortigate_api_session",
        fake_api_session,
    )

    creds = topology_workflow.FortiGateCredentials(
        host="192.168.0.254:10443",
        username="admin",
        password="secret",
        wifi_host="fw.example.com:10443",
    )
    aps = topology_workflow._fetch_wifi_override(creds)
    assert aps and aps[0]["name"] == "AP-01"
    session = sessions[0]
    assert session.authenticated is True
    assert any(call[0] == "get" for call in session.calls)


def test_render_markdown_doc_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "DOCS_DIR", tmp_path)
    with pytest.raises(HTTPException):
        api._render_markdown_doc("missing.md", title="Missing")


def test_platform_static_fallback(tmp_path):
    client = TestClient(api.app)
    resp = client.get("/smart-tools")
    assert resp.status_code == 404
    assert "Smart Analysis Tools" in resp.text


@pytest.fixture
def platform_map(tmp_path, monkeypatch):
    data = {
        "service_mapping": {
            "9876": {
                "container": "demo-service",
                "status": "running",
                "image": "demo:latest",
            }
        },
        "categories": {"automation": ["demo-service"]},
        "docker_containers": {},
        "discovered_ports": {},
        "discovery_time": "now",
    }
    monkeypatch.setattr(api, "DISCOVERY_DIR", tmp_path)
    (tmp_path / "platform_map.json").write_text(json.dumps(data), encoding="utf-8")
    return data


class DummyAsyncResponse:
    def __init__(self, status_code=200, headers=None, text="OK"):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text


class DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        self.request_args = None
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def request(self, method, url, headers=None, content=None):
        self.request_args = (method, url, headers or {}, content)
        return DummyAsyncResponse()

    async def aclose(self):
        self.closed = True


def test_call_service_success(monkeypatch, platform_map):
    dummy_client = DummyAsyncClient()
    monkeypatch.setattr(api.httpx, "AsyncClient", lambda timeout=10.0: dummy_client)
    client = TestClient(api.app)
    resp = client.post(
        "/api/platform/service/1/call",
        json={"method": "get", "path": "/health", "headers": {"X": "1"}},
    )
    assert resp.status_code == 200
    method, url, headers, _ = dummy_client.request_args
    assert method == "GET"
    assert url.endswith("/health")
    assert headers["X"] == "1"


def test_call_service_invalid(platform_map):
    client = TestClient(api.app)
    resp = client.post("/api/platform/service/99/call", json={})
    assert resp.status_code == 400


def test_call_service_platform_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "DISCOVERY_DIR", tmp_path)
    client = TestClient(api.app)
    resp = client.post("/api/platform/service/1/call", json={})
    assert resp.status_code == 404


def test_platform_status_active(platform_map):
    client = TestClient(api.app)
    resp = client.get("/api/platform/status")
    assert resp.json()["status"] == "active"


def test_platform_status_not_discovered(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "DISCOVERY_DIR", tmp_path)
    client = TestClient(api.app)
    resp = client.get("/api/platform/status")
    assert resp.json()["status"] == "not_discovered"


def test_discover_platform_success(monkeypatch):
    async def immediate(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(api, "run_discovery", lambda: True)
    monkeypatch.setattr(api, "load_platform_data", lambda refresh=False: {"ok": True})
    monkeypatch.setattr(api.asyncio, "to_thread", immediate)
    client = TestClient(api.app)
    resp = client.post("/api/platform/discover")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_discover_platform_failure(monkeypatch):
    async def immediate(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(api, "run_discovery", lambda: False)
    monkeypatch.setattr(api.asyncio, "to_thread", immediate)
    client = TestClient(api.app)
    resp = client.post("/api/platform/discover")
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_discover_platform_triggers_auto_drawio(monkeypatch):
    async def immediate(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(api, "run_discovery", lambda: True)
    monkeypatch.setattr(api, "load_platform_data", lambda refresh=False: {"ok": True})
    monkeypatch.setattr(api.asyncio, "to_thread", immediate)

    captured = []

    def fake_create_task(coro):
        captured.append(coro)
        coro.close()

        class DummyTask:
            def cancel(self):
                pass

        return DummyTask()

    monkeypatch.setenv("AUTO_DRAWIO_EXPORT", "1")
    monkeypatch.setattr(api.asyncio, "create_task", fake_create_task)

    client = TestClient(api.app)
    resp = client.post("/api/platform/discover")
    assert resp.status_code == 200
    assert captured, "Expected DrawIO export coroutine to be scheduled"

    monkeypatch.delenv("AUTO_DRAWIO_EXPORT")


@pytest.mark.asyncio
async def test_discover_platform_no_auto_drawio_when_disabled(monkeypatch):
    async def immediate(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setenv("AUTO_DRAWIO_EXPORT", "0")
    monkeypatch.setattr(api, "run_discovery", lambda: True)
    monkeypatch.setattr(api, "load_platform_data", lambda refresh=False: {"ok": True})
    monkeypatch.setattr(api.asyncio, "to_thread", immediate)

    def fail_create_task(_coro):
        raise AssertionError("create_task should not be called")

    monkeypatch.setattr(api.asyncio, "create_task", fail_create_task)

    client = TestClient(api.app)
    resp = client.post("/api/platform/discover")
    assert resp.status_code == 200


def test_auto_drawio_request_env(monkeypatch):
    monkeypatch.setenv("AUTO_DRAWIO_LAYOUT", "circular")
    monkeypatch.setenv("AUTO_DRAWIO_GROUP_BY", "vendor")
    monkeypatch.setenv("AUTO_DRAWIO_DETAILS", "false")
    monkeypatch.setenv("AUTO_DRAWIO_COLOR", "0")
    monkeypatch.setenv("AUTO_DRAWIO_REFRESH", "no")
    monkeypatch.setenv("AUTO_DRAWIO_WRITE_FILE", "0")
    monkeypatch.setenv("AUTO_DRAWIO_OUTPUT_DIR", "/tmp/output")
    monkeypatch.setenv("AUTO_DRAWIO_FILENAME", "custom.drawio")

    request = api._auto_drawio_request()
    assert request.layout == "circular"
    assert request.group_by == "vendor"
    assert request.show_details is False
    assert request.color_code is False
    assert request.refresh_topology is False
    assert request.write_file is False
    assert request.output_dir == "/tmp/output"
    assert request.filename == "custom.drawio"

    for key in [
        "AUTO_DRAWIO_LAYOUT",
        "AUTO_DRAWIO_GROUP_BY",
        "AUTO_DRAWIO_DETAILS",
        "AUTO_DRAWIO_COLOR",
        "AUTO_DRAWIO_REFRESH",
        "AUTO_DRAWIO_WRITE_FILE",
        "AUTO_DRAWIO_OUTPUT_DIR",
        "AUTO_DRAWIO_FILENAME",
    ]:
        monkeypatch.delenv(key)


@pytest.mark.asyncio
async def test_auto_drawio_export_after_discovery(monkeypatch):
    recorded = {}

    async def fake_generate(payload):
        recorded["payload"] = payload
        return {"diagram_xml": "<xml/>"}

    monkeypatch.setattr(api, "_generate_drawio_via_mcp", fake_generate)
    monkeypatch.setenv("AUTO_DRAWIO_LAYOUT", "force-directed")
    monkeypatch.setenv("AUTO_DRAWIO_WRITE_FILE", "1")

    await api._auto_drawio_export_after_discovery()
    assert "payload" in recorded
    assert recorded["payload"].layout == "force-directed"
    assert recorded["payload"].write_file is True

    monkeypatch.delenv("AUTO_DRAWIO_LAYOUT")
    monkeypatch.delenv("AUTO_DRAWIO_WRITE_FILE")


@pytest.mark.asyncio
async def test_mcp_export_topology_json(monkeypatch):
    async def fake_call(name, params):
        return {"nodes": []}

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.post(
        "/mcp/export_topology_json",
        json={"include_health": True, "format": "detailed"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"nodes": []}


@pytest.mark.asyncio
async def test_mcp_export_topology_json_error(monkeypatch):
    async def fake_call(name, params):
        raise RuntimeError("boom")

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.post("/mcp/export_topology_json", json={})
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_mcp_generate_drawio_diagram(monkeypatch):
    calls: List[Tuple[str, Dict[str, Any]]] = []

    async def fake_call(name, params):
        calls.append((name, params))
        return {"content": "<xml/>"}

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.post("/mcp/generate_drawio_diagram", json={"layout": "circular"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["diagram_xml"] == "<xml/>"
    assert data["layout"] == "circular"
    assert calls == [("generate_drawio_diagram", {"layout": "circular", "group_by": "type", "show_details": True, "color_code": True})]


@pytest.mark.asyncio
async def test_generate_automated_drawio_writes_file(monkeypatch, tmp_path):
    calls: List[Tuple[str, Dict[str, Any]]] = []

    async def fake_call(name, params):
        calls.append((name, params))
        if name == "generate_drawio_diagram":
            return {"content": "<xml>diagram</xml>"}
        return {}

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    monkeypatch.setattr(api.topology_workflow, "DEFAULT_OUTPUT_DIR", tmp_path)

    client = TestClient(api.app)
    payload = {
        "write_file": True,
        "filename": "mcp_diagram.drawio",
        "refresh_topology": True,
        "layout": "hierarchical",
        "group_by": "vendor",
        "show_details": False,
        "color_code": False,
    }
    resp = client.post("/api/topology/automated/drawio", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["diagram_xml"] == "<xml>diagram</xml>"
    assert data["artifacts"]["drawio_path"].endswith("mcp_diagram.drawio")
    drawio_file = tmp_path / "mcp_diagram.drawio"
    assert drawio_file.read_text() == "<xml>diagram</xml>"
    assert calls[0][0] == "collect_topology"
    assert calls[1][0] == "generate_drawio_diagram"


@pytest.mark.asyncio
async def test_generate_automated_drawio_invalid_filename(monkeypatch):
    async def fake_call(name, params):
        return {"content": "<xml/>"}

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.post(
        "/api/topology/automated/drawio",
        json={"write_file": True, "filename": "../bad.drawio"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_generate_automated_drawio_missing_content(monkeypatch):
    async def fake_call(name, params):
        return {}

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.post("/api/topology/automated/drawio", json={})
    assert resp.status_code == 502


@pytest.mark.asyncio
async def test_generate_automated_drawio_invalid_payload_type(monkeypatch):
    async def fake_call(name, params):
        return "<xml/>"

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.post("/api/topology/automated/drawio", json={})
    assert resp.status_code == 502


@pytest.mark.asyncio
async def test_mcp_generate_drawio_with_metadata(monkeypatch):
    async def fake_call(name, params):
        return {"diagram_xml": "<xml/>", "summary": {"devices": 5}}

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.post("/mcp/generate_drawio_diagram", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["metadata"] == {"summary": {"devices": 5}}


@pytest.mark.asyncio
async def test_mcp_generate_drawio_exception(monkeypatch):
    async def fake_call(name, params):
        raise RuntimeError("bridge down")

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.post("/mcp/generate_drawio_diagram", json={})
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_mcp_discover_fortinet_topology_success(monkeypatch):
    async def fake_call(name, params):
        return {"result": "ok"}

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.post("/mcp/discover_fortinet_topology", json={"device_ip": "a"})
    assert resp.status_code == 200
    assert resp.json()["result"] == "ok"


@pytest.mark.asyncio
async def test_mcp_discover_fortinet_topology_failure(monkeypatch):
    async def fake_call(name, params):
        raise RuntimeError("error")

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.post("/mcp/discover_fortinet_topology", json={})
    assert resp.status_code == 500


def test_list_services_success(platform_map):
    client = TestClient(api.app)
    resp = client.get("/api/platform/services")
    payload = resp.json()
    assert payload["services"][0]["name"] == "demo-service"


def test_list_services_no_platform(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "DISCOVERY_DIR", tmp_path)
    client = TestClient(api.app)
    resp = client.get("/api/platform/services")
    assert resp.status_code == 404


def test_open_service_success(platform_map):
    client = TestClient(api.app)
    resp = client.post("/api/platform/service/1/open")
    assert resp.json()["action"].startswith("window.open")


def test_open_service_invalid(platform_map):
    client = TestClient(api.app)
    resp = client.post("/api/platform/service/99/open")
    assert resp.status_code == 400


def test_fortinet_credentials(monkeypatch):
    monkeypatch.setenv("FORTIGATE_HOSTS", "10.0.0.1,10.0.0.2")
    monkeypatch.setenv("FORTIGATE_USERNAME", "user")
    monkeypatch.setenv("FORTIGATE_10_0_0_1_TOKEN", "secret")
    creds = api._fortinet_credentials()
    assert creds["device_ip"] == "10.0.0.1"
    assert creds["username"] == "user"
    assert creds["password"] == "secret"


def test_fortinet_credentials_defaults(monkeypatch):
    monkeypatch.delenv("FORTIGATE_HOSTS", raising=False)
    monkeypatch.delenv("FORTIGATE_USERNAME", raising=False)
    monkeypatch.delenv("FORTIGATE_PASSWORD", raising=False)
    monkeypatch.delenv("FORTIGATE_192_168_0_254_TOKEN", raising=False)
    monkeypatch.delenv("FORTIGATE_WIFI_HOST", raising=False)
    monkeypatch.delenv("FORTIGATE_WIFI_TOKEN", raising=False)
    creds = api._fortinet_credentials()
    assert creds["username"] == "admin"
    assert isinstance(creds["password"], str)


def test_fortinet_mcp_http_url(monkeypatch):
    monkeypatch.setenv("FORTINET_MCP_HTTP_URL", "http://example.com")
    assert api._fortinet_mcp_http_url() == "http://example.com"


class MockResponse:
    def __init__(self, status_code=200, json_payload=None):
        self.status_code = status_code
        self._json_payload = json_payload or {}

    def json(self):
        return self._json_payload

    @property
    def text(self):
        return json.dumps(self._json_payload)


class MockSession:
    def __init__(self, responses):
        self.responses = responses
        self.calls = 0

    async def post(self, url, json):
        response = self.responses[self.calls]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_fortinet_client_cache(monkeypatch):
    responses = [
        MockResponse(
            json_payload={"content": [{"text": '{"devices":[{"id":"a","type":"fortigate"}],"links":[]}'}]}
        )
    ]
    session = MockSession(responses)
    client = api.FortinetMCPClient(
        url="http://mcp",
        credentials={"device_ip": "x"},
        session=session,
        cache_lock=asyncio.Lock(),
        loop=asyncio.get_running_loop(),
    )
    monkeypatch.setattr(api.time, "monotonic", lambda: 0.0)
    await client.call("discover_fortinet_topology", None)
    # second call should hit cache
    await client.call("discover_fortinet_topology", None)
    assert session.calls == 1
    await client.close()


@pytest.mark.asyncio
async def test_fortinet_client_refresh_cache(monkeypatch):
    responses = [
        MockResponse(json_payload={"content": [{"text": '{"devices":[],"links":[]}'}]}),
        MockResponse(json_payload={"content": [{"text": '{"devices":[],"links":[]}'}]}),
    ]
    session = MockSession(responses)
    client = api.FortinetMCPClient(
        url="http://mcp",
        credentials={"device_ip": "x"},
        session=session,
        cache_lock=asyncio.Lock(),
        loop=asyncio.get_running_loop(),
    )
    monkeypatch.setattr(api.time, "monotonic", lambda: 0.0)
    await client.call("discover_fortinet_topology", {"refresh_cache": True})
    await client.call("discover_fortinet_topology", {"refresh_cache": True})
    assert session.calls == 2
    await client.close()


@pytest.mark.asyncio
async def test_fortinet_client_request_error():
    session = MockSession([httpx.RequestError("boom", request=None)])
    client = api.FortinetMCPClient(
        url="http://mcp",
        credentials={},
        session=session,
        cache_lock=asyncio.Lock(),
        loop=asyncio.get_running_loop(),
    )
    with pytest.raises(HTTPException) as exc:
        await client.call("discover_fortinet_topology", None)
    assert exc.value.status_code == 502
    await client.close()


@pytest.mark.asyncio
async def test_fortinet_client_http_error():
    session = MockSession([MockResponse(status_code=500, json_payload={"message": "failure"})])
    client = api.FortinetMCPClient(
        url="http://mcp",
        credentials={},
        session=session,
        cache_lock=asyncio.Lock(),
        loop=asyncio.get_running_loop(),
    )
    with pytest.raises(HTTPException) as exc:
        await client.call("discover_fortinet_topology", None)
    assert exc.value.status_code == 500
    await client.close()


@pytest.mark.asyncio
async def test_fortinet_client_error_flag():
    payload = {"isError": True}
    session = MockSession([MockResponse(json_payload=payload)])
    client = api.FortinetMCPClient(
        url="http://mcp",
        credentials={},
        session=session,
        cache_lock=asyncio.Lock(),
        loop=asyncio.get_running_loop(),
    )
    with pytest.raises(HTTPException):
        await client.call("discover_fortinet_topology", None)
    await client.close()


@pytest.mark.asyncio
async def test_fortinet_client_json_fallback(monkeypatch):
    responses = [
        MockResponse(json_payload={"content": [{"text": "not-json"}]}),
        MockResponse(json_payload={"content": []}),
    ]
    session = MockSession(responses)
    client = api.FortinetMCPClient(
        url="http://mcp",
        credentials={},
        session=session,
        cache_lock=asyncio.Lock(),
        loop=asyncio.get_running_loop(),
    )
    monkeypatch.setattr(api.time, "monotonic", lambda: 0.0)
    result = await client.call("discover_fortinet_topology", None)
    assert result == {"content": "not-json"}
    await client.close()


@pytest.mark.asyncio
async def test_get_fortinet_client_reuse(monkeypatch):
    api._FORTINET_CLIENT = None
    created = []

    class DummyFortinetClient:
        def __init__(self, url, credentials, session, loop, cache_ttl=10.0):
            self.url = url
            self.credentials = credentials
            self.session = session
            self.loop = loop
            self.cache = {}
            self.cache_lock = asyncio.Lock()
            created.append(self)

        async def close(self):
            pass

        async def call(self, tool_name, extra_arguments):
            return {"devices": [], "links": []}

    async_client = httpx.AsyncClient(base_url="http://dummy")
    monkeypatch.setattr(api.httpx, "AsyncClient", lambda base_url, timeout: async_client)
    monkeypatch.setattr(api, "FortinetMCPClient", DummyFortinetClient)
    monkeypatch.setenv("FORTIGATE_HOSTS", "10.1.1.1")

    first = await api._get_fortinet_client()
    second = await api._get_fortinet_client()

    assert first is second
    assert len(created) == 1
    api._FORTINET_CLIENT = None
    await async_client.aclose()


@pytest.mark.asyncio
async def test_get_fortinet_client_closes_on_change(monkeypatch):
    class DummyFortinetClient:
        def __init__(self, url, credentials, session, loop, cache_ttl=10.0):
            self.url = url
            self.credentials = credentials
            self.session = session
            self.loop = loop
            self.cache = {}
            self.cache_lock = asyncio.Lock()
            self.closed = False

        async def close(self):
            self.closed = True

        async def call(self, tool_name, extra_arguments):
            return {}

    async_client = httpx.AsyncClient(base_url="http://dummy")
    monkeypatch.setattr(api.httpx, "AsyncClient", lambda base_url, timeout: async_client)
    monkeypatch.setattr(api, "FortinetMCPClient", DummyFortinetClient)
    api._FORTINET_CLIENT = DummyFortinetClient(
        url="http://old", credentials={}, session=None, loop=asyncio.get_running_loop()
    )
    monkeypatch.setenv("FORTINET_MCP_HTTP_URL", "http://new")

    new_client = await api._get_fortinet_client()
    assert new_client.url == "http://new"
    assert api._FORTINET_CLIENT is new_client
    await async_client.aclose()


@pytest.mark.asyncio
async def test_call_fortinet_tool_async(monkeypatch):
    class DummyClient:
        async def call(self, tool_name, extra_arguments):
            return {"result": tool_name}

    async def fake_get_client():
        return DummyClient()

    monkeypatch.setattr(api, "_get_fortinet_client", fake_get_client)
    result = await api._call_fortinet_tool_async("demo")
    assert result == {"result": "demo"}


def test_call_fortinet_tool_sync(monkeypatch):
    async def fake_async(tool_name, extra_arguments=None):
        return {"tool": tool_name}

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_async)
    result = api._call_fortinet_tool("name")
    assert result == {"tool": "name"}


@pytest.mark.asyncio
async def test_call_fortinet_tool_sync_in_loop():
    with pytest.raises(RuntimeError):
        api._call_fortinet_tool("demo")


@pytest.mark.asyncio
async def test_get_topology_raw(monkeypatch):
    async def fake_call(name, extra=None):
        return {"devices": []}

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.get("/api/topology/raw")
    assert resp.json() == {"devices": []}


@pytest.mark.asyncio
async def test_get_topology_scene_success(monkeypatch):
    async def fake_call(name, extra=None):
        return {"devices": [{"id": "a", "type": "fortigate"}], "links": []}

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.get("/api/topology/scene")
    assert resp.json()["nodes"][0]["id"] == "a"


@pytest.mark.asyncio
async def test_get_topology_scene_http_error(monkeypatch):
    async def fake_call(name, extra=None):
        raise HTTPException(status_code=502, detail="down")

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.get("/api/topology/scene")
    assert resp.json()["nodes"][0]["id"] == "fg-core"


@pytest.mark.asyncio
async def test_get_topology_scene_exception(monkeypatch):
    async def fake_call(name, extra=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.get("/api/topology/scene")
    assert resp.json()["nodes"][0]["id"] == "fg-core"


@pytest.mark.asyncio
async def test_get_topology_scene_no_nodes(monkeypatch):
    async def fake_call(name, extra=None):
        return {"devices": []}

    monkeypatch.setattr(api, "_call_fortinet_tool_async", fake_call)
    client = TestClient(api.app)
    resp = client.get("/api/topology/scene")
    assert resp.json()["nodes"][0]["id"] == "fg-core"


def test_normalize_scene_from_string():
    payload = json.dumps({"devices": [{"id": "node1", "type": "fortigate"}], "links": []})
    result = api._normalize_scene(payload)
    assert result["nodes"][0]["id"] == "node1"


def test_normalize_scene_with_edges():
    topology = {
        "nodes": [{"id": "a", "type": "fortigate", "extra": 1}],
        "edges": [{"source": "a", "target": "b", "interfaces": ["p1", "p2"]}],
    }
    result = api._normalize_scene(topology)
    assert result["nodes"][0]["id"] == "a"
    assert result["links"][0]["ports"] == ["p1", "p2"]


def test_health_check_success():
    client = TestClient(api.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_health_check_failure(monkeypatch):
    real_json_response = api.JSONResponse

    def flaky_json_response(*args, **kwargs):
        if not hasattr(flaky_json_response, "called"):
            flaky_json_response.called = True
            raise RuntimeError("failure")
        return real_json_response(*args, **kwargs)

    monkeypatch.setattr(api, "JSONResponse", flaky_json_response)
    client = TestClient(api.app)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"


def test_path_from_env_expanduser(monkeypatch, tmp_path):
    monkeypatch.setenv("EXPAND_PATH", "~/custom_path")
    expanded = api._path_from_env("EXPAND_PATH", tmp_path)
    assert expanded == Path("~/custom_path").expanduser()


def test_path_from_env_empty(monkeypatch, tmp_path):
    monkeypatch.setenv("EMPTY_PATH", "")
    assert api._path_from_env("EMPTY_PATH", tmp_path) == tmp_path


class ErrorClient(DummyAsyncClient):
    async def request(self, method, url, headers=None, content=None):
        raise httpx.RequestError("boom", request=None)


def test_call_service_request_error(monkeypatch, platform_map):
    monkeypatch.setattr(api.httpx, "AsyncClient", lambda timeout=10.0: ErrorClient())
    client = TestClient(api.app)
    resp = client.post("/api/platform/service/1/call", json={})
    assert resp.status_code == 500


def test_normalize_scene_invalid_json():
    result = api._normalize_scene('{"invalid"}')
    assert result == {"nodes": [], "links": []}


def test_normalize_scene_non_dict_devices():
    topology = {"devices": ["bad", {"type": "fortigate"}], "links": [{"from": "a"}, {"from": "a", "to": "b"}]}
    result = api._normalize_scene(topology)
    assert result["nodes"] == []
    assert result["links"] == [{"from": "a", "to": "b"}]


def test_normalize_scene_non_mapping_links():
    topology = {"devices": [{"id": "a", "type": "fortigate"}], "links": ["bad", {"source": "a", "target": "b"}]}
    result = api._normalize_scene(topology)
    assert result["links"][0]["from"] == "a"


@pytest.mark.asyncio
async def test_fortinet_client_no_content():
    session = MockSession([MockResponse(json_payload={})])
    client = api.FortinetMCPClient(
        url="http://mcp",
        credentials={},
        session=session,
        cache_lock=asyncio.Lock(),
        loop=asyncio.get_running_loop(),
    )
    result = await client.call("other_tool", None)
    assert result == {}
    await client.close()


@pytest.mark.asyncio
async def test_get_fortinet_client_close_error(monkeypatch):
    class CloseErrorClient:
        def __init__(self):
            self.url = "http://old"
            self.credentials = {}
            self.cache = {}
            self.cache_lock = asyncio.Lock()
            self.loop = asyncio.get_running_loop()

        async def close(self):
            raise RuntimeError("closed")

    api._FORTINET_CLIENT = CloseErrorClient()

    class DummyFortinetClient:
        def __init__(self, url, credentials, session, loop, cache_ttl=10.0):
            self.url = url
            self.credentials = credentials
            self.session = session
            self.loop = loop
            self.cache = {}
            self.cache_lock = asyncio.Lock()

        async def close(self):
            pass

        async def call(self, tool_name, extra_arguments):
            return {}

    async_client = httpx.AsyncClient(base_url="http://dummy")
    monkeypatch.setattr(api.httpx, "AsyncClient", lambda base_url, timeout: async_client)
    monkeypatch.setattr(api, "FortinetMCPClient", DummyFortinetClient)
    monkeypatch.setenv("FORTINET_MCP_HTTP_URL", "http://new")

    new_client = await api._get_fortinet_client()
    assert new_client.url == "http://new"
    api._FORTINET_CLIENT = None
    await async_client.aclose()


def test_open_service_not_discovered(monkeypatch):
    monkeypatch.setattr(api, "load_platform_data", lambda: None)
    client = TestClient(api.app)
    response = client.post("/api/platform/service/1/open")
    assert response.status_code == 404


def test_normalize_scene_other_types():
    result = api._normalize_scene(123)
    assert result == {"nodes": [], "links": []}


def test_normalize_scene_preserves_fields():
    topology = {
        "devices": [
            {
                "id": "fg",
                "name": "FG",
                "type": "fortigate",
                "hostname": "fg.local",
                "status": "active",
            }
        ],
        "links": [
            {
                "source": "fg",
                "target": "switch",
                "type": "wired",
                "status": "up",
                "description": "uplink",
                "ports": ["port1", "port2"],
            }
        ],
    }
    result = api._normalize_scene(topology)
    node = result["nodes"][0]
    assert node["hostname"] == "fg.local"
    assert node["status"] == "active"
    link = result["links"][0]
    assert link["type"] == "wired"
    assert link["status"] == "up"
    assert link["description"] == "uplink"
    assert link["ports"] == ["port1", "port2"]


async def _raise_http_exception(*args, **kwargs):
    raise HTTPException(status_code=500, detail="fail")


def test_get_topology_scene_other_http_error(monkeypatch):
    monkeypatch.setattr(api, "_call_fortinet_tool_async", _raise_http_exception)
    client = TestClient(api.app)
    response = client.get("/api/topology/scene")
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_shutdown_event_closes_clients(monkeypatch):
    class StubFortinet:
        def __init__(self):
            self.closed = False

        async def close(self):
            self.closed = True

    fortinet_stub = StubFortinet()
    client_stub = DummyAsyncClient()
    api._FORTINET_CLIENT = fortinet_stub
    api._SERVICE_HTTP_CLIENT = client_stub
    api._SERVICE_CLIENT_LOOP = None
    api._VLLM_CLIENT = DummyAsyncClient()
    api._VLLM_CLIENT_BASE = "http://localhost:8000"

    await api.shutdown_event()

    assert fortinet_stub.closed is True
    assert client_stub.closed is True
    assert api._FORTINET_CLIENT is None
    assert api._SERVICE_HTTP_CLIENT is None
    assert api._VLLM_CLIENT is None


@pytest.mark.asyncio
async def test_shutdown_event_cancels_docs_task():
    api._FORTINET_CLIENT = None
    api._SERVICE_HTTP_CLIENT = None
    api._VLLM_CLIENT = None
    api._DOCS_INDEX_TASK = asyncio.create_task(asyncio.sleep(10))
    await api.shutdown_event()
    assert api._DOCS_INDEX_TASK is None


@pytest.mark.asyncio
async def test_get_service_http_client_close_runtime_error(monkeypatch):
    class StubClient:
        def __init__(self):
            self.closed = False

        async def request(self, *args, **kwargs):
            return DummyAsyncResponse()

        async def aclose(self):
            self.closed = True
            raise RuntimeError("loop closed")

    stub = StubClient()
    api._SERVICE_HTTP_CLIENT = stub
    api._FORTINET_CLIENT = None
    new_loop = asyncio.new_event_loop()
    api._SERVICE_CLIENT_LOOP = new_loop

    monkeypatch.setattr(api.httpx, "AsyncClient", lambda timeout=10.0: DummyAsyncClient())

    try:
        await api._get_service_http_client()
    finally:
        new_loop.close()

    assert stub.closed is True
    assert api._SERVICE_HTTP_CLIENT is not stub
    assert isinstance(api._SERVICE_HTTP_CLIENT, DummyAsyncClient)


@pytest.mark.asyncio
async def test_get_service_http_client_reuse(monkeypatch):
    class TrackingClient:
        def __init__(self, *args, **kwargs):
            self.closed = False
            self.args = args
            self.kwargs = kwargs

        async def request(self, *args, **kwargs):
            return DummyAsyncResponse()

        async def aclose(self):
            self.closed = True

    created = []

    def factory(*args, **kwargs):
        client = TrackingClient(*args, **kwargs)
        created.append(client)
        return client

    api._SERVICE_HTTP_CLIENT = None
    api._SERVICE_CLIENT_LOOP = None
    api._FORTINET_CLIENT = None
    monkeypatch.setattr(api.httpx, "AsyncClient", factory)

    first = await api._get_service_http_client()
    second = await api._get_service_http_client()

    assert first is second
    assert len(created) == 1

    await api.shutdown_event()
    assert created[0].closed is True


def test_load_platform_data_refresh(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "DISCOVERY_DIR", tmp_path)
    data_path = tmp_path / "platform_map.json"
    data_path.write_text(json.dumps({"value": 1}), encoding="utf-8")
    api._clear_platform_data_cache()

    first = api.load_platform_data()
    assert first["value"] == 1

    data_path.write_text(json.dumps({"value": 2}), encoding="utf-8")
    api._PLATFORM_DATA_CACHE["data"] = {"value": 999}

    refreshed = api.load_platform_data(refresh=True)
    assert refreshed["value"] == 2


def test_performance_recorder_empty_bucket():
    api.PERF_RECORDER.reset()
    api.PERF_RECORDER._samples["empty"] = deque(maxlen=4)
    metrics = api.get_performance_metrics()
    assert "empty" not in metrics


def test_performance_metrics_endpoint():
    api.PERF_RECORDER.reset()
    with api._profile_section("unit-test"):
        pass
    client = TestClient(api.app)
    response = client.get("/api/performance/metrics")
    payload = response.json()
    assert response.status_code == 200
    assert "unit-test" in payload["metrics"]


def test_get_performance_metrics_helper():
    api.PERF_RECORDER.reset()
    with api._profile_section("helper"):
        pass
    metrics = api.get_performance_metrics()
    assert metrics["helper"]["count"] == 1


def test_topology_workflow_generate_artifacts_samples(tmp_path):
    result = topology_workflow.generate_artifacts(
        use_samples=True,
        output_dir=tmp_path,
        json_name="auto.json",
        graphml_name="auto.graphml",
        write_files=True,
    )
    metadata = result["topology"]["metadata"]
    assert metadata["node_count"] > 0
    assert metadata["link_count"] > 0
    artifacts = result["artifacts"]
    assert artifacts["json_path"].endswith("auto.json")
    assert artifacts["graphml_path"].endswith("auto.graphml")
    assert (tmp_path / "auto.json").exists()
    assert (tmp_path / "auto.graphml").exists()


def test_topology_workflow_generate_artifacts_drawio(tmp_path):
    result = topology_workflow.generate_artifacts(
        use_samples=True,
        output_dir=tmp_path,
        json_name="auto.json",
        graphml_name="auto.graphml",
        drawio_name="auto.drawio",
        write_files=True,
    )
    artifacts = result["artifacts"]
    assert artifacts["drawio_path"].endswith("auto.drawio")
    assert (tmp_path / "auto.drawio").exists()


def test_topology_workflow_generate_artifacts_missing(tmp_path):
    with pytest.raises(ValueError):
        topology_workflow.generate_artifacts(
            use_samples=False,
            output_dir=tmp_path,
            write_files=False,
        )


def test_automated_topology_endpoint_samples():
    client = TestClient(api.app)
    response = client.post("/api/topology/automated", json={"use_samples": True})
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["node_count"] > 0
    assert payload["sources"]["fortimanager"]["source"] == "sample"


def test_automated_topology_endpoint_writes_files(tmp_path):
    client = TestClient(api.app)
    response = client.post(
        "/api/topology/automated",
        json={
            "use_samples": True,
            "write_files": True,
            "output_dir": str(tmp_path),
            "json_name": "workflow.json",
            "graphml_name": "workflow.graphml",
            "drawio_name": "workflow.drawio",
        },
    )
    assert response.status_code == 200
    data = response.json()
    artifacts = data["artifacts"]
    assert artifacts["json_path"].endswith("workflow.json")
    assert artifacts["graphml_path"].endswith("workflow.graphml")
    assert artifacts["drawio_path"].endswith("workflow.drawio")
    assert (tmp_path / "workflow.json").exists()
    assert (tmp_path / "workflow.graphml").exists()
    assert (tmp_path / "workflow.drawio").exists()


def test_automated_topology_endpoint_invalid():
    client = TestClient(api.app)
    response = client.post("/api/topology/automated", json={"use_samples": False})
    assert response.status_code == 400


def test_automated_topology_endpoint_passes_credentials(monkeypatch):
    captured = {}

    def fake_generate_artifacts(**kwargs):
        captured["kwargs"] = kwargs
        return {
            "topology": {"nodes": [], "links": [], "metadata": {}},
            "artifacts": {},
            "sources": {"fortimanager": {"source": "sample", "device_count": 0}, "meraki": {"source": "sample", "device_count": 0}},
        }

    monkeypatch.setattr(api.topology_workflow, "generate_artifacts", fake_generate_artifacts)

    client = TestClient(api.app)
    response = client.post(
        "/api/topology/automated",
        json={
            "use_samples": True,
            "fortigate_credentials": {
                "host": "192.168.0.254:10443",
                "token": "token123",
                "verify_ssl": True,
                "wifi_host": "fw.example.com:10443",
                "wifi_token": "wifi-token",
            },
            "fortimanager_credentials": {
                "host": "fmg.example.com",
                "username": "apiuser",
                "password": "secret",
                "adom": "root",
            },
            "meraki_credentials": {
                "api_key": "abc123",
                "network_id": "N_42",
                "organization_id": "123",
                "base_url": "https://example.com/api/v1",
            },
        },
    )
    assert response.status_code == 200
    kwargs = captured["kwargs"]
    fg_creds = kwargs["fortigate_credentials"]
    fm_creds = kwargs["fortimanager_credentials"]
    meraki_creds = kwargs["meraki_credentials"]
    assert isinstance(fg_creds, topology_workflow.FortiGateCredentials)
    assert fg_creds.host == "192.168.0.254:10443"
    assert fg_creds.token == "token123"
    assert fg_creds.verify_ssl is True
    assert fg_creds.wifi_host == "fw.example.com:10443"
    assert fg_creds.wifi_token == "wifi-token"
    assert isinstance(fm_creds, topology_workflow.FortiManagerCredentials)
    assert fm_creds.host == "fmg.example.com"
    assert fm_creds.username == "apiuser"
    assert fm_creds.password == "secret"
    assert meraki_creds.network_id == "N_42"


def test_automated_topology_endpoint_internal_error(monkeypatch):
    client = TestClient(api.app)

    def boom(**kwargs):
        raise RuntimeError("workflow failure")

    monkeypatch.setattr(api.topology_workflow, "generate_artifacts", boom)
    response = client.post("/api/topology/automated", json={"use_samples": True})
    assert response.status_code == 500


def test_list_automated_artifacts_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(api.topology_workflow, "DEFAULT_OUTPUT_DIR", tmp_path)
    client = TestClient(api.app)
    response = client.get("/api/topology/automated/artifacts")
    assert response.status_code == 200
    assert response.json()["artifacts"] == []


def test_list_and_download_automated_artifact(monkeypatch, tmp_path):
    monkeypatch.setattr(api.topology_workflow, "DEFAULT_OUTPUT_DIR", tmp_path)
    json_path = tmp_path / "combined_topology.json"
    json_path.write_text("{}", encoding="utf-8")
    graphml_path = tmp_path / "combined_topology.graphml"
    graphml_path.write_text("<graphml/>", encoding="utf-8")

    client = TestClient(api.app)
    list_response = client.get("/api/topology/automated/artifacts")
    assert list_response.status_code == 200
    artifacts = list_response.json()["artifacts"]
    assert len(artifacts) == 2

    download_response = client.get(f"/api/topology/automated/artifacts/{json_path.name}")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith("application/json")
    assert download_response.content == b"{}"


def test_download_automated_artifact_invalid_name(monkeypatch, tmp_path):
    monkeypatch.setattr(api.topology_workflow, "DEFAULT_OUTPUT_DIR", tmp_path)
    client = TestClient(api.app)
    response = client.get("/api/topology/automated/artifacts/..%5Cetc%5Cpasswd")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_fetch_artifact_rejects_path_traversal(monkeypatch, tmp_path):
    monkeypatch.setattr(api.topology_workflow, "DEFAULT_OUTPUT_DIR", tmp_path)
    with pytest.raises(HTTPException) as exc:
        await api.fetch_automated_topology_artifact("../evil.txt")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_fetch_artifact_drawio_content(monkeypatch, tmp_path):
    monkeypatch.setattr(api.topology_workflow, "DEFAULT_OUTPUT_DIR", tmp_path)
    drawio_path = tmp_path / "diagram.drawio"
    drawio_path.write_text("<mxfile/>", encoding="utf-8")
    response = await api.fetch_automated_topology_artifact("diagram.drawio")
    assert isinstance(response, FileResponse)
    assert response.media_type == "application/xml"


@pytest.mark.asyncio
async def test_fetch_artifact_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(api.topology_workflow, "DEFAULT_OUTPUT_DIR", tmp_path)
    with pytest.raises(HTTPException) as exc:
        await api.fetch_automated_topology_artifact("missing.json")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_fetch_artifact_graphml_content(monkeypatch, tmp_path):
    monkeypatch.setattr(api.topology_workflow, "DEFAULT_OUTPUT_DIR", tmp_path)
    graphml_path = tmp_path / "diagram.graphml"
    graphml_path.write_text("<graphml/>", encoding="utf-8")
    response = await api.fetch_automated_topology_artifact("diagram.graphml")
    assert isinstance(response, FileResponse)
    assert response.media_type == "application/graphml+xml"


def test_resolve_inputs_prefers_fortigate(monkeypatch):
    fortigate_payload = (
        {"fabric_devices": [{"id": "fg1", "name": "FG", "type": "fortigate"}], "fabric_links": []},
        "fortigate:lab",
    )
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_fortigate_payload",
        lambda creds: fortigate_payload,
    )
    monkeypatch.setattr(
        api.topology_workflow,
        "_fetch_fortigate_payload",
        lambda creds: fortigate_payload,
    )
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_fortimanager_payload",
        lambda creds: ({"fabric_devices": [], "fabric_links": []}, "fortimanager:none"),
    )
    monkeypatch.setattr(
        api.topology_workflow,
        "_fetch_fortimanager_payload",
        lambda creds: ({"fabric_devices": [], "fabric_links": []}, "fortimanager:none"),
    )
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_meraki_payload",
        lambda creds: ({"devices": [], "links": []}, "meraki:none"),
    )
    monkeypatch.setattr(
        api.topology_workflow,
        "_fetch_meraki_payload",
        lambda creds: ({"devices": [], "links": []}, "meraki:none"),
    )
    inputs = topology_workflow.resolve_inputs(
        fortigate_json=None,
        fortimanager_json=None,
        meraki_json=None,
        use_samples=False,
        fortigate_credentials=topology_workflow.FortiGateCredentials(host="fg", token="tok"),
        meraki_credentials=topology_workflow.MerakiCredentials(api_key="k", network_id="n"),
    )
    assert inputs.fortimanager_source == "fortigate:lab"
    assert inputs.fortimanager["fabric_devices"][0]["id"] == "fg1"


def test_generate_artifacts_with_fortigate_payload(monkeypatch):
    fortigate_payload = (
        {"fabric_devices": [{"id": "fg1", "name": "FG", "type": "fortigate"}], "fabric_links": []},
        "fortigate:lab",
    )
    meraki_payload = ({"devices": [], "links": []}, "meraki:none")
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_fortigate_payload",
        lambda creds: fortigate_payload,
    )
    monkeypatch.setattr(
        api.topology_workflow,
        "_fetch_fortigate_payload",
        lambda creds: fortigate_payload,
    )
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_fortimanager_payload",
        lambda creds: ({"fabric_devices": [], "fabric_links": []}, "fortimanager:none"),
    )
    monkeypatch.setattr(
        api.topology_workflow,
        "_fetch_fortimanager_payload",
        lambda creds: ({"fabric_devices": [], "fabric_links": []}, "fortimanager:none"),
    )
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_meraki_payload",
        lambda creds: meraki_payload,
    )
    monkeypatch.setattr(
        api.topology_workflow,
        "_fetch_meraki_payload",
        lambda creds: meraki_payload,
    )
    result = topology_workflow.generate_artifacts(
        fortigate_json=None,
        fortimanager_json=None,
        meraki_json=None,
        fortigate_credentials=topology_workflow.FortiGateCredentials(host="fg", token="tok"),
        meraki_credentials=topology_workflow.MerakiCredentials(api_key="k", network_id="n"),
        use_samples=False,
        write_files=False,
    )
    assert result["sources"]["fortimanager"]["source"] == "fortigate:lab"
    assert result["topology"]["metadata"]["node_count"] > 0


def test_resolve_inputs_fortimanager_missing(monkeypatch):
    fortigate_payload = (
        {"fabric_devices": [{"id": "fg1", "name": "FG", "type": "fortigate"}], "fabric_links": []},
        "fortigate:lab",
    )
    meraki_payload = ({"devices": [], "links": []}, "meraki:none")
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_fortigate_payload",
        lambda creds: fortigate_payload,
    )
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_fortimanager_payload",
        lambda creds: None,
    )
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_meraki_payload",
        lambda creds: meraki_payload,
    )
    inputs = topology_workflow.resolve_inputs(
        fortigate_json=None,
        fortimanager_json=None,
        meraki_json=None,
        use_samples=False,
        fortigate_credentials=topology_workflow.FortiGateCredentials(host="fg", token="tok"),
        meraki_credentials=topology_workflow.MerakiCredentials(api_key="k", network_id="n"),
    )
    assert inputs.fortimanager_source == "fortigate:lab"
    assert inputs.fortimanager["fabric_devices"][0]["id"] == "fg1"


def test_resolve_inputs_meraki_missing(monkeypatch):
    fortigate_payload = (
        {"fabric_devices": [{"id": "fg1", "name": "FG", "type": "fortigate"}], "fabric_links": []},
        "fortigate:lab",
    )
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_fortigate_payload",
        lambda creds: fortigate_payload,
    )
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_fortimanager_payload",
        lambda creds: None,
    )
    monkeypatch.setattr(
        topology_workflow,
        "_fetch_meraki_payload",
        lambda creds: None,
    )
    inputs = topology_workflow.resolve_inputs(
        fortigate_json=None,
        fortimanager_json=None,
        meraki_json=None,
        use_samples=False,
        fortigate_credentials=topology_workflow.FortiGateCredentials(host="fg", token="tok"),
    )
    assert inputs.meraki["devices"] == []
    assert inputs.meraki_source == "meraki:unavailable"
