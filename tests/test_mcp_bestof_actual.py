#!/usr/bin/env python3
"""
Actually test the MCP Best-of-N tool by calling it end-to-end.
"""

import json
import subprocess
import time
import sys


def test_mcp_best_of_n_actual():
    """Actually test the terraform_explain_best_of_n MCP tool."""
    print("🧪 Testing MCP Best-of-N Tool (ACTUAL)")
    print("=" * 50)
    
    # Start MCP server
    process = subprocess.Popen(
        ['uv', 'run', 'python', 'mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Step 1: Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        print("📡 Step 1: Initialize MCP server")
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        
        response = process.stdout.readline()
        if not response:
            print("❌ No init response")
            return False
            
        init_response = json.loads(response.strip())
        print(f"✅ Server initialized: {init_response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
        
        # Step 2: Send initialized notification
        initialized = {"jsonrpc": "2.0", "method": "initialized"}
        process.stdin.write(json.dumps(initialized) + '\n')
        process.stdin.flush()
        time.sleep(0.5)
        
        # Step 3: Read plan text
        with open('fixtures/plan_small.txt', 'r') as f:
            plan_text = f.read()
        
        # Step 4: Call terraform_explain_best_of_n
        best_of_n_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "terraform_explain_best_of_n",
                "arguments": {
                    "plan_text": plan_text,
                    "n": 3,
                    "temperature": 0.7
                }
            }
        }
        
        print("🎯 Step 3: Calling terraform_explain_best_of_n tool")
        print(f"   Parameters: n=3, temperature=0.7")
        process.stdin.write(json.dumps(best_of_n_request) + '\n')
        process.stdin.flush()
        
        print("⏳ Waiting for Best-of-N response (generating 3 responses)...")
        
        # Read response (this will take longer due to multiple API calls)
        response = process.stdout.readline()
        if not response:
            print("❌ No Best-of-N response")
            return False
            
        best_of_n_response = json.loads(response.strip())
        
        if 'result' in best_of_n_response:
            content = best_of_n_response['result'].get('content', [])
            if content:
                result_text = content[0].get('text', 'No text')
                print("✅ Best-of-N MCP tool response:")
                print("-" * 40)
                
                # Show first few lines
                lines = result_text.split('\n')
                for i, line in enumerate(lines[:10]):
                    print(f"   {line}")
                    if i == 9 and len(lines) > 10:
                        print(f"   ... ({len(lines) - 10} more lines)")
                        break
                
                # Validate it contains expected elements
                if "Best-of-" in result_text and "Score:" in result_text:
                    print("✅ Response contains Best-of-N results")
                else:
                    print("❌ Response missing Best-of-N elements")
                    return False
                    
                if "Detailed Results:" in result_text:
                    print("✅ Response contains detailed scoring")
                else:
                    print("❌ Response missing detailed results")
                    return False
                    
                print("✅ MCP Best-of-N tool works correctly!")
                return True
            else:
                print("❌ No content in Best-of-N response")
                return False
        else:
            print(f"❌ Best-of-N error: {best_of_n_response}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Best-of-N: {e}")
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
    try:
        success = test_mcp_best_of_n_actual()
        if success:
            print("\n🎉 MCP Best-of-N tool ACTUALLY WORKS!")
            sys.exit(0)
        else:
            print("\n❌ MCP Best-of-N tool FAILED actual testing!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted")
        sys.exit(1)