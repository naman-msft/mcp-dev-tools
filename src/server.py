import os
import sys
import json
import asyncio
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiohttp import web
from metrics import track_metrics
    
# MCP imports - make them optional for now
try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
    import mcp.types as types
    MCP_AVAILABLE = True
except ImportError:
    print("Warning: MCP SDK not installed. Running in health-check only mode.", file=sys.stderr)
    MCP_AVAILABLE = False
    
    # Define dummy types for health-check only mode
    class types:
        class Tool:
            def __init__(self, **kwargs): pass
        class TextContent:
            def __init__(self, **kwargs): pass

# Configuration from environment
SERVER_NAME = os.getenv("MCP_SERVER_NAME", "dev-tools")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8080"))
WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", "/workspace")

# Initialize MCP server if available
if MCP_AVAILABLE:
    app = Server(SERVER_NAME)
else:
    app = None

# Simple health check handler
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ["/healthz", "/readyz", "/"]:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"healthy")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress logs unless debug
        if LOG_LEVEL == "debug":
            super().log_message(format, *args)

# Start health server in background
def start_health_server():
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    server.allow_reuse_address = True
    print(f"Health server listening on 0.0.0.0:{HEALTH_PORT}", file=sys.stderr)
    server.serve_forever()

# MCP Tool definitions (only if MCP is available)
if MCP_AVAILABLE and app:
    @app.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List all available tools."""
        return [
            types.Tool(
                name="execute_command",
                description="Execute a shell command and return the output",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to execute"},
                        "working_dir": {"type": "string", "description": "Optional working directory"}
                    },
                    "required": ["command"]
                }
            ),
            types.Tool(
                name="file_operation",
                description="Perform file operations (read, write, append, delete, list)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["read", "write", "append", "delete", "list"]},
                        "path": {"type": "string", "description": "File or directory path"},
                        "content": {"type": "string", "description": "Content for write/append operations"},
                        "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"}
                    },
                    "required": ["operation", "path"]
                }
            ),
            types.Tool(
                name="system_info",
                description="Get system and environment information",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]

    @app.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        """Handle tool execution requests."""
        
        if name == "execute_command":
            result = await execute_command(
                arguments.get("command"),
                arguments.get("working_dir")
            )
        elif name == "file_operation":
            result = await file_operation(
                arguments.get("operation"),
                arguments.get("path"),
                arguments.get("content"),
                arguments.get("encoding", "utf-8")
            )
        elif name == "system_info":
            result = await system_info()
        else:
            result = f"Unknown tool: {name}"
        
        return [types.TextContent(type="text", text=str(result))]

# Tool implementations
@track_metrics("execute_command")
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
            if content is None:
                return "Error: Content required for write operation"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding=encoding)
            return f"Successfully wrote {len(content)} chars to {path}"
            
        elif operation == "list":
            if not file_path.exists():
                return f"Error: Path {path} not found"
            if file_path.is_file():
                return f"File: {path}"
            items = []
            for item in file_path.iterdir():
                type_str = "DIR" if item.is_dir() else "FILE"
                items.append(f"[{type_str}] {item.name}")
            return "\n".join(items) if items else "Empty directory"
            
        else:
            return f"Error: Unknown operation '{operation}'"
            
    except Exception as e:
        return f"Error in file operation: {str(e)}"

async def system_info() -> str:
    """Get system and environment information."""
    import platform
    info = {
        "timestamp": datetime.now().isoformat(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "working_directory": os.getcwd(),
        "workspace_path": WORKSPACE_PATH,
        "mcp_available": MCP_AVAILABLE
    }
    return json.dumps(info, indent=2)

# HTTP-to-stdio bridge for remote MCP access
async def http_to_stdio_bridge(request):
    """Convert HTTP requests to stdio MCP calls"""
    try:
        json_rpc = await request.json()
        
        # Forward to MCP server via stdio
        proc = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'src.server',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, 'MCP_MODE': 'stdio'}  # Force stdio mode
        )
        
        # Send JSON-RPC to stdin
        proc.stdin.write(json.dumps(json_rpc).encode() + b'\n')
        await proc.stdin.drain()
        proc.stdin.close()
        
        # Read response from stdout (with timeout)
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), 
                timeout=30.0
            )
            
            if stderr and LOG_LEVEL == "debug":
                print(f"Bridge stderr: {stderr.decode()}", file=sys.stderr)
            
            # Parse response
            response = json.loads(stdout.decode())
            return web.json_response(response)
            
        except asyncio.TimeoutError:
            proc.kill()
            return web.json_response(
                {"error": "MCP request timeout"},
                status=504
            )
            
    except json.JSONDecodeError as e:
        return web.json_response(
            {"error": f"Invalid JSON: {str(e)}"},
            status=400
        )
    except Exception as e:
        print(f"Bridge error: {e}", file=sys.stderr)
        return web.json_response(
            {"error": f"Bridge error: {str(e)}"},
            status=500
        )

async def start_http_bridge():
    """Start HTTP-to-stdio bridge server"""
    app = web.Application()
    app.router.add_post('/mcp', http_to_stdio_bridge)
    app.router.add_get('/health', lambda r: web.Response(text="OK"))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', HEALTH_PORT)
    
    print(f"HTTP-to-stdio bridge listening on 0.0.0.0:{HEALTH_PORT}/mcp", file=sys.stderr)
    await site.start()
    
    # Keep running forever
    while True:
        await asyncio.sleep(3600)

# Main async function
async def run_server():
    """Run the server with health check and optional MCP."""
    
    # Check if we're in stdio mode (direct MCP) or HTTP bridge mode
    mcp_mode = os.getenv("MCP_MODE", "auto")
    
    if mcp_mode == "stdio" or (mcp_mode == "auto" and sys.stdin.isatty()):
        # Direct stdio mode for MCP
        if MCP_AVAILABLE and app:
            try:
                async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                    print(f"MCP Server running with stdio transport", file=sys.stderr)
                    await app.run(
                        read_stream,
                        write_stream,
                        InitializationOptions(
                            server_name=SERVER_NAME,
                            server_version="1.0.0",
                            capabilities=app.get_capabilities(
                                notification_options=NotificationOptions(),
                                experimental_capabilities={},
                            )
                        )
                    )
            except Exception as e:
                print(f"MCP server error: {e}", file=sys.stderr)
        else:
            print("MCP not available or no app initialized", file=sys.stderr)
    
    elif mcp_mode == "http" or (mcp_mode == "auto" and not sys.stdin.isatty()):
        # HTTP bridge mode (for Kubernetes)
        print(f"Starting HTTP-to-stdio bridge mode", file=sys.stderr)
        await start_http_bridge()
    
    else:
        # Fallback: just run health server
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        print(f"Running in health-check only mode", file=sys.stderr)
        while True:
            await asyncio.sleep(60)

# Entry point
if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nServer shutting down...", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)