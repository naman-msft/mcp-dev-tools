#!/bin/bash

echo "🔧 Setting up environment variables for MCP deployment..."

# Check required environment variables
if [[ -z "$ACR_LOGIN_SERVER" || -z "$RG_NAME" || -z "$AKS_NAME" ]]; then
    echo "❌ Missing required environment variables:"
    echo "   ACR_LOGIN_SERVER, RG_NAME, AKS_NAME"
    echo ""
    echo "Set them like this:"
    echo "export ACR_LOGIN_SERVER=\"youracr.azurecr.io\""
    echo "export RG_NAME=\"your-resource-group\""
    echo "export AKS_NAME=\"your-aks-cluster\""
    exit 1
fi

echo "✅ Using environment:"
echo "   ACR: $ACR_LOGIN_SERVER"
echo "   Resource Group: $RG_NAME"
echo "   AKS Cluster: $AKS_NAME"

# Update deployment.yaml
echo "📝 Updating k8s/deployment.yaml..."
sed -i.bak "s|acrmcp6ce9d7\.azurecr\.io|${ACR_LOGIN_SERVER}|g" k8s/deployment.yaml

# Update deploy script
echo "📝 Updating scripts/deploy-v2.sh..."
sed -i.bak "s|acrmcp6ce9d7\.azurecr\.io|${ACR_LOGIN_SERVER}|g" scripts/deploy-v2.sh

echo "✅ Environment setup complete!"
echo "💡 Run './scripts/deploy-v2.sh' to deploy"