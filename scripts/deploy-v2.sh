#!/bin/bash

set -e

echo "🚀 Deploying MCP Server v2.0 to AKS..."

# Build and push new image
echo "📦 Building Docker image..."
docker build -t mcp-dev-tools:v2.0 . --load

# Tag for ACR
docker tag mcp-dev-tools:v2.0 acrmcp6ce9d7.azurecr.io/mcp-dev-tools:v2.0

# Push to ACR
echo "⬆️  Pushing to ACR..."
docker push acrmcp6ce9d7.azurecr.io/mcp-dev-tools:v2.0

# Update AKS deployment
echo "🔄 Updating AKS deployment..."
kubectl set image deployment/mcp-dev-tools -n mcp-system \
  mcp-server=acrmcp6ce9d7.azurecr.io/mcp-dev-tools:v2.0

# Wait for rollout
echo "⏳ Waiting for rollout to complete..."
kubectl rollout status deployment/mcp-dev-tools -n mcp-system

# Verify deployment
echo "✅ Verifying deployment..."
kubectl get pods -n mcp-system -l app=mcp-dev-tools

echo "🎉 Deployment complete! Server is running v2.0"
echo "💡 Run './scripts/test-deployment.sh' to test the deployment"