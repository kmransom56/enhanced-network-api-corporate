  
  
 • ✅ platform_web_api_fastapi audit: response caching tightened (docs index pre-warm, tree mtime cache), vLLM AsyncClient pooling, and
   startup warmup to eliminate first-request stalls.
 • ✅ FortiGate docs search now persists a prebuilt index (.cache/fortigate_docs_index.json) and reuses recorded tree mtimes so warm-up drops
   from double-digit seconds to <1 ms once cached; steady-state searches remain <50 ms.
 • ✅ Profiling identified `run_discovery` and topology normalization as blocking the event loop; both are now offloaded via `asyncio.to_thread`
    with `_normalize_scene` backed by an LRU cache and signature hashing so repeated scene requests return in microseconds instead of milliseconds.
 • After each optimization, rerun uv run pytest tests/test_platform_web_api_fastapi_unit.py to confirm behaviour stays green and keep
    100 % coverage intact.

  Diagram Workflow Integration
  • ✅ Automated Topology Diagrams guide published under docs/ and linked directly from Smart Tools and /automated-topology for one-click reference.
  • ✅ Smart Tools now exposes MCP-backed DrawIO export controls (layout/group toggles) via POST /api/topology/automated/drawio with optional on-disk .drawio persistence.
  • ✅ Long-interval scheduling guidance added (systemd timer + `scripts/trigger_drawio_export.py`) so exports stay infrequent today but can be tightened for production FortiManager rollouts.