#!/usr/bin/env python3
"""
Debug MCP tool calling to understand the parameter issue.
"""

import json
import subprocess
import time


def test_basic_mcp_tool():
    """Test basic terraform_explain first."""
    print("🔍 Debugging MCP Tool Calls")
    print("=" * 40)
    
    process = subprocess.Popen(
        ['uv', 'run', 'python', 'mcp_server.py'],
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
        print(f"✅ Initialized: {init_response['result']['serverInfo']['name']}")
        
        # Send initialized
        initialized = {"jsonrpc": "2.0", "method": "initialized"}
        process.stdin.write(json.dumps(initialized) + '\n')
        process.stdin.flush()
        time.sleep(0.5)
        
        # Test basic terraform_explain first
        with open('fixtures/plan_small.txt', 'r') as f:
            plan_text = f.read()
            
        explain_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "terraform_explain",
                "arguments": {
                    "plan_text": plan_text,
                    "user_preference": "count_only"
                }
            }
        }
        
        print("🔧 Testing terraform_explain...")
        process.stdin.write(json.dumps(explain_request) + '\n')
        process.stdin.flush()
        
        response = process.stdout.readline()
        explain_response = json.loads(response.strip())
        
        if 'result' in explain_response:
            result_text = explain_response['result']['content'][0]['text']
            print(f"✅ terraform_explain works: {result_text}")
        else:
            print(f"❌ terraform_explain failed: {explain_response}")
            return False
            
        # Now test Best-of-N with more debugging
        print("🎯 Testing terraform_explain_best_of_n...")
        
        best_of_n_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call", 
            "params": {
                "name": "terraform_explain_best_of_n",
                "arguments": {
                    "plan_text": plan_text,
                    "n": 2,  # Use smaller N for faster testing
                    "temperature": 0.5
                }
            }
        }
        
        print(f"📋 Request: {json.dumps(best_of_n_request, indent=2)}")
        
        process.stdin.write(json.dumps(best_of_n_request) + '\n')
        process.stdin.flush()
        
        print("⏳ Waiting for response...")
        response = process.stdout.readline()
        
        if response:
            best_response = json.loads(response.strip())
            print(f"📤 Raw response: {json.dumps(best_response, indent=2)}")
            
            if 'result' in best_response:
                print("✅ Best-of-N tool worked!")
                return True
            else:
                print("❌ Best-of-N tool failed")
                return False
        else:
            print("❌ No response received")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    test_basic_mcp_tool()