import json
import requests

# Start a session
session = requests.Session()
base_url = "http://localhost:8080/mcp"

# Initialize
init_request = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "1.0.0",
        "capabilities": {"tools": {}},
        "clientInfo": {"name": "test", "version": "1.0.0"}
    },
    "id": 1
}

print("Initializing...")
response = session.post(base_url, json=init_request)
print(f"Init response: {response.json()}")

# List tools
list_request = {
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 2
}

print("\nListing tools...")
response = session.post(base_url, json=list_request)
print(f"Tools response: {response.json()}")

# Call system_info
call_request = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "system_info",
        "arguments": {}
    },
    "id": 3
}

print("\nCalling system_info...")
response = session.post(base_url, json=call_request)
print(f"System info: {response.json()}")
