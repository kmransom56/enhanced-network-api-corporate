# Browser MCP Tools Setup

## Current Status

The MCP browser tools are available and functional, but they cannot access `localhost:11111` because the browser runs in an isolated network context (likely a Docker container) that cannot reach the host machine's localhost.

## Available Browser Tools

The following MCP browser tools are available:
- `browser_navigate` - Navigate to URLs
- `browser_snapshot` - Capture accessibility snapshot
- `browser_take_screenshot` - Take screenshots
- `browser_console_messages` - Read console messages
- `browser_evaluate` - Execute JavaScript
- And many more browser interaction tools

## Network Access Issue

**Problem**: Browser tools return `ERR_CONNECTION_REFUSED` when trying to access `localhost:11111` or `127.0.0.1:11111`

**Root Cause**: The browser runs in an isolated network and cannot access the host's localhost.

**Verification**: 
- ✅ Service is running: `docker compose ps enhanced-network-api` shows "Up"
- ✅ Service responds: `curl http://localhost:11111/health` returns HTTP 200
- ❌ Browser cannot connect: Browser tools get `ERR_CONNECTION_REFUSED`

## Solutions

### Option 1: Use Host Network Mode (if browser runs in Docker)
If the browser MCP server runs in Docker, configure it to use host network:
```yaml
# In browser MCP server docker-compose.yml
network_mode: "host"
```

### Option 2: Use Host Machine IP
Instead of `localhost`, use the actual host machine IP address:
- Find host IP: `hostname -I | awk '{print $1}'`
- Use: `http://<HOST_IP>:11111/static/babylon_lab_view.html`

### Option 3: Expose via Nginx/Tunnel
Set up a tunnel or reverse proxy that the browser can access.

### Option 4: Manual Browser Testing
Since the browser tools have network limitations, manual testing is recommended:
1. Open browser on your machine: `http://localhost:11111/static/babylon_lab_view.html`
2. Open Developer Tools (F12)
3. Check Console tab for:
   - `🎨 Attempting to create 3D from SVG`
   - `✅ Successfully created 3D mesh from SVG`
   - Any errors about SVG loading
4. Check Network tab for:
   - SVG file requests (should be HTTP 200)
   - API requests to `/api/topology/babylon-lab-format`

## Testing Checklist

### 1. Verify Service is Running
```bash
docker compose -f docker-compose.corporate.yml ps enhanced-network-api
curl http://localhost:11111/health
```

### 2. Verify SVG Files Are Accessible
```bash
curl http://localhost:11111/extracted_icons/lab_vss_svgs/shape_001___PF.svg
# Should return SVG content (HTTP 200)
```

### 3. Verify API Returns icon_svg
```bash
curl http://localhost:11111/api/topology/babylon-lab-format | jq '.models[] | {name, type, icon_svg}'
```

### 4. Manual Browser Testing
1. Navigate to: `http://localhost:11111/static/babylon_lab_view.html`
2. Open Console (F12)
3. Look for:
   - ✅ SVG loading messages
   - ✅ 3D mesh creation success
   - ❌ Any 404 errors for SVG files
   - ❌ Any JavaScript errors

## Expected Console Output

### Success Case:
```
🎨 Attempting to create 3D from SVG: /extracted_icons/lab_vss_svgs/shape_001___PF.svg for FW
✅ Successfully created 3D mesh from SVG: /extracted_icons/lab_vss_svgs/shape_001___PF.svg
✅ Created 3D mesh from SVG: /extracted_icons/lab_vss_svgs/shape_001___PF.svg (X points)
```

### Error Case:
```
SVG not found: /extracted_icons/lab_vss_svgs/shape_001___PF.svg
⚠️ Failed to create 3D from SVG: /extracted_icons/lab_vss_svgs/shape_001___PF.svg, trying fallbacks...
```

## Network Configuration

If you need the browser tools to access the service, you may need to:

1. **Configure browser MCP server network**: Check the MCP server configuration for network settings
2. **Use host.docker.internal**: If browser runs in Docker, try `http://host.docker.internal:11111`
3. **Expose service publicly**: Use a public URL or tunnel service
4. **Run browser on host**: Configure browser to run directly on the host machine

## Current Workaround

Since browser tools cannot access localhost, use:
- ✅ Manual browser testing on your machine
- ✅ curl commands to verify API responses
- ✅ Server logs to check for errors
- ✅ Screenshots from your browser (manual)

The browser MCP tools are functional but limited by network isolation. For local development, manual browser testing is the most reliable approach.

