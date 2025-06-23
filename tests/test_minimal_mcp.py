#!/usr/bin/env python3
"""
Test minimal MCP server to isolate the JSON-RPC issue.
"""

import asyncio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
import mcp.server.stdio
from typing import Any


# Create minimal server
server = Server("test-server")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List a simple tool."""
    return [
        types.Tool(
            name="hello",
            description="A simple hello tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name to greet"
                    }
                },
                "required": ["name"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    """Handle tool calls."""
    if arguments is None:
        arguments = {}
    
    if name == "hello":
        user_name = arguments.get("name", "World")
        return [
            types.TextContent(
                type="text",
                text=f"Hello, {user_name}!"
            )
        ]
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the minimal MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="test-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())