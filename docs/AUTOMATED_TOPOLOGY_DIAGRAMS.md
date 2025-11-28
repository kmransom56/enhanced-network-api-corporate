## Automated Topology Diagrams

This guide distills the research captured in `Creating Network Topology Diagrams from FortiManager and Meraki API Data Sources.md`
into a practical, repeatable workflow for the Enhanced Network API platform.

### Why automate?
- Keeps documentation synchronized with live Fortinet and Meraki infrastructure.
- Enables 2D (Visio, DrawIO, yEd) and 3D (Plotly, Three.js, Babylon.js) visualizations from the same source data.
- Feeds MCP-driven diagram automation for AI-assisted troubleshooting and reporting.

### Workflow overview
1. **Collect** device and topology data  
   - FortiManager JSON-RPC: inventory, fabric links, interfaces.  
   - Meraki Dashboard REST: networks, L2/L3 topology, LLDP/CDP neighbors.  
   - Optional SNMP / pyATS enrichment for interface metrics.

2. **Normalize** into a shared schema  
   - Nodes: device metadata, management IPs, vendor-specific attributes.  
   - Links: typed edges with interface labels, bandwidth, health flags.  
   - Supplement with site/group metadata for hierarchical layouts.

3. **Generate artifacts**
   - `combined_topology.json`: canonical JSON for REST responses and 3D scenes.  
   - `combined_topology.graphml`: GraphML for yEd / AutoNetkit pipelines.  
   - Optional DrawIO XML or Mermaid definitions for documentation portals.

4. **Render**
   - DrawIO MCP server for conversational diagram updates.  
   - N2G / yEd for export to Visio and PDF.  
   - Enhanced Network API 3D scene endpoint for immersive views.

5. **Automate**
   - Schedule `scripts/generate_topology_artifacts.py` to detect topology drift.  
   - Feed generated diagrams into MCP workflows for ChatOps, CI/CD, or self-healing playbooks.

### Starter script
Use `scripts/generate_topology_artifacts.py` to bootstrap the process:

```bash
uv run python scripts/generate_topology_artifacts.py \
  --fortimanager-json ./data/fortimanager_topology.json \
  --meraki-json ./data/meraki_topology.json \
  --output-dir ./data/generated
```

The script can read live API responses when `FORTIMANAGER_HOST`, `FORTIMANAGER_TOKEN`,
and `MERAKI_API_KEY` environment variables are supplied. By default it falls back to
sample payloads so you can test the pipeline without production credentials.

### Integration tips
- Commit generated JSON/GraphML artifacts alongside infrastructure-as-code changes for traceability.
- Reference the JSON output in `_normalize_scene` before publishing 3D visualizations.
- Configure the DrawIO MCP server to watch the output directory for quick, AI-driven redraws.
- Surface the HTML summary at `/automated-topology` inside the FastAPI UI (see `smart-tools` link).

### FastAPI endpoints
- `POST /api/topology/automated`: combine FortiManager, Meraki, and FortiGate data, returning normalized JSON (optionally persisting JSON/GraphML/DrawIO artifacts).
- `POST /api/topology/automated/drawio`: call the MCP bridge to generate DrawIO XML, with options for layout/grouping, topology refresh, and on-disk `.drawio` export in `data/generated/`.
- `GET /api/topology/automated/artifacts`: browse previously generated JSON, GraphML, and DrawIO files ready for download from the UI or automation workflows.

### Scheduled exports (long interval)
- Use `scripts/trigger_drawio_export.py` to invoke `POST /api/topology/automated/drawio` from timers or CI jobs:

```bash
uv run python scripts/trigger_drawio_export.py \
  --output-dir data/generated \
  --filename weekly.drawio \
  --layout hierarchical \
  --group-by vendor
```

- The script respects `DRAWIO_EXPORT_URL`, so production FortiManager gateways can override the endpoint without editing the timer.
- Set `AUTO_DRAWIO_EXPORT=1` (plus optional `AUTO_DRAWIO_*` overrides) to trigger an asynchronous export immediately after `/api/platform/discover` succeeds—useful when discovery runs infrequently but you want artifacts refreshed automatically.
- For static networks, start with a weekly cadence; adjust the interval as FortiManager integration expands:

```ini
# /etc/systemd/system/mcp-drawio-export.timer
[Unit]
Description=Weekly DrawIO export (adjust OnCalendar for production)

[Timer]
OnCalendar=Mon 02:00
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/mcp-drawio-export.service
[Unit]
Description=Trigger DrawIO export via FastAPI
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/home/keith/enhanced-network-api-corporate
ExecStart=/usr/bin/env uv run python scripts/trigger_drawio_export.py \
  --output-dir data/generated --filename weekly.drawio
```

- Enable with `sudo systemctl enable --now mcp-drawio-export.timer`. Update `OnCalendar=` or pass different CLI flags as topology requirements evolve.

### Next steps
1. Validate credentials and API reachability in non-production lab environments.  
2. Extend the script to push refreshed diagrams to collaboration spaces (Confluence, SharePoint).  
3. Combine with the platform health monitor to trigger regenerations when device inventory changes.  
4. Experiment with the MCP workflow examples from the research memo to close the loop with self-healing actions.
