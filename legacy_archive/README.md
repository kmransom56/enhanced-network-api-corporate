## Legacy Archive Overview

This directory contains scripts, data dumps, and status notes that the current
FastAPI + MCP stack no longer depends on. They were moved here during
housekeeping to keep the project root focused on the live application.

### Archived items

- Historical automation scripts (e.g., `deep_fortigate_explorer.py`,
  `deploy_sealed.py`, `license_feature_check.py`, `run_complete_workflow.py`)
- FortiGate discovery snapshots and alternate flows (`complete_fortigate_discovery.*`,
  `bearer_token_discovery.py`, `session_auth_discovery.py`, etc.)
- Legacy documentation and “*_COMPLETE.md” status reports
- Old example/demo content (`examples/`, `eraser_ai_processed/`, `reports/`)
- Archived Playwright or tooling experiments (`playwright_device_finder.py`, `validate_js.py`)

### Notes

- Nothing in this folder is invoked by the live platform. You can safely delete
  it once you’re sure you don’t need the legacy tooling.
- The active scripts now live under `scripts/` (`start_platform_stack.sh`,
  `trigger_drawio_export.py`), and the running application code remains under `src/`.
- The `data/` directory still contains any sample artifacts that were generated;
  they can be pruned separately if no longer required.

If you later discover a utility you want to resurrect, simply move it back to
the root or call it directly from this archive.
