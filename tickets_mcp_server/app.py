"""
Tickets MCP Server - FastAPI Application
Mounts FastMCP server to HTTP endpoint using FastAPI.

Port: 5011
Protocol: MCP over HTTP (Server-Sent Events)
Phase: 2B - FastMCP Authentication

This application serves the Tickets MCP server over HTTP, allowing
ADK agents to connect via McpToolset with SseConnectionParams.
"""

import sys
import os

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tickets_mcp_server.server import mcp
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.authentication import (
    AuthenticationBackend, AuthenticationError, BaseUser, AuthCredentials
)
from auth.fastmcp_provider import JWTTokenVerifier
import uvicorn

# =============================================================================
# Custom User Class with Full Claims
# =============================================================================

class AuthenticatedUser(BaseUser):
    """User object that stores full JWT claims."""

    def __init__(self, claims: dict):
        self.claims = claims
        self._username = claims.get("username", "")

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self._username

    @property
    def identity(self) -> dict:
        """Return full claims for tool access."""
        return self.claims

# =============================================================================
# Authentication Backend for FastAPI/Starlette Middleware
# =============================================================================

class BearerTokenBackend(AuthenticationBackend):
    """
    Authentication backend that validates Bearer tokens for HTTP requests.

    This backend:
    1. Extracts Bearer token from Authorization header
    2. Validates using JWTTokenVerifier
    3. Populates request.user with authenticated user
    4. Allows unauthenticated requests (tools decide if auth is required)
    """

    def __init__(self):
        self.verifier = JWTTokenVerifier()

    async def authenticate(self, request):
        """Authenticate request using Bearer token."""
        # Check for Authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            # No auth header - return None (unauthenticated, but not an error)
            # Public tools can still be called
            return None

        if not auth_header.startswith("Bearer "):
            # Invalid format - but don't block the request
            # Let the tool handle auth requirements
            return None

        # Extract token
        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            # Validate token
            access_token = await self.verifier.verify_token(token)

            if not access_token:
                return None

            # Return authenticated user with full claims
            return AuthCredentials(["authenticated"]), AuthenticatedUser(access_token.claims)

        except Exception:
            # Token validation failed - return None (not authenticated)
            return None

# =============================================================================
# Create MCP Application with Authentication Middleware
# =============================================================================
# Use FastMCP's http_app() to create HTTP endpoints with SSE transport
# SSE (Server-Sent Events) is required for ADK agents to connect

app = mcp.http_app(path="/mcp", transport="sse")

# Add authentication middleware to FastAPI app
# This makes request.user available to all tools via get_http_request()
app.add_middleware(
    AuthenticationMiddleware,
    backend=BearerTokenBackend()
)


# =============================================================================
# Application Entry Point
# =============================================================================

def main():
    """Main entry point for running the MCP server."""
    print("=" * 70)
    print(" Tickets MCP Server (Phase 2B - FastMCP Authentication)")
    print("=" * 70)
    print()
    print("  Port: 5011")
    print("  Protocol: Model Context Protocol (MCP)")
    print("  MCP Endpoint: http://localhost:5011/mcp")
    print("  Health Check: http://localhost:5011/health")
    print("  Info: http://localhost:5011/info")
    print()
    print("  Authentication: FastMCP JWT Validation")
    print("  Auth Provider: JWTTokenVerifier")
    print("  Tools: 6 tools (2 public, 4 authenticated)")
    print()
    print("  Public Tools:")
    print("    - get_all_tickets")
    print("    - get_ticket")
    print()
    print("  Authenticated Tools:")
    print("    - get_my_tickets (user)")
    print("    - create_my_ticket (user)")
    print("    - get_user_tickets (admin/self)")
    print("    - create_ticket (admin/self)")
    print()
    print("=" * 70)
    print()

    try:
        uvicorn.run(
            app,
            host="localhost",
            port=5011,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nShutting down Tickets MCP Server...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
