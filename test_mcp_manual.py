#!/usr/bin/env python3
"""
Manual MCP Server Testing Script

Tests the MCP server by simulating JSON-RPC calls over stdio.
This is useful for debugging and validating MCP server functionality.
"""

import json
import subprocess
import sys
import time


def send_mcp_request(process, request):
    """Send a JSON-RPC request to the MCP server."""
    request_json = json.dumps(request) + '\n'
    process.stdin.write(request_json.encode())
    process.stdin.flush()
    
    # Read response
    response_line = process.stdout.readline().decode().strip()
    if response_line:
        return json.loads(response_line)
    return None


def test_mcp_server():
    """Test MCP server functionality."""
    print("🧪 Testing MCP Server")
    print("=" * 40)
    
    # Start MCP server process
    process = subprocess.Popen(
        ['python', 'mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False  # Use binary mode for better control
    )
    
    try:
        # Test 1: Initialize
        print("📡 Test 1: Initialize MCP connection")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = send_mcp_request(process, init_request)
        if response:
            print(f"✅ Initialize response: {response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
        else:
            print("❌ No initialize response")
        
        # Test 2: List tools
        print("\n📋 Test 2: List available tools")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        response = send_mcp_request(process, list_tools_request)
        if response and 'result' in response:
            tools = response['result'].get('tools', [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
        else:
            print("❌ No tools list response")
        
        # Test 3: Call terraform_explain
        print("\n🔧 Test 3: Call terraform_explain tool")
        with open('fixtures/plan_small.txt', 'r') as f:
            plan_text = f.read()
        
        explain_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "terraform_explain",
                "arguments": {
                    "plan_text": plan_text,
                    "user_preference": "count_only"
                }
            }
        }
        
        response = send_mcp_request(process, explain_request)
        if response and 'result' in response:
            content = response['result'].get('content', [])
            if content:
                explanation = content[0].get('text', 'No text content')
                print(f"✅ Explanation: {explanation}")
            else:
                print("❌ No content in response")
        else:
            print(f"❌ No explanation response: {response}")
        
        # Test 4: Call terraform_explain_best_of_n
        print("\n🎯 Test 4: Call terraform_explain_best_of_n tool")
        best_of_n_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "terraform_explain_best_of_n",
                "arguments": {
                    "plan_text": plan_text,
                    "n": 3,
                    "temperature": 0.8
                }
            }
        }
        
        response = send_mcp_request(process, best_of_n_request)
        if response and 'result' in response:
            content = response['result'].get('content', [])
            if content:
                result_text = content[0].get('text', 'No text content')
                print(f"✅ Best-of-N result:")
                print(result_text[:200] + "..." if len(result_text) > 200 else result_text)
            else:
                print("❌ No content in Best-of-N response")
        else:
            print(f"❌ No Best-of-N response: {response}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        
    finally:
        # Clean up
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("\n🏁 MCP server testing complete")


def test_mcp_with_curl():
    """Show how to test MCP server with curl (doesn't work but shows the concept)."""
    print("\n💡 Note: MCP servers use stdio, not HTTP.")
    print("To test manually, you can:")
    print("1. Run: python mcp_server.py")
    print("2. Send JSON-RPC over stdin")
    print("3. Read responses from stdout")
    print("\nExample JSON-RPC request:")
    example_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list"
    }
    print(json.dumps(example_request, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--curl-info":
        test_mcp_with_curl()
    else:
        try:
            test_mcp_server()
        except KeyboardInterrupt:
            print("\n🛑 Testing interrupted")
        except Exception as e:
            print(f"❌ Testing failed: {e}")
            print("\nMake sure:")
            print("- OPENAI_API_KEY is set")
            print("- mcp_server.py exists and is executable")
            print("- fixtures/plan_small.txt exists")