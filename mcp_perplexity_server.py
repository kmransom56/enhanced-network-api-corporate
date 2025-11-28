#!/usr/bin/env python3
"""
Perplexity-inspired MCP Server
Provides advanced knowledge retrieval and synthesis capabilities
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

# Create the perplexity server
app = Server("perplexity")

class KnowledgeSynthesizer:
    """Advanced knowledge synthesis and retrieval system"""
    
    def __init__(self):
        self.knowledge_base = {
            "fortinet": {
                "fortigate": {
                    "description": "Next-generation firewall (NGFW) providing advanced threat protection",
                    "key_features": ["Threat Protection", "SSL Inspection", "Application Control", "IPS"],
                    "models": ["FortiGate 30E", "FortiGate 60E", "FortiGate 100E", "FortiGate 200E", "FortiGate 600E"],
                    "deployment": "Edge/perimeter security, internal network segmentation"
                },
                "fortiswitch": {
                    "description": "Secure access switches with integrated security",
                    "key_features": ["FortiLink Integration", "MAC-Based Authentication", "Dynamic VLAN Assignment"],
                    "models": ["FortiSwitch 100E", "FortiSwitch 200E", "FortiSwitch 448E", "FortiSwitch 148E"],
                    "deployment": "Access layer switching, PoE deployment for APs and cameras"
                },
                "fortiap": {
                    "description": "Wireless access points with centralized management",
                    "key_features": ["Dual-band WiFi", "MU-MIMO", "Beamforming", "Centralized Management"],
                    "models": ["FortiAP 23E", "FortiAP 432F", "FortiAP 443K"],
                    "deployment": "Enterprise WiFi coverage, high-density environments"
                }
            },
            "networking": {
                "topology": {
                    "star": "Central hub with spoke connections",
                    "mesh": "Multiple interconnected nodes",
                    "hybrid": "Combination of star and mesh",
                    "hierarchical": "Multi-level tree structure"
                },
                "protocols": {
                    "fortilink": "Proprietary protocol for FortiGate-FortiSwitch integration",
                    "wifi": "Wireless communication standards (802.11ac, 802.11ax)",
                    "ethernet": "Wired networking standard"
                }
            }
        }
    
    def search_knowledge(self, query: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant information"""
        query_lower = query.lower()
        results = []
        
        # Search through knowledge base
        for category, items in self.knowledge_base.items():
            for item_name, item_data in items.items():
                relevance_score = 0
                
                # Check title match
                if query_lower in item_name.lower():
                    relevance_score += 0.5
                
                # Check description match
                if item_data.get("description"):
                    desc_lower = item_data["description"].lower()
                    if query_lower in desc_lower:
                        relevance_score += 0.3
                    # Check partial matches
                    for word in query_lower.split():
                        if word in desc_lower:
                            relevance_score += 0.1
                
                # Check features match
                if "key_features" in item_data:
                    for feature in item_data["key_features"]:
                        if query_lower in feature.lower():
                            relevance_score += 0.2
                
                # Check models match
                if "models" in item_data:
                    for model in item_data["models"]:
                        if query_lower in model.lower():
                            relevance_score += 0.2
                
                if relevance_score > 0:
                    result = {
                        "title": f"{category.title()} - {item_name.title()}",
                        "content": item_data.get("description", ""),
                        "relevance": relevance_score,
                        "category": category,
                        "item": item_name,
                        "details": item_data
                    }
                    results.append(result)
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)
        
        return results[:5]  # Return top 5 results
    
    def synthesize_answer(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize a comprehensive answer from search results"""
        if not search_results:
            return {
                "answer": f"I couldn't find specific information about '{query}' in my knowledge base.",
                "confidence": 0.0,
                "sources": []
            }
        
        # Build answer from top results
        answer_parts = []
        sources = []
        confidence = 0
        
        for result in search_results[:3]:  # Use top 3 results
            if result["relevance"] > 0.3:
                answer_parts.append(result["content"])
                sources.append(result["title"])
                confidence += result["relevance"] * 0.3
        
        # Combine answer parts
        if answer_parts:
            answer = f"Based on my knowledge: {' '.join(answer_parts)}"
            
            # Add specific details if available
            if search_results[0]["details"].get("key_features"):
                features = search_results[0]["details"]["key_features"]
                answer += f" Key features include: {', '.join(features[:3])}."
            
            if search_results[0]["details"].get("models"):
                models = search_results[0]["details"]["key_features"]
                answer += f" Available models: {', '.join(models[:3])}."
        else:
            answer = f"I found some information about '{query}', but it may not be directly relevant."
        
        confidence = min(confidence, 0.95)  # Cap confidence at 95%
        
        return {
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "related_topics": [r["title"] for r in search_results[1:4]]
        }
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract entities from text"""
        entities = []
        
        # Known entity patterns
        entity_patterns = {
            "fortigate": r"\b(FortiGate-\d+[A-Z]?)\b",
            "fortiswitch": r"\b(FortiSwitch-\d+[A-Z]?)\b",
            "fortiap": r"\b(FortiAP-\d+[A-Z]?)\b",
            "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "mac_address": r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"
        }
        
        for entity_type, pattern in entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    "type": entity_type,
                    "value": match,
                    "context": text[max(0, text.find(match)-20):text.find(match)+len(match)+20]
                })
        
        return entities
    
    def generate_insights(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Generate insights about the query"""
        insights = []
        
        # Analyze query type
        query_lower = query.lower()
        
        if "troubleshoot" in query_lower or "problem" in query_lower:
            insights.append("This appears to be a troubleshooting request")
        elif "configure" in query_lower or "setup" in query_lower:
            insights.append("This appears to be a configuration request")
        elif "compare" in query_lower or "vs" in query_lower:
            insights.append("This appears to be a comparison request")
        elif "topology" in query_lower or "network" in query_lower:
            insights.append("This appears to be related to network topology")
        
        # Extract entities
        entities = self.extract_entities(query)
        if context:
            entities.extend(self.extract_entities(context))
        
        # Generate context-specific insights
        if entities:
            entity_types = list(set(e["type"] for e in entities))
            insights.append(f"Detected entities: {', '.join(entity_types)}")
        
        if "fortigate" in query_lower and "fortiswitch" in query_lower:
            insights.append("Query involves FortiGate-FortiSwitch integration")
        elif "fortiap" in query_lower:
            insights.append("Query involves wireless access points")
        
        return {
            "insights": insights,
            "entities": entities,
            "query_type": self._classify_query(query),
            "complexity": self._assess_complexity(query)
        }
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["what", "describe", "explain"]):
            return "informational"
        elif any(word in query_lower for word in ["how", "configure", "setup"]):
            return "procedural"
        elif any(word in query_lower for word in ["why", "troubleshoot", "error"]):
            return "diagnostic"
        elif any(word in query_lower for word in ["compare", "vs", "difference"]):
            return "comparative"
        else:
            return "general"
    
    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity"""
        complexity_indicators = [
            "multiple", "several", "various", "complex", "advanced",
            "integration", "architecture", "design", "deployment"
        ]
        
        query_lower = query.lower()
        indicator_count = sum(1 for indicator in complexity_indicators if indicator in query_lower)
        
        if indicator_count >= 3:
            return "high"
        elif indicator_count >= 1:
            return "medium"
        else:
            return "low"

# Initialize the synthesizer
synthesizer = KnowledgeSynthesizer()

@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available perplexity tools"""
    return [
        Tool(
            name="search_knowledge",
            description="Search knowledge base for relevant information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context for search"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="synthesize_answer",
            description="Synthesize comprehensive answer from search results",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Original query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum search results to use",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="generate_insights",
            description="Generate insights and analysis about the query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query to analyze"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="extract_entities",
            description="Extract entities from text (IP addresses, MAC addresses, device models)",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to extract entities from"
                    }
                },
                "required": ["text"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls for perplexity"""
    
    if name == "search_knowledge":
        query = arguments.get("query", "")
        context = arguments.get("context")
        
        results = synthesizer.search_knowledge(query, context)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(results, indent=2))]
        )
    
    elif name == "synthesize_answer":
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 5)
        
        search_results = synthesizer.search_knowledge(query)
        answer = synthesizer.synthesize_answer(query, search_results[:max_results])
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(answer, indent=2))]
        )
    
    elif name == "generate_insights":
        query = arguments.get("query", "")
        context = arguments.get("context")
        
        insights = synthesizer.generate_insights(query, context)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(insights, indent=2))]
        )
    
    elif name == "extract_entities":
        text = arguments.get("text", "")
        
        entities = synthesizer.extract_entities(text)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(entities, indent=2))]
        )
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main entry point"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="perplexity",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
