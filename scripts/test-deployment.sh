#!/bin/bash

echo "🧪 Testing MCP Server v2.0 Deployment"
echo "====================================="

# Kill any existing port-forwards
pkill -f "kubectl port-forward" 2>/dev/null || true

# Wait for pods to be ready
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=mcp-dev-tools -n mcp-system --timeout=60s

# Start port-forward in background
echo "🔗 Starting port-forward..."
kubectl port-forward -n mcp-system svc/mcp-dev-tools 8080:8080 &
PF_PID=$!

# Wait for port-forward to establish
sleep 3

# Run comprehensive tests
echo "🔍 Running MCP protocol tests..."

# Test 1: Health Check
echo -n "1. Health Check: "
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
    exit 1
fi

# Test 2: MCP Initialize
echo -n "2. MCP Initialize: "
INIT_RESPONSE=$(curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"1.0.0"},"id":1}')

if echo "$INIT_RESPONSE" | jq -e '.result.serverInfo.name' > /dev/null 2>&1; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
    echo "Response: $INIT_RESPONSE"
    exit 1
fi

# Test 3: Tools List
echo -n "3. Tools List: "
TOOLS_RESPONSE=$(curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}')

TOOL_COUNT=$(echo "$TOOLS_RESPONSE" | jq -r '.result.tools | length' 2>/dev/null)
if [ "$TOOL_COUNT" = "3" ]; then
    echo "✅ PASS (3 tools)"
else
    echo "❌ FAIL (expected 3 tools, got $TOOL_COUNT)"
    exit 1
fi

# Test 4: System Info Tool
echo -n "4. System Info Tool: "
SYSINFO_RESPONSE=$(curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"system_info","arguments":{}},"id":3}')

if echo "$SYSINFO_RESPONSE" | jq -e '.result.content[0].text' > /dev/null 2>&1; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
    echo "Response: $SYSINFO_RESPONSE"
    exit 1
fi

# Test 5: Command Execution
echo -n "5. Command Execution: "
CMD_RESPONSE=$(curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"execute_command","arguments":{"command":"echo MCP v2.0 Works!"}},"id":4}')

if echo "$CMD_RESPONSE" | jq -e '.result.content[0].text' | grep -q "MCP v2.0 Works!"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
    echo "Response: $CMD_RESPONSE"
    exit 1
fi

# Test 6: File Operations
echo -n "6. File Operations: "
FILE_RESPONSE=$(curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"file_operation","arguments":{"operation":"write","path":"test-v2.txt","content":"Hello from MCP v2.0!"}},"id":5}')

if echo "$FILE_RESPONSE" | jq -e '.result.content[0].text' | grep -q "Successfully wrote"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
    echo "Response: $FILE_RESPONSE"
    exit 1
fi

# Cleanup
kill $PF_PID 2>/dev/null || true

echo ""
echo "🎉 All tests passed! MCP Server v2.0 is working correctly."
echo "🔗 Server is accessible via kubectl port-forward on port 8080"
echo "📊 Ready for IDE integration and production use!"