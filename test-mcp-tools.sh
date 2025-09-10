#!/bin/bash

echo "================================"
echo "Testing MCP Dev Tools Server"
echo "================================"

MCP_URL="http://localhost:8080/mcp"

# Function to make MCP call
call_mcp() {
    local method=$1
    local params=$2
    local description=$3
    
    echo ""
    echo "Test: $description"
    echo "-------------------"
    
    # First initialize (required for each call due to stateless bridge)
    INIT_RESPONSE=$(curl -s -X POST $MCP_URL \
      -H "Content-Type: application/json" \
      -d '{
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
          "protocolVersion": "2025-06-18",
          "capabilities": {"tools": {}},
          "clientInfo": {"name": "test", "version": "1.0"}
        },
        "id": 1
      }')
    
    # Check if init succeeded
    if echo "$INIT_RESPONSE" | grep -q '"result"'; then
        echo "✓ Initialized successfully"
        
        # Now make the actual call
        RESPONSE=$(curl -s -X POST $MCP_URL \
          -H "Content-Type: application/json" \
          -d "{
            \"jsonrpc\": \"2.0\",
            \"method\": \"$method\",
            \"params\": $params,
            \"id\": 2
          }")
        
        echo "Response: $RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
    else
        echo "✗ Initialization failed"
        echo "$INIT_RESPONSE" | jq .
    fi
}

# Test 1: System Info
call_mcp "tools/call" '{
  "name": "system_info",
  "arguments": {}
}' "System Information"

# Test 2: Execute Command
call_mcp "tools/call" '{
  "name": "execute_command",
  "arguments": {
    "command": "echo Hello from MCP && date && pwd"
  }
}' "Execute Command: echo & date & pwd"

# Test 3: List files in root
call_mcp "tools/call" '{
  "name": "file_operation",
  "arguments": {
    "operation": "list",
    "path": "/"
  }
}' "List files in workspace root"

# Test 4: Create a test file
call_mcp "tools/call" '{
  "name": "file_operation",
  "arguments": {
    "operation": "write",
    "path": "test-mcp.txt",
    "content": "This file was created by MCP server at $(date)"
  }
}' "Create a test file"

# Test 5: Read the test file
call_mcp "tools/call" '{
  "name": "file_operation",
  "arguments": {
    "operation": "read",
    "path": "test-mcp.txt"
  }
}' "Read the test file"

# Test 6: Execute a more complex command
call_mcp "tools/call" '{
  "name": "execute_command",
  "arguments": {
    "command": "ls -la /workspace && df -h"
  }
}' "List workspace and disk usage"

echo ""
echo "================================"
echo "Test Complete!"
echo "================================"
