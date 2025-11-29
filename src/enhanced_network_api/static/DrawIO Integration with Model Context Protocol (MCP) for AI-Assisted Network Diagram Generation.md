DrawIO Integration with Model Context Protocol (MCP) for AI-Assisted Network Diagram Generation
The integration of Draw.io (Diagrams.net) with Model Context Protocol (MCP) represents a breakthrough in AI-assisted network topology visualization. This integration enables Large Language Models (LLMs) to programmatically create, modify, and analyze network diagrams through natural language commands, dramatically accelerating the documentation process for FortiManager and Meraki-based networks.

What is Model Context Protocol (MCP)?
Model Context Protocol (MCP) is an open standard developed by Anthropic that enables seamless integration between Large Language Models and external data sources, tools, and systems. MCP provides a lightweight, capability-oriented RPC layer that addresses the challenge of safely exposing real-time actions and data to AI systems.​

Core Architecture:

MCP follows a client-server architecture with three foundational components:​

MCP Clients (AI applications like Claude Desktop, Amazon Q CLI, VS Code extensions)

MCP Servers (Expose specific capabilities to clients via standard protocol)

Local Data Sources (Files, databases, APIs that servers can access)

Transport Mechanisms:

Stdio Transport: Uses standard input/output streams for local process communication between client and server on the same machine​

HTTP/WebSocket Transport: Enables remote server communication with standard authentication (OAuth, bearer tokens, API keys)​​

Key Capabilities:

Tools: AI-callable functions that perform specific actions (e.g., create diagram, query API, execute command)​

Resources: Contextual data that AI can access (e.g., device configurations, topology data)​

Prompts: Reusable templates for common workflows​

Sampling: Ability for servers to request LLM inference on behalf of systems​

DrawIO MCP Server Implementation
Project Overview:

The Draw.io MCP Server (drawio-mcp-server) is an open-source implementation that brings programmatic diagramming capabilities to AI agentic systems. Created by László Gazo and available on GitHub, it has gained significant traction with 278+ stars and active community contributions.​

Architecture Components:

MCP Server (Node.js-based, v20+)

Listens on localhost port 3333 by default​

Implements standard MCP protocol via JSON-RPC 2.0​

Manages bidirectional communication with Draw.io browser instance​

Browser Extension (Chrome/Firefox)

Bridges communication between Draw.io web app and MCP server​

Uses WebSocket protocol for real-time updates​

Displays connection status in extension popup​

MCP Client (AI interface)

Claude Desktop, VS Code extensions, Windsurf, Zed, Cursor, cursor-agent, gemini, copilot cli, claude code or register as Docker MCP​

Sends natural language requests to LLM

LLM translates requests into MCP tool calls​

Installation and Setup:

bash
undefined
Published
5 seconds ago
Install via npm
npx -y drawio-mcp-server

Or via pnpm
pnpm dlx drawio-mcp-server

text

**Configuration for AI Clients**

{
"mcpServers": {
"drawio": {
"command": "npx",
"args": ["-y", "drawio-mcp-server"]
}
}
}

text

### MCP Tools for Network Diagram Creation

The Draw.io MCP server provides comprehensive tools organized into two categories:[1][2]

#### Diagram Inspection Tools

**1. `get-selected-cell`**
- Retrieves currently selected diagram element with all attributes
- Returns: JSON object with cell ID, geometry, style, value, connections
- Use case: Understanding existing diagram structure for modifications[1]

**2. `get-shape-categories`**
- Lists all available shape libraries (AWS, Azure, Cisco, networking icons)
- Returns: Array of category objects with IDs and names
- Use case: Discovering available icon sets for network devices[1]

**3. `get-shapes-in-category`**
- Parameters: `category_id`
- Returns: All shapes within specified category with properties
- Use case: Finding specific network device icons (routers, switches, firewalls)[1]

**4. `get-shape-by-name`**
- Parameters: `shape_name`
- Returns: Specific shape with category and style information
- Use case: Locating FortiGate, Meraki, or generic networking icons[1]

**5. `list-paged-model`**
- Retrieves paginated view of all diagram cells (vertices and edges)
- Supports filtering with boolean logic on multiple criteria
- Returns: Sanitized model data without circular dependencies
- Use case: Programmatic inspection of entire network topology structure[2][1]

#### Diagram Modification Tools

**1. `add-rectangle`**
- Creates basic shape with customizable properties
- Parameters: `x`, `y`, `width`, `height`, `text`, `style`
- Style syntax: Draw.io format (e.g., `fillColor=#ffffff;strokeColor=#000000`)
- Use case: Creating labeled boxes for network segments or zones[2]

**2. `add-edge`**
- Creates connections between network devices
- Parameters: `source_id`, `target_id`, `text` (label), `style`
- Use case: Drawing links between routers, switches, and access points with interface labels[2][1]

**3. `delete-cell-by-id`**
- Parameters: `cell_id`
- Removes specified diagram element
- Use case: Removing outdated devices or connections from topology[2]

**4. `add-cell-of-shape`**
- Creates cell from library shape (network device icons)
- Parameters: `shape_name`, `x`, `y`, `width`, `height`, `text`, `style`
- Use case: Adding FortiGate firewall, Meraki AP, or Cisco router icons with proper positioning[1][2]

### Network Topology Automation Workflow

**End-to-End Process for FortiManager/Meraki Integration:**

**Phase 1: Data Collection from APIs**

mcp.pizza favicon
github.com favicon
2 sources
Pseudo-code example
import requests

Query FortiManager API
fortimanager_data = get_fortimanager_devices()

Returns: device list, interfaces, connections, locations
Query Meraki API
meraki_data = get_meraki_topology()

Returns: networks, devices, L2/L3 links, client counts
text

**Phase 2: Natural Language Request to AI Agent**

User interacts with Claude Desktop, Amazon Q CLI, or similar MCP client:

"Create a network diagram showing:

All FortiGate firewalls from site A and B

Meraki access points with client counts

WAN connections between sites

Use appropriate vendor icons

Label all interfaces and VLANs"

text

**Phase 3: AI Tool Orchestration**

The LLM breaks down the request into MCP tool calls:

1. **Discovery Phase**:
get-shape-categories()
get-shapes-in-category(category_id: "cisco_network")
get-shape-by-name(shape_name: "FortiGate Firewall")
get-shape-by-name(shape_name: "Meraki AP")

text

2. **Device Placement Phase**:
add-cell-of-shape(
shape_name: "FortiGate Firewall",
x: 100, y: 100,
text: "FGT-Site-A\n192.168.1.1",
style: "..."
)

add-cell-of-shape(
shape_name: "Meraki MR Access Point",
x: 300, y: 200,
text: "AP-Floor1\n52 clients",
style: "..."
)

text

3. **Connection Phase**:
add-edge(
source_id: "fortigate-1",
target_id: "meraki-ap-1",
text: "Trunk\nVLAN 10,20,30",
style: "endArrow=classic;..."
)

text

**Phase 4: Iterative Refinement**

User can request modifications in natural language:

"Move all APs to the right side and group by floor"
"Change the firewall connection to show redundant links"
"Add a legend showing device types and connection speeds"

text

The AI agent uses `list-paged-model` to understand current layout, then applies modifications using `delete-cell-by-id` and repositioning commands.

### Real-World Implementation: pyATS MCP Integration

**John Capobianco's Breakthrough Integration**

Network engineer John Capobianco at Selector.ai demonstrated a production-ready implementation combining Draw.io MCP with Cisco pyATS for automated network topology generation.[1][2][3][4]

**Architecture Overview:**

Cisco Devices (Live Network)
↓ (CLI/API)
pyATS (Network Test Framework)
↓ (WebSocket/HTTP)
MCP Server (Custom Implementation)
↓ (MCP Protocol)
LLM Agent (GPT-4/Claude)
↓ (MCP Tool Calls)
Draw.io Browser + Extension
↓ (Visual Output)
Network Topology Diagram

text

**Key Capabilities Demonstrated:**

1. **Automatic Topology Discovery**:[4][1]
   - pyATS connects to network devices via SSH/NETCONF
   - Collects CDP/LLDP neighbor information
   - Parses interface configurations and VLAN data
   - Streams real-time data to MCP server via WebSocket

2. **AI-Driven Diagram Generation**:[1]
   - LLM interprets device data and relationships
   - Determines optimal diagram layout
   - Selects appropriate shapes from Draw.io libraries
   - Generates labeled connections with interface names

3. **Bidirectional Workflow**:[1]
   - **Data → Diagram**: Automatically draw topology from live network state
   - **Diagram → Config**: Parse Draw.io diagrams to generate device configurations
   - Enables "visual NetDevOps" where diagrams represent intent

**Tool Functions Implemented:**

- `get-all-cells-detailed`: Extract complete topology structure from Draw.io
- `get-edge-labels`: Parse interface labels (e.g., "Eth0/2", "Trunk", "VLAN30")
- Interface parsing translates labels into real IOS configuration commands[1]

**Use Cases:**

- **Real-time topology views during CI/CD pipelines**[4]
- **Incident response**: Generate live topology showing affected paths
- **ChatOps integration**: Request diagrams via Slack/Teams commands
- **Multi-agent workflows**: Chain with LangGraph for complex automation[4]

**Video Demonstrations:**

Two detailed videos showcase the capabilities:
- "Automated Network Diagrams with DrawIO and pyATS MCP" (20 minutes)[4]
- "Fully Configuring a Network from DrawIO Diagram with pyATS MCP" (46 minutes)[1]

### Network-Specific MCP Applications

**IETF Draft: MCP for Network Troubleshooting**

An emerging IETF draft (`draft-zeng-mcp-troubleshooting-00`) describes using MCP for intent-based network management:[5]

**Proposed Architecture:**

- **Network Devices as MCP Servers**: Routers, switches, and firewalls expose MCP tools
- **Network Controllers as MCP Clients**: SDN controllers and management systems consume MCP
- **LLM Integration**: AI agents reason about device logs, configurations, and telemetry[5]

**MCP Tools for Network Devices:**

Example tool schema for network diagnostics:[5]

{
"name": "ping",
"description": "Execute ping test to target IP",
"inputSchema": {
"type": "object",
"properties": {
"target": {"type": "string"},
"count": {"type": "integer"}
}
}
}

text

**Prompts for Troubleshooting Workflows:**

Vendors can encode golden troubleshooting workflows as MCP prompts:

Prompt: "Diagnose interface {{interface}} high error rate"
Variables: interface name from user
Actions:

show interface {{interface}}

show logging | include {{interface}}

show controllers {{interface}}

Analyze error patterns with LLM

text

**Benefits for FortiManager/Meraki Environments:**

- **Conversational troubleshooting**: "Why is VLAN 30 not passing traffic?"
- **Configuration validation**: "Check if all APs have consistent SSIDs"
- **Closed-loop remediation**: AI detects issue, proposes fix, applies after approval[5]

### Commercial MCP Server Examples

**AWS Diagram MCP Server**

AWS Labs developed an MCP server for generating AWS architecture diagrams using the Python `diagrams` package.[6][7][8]

**Key Features:**

- Supports AWS, sequence, flow, and class diagrams
- Uses Python DSL for diagram generation
- Integrates with Amazon Q CLI for natural language diagramming
- Code scanning for secure diagram generation[6]

**Network Relevance:**

While AWS-focused, the pattern applies to network diagrams:

youtube.com favicon
linkedin.com favicon
reddit.com favicon
8 sources
Network topology equivalent
from diagrams import Diagram
from diagrams.cisco.routing import Router
from diagrams.cisco.switching import Switch

with Diagram("Network Topology", show=False):
router = Router("Core Router")
switch1 = Switch("Access Switch 1")
switch2 = Switch("Access Switch 2")

text
router >> switch1
router >> switch2
text

Amazon Q CLI can generate this code from natural language: "Create a diagram with one core router connected to two access switches".[1]

**ToDiagram MCP Server**

ToDiagram offers a commercial MCP server for generating interactive diagrams from structured data:[2]

- Supports JSON, YAML, XML, CSV, and Mermaid inputs
- Outputs editable, shareable diagrams
- Integrates with AI copilots and CI/CD workflows
- Secure with API key authentication[2]

**Network Application:**

Export FortiManager/Meraki data as JSON, send to MCP server, receive interactive diagram.

### Integration Strategies for FortiManager and Meraki

**Strategy 1: Direct API → MCP → Draw.io**

FortiManager/Meraki APIs
↓ (Python script)
JSON Topology Data
↓ (MCP client request)
LLM with Draw.io MCP Server
↓ (MCP tool calls)
Draw.io Network Diagram

text

**Implementation Steps:**

1. **Data Collection Script**:
Collect topology data
devices = get_fortimanager_devices()
links = get_meraki_l2_topology()

Format for LLM context
topology_description = format_topology_for_llm(devices, links)

text

2. **Natural Language Request**:
User → Claude Desktop:
"Here's my network topology data: {topology_description}
Create a hierarchical diagram showing:
- Core FortiGate cluster at top
- Distribution switches in middle
- Meraki APs at bottom grouped by building
- Use red lines for 10G links, blue for 1G"

text

3. **AI Orchestration**:
- LLM parses topology data
- Plans diagram layout (hierarchical, force-directed, or custom)
- Executes MCP tool calls to Draw.io server
- Creates professional network diagram

**Strategy 2: pyATS-Style Real-Time Polling**

Implement continuous topology monitoring similar to Capobianco's pyATS integration:[3][4]

aws.amazon.com favicon
youtube.com favicon
4 sources
Pseudo-code
while True:
# Poll APIs every 5 minutes
current_state = {
'fortimanager': poll_fortimanager_api(),
'meraki': poll_meraki_api()
}

text
# Detect changes
if topology_changed(current_state, previous_state):
    # Trigger diagram update via MCP
    update_diagram_via_mcp(current_state)

sleep(300)
text

**Benefits:**

- Live topology views during network changes
- Automated documentation updates
- Incident response visualization (show affected segments)[1]

**Strategy 3: CI/CD Integration**

Embed topology diagram generation in deployment pipelines:

youtube.com favicon
1 source
GitLab CI example
topology-diagram:
stage: documentation
script:
- python collect_topology_data.py
- mcp-client generate-diagram --input topology.json --output diagram.drawio
artifacts:
paths:
- network-topology.drawio
- network-topology.png

text

**Strategy 4: ChatOps Integration**

Enable Slack/Teams commands for on-demand diagrams:[1]

/network-diagram site=headquarters layer=physical
/network-diagram show-vpn-tunnels between=site-a and site-b
/network-diagram highlight-path from=10.1.1.0/24 to=10.5.5.0/24

text

Bot triggers MCP workflow, returns diagram link in chat.

### Advanced Features and Capabilities

**Multi-Layer Visualization**

Create separate diagram layers for different network aspects:

- **Physical Layer**: Devices, connections, interface labels
- **VLAN Layer**: Logical segmentation, trunk ports
- **Security Layer**: Firewall zones, ACLs, security policies
- **Application Layer**: Services, load balancers, application paths

MCP enables programmatic layer management through multiple diagram pages.

**Style Customization**

Apply consistent styling based on device state or metrics:

youtube.com favicon
1 source
Pseudo-code for dynamic styling
for device in devices:
if device.cpu_usage > 80:
style = "fillColor=#ff0000;fontColor=#ffffff" # Red
elif device.cpu_usage > 50:
style = "fillColor=#ffa500;fontColor=#000000" # Orange
else:
style = "fillColor=#00ff00;fontColor=#000000" # Green

text
add_cell_of_shape(
    shape_name=device.type,
    text=f"{device.name}\nCPU: {device.cpu_usage}%",
    style=style
)
text

**Diff Visualization**

Compare topology snapshots and highlight changes:

1. Generate diagram from previous state (green devices/links)
2. Generate diagram from current state (blue devices/links)
3. Highlight differences (red for removed, yellow for modified)

Enables "before/after" views for change management.

**Interactive Documentation**

Embed metadata in diagram cells for interactive documentation:

- Click device → Show configuration
- Click link → Show bandwidth utilization graph
- Hover interface → Display traffic statistics

While Draw.io natively supports links, MCP enables programmatic metadata injection.

### Performance and Scalability

**Handling Large Topologies:**

For enterprise networks with 500+ devices:

1. **Hierarchical Decomposition**:
   - Create separate diagrams per site/region
   - Generate overview diagram with site-to-site links
   - Use hyperlinks between diagrams

2. **Filtering and Pagination**:
   - Use `list-paged-model` with filters for targeted updates
   - Process topology in chunks to avoid overwhelming LLM context

3. **Incremental Updates**:
   - Track previous diagram state
   - Only modify changed elements using `delete-cell-by-id` and `add-cell-of-shape`
   - Avoid regenerating entire diagram

**WebSocket for Real-Time Updates:**

The HTTP/WebSocket transport enables streaming updates:[1][2]

// MCP server receives continuous stream
websocket.on('topology_update', (data) => {
// Process delta
const changes = compute_changes(data);

text
// Apply to diagram
changes.forEach(change => {
    mcp_client.call_tool('update-cell', change);
});
});

text

### Security Considerations

**Authentication and Authorization:**

- MCP servers should implement OAuth or API key authentication[3]
- Draw.io extension communicates over localhost WebSocket (port 3333)[1]
- Network API credentials stored securely (environment variables, secrets manager)

**Code Execution Risks:**

- LLM-generated MCP tool calls should be validated
- AWS Diagram MCP Server includes code scanning for security[4]
- Implement approval workflows for production diagram updates

**Data Privacy:**

- Topology data may contain sensitive IP addressing schemes
- Consider on-premises MCP server deployment for air-gapped networks
- Audit LLM API requests to ensure no sensitive data leakage

### Ecosystem and Future Directions

**MCP Standardization Efforts:**

- Anthropic maintains official MCP specification at modelcontextprotocol.io[3]
- IETF exploring network-specific MCP applications[5]
- Growing ecosystem of MCP servers (278+ GitHub stars for Draw.io MCP)[6]

**Agentic AI for Networks:**

The broader trend toward "agentic AI" in networking:[7][8][9][10]

- **Autonomous network management**: AI agents that monitor, diagnose, and remediate without human intervention
- **Multi-agent orchestration**: LangGraph, AutoGen enabling complex workflows
- **Natural language interfaces**: Engineers describe intent, AI handles implementation

MCP provides the "protocol glue" enabling AI agents to interact with disparate network systems.[8]

**Integration with Network Automation Frameworks:**

- **Ansible + MCP**: Playbooks trigger diagram updates
- **Terraform + MCP**: Infrastructure-as-Code generates corresponding diagrams
- **Nornir + MCP**: Python automation framework with MCP tool integration[7]

**Vision for Network Engineers:**

The future workflow:[9][10]

Engineer: "Show me why VLAN 100 can't reach the internet"

AI Agent (via MCP):

Queries network devices for routing tables

Checks firewall policies via FortiManager API

Validates Meraki VLAN configuration

Generates topology diagram highlighting the path

Identifies misconfigured NAT rule

Proposes fix and applies after approval

Updates documentation diagram automatically

text

This shifts network engineering from manual, repetitive tasks to strategic, intent-based interactions.

### Getting Started: Quick Implementation

**Minimal Setup for FortiManager/Meraki Topology Automation:**

1. **Install Prerequisites**:
Node.js v20+
curl -fsSL https://nodejs.org/dist/v20.x/node-v20.x.tar.gz | tar xz

Draw.io MCP Server
npm install -g drawio-mcp-server

Python libraries
pip install pyFortiManagerAPI meraki

text

2. **Configure Claude Desktop**:
{
"mcpServers": {
"drawio": {
"command": "npx",
"args": ["-y", "drawio-mcp-server"]
}
}
}

text

3. **Install Browser Extension**:
- Chrome: [Draw.io MCP Extension](https://chromewebstore.google.com/detail/drawio-mcp-extension/okdbbjbbccdhhfaefmcmekalmmdjjide)[1]
- Firefox: [Draw.io MCP Extension](https://addons.mozilla.org/firefox/addon/drawio-mcp-extension/)[11]

4. **Open Draw.io and Connect**:
- Navigate to https://app.diagrams.net/
- Extension should show "Connected" status
- Open Claude Desktop or compatible MCP client

5. **Test Basic Functionality**:
User → Claude:
"In Draw.io, create a simple network with:
- One router at coordinates (200, 100)
- Two switches at (100, 300) and (300, 300)
- Connect router to both switches
- Label the router 'Core-Router-1'"

text

6. **Integrate API Data**:
collect_topology.py
from pyFortiManagerAPI import FortiManager
import meraki

Collect data
fm = FortiManager(host='fmg.example.com', username='api', password='***')
fm_devices = fm.get_devices()

meraki_dashboard = meraki.DashboardAPI(api_key='***')
meraki_devices = meraki_dashboard.organizations.getOrganizationDevices(org_id)

Format for Claude
context = format_for_llm(fm_devices, meraki_devices)
print(context)

text

7. **Generate Diagram**:
User → Claude:
"Using this network data: {context}
Create a professional topology diagram in Draw.io showing:
- FortiGate firewalls in the top row
- Meraki switches in the middle row
- Meraki APs in the bottom row grouped by building
- Use Fortinet and Meraki icons from the shape libraries
- Label all devices with hostname and management IP
- Show trunk links between firewalls and switches"

text

### Key Takeaways

**Draw.io MCP Integration Benefits:**

1. **Natural Language Diagramming**: Describe topology intent, AI creates diagram
2. **API-Driven Automation**: FortiManager/Meraki data → automatic diagram generation
3. **Bidirectional Workflow**: Diagrams ↔ Configuration (visual NetDevOps)
4. **Real-Time Updates**: Live topology views during network changes
5. **Standardized Protocol**: MCP enables tool interoperability across vendors

**Comparison to Traditional Methods:**

| Aspect | Manual Visio | Python Scripts | MCP + Draw.io |
|--------|-------------|----------------|---------------|
| **Speed** | Hours | Minutes | Seconds |
| **Skill Required** | Design + Network | Programming | Natural Language |
| **Real-Time Updates** | Manual | Scheduled | Continuous |
| **Flexibility** | High (manual) | Medium (coding) | High (conversational) |
| **Integration** | Low | Medium | High (standard protocol) |

**When to Use MCP + Draw.io:**

- ✅ Rapid topology documentation from API data
- ✅ AI-assisted diagram refinement (layout, styling, grouping)
- ✅ ChatOps and CI/CD integration for on-demand diagrams
- ✅ Multi-agent workflows requiring diagram generation
- ✅ Educational environments teaching network design

**When Traditional Methods May Be Better:**

- Manual artistic control needed (marketing materials)
- Legacy Visio templates with complex macros
- Air-gapped environments without LLM access
- Highly specialized diagram types not supported by Draw.io libraries

The Draw.io MCP integration represents a paradigm shift in network documentation, enabling natural language interactions with diagramming tools powered by FortiManager and Meraki APIs. As the MCP ecosystem matures, expect deeper integrations with network automation frameworks, enhanced security features, and broader adoption across the networking industry.
chromewebstore.google.com favicon
youtube.com favicon
modelcontextprotocol.io favicon
11 sources
Discover more