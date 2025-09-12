from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
import os
import jwt
import httpx
from functools import wraps
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class AzureADAuthenticator:
    def __init__(self):
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID", None)
        
        # Use Managed Identity in AKS, fallback to DefaultAzureCredential locally
        if os.getenv("KUBERNETES_SERVICE_HOST"):
            # Running in Kubernetes - use Managed Identity
            self.credential = ManagedIdentityCredential(
                client_id=self.client_id
            ) if self.client_id else ManagedIdentityCredential()
        else:
            # Local development - use Azure CLI or other methods
            self.credential = DefaultAzureCredential()
        
    async def get_token(self, scope: str = "https://management.azure.com/.default"):
        """Get Azure AD token using managed identity or default credentials."""
        try:
            token = self.credential.get_token(scope)
            return token.token
        except Exception as e:
            print(f"Failed to get Azure AD token: {e}")
            return None

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate Azure AD JWT token."""
        try:
            # For development/testing, do basic validation
            # In production, you'd validate against Azure AD JWKS
            if not token:
                raise ValueError("No token provided")
            
            # Simple validation - just check if token exists
            # TODO: Implement proper JWT validation against Azure AD
            return {
                "validated": True, 
                "user": "authenticated_user",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise ValueError(f"Token validation failed: {str(e)}")

def require_auth(func):
    """Decorator to require authentication for MCP tools."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # For now, just pass through - implement full auth in production
        # In a real implementation, you'd check for auth headers/tokens
        auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
        
        if auth_enabled:
            # TODO: Extract and validate auth token from request
            print("Auth is enabled but validation is placeholder")
        
        return await func(*args, **kwargs)
    return wrapper

# Global authenticator instance
authenticator = AzureADAuthenticator()