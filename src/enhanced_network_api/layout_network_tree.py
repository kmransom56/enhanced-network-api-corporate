"""
Network Tree Layout - Matches the specific Fortinet topology diagram layout
Internet → Fortigate → (FortiSwitch | Wireless AP) → End Devices
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict


def calculate_network_tree_layout(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    spacing: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """
    Calculate positions for network devices in a tree layout matching the diagram:
    
    Layout:
    - Layer 1 (top): Internet (center)
    - Layer 2: Fortigate (center, below Internet)
    - Layer 3: FortiSwitch (left) and Wireless AP (right)
    - Layer 4: End devices (below their parent)
    
    Args:
        nodes: List of device nodes
        links: List of connection links
        spacing: Optional spacing configuration
        
    Returns:
        List of nodes with position data added
    """
    if spacing is None:
        spacing = {
            'vertical': 8.0,      # Y spacing between layers
            'horizontal': 6.0,    # X spacing between branches
            'device': 4.0,        # Spacing between devices in same group
        }
    
    # Build node map and identify device types
    node_map = {node.get('id') or node.get('name'): node for node in nodes}
    
    # Identify devices by type
    internet_nodes = []
    fortigate_nodes = []
    switch_nodes = []
    ap_nodes = []
    wired_clients = []
    wireless_clients = []
    other_nodes = []
    
    for node in nodes:
        node_id = node.get('id') or node.get('name')
        node_type = (node.get('type') or node.get('role') or '').lower()
        connection_type = (node.get('connection_type') or '').lower()
        
        if 'internet' in node_type or 'wan' in node_type:
            internet_nodes.append(node_id)
        elif 'fortigate' in node_type or 'firewall' in node_type or 'gateway' in node_type:
            fortigate_nodes.append(node_id)
        elif 'fortiswitch' in node_type or ('switch' in node_type and 'forti' in node_type):
            switch_nodes.append(node_id)
        elif 'fortiap' in node_type or 'access_point' in node_type or 'ap' in node_type or 'wireless' in node_type:
            ap_nodes.append(node_id)
        elif connection_type == 'wifi' or 'wireless' in node_type or node.get('ssid'):
            wireless_clients.append(node_id)
        elif connection_type == 'ethernet' or 'wired' in node_type:
            wired_clients.append(node_id)
        elif 'client' in node_type or 'endpoint' in node_type or 'device' in node_type:
            # Default to wired if unclear
            wired_clients.append(node_id)
        else:
            other_nodes.append(node_id)
    
    # Build parent-child relationships from links
    children_by_parent = defaultdict(list)
    parent_by_child = {}
    
    for link in links:
        source = link.get('from') or link.get('source') or link.get('source_id')
        target = link.get('to') or link.get('target') or link.get('target_id')
        
        if not source or not target:
            continue
        
        # Determine parent-child relationship based on device types
        source_type = (node_map.get(source, {}).get('type') or node_map.get(source, {}).get('role') or '').lower()
        target_type = (node_map.get(target, {}).get('type') or node_map.get(target, {}).get('role') or '').lower()
        
        # Internet is always parent
        if 'internet' in source_type:
            children_by_parent[source].append(target)
            parent_by_child[target] = source
        elif 'internet' in target_type:
            children_by_parent[target].append(source)
            parent_by_child[source] = target
        # Fortigate is parent to switches and APs
        elif 'fortigate' in source_type or 'firewall' in source_type:
            if 'switch' in target_type or 'ap' in target_type or 'access' in target_type:
                children_by_parent[source].append(target)
                parent_by_child[target] = source
        elif 'fortigate' in target_type or 'firewall' in target_type:
            if 'switch' in source_type or 'ap' in source_type or 'access' in source_type:
                children_by_parent[target].append(source)
                parent_by_child[source] = target
        # Switches and APs are parents to clients
        elif 'switch' in source_type:
            if 'client' in target_type or 'endpoint' in target_type or 'device' in target_type:
                children_by_parent[source].append(target)
                parent_by_child[target] = source
        elif 'switch' in target_type:
            if 'client' in source_type or 'endpoint' in source_type or 'device' in source_type:
                children_by_parent[target].append(source)
                parent_by_child[source] = target
        elif 'ap' in source_type or 'access' in source_type or 'wireless' in source_type:
            if 'client' in target_type or 'endpoint' in target_type or 'device' in target_type:
                children_by_parent[source].append(target)
                parent_by_child[target] = source
        elif 'ap' in target_type or 'access' in target_type or 'wireless' in target_type:
            if 'client' in source_type or 'endpoint' in source_type or 'device' in source_type:
                children_by_parent[target].append(source)
                parent_by_child[source] = target
    
    # Calculate positions
    positions = {}
    
    # Layer 1: Internet (top center)
    y_internet = spacing['vertical'] * 3
    for i, node_id in enumerate(internet_nodes):
        positions[node_id] = {
            'x': 0.0,
            'y': y_internet,
            'z': 0.0
        }
    
    # Layer 2: Fortigate (center, below Internet)
    y_fortigate = spacing['vertical'] * 2
    for i, node_id in enumerate(fortigate_nodes):
        positions[node_id] = {
            'x': 0.0,
            'y': y_fortigate,
            'z': 0.0
        }
    
    # Layer 3: FortiSwitch (left) and Wireless AP (right)
    y_layer3 = spacing['vertical']
    x_left = -spacing['horizontal']  # Switch on left
    x_right = spacing['horizontal']  # AP on right
    
    # Position switches on the left
    for i, node_id in enumerate(switch_nodes):
        positions[node_id] = {
            'x': x_left,
            'y': y_layer3,
            'z': 0.0
        }
    
    # Position APs on the right
    for i, node_id in enumerate(ap_nodes):
        positions[node_id] = {
            'x': x_right,
            'y': y_layer3,
            'z': 0.0
        }
    
    # Layer 4: End devices (below their parent)
    y_clients = 0.0
    
    # Wired clients below switch
    switch_parent = switch_nodes[0] if switch_nodes else None
    for i, node_id in enumerate(wired_clients):
        # Check if this client is connected to a switch
        parent = parent_by_child.get(node_id)
        if parent and parent in switch_nodes:
            switch_idx = switch_nodes.index(parent)
            x_pos = x_left + (i - len(wired_clients) / 2) * spacing['device']
        else:
            # Default to left side if no specific parent
            x_pos = x_left + (i - len(wired_clients) / 2) * spacing['device']
        
        positions[node_id] = {
            'x': x_pos,
            'y': y_clients,
            'z': 0.0
        }
    
    # Wireless clients below AP
    ap_parent = ap_nodes[0] if ap_nodes else None
    for i, node_id in enumerate(wireless_clients):
        # Check if this client is connected to an AP
        parent = parent_by_child.get(node_id)
        if parent and parent in ap_nodes:
            ap_idx = ap_nodes.index(parent)
            x_pos = x_right + (i - len(wireless_clients) / 2) * spacing['device']
        else:
            # Default to right side if no specific parent
            x_pos = x_right + (i - len(wireless_clients) / 2) * spacing['device']
        
        positions[node_id] = {
            'x': x_pos,
            'y': y_clients,
            'z': 0.0
        }
    
    # Handle other nodes (place them in a reasonable location)
    for i, node_id in enumerate(other_nodes):
        positions[node_id] = {
            'x': (i % 3 - 1) * spacing['horizontal'],
            'y': spacing['vertical'] * (1 - (i // 3) * 0.5),
            'z': 0.0
        }
    
    # Apply positions to nodes
    result_nodes = []
    for node in nodes:
        node_id = node.get('id') or node.get('name')
        node_copy = node.copy()
        
        if node_id in positions:
            node_copy['position'] = positions[node_id]
        else:
            # Default position if not assigned
            node_copy['position'] = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        
        result_nodes.append(node_copy)
    
    return result_nodes


def apply_network_tree_layout_2d(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    width: float = 800,
    height: float = 600
) -> List[Dict[str, Any]]:
    """
    Calculate 2D positions for network devices (for SVG/Canvas rendering).
    
    Args:
        nodes: List of device nodes
        links: List of connection links
        width: Canvas width
        height: Canvas height
        
    Returns:
        List of nodes with 2D position data (x, y)
    """
    spacing = {
        'vertical': height / 6,
        'horizontal': width / 4,
        'device': width / 8,
    }
    
    # Use 3D layout but convert to 2D
    positioned_nodes = calculate_network_tree_layout(nodes, links, spacing)
    
    # Convert 3D positions to 2D (use x and y, ignore z)
    for node in positioned_nodes:
        pos_3d = node.get('position', {})
        node['x'] = pos_3d.get('x', 0) + width / 2  # Center horizontally
        node['y'] = height - (pos_3d.get('y', 0) + height / 2)  # Flip Y for screen coordinates
    
    return positioned_nodes

