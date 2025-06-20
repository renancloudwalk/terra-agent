#!/usr/bin/env python3
"""
Simple MCP Server Test

Tests the MCP server by importing and calling functions directly.
This bypasses the stdio protocol complexity for easier testing.
"""

import asyncio
import json
from mcp import types
from mcp_server import list_tools, call_tool


async def test_mcp_functionality():
    """Test MCP server functions directly."""
    print("🧪 Testing MCP Server Functions")
    print("=" * 40)
    
    try:
        # Test 1: List tools
        print("📋 Test 1: List available tools")
        tools_result = await list_tools()
        tools = tools_result.tools
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        
        # Test 2: Test terraform_explain
        print("\n🔧 Test 2: Test terraform_explain")
        with open('fixtures/plan_small.txt', 'r') as f:
            plan_text = f.read()
        
        request = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(
                name="terraform_explain",
                arguments={
                    "plan_text": plan_text,
                    "user_preference": "count_only"
                }
            )
        )
        
        result = await call_tool(request)
        explanation = result.content[0].text
        print(f"✅ terraform_explain result: {explanation}")
        
        # Test 3: Test terraform_parse
        print("\n📊 Test 3: Test terraform_parse")
        request = types.CallToolRequest(
            method="tools/call", 
            params=types.CallToolRequestParams(
                name="terraform_parse",
                arguments={
                    "plan_text": plan_text
                }
            )
        )
        
        result = await call_tool(request)
        parse_result = result.content[0].text
        parsed_data = json.loads(parse_result)
        print(f"✅ terraform_parse found {parsed_data['summary']['total_changes']} changes")
        
        # Test 4: Test terraform_explain_best_of_n
        print("\n🎯 Test 4: Test terraform_explain_best_of_n")
        request = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(
                name="terraform_explain_best_of_n", 
                arguments={
                    "plan_text": plan_text,
                    "n": 3,
                    "temperature": 0.7
                }
            )
        )
        
        result = await call_tool(request)
        best_of_n_result = result.content[0].text
        print("✅ terraform_explain_best_of_n completed:")
        # Show first line of result
        first_line = best_of_n_result.split('\n')[0]
        print(f"   {first_line}")
        
        print("\n🎉 All MCP function tests passed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


def test_manual_mcp_commands():
    """Show manual testing commands."""
    print("\n💡 Manual MCP Server Testing")
    print("=" * 40)
    print("To test the MCP server manually:")
    print()
    print("1. Start server in one terminal:")
    print("   make mcp-server")
    print()
    print("2. In another terminal, send JSON-RPC:")
    print("   echo '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}' | python mcp_server.py")
    print()
    print("3. Or test with Claude Desktop:")
    print("   - Add to Claude Desktop config")
    print("   - Use tools in conversation")
    print()
    print("4. Or use our function testing:")
    print("   make test-mcp-functions")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual-info":
        test_manual_mcp_commands()
    else:
        try:
            asyncio.run(test_mcp_functionality())
        except Exception as e:
            print(f"❌ Failed to test MCP functionality: {e}")
            print("\nThis might be due to missing MCP dependencies.")
            print("The MCP server is designed to work with Claude Desktop integration.")
            print("\nFor basic functionality testing, use:")
            print("  make demo")
            print("  make test")
            print("  make best")