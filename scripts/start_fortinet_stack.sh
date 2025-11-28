#!/usr/bin/env bash
set -euo pipefail

# Simple helper to start the Fortinet HTTP bridge and the enhanced-network
# FastAPI web API. Uses `uv run --no-project` so it does not depend on any
# local Python packaging layout.

BRIDGE_DIR="/home/keith/chat-copilot/fortinet-meraki-llm/mcp-integration/fortinet-enhanced"
API_DIR="/home/keith/enhanced-network-api-corporate"

BRIDGE_LOG="${BRIDGE_DIR}/fortinet_http_bridge.log"
API_LOG="${API_DIR}/platform_web_api_fastapi.log"

echo "Starting Fortinet HTTP bridge (port 9001)..."
(
  cd "${BRIDGE_DIR}"
  uv run --no-project \
    --with httpx \
    --with fastapi \
    --with python-dotenv \
    --with pydantic \
    --with uvicorn[standard] \
    python fortinet_http_bridge.py \
    >"${BRIDGE_LOG}" 2>&1
) &
BRIDGE_PID=$!

echo "Fortinet HTTP bridge started with PID ${BRIDGE_PID}, logging to ${BRIDGE_LOG}"

sleep 2

echo "Starting enhanced-network FastAPI web API (port 8000)..."
(
  cd "${API_DIR}"
  uv run --no-project \
    --with fastapi \
    --with uvicorn[standard] \
    python -m uvicorn enhanced_network_api.platform_web_api_fastapi:app --host 0.0.0.0 --port 8000 \
    >"${API_LOG}" 2>&1
) &
API_PID=$!

echo "Enhanced-network API started with PID ${API_PID}, logging to ${API_LOG}"

echo
echo "Fortinet stack is starting up. PIDs:"
echo "  Bridge : ${BRIDGE_PID} (http://127.0.0.1:9001)"
echo "  API    : ${API_PID} (http://127.0.0.1:8000)"
echo
echo "To stop them, run: kill ${BRIDGE_PID} ${API_PID}"
