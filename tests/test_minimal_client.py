#!/usr/bin/env python3
"""
Test client for minimal MCP server.
"""

import json
import subprocess
import time


def test_minimal_mcp():
    """Test the minimal MCP server."""
    print("🧪 Testing Minimal MCP Server")
    print("=" * 40)
    
    process = subprocess.Popen(
        ['uv', 'run', 'python', 'test_minimal_mcp.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        
        response = process.stdout.readline()
        init_response = json.loads(response.strip())
        print(f"✅ Init: {init_response['result']['serverInfo']['name']}")
        
        # Send initialized
        initialized = {"jsonrpc": "2.0", "method": "initialized"}
        process.stdin.write(json.dumps(initialized) + '\n')
        process.stdin.flush()
        time.sleep(0.5)
        
        # List tools
        list_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        process.stdin.write(json.dumps(list_request) + '\n')
        process.stdin.flush()
        
        response = process.stdout.readline()
        list_response = json.loads(response.strip())
        
        if 'result' in list_response:
            tools = list_response['result']['tools']
            print(f"✅ Tools: {[t['name'] for t in tools]}")
        else:
            print(f"❌ List tools failed: {list_response}")
            return False
        
        # Call hello tool
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "hello",
                "arguments": {"name": "MCP"}
            }
        }
        
        process.stdin.write(json.dumps(call_request) + '\n')
        process.stdin.flush()
        
        response = process.stdout.readline()
        call_response = json.loads(response.strip())
        
        if 'result' in call_response:
            result_text = call_response['result']['content'][0]['text']
            print(f"✅ Tool call: {result_text}")
            return True
        else:
            print(f"❌ Tool call failed: {call_response}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    success = test_minimal_mcp()
    print(f"\n{'✅ Success' if success else '❌ Failed'}")