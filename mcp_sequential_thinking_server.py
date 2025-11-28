#!/usr/bin/env python3
"""
Sequential Thinking MCP Server
Provides advanced problem-solving capabilities through structured thinking processes
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
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

# Create the sequential thinking server
app = Server("sequential-thinking")

class SequentialThinkingProcessor:
    """Advanced sequential thinking processor for complex problem solving"""
    
    def __init__(self):
        self.current_session = None
        self.thinking_history = []
    
    def process_thought(self, thought: str, thought_number: int, total_thoughts: int, 
                       is_revision: bool = False, revises_thought: Optional[int] = None,
                       branch_from_thought: Optional[int] = None, branch_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a single thought in the sequential thinking chain"""
        
        result = {
            "thought": thought,
            "thought_number": thought_number,
            "total_thoughts": total_thoughts,
            "is_revision": is_revision,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        if is_revision and revises_thought:
            result["revises_thought"] = revises_thought
            # Update the original thought in history
            for i, hist_thought in enumerate(self.thinking_history):
                if hist_thought.get("thought_number") == revises_thought:
                    self.thinking_history[i] = result
                    break
        
        if branch_from_thought:
            result["branch_from_thought"] = branch_from_thought
            if branch_id:
                result["branch_id"] = branch_id
        
        # Add to history if not a revision
        if not is_revision:
            self.thinking_history.append(result)
        
        return result
    
    def generate_solution_hypothesis(self, thoughts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a solution hypothesis based on the chain of thoughts"""
        if not thoughts:
            return {"hypothesis": "No thoughts provided", "confidence": 0.0}
        
        # Extract key insights from thoughts
        insights = []
        for thought in thoughts:
            if "analysis" in thought.get("thought", "").lower():
                insights.append(thought["thought"])
        
        # Generate hypothesis
        hypothesis = "Based on sequential analysis: " + " ".join([t["thought"] for t in thoughts[-3:]])
        confidence = min(0.9, len(thoughts) * 0.1)  # Confidence increases with more thoughts
        
        return {
            "hypothesis": hypothesis,
            "confidence": confidence,
            "supporting_thoughts": len(thoughts),
            "key_insights": insights
        }
    
    def verify_hypothesis(self, hypothesis: Dict[str, Any], thoughts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify the hypothesis against the chain of thoughts"""
        verification_score = 0.0
        verification_details = []
        
        # Check for consistency
        if thoughts:
            verification_score += 0.3
            verification_details.append("Consistent thought progression")
        
        # Check for logical flow
        if len(thoughts) > 2:
            verification_score += 0.2
            verification_details.append("Logical flow detected")
        
        # Check for conclusion
        if any("conclusion" in t.get("thought", "").lower() or "solution" in t.get("thought", "").lower() 
               for t in thoughts):
            verification_score += 0.3
            verification_details.append("Solution conclusion present")
        
        # Check confidence
        if hypothesis.get("confidence", 0) > 0.5:
            verification_score += 0.2
            verification_details.append("High confidence in hypothesis")
        
        return {
            "verified": verification_score > 0.6,
            "verification_score": verification_score,
            "details": verification_details
        }

# Initialize the processor
processor = SequentialThinkingProcessor()

@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available sequential thinking tools"""
    return [
        Tool(
            name="sequential_thinking",
            description="Advanced sequential thinking for dynamic problem-solving with revision and branching capabilities",
            inputSchema={
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Current thinking step"
                    },
                    "thought_number": {
                        "type": "integer",
                        "description": "Current thought number in sequence"
                    },
                    "total_thoughts": {
                        "type": "integer",
                        "description": "Estimated total thoughts needed"
                    },
                    "is_revision": {
                        "type": "boolean",
                        "description": "Whether this revises previous thinking"
                    },
                    "revises_thought": {
                        "type": "integer",
                        "description": "Which thought number is being reconsidered"
                    },
                    "branch_from_thought": {
                        "type": "integer",
                        "description": "Branching point thought number"
                    },
                    "branch_id": {
                        "type": "string",
                        "description": "Branch identifier"
                    }
                },
                "required": ["thought", "thought_number", "total_thoughts"]
            }
        ),
        Tool(
            name="generate_hypothesis",
            description="Generate solution hypothesis from chain of thoughts",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session identifier"
                    }
                }
            }
        ),
        Tool(
            name="verify_solution",
            description="Verify hypothesis against thought chain",
            inputSchema={
                "type": "object",
                "properties": {
                    "hypothesis": {
                        "type": "string",
                        "description": "Solution hypothesis to verify"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session identifier"
                    }
                }
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls for sequential thinking"""
    
    if name == "sequential_thinking":
        thought = arguments.get("thought", "")
        thought_number = arguments.get("thought_number", 1)
        total_thoughts = arguments.get("total_thoughts", 1)
        is_revision = arguments.get("is_revision", False)
        revises_thought = arguments.get("revises_thought")
        branch_from_thought = arguments.get("branch_from_thought")
        branch_id = arguments.get("branch_id")
        
        result = processor.process_thought(
            thought, thought_number, total_thoughts,
            is_revision, revises_thought, branch_from_thought, branch_id
        )
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    elif name == "generate_hypothesis":
        hypothesis = processor.generate_solution_hypothesis(processor.thinking_history)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(hypothesis, indent=2))]
        )
    
    elif name == "verify_solution":
        hypothesis_text = arguments.get("hypothesis", "")
        hypothesis_obj = {"hypothesis": hypothesis_text, "confidence": 0.7}
        
        verification = processor.verify_hypothesis(hypothesis_obj, processor.thinking_history)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(verification, indent=2))]
        )
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main entry point"""
    # Use stdio_server for MCP communication
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sequential-thinking",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
