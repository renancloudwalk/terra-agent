#!/usr/bin/env python3
"""
Working MCP Server - simplified structure based on MCP 1.9.4 patterns.
"""

import asyncio
import json
import tempfile
import os
from typing import Any
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server


# Import our agent functions
from tools import parse_terraform_plan_text
from agent import run_agent_best_of_n, build_context, BOT_PROMPT
from openai import OpenAI


async def main():
    """Main entry point for the MCP server."""
    
    # Create the server
    server = Server("terraform-agent")
    
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools."""
        return [
            types.Tool(
                name="terraform_explain",
                description="Parse and explain Terraform plan output in plain English",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plan_text": {
                            "type": "string",
                            "description": "The raw Terraform plan output text"
                        },
                        "user_preference": {
                            "type": "string",
                            "enum": ["auto", "count_only", "full_summary"],
                            "default": "auto"
                        }
                    },
                    "required": ["plan_text"]
                }
            ),
            types.Tool(
                name="terraform_explain_best_of_n",
                description="Generate multiple explanations and return the best one",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plan_text": {
                            "type": "string",
                            "description": "The raw Terraform plan output text"
                        },
                        "n": {
                            "type": "integer",
                            "default": 3,
                            "minimum": 1,
                            "maximum": 10
                        },
                        "temperature": {
                            "type": "number",
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
        """Handle tool execution."""
        if arguments is None:
            arguments = {}
        
        if name == "terraform_explain":
            plan_text = arguments.get("plan_text", "")
            user_preference = arguments.get("user_preference", "count_only")
            
            # Parse plan
            resource_changes = parse_terraform_plan_text(plan_text)
            if not resource_changes:
                return [types.TextContent(type="text", text="No changes found")]
            
            # Build context
            tool_output = [f"- {change.change.actions[0] if change.change.actions else 'no-op'} {change.address}" 
                          for change in resource_changes]
            
            # Get explanation
            history = [{"role": "user", "content": "Count only"}] if user_preference == "count_only" else []
            context_json = build_context(BOT_PROMPT, tool_output, history)
            
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": context_json}],
                temperature=0
            )
            
            return [types.TextContent(type="text", text=response.choices[0].message.content)]
        
        elif name == "terraform_explain_best_of_n":
            plan_text = arguments.get("plan_text", "")
            n = arguments.get("n", 3)
            temperature = arguments.get("temperature", 0.7)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(plan_text)
                temp_path = f.name
            
            try:
                # Run Best-of-N
                best_response, best_score, all_responses = run_agent_best_of_n(
                    plan_path=temp_path,
                    n=n,
                    user_reply="Count only",
                    temperature=temperature
                )
                
                # Format result
                result = f"Best-of-{n} Result:\n\n{best_response}\n\nScore: {best_score}/100\n\n"
                result += f"All attempts:\n"
                for i, (resp, score) in enumerate(all_responses, 1):
                    result += f"{i}. {resp} ({score}/100)\n"
                
                return [types.TextContent(type="text", text=result)]
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    # Run the server
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