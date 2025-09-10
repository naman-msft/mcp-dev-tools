#!/bin/bash

echo "========================================="
echo "Testing Stateful MCP Server"
echo "========================================="

# 1. Health Check
echo -e "\n1. Health Check:"
curl -s http://localhost:8080/health && echo " ✅" || echo " ❌"

# 2. Initialize
echo -e "\n2. Initialize MCP Session:"
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18"},"id":1}' | jq -r '.result.serverInfo'

# 3. List Tools (should work after init)
echo -e "\n3. List Tools:"
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}' | jq -r '.result.tools[].name'

# 4. Call system_info
echo -e "\n4. Call system_info:"
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"system_info","arguments":{}},"id":3}' | jq -r '.result.content[0].text' | head -5

# 5. Execute command
echo -e "\n5. Execute Command:"
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"execute_command","arguments":{"command":"echo MCP Works && date"}},"id":4}' | jq -r '.result.content[0].text' | head -3

echo -e "\n========================================="
echo "Test Complete!"
