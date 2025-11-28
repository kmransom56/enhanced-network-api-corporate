# DrawIO Fortinet/Meraki MCP Server

An MCP (Model Context Protocol) server that enables AI-assisted network diagram generation by integrating DrawIO with FortiManager and Meraki APIs.

## Features

- **Real-time Topology Discovery**: Automatically collect network topology from FortiManager and Meraki Dashboard
- **Natural Language Diagramming**: Generate network diagrams using natural language commands
- **Multiple Layout Options**: Hierarchical, circular, force-directed, and custom layouts
- **Device-specific Styling**: Automatic color-coding and icon selection for different device types
- **Bidirectional Workflow**: Export diagrams and import configurations
- **Real-time Updates**: Continuous topology monitoring with automatic diagram updates

## Supported Devices

### Fortinet
- FortiGate Firewalls
- FortiSwitch Ethernet Switches  
- FortiAP Wireless Access Points
- FortiManager Centralized Management

### Meraki
- MX Security Appliances
- MS Switches
- MR Access Points
- MV Cameras
- SM Mobile Device Management

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/enhanced-network-api/drawio-fortinet-meraki-mcp.git
cd drawio-fortinet-meraki-mcp

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### 2. Configuration

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your API credentials:

```bash
# FortiManager Configuration
FORTIMANAGER_HOST=192.168.0.254
FORTIMANAGER_USERNAME=admin
FORTIMANAGER_PASSWORD=your_password

# Meraki Dashboard Configuration  
MERAKI_API_KEY=your_meraki_api_key
```

### 3. DrawIO Setup

1. Install the [DrawIO MCP Extension](https://chromewebstore.google.com/detail/drawio-mcp-extension/okdbbjbbccdhhfaefmcmekalmmdjjide)
2. Open [DrawIO](https://app.diagrams.net/)
3. The extension should show "Connected" status

### 4. MCP Client Configuration

#### Claude Desktop (macOS)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "drawio-fortinet-meraki": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/drawio-fortinet-meraki-mcp"
      }
    }
  }
}
```

#### Windsurf/Cursor/VS Code

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "drawio-fortinet-meraki": {
      "command": "python",
      "args": ["/path/to/drawio-fortinet-meraki-mcp/mcp_server.py"],
      "cwd": "/path/to/drawio-fortinet-meraki-mcp"
    }
  }
}
```

## Usage Examples

### Basic Topology Collection

```
User: Collect the network topology from my FortiManager and Meraki devices

AI: I'll collect the network topology from your configured APIs.
[Executes collect_topology tool]
```

### Generate Network Diagram

```
User: Create a hierarchical diagram showing:
- FortiGate firewalls at the top
- Meraki switches in the middle  
- Meraki access points at the bottom
- Use appropriate vendor icons
- Label devices with hostnames and IPs

AI: I'll generate a hierarchical network diagram with your devices organized by type.
[Executes generate_drawio_diagram tool with layout=hierarchical, group_by=type]
```

### Custom Layout

```
User: Create a circular layout of all devices, grouped by site, with color-coding by device status

AI: I'll arrange your devices in a circular pattern grouped by site location.
[Executes generate_drawio_diagram tool with layout=circular, group_by=site, color_code=true]
```

### Export and Integration

```
User: Export the topology as JSON and create a CSV report of all devices

AI: I'll export the complete topology data in both JSON and CSV formats.
[Executes export_topology_json tool with format=json and format=csv]
```

## MCP Tools

### collect_topology
Collect network topology from FortiManager and Meraki APIs.

**Parameters:**
- `refresh` (boolean): Force refresh of cached data
- `device_types` (array): Filter by device types

**Returns:** Complete topology with devices and links

### generate_drawio_diagram
Generate DrawIO diagram from collected topology data.

**Parameters:**
- `layout` (string): hierarchical, circular, force-directed, custom
- `group_by` (string): site, type, vendor, none
- `show_details` (boolean): Include device details in labels
- `color_code` (boolean): Color code devices by type/status

**Returns:** DrawIO XML that can be imported directly

### get_topology_summary
Get summary statistics of the network topology.

**Returns:** Device counts, link counts, sites, and health metrics

### export_topology_json
Export topology data in various formats.

**Parameters:**
- `include_health` (boolean): Include health metrics
- `format` (string): json, csv, yaml

**Returns:** Exported topology data

## Resources

- `topology://current` - Latest collected network topology
- `topology://summary` - Topology summary statistics

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FortiManager   │    │  Meraki Dashboard │    │   DrawIO App    │
│      API         │    │       API         │    │   (Browser)     │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          │                      │                       │
          └──────────┬───────────┴───────────────────────┘
                     │
          ┌─────────────────────────────┐
          │  DrawIO MCP Server          │
          │  (Python)                   │
          │                             │
          │  • Topology Collection      │
          │  • Diagram Generation       │
          │  • Data Transformation      │
          └─────────────┬───────────────┘
                        │
          ┌─────────────────────────────┐
          │  MCP Client (Claude, etc.)  │
          │                             │
          │  • Natural Language         │
          │  • Tool Orchestration       │
          │  • Context Management       │
          └─────────────────────────────┘
```

## Advanced Features

### Real-time Topology Monitoring

Enable continuous topology updates:

```python
# In your monitoring script
import asyncio
from mcp_servers.drawio_fortinet_meraki import DrawIOMCPServer

async def monitor_topology():
    server = DrawIOMCPServer()
    await server.initialize_topology_collector()
    
    while True:
        # Collect latest topology
        topology = await server.topology_collector.get_complete_topology()
        
        # Check for changes
        if topology_changed(topology, previous_topology):
            # Trigger diagram update
            await server.generate_drawio_diagram({
                'layout': 'hierarchical',
                'group_by': 'type'
            })
        
        await asyncio.sleep(300)  # Check every 5 minutes
```

### CI/CD Integration

Add to your GitLab CI pipeline:

```yaml
topology-diagram:
  stage: documentation
  script:
    - python -c "
import asyncio
from mcp_servers.drawio_fortinet_meraki import DrawIOMCPServer

async def generate_docs():
    server = DrawIOMCPServer()
    await server.initialize_topology_collector()
    result = await server.collect_topology({'refresh': True})
    diagram = await server.generate_drawio_diagram({'layout': 'hierarchical'})
    
    with open('network-topology.drawio', 'w') as f:
        f.write(diagram.content[2].text)

asyncio.run(generate_docs())
"
  artifacts:
    paths:
      - network-topology.drawio
```

### ChatOps Integration

Slack bot example:

```python
from slack_sdk import WebClient
from mcp_servers.drawio_fortinet_meraki import DrawIOMCPServer

async def handle_topology_command(client, channel, command):
    server = DrawIOMCPServer()
    await server.initialize_topology_collector()
    
    if command == '/topology-generate':
        result = await server.generate_drawio_diagram({
            'layout': 'hierarchical',
            'group_by': 'site'
        })
        
        # Upload diagram to Slack
        client.files_upload_v2(
            channel=channel,
            title='Network Topology',
            content=result.content[2].text,
            filename='topology.drawio'
        )
```

## Troubleshooting

### Common Issues

1. **API Authentication Errors**
   - Verify FortiManager credentials and connectivity
   - Check Meraki API key permissions
   - Ensure firewall allows API access

2. **DrawIO Connection Issues**
   - Install DrawIO MCP browser extension
   - Check WebSocket connection (port 3333)
   - Restart DrawIO browser tab

3. **MCP Server Not Starting**
   - Check Python version (3.8+ required)
   - Install all dependencies: `pip install -r requirements.txt`
   - Verify PYTHONPATH configuration

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python mcp_server.py
```

### Performance Optimization

For large networks (500+ devices):

1. Use device type filtering
2. Enable topology caching
3. Implement incremental updates
4. Use hierarchical layouts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: [Wiki](https://github.com/enhanced-network-api/drawio-fortinet-meraki-mcp/wiki)
- Issues: [GitHub Issues](https://github.com/enhanced-network-api/drawio-fortinet-meraki-mcp/issues)
- Discussions: [GitHub Discussions](https://github.com/enhanced-network-api/drawio-fortinet-meraki-mcp/discussions)

## Roadmap

- [ ] Support for additional vendors (Cisco, Juniper, Aruba)
- [ ] Advanced layout algorithms (force-directed, tree)
- [ ] Real-time bandwidth visualization
- [ ] Integration with network monitoring tools
- [ ] Template-based diagram generation
- [ ] Multi-tenant support
- [ ] GraphQL API support
