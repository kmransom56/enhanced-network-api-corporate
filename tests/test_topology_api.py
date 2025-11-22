"""
Live topology API integration tests using real Fortinet data.
"""

import json
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def topology_scene(test_client: TestClient) -> dict:
    """
    Fetch the live topology scene once for the entire session.
    Relies on the MCP HTTP bridge started in conftest.py.
    """
    response = test_client.get("/api/topology/scene")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, dict)
    assert "nodes" in data and isinstance(data["nodes"], list)
    assert "links" in data and isinstance(data["links"], list)
    return data


@pytest.fixture(scope="session")
def topology_raw(test_client: TestClient) -> dict:
    """Fetch raw FortiGate topology once for reuse across tests."""
    response = test_client.get("/api/topology/raw")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, dict)
    assert "devices" in data and isinstance(data["devices"], list)
    assert "links" in data and isinstance(data["links"], list)
    return data


@pytest.mark.api
@pytest.mark.topology
def test_scene_contains_gateway_device(topology_scene: dict):
    """A FortiGate gateway should always be present in the live scene."""
    nodes = topology_scene["nodes"]
    assert any(node.get("type") == "fortigate" for node in nodes), "No FortiGate gateway detected"


@pytest.mark.api
@pytest.mark.topology
def test_scene_includes_clients(topology_scene: dict):
    """Client endpoints should be discovered alongside infrastructure nodes."""
    client_nodes = [node for node in topology_scene["nodes"] if node.get("role") == "client"]
    assert client_nodes, "No client devices found in topology discovery"


@pytest.mark.api
@pytest.mark.topology
def test_scene_links_reference_known_nodes(topology_scene: dict):
    """Every reported link should reference discovered node identifiers."""
    node_ids = {node["id"] for node in topology_scene["nodes"] if "id" in node}
    assert node_ids, "No node identifiers available to validate link endpoints"

    for link in topology_scene["links"]:
        source = link.get("source") or link.get("from")
        target = link.get("target") or link.get("to")
        assert source in node_ids, f"Link source {source} not found among nodes"
        assert target in node_ids, f"Link target {target} not found among nodes"


@pytest.mark.api
@pytest.mark.topology
def test_scene_nodes_include_network_metadata(topology_scene: dict):
    """Nodes should contain basic metadata such as hostname or IP."""
    for node in topology_scene["nodes"]:
        assert node.get("hostname") or node.get("name"), f"Node missing name/hostname: {node}"
        assert node.get("ip") is not None, f"Node missing IP information: {node}"


@pytest.mark.api
@pytest.mark.topology
def test_scene_request_performance(test_client: TestClient):
    """A direct scene request should complete successfully using the live bridge."""
    response = test_client.get("/api/topology/scene")
    assert response.status_code == 200
    payload = response.json()
    assert "nodes" in payload and len(payload["nodes"]) > 0
    assert "links" in payload


@pytest.mark.api
@pytest.mark.topology
def test_topology_pages_serve_html(test_client: TestClient):
    """Ensure the 2D/3D visualization pages respond with HTML content."""
    for path in ("/", "/2d-topology-enhanced", "/babylon-test"):
        response = test_client.get(path)
        assert response.status_code == 200, f"{path} did not return 200"
        assert "<html" in response.text.lower(), f"{path} did not return HTML content"


@pytest.mark.api
@pytest.mark.topology
def test_raw_topology_contains_gateways(topology_raw: dict):
    """Raw topology must include at least one FortiGate gateway with serial metadata."""
    gateways = [device for device in topology_raw["devices"] if device.get("type") == "fortigate"]
    assert gateways, "No FortiGate gateways returned from raw topology"
    assert all(device.get("serial") for device in gateways), "Gateway missing serial number"


@pytest.mark.api
@pytest.mark.topology
def test_raw_topology_links_reference_devices(topology_raw: dict):
    """Raw topology links should reference valid device identifiers."""
    device_ids = {device["id"] for device in topology_raw["devices"] if "id" in device}
    assert device_ids, "Device identifiers missing from raw topology result"
    for link in topology_raw["links"]:
        assert link.get("source_id") in device_ids, f"Unknown source id {link}"
        assert link.get("target_id") in device_ids, f"Unknown target id {link}"


@pytest.mark.api
@pytest.mark.topology
def test_export_topology_json(test_client: TestClient):
    """The export endpoint should return serialised topology data via the MCP bridge."""
    response = test_client.post(
        "/mcp/export_topology_json",
        json={"include_health": False, "format": "json"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert "topology" in payload, "Export response missing topology data"
    topology = payload["topology"]
    assert "devices" in topology
    assert "links" in topology