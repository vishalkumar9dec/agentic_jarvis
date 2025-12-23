"""
ADK Callbacks for Authentication and Policy Enforcement.
Implements centralized authentication via before_tool_callback.

This module provides centralized authentication validation for MCP tools.
Instead of validating authentication in each individual tool, we use ADK's
callback pattern to intercept and validate tool calls BEFORE execution.

See: https://google.github.io/adk-docs/callbacks/
"""

from auth.jwt_utils import verify_jwt_token
from typing import Optional, Dict, Any


# =============================================================================
# Authenticated Tools Registry
# =============================================================================

# Tools that require authentication (ADK pattern)
# These tools will be blocked unless a valid bearer token is present in session state
AUTHENTICATED_TOOLS = {
    # Tickets authenticated tools
    "tickets_get_my_tickets",
    "tickets_create_my_ticket",

    # Oxygen authenticated tools
    "oxygen_get_my_courses",
    "oxygen_get_my_exams",
    "oxygen_get_my_preferences",
    "oxygen_get_my_learning_summary"
}


# =============================================================================
# Before Tool Callback - Centralized Authentication
# =============================================================================

def before_tool_callback(tool_name: str, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Validate authentication before tool execution.

    This callback intercepts tool calls BEFORE execution to:
    1. Validate authentication for sensitive tools
    2. Enforce policy (block unauthenticated access)
    3. Cache user info for this invocation

    IMPORTANT: This callback reads bearer token from state,
    which was populated by the Web UI/CLI layer before agent execution.

    NOTE: The actual integration with ADK App will be done in Task 13.
    This function signature will be adapted to match ADK's callback requirements.

    Args:
        tool_name: Name of the tool being called
        state: Session state dictionary containing user:bearer_token

    Returns:
        None: Allow tool execution to proceed
        dict: Return this result instead (blocks tool execution)

    Example:
        # If authentication succeeds:
        return None  # Tool executes normally

        # If authentication fails:
        return {"error": "Authentication required", "status": 401}
    """

    # Check if tool requires authentication
    if tool_name in AUTHENTICATED_TOOLS:
        bearer_token = state.get("user:bearer_token")

        if not bearer_token:
            # Block tool execution, return error
            return {
                "error": "Authentication required",
                "status": 401,
                "message": f"Tool '{tool_name}' requires authentication. Please log in.",
                "tool": tool_name
            }

        # Validate token
        payload = verify_jwt_token(bearer_token)

        if not payload:
            # Token invalid or expired
            return {
                "error": "Invalid or expired token",
                "status": 401,
                "message": "Your session has expired. Please log in again.",
                "tool": tool_name
            }

        # Store current user info in temporary state (this invocation only)
        # Tools can access this if needed via tool_context.state.get("temp:current_user")
        state["temp:current_user"] = payload.get("username")
        state["temp:user_id"] = payload.get("user_id")

    # Allow tool to execute normally
    return None


# =============================================================================
# After Tool Callback - Post-Processing (Optional)
# =============================================================================

def after_tool_callback(tool_name: str, result: Any) -> Any:
    """
    Post-process tool results for security (optional).

    This callback runs AFTER tool execution to:
    1. Sanitize results if needed
    2. Log security events
    3. Mask sensitive data

    NOTE: The actual integration with ADK App will be done in Task 13.
    This function signature will be adapted to match ADK's callback requirements.

    Args:
        tool_name: Name of the tool that was called
        result: Tool execution result

    Returns:
        Modified result (with sensitive data masked if needed)

    Example:
        # Mask bearer tokens that might have leaked into results
        if "bearer" in str(result).lower():
            result = mask_sensitive_data(result)
        return result
    """

    # Check if result contains sensitive data
    result_str = str(result)

    if "bearer" in result_str.lower() or "eyJ" in result_str:
        # Warning: Tool might have leaked sensitive data
        print(f"⚠️  WARNING: Tool {tool_name} returned sensitive data")

        # In production, you would mask the token here
        # For now, we just log the warning
        # result = mask_sensitive_data(result)

    return result


# =============================================================================
# Helper Functions
# =============================================================================

def is_authenticated_tool(tool_name: str) -> bool:
    """
    Check if a tool requires authentication.

    Args:
        tool_name: Name of the tool to check

    Returns:
        True if tool requires authentication, False otherwise
    """
    return tool_name in AUTHENTICATED_TOOLS


def get_authenticated_tools() -> set:
    """
    Get the set of tools that require authentication.

    Returns:
        Set of authenticated tool names
    """
    return AUTHENTICATED_TOOLS.copy()
