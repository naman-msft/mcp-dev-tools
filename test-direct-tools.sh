#!/bin/bash

echo "Testing MCP Tools Directly in Pod"
echo "=================================="

# Test system_info
echo -e "\n1. Testing system_info:"
kubectl exec -n mcp-system deployment/mcp-dev-tools -- python3 -c "
import asyncio, json, sys
sys.path.insert(0, '/app')
from src.server import system_info
result = asyncio.run(system_info())
print('SUCCESS:', result[:100] + '...' if len(result) > 100 else result)
"

# Test execute_command
echo -e "\n2. Testing execute_command:"
kubectl exec -n mcp-system deployment/mcp-dev-tools -- python3 -c "
import asyncio, sys
sys.path.insert(0, '/app')
from src.server import execute_command
result = asyncio.run(execute_command('echo MCP Tools Working! && date', None))
print('SUCCESS:', result)
"

# Test file operations
echo -e "\n3. Testing file_operation (write):"
kubectl exec -n mcp-system deployment/mcp-dev-tools -- python3 -c "
import asyncio, sys
sys.path.insert(0, '/app')
from src.server import file_operation
result = asyncio.run(file_operation('write', 'demo.txt', 'This file created by MCP tools!', 'utf-8'))
print('SUCCESS:', result)
"

echo -e "\n4. Testing file_operation (read):"
kubectl exec -n mcp-system deployment/mcp-dev-tools -- python3 -c "
import asyncio, sys
sys.path.insert(0, '/app')
from src.server import file_operation
result = asyncio.run(file_operation('read', 'demo.txt', None, 'utf-8'))
print('SUCCESS:', result)
"

echo -e "\n5. Testing file_operation (list):"
kubectl exec -n mcp-system deployment/mcp-dev-tools -- python3 -c "
import asyncio, sys
sys.path.insert(0, '/app')
from src.server import file_operation
result = asyncio.run(file_operation('list', '/', None, 'utf-8'))
print('SUCCESS:', result[:200] + '...' if len(result) > 200 else result)
"

echo -e "\n=================================="
echo "All Direct Tests Complete!"
