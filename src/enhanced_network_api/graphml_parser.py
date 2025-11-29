
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

def parse_graphml_topology(file_path: str) -> Dict[str, Any]:
    """
    Parse a GraphML topology file and return a scene dictionary 
    compatible with the Enhanced Network API.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # GraphML namespace
        ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
        
        nodes = []
        links = []
        
        # Find the graph element
        graph = root.find('graphml:graph', ns)
        if graph is None:
            # Try without namespace if not found
            graph = root.find('graph')
            
        if graph is None:
            logger.error("No graph element found in GraphML file")
            return {"nodes": [], "links": []}
            
        # Parse nodes
        for node_elem in graph.findall('graphml:node', ns):
            node_data = node_elem.attrib
            node_id = node_data.get('id')
            
            # Extract attributes directly from the node element attributes
            # (The provided GraphML uses attributes on the node tag itself, not <data> sub-elements)
            
            # Map GraphML attributes to our internal schema
            node = {
                "id": node_id,
                "name": node_data.get('name', node_id),
                "type": node_data.get('type', 'unknown'),
                "vendor": node_data.get('vendor'),
                "model": node_data.get('model'),
                "ip": node_data.get('ip'),
                "serial": node_data.get('serial'),
                "status": node_data.get('status', 'online'),
                "role": node_data.get('type') # Use type as role for now
            }
            
            # Filter out None values
            node = {k: v for k, v in node.items() if v is not None}
            nodes.append(node)
            
        # Parse edges
        for edge_elem in graph.findall('graphml:edge', ns):
            edge_data = edge_elem.attrib
            
            link = {
                "id": edge_data.get('id'),
                "from": edge_data.get('source'),
                "to": edge_data.get('target'),
                "type": edge_data.get('type'),
                "status": "up" # Default status
            }
            
            # Parse ports if available (stored as string representation of list)
            ports_str = edge_data.get('ports')
            if ports_str:
                try:
                    # Simple cleanup for the string format "['portname']"
                    link["ports"] = ports_str.replace("[", "").replace("]", "").replace("'", "").split(", ")
                except Exception:
                    pass
                    
            links.append(link)
            
        return {"nodes": nodes, "links": links}
        
    except Exception as e:
        logger.error(f"Failed to parse GraphML file {file_path}: {e}")
        return {"nodes": [], "links": []}
