"""
Authentication Context for MCP Tools

Provides a context-aware header provider that can inject Bearer tokens
into MCP tool requests. This module uses Python's contextvars to maintain
the current session context across async boundaries.

Pattern:
1. CLI/Web UI sets the current bearer token before calling agent
2. Header provider reads the token from context
3. McpToolset injects it as Authorization header in MCP requests
4. MCP server extracts the token and validates it

This is the official ADK pattern for authentication with MCP servers.
"""

from contextvars import ContextVar
from typing import Dict, Optional

# Context variable to store the current session's bearer token
# This is thread-safe and async-safe
_current_bearer_token: ContextVar[Optional[str]] = ContextVar(
    'current_bearer_token',
    default=None
)


def set_bearer_token(token: Optional[str]) -> None:
    """
    Set the bearer token for the current execution context.

    Call this before invoking the agent to ensure the token is available
    to the header provider during tool execution.

    Args:
        token: JWT bearer token from the authenticated session

    Example:
        >>> set_bearer_token(session.state.get("user:bearer_token"))
        >>> # Now any MCP tool calls will include this token
    """
    _current_bearer_token.set(token)


def get_bearer_token() -> Optional[str]:
    """
    Get the bearer token from the current execution context.

    Returns:
        Bearer token if set, None otherwise
    """
    return _current_bearer_token.get()


def clear_bearer_token() -> None:
    """Clear the bearer token from the current context."""
    _current_bearer_token.set(None)


def create_auth_header_provider() -> callable:
    """
    Create a header provider function for McpToolset.

    This function returns a callable that McpToolset will invoke
    for each MCP request to get HTTP headers. The provider reads
    the bearer token from the execution context.

    Returns:
        Callable that returns HTTP headers dict

    Example:
        >>> header_provider = create_auth_header_provider()
        >>> toolset = McpToolset(
        ...     connection_params=SseConnectionParams(url="..."),
        ...     header_provider=header_provider
        ... )
    """
    def header_provider(context) -> Dict[str, str]:
        """
        Provide HTTP headers for MCP requests.

        Args:
            context: ReadonlyContext provided by McpToolset (contains session state)

        Returns:
            Dict with Authorization header if token is available, empty dict otherwise

        How it works:
        1. Extracts bearer_token from context.session.state
        2. Token is stored there via EventActions state_delta during login
        3. Returns Authorization header with Bearer token format
        """
        # Try to get token from ADK context.session.state
        token = None
        if context and hasattr(context, 'session') and context.session:
            # Session state contains bearer_token (stored without prefix)
            token = context.session.state.get("bearer_token")

        # Fallback to contextvars (for testing/debugging)
        if not token:
            token = get_bearer_token()

        # Return Authorization header if token exists
        if token:
            return {"Authorization": f"Bearer {token}"}

        return {}

    return header_provider
