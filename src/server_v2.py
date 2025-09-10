import os
import sys
import json
import asyncio
import subprocess
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from aiohttp import web

# Configuration
SERVER_NAME = os.getenv("MCP_SERVER_NAME", "dev-tools-production")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8080"))
WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", "/workspace")

# Tool implementations (your existing working code)
async def execute_command(command: str, working_dir: Optional[str] = None) -> str:
    """Execute a shell command and return the output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir or WORKSPACE_PATH,
            capture_output=True,
            text=True,
            timeout=30
        )
        return f"Exit code: {result.returncode}\nOutput:\n{result.stdout}\nErrors:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"

async def file_operation(
    operation: str, 
    path: str, 
    content: Optional[str] = None,
    encoding: str = "utf-8"
) -> str:
    """Perform file operations."""
    try:
        file_path = Path(WORKSPACE_PATH) / path
        
        if operation == "read":
            if not file_path.exists():
                return f"Error: File {path} not found"
            return file_path.read_text(encoding=encoding)
            
        elif operation == "write":
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content or "", encoding=encoding)
            return f"Successfully wrote to {path}"
            
        elif operation == "list":
            if file_path.is_file():
                return f"File: {path}"
            elif file_path.is_dir():
                items = []
                for item in file_path.iterdir():
                    if item.is_dir():
                        items.append(f"DIR:  {item.name}/")
                    else:
                        items.append(f"FILE: {item.name}")
                return "\n".join(sorted(items))
            else:
                return f"Error: Path {path} not found"
        else:
            return f"Error: Unknown operation '{operation}'"
            
    except Exception as e:
        return f"Error performing {operation} on {path}: {str(e)}"

async def system_info() -> str:
    """Get system and environment information."""
    info = {
        "timestamp": datetime.now().isoformat(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "working_directory": os.getcwd(),
        "workspace_path": WORKSPACE_PATH,
        "mcp_available": True
    }
    return json.dumps(info, indent=2)

# MCP-like protocol handler (stateful)
class MCPHandler:
    def __init__(self):
        self.initialized = False
        self.session_data = {}
        
    async def handle_request(self, request_data):
        """Handle incoming MCP request"""
        method = request_data.get("method")
        params = request_data.get("params", {})
        request_id = request_data.get("id")
        
        if method == "initialize":
            return await self.handle_initialize(params, request_id)
        elif method == "tools/list":
            return await self.handle_tools_list(request_id)
        elif method == "tools/call":
            return await self.handle_tool_call(params, request_id)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def handle_initialize(self, params, request_id):
        """Handle MCP initialize request"""
        self.initialized = True
        self.session_data["protocolVersion"] = params.get("protocolVersion", "1.0.0")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "1.0.0",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": "2.0.0"
                }
            }
        }
    
    async def handle_tools_list(self, request_id):
        """Handle tools/list request"""
        if not self.initialized:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32002,
                    "message": "Server not initialized"
                }
            }
        
        tools = [
            {
                "name": "execute_command",
                "description": "Execute a shell command",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                        "working_dir": {"type": "string"}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "file_operation", 
                "description": "Perform file operations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string"},
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                        "encoding": {"type": "string"}
                    },
                    "required": ["operation", "path"]
                }
            },
            {
                "name": "system_info",
                "description": "Get system information",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools
            }
        }
    
    async def handle_tool_call(self, params, request_id):
        """Handle tools/call request"""
        if not self.initialized:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32002,
                    "message": "Server not initialized"
                }
            }
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "execute_command":
                result = await execute_command(
                    arguments.get("command"),
                    arguments.get("working_dir")
                )
            elif tool_name == "file_operation":
                result = await file_operation(
                    arguments.get("operation"),
                    arguments.get("path"),
                    arguments.get("content"),
                    arguments.get("encoding", "utf-8")
                )
            elif tool_name == "system_info":
                result = await system_info()
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
                }
            }

# Global handler instance (maintains state)
mcp_handler = MCPHandler()

async def handle_mcp_request(request):
    """HTTP endpoint for MCP requests"""
    try:
        data = await request.json()
        response = await mcp_handler.handle_request(data)
        return web.json_response(response)
    except json.JSONDecodeError:
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }, status=400)
    except Exception as e:
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }, status=500)

async def handle_health(request):
    """Health check endpoint"""
    return web.Response(text="OK")

async def start_server():
    """Start the HTTP server with MCP handler"""
    app = web.Application()
    app.router.add_post('/mcp', handle_mcp_request)
    app.router.add_get('/health', handle_health)
    app.router.add_get('/healthz', handle_health)
    app.router.add_get('/readyz', handle_health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', HEALTH_PORT)
    
    print(f"MCP Server (Stateful) listening on 0.0.0.0:{HEALTH_PORT}", file=sys.stderr)
    print(f"  Health: http://0.0.0.0:{HEALTH_PORT}/health", file=sys.stderr)
    print(f"  MCP:    http://0.0.0.0:{HEALTH_PORT}/mcp", file=sys.stderr)
    
    await site.start()
    
    # Keep running
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\nServer shutting down...", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)