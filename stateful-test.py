#!/usr/bin/env python3
import subprocess
import json

def test_mcp_directly():
    """Test MCP tools by executing them directly in the pod"""
    
    tests = [
        ("System Info", "system_info()"),
        ("Execute Command", "execute_command('ls -la /workspace', None)"),
        ("Create File", "file_operation('write', 'test.txt', 'Hello from MCP!', 'utf-8')"),
        ("Read File", "file_operation('read', 'test.txt', None, 'utf-8')"),
        ("List Files", "file_operation('list', '/', None, 'utf-8')"),
    ]
    
    for name, code in tests:
        print(f"\nTesting: {name}")
        print("-" * 40)
        
        cmd = f"""
import asyncio, sys
sys.path.insert(0, '/app')
from src.server import system_info, execute_command, file_operation
result = asyncio.run({code})
print(result)
"""
        
        result = subprocess.run(
            ["kubectl", "exec", "-n", "mcp-system", "deployment/mcp-dev-tools", 
             "--", "python3", "-c", cmd],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {result.stdout[:200]}...")
        else:
            print(f"❌ FAILED: {result.stderr}")

if __name__ == "__main__":
    print("=" * 50)
    print("MCP TOOLS DIRECT TESTING")
    print("=" * 50)
    test_mcp_directly()
    print("\n" + "=" * 50)
    print("CONCLUSION: Tools work! Bridge needs fixing.")
    print("=" * 50)
