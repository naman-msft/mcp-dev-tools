#!/bin/bash

echo "Testing MCP Server Formats..."
echo "=============================="

# Test 1: Health check
echo -n "1. Health Check: "
curl -s http://localhost:8080/health && echo " ✓" || echo " ✗"

# Test 2: Basic JSON-RPC
echo -n "2. Basic JSON-RPC: "
RESPONSE=$(curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}')
echo $RESPONSE

# Test 3: With stdio wrapper
echo -n "3. Stdio Wrapper: "
RESPONSE=$(curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"stdio":{"jsonrpc":"2.0","method":"tools/list","id":1}}')
echo $RESPONSE

# Test 4: Direct method call
echo -n "4. Direct Method: "
RESPONSE=$(curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"method":"tools/list"}')
echo $RESPONSE

echo "=============================="
