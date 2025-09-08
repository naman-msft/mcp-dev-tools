#!/bin/bash

# Port forward for local access
echo "Starting port forward to MCP server..."
echo "Health check will be available at: http://localhost:8080/healthz"

kubectl port-forward \
  -n mcp-system \
  service/mcp-dev-tools \
  8080:8080