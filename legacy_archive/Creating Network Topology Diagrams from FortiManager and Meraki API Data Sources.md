Home
Home
Discover
Spaces
Finance
Account

research how to create network topology using Fortimanager AP and Meraki API  as a data sources for Visio drawing. Also research other methods to create network maps  Fortimanager AP and Meraki API  as a data sources for other drawing tools including 2D and 3D tools

I have gathered comprehensive information about creating network topology diagrams using FortiManager and Meraki APIs as data sources. Let me now compile this research into a detailed report.
Creating Network Topology Diagrams from FortiManager and Meraki API Data Sources

Network topology visualization is essential for understanding, documenting, and troubleshooting modern enterprise networks. Both FortiManager and Meraki provide robust APIs that can be leveraged to automatically generate network diagrams, eliminating manual documentation processes and ensuring accuracy.
FortiManager API as a Data Source

FortiManager provides a comprehensive JSON-RPC API that enables automation and DevOps integration for managing Fortinet Security Fabric deployments. The API offers complete management and monitoring capabilities, allowing users to automate tasks such as configuring devices, creating backups, and retrieving device information.

​

Key Topology Discovery Features:

FortiManager includes built-in topology views that can be accessed programmatically:

​

    Physical Topology: Displays devices in the Security Fabric and their connections, organized by traffic, device count, operating system, or hardware vendor

​

Logical Topology: Shows network interfaces (logical or physical) used to connect devices in the Security Fabric

​

Layer 2 and Layer 3 Discovery: FortiManager discovers network topology at both layers using SNMP (RFC 1213) to obtain network interface IP addresses and masks

    ​

Python Libraries for FortiManager:

Several Python libraries facilitate interaction with FortiManager's API:

    pyFortiManagerAPI: A Python wrapper for the FortiManager JSON RPC API with comprehensive documentation

​

pyfmg: Represents base components of the FortiManager JSON-RPC interface, maintained by Fortinet's CSE Team

​

BESTSELLER/pyfortimanager: Provides API client functionality for FortiManager v7.2.x and above

    ​

These libraries support operations like retrieving device information, managing ADOMs, and querying topology data.

​
Meraki API as a Data Source

The Cisco Meraki Dashboard API is a modern REST API based on the OpenAPI specification that provides extensive network management capabilities.

​

Topology Discovery Capabilities:

Meraki offers native topology visualization features accessible via API:

​

    Layer 2 Topology: Displays physical links and their traffic statistics, including negotiated speed, usage, and connected clients

​

Layer 3 Topology: Visualizes Layer 3 connectivity, showing subnets, node IPs, and static routes

​

Network Topology Link Layer API: Returns LLDP and CDP information for all discovered devices and connections in a network

    ​

Python Integration:

    Meraki Dashboard API Python Library: Official library providing all current Meraki Dashboard API calls

​

meraki-sdk: Python client library for programmatic network management

    ​

The Meraki API can be used to retrieve device information, network topology, and create automation scripts.

​
Creating Visio Diagrams from API Data

Microsoft Visio supports automation through various methods for creating network diagrams from FortiManager and Meraki data sources.

Approach 1: Text File Import

Visio can import structured text files to automatically generate diagrams:

​

    Define nodes with shape names, master types, and labels

    Document connections between nodes in a specific format

    Import the file into Visio for automatic diagramming

Approach 2: External Data Linking

Visio Professional and Premium include features for linking external data to network shapes:

​

    Use the Data Link wizard to automatically link external data to network shapes

    Import data from Excel, databases, or API responses

    Update diagrams dynamically as source data changes

Approach 3: PowerShell/Python Automation

Visio can be automated using COM objects via PowerShell or Python:

​

    Create new Visio documents programmatically

    Add shapes and connections based on API data

    Save diagrams in various formats (VSD, VSDX, PDF)

Implementation Workflow:

    Query FortiManager or Meraki API using Python libraries

    Parse topology data (devices, connections, interfaces)

    Transform data into Visio-compatible format

    Generate Visio diagram using COM automation or text file import

    Apply automatic layout algorithms for optimal visualization

    ​

Alternative 2D Drawing Tools and Methods

Beyond Visio, several powerful alternatives exist for creating network topology diagrams from API data.
DrawIO (Diagrams.net)

DrawIO Network Plot Library: A Python library specifically designed for programmatically creating DrawIO network topology diagrams.

​

Features:

    Programmatic diagram creation from code

    Customizable nodes with device type, hostname, model, and role

    Labeled links showing interface names and IP addresses

    Uses built-in Cisco icon sets for professional appearance

    Generates XML files compatible with DrawIO web and desktop versions

    ​

Implementation Example:

Python scripts can use the drawio_network_plot library to:

    Gather device data from FortiManager/Meraki APIs

    Use Netmiko or similar tools to collect CDP/LLDP information

    Generate DrawIO XML files automatically

    ​

Recent innovations include DrawIO integration with Model Context Protocol (MCP) for AI-assisted diagram generation from network data.

​
yEd Graph Editor

yEd is a free desktop application for creating and editing network diagrams that supports the GraphML format.

​

N2G (Need To Graph) Library:

N2G is a Python library designed to generate network diagrams in yEd graphml or DrawIO formats:

​

    Creates diagrams from network device data

    Supports CDP and LLDP protocol information

    Includes automatic layout algorithms

    Generates professional network topology visualizations

​

    ​

Integration with Network Data:

python
from N2G import yed_diagram
diagram = yed_diagram()
diagram.add_node('Router1', top_label='Core', bottom_label='ASR1004')
diagram.add_node('Router2', top_label='Edge', bottom_label='MX240')
diagram.add_link('Router1', 'Router2', src_label='Gi0/1', trgt_label='ge-0/1/2')
diagram.layout(algo="kk")
diagram.dump_file(filename="topology.graphml", folder="./Output/")

The yEd Python library (pyyed) provides simple interfaces for exporting networks to yEd format.

​
NetBrain

NetBrain is an enterprise-grade network automation platform with advanced topology mapping capabilities.

​

Key Features:

    Automatic network discovery via device CLI, API, or SNMP

    Dynamic maps providing real-time network topology and live traffic paths

    Multi-vendor support including FortiManager and Meraki integration

​

Integration with existing Visio diagrams

​

Automated network documentation that updates with topology changes
​

    ​

Data Collection Methods:

    SNMP walks against LLDP and CDP MIBs

    Direct API integration with Fabric networks

    VMware infrastructure topology data

    ​

NetBrain creates a four-layered digital twin model: device layer, topology layer, control plane layer, and intent layer.

​
SolarWinds Network Topology Mapper

Network Topology Mapper (NTM) automatically discovers and maps network topology using multiple discovery methods:

​

    ICMP, SNMP, WMI, CDP, VMware, Microsoft Hyper-V discovery

    Multi-level network mapping (Layer 2 and Layer 3)

    Export to Microsoft Visio, PDF, and PNG formats

    Scheduled map updates and exports

    ​

Graphviz

Graphviz is an open-source graph visualization software that represents structural information as diagrams.

​

Python Integration:

    PyGraphviz: Python interface to Graphviz

    pydot: Pure Python interface to Graphviz's dot language

    Supports automatic layout algorithms (dot, neato, fdp, circo)

    ​

Network Diagram Creation:

Graphviz can create updatable network diagrams by:

    Writing network topology in DOT language

    Specifying node positions and connections

    Using layout engines like neato for network-style layouts

    ​

Python scripts can generate DOT files from FortiManager/Meraki API data and render them as network diagrams.

​
3D Visualization Tools and Methods

3D network visualization provides enhanced spatial understanding of complex network topologies, particularly useful for large-scale or hierarchical networks.
Three.js

Three.js is a JavaScript library for creating 3D graphics in web browsers.

​

3D Force Graph Library: A web component built with Three.js for representing graph data structures in 3D space using force-directed layouts.

​

Features:

    Interactive 3D network visualization

    Force-directed layout algorithms

    WebGL rendering for performance

    Support for large datasets

    Pan, zoom, and rotation controls

​

    ​

Network Topology Applications:

    Visualize hierarchical network structures

    Display network clusters and communities

    Interactive node selection and highlighting

    Real-time topology updates

​

    ​

Implementation Approach:

While Three.js doesn't provide built-in network algorithms, developers can:

    Retrieve topology data from FortiManager/Meraki APIs

    Process data into nodes and edges format

    Implement force-directed layout algorithms

    Render using Three.js 3D primitives

    ​

Libraries like 3d-force-graph simplify this process by providing ready-made 3D network visualization components.

​
Plotly 3D Network Graphs

Plotly is a Python library for creating interactive visualizations, including 3D network graphs.

​

3D Network Visualization Capabilities:

    Interactive 3D scatter plots for nodes

    Line traces for edges

    Color coding by communities or metrics

    Hover information and tooltips

    Integration with NetworkX for graph analysis

    ​

Implementation Example:

python
import plotly.graph_objects as go
import networkx as nx

# Create or load graph
G = nx.random_geometric_graph(200, 0.125)

# Generate 3D spring layout
pos = nx.spring_layout(G, dim=3)

# Extract coordinates
x_nodes = [pos[i][0] for i in G.nodes()]
y_nodes = [pos[i][1] for i in G.nodes()]
z_nodes = [pos[i][2] for i in G.nodes()]

# Create 3D scatter plot
fig = go.Figure(data=[edge_trace, node_trace])
fig.show()

Plotly's 3D network graphs are fully interactive, allowing rotation, zoom, and hover interactions.

​
D3.js with 3D Extensions

D3.js is a powerful JavaScript library for data-driven visualizations.

​

3D Network Visualization:

    Force-directed graph layouts

    WebGL rendering for performance

    Interactive node manipulation

    Custom styling and animations

    ​

D3.js can be combined with Three.js for enhanced 3D capabilities, leveraging D3's data manipulation with Three.js's 3D rendering.

​
Cytoscape.js

Cytoscape.js is an open-source JavaScript graph theory library designed for visualization and analysis.

​

Key Features:

    Optimized for large datasets

    Rich styling options

    Custom renderers and layouts

    Plugin architecture for extensibility

    Support for 2D and 3D visualizations

    ​

Network Visualization Applications:

    Biological networks

    Social network analysis

    Transportation networks

    Enterprise network topologies

    ​

Cytoscape.js integrates well with other JavaScript libraries and can consume data from REST APIs.

​
nuVML (Virtual Modeling Lab)

nuVML is a specialized 3D network visualization tool designed for network design and simulation.

​

Features:

    2D and 3D views of network topology

    Real-time visualization of routing protocols and traffic flow

    Multi-vendor environment support

    Integration with Cisco VIRL, CML, and GNS3

    Support for production network monitoring

    ​

Use Cases:

    Network design and capacity planning

    Proof of concept testing

    Change validation and "what-if" scenarios

    Training and certification preparation

    ​

GNS3 (Graphical Network Simulator-3)

GNS3 is a network software emulator that includes visualization capabilities.

​

Visualization Features:

    Graphical network topology modeling

    Simulation of complex networks

    Support for unlimited network components (routers, switches, firewalls)

    Various link types (Ethernet, GigaEthernet, ATM, Serial)

    ​

While primarily a simulation tool, GNS3 can be used to visualize live network topologies when connected to production environments.

​
Integrated Workflow Example

End-to-End Automation Workflow:

    Data Collection Phase:

        Use Python scripts with FortiManager API libraries to retrieve device inventory, topology data, and interface information

        Query Meraki API for network devices, L2/L3 topology, and connection details

        Collect LLDP/CDP neighbor information

    Data Processing Phase:

        Parse API responses into standardized node/edge format

        Identify device types, locations, and connection relationships

        Enrich data with metadata (IP addresses, hostnames, models)

    Diagram Generation Phase:

        For 2D Diagrams:

            Use N2G library to generate yEd or DrawIO files

            Apply automatic layout algorithms (force-directed, hierarchical)

            Export to Visio format if needed

        For 3D Visualizations:

            Generate 3D coordinates using NetworkX spring layout

            Render with Plotly, Three.js, or specialized tools

            Add interactive controls and metadata overlays

    Automation and Updates:

        Schedule periodic API queries to detect topology changes

        Automatically regenerate diagrams when changes detected

        Version control diagram outputs for change tracking

Technology Stack Recommendations:

For Enterprise Environments:

    NetBrain for comprehensive automation and integration

​

SolarWinds NTM for multi-vendor discovery and Visio export

    ​

For Open-Source/Custom Solutions:

    Python + pyFortiManagerAPI/Meraki SDK for data collection

​

N2G + yEd/DrawIO for 2D diagram generation

​

Plotly or Three.js for interactive 3D visualizations

    ​

For Cloud-Based Approaches:

    Mermaid.js for simple, version-controlled diagrams

​

Cytoscape.js for web-based interactive visualizations

    ​

Additional Automation Libraries and Tools

Nwdiag: A Python library for creating network diagrams using simple text-based syntax.

​

Diagrams: A Python package for drawing cloud system architecture using code (Diagram as Code).

​

Mermaid.js: A JavaScript-based diagramming tool that renders Markdown-inspired text definitions, suitable for network architecture diagrams.

​

AutoNetkit: Uses yEd for network design and can export to graph interchange formats for programmatic manipulation.

​

Python-Visio Libraries: While direct Visio automation requires Windows and COM objects, cross-platform alternatives include exporting to formats that Visio can import (VSDX, VDX).

​
Best Practices

    API Authentication Security: Store API keys securely using environment variables or secret management systems

​

Rate Limiting: Implement appropriate delays and pagination when querying APIs to avoid hitting rate limits

​

Error Handling: Include robust error handling for API failures, network timeouts, and data inconsistencies

Version Control: Store diagram source data (JSON, DOT files) in version control alongside generated images

​

Incremental Updates: Cache API responses and only regenerate diagrams when topology changes are detected

​

Documentation: Maintain clear documentation of data sources, transformation logic, and diagram generation processes

Testing: Validate generated diagrams against known network topologies before deploying automation

    ​

The combination of FortiManager and Meraki APIs with modern visualization tools provides powerful capabilities for automated network topology documentation. The choice between 2D and 3D visualization, and between commercial and open-source tools, depends on your specific requirements for interactivity, scale, integration needs, and budget considerations.

AutoNetkit:

Now I have comprehensive information about AutoNetkit. Let me compile a detailed report about this tool.
AutoNetkit: Automated Network Configuration Engine

AutoNetkit is a powerful, open-source Python-based framework designed to automatically build large-scale network configurations from topology diagrams. It addresses a critical challenge in network engineering: the time-consuming and error-prone manual configuration of complex networks with hundreds or thousands of devices.

​
Core Purpose and Use Cases

AutoNetkit was originally developed as part of PhD thesis research at the University of Adelaide and has been further developed in collaboration with Cisco and other industry partners. The tool is used by network operators, vendors, academia, and educational institutions for designing, configuring, and measuring large-scale networks.
​

​

Key Applications:

    Academic research and network design experiments (supporting topologies with over 800 virtual routers)

​

University teaching and training environments

Industry network planning and proof-of-concept deployment

​

Configuration generation for network emulation and simulation platforms

Cisco Modeling Labs (CML), formerly VIRL, includes AutoNetkit as its network modeling engine

​

Juniper Junosphere automated topology and configuration generation

    ​

Architecture and Data Model

Input Format: GraphML

AutoNetkit uses GraphML (Graph Markup Language) as its primary input format. GraphML is an XML-based format that allows defining network topologies with node properties and edge connections.

​

Key GraphML Properties for AutoNetkit:

    asn: Autonomous System Number for BGP routing configuration. Different ASNs between connected nodes trigger eBGP peering; identical ASNs create iBGP relationships

​

node labels: Device names and identifiers

edge definitions: Links between devices with optional properties (bandwidth, delay, loss)

device type: Router, switch, or server classification

role: Device function within the topology (core, edge, host)

    ​

Topology Sources:

AutoNetkit can consume topologies from multiple sources:

    yEd diagrams: Created using the free yEd graph editor, which exports to GraphML format

​

​

Topology Zoo: Real-world network topologies in GraphML format available from topology-zoo.org

​

Custom GraphML files: User-generated topology files

    ​

Configuration Generation Capabilities

AutoNetkit automatically generates router configurations for multiple vendor platforms from a single topology input:

​

Supported Platforms:

    Cisco IOS and IOS-XE

​

Juniper Junos

​

Quagga (open-source routing software)

​

Netkit (Linux-based network emulation)

    ​

Routing Protocol Configuration:

AutoNetkit automatically generates routing protocol configurations based on topology properties:

    BGP: Configured based on ASN values; creates iBGP mesh or eBGP peering as appropriate

​

OSPF: Interior Gateway Protocol configuration with area definitions

​

IS-IS: Alternative IGP option

​

EIGRP: Enterprise IGP support

    ​

Automatic Features:

    IP Address Allocation: Automatically allocates IPv4, IPv6, or dual-stack (both IPv4 and IPv6) addresses throughout the topology

​

Loopback Addresses: Automatic loopback interface configuration for routing stability

Interface Configuration: Automatic generation of interface configurations with IP addresses and metrics

​

Layer 3 VPN (L3VPN): Automatic MPLS VPN configuration

    ​

Template System

AutoNetkit uses Mako template engine for configuration generation:

​

Mako Template Integration:

    Python-based template engine allowing dynamic configuration generation

    Supports Python code directly within templates

​

More readable syntax compared to alternative template engines (Jinja2) with fewer curly brackets

​

Enables bulk configuration generation from topology data

    ​

Template Features:

    Control structures (loops, conditionals) for device-specific configurations

    Python functions for complex calculations (IP subnetting, address manipulation)

​

Support for netaddr module integration for advanced IP address operations

​

Compatible with vendor-specific configuration syntax requirements

    ​

Visualization and Output

Built-in Visualization:

AutoNetkit provides browser-based visualization of network topologies and routing protocols:

    Physical Model Visualization: Shows device nodes and physical interface connections

​

Layer Views: Distinct visualization layers for:

    Physical topology

    OSPF areas and adjacencies

    BGP autonomous systems and peering relationships

    MPLS paths (when applicable)

    L3VPN overlays

    ​

Interactive Controls: Pan, zoom, rotation, and search/filter capabilities

​

HTML Plotting Output: The --plot option generates network graphs in HTML format and places them in the "ank_labplots" directory

    ​

File-based Output:

AutoNetkit creates comprehensive output directories:

    Configuration files for each router in device-specific formats

    Topology visualization files

    Archive of previous configurations

    Topology descriptor files (Topology.vmm for Junosphere)

    ​

Platform-Specific Integration

Junosphere Integration:

Junosphere is Juniper's cloud-based network simulation platform. AutoNetkit provides complete integration:

​

bash
# Generate Junosphere configuration
autonetkit -f ./topology.graphml --junosphere [--ospf|--isis] [--plot]

    Generates .gz files for uploading to Junosphere library

    Creates Junos-specific configurations for VJX virtual routers

    Supports both standard VJX and custom Olive-based installations

    Configuration placed in ank_lab/junos_lab directory

    ​

Netkit Integration:

Netkit is a lightweight Linux-based network emulator:

​

bash
# Generate Netkit configuration
autonetkit -f simple.graphml --netkit

    Creates per-router configuration files in Netkit format

    Includes startup scripts and network daemon configurations

    Generates OSPF and BGP configurations for Quagga routing software

    ​

GNS3 Integration:

GNS3 (Graphical Network Simulator-3) is a network emulation platform:

bash
autonetkit -f topology.graphml --gns3 [--ospf|--isis]

    Generates GNS3-compatible configuration sets

    Automates deployment of topologies in GNS3 environments

cBGP Integration:

cBGP (Cisco BGP Simulator) for testing BGP behavior:

bash
autonetkit -f topology.graphml --cbgp

Python API Usage

AutoNetkit provides a Python API for programmatic network design:

​

Core Network Object:

python
import autonetkit as ank

# Load or create topology
network = ank.example_multi_as()

# Access network properties
devices = network.devices()
routers = network.routers()
asn = network.asn("1a.AS1")

Data Model Methods:

AutoNetkit implements intuitive data model methods for elegant network specification:

​

    __lt__, __eq__, __contains__: Comparison and membership operators

    __getattr__, __setattr__: Attribute access for network properties

    __iter__: Iteration over network elements

    List comprehensions: For expressive network design

    ​

NetworkX Integration:

AutoNetkit is built on top of NetworkX graph library:

​

    Provides graph theory capabilities

    Enables programmatic topology manipulation

    Supports complex network analysis

Command-Line Interface

AutoNetkit provides a comprehensive command-line interface:

​

bash
autonetkit -f <topology.graphml> [options]

Options:
  -p, --plot              Plot lab topology visualization
  -d, --deploy            Deploy lab to Netkit host
  -f FILE, --file=FILE    Load topology from FILE
  -n NETKITHOST           Netkit host machine (if remote)
  -u USERNAME             Username for Netkit host
  -v, --verify            Verify lab on Netkit host
  --xterm                 Load each VM console in Xterm
  --debug                 Enable debugging output
  --netkit                Compile for Netkit
  --cbgp                  Compile for cBGP
  --gns3                  Compile for GNS3
  --junos                 Compile for JunOS
  --isis                  Use IS-IS as IGP (instead of OSPF)
  --tapsn=TAPSN           Tap subnet for VM connectivity

Integration with Network Design Workflow

AutoNetkit seamlessly integrates with visual network design workflows:

​

Design → Configuration → Deployment Workflow:

    Topology Design Phase: Create network topology in yEd or Topology Zoo

    Property Assignment: Add ASN, device roles, and connection properties

    Export to GraphML: yEd exports topology to GraphML format

    Configuration Generation: AutoNetkit generates device configurations

    Deployment: Push configurations to target platforms (Junosphere, Netkit, GNS3)

    Verification: Deploy and test configurations in emulated network

    Visualization: View topology relationships and protocol adjacencies

    ​

Advanced Features

IPv4 and IPv6 Support:

AutoNetkit can be configured globally for IPv4-only, IPv6-only, or dual-stack addressing:

​

    Automatic address block allocation from specified ranges

    Consistent address scheme generation across all devices

    Support for RFC-compliant address allocation

    ​

IP Addressing with Netaddr:

Integration with Python netaddr module for sophisticated addressing:

    CIDR notation support

    Network mask calculations

    Subnet generation and validation

    Automatic inverse mask calculation for access control lists (ACLs)

    ​

Real-Time Updates:

AutoNetkit includes experimental support for dynamic topology updates using Tornado web server:

​

    Live browser-based visualization

    Real-time feedback during design and measurement

    Interactive network model manipulation

Industry and Academic Adoption

Cisco Integration:

Cisco Modeling Labs (CML) incorporates AutoNetkit as the core network modeling engine:

​

    Used for topology design and initial configuration

    Provides BGP, OSPF, L3VPN, and MPLS configuration generation

    Integrated visualization layers for protocol relationships

    ​

Juniper Integration:

Junosphere platform uses AutoNetkit for automated topology and configuration generation:

​

    Supports Junos-specific features and configurations

    Enables rapid deployment of complex Juniper network scenarios

Research and Academia:

AutoNetkit has been used in research projects including:

    Network experiments with 800+ virtual routers

    BGP security evaluation frameworks

​

Network emulation studies and topology assessment

    ​

Workflow for FortiManager/Meraki Integration

While AutoNetkit traditionally focuses on topology generation and configuration, it can be incorporated into a broader automation workflow with FortiManager and Meraki:

Potential Integration Approach:

    Extract Topology: Query FortiManager and Meraki APIs to retrieve network device inventory and connections

    Generate GraphML: Convert API data into GraphML topology format

    Apply AutoNetkit: Generate initial configurations or visualization

    Augment with Vendor-Specific Logic: Add FortiManager/Meraki-specific configurations

    Deploy: Push configurations back to devices via APIs or management tools

Key Strengths

    Rapid Configuration Generation: Automatically generates thousands of lines of configuration from simple topology diagram

    Multi-Vendor Support: Single topology generates configurations for Cisco, Juniper, Quagga, and other platforms

    Error Reduction: Eliminates manual configuration errors through automation

    Educational Value: Excellent tool for teaching network design and routing protocols

    Active Protocol Support: Handles complex protocols (BGP, OSPF, MPLS, L3VPN) automatically

    Flexible Input: Accepts topologies from visual tools, topology databases, or programmatic API

    Proven Reliability: Used by major vendors, operators, and research institutions

Limitations and Considerations

    Learning Curve: GraphML format and topology property definitions require some training

    Platform-Specific Features: Vendor-specific features may require manual template customization

    Python 3 Rewrite: Newer version in finalization; documentation may reference older Python 2 version

    Limited to Supported Platforms: Extends to FortiManager/Meraki would require custom template development

    Static Generation: Designed for initial configuration; dynamic updates require additional tooling

Recent Development

AutoNetkit was rewritten for Python 3 compatibility with improved performance and a cleaner API. The modernized version removes complexities and quirks from the original research-based codebase, making it more suitable for production use.

​

AutoNetkit represents a mature, battle-tested approach to automated network configuration generation. Its integration with commercial platforms like Cisco Modeling Labs and Juniper Junosphere demonstrates its value in enterprise and educational environments. For organizations managing complex multi-vendor networks, AutoNetkit provides significant efficiency gains by automating configuration generation from topology diagrams.

DrawIO integration with Model Context Protocol (MCP) for AI-assisted diagram generation from network data
DrawIO Integration with Model Context Protocol (MCP) for AI-Assisted Network Diagram Generation

The integration of Draw.io (Diagrams.net) with Model Context Protocol (MCP) represents a breakthrough in AI-assisted network topology visualization. This integration enables Large Language Models (LLMs) to programmatically create, modify, and analyze network diagrams through natural language commands, dramatically accelerating the documentation process for FortiManager and Meraki-based networks.
What is Model Context Protocol (MCP)?

Model Context Protocol (MCP) is an open standard developed by Anthropic that enables seamless integration between Large Language Models and external data sources, tools, and systems. MCP provides a lightweight, capability-oriented RPC layer that addresses the challenge of safely exposing real-time actions and data to AI systems.

​

Core Architecture:

MCP follows a client-server architecture with three foundational components:

​

    MCP Clients (AI applications like Claude Desktop, Amazon Q CLI, VS Code extensions)

    MCP Servers (Expose specific capabilities to clients via standard protocol)

    Local Data Sources (Files, databases, APIs that servers can access)

Transport Mechanisms:

    Stdio Transport: Uses standard input/output streams for local process communication between client and server on the same machine

​

HTTP/WebSocket Transport: Enables remote server communication with standard authentication (OAuth, bearer tokens, API keys)
​

    ​

Key Capabilities:

    Tools: AI-callable functions that perform specific actions (e.g., create diagram, query API, execute command)

​

Resources: Contextual data that AI can access (e.g., device configurations, topology data)

​

Prompts: Reusable templates for common workflows

​

Sampling: Ability for servers to request LLM inference on behalf of systems

    ​

DrawIO MCP Server Implementation

Project Overview:

The Draw.io MCP Server (drawio-mcp-server) is an open-source implementation that brings programmatic diagramming capabilities to AI agentic systems. Created by László Gazo and available on GitHub, it has gained significant traction with 278+ stars and active community contributions.

​

Architecture Components:

    MCP Server (Node.js-based, v20+)

        Listens on localhost port 3333 by default

​

Implements standard MCP protocol via JSON-RPC 2.0

​

Manages bidirectional communication with Draw.io browser instance

    ​

Browser Extension (Chrome/Firefox)

    Bridges communication between Draw.io web app and MCP server

​

Uses WebSocket protocol for real-time updates

​

Displays connection status in extension popup

    ​

MCP Client (AI interface)

    Claude Desktop, Amazon Q CLI, VS Code extensions, Zed, oterm, or custom clients

​

Sends natural language requests to LLM

LLM translates requests into MCP tool calls

        ​

Installation and Setup:

bash
# Install via npm
npx -y drawio-mcp-server

# Or via pnpm
pnpm dlx drawio-mcp-server

Configuration for Claude Desktop (macOS):

json
{
  "mcpServers": {
    "drawio": {
      "command": "npx",
      "args": ["-y", "drawio-mcp-server"]
    }
  }
}

Configuration for Amazon Q CLI:

json
{
  "mcpServers": {
    "awslabs.drawio-mcp-server": {
      "command": "uvx",
      "args": ["drawio-mcp-server"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "autoApprove": [],
      "disabled": false
    }
  }
}

MCP Tools for Network Diagram Creation

The Draw.io MCP server provides comprehensive tools organized into two categories:

​
Diagram Inspection Tools

1. get-selected-cell

    Retrieves currently selected diagram element with all attributes

    Returns: JSON object with cell ID, geometry, style, value, connections

    Use case: Understanding existing diagram structure for modifications

    ​

2. get-shape-categories

    Lists all available shape libraries (AWS, Azure, Cisco, networking icons)

    Returns: Array of category objects with IDs and names

    Use case: Discovering available icon sets for network devices

    ​

3. get-shapes-in-category

    Parameters: category_id

    Returns: All shapes within specified category with properties

    Use case: Finding specific network device icons (routers, switches, firewalls)

    ​

4. get-shape-by-name

    Parameters: shape_name

    Returns: Specific shape with category and style information

    Use case: Locating FortiGate, Meraki, or generic networking icons

    ​

5. list-paged-model

    Retrieves paginated view of all diagram cells (vertices and edges)

    Supports filtering with boolean logic on multiple criteria

    Returns: Sanitized model data without circular dependencies

    Use case: Programmatic inspection of entire network topology structure

    ​

Diagram Modification Tools

1. add-rectangle

    Creates basic shape with customizable properties

    Parameters: x, y, width, height, text, style

    Style syntax: Draw.io format (e.g., fillColor=#ffffff;strokeColor=#000000)

    Use case: Creating labeled boxes for network segments or zones

    ​

2. add-edge

    Creates connections between network devices

    Parameters: source_id, target_id, text (label), style

    Use case: Drawing links between routers, switches, and access points with interface labels

    ​

3. delete-cell-by-id

    Parameters: cell_id

    Removes specified diagram element

    Use case: Removing outdated devices or connections from topology

    ​

4. add-cell-of-shape

    Creates cell from library shape (network device icons)

    Parameters: shape_name, x, y, width, height, text, style

    Use case: Adding FortiGate firewall, Meraki AP, or Cisco router icons with proper positioning

    ​

Network Topology Automation Workflow

End-to-End Process for FortiManager/Meraki Integration:

Phase 1: Data Collection from APIs

python
# Pseudo-code example
import requests

# Query FortiManager API
fortimanager_data = get_fortimanager_devices()
# Returns: device list, interfaces, connections, locations

# Query Meraki API  
meraki_data = get_meraki_topology()
# Returns: networks, devices, L2/L3 links, client counts

Phase 2: Natural Language Request to AI Agent

User interacts with Claude Desktop, Amazon Q CLI, or similar MCP client:

text
"Create a network diagram showing:
- All FortiGate firewalls from site A and B
- Meraki access points with client counts
- WAN connections between sites
- Use appropriate vendor icons
- Label all interfaces and VLANs"

Phase 3: AI Tool Orchestration

The LLM breaks down the request into MCP tool calls:

    Discovery Phase:

text
get-shape-categories()
get-shapes-in-category(category_id: "cisco_network")
get-shape-by-name(shape_name: "FortiGate Firewall")
get-shape-by-name(shape_name: "Meraki AP")

Device Placement Phase:

text
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

Connection Phase:

    text
    add-edge(
      source_id: "fortigate-1",
      target_id: "meraki-ap-1",
      text: "Trunk\nVLAN 10,20,30",
      style: "endArrow=classic;..."
    )

Phase 4: Iterative Refinement

User can request modifications in natural language:

text
"Move all APs to the right side and group by floor"
"Change the firewall connection to show redundant links"
"Add a legend showing device types and connection speeds"

The AI agent uses list-paged-model to understand current layout, then applies modifications using delete-cell-by-id and repositioning commands.
Real-World Implementation: pyATS MCP Integration

John Capobianco's Breakthrough Integration

Network engineer John Capobianco at Selector.ai demonstrated a production-ready implementation combining Draw.io MCP with Cisco pyATS for automated network topology generation.
​

​

Architecture Overview:

text
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

Key Capabilities Demonstrated:

    Automatic Topology Discovery:

​

    pyATS connects to network devices via SSH/NETCONF

    Collects CDP/LLDP neighbor information

    Parses interface configurations and VLAN data

    Streams real-time data to MCP server via WebSocket

AI-Driven Diagram Generation:

​

    LLM interprets device data and relationships

    Determines optimal diagram layout

    Selects appropriate shapes from Draw.io libraries

    Generates labeled connections with interface names

Bidirectional Workflow:

    ​

        Data → Diagram: Automatically draw topology from live network state

        Diagram → Config: Parse Draw.io diagrams to generate device configurations

        Enables "visual NetDevOps" where diagrams represent intent

Tool Functions Implemented:

    get-all-cells-detailed: Extract complete topology structure from Draw.io

    get-edge-labels: Parse interface labels (e.g., "Eth0/2", "Trunk", "VLAN30")

    Interface parsing translates labels into real IOS configuration commands

    ​

Use Cases:

    Real-time topology views during CI/CD pipelines

​

Incident response: Generate live topology showing affected paths

ChatOps integration: Request diagrams via Slack/Teams commands

Multi-agent workflows: Chain with LangGraph for complex automation

    ​

Video Demonstrations:

Two detailed videos showcase the capabilities:

    "Automated Network Diagrams with DrawIO and pyATS MCP" (20 minutes)

​

"Fully Configuring a Network from DrawIO Diagram with pyATS MCP" (46 minutes)

    ​

Network-Specific MCP Applications

IETF Draft: MCP for Network Troubleshooting

An emerging IETF draft (draft-zeng-mcp-troubleshooting-00) describes using MCP for intent-based network management:

​

Proposed Architecture:

    Network Devices as MCP Servers: Routers, switches, and firewalls expose MCP tools

    Network Controllers as MCP Clients: SDN controllers and management systems consume MCP

    LLM Integration: AI agents reason about device logs, configurations, and telemetry

    ​

MCP Tools for Network Devices:

Example tool schema for network diagnostics:

​

json
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

Prompts for Troubleshooting Workflows:

Vendors can encode golden troubleshooting workflows as MCP prompts:

text
Prompt: "Diagnose interface {{interface}} high error rate"
Variables: interface name from user
Actions: 
  1. show interface {{interface}}
  2. show logging | include {{interface}}
  3. show controllers {{interface}}
  4. Analyze error patterns with LLM

Benefits for FortiManager/Meraki Environments:

    Conversational troubleshooting: "Why is VLAN 30 not passing traffic?"

    Configuration validation: "Check if all APs have consistent SSIDs"

    Closed-loop remediation: AI detects issue, proposes fix, applies after approval

    ​

Commercial MCP Server Examples

AWS Diagram MCP Server

AWS Labs developed an MCP server for generating AWS architecture diagrams using the Python diagrams package.

​

Key Features:

    Supports AWS, sequence, flow, and class diagrams

    Uses Python DSL for diagram generation

    Integrates with Amazon Q CLI for natural language diagramming

    Code scanning for secure diagram generation

    ​

Network Relevance:

While AWS-focused, the pattern applies to network diagrams:

python
# Network topology equivalent
from diagrams import Diagram
from diagrams.cisco.routing import Router
from diagrams.cisco.switching import Switch

with Diagram("Network Topology", show=False):
    router = Router("Core Router")
    switch1 = Switch("Access Switch 1")
    switch2 = Switch("Access Switch 2")
    
    router >> switch1
    router >> switch2

Amazon Q CLI can generate this code from natural language: "Create a diagram with one core router connected to two access switches".

​

ToDiagram MCP Server

ToDiagram offers a commercial MCP server for generating interactive diagrams from structured data:

​

    Supports JSON, YAML, XML, CSV, and Mermaid inputs

    Outputs editable, shareable diagrams

    Integrates with AI copilots and CI/CD workflows

    Secure with API key authentication

    ​

Network Application:

Export FortiManager/Meraki data as JSON, send to MCP server, receive interactive diagram.
Integration Strategies for FortiManager and Meraki

Strategy 1: Direct API → MCP → Draw.io

text
FortiManager/Meraki APIs
    ↓ (Python script)
JSON Topology Data
    ↓ (MCP client request)
LLM with Draw.io MCP Server
    ↓ (MCP tool calls)
Draw.io Network Diagram

Implementation Steps:

    Data Collection Script:

python
# Collect topology data
devices = get_fortimanager_devices()
links = get_meraki_l2_topology()

# Format for LLM context
topology_description = format_topology_for_llm(devices, links)

Natural Language Request:

    text
    User → Claude Desktop: 
    "Here's my network topology data: {topology_description}
     Create a hierarchical diagram showing:
     - Core FortiGate cluster at top
     - Distribution switches in middle
     - Meraki APs at bottom grouped by building
     - Use red lines for 10G links, blue for 1G"

    AI Orchestration:

        LLM parses topology data

        Plans diagram layout (hierarchical, force-directed, or custom)

        Executes MCP tool calls to Draw.io server

        Creates professional network diagram

Strategy 2: pyATS-Style Real-Time Polling

Implement continuous topology monitoring similar to Capobianco's pyATS integration:

​

python
# Pseudo-code
while True:
    # Poll APIs every 5 minutes
    current_state = {
        'fortimanager': poll_fortimanager_api(),
        'meraki': poll_meraki_api()
    }
    
    # Detect changes
    if topology_changed(current_state, previous_state):
        # Trigger diagram update via MCP
        update_diagram_via_mcp(current_state)
    
    sleep(300)

Benefits:

    Live topology views during network changes

    Automated documentation updates

    Incident response visualization (show affected segments)

    ​

Strategy 3: CI/CD Integration

Embed topology diagram generation in deployment pipelines:

text
# GitLab CI example
topology-diagram:
  stage: documentation
  script:
    - python collect_topology_data.py
    - mcp-client generate-diagram --input topology.json --output diagram.drawio
  artifacts:
    paths:
      - network-topology.drawio
      - network-topology.png

Strategy 4: ChatOps Integration

Enable Slack/Teams commands for on-demand diagrams:

​

text
/network-diagram site=headquarters layer=physical
/network-diagram show-vpn-tunnels between=site-a and site-b
/network-diagram highlight-path from=10.1.1.0/24 to=10.5.5.0/24

Bot triggers MCP workflow, returns diagram link in chat.
Advanced Features and Capabilities

Multi-Layer Visualization

Create separate diagram layers for different network aspects:

    Physical Layer: Devices, connections, interface labels

    VLAN Layer: Logical segmentation, trunk ports

    Security Layer: Firewall zones, ACLs, security policies

    Application Layer: Services, load balancers, application paths

MCP enables programmatic layer management through multiple diagram pages.

Style Customization

Apply consistent styling based on device state or metrics:

python
# Pseudo-code for dynamic styling
for device in devices:
    if device.cpu_usage > 80:
        style = "fillColor=#ff0000;fontColor=#ffffff"  # Red
    elif device.cpu_usage > 50:
        style = "fillColor=#ffa500;fontColor=#000000"  # Orange
    else:
        style = "fillColor=#00ff00;fontColor=#000000"  # Green
    
    add_cell_of_shape(
        shape_name=device.type,
        text=f"{device.name}\nCPU: {device.cpu_usage}%",
        style=style
    )

Diff Visualization

Compare topology snapshots and highlight changes:

    Generate diagram from previous state (green devices/links)

    Generate diagram from current state (blue devices/links)

    Highlight differences (red for removed, yellow for modified)

Enables "before/after" views for change management.

Interactive Documentation

Embed metadata in diagram cells for interactive documentation:

    Click device → Show configuration

    Click link → Show bandwidth utilization graph

    Hover interface → Display traffic statistics

While Draw.io natively supports links, MCP enables programmatic metadata injection.
Performance and Scalability

Handling Large Topologies:

For enterprise networks with 500+ devices:

    Hierarchical Decomposition:

        Create separate diagrams per site/region

        Generate overview diagram with site-to-site links

        Use hyperlinks between diagrams

    Filtering and Pagination:

        Use list-paged-model with filters for targeted updates

        Process topology in chunks to avoid overwhelming LLM context

    Incremental Updates:

        Track previous diagram state

        Only modify changed elements using delete-cell-by-id and add-cell-of-shape

        Avoid regenerating entire diagram

WebSocket for Real-Time Updates:

The HTTP/WebSocket transport enables streaming updates:
​

​

javascript
// MCP server receives continuous stream
websocket.on('topology_update', (data) => {
    // Process delta
    const changes = compute_changes(data);
    
    // Apply to diagram
    changes.forEach(change => {
        mcp_client.call_tool('update-cell', change);
    });
});

Security Considerations

Authentication and Authorization:

    MCP servers should implement OAuth or API key authentication

​

Draw.io extension communicates over localhost WebSocket (port 3333)

    ​

    Network API credentials stored securely (environment variables, secrets manager)

Code Execution Risks:

    LLM-generated MCP tool calls should be validated

    AWS Diagram MCP Server includes code scanning for security

    ​

    Implement approval workflows for production diagram updates

Data Privacy:

    Topology data may contain sensitive IP addressing schemes

    Consider on-premises MCP server deployment for air-gapped networks

    Audit LLM API requests to ensure no sensitive data leakage

Ecosystem and Future Directions

MCP Standardization Efforts:

    Anthropic maintains official MCP specification at modelcontextprotocol.io

​

IETF exploring network-specific MCP applications

​

Growing ecosystem of MCP servers (278+ GitHub stars for Draw.io MCP)

    ​

Agentic AI for Networks:

The broader trend toward "agentic AI" in networking:

​

    Autonomous network management: AI agents that monitor, diagnose, and remediate without human intervention

    Multi-agent orchestration: LangGraph, AutoGen enabling complex workflows

    Natural language interfaces: Engineers describe intent, AI handles implementation

MCP provides the "protocol glue" enabling AI agents to interact with disparate network systems.

​

Integration with Network Automation Frameworks:

    Ansible + MCP: Playbooks trigger diagram updates

    Terraform + MCP: Infrastructure-as-Code generates corresponding diagrams

    Nornir + MCP: Python automation framework with MCP tool integration

    ​

Vision for Network Engineers:

The future workflow:

​

text
Engineer: "Show me why VLAN 100 can't reach the internet"

AI Agent (via MCP):
1. Queries network devices for routing tables
2. Checks firewall policies via FortiManager API
3. Validates Meraki VLAN configuration
4. Generates topology diagram highlighting the path
5. Identifies misconfigured NAT rule
6. Proposes fix and applies after approval
7. Updates documentation diagram automatically

This shifts network engineering from manual, repetitive tasks to strategic, intent-based interactions.
Getting Started: Quick Implementation

Minimal Setup for FortiManager/Meraki Topology Automation:

    Install Prerequisites:

bash
# Node.js v20+
curl -fsSL https://nodejs.org/dist/v20.x/node-v20.x.tar.gz | tar xz

# Draw.io MCP Server
npm install -g drawio-mcp-server

# Python libraries
pip install pyFortiManagerAPI meraki

Configure Claude Desktop:

json
{
  "mcpServers": {
    "drawio": {
      "command": "npx",
      "args": ["-y", "drawio-mcp-server"]
    }
  }
}

Install Browser Extension:

    Chrome: Draw.io MCP Extension

​

Firefox: Draw.io MCP Extension

    ​

Open Draw.io and Connect:

    Navigate to https://app.diagrams.net/

    Extension should show "Connected" status

    Open Claude Desktop or compatible MCP client

Test Basic Functionality:

text
User → Claude: 
"In Draw.io, create a simple network with:
 - One router at coordinates (200, 100)
 - Two switches at (100, 300) and (300, 300)
 - Connect router to both switches
 - Label the router 'Core-Router-1'"

Integrate API Data:

python
# collect_topology.py
from pyFortiManagerAPI import FortiManager
import meraki

# Collect data
fm = FortiManager(host='fmg.example.com', username='api', password='***')
fm_devices = fm.get_devices()

meraki_dashboard = meraki.DashboardAPI(api_key='***')
meraki_devices = meraki_dashboard.organizations.getOrganizationDevices(org_id)

# Format for Claude
context = format_for_llm(fm_devices, meraki_devices)
print(context)

Generate Diagram:

    text
    User → Claude:
    "Using this network data: {context}
     Create a professional topology diagram in Draw.io showing:
     - FortiGate firewalls in the top row
     - Meraki switches in the middle row
     - Meraki APs in the bottom row grouped by building
     - Use Fortinet and Meraki icons from the shape libraries
     - Label all devices with hostname and management IP
     - Show trunk links between firewalls and switches"

Key Takeaways

Draw.io MCP Integration Benefits:

    Natural Language Diagramming: Describe topology intent, AI creates diagram

    API-Driven Automation: FortiManager/Meraki data → automatic diagram generation

    Bidirectional Workflow: Diagrams ↔ Configuration (visual NetDevOps)

    Real-Time Updates: Live topology views during network changes

    Standardized Protocol: MCP enables tool interoperability across vendors

Comparison to Traditional Methods:
Aspect	Manual Visio	Python Scripts	MCP + Draw.io
Speed	Hours	Minutes	Seconds
Skill Required	Design + Network	Programming	Natural Language
Real-Time Updates	Manual	Scheduled	Continuous
Flexibility	High (manual)	Medium (coding)	High (conversational)
Integration	Low	Medium	High (standard protocol)

When to Use MCP + Draw.io:

    ✅ Rapid topology documentation from API data

    ✅ AI-assisted diagram refinement (layout, styling, grouping)

    ✅ ChatOps and CI/CD integration for on-demand diagrams

    ✅ Multi-agent workflows requiring diagram generation

    ✅ Educational environments teaching network design

When Traditional Methods May Be Better:

    Manual artistic control needed (marketing materials)

    Legacy Visio templates with complex macros

    Air-gapped environments without LLM access

    Highly specialized diagram types not supported by Draw.io libraries

The Draw.io MCP integration represents a paradigm shift in network documentation, enabling natural language interactions with diagramming tools powered by FortiManager and Meraki APIs. As the MCP ecosystem matures, expect deeper integrations with network automation frameworks, enhanced security features, and broader adoption across the networking industry.

