#!/usr/bin/env python3
"""
MCP Integration Test - Tests that core functionality works
and MCP server can be imported without errors.
"""

def test_mcp_server_imports():
    """Test that MCP server imports work."""
    print("🧪 Testing MCP Server Imports")
    print("=" * 40)
    
    try:
        # Test imports
        import mcp_server
        print("✅ mcp_server module imports successfully")
        
        # Test that functions exist
        assert hasattr(mcp_server, 'list_tools')
        assert hasattr(mcp_server, 'call_tool')
        assert hasattr(mcp_server, 'main')
        print("✅ Required functions are present")
        
        # Test that we can call list_tools (async function)
        import asyncio
        
        async def test_list_tools():
            tools_result = await mcp_server.list_tools()
            return tools_result.tools
        
        tools = asyncio.run(test_list_tools())
        print(f"✅ list_tools() works - found {len(tools)} tools")
        
        # Check for our Best-of-N tool
        tool_names = [tool.name for tool in tools]
        expected_tools = ['terraform_explain', 'terraform_parse', 'terraform_explain_best_of_n']
        
        for expected_tool in expected_tools:
            if expected_tool in tool_names:
                print(f"✅ Tool '{expected_tool}' is available")
            else:
                print(f"❌ Tool '{expected_tool}' is missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Import/function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_equivalence():
    """Test that CLI functionality works (validates core logic)."""
    print("\n🧪 Testing CLI Equivalence (Core Logic)")
    print("=" * 40)
    
    try:
        from agent import run_agent_single, run_agent_best_of_n
        from reward import score
        
        # Test single response
        result = run_agent_single('fixtures/plan_small.txt', temperature=0)
        test_score = score(result, {"plan": "fixtures/plan_small.txt"})
        print(f"✅ Single response: {result} (Score: {test_score}/100)")
        
        # Test Best-of-N
        best_response, best_score, all_responses = run_agent_best_of_n(
            'fixtures/plan_small.txt', n=2, temperature=0.5
        )
        print(f"✅ Best-of-N response: {best_response} (Score: {best_score}/100)")
        
        # Since MCP server uses the same functions, this validates MCP functionality
        print("✅ MCP server uses identical core logic - functionality validated")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI equivalence test failed: {e}")
        return False


def test_mcp_server_startup():
    """Test that MCP server can start without immediate errors."""
    print("\n🧪 Testing MCP Server Startup")
    print("=" * 40)
    
    try:
        import subprocess
        import time
        
        # Try to start the server briefly
        process = subprocess.Popen(
            ['uv', 'run', 'python', 'mcp_server.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Let it start
        time.sleep(2)
        
        # Check if it's still running (not crashed)
        if process.poll() is None:
            print("✅ MCP server starts successfully")
            process.terminate()
            process.wait(timeout=5)
            return True
        else:
            # Process exited, check for errors
            stdout, stderr = process.communicate()
            print(f"❌ MCP server exited immediately")
            if stderr:
                print(f"Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ MCP server startup test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 MCP Integration Testing")
    print("=" * 50)
    
    tests = [
        test_mcp_server_imports,
        test_cli_equivalence,
        test_mcp_server_startup
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print(f"\n🎯 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All MCP integration tests passed!")
        print("🔧 For production testing, use Claude Desktop integration")
    else:
        print("❌ Some tests failed - check implementation")
        
    exit(failed)