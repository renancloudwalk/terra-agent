#!/bin/bash

echo "🧪 Testing Running MCP Server"
echo "=============================="

# Test 1: List tools
echo "📋 Test 1: List Tools"
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | uv run python mcp_server.py
echo ""

# Test 2: Call terraform_explain
echo "🔧 Test 2: Call terraform_explain"
PLAN_TEXT=$(cat fixtures/plan_small.txt | tr '\n' ' ')
echo "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"terraform_explain\",\"arguments\":{\"plan_text\":\"$PLAN_TEXT\",\"user_preference\":\"count_only\"}}}" | uv run python mcp_server.py
echo ""

# Test 3: Call terraform_explain_best_of_n  
echo "🎯 Test 3: Call terraform_explain_best_of_n"
echo "{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"terraform_explain_best_of_n\",\"arguments\":{\"plan_text\":\"$PLAN_TEXT\",\"n\":3,\"temperature\":0.7}}}" | uv run python mcp_server.py
echo ""

echo "✅ MCP Server Testing Complete!"