#!/usr/bin/env python3
"""
Fixed MCP Server for Terraform Agent with proper JSON-RPC handling.
"""

import asyncio
import json
import tempfile
import os
from typing import Any
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

from tools import parse_terraform_plan_text
from agent import run_agent_best_of_n, build_context, BOT_PROMPT
from openai import OpenAI


# Create the server instance
server = Server("terraform-agent")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    """
    return [
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
        ),
        types.Tool(
            name="terraform_explain_best_of_n",
            description="Generate N explanations and return the best one according to reward function",
            inputSchema={
                "type": "object",
                "properties": {
                    "plan_text": {
                        "type": "string",
                        "description": "The raw Terraform plan output text to analyze"
                    },
                    "n": {
                        "type": "integer",
                        "description": "Number of responses to generate (default: 3)",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    },
                    "user_preference": {
                        "type": "string", 
                        "enum": ["auto", "count_only", "full_summary"],
                        "description": "Response preference for multi-turn scenarios",
                        "default": "count_only"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature for response generation (default: 0.7)",
                        "default": 0.7,
                        "minimum": 0,
                        "maximum": 2
                    }
                },
                "required": ["plan_text"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    """
    Handle tool call requests.
    """
    if arguments is None:
        arguments = {}
    
    if name == "terraform_parse":
        # Parse and return structured data
        plan_text = arguments.get("plan_text", "")
        resource_changes = parse_terraform_plan_text(plan_text)
        
        # Convert to JSON-serializable format
        changes_data = []
        for change in resource_changes:
            changes_data.append({
                "address": change.address,
                "mode": change.mode,
                "type": change.type,
                "name": change.name,
                "provider_name": change.provider_name,
                "actions": change.change.actions
            })
        
        def _count_actions(resource_changes):
            """Count actions in resource changes."""
            action_counts = {}
            for change in resource_changes:
                for action in change.change.actions:
                    action_counts[action] = action_counts.get(action, 0) + 1
            return action_counts
        
        return [
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
    
    elif name == "terraform_explain":
        # Parse and explain the plan
        plan_text = arguments.get("plan_text", "")
        user_preference = arguments.get("user_preference", "auto")
        
        resource_changes = parse_terraform_plan_text(plan_text)
        
        if not resource_changes:
            return [
                types.TextContent(
                    type="text", 
                    text="No resource changes found in the Terraform plan."
                )
            ]
        
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
            
            # Build context and get explanation
            context_json = build_context(BOT_PROMPT, tool_output, history)
            
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": context_json}],
                temperature=0
            )
            
            explanation = response.choices[0].message.content
        else:
            # Full summary
            history = []
            context_json = build_context(BOT_PROMPT, tool_output, history)
            
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": context_json}],
                temperature=0
            )
            
            explanation = response.choices[0].message.content
        
        return [
            types.TextContent(
                type="text",
                text=explanation
            )
        ]
    
    elif name == "terraform_explain_best_of_n":
        # Best-of-N explanation generation
        plan_text = arguments.get("plan_text", "")
        n = arguments.get("n", 3)
        user_preference = arguments.get("user_preference", "count_only")
        temperature = arguments.get("temperature", 0.7)
        
        # Write plan to temporary file for processing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(plan_text)
            temp_plan_path = f.name
        
        try:
            # Determine user_reply based on preference
            user_reply = None
            if user_preference in ["count_only", "auto"]:
                user_reply = "Count only"
            
            # Run Best-of-N
            best_response, best_score, all_responses = run_agent_best_of_n(
                plan_path=temp_plan_path,
                n=n,
                user_reply=user_reply,
                temperature=temperature
            )
            
            # Format detailed results
            results = {
                "best_response": best_response,
                "best_score": f"{best_score}/100",
                "total_attempts": n,
                "all_responses": [
                    {
                        "response": resp,
                        "score": f"{score}/100"
                    }
                    for resp, score in all_responses
                ]
            }
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Best-of-{n} Result:\n\n{best_response}\n\nScore: {best_score}/100\n\nDetailed Results:\n{json.dumps(results, indent=2)}"
                )
            ]
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_plan_path):
                os.unlink(temp_plan_path)
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="terraform-agent",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())