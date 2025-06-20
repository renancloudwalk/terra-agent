#!/usr/bin/env python3
"""
Terraform Agent MCP Server

A Model Context Protocol server that provides Terraform plan explanation capabilities.
Exposes tools for parsing and explaining Terraform plan output in plain English.
"""

import asyncio
import json
from typing import List, Optional
import mcp
from mcp import types
from mcp.server.stdio import stdio_server
from tools import parse_terraform_plan_text
from agent import build_context, BOT_PROMPT
from openai import OpenAI


async def list_tools() -> types.ListToolsResult:
    """List available MCP tools."""
    return types.ListToolsResult(
        tools=[
            types.Tool(
                name="terraform_explain",
                description="Parse and explain Terraform plan output in plain English for non-technical users",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plan_text": {
                            "type": "string",
                            "description": "The raw Terraform plan output text to analyze"
                        },
                        "user_preference": {
                            "type": "string", 
                            "enum": ["auto", "count_only", "full_summary"],
                            "description": "Response preference: 'auto' (ask if >5 changes), 'count_only' (brief), 'full_summary' (detailed)",
                            "default": "auto"
                        }
                    },
                    "required": ["plan_text"]
                }
            ),
            types.Tool(
                name="terraform_parse",
                description="Parse Terraform plan text and return structured resource changes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plan_text": {
                            "type": "string",
                            "description": "The raw Terraform plan output text to parse"
                        }
                    },
                    "required": ["plan_text"]
                }
            )
        ]
    )


async def call_tool(request: types.CallToolRequest) -> types.CallToolResult:
    """Handle MCP tool calls."""
    
    name = request.params.name
    arguments = request.params.arguments or {}
    
    if name == "terraform_parse":
        # Parse and return structured data
        plan_text = arguments.get("plan_text", "")
        resource_changes = parse_terraform_plan_text(plan_text)
        
        # Convert to JSON-serializable format
        changes_data = []
        for change in resource_changes:
            changes_data.append({
                "address": change.address,
                "type": change.type,
                "name": change.name,
                "actions": change.change.actions
            })
        
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps({
                        "resource_changes": changes_data,
                        "summary": {
                            "total_changes": len(changes_data),
                            "actions": _count_actions(resource_changes)
                        }
                    }, indent=2)
                )
            ]
        )
    
    elif name == "terraform_explain":
        # Parse and explain the plan
        plan_text = arguments.get("plan_text", "")
        user_preference = arguments.get("user_preference", "auto")
        
        resource_changes = parse_terraform_plan_text(plan_text)
        
        if not resource_changes:
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text", 
                        text="No resource changes found in the Terraform plan."
                    )
                ]
            )
        
        # Build tool output for MCP context
        tool_output = []
        for change in resource_changes:
            actions = change.change.actions
            action = actions[0] if actions else "no-op"
            tool_output.append(f"- {action} {change.address}")
        
        # Determine response type based on user preference and change count
        num_changes = len(resource_changes)
        
        if user_preference == "count_only" or (user_preference == "auto" and num_changes > 5):
            # For count-only or auto with >5 changes, provide brief summary
            if user_preference == "auto" and num_changes > 5:
                # Simulate the multi-turn conversation
                history = [
                    {"role": "user", "content": "Count only"},
                    {"role": "assistant", "content": "Count only or full summary?"}
                ]
            else:
                history = [{"role": "user", "content": "Count only"}]
            
            # Build MCP context
            context_json = build_context(BOT_PROMPT, tool_output, history)
            
            # Call OpenAI with MCP context
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": context_json}],
                temperature=0
            )
            
            explanation = response.choices[0].message.content
            
        else:
            # Full summary
            context_json = build_context(BOT_PROMPT, tool_output, [])
            
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": context_json}],
                temperature=0
            )
            
            explanation = response.choices[0].message.content
        
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=explanation
                )
            ]
        )
    
    else:
        raise ValueError(f"Unknown tool: {name}")


def _count_actions(resource_changes):
    """Count actions in resource changes."""
    action_counts = {}
    for change in resource_changes:
        for action in change.change.actions:
            action_counts[action] = action_counts.get(action, 0) + 1
    return action_counts


async def main():
    """Run the MCP server."""
    from mcp.server import Server
    
    # Create server instance
    server = Server("terraform-agent")
    
    # Register handlers
    @server.list_tools()
    async def handle_list_tools():
        return await list_tools()
    
    @server.call_tool()
    async def handle_call_tool(request):
        return await call_tool(request)
    
    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())