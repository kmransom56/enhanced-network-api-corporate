# Plotly Network Graphs Analysis

## Overview

This document analyzes [Plotly's network graph capabilities](https://plotly.com/python/network-graphs/) and evaluates their suitability for integration into our network topology visualization application.

## Library Summary

**Plotly Python** is a graphing library that offers:
- **Language**: Python (backend integration)
- **Rendering**: Interactive HTML/JavaScript (Plotly.js)
- **Layout**: NetworkX-based or custom positioning
- **Export**: PNG, PDF, SVG, HTML (interactive)
- **Framework**: Dash for building analytical web apps
- **License**: MIT (open-source core)

## Current Application State

### Current Implementation
- **Backend**: FastAPI (Python)
- **3D Visualization**: Babylon.js (client-side)
- **2D Visualization**: D3.js (client-side)
- **Export Formats**: JSON, DrawIO XML, GraphML, Babylon.js format
- **Layout**: Custom hierarchical "Network Tree" (Python + JavaScript)
- **Icons**: SVG-based (from VSS extraction)
- **Missing**: Static image/PDF export for reports

## Feature Comparison

| Feature | Plotly | Current Implementation | Winner |
|---------|--------|----------------------|--------|
| **Backend Integration** | ✅ Python-native | ✅ FastAPI (Python) | Tie |
| **3D Visualization** | ❌ 2D only | ✅ Babylon.js 3D | **Current** |
| **2D Visualization** | ✅ Interactive HTML | ✅ D3.js interactive | Tie |
| **Static Export** | ✅ PNG, PDF, SVG | ❌ Not implemented | **Plotly** |
| **Interactive Export** | ✅ HTML with JS | ✅ HTML viewers | Tie |
| **Layout Control** | ⚠️ NetworkX-based | ✅ Custom hierarchical | **Current** |
| **Dash Integration** | ✅ Full Dash support | ❌ Not used | **Plotly** |
| **Network Analysis** | ✅ NetworkX integration | ⚠️ Custom logic | **Plotly** |
| **Custom Icons** | ⚠️ Limited (markers) | ✅ SVG-based 3D icons | **Current** |
| **Hierarchical Layout** | ⚠️ Via NetworkX | ✅ Custom Network Tree | **Current** |

## Detailed Analysis

### ✅ Advantages of Plotly

1. **Static Image/PDF Export** ⭐ **Major Benefit**
   - Export network diagrams to PNG, PDF, SVG
   - Perfect for reports, documentation, presentations
   - Server-side generation (no browser needed)
   - **Use Case**: Generate topology diagrams for PDF reports, email attachments, documentation

2. **Dash Framework Integration**
   - Build analytical dashboards with network topology
   - Interactive filtering, drill-down, real-time updates
   - Python-only (no JavaScript required)
   - **Use Case**: Network analysis dashboard, topology explorer with metrics

3. **NetworkX Integration**
   - Leverage NetworkX algorithms (centrality, clustering, path analysis)
   - Built-in graph analysis capabilities
   - Community algorithms and tools
   - **Use Case**: Network analysis, path finding, topology optimization

4. **Backend-Generated Visualizations**
   - Generate diagrams server-side
   - No client-side JavaScript required
   - Can embed in emails, reports, API responses
   - **Use Case**: Automated report generation, email notifications with diagrams

5. **Interactive HTML Export**
   - Self-contained HTML files with embedded Plotly.js
   - Zoom, pan, hover tooltips
   - Shareable without server
   - **Use Case**: Standalone topology reports, offline viewing

### ❌ Disadvantages of Plotly

1. **2D Only (No 3D)**
   - Plotly network graphs are 2D only
   - Your requirement includes 3D visualization
   - **Issue**: Would need to maintain both 2D (Plotly) and 3D (Babylon.js) implementations

2. **Layout Limitations**
   - Uses NetworkX layouts (spring, circular, hierarchical, etc.)
   - Not your custom "Network Tree" layout
   - Would need to adapt NetworkX layout or use custom positions
   - **Issue**: May not match your exact Visio-like hierarchical layout

3. **Custom Icon Support**
   - Limited to markers (circles, squares, custom images)
   - No SVG-to-3D conversion
   - No support for your VSS-extracted SVG icons as 3D meshes
   - **Issue**: Would lose the Visio-like appearance you've built

4. **Different Rendering Engine**
   - Plotly.js (not D3.js or Babylon.js)
   - Different API and customization approach
   - **Issue**: Additional learning curve, different codebase to maintain

5. **No Port-Based Positioning**
   - NetworkX layouts don't support port-based client positioning
   - Would need custom positioning logic anyway
   - **Issue**: Your port-based layout feature wouldn't work out-of-the-box

## Use Case Analysis

### ✅ When Plotly Would Be Valuable

1. **Static Image/PDF Export** ⭐ **Primary Use Case**
   ```python
   # Generate topology diagram for PDF report
   import plotly.graph_objects as go
   import networkx as nx
   
   # Create network graph
   G = nx.Graph()
   # Add nodes and edges from your topology
   
   # Generate Plotly figure
   fig = create_plotly_network_graph(G)
   
   # Export to PDF for report
   fig.write_image("topology_diagram.pdf")
   fig.write_image("topology_diagram.png")  # For presentations
   ```
   - **Benefit**: Currently missing feature
   - **Integration**: Add as new endpoint `/api/topology/export-pdf` or `/api/topology/export-png`

2. **Dash Analytical Dashboard**
   ```python
   # Build network analysis dashboard
   import dash
   from dash import dcc, html
   import plotly.graph_objects as go
   
   app = dash.Dash(__name__)
   
   # Network topology view with metrics
   # Device health overlay
   # Connection quality indicators
   # Real-time updates
   ```
   - **Benefit**: Network analysis and monitoring dashboard
   - **Integration**: Separate Dash app alongside FastAPI

3. **Network Analysis Features**
   - Centrality analysis (most important devices)
   - Path finding (shortest routes)
   - Clustering (device groups)
   - Topology optimization suggestions
   - **Benefit**: Advanced network analysis capabilities

4. **Email/Report Generation**
   - Automatically generate topology diagrams for reports
   - Embed in automated emails
   - Include in documentation
   - **Benefit**: Automated documentation and reporting

### ❌ When Current Implementation Is Better

1. **3D Visualization** ✅ (Your Requirement)
   - Plotly doesn't support 3D network graphs
   - Your Babylon.js implementation is essential
   - **Keep**: Current 3D viewer

2. **Custom Hierarchical Layout** ✅ (Your Requirement)
   - Your Network Tree layout matches Visio diagram exactly
   - Plotly would need custom positioning
   - **Keep**: Current layout algorithm

3. **SVG-Based 3D Icons** ✅ (Your Requirement)
   - Your VSS-extracted SVG icons with 3D extrusion
   - Plotly can't replicate this
   - **Keep**: Current icon system

4. **Interactive 2D Viewer** ✅ (Already Working)
   - Your D3.js implementation is working well
   - Plotly would be redundant
   - **Keep**: Current 2D viewer

## Recommended Integration Strategy

### ✅ **Hybrid Approach: Add Plotly for Export & Analysis**

**Keep your current implementation** and **add Plotly** for specific use cases:

#### 1. **Static Export Endpoint** (High Priority)

Add new FastAPI endpoint for static image/PDF export:

```python
# src/enhanced_network_api/platform_web_api_fastapi.py

import plotly.graph_objects as go
import networkx as nx
from plotly.io import write_image

@app.post("/api/topology/export-image")
async def export_topology_image(
    format: str = "png",  # png, pdf, svg
    layout: str = "network_tree"
):
    """Export topology as static image (PNG, PDF, or SVG)"""
    # Load topology data
    topology = await get_topology_data()
    
    # Convert to NetworkX graph
    G = nx.Graph()
    for node in topology["nodes"]:
        G.add_node(node["id"], **node)
    for link in topology["links"]:
        G.add_edge(link["source"], link["target"], **link)
    
    # Apply your custom layout (convert positions to NetworkX)
    pos = apply_network_tree_layout_to_networkx(G, topology)
    
    # Create Plotly figure
    fig = create_plotly_network_from_graph(G, pos)
    
    # Export
    if format == "png":
        return Response(write_image(fig, "topology.png"), media_type="image/png")
    elif format == "pdf":
        return Response(write_image(fig, "topology.pdf"), media_type="application/pdf")
    elif format == "svg":
        return Response(write_image(fig, "topology.svg"), media_type="image/svg+xml")
```

**Benefits**:
- ✅ Adds missing static export capability
- ✅ Minimal code changes
- ✅ Complements existing visualization
- ✅ Useful for reports and documentation

#### 2. **Dash Analytical Dashboard** (Optional, Medium Priority)

Create separate Dash app for network analysis:

```python
# src/enhanced_network_api/dash_analytics.py

import dash
from dash import dcc, html
import plotly.graph_objects as go
import networkx as nx

app = dash.Dash(__name__)

@app.callback(...)
def update_network_analysis(...):
    # Network analysis with Plotly
    # Centrality metrics
    # Path analysis
    # Health indicators
    pass
```

**Benefits**:
- ✅ Advanced network analysis
- ✅ Separate from main app (optional)
- ✅ Python-only (easier for data scientists)

#### 3. **Network Analysis Utilities** (Low Priority)

Add NetworkX-based analysis functions:

```python
# src/enhanced_network_api/network_analysis.py

import networkx as nx

def analyze_topology_centrality(topology):
    """Find most critical devices"""
    G = convert_topology_to_networkx(topology)
    centrality = nx.betweenness_centrality(G)
    return centrality

def find_shortest_path(topology, source, target):
    """Find shortest path between devices"""
    G = convert_topology_to_networkx(topology)
    return nx.shortest_path(G, source, target)
```

## Implementation Plan

### Phase 1: Static Export (Recommended)

1. **Add Dependencies**
   ```bash
   pip install plotly networkx kaleido  # kaleido for static image export
   ```

2. **Create Export Utility**
   - `src/enhanced_network_api/plotly_export.py`
   - Convert topology to NetworkX graph
   - Apply your Network Tree layout positions
   - Generate Plotly figure
   - Export to PNG/PDF/SVG

3. **Add API Endpoint**
   - `/api/topology/export-image?format=png`
   - `/api/topology/export-image?format=pdf`
   - `/api/topology/export-image?format=svg`

4. **Test Integration**
   - Verify layout matches your Network Tree
   - Test export quality
   - Ensure device icons are visible

### Phase 2: Dash Dashboard (Optional)

1. **Create Dash App**
   - `src/enhanced_network_api/dash_app.py`
   - Network topology view
   - Metrics overlay
   - Real-time updates

2. **Integrate with FastAPI**
   - Mount Dash app at `/analytics`
   - Share topology data

### Phase 3: Network Analysis (Optional)

1. **Add Analysis Functions**
   - Centrality analysis
   - Path finding
   - Clustering
   - Health scoring

2. **Expose via API**
   - `/api/topology/analyze/centrality`
   - `/api/topology/analyze/path`
   - `/api/topology/analyze/clusters`

## Code Example: Static Export

```python
# src/enhanced_network_api/plotly_export.py

import plotly.graph_objects as go
import networkx as nx
from typing import Dict, List, Any
from plotly.io import write_image

def create_plotly_network_from_topology(
    topology: Dict[str, Any],
    layout_positions: Dict[str, Dict[str, float]]
) -> go.Figure:
    """Create Plotly network graph from topology data"""
    
    # Extract edges
    edge_x = []
    edge_y = []
    for link in topology.get("links", []):
        source = link.get("source") or link.get("from")
        target = link.get("target") or link.get("to")
        
        if source in layout_positions and target in layout_positions:
            x0, y0 = layout_positions[source]["x"], layout_positions[source]["y"]
            x1, y1 = layout_positions[target]["x"], layout_positions[target]["y"]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
    
    # Create edge trace
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    # Extract nodes
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    
    for node in topology.get("nodes", []):
        node_id = node.get("id")
        if node_id in layout_positions:
            pos = layout_positions[node_id]
            node_x.append(pos["x"])
            node_y.append(pos["y"])
            
            # Node label
            name = node.get("name") or node_id
            node_type = node.get("type", "unknown")
            node_text.append(f"{name}<br>Type: {node_type}")
            
            # Color by device type
            if "fortigate" in node_type.lower():
                node_colors.append("red")
            elif "fortiswitch" in node_type.lower():
                node_colors.append("cyan")
            elif "fortiap" in node_type.lower():
                node_colors.append("blue")
            else:
                node_colors.append("gray")
    
    # Create node trace
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[node.get("name", "") for node in topology.get("nodes", [])],
        textposition="middle center",
        hoverinfo='text',
        hovertext=node_text,
        marker=dict(
            size=20,
            color=node_colors,
            line=dict(width=2, color='white')
        )
    )
    
    # Create figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="Network Topology",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
    )
    
    return fig

def export_topology_to_image(
    topology: Dict[str, Any],
    layout_positions: Dict[str, Dict[str, float]],
    output_path: str,
    format: str = "png"
):
    """Export topology to static image"""
    fig = create_plotly_network_from_topology(topology, layout_positions)
    write_image(fig, output_path, format=format, width=1920, height=1080)
```

## Dependencies

Add to `requirements.txt`:
```
plotly>=5.18.0
networkx>=3.2
kaleido>=0.2.1  # Required for static image export (PNG, PDF, SVG)
```

**Note**: `kaleido` is required for `write_image()` to work. It's a headless browser for rendering.

## Conclusion

### ✅ **Recommended: Add Plotly for Static Export**

**Primary Benefit**: Adds missing static image/PDF export capability

**Integration Strategy**:
1. ✅ **Keep** current 3D (Babylon.js) and 2D (D3.js) viewers
2. ✅ **Add** Plotly for static export (PNG, PDF, SVG)
3. ⚠️ **Optional** Dash dashboard for network analysis
4. ⚠️ **Optional** NetworkX analysis utilities

**Why This Approach**:
- ✅ Complements existing visualization (doesn't replace)
- ✅ Adds valuable missing feature (static export)
- ✅ Minimal code changes
- ✅ No disruption to current functionality
- ✅ Useful for reports and documentation

**Implementation Priority**:
1. **High**: Static export endpoint (`/api/topology/export-image`)
2. **Medium**: Dash analytical dashboard (optional)
3. **Low**: NetworkX analysis utilities (optional)

## References

- [Plotly Network Graphs Documentation](https://plotly.com/python/network-graphs/)
- [Plotly Static Image Export](https://plotly.com/python/static-image-export/)
- [NetworkX Documentation](https://networkx.org/)
- [Dash Framework](https://dash.plotly.com/)

