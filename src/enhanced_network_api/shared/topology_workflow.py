"""Utilities for automating FortiManager + Meraki topology generation.

This module centralises the logic so both FastAPI endpoints and CLI scripts
can reuse the same workflow when combining FortiManager and Meraki data into
canonical topology artefacts.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse, quote_plus

import requests

try:
    from fortiosapi import FortiOSAPI, NotLogged  # type: ignore
except ImportError:  # pragma: no cover
    FortiOSAPI = None
    NotLogged = Exception

from src.enhanced_network_api.fortigate_topology_drawio import generate_drawio_xml_from_topology

DEFAULT_OUTPUT_DIR = Path("data/generated")
FORTIGATE_JSON_ENV = "FORTIGATE_JSON_PATH"
FORTIMANAGER_JSON_ENV = "FORTIMANAGER_JSON_PATH"
MERAKI_JSON_ENV = "MERAKI_JSON_PATH"
_HTTP_TIMEOUT = float(os.getenv("TOPOLOGY_WORKFLOW_HTTP_TIMEOUT", "15"))

logger = logging.getLogger(__name__)

# Suppress warnings for self-signed lab environments
try:  # pragma: no cover - optional dependency
    import urllib3

    urllib3.disable_warnings()  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - safety
    pass


# --------------------------------------------------------------------------- #
# Sample payloads keep the workflow functional without live credentials
# --------------------------------------------------------------------------- #


def _build_sample_fortimanager_payload() -> Dict[str, Any]:
    return {
        "fabric_devices": [
            {
                "id": "fg-core",
                "name": "FortiGate Core",
                "type": "fortigate",
                "ip": "192.168.0.254",
                "role": "gateway",
                "serial": "FGT61FTK20020975",
            },
            {
                "id": "fsw-edge",
                "name": "Edge Switch",
                "type": "fortiswitch",
                "ip": "10.255.1.2",
                "role": "switch",
                "serial": "FSW24F3Z21001234",
            },
        ],
        "fabric_links": [
            {
                "source": "fg-core",
                "target": "fsw-edge",
                "type": "fortilink",
                "interfaces": ["port1", "port1"],
            }
        ],
    }


def _build_sample_meraki_payload() -> Dict[str, Any]:
    return {
        "devices": [
            {
                "id": "meraki-ap-1",
                "name": "MR46 Office",
                "model": "MR46",
                "lanIp": "192.168.10.15",
                "serial": "Q2MW-1234-ABCD",
                "tags": ["floor-1", "west-wing"],
            },
            {
                "id": "meraki-switch-1",
                "name": "MS225 Access",
                "model": "MS225-48LP",
                "lanIp": "192.168.10.2",
                "serial": "Q3MN-9876-DCBA",
                "tags": ["closet-a"],
            },
        ],
        "links": [
            {
                "source": "meraki-switch-1",
                "target": "meraki-ap-1",
                "type": "ethernet",
                "interfaces": ["Port 10", "eth0"],
            }
        ],
    }


SAMPLE_FORTIMANAGER_PAYLOAD = _build_sample_fortimanager_payload()
SAMPLE_MERAKI_PAYLOAD = _build_sample_meraki_payload()


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #


@dataclass
class TopologyInputs:
    fortimanager: Dict[str, Any]
    meraki: Dict[str, Any]
    fortimanager_source: str
    meraki_source: str


@dataclass
class FortiGateCredentials:
    host: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: bool = False
    wifi_host: Optional[str] = None
    wifi_token: Optional[str] = None


@dataclass
class FortiManagerCredentials:
    host: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    adom: Optional[str] = "root"


@dataclass
class MerakiCredentials:
    api_key: Optional[str] = None
    organization_id: Optional[str] = None
    network_id: Optional[str] = None
    base_url: Optional[str] = None


def _load_json_payload(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Topology JSON not found at {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected an object in {path}, got {type(data).__name__}")
    return data


def _resolve_payload(
    cli_path: Optional[str],
    env_var: str,
    sample_payload: Dict[str, Any],
    use_samples: bool,
    fetcher: Optional[Callable[[], Optional[Tuple[Dict[str, Any], str]]]] = None,
) -> Tuple[Dict[str, Any], str]:
    """Return payload and string describing the source."""

    if cli_path:
        path = Path(cli_path).expanduser()
        return _load_json_payload(path), f"file:{path}"

    env_path = os.getenv(env_var)
    if env_path:
        path = Path(env_path).expanduser()
        return _load_json_payload(path), f"env:{env_var}"

    if fetcher:
        try:
            fetched = fetcher()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Automated topology fetcher for %s failed: %s", env_var, exc)
            fetched = None
        if fetched:
            return fetched

    if use_samples:
        return sample_payload, "sample"

    raise ValueError(
        "Topology payload not provided and samples disabled. "
        f"Pass a JSON path, configure {env_var}, or enable samples."
    )


def _first_non_empty(*values: Optional[str]) -> Optional[str]:
    for value in values:
        if value:
            value = value.strip()
            if value:
                return value
    return None


def _fortimanager_env_credentials(
    credentials: Optional[FortiManagerCredentials],
) -> Optional[FortiManagerCredentials]:
    host = _first_non_empty(
        credentials.host if credentials else None,
        os.getenv("FORTIMANAGER_HOST"),
        os.getenv("ARBYS_FM_HOST"),
        os.getenv("BWW_FM_HOST"),
        os.getenv("SONIC_FM_HOST"),
    )
    username = _first_non_empty(
        credentials.username if credentials else None,
        os.getenv("FORTIMANAGER_USERNAME"),
        os.getenv("FORTIMANAGER_USER"),
        os.getenv("ARBYS_FM_USER"),
        os.getenv("BWW_FM_USER"),
        os.getenv("SONIC_FM_USER"),
    )
    password = _first_non_empty(
        credentials.password if credentials else None,
        os.getenv("FORTIMANAGER_PASSWORD"),
        os.getenv("FORTIMANAGER_PASS"),
        os.getenv("ARBYS_FM_PASS"),
        os.getenv("BWW_FM_PASS"),
        os.getenv("SONIC_FM_PASS"),
    )
    adom = _first_non_empty(
        credentials.adom if credentials else None,
        os.getenv("FORTIMANAGER_ADOM"),
        "root",
    )
    if not host or not username or not password:
        return None
    return FortiManagerCredentials(host=host, username=username, password=password, adom=adom)


def _fetch_fortimanager_payload(
    credentials: Optional[FortiManagerCredentials],
) -> Optional[Tuple[Dict[str, Any], str]]:
    creds = _fortimanager_env_credentials(credentials)
    if not creds:
        return None

    login_url = f"https://{creds.host}/jsonrpc"
    try:
        with requests.Session() as session:
            session.headers.update({"Content-Type": "application/json"})
            login_payload = {
                "id": 1,
                "method": "exec",
                "params": [
                    {
                        "url": "/sys/login/user",
                        "data": {"user": creds.username, "passwd": creds.password},
                    }
                ],
            }
            response = session.post(
                login_url,
                data=json.dumps(login_payload),
                timeout=_HTTP_TIMEOUT,
                verify=False,
            )
            response.raise_for_status()
            result = response.json()
            session_id = result.get("session")
            if not session_id:
                logger.warning("FortiManager login to %s did not return a session token", creds.host)
                return None

            params = [
                {
                    "url": "/dvmdb/device",
                }
            ]
            device_payload = {
                "id": 1,
                "method": "get",
                "params": params,
                "session": session_id,
            }
            device_resp = session.post(
                login_url,
                data=json.dumps(device_payload),
                timeout=_HTTP_TIMEOUT,
                verify=False,
            )
            device_resp.raise_for_status()
            device_data = device_resp.json()

            devices: List[Dict[str, Any]] = []
            results = device_data.get("result", [])
            for entry in results:
                records = entry.get("data") or entry.get("results") or []
                if isinstance(records, dict):
                    records = records.get("entries", [])
                if not isinstance(records, list):
                    continue
                for raw in records:
                    node_id = _first_non_empty(
                        str(raw.get("name") or ""),
                        str(raw.get("device_id") or ""),
                        str(raw.get("sn") or ""),
                        str(raw.get("serial") or ""),
                    )
                    if not node_id:
                        continue
                    device_entry = {
                        "id": node_id,
                        "name": raw.get("name") or raw.get("hostname") or node_id,
                        "type": raw.get("device_type") or raw.get("platform") or raw.get("os_type") or "device",
                        "ip": raw.get("ip") or raw.get("mgmt_ip") or raw.get("ipv4") or raw.get("ipv4address"),
                        "model": raw.get("platform") or raw.get("model"),
                        "serial": raw.get("sn") or raw.get("serial"),
                        "role": raw.get("device_role"),
                        "status": raw.get("status"),
                    }
                    devices.append({k: v for k, v in device_entry.items() if v not in (None, "", [])})
            logout_payload = {"id": 1, "method": "exec", "params": [{"url": "/sys/logout"}], "session": session_id}
            try:
                session.post(
                    login_url,
                    data=json.dumps(logout_payload),
                    timeout=_HTTP_TIMEOUT,
                    verify=False,
                )
            except requests.exceptions.RequestException:
                logger.debug("FortiManager logout call failed for %s", creds.host)
    except requests.exceptions.RequestException as exc:
        logger.warning("Failed to fetch FortiManager topology from %s: %s", creds.host, exc)
        return None

    if not devices:
        logger.warning("FortiManager topology fetch returned no devices for %s", creds.host)
        return None

    payload = {"fabric_devices": devices, "fabric_links": []}
    return payload, f"live:{creds.host}"


def _fortigate_env_credentials(
    credentials: Optional[FortiGateCredentials],
) -> Optional[FortiGateCredentials]:
    host = _first_non_empty(
        credentials.host if credentials else None,
        os.getenv("FORTIGATE_HOST"),
        os.getenv("FORTIGATE_HOSTS"),
    )
    port_candidates: List[Optional[str]] = [
        os.getenv("FORTIGATE_PORT"),
        os.getenv("FORTIGATE_DEFAULT_PORT"),
        "10443",
    ]
    if host:
        host_base = host.split(",")[0].split(":")[0]
        host_key = f"FORTIGATE_{host_base.replace('.', '_').replace('-', '_')}_PORT"
        port_candidates.append(os.getenv(host_key))
    port = _first_non_empty(*port_candidates)
    token = _first_non_empty(
        credentials.token if credentials else None,
        os.getenv("FORTIGATE_TOKEN"),
        os.getenv("FORTIGATE_API_TOKEN"),
        os.getenv("FORTIGATE_192_168_0_254_TOKEN"),
    )
    username = _first_non_empty(
        credentials.username if credentials else None,
        os.getenv("FORTIGATE_USERNAME"),
    )
    password = _first_non_empty(
        credentials.password if credentials else None,
        os.getenv("FORTIGATE_PASSWORD"),
    )
    wifi_host = _first_non_empty(
        credentials.wifi_host if credentials else None,
        os.getenv("FORTIGATE_WIFI_HOST"),
        os.getenv("FORTIGATE_WIFI_URL"),
    )
    wifi_token = _first_non_empty(
        credentials.wifi_token if credentials else None,
        os.getenv("FORTIGATE_WIFI_TOKEN"),
    )
    verify_ssl = credentials.verify_ssl if credentials else False

    if not host or (not token and not (username and password)):
        return None

    if ":" not in host and port:
        host = f"{host}:{port}"

    return FortiGateCredentials(
        host=host,
        token=token,
        username=username,
        password=password,
        verify_ssl=verify_ssl,
        wifi_host=wifi_host,
        wifi_token=wifi_token,
    )


def _fortigate_session_login(
    session: requests.Session,
    base_url: str,
    creds: FortiGateCredentials,
) -> Optional[str]:
    if not (creds.username and creds.password):
        return None
    login_base = base_url.rstrip("/")

    def _extract_csrf() -> Optional[str]:
        for cookie_jar in (session.cookies,):
            for cookie in cookie_jar:
                name = cookie.name.lower()
                if name.startswith("ccsrf_token") or name.startswith("ccsrftoken") or name == "csrftoken":
                    value = cookie.value
                    if isinstance(value, str):
                        value = value.strip('"')
                    if value:
                        return value
        return None

    # Modern FortiOS login flow (FortiOS 7.4+)
    try:
        session.get(f"{login_base}/login", timeout=_HTTP_TIMEOUT)
        json_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Referer": f"{login_base}/login",
        }
        auth_payload = {"username": creds.username, "password": creds.password}
        response = session.post(
            f"{login_base}/api/v2/authentication",
            json=auth_payload,
            headers=json_headers,
            timeout=_HTTP_TIMEOUT,
        )
        response.raise_for_status()
        csrf_token = _extract_csrf()
        if not csrf_token:
            # Some FortiOS builds only include the CSRF token in the Set-Cookie header.
            set_cookie = response.headers.get("set-cookie", "")
            for part in set_cookie.split("\n"):
                if "ccsrf_token" in part.lower():
                    value = part.split("=", 1)[1].split(";", 1)[0].strip().strip('"')
                    if value:
                        csrf_token = value
                        session.cookies.set(
                            part.split("=", 1)[0],
                            value,
                            domain=urlparse(base_url).hostname or "",
                            path="/",
                        )
                        break
        if csrf_token:
            session.headers.update(
                {
                    "X-CSRFTOKEN": csrf_token,
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json, text/plain, */*",
                }
            )
            return csrf_token
    except requests.exceptions.RequestException as exc:
        logger.warning("FortiGate JSON authentication failed for %s: %s", base_url, exc)

    # Legacy FortiOS login flow (fallback)
    login_url = f"{login_base}/logincheck"
    try:
        session.get(login_base, timeout=_HTTP_TIMEOUT)
    except requests.exceptions.RequestException:
        logger.debug("FortiGate pre-login GET failed for %s", base_url)
    payload = (
        f"username={quote_plus(creds.username or '')}"
        f"&secretkey={quote_plus(creds.password or '')}"
        "&ajax=1"
    )
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = session.post(
            login_url,
            data=payload,
            headers=headers,
            timeout=_HTTP_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.warning("FortiGate legacy session login failed for %s: %s", base_url, exc)
        return None
    text = (response.text or "").strip()
    if not text.startswith("1"):
        logger.warning(
            "FortiGate logincheck unexpected response for %s: %s",
            base_url,
            text[:120].replace("\n", " "),
        )
        return None
    csrf_token = _extract_csrf()
    if not csrf_token:
        logger.warning("FortiGate legacy session login for %s missing CSRF token", base_url)
        return None
    session.headers.update({"X-CSRFTOKEN": csrf_token})
    return csrf_token


def _fortigate_api_session(
    base_url: str, creds: FortiGateCredentials
) -> Optional[requests.Session]:
    if FortiOSAPI is None or not (creds.username and creds.password):
        return None
    parsed = urlparse(base_url)
    host = parsed.netloc or base_url.replace("https://", "").replace("http://", "")
    client = FortiOSAPI()
    try:
        client.login(
            host,
            creds.username,
            creds.password,
            verify=creds.verify_ssl,
            timeout=_HTTP_TIMEOUT,
        )
    except NotLogged as exc:
        logger.debug("FortiGate API session login failed for %s: %s", base_url, exc)
        return None
    except Exception as exc:  # pragma: no cover
        logger.debug("FortiGate API session unexpected error for %s: %s", base_url, exc)
        return None
    return client._session


def _fetch_fortigate_payload(
    credentials: Optional[FortiGateCredentials],
) -> Optional[Tuple[Dict[str, Any], str]]:
    creds = _fortigate_env_credentials(credentials)
    if not creds or not creds.host:
        return None

    base_url = creds.host
    if "://" not in base_url:
        base_url = f"https://{base_url}"

    session = requests.Session()
    session.verify = creds.verify_ssl

    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if creds.token:
        headers["Authorization"] = f"Bearer {creds.token}"
    elif not (creds.username and creds.password):
        logger.warning("FortiGate credentials missing token or username/password")
        return None

    session_authenticated = False

    def _ensure_session_authenticated() -> bool:
        nonlocal session_authenticated, session, headers
        if session_authenticated:
            return True
        api_session = _fortigate_api_session(base_url, creds)
        if not api_session:
            csrf = _fortigate_session_login(session, base_url, creds)
            if not csrf:
                return False
        else:
            session = api_session
            session.verify = creds.verify_ssl
            csrf = session.headers.get("X-CSRFTOKEN")
        session_authenticated = True
        session.auth = None
        headers.clear()
        headers["Content-Type"] = "application/json"
        if csrf:
            headers["X-CSRFTOKEN"] = csrf
        return True

    def _get_json(endpoint: str) -> Optional[Any]:
        try:
            url = f"{base_url}{endpoint}"
            response = session.get(
                url,
                headers=headers,
                timeout=_HTTP_TIMEOUT,
            )
            if response.status_code == 401 and _ensure_session_authenticated():
                response = session.get(
                    url,
                    headers=headers,
                    timeout=_HTTP_TIMEOUT,
                )
            if (
                response.status_code == 401
                and creds.token
                and headers.get("Authorization")
            ):
                alt_headers = {
                    k: v for k, v in headers.items() if k.lower() != "authorization"
                }
                parsed_url = urlparse(url)
                pairs = parse_qsl(parsed_url.query, keep_blank_values=True)
                if not any(k == "access_token" for k, _ in pairs):
                    pairs.append(("access_token", _format_access_token(creds.token)))
                alt_url = urlunparse(parsed_url._replace(query=urlencode(pairs, doseq=True)))
                response = session.get(
                    alt_url,
                    headers=alt_headers,
                    timeout=_HTTP_TIMEOUT,
                )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.JSONDecodeError as exc:
            logger.warning("FortiGate %s returned non-JSON payload: %s", endpoint, exc)
        except requests.exceptions.RequestException as exc:
            logger.warning("Failed to fetch FortiGate endpoint %s: %s", endpoint, exc)
        return None

    status_data = _get_json("/api/v2/monitor/system/status")
    if not status_data:
        logger.warning("FortiGate status endpoint unavailable for %s", creds.host)
        status_data = {}

    status_results = status_data.get("results") if isinstance(status_data, dict) else {}
    if not isinstance(status_results, dict):
        status_results = {}

    host_without_port = creds.host.split(":")[0]
    fortigate_serial = _first_non_empty(
        status_data.get("serial"),
        status_results.get("serial"),
        status_results.get("sn"),
        host_without_port,
        "fortigate",
    )
    fortigate_hostname = _first_non_empty(
        status_results.get("hostname"),
        status_results.get("name"),
        "FortiGate",
    )
    fortigate_model = _first_non_empty(
        status_results.get("model"),
        status_results.get("model_name"),
        status_results.get("model_number"),
    )
    fortigate_node = {
        "id": fortigate_serial,
        "name": fortigate_hostname,
        "type": "fortigate",
        "ip": status_results.get("management-ip") or status_results.get("ip") or host_without_port,
        "model": fortigate_model,
        "serial": fortigate_serial,
        "status": status_results.get("status", "online"),
    }
    devices: List[Dict[str, Any]] = [
        {k: v for k, v in fortigate_node.items() if v not in (None, "", [])}
    ]
    links: List[Dict[str, Any]] = []

    interfaces_data = _get_json("/api/v2/cmdb/system/interface") or {}
    interfaces = interfaces_data.get("results") or interfaces_data.get("data") or []
    if isinstance(interfaces, dict):
        interfaces = interfaces.get("entries", [])
    if not isinstance(interfaces, list):
        interfaces = []
    for interface in interfaces:
        name = interface.get("name") or interface.get("id")
        if not name:
            continue
        node_id = f"port-{name}"
        devices.append(
            {
                "id": node_id,
                "name": name,
                "type": "interface",
                "ip": interface.get("ip"),
                "model": interface.get("type"),
                "status": interface.get("status"),
            }
        )
        links.append(
            {
                "source": fortigate_serial,
                "target": node_id,
                "type": "interface",
                "interfaces": [name],
            }
        )

    switches_data = _get_json("/api/v2/cmdb/switch-controller/managed-switch") or {}
    switches = switches_data.get("results") or switches_data.get("data") or []
    if isinstance(switches, dict):
        switches = switches.get("entries", [])
    if not isinstance(switches, list):
        switches = []
    for switch in switches:
        name = (
            switch.get("name")
            or switch.get("switch-id")
            or switch.get("id")
            or switch.get("serial")
            or switch.get("sn")
        )
        if not name:
            continue
        node_id = f"switch-{name}"
        devices.append(
            {
                "id": node_id,
                "name": name,
                "type": "fortiswitch",
                "ip": switch.get("ip") or switch.get("mgmt-ip"),
                "model": switch.get("model"),
                "serial": switch.get("serial") or switch.get("sn"),
                "status": switch.get("status") or switch.get("fsw-wan1-admin"),
            }
        )
        peer = switch.get("fsw-wan1-peer") or switch.get("fsw-wan2-peer") or "fortilink"
        links.append(
            {
                "source": fortigate_serial,
                "target": node_id,
                "type": "switch",
                "interfaces": [peer] if peer else [],
            }
        )

    aps_data = _get_json("/api/v2/monitor/wifi/managed-ap") or {}
    aps = aps_data.get("results") or aps_data.get("data") or []
    if isinstance(aps, dict):
        aps = aps.get("entries", [])
    if not isinstance(aps, list) or not aps:
        wtp_data = _get_json("/api/v2/cmdb/wireless-controller/wtp") or {}
        aps = wtp_data.get("results") or []
    if (not isinstance(aps, list) or not aps) and credentials.wifi_host:
        aps = _fetch_wifi_override(credentials)
    if not isinstance(aps, list):
        aps = []
    for ap in aps:
        name = (
            ap.get("name")
            or ap.get("id")
            or ap.get("serial")
            or ap.get("wtp-id")
        )
        if not name:
            continue
        node_id = f"ap-{name}"
        serial = ap.get("serial") or ap.get("wtp-id")
        model = (
            ap.get("model")
            or ap.get("platform", {}).get("type")
        )
        status_label = (
            ap.get("status")
            or ap.get("state")
            or ap.get("admin")
        )
        devices.append(
            {
                "id": node_id,
                "name": name,
                "type": "fortiap",
                "ip": ap.get("ip-address") or ap.get("ip"),
                "model": model,
                "serial": serial,
                "status": status_label,
            }
        )
        uplink = ap.get("uplink") or ap.get("switch_id") or ap.get("associated-fortiAP") or fortigate_serial
        links.append(
            {
                "source": uplink if isinstance(uplink, str) else fortigate_serial,
                "target": node_id,
                "type": "wireless",
                "interfaces": [ap.get("ethernet-port")] if ap.get("ethernet-port") else [],
            }
        )

    # Fetch endpoint/asset devices from multiple sources
    # 1. Wireless clients (from FortiAPs) - matches WiFi client table in web UI
    # 2. Wired clients (from FortiSwitches) - matches switch client table in web UI
    # 3. User device endpoints (Assets dashboard)
    logger.info("Fetching connected devices from FortiGate API endpoints...")
    endpoint_devices = []
    existing_macs = set()  # Track MACs to avoid duplicates
    
    # 1. Try wireless clients endpoint (matches the WiFi client table in web UI)
    wifi_clients_data = _get_json("/api/v2/monitor/wifi/client")
    if wifi_clients_data:
        logger.info("✅ Successfully fetched from /api/v2/monitor/wifi/client")
        wifi_clients = wifi_clients_data.get("results") or wifi_clients_data.get("data") or []
        if isinstance(wifi_clients, dict):
            wifi_clients = wifi_clients.get("entries", [])
        if isinstance(wifi_clients, list) and len(wifi_clients) > 0:
            logger.info(f"Found {len(wifi_clients)} wireless clients from wifi/client endpoint")
            for client in wifi_clients:
                mac = client.get("mac")
                if mac and mac not in existing_macs:
                    endpoint_devices.append({
                        "name": client.get("device") or client.get("hostname") or mac,
                        "mac": mac,
                        "ip": client.get("ip"),
                        "os": client.get("os") or "Unknown",
                        "connection_type": "wifi",
                        "ssid": client.get("ssid"),
                        "ap_sn": client.get("ap_sn") or client.get("fortiap"),
                        "ap_name": client.get("fortiap") or client.get("ap"),
                        "status": "online",
                    })
                    existing_macs.add(mac)
    else:
        logger.debug("❌ Failed to fetch from /api/v2/monitor/wifi/client")
    
    # 2. Try switch controller clients (for wired devices on FortiSwitch)
    # First get managed switches
    switch_status_data = _get_json("/api/v2/monitor/switch-controller/managed-switch/status")
    if switch_status_data:
        switches = switch_status_data.get("results") or switch_status_data.get("data") or []
        if isinstance(switches, dict):
            switches = switches.get("entries", [])
        if isinstance(switches, list):
            # Try to get clients for each switch
            for switch in switches[:5]:  # Limit to first 5 switches
                switch_id = switch.get("switch-id") or switch.get("id") or switch.get("serial")
                if not switch_id:
                    continue
                
                # Try switch clients endpoint
                switch_clients_data = _get_json(f"/api/v2/monitor/switch-controller/managed-switch/clients?switch_id={switch_id}")
                if switch_clients_data:
                    clients = switch_clients_data.get("results") or switch_clients_data.get("data") or []
                    if isinstance(clients, dict):
                        clients = clients.get("entries", [])
                    if isinstance(clients, list) and len(clients) > 0:
                        logger.info(f"Found {len(clients)} wired clients on switch {switch_id}")
                        for client in clients:
                            mac = client.get("mac")
                            if mac and mac not in existing_macs:
                                endpoint_devices.append({
                                    "name": client.get("device") or client.get("hostname") or mac,
                                    "mac": mac,
                                    "ip": client.get("ip") or client.get("address"),
                                    "os": client.get("os") or client.get("software_os") or "Unknown",
                                    "connection_type": "ethernet",
                                    "switch_id": switch_id,
                                    "switch_name": switch.get("name") or switch_id,
                                    "port": client.get("port"),
                                    "vlan": client.get("vlan"),
                                    "status": client.get("status") or "online",
                                })
                                existing_macs.add(mac)
    
    # 3. Try user device endpoints (Assets dashboard endpoints)
    # Try first endpoint: /api/v2/monitor/user/device/select
    endpoint_devices_data = _get_json("/api/v2/monitor/user/device/select")
    if endpoint_devices_data:
        logger.info("✅ Successfully fetched from /api/v2/monitor/user/device/select")
        user_devices = endpoint_devices_data.get("results") or endpoint_devices_data.get("data") or []
        if isinstance(user_devices, dict):
            user_devices = user_devices.get("entries", [])
        if isinstance(user_devices, list) and len(user_devices) > 0:
            logger.info(f"Found {len(user_devices)} devices from device/select endpoint")
            for device in user_devices:
                mac = device.get("mac")
                if mac and mac not in existing_macs:
                    endpoint_devices.append({
                        "name": device.get("name") or device.get("hostname") or device.get("device") or mac,
                        "mac": mac,
                        "ip": device.get("ip") or device.get("address"),
                        "os": device.get("os") or device.get("os-type") or device.get("software_os") or "Unknown",
                        "connection_type": "wifi" if device.get("ssid") else "ethernet",
                        "ssid": device.get("ssid"),
                        "ap_sn": device.get("ap_sn"),
                        "switch_sn": device.get("switch_sn"),
                        "port": device.get("port"),
                        "status": device.get("status") or "online",
                        "vulnerabilities": device.get("vulnerabilities", 0),
                    })
                    existing_macs.add(mac)
    else:
        logger.debug("❌ Failed to fetch from /api/v2/monitor/user/device/select")
    
    # Try alternative endpoint if we still don't have many devices
    if len(endpoint_devices) < 5:
        logger.info("Trying alternative endpoint: /api/v2/monitor/user/device/query")
        endpoint_devices_data = _get_json("/api/v2/monitor/user/device/query")
        if endpoint_devices_data:
            logger.info("✅ Successfully fetched from /api/v2/monitor/user/device/query")
            user_devices = endpoint_devices_data.get("results") or endpoint_devices_data.get("data") or []
            if isinstance(user_devices, dict):
                user_devices = user_devices.get("entries", [])
            if isinstance(user_devices, list) and len(user_devices) > 0:
                logger.info(f"Found {len(user_devices)} devices from device/query endpoint")
                for device in user_devices:
                    mac = device.get("mac")
                    if mac and mac not in existing_macs:
                        endpoint_devices.append({
                            "name": device.get("name") or device.get("hostname") or device.get("device") or mac,
                            "mac": mac,
                            "ip": device.get("ip") or device.get("address"),
                            "os": device.get("os") or device.get("os-type") or device.get("software_os") or "Unknown",
                            "connection_type": "wifi" if device.get("ssid") else "ethernet",
                            "ssid": device.get("ssid"),
                            "ap_sn": device.get("ap_sn"),
                            "switch_sn": device.get("switch_sn"),
                            "port": device.get("port"),
                            "status": device.get("status") or "online",
                            "vulnerabilities": device.get("vulnerabilities", 0),
                        })
                        existing_macs.add(mac)
        else:
            logger.debug("❌ Failed to fetch from /api/v2/monitor/user/device/query")
    
    # Try third alternative endpoint if still no devices
    if len(endpoint_devices) < 5:
        logger.info("Trying third endpoint: /api/v2/monitor/endpoint-control/registered_ems")
        endpoint_devices_data = _get_json("/api/v2/monitor/endpoint-control/registered_ems")
        if endpoint_devices_data:
            logger.info("✅ Successfully fetched from /api/v2/monitor/endpoint-control/registered_ems")
            user_devices = endpoint_devices_data.get("results") or endpoint_devices_data.get("data") or []
            if isinstance(user_devices, dict):
                user_devices = user_devices.get("entries", [])
            if isinstance(user_devices, list) and len(user_devices) > 0:
                logger.info(f"Found {len(user_devices)} devices from registered_ems endpoint")
                for device in user_devices:
                    mac = device.get("mac")
                    if mac and mac not in existing_macs:
                        endpoint_devices.append({
                            "name": device.get("name") or device.get("hostname") or device.get("device") or mac,
                            "mac": mac,
                            "ip": device.get("ip") or device.get("address"),
                            "os": device.get("os") or device.get("os-type") or device.get("software_os") or "Unknown",
                            "connection_type": "wifi" if device.get("ssid") else "ethernet",
                            "ssid": device.get("ssid"),
                            "ap_sn": device.get("ap_sn"),
                            "switch_sn": device.get("switch_sn"),
                            "port": device.get("port"),
                            "status": device.get("status") or "online",
                            "vulnerabilities": device.get("vulnerabilities", 0),
                        })
                        existing_macs.add(mac)
        else:
            logger.debug("❌ Failed to fetch from /api/v2/monitor/endpoint-control/registered_ems")
    
    if not endpoint_devices:
        logger.warning("⚠️  No connected devices found from any FortiGate endpoint. This may be normal if no devices are connected.")
    else:
        logger.info(f"✅ Total connected devices found: {len(endpoint_devices)}")
    
    # Add endpoint devices to the device list
    for endpoint in endpoint_devices:
        name = (
            endpoint.get("name")
            or endpoint.get("hostname")
            or endpoint.get("mac")
            or endpoint.get("id")
        )
        if not name:
            continue
        
        # Determine device type from OS or other indicators
        os_type = (endpoint.get("os") or endpoint.get("os-type") or endpoint.get("software_os") or "").lower()
        device_type = "client"
        if "fortiap" in os_type or "ap" in os_type:
            device_type = "fortiap"
        elif "fortiswitch" in os_type or "switch" in os_type:
            device_type = "fortiswitch"
        elif "fortios" in os_type or "fortigate" in os_type:
            device_type = "fortigate"
        
        node_id = f"endpoint-{name.replace(' ', '-').replace(':', '-')}"
        # Add connection_type to help with icon selection
        connection_type = "ethernet"
        if endpoint.get("ssid") or endpoint.get("wireless") or "wifi" in os_type:
            connection_type = "wifi"
        
        devices.append(
            {
                "id": node_id,
                "name": name,
                "type": device_type,
                "os": endpoint.get("os") or endpoint.get("os-type") or endpoint.get("software_os"),
                "ip": endpoint.get("ip") or endpoint.get("address"),
                "mac": endpoint.get("mac"),
                "status": endpoint.get("status") or "online",
                "vulnerabilities": endpoint.get("vulnerabilities", 0),
                "forticlient_user": endpoint.get("forticlient_user", 0),
                "connection_type": connection_type,  # Add connection type for icon selection
                "ssid": endpoint.get("ssid"),  # Add SSID for wireless devices
            }
        )
        
        # Try to link endpoint to switch/AP based on connection info
        connected_to = (
            endpoint.get("switch")
            or endpoint.get("fortiswitch")
            or endpoint.get("ap")
            or endpoint.get("fortiap")
        )
        if connected_to:
            # Find the switch/AP device ID
            switch_ap_id = None
            for dev in devices:
                if dev.get("name") == connected_to or dev.get("id") == f"switch-{connected_to}" or dev.get("id") == f"ap-{connected_to}":
                    switch_ap_id = dev.get("id")
                    break
            
            if switch_ap_id:
                links.append(
                    {
                        "source": switch_ap_id,
                        "target": node_id,
                        "type": "wired" if "switch" in device_type else "wireless",
                        "interfaces": [endpoint.get("port")] if endpoint.get("port") else [],
                    }
                )

    normalized_devices = [
        {k: v for k, v in device.items() if v not in (None, "", [])}
        for device in devices
    ]
    normalized_links = [
        {k: v for k, v in link.items() if v not in (None, "", [])}
        for link in links
    ]

    payload = {"fabric_devices": normalized_devices, "fabric_links": normalized_links}
    return payload, f"fortigate:{creds.host}"


def _format_access_token(token: str) -> str:
    if token.lower().startswith("authorization"):
        return token
    if token.startswith("FG_API_KEY="):
        return f"Authorization: Bearer {token}"
    return f"Authorization: Bearer FG_API_KEY={token}"


def _fetch_wifi_override(credentials: FortiGateCredentials) -> List[Dict[str, Any]]:
    wifi_host = credentials.wifi_host
    if not wifi_host:
        return []

    def _candidate_urls(host: str) -> List[str]:
        urls: List[str] = []
        parsed = urlparse(host)
        if parsed.scheme:
            base = host
        else:
            base = f"https://{host}"
            parsed = urlparse(base)
        if parsed.path and parsed.path != "/":
            urls.append(base)
        else:
            base = base.rstrip("/")
            urls.extend(
                [
                    f"{base}/api/v2/monitor/wifi/managed-ap",
                    f"{base}/api/v2/monitor/wifi/managed_ap",
                    f"{base}/api/v2/cmdb/wireless-controller/wtp",
                ]
            )
        return urls

    def _normalize_query(url: str) -> str:
        parsed = urlparse(url)
        if not parsed.query:
            return url
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        new_query = urlencode(pairs, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    def _append_access_token(url: str, token: str) -> str:
        token_value = _format_access_token(token)
        parsed = urlparse(url)
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        if any(k == "access_token" for k, _ in pairs):
            return url
        pairs.append(("access_token", token_value))
        return urlunparse(parsed._replace(query=urlencode(pairs, doseq=True)))

    def _request(url: str, token: Optional[str]) -> Optional[Any]:
        session = requests.Session()
        session.verify = credentials.verify_ssl
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        safe_url = url.split("?")[0]

        def _session_login() -> bool:
            nonlocal session
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            api_session = _fortigate_api_session(base, credentials)
            if api_session:
                session = api_session
                session.verify = credentials.verify_ssl
                csrf = session.headers.get("X-CSRFTOKEN")
            else:
                csrf = _fortigate_session_login(session, base, credentials)
            if not csrf:
                return False
            headers.pop("Authorization", None)
            headers["X-CSRFTOKEN"] = csrf
            return True

        try:
            response = session.get(url, headers=headers, timeout=_HTTP_TIMEOUT)
            if response.status_code == 401 and token:
                alt_url = _append_access_token(url, token)
                if alt_url != url:
                    response = session.get(alt_url, headers=headers, timeout=_HTTP_TIMEOUT)
                    url = alt_url
            if response.status_code == 401 and credentials.username and credentials.password:
                if _session_login():
                    response = session.get(url, headers=headers, timeout=_HTTP_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.debug("Wi-Fi endpoint %s failed: %s", safe_url, exc)
            return None

    def _extract_entries(data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, dict):
            if "results" in data:
                results = data["results"]
                if isinstance(results, list):
                    return results
                if isinstance(results, dict):
                    entries = results.get("entries")
                    if isinstance(entries, list):
                        return entries
            if "data" in data and isinstance(data["data"], list):
                return data["data"]
        elif isinstance(data, list):
            return data
        return []

    tokens: List[Optional[str]] = []
    if credentials.wifi_token and credentials.wifi_token not in tokens:
        tokens.append(credentials.wifi_token)
    if credentials.token and credentials.token not in tokens:
        tokens.append(credentials.token)
    tokens.append(None)

    entries: List[Dict[str, Any]] = []
    visited: set[Tuple[str, Optional[str]]] = set()
    for base_url in _candidate_urls(wifi_host):
        base_variants = [base_url]
        normalized = _normalize_query(base_url)
        if normalized != base_url:
            base_variants.insert(0, normalized)

        for url_variant in base_variants:
            for token in tokens:
                attempt_pairs: List[Tuple[str, Optional[str]]] = []
                attempt_pairs.append((url_variant, token))
                if token:
                    attempt_pairs.append((_append_access_token(url_variant, token), None))
                else:
                    attempt_pairs.append((url_variant, None))

                for attempt_url, attempt_token in attempt_pairs:
                    combo = (attempt_url, attempt_token)
                    if combo in visited:
                        continue
                    visited.add(combo)
                    data = _request(attempt_url, attempt_token)
                    if not data:
                        continue
                    records = _extract_entries(data)
                    if records:
                        entries.extend(records)
                        break
                if entries:
                    break
            if entries:
                break
        if entries:
            break
    return entries


def _meraki_env_credentials(credentials: Optional[MerakiCredentials]) -> Optional[MerakiCredentials]:
    api_key = _first_non_empty(
        credentials.api_key if credentials else None,
        os.getenv("MERAKI_API_KEY"),
    )
    organization_id = _first_non_empty(
        credentials.organization_id if credentials else None,
        os.getenv("MERAKI_ORG_ID"),
        os.getenv("MERAKI_ORGANIZATION_ID"),
    )
    network_id = _first_non_empty(
        credentials.network_id if credentials else None,
        os.getenv("MERAKI_NETWORK_ID"),
    )
    base_url = _first_non_empty(
        credentials.base_url if credentials else None,
        os.getenv("MERAKI_BASE_URL"),
        "https://api.meraki.com/api/v1",
    )
    if not api_key or not network_id:
        return None
    return MerakiCredentials(
        api_key=api_key,
        organization_id=organization_id,
        network_id=network_id,
        base_url=base_url,
    )


def _extract_link_endpoint(value: Any) -> Optional[str]:
    if isinstance(value, dict):
        return _first_non_empty(
            value.get("serial"),
            value.get("mac"),
            value.get("deviceId"),
            value.get("id"),
            value.get("name"),
        )
    if isinstance(value, str):
        return value
    return None


def _fetch_meraki_payload(
    credentials: Optional[MerakiCredentials],
) -> Optional[Tuple[Dict[str, Any], str]]:
    creds = _meraki_env_credentials(credentials)
    if not creds:
        return None

    base_url = creds.base_url.rstrip("/")
    headers = {
        "Authorization": f"Bearer {creds.api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        devices_resp = requests.get(
            f"{base_url}/networks/{creds.network_id}/devices",
            headers=headers,
            timeout=_HTTP_TIMEOUT,
        )
        devices_resp.raise_for_status()
        devices_raw = devices_resp.json()
    except requests.exceptions.RequestException as exc:
        logger.warning("Failed to fetch Meraki devices for network %s: %s", creds.network_id, exc)
        return None

    devices: List[Dict[str, Any]] = []
    if isinstance(devices_raw, list):
        for raw in devices_raw:
            node_id = _first_non_empty(
                raw.get("serial"),
                raw.get("mac"),
                raw.get("name"),
            )
            if not node_id:
                continue
            device_entry = {
                "id": node_id,
                "name": raw.get("name") or raw.get("model") or node_id,
                "model": raw.get("model"),
                "lanIp": raw.get("lanIp"),
                "serial": raw.get("serial"),
                "tags": raw.get("tags", []),
                "productType": raw.get("productType"),
                "type": raw.get("productType") or raw.get("model"),
            }
            devices.append({k: v for k, v in device_entry.items() if v not in (None, "", [])})

    links: List[Dict[str, Any]] = []
    try:
        link_resp = requests.get(
            f"{base_url}/networks/{creds.network_id}/topology/linkLayer",
            headers=headers,
            timeout=_HTTP_TIMEOUT,
        )
        if link_resp.status_code == 200:
            link_data = link_resp.json() or {}
            raw_links = link_data.get("links") if isinstance(link_data, dict) else link_data
            if isinstance(raw_links, list):
                for entry in raw_links:
                    if not isinstance(entry, dict):
                        continue
                    source = _extract_link_endpoint(entry.get("source") or entry.get("src"))
                    target = _extract_link_endpoint(entry.get("target") or entry.get("dst"))
                    if not source or not target:
                        continue
                    interfaces: List[str] = []
                    for key in (
                        "interfaces",
                        "ports",
                        "sourcePort",
                        "targetPort",
                        "srcPort",
                        "dstPort",
                        "upstreamPort",
                        "downstreamPort",
                    ):
                        value = entry.get(key)
                        if isinstance(value, str):
                            interfaces.append(value)
                        elif isinstance(value, list):
                            interfaces.extend(str(v) for v in value if v)
                    links.append(
                        {
                            "source": source,
                            "target": target,
                            "type": entry.get("type") or "ethernet",
                            "interfaces": interfaces,
                        }
                    )
    except requests.exceptions.RequestException as exc:
        logger.debug("Meraki link-layer fetch failed for %s: %s", creds.network_id, exc)

    if not devices:
        logger.warning("Meraki topology fetch returned no devices for network %s", creds.network_id)
        return None

    payload = {"devices": devices, "links": links}
    return payload, f"live:{creds.network_id}"


def _to_node(node_id: str, vendor: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
    metadata = {
        "id": node_id,
        "vendor": vendor,
        "name": attributes.get("name", node_id),
        "ip": attributes.get("ip") or attributes.get("lanIp"),
        "model": attributes.get("model"),
        "serial": attributes.get("serial"),
        "status": attributes.get("status", "active"),
    }

    if vendor == "fortinet":
        metadata["type"] = attributes.get("type", "device")
        metadata["role"] = attributes.get("role")
    elif vendor == "meraki":
        model_lower = (attributes.get("model") or "").upper()
        product_type = (attributes.get("productType") or attributes.get("type") or "").lower()
        if "wireless" in product_type or "mr" in model_lower:
            metadata["type"] = "wireless"
        elif "appliance" in product_type or model_lower.startswith("MX"):
            metadata["type"] = "gateway"
        else:
            metadata["type"] = "switch"
        metadata["tags"] = attributes.get("tags", [])

    return {k: v for k, v in metadata.items() if v not in (None, [], "")}


def _to_link(source: str, target: str, link_type: str, interfaces: Iterable[str]) -> Dict[str, Any]:
    link = {"from": source, "to": target, "type": link_type}
    ports = [p for p in interfaces if p]
    if ports:
        link["ports"] = ports
    return link


def _write_json(topology: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(topology, indent=2, sort_keys=True), encoding="utf-8")


def _write_graphml(topology: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    def _node_attrs(node: Dict[str, Any]) -> str:
        return " ".join(
            f'{key}="{value}"'
            for key, value in node.items()
            if key != "id" and value is not None
        )

    def _edge_attrs(edge: Dict[str, Any]) -> str:
        return " ".join(
            f'{key}="{value}"'
            for key, value in edge.items()
            if key not in {"from", "to"} and value is not None
        )

    lines: List[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '  <graph id="automated-topology" edgedefault="undirected">',
    ]

    for node in topology.get("nodes", []):
        attrs = _node_attrs(node)
        if attrs:
            lines.append(f'    <node id="{node["id"]}" {attrs}/>')
        else:
            lines.append(f'    <node id="{node["id"]}"/>')

    for idx, edge in enumerate(topology.get("links", [])):
        attrs = _edge_attrs(edge)
        if attrs:
            lines.append(
                f'    <edge id="e{idx}" source="{edge["from"]}" target="{edge["to"]}" {attrs}/>'
            )
        else:
            lines.append(
                f'    <edge id="e{idx}" source="{edge["from"]}" target="{edge["to"]}"/>'
            )

    lines.append("  </graph>")
    lines.append("</graphml>")
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def resolve_inputs(
    fortigate_json: Optional[str],
    fortimanager_json: Optional[str],
    meraki_json: Optional[str],
    *,
    use_samples: bool = True,
    fortigate_credentials: Optional[FortiGateCredentials] = None,
    fortimanager_credentials: Optional[FortiManagerCredentials] = None,
    meraki_credentials: Optional[MerakiCredentials] = None,
) -> TopologyInputs:
    """Resolve payloads from provided paths/env/sample data."""

    fortigate: Optional[Dict[str, Any]]
    fortigate_src: str
    try:
        fortigate, fortigate_src = _resolve_payload(
            fortigate_json,
            FORTIGATE_JSON_ENV,
            SAMPLE_FORTIMANAGER_PAYLOAD,
            use_samples,
            fetcher=lambda: _fetch_fortigate_payload(fortigate_credentials),
        )
    except ValueError:
        fortigate = None
        fortigate_src = "fortigate:unavailable"

    try:
        fortimanager, fortinet_src = _resolve_payload(
            fortimanager_json,
            FORTIMANAGER_JSON_ENV,
            SAMPLE_FORTIMANAGER_PAYLOAD,
            use_samples,
            fetcher=lambda: _fetch_fortimanager_payload(fortimanager_credentials),
        )
    except ValueError:
        if not fortigate:
            raise
        fortimanager = fortigate
        fortinet_src = fortigate_src
    try:
        meraki, meraki_src = _resolve_payload(
            meraki_json,
            MERAKI_JSON_ENV,
            SAMPLE_MERAKI_PAYLOAD,
            use_samples,
            fetcher=lambda: _fetch_meraki_payload(meraki_credentials),
        )
    except ValueError:
        meraki = {"devices": [], "links": []}
        meraki_src = "meraki:unavailable"
    return TopologyInputs(
        fortimanager=fortigate or fortimanager,
        meraki=meraki,
        fortimanager_source=fortigate_src if fortigate else fortinet_src,
        meraki_source=meraki_src,
    )


def combine_topology(inputs: TopologyInputs) -> Dict[str, Any]:
    """Merge Fortimanager and Meraki payloads into canonical topology JSON."""

    nodes: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []

    fortinet_devices = inputs.fortimanager.get("fabric_devices", [])
    for device in fortinet_devices:
        nodes.append(_to_node(device["id"], "fortinet", device))

    meraki_devices = inputs.meraki.get("devices", [])
    for device in meraki_devices:
        nodes.append(_to_node(device["id"], "meraki", device))

    for link in inputs.fortimanager.get("fabric_links", []):
        links.append(
            _to_link(
                link.get("source"),
                link.get("target"),
                link.get("type", "link"),
                link.get("interfaces", []),
            )
        )

    for link in inputs.meraki.get("links", []):
        links.append(
            _to_link(
                link.get("source"),
                link.get("target"),
                link.get("type", "ethernet"),
                link.get("interfaces", []),
            )
        )

    topology = {
        "nodes": nodes,
        "links": links,
        "metadata": {
            "source": "automated_topology_workflow",
            "fortimanager_device_count": len(fortinet_devices),
            "meraki_device_count": len(meraki_devices),
            "node_count": len(nodes),
            "link_count": len(links),
        },
    }
    return topology


def generate_artifacts(
    *,
    fortigate_json: Optional[str] = None,
    fortimanager_json: Optional[str] = None,
    meraki_json: Optional[str] = None,
    fortigate_credentials: Optional[FortiGateCredentials] = None,
    fortimanager_credentials: Optional[FortiManagerCredentials] = None,
    meraki_credentials: Optional[MerakiCredentials] = None,
    use_samples: bool = True,
    output_dir: Optional[Path] = None,
    json_name: str = "combined_topology.json",
    graphml_name: str = "combined_topology.graphml",
    drawio_name: Optional[str] = None,
    write_files: bool = False,
) -> Dict[str, Any]:
    """Resolve inputs, combine topology, and optionally write artefacts."""

    inputs = resolve_inputs(
        fortigate_json=fortigate_json,
        fortimanager_json=fortimanager_json,
        meraki_json=meraki_json,
        use_samples=use_samples,
        fortigate_credentials=fortigate_credentials,
        fortimanager_credentials=fortimanager_credentials,
        meraki_credentials=meraki_credentials,
    )
    topology = combine_topology(inputs)

    artifacts: Optional[Dict[str, Any]] = None
    if write_files:
        target_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
        target_dir.mkdir(parents=True, exist_ok=True)
        json_path = target_dir / json_name
        graphml_path = target_dir / graphml_name
        _write_json(topology, json_path)
        _write_graphml(topology, graphml_path)
        artifacts = {
            "json_path": str(json_path),
            "graphml_path": str(graphml_path),
        }
        if drawio_name:
            drawio_path = target_dir / drawio_name
            drawio_xml = generate_drawio_xml_from_topology(topology)
            drawio_path.write_text(drawio_xml, encoding="utf-8")
            artifacts["drawio_path"] = str(drawio_path)

    return {
        "topology": topology,
        "artifacts": artifacts,
        "sources": {
            "fortimanager": {
                "source": inputs.fortimanager_source,
                "device_count": len(inputs.fortimanager.get("fabric_devices", [])),
            },
            "meraki": {
                "source": inputs.meraki_source,
                "device_count": len(inputs.meraki.get("devices", [])),
            },
        },
    }


def list_artifacts(directory: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Return metadata about generated topology artefacts."""

    target_dir = Path(directory or DEFAULT_OUTPUT_DIR)
    if not target_dir.exists():
        return []

    artefacts: List[Dict[str, Any]] = []
    for path in sorted(target_dir.glob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".json", ".graphml", ".xml", ".drawio"}:
            continue
        try:
            stat = path.stat()
        except OSError:  # pragma: no cover - filesystem race
            continue
        artefacts.append(
            {
                "name": path.name,
                "path": str(path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "type": path.suffix.lstrip("."),
            }
        )
    return artefacts


__all__ = [
    "DEFAULT_OUTPUT_DIR",
    "FortiGateCredentials",
    "FortiManagerCredentials",
    "MerakiCredentials",
    "SAMPLE_FORTIMANAGER_PAYLOAD",
    "SAMPLE_MERAKI_PAYLOAD",
    "TopologyInputs",
    "combine_topology",
    "generate_artifacts",
    "list_artifacts",
    "resolve_inputs",
]
