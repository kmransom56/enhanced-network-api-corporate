#!/usr/bin/env bash
set -euo pipefail

SESSION_NAME="fortinet-stack"
BRIDGE_CMD="cd /home/keith/chat-copilot/fortinet-meraki-llm/mcp-integration/fortinet-enhanced && uv run --no-project --with httpx --with fastapi --with python-dotenv --with pydantic --with uvicorn[standard] python fortinet_http_bridge.py"
API_CMD="cd /home/keith/enhanced-network-api-corporate && uv run --no-project --with fastapi --with uvicorn[standard] python -m uvicorn enhanced_network_api.platform_web_api_fastapi:app --host 0.0.0.0 --port 8000"

# Create or attach to tmux session
if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
  echo "Attaching to existing tmux session: ${SESSION_NAME}"
  exec tmux attach-session -t "${SESSION_NAME}"
else
  echo "Creating new tmux session: ${SESSION_NAME}"
  tmux new-session -d -s "${SESSION_NAME}" "${BRIDGE_CMD}"
  tmux split-window -h -t "${SESSION_NAME}:0" "${API_CMD}"
  tmux select-pane -t "${SESSION_NAME}:0.0"
  echo "Bridge running in left pane, API in right pane."
  exec tmux attach-session -t "${SESSION_NAME}"
fi
