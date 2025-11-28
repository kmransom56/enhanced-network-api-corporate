#!/usr/bin/env bash
# Launch the Fortinet MCP bridge and FastAPI platform services inside the uv virtual environment.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/.logs"
mkdir -p "${LOG_DIR}"

# Load environment variables from .env (if python-dotenv is available)
if [[ -f "${ROOT_DIR}/.env" ]]; then
    if command -v python3 >/dev/null 2>&1; then
        eval "$(
            python3 - <<'PY' 2>/dev/null || true
import pathlib, shlex
from dotenv import dotenv_values  # type: ignore

env_path = pathlib.Path(__file__).resolve().parents[1] / ".env"
try:
    values = dotenv_values(env_path)
except Exception:
    values = {}

for key, value in values.items():
    if value is None:
        continue
    print(f"export {key}={shlex.quote(value)}")
PY
        )"
    fi
fi

# Default ports (override via environment variables if desired)
MCP_PORT="${MCP_PORT:-9001}"
FASTAPI_PORT="${FASTAPI_PORT:-11111}"

echo "🔧 Starting Fortinet MCP bridge on 127.0.0.1:${MCP_PORT}"
cd "${ROOT_DIR}"
uv run uvicorn mcp_bridge:app --host 127.0.0.1 --port "${MCP_PORT}" \
    > "${LOG_DIR}/mcp_bridge.log" 2>&1 &
MCP_PID=$!

sleep 1

echo "🚀 Starting FastAPI platform on 0.0.0.0:${FASTAPI_PORT}"
uv run uvicorn src.enhanced_network_api.platform_web_api_fastapi:app \
    --host 0.0.0.0 --port "${FASTAPI_PORT}" \
    > "${LOG_DIR}/fastapi.log" 2>&1 &
FASTAPI_PID=$!

cleanup() {
    echo
    echo "🛑 Shutting down services..."
    kill "${FASTAPI_PID}" "${MCP_PID}" >/dev/null 2>&1 || true
    wait "${FASTAPI_PID}" "${MCP_PID}" >/dev/null 2>&1 || true
}

trap cleanup INT TERM EXIT

echo
echo "✅ Services started:"
echo "   MCP bridge log:     ${LOG_DIR}/mcp_bridge.log"
echo "   FastAPI log:        ${LOG_DIR}/fastapi.log"
echo "   MCP bridge PID:     ${MCP_PID}"
echo "   FastAPI PID:        ${FASTAPI_PID}"
echo
echo "Press Ctrl+C to stop both services."

wait
