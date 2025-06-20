#!/usr/bin/env python3
"""
Working MCP server test that properly handles initialization.
"""

import json
import subprocess
import sys
import time
import tempfile
import os


def test_mcp_server_properly():
    """Test MCP server with proper initialization sequence."""
    print("🧪 Testing MCP Server with Proper Initialization")
    print("=" * 50)
    
    # Start MCP server process
    process = subprocess.Popen(
        ['uv', 'run', 'python', 'mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Step 1: Send initialize request
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
        
        print("📡 Step 1: Sending initialize request")
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        
        # Read initialization response
        response_line = process.stdout.readline()
        if response_line:
            init_response = json.loads(response_line.strip())
            print(f"✅ Initialize response: {init_response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
        else:
            print("❌ No initialization response")
            return False
        
        # Step 2: Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "initialized"
        }
        
        print("📡 Step 2: Sending initialized notification")
        process.stdin.write(json.dumps(initialized_notification) + '\n')
        process.stdin.flush()
        
        time.sleep(0.5)  # Give server time to process
        
        # Step 3: List tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        print("📋 Step 3: Listing tools")
        process.stdin.write(json.dumps(list_tools_request) + '\n')
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            tools_response = json.loads(response_line.strip())
            if 'result' in tools_response:
                tools = tools_response['result'].get('tools', [])
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"   - {tool['name']}")
                
                # Check if our Best-of-N tool is there
                best_of_n_tool = next((t for t in tools if t['name'] == 'terraform_explain_best_of_n'), None)
                if best_of_n_tool:
                    print("✅ Best-of-N tool is available!")
                else:
                    print("❌ Best-of-N tool not found")
                    
            else:
                print(f"❌ Tools list error: {tools_response}")
                return False
        else:
            print("❌ No tools list response")
            return False
        
        # Step 4: Test terraform_explain
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
        
        print("🔧 Step 4: Testing terraform_explain")
        process.stdin.write(json.dumps(explain_request) + '\n')
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            explain_response = json.loads(response_line.strip())
            if 'result' in explain_response:
                content = explain_response['result'].get('content', [])
                if content:
                    result_text = content[0].get('text', 'No text')
                    print(f"✅ terraform_explain result: {result_text}")
                else:
                    print("❌ No content in explain response")
            else:
                print(f"❌ Explain error: {explain_response}")
                return False
        
        print("\n🎉 MCP Server is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
        
    finally:
        # Clean up
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    try:
        success = test_mcp_server_properly()
        if success:
            print("\n✅ All MCP tests passed!")
            sys.exit(0)
        else:
            print("\n❌ MCP tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted")
        sys.exit(1)