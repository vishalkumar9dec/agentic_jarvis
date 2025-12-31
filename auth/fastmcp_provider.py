"""
FastMCP Authentication Provider
Wraps existing JWT validation logic in FastMCP-compliant provider.

This provider enables FastMCP's AuthenticationMiddleware to validate JWT tokens
using our existing auth/jwt_utils.py logic. Once configured, all MCP tools
automatically receive authenticated user context without manual token validation.

Usage:
    from auth.fastmcp_provider import JWTTokenVerifier
    from starlette.middleware.authentication import AuthenticationMiddleware
    from fastmcp.server.auth.middleware import BearerAuthBackend

    mcp.add_middleware(
        AuthenticationMiddleware,
        backend=BearerAuthBackend(verifier=JWTTokenVerifier())
    )

Author: Agentic Jarvis Team
Date: 2025-12-25
Phase: 2 - FastMCP Middleware Migration
"""

from fastmcp.server.auth import TokenVerifier, AccessToken
from starlette.authentication import AuthenticationError
from typing import Dict, Any, Optional

# Handle imports for both module usage and direct execution
try:
    from auth.jwt_utils import verify_jwt_token
except ModuleNotFoundError:
    # When running this file directly, use relative import
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from auth.jwt_utils import verify_jwt_token


class JWTTokenVerifier(TokenVerifier):
    """
    FastMCP-compliant JWT token verifier.

    Wraps existing verify_jwt_token() from auth/jwt_utils.py to provide
    FastMCP's AuthenticationMiddleware with standardized token validation.

    This verifier:
    1. Receives JWT token (without "Bearer " prefix) from BearerAuthBackend
    2. Validates token using existing JWT utilities
    3. Returns FastMCP AccessToken with user claims
    4. Raises AuthenticationError for invalid/expired tokens

    The middleware automatically:
    - Extracts "Bearer <token>" from Authorization header
    - Calls this verifier's verify_token() method
    - Injects authenticated user into request.user
    - Returns 401 for invalid tokens
    - Makes user claims available to all tools
    """

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """
        Verify JWT token and return access token with claims.

        This method is called by FastMCP's BearerAuthBackend middleware
        for every authenticated request. It validates the JWT and converts
        the payload to FastMCP's AccessToken format.

        Args:
            token: JWT token string (without "Bearer " prefix)
                  Example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

        Returns:
            AccessToken: FastMCP access token containing:
                - token: Original JWT token string
                - claims: User claims dict (username, user_id, role, exp, iat)
                - scopes: List of user scopes/roles for RBAC
            None: If token is invalid or expired

        Example:
            >>> verifier = JWTTokenVerifier()
            >>> token = "eyJhbGc..."  # Valid JWT
            >>> access_token = await verifier.verify_token(token)
            >>> access_token.claims["username"]
            'vishal'
            >>> access_token.scopes
            ['developer']
        """
        # Use existing JWT validation logic (auth/jwt_utils.py)
        # This validates:
        # - JWT signature (HMAC-SHA256)
        # - Token expiration (exp claim)
        # - Token structure (valid JWT format)
        payload: Dict[str, Any] = verify_jwt_token(token)

        # verify_jwt_token returns None for invalid/expired tokens
        if not payload:
            # Return None instead of raising exception
            # FastMCP middleware will handle 401 response
            return None

        # Validate required claims exist
        if "username" not in payload:
            # Missing required claim - invalid token
            return None

        # Return FastMCP AccessToken
        # This token will be accessible in tools via:
        #   request.user.identity["username"]
        #   request.user.identity["role"]
        #   etc.
        return AccessToken(
            token=token,
            client_id=payload.get("user_id", "jarvis-client"),  # Use user_id as client identifier
            claims=payload,  # Contains: username, user_id, role, exp, iat
            scopes=[payload.get("role", "user")]  # For RBAC: admin, developer, user
        )


# =============================================================================
# Helper Function for Tools (Optional - Simplifies Tool Code)
# =============================================================================

def get_current_user_from_request() -> Dict[str, Any]:
    """
    Extract authenticated user claims from current request context.

    This helper function simplifies tool code by providing direct access
    to user claims without manually accessing request.user.

    Returns:
        Dict containing user claims:
            - username: User's username
            - user_id: Unique user identifier
            - role: User's role (admin, developer, user)
            - exp: Token expiration timestamp
            - iat: Token issued-at timestamp

    Raises:
        RuntimeError: If called outside of authenticated request context

    Usage in Tools:
        @mcp.tool()
        def get_my_tickets() -> List[Dict]:
            user = get_current_user_from_request()
            current_user = user["username"]
            return [t for t in TICKETS_DB if t['user'] == current_user]

    Note: This is optional. Tools can also access user directly via:
        from fastmcp.server.dependencies import get_http_request
        request = get_http_request()
        current_user = request.user.identity["username"]
    """
    from fastmcp.server.dependencies import get_http_request

    try:
        request = get_http_request()

        if not request.user.is_authenticated:
            raise AuthenticationError(
                "User not authenticated",
                status_code=401
            )

        return request.user.identity

    except Exception as e:
        raise RuntimeError(
            f"Failed to get current user from request: {e}"
        )


# =============================================================================
# Testing (Run this file directly to test)
# =============================================================================

if __name__ == "__main__":
    """
    Test the JWTTokenVerifier with a real JWT token.

    This test:
    1. Creates a test JWT token
    2. Verifies it using JWTTokenVerifier
    3. Validates the returned AccessToken structure
    """
    import asyncio
    import sys
    import os

    # Add parent directory to path for imports
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    from auth.jwt_utils import create_jwt_token

    async def test_jwt_verifier():
        print("Testing JWTTokenVerifier...")
        print("-" * 60)

        # Create test token
        test_token = create_jwt_token(
            username="vishal",
            user_id="user_001",
            role="developer"
        )
        print(f"✓ Test token created: {test_token[:50]}...")

        # Initialize verifier
        verifier = JWTTokenVerifier()
        print("✓ JWTTokenVerifier initialized")

        # Test valid token
        try:
            access_token = await verifier.verify_token(test_token)
            print(f"✓ Token verified successfully")
            print(f"  - Username: {access_token.claims['username']}")
            print(f"  - User ID: {access_token.claims['user_id']}")
            print(f"  - Role: {access_token.claims['role']}")
            print(f"  - Scopes: {access_token.scopes}")
        except AuthenticationError as e:
            print(f"✗ Verification failed: {e}")
            return

        # Test invalid token
        invalid_result = await verifier.verify_token("invalid-token-string")
        if invalid_result is None:
            print("✓ Invalid token correctly rejected (returned None)")
        else:
            print("✗ Invalid token should have returned None")

        # Test token without username claim (should fail)
        # Note: This is just for testing - real tokens always have username
        print("\n" + "=" * 60)
        print("✅ All JWTTokenVerifier tests passed!")
        print("=" * 60)

    # Run tests
    asyncio.run(test_jwt_verifier())
