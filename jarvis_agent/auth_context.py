"""
Authentication Context for passing bearer tokens to toolbox clients.
Uses context variables to store the current request's bearer token.
"""

from contextvars import ContextVar
from typing import Optional

# Context variable to store the current bearer token
_bearer_token: ContextVar[Optional[str]] = ContextVar('bearer_token', default=None)


def set_bearer_token(token: Optional[str]) -> None:
    """Set the bearer token for the current context."""
    _bearer_token.set(token)


def get_bearer_token() -> Optional[str]:
    """Get the bearer token from the current context."""
    return _bearer_token.get()


def get_authorization_header() -> str:
    """Get the Authorization header value for the current context."""
    token = get_bearer_token()
    if token:
        return f"Bearer {token}"
    return ""
