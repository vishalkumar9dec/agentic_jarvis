"""
Tickets MCP Server - Tool Definitions
Uses FastMCP library for Model Context Protocol.

Port: 5011
Protocol: MCP (Model Context Protocol)
Phase: 2B - FastMCP Middleware Authentication

This server provides IT operations ticket management tools via MCP.
Uses FastMCP's AuthenticationMiddleware for centralized JWT validation.
"""

from fastmcp import FastMCP
from typing import List, Dict, Optional
from datetime import datetime, timezone
import sys
import os

# Add project root to Python path for auth imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.fastmcp_provider import JWTTokenVerifier

# =============================================================================
# In-Memory Ticket Database (Mock Data - Same as Phase 1)
# =============================================================================
# In production, this would be replaced with a real database connection

TICKETS_DB: List[Dict] = [
    {
        "id": 12301,
        "operation": "create_ai_key",
        "user": "vishal",
        "status": "pending",
        "created_at": "2025-01-10T10:00:00Z",
        "updated_at": "2025-01-10T10:00:00Z"
    },
    {
        "id": 12302,
        "operation": "create_gitlab_account",
        "user": "alex",
        "status": "completed",
        "created_at": "2025-01-09T14:30:00Z",
        "updated_at": "2025-01-10T16:00:00Z"
    },
    {
        "id": 12303,
        "operation": "update_budget",
        "user": "vishal",
        "status": "in_progress",
        "created_at": "2025-01-11T09:15:00Z",
        "updated_at": "2025-01-11T11:30:00Z"
    },
    {
        "id": 12304,
        "operation": "vpn_access",
        "user": "alex",
        "status": "pending",
        "created_at": "2025-01-12T08:00:00Z",
        "updated_at": "2025-01-12T08:00:00Z"
    },
    {
        "id": 12305,
        "operation": "gpu_allocation",
        "user": "sarah",
        "status": "approved",
        "created_at": "2025-01-13T10:30:00Z",
        "updated_at": "2025-01-13T12:00:00Z"
    },
]

# =============================================================================
# FastMCP Server Instance (No server-level auth for mixed public/private tools)
# =============================================================================
# Note: We don't use auth= parameter here because:
# 1. We have BOTH public tools (get_all_tickets) and authenticated tools
# 2. Server-level auth would block MCP protocol connections
# 3. Authentication middleware is added to the FastAPI app in app.py
# 4. Tools access authenticated user via get_current_user() helper

mcp = FastMCP(name="tickets-server")


# ============================================================================
# Helper Function: Get Current Authenticated User
# ============================================================================

def get_current_user() -> Dict:
    """
    Get authenticated user from current request context.

    This helper extracts user claims from the authenticated request.
    Authentication middleware (added in app.py) populates request.user.

    Returns:
        Dict containing user claims:
            - username: User's username
            - user_id: Unique user identifier
            - role: User's role (admin, developer, user)

    Raises:
        AttributeError: If called from unauthenticated context
    """
    from fastmcp.server.dependencies import get_http_request

    request = get_http_request()

    # Check if user is authenticated
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        raise ValueError("Authentication required")

    return request.user.identity


# =============================================================================
# PUBLIC TOOLS (No Authentication Required)
# =============================================================================


@mcp.tool()
def get_all_tickets() -> List[Dict]:
    """Retrieve all tickets in the IT operations system.

    This tool returns all tickets regardless of user or status.
    Useful for admin views and system-wide ticket monitoring.

    Returns:
        List[Dict]: List of all tickets with fields:
            - id (int): Unique ticket identifier
            - operation (str): Type of operation requested
            - user (str): Username who created the ticket
            - status (str): Current ticket status
            - created_at (str): ISO 8601 timestamp
            - updated_at (str): ISO 8601 timestamp

    Example:
        >>> tickets = get_all_tickets()
        >>> len(tickets)
        5
    """
    return TICKETS_DB


@mcp.tool()
def get_ticket(ticket_id: int) -> Optional[Dict]:
    """Get a specific ticket by its unique ID.

    Args:
        ticket_id (int): The unique ticket identifier to retrieve

    Returns:
        Optional[Dict]: Ticket details if found, None otherwise.
            Returns dictionary with same fields as get_all_tickets().

    Example:
        >>> ticket = get_ticket(12301)
        >>> ticket['operation']
        'create_ai_key'
    """
    for ticket in TICKETS_DB:
        if ticket['id'] == ticket_id:
            return ticket
    return None


@mcp.tool()
def get_user_tickets(username: str) -> List[Dict]:
    """Get all tickets for a specific user (Admin or self).

    This tool requires authentication.
    - Admins can view any user's tickets
    - Regular users can only view their own tickets

    Authentication is handled automatically by FastMCP middleware.

    Args:
        username (str): The username to filter tickets by

    Returns:
        List[Dict]: List of tickets belonging to the specified user (if authorized).
            Returns error dict if not authorized.

    Example (as admin):
        >>> # HTTP Request includes: Authorization: Bearer <admin_jwt>
        >>> tickets = get_user_tickets("alex")
        >>> all(t['user'] == 'alex' for t in tickets)
        True
    """
    # Get authenticated user from middleware
    user = get_current_user()
    current_user = user["username"]
    user_role = user.get("role", "")

    # Authorization check: Only admins can view other users' tickets
    if user_role != "admin" and current_user.lower() != username.lower():
        return {
            "error": "Access denied",
            "status": 403,
            "message": f"You can only view your own tickets. Use 'show my tickets' instead.",
            "your_username": current_user,
            "requested_username": username
        }

    # Admin or viewing own tickets - allow access
    username_lower = username.lower()
    return [t for t in TICKETS_DB if t['user'].lower() == username_lower]


@mcp.tool()
def create_ticket(operation: str, user: str) -> Dict:
    """Create a new IT operations ticket for a specific user (Admin or self).

    This tool requires authentication.
    - Admins can create tickets for any user
    - Regular users can only create tickets for themselves

    Authentication is handled automatically by FastMCP middleware.

    Args:
        operation (str): The operation type (e.g., create_ai_key, vpn_access)
        user (str): Username for whom the ticket is being created

    Returns:
        Dict: Response containing:
            - success (bool): Whether ticket creation succeeded
            - ticket (Dict): The created ticket with all fields
            - message (str): Success message with ticket ID

        Returns error dict if not authorized.

    Example (as admin):
        >>> # HTTP Request includes: Authorization: Bearer <admin_jwt>
        >>> result = create_ticket("create_ai_key", "vishal")
        >>> result['success']
        True
    """
    # Get authenticated user from middleware
    authenticated_user = get_current_user()
    current_user = authenticated_user["username"]
    user_role = authenticated_user.get("role", "")

    # Authorization check: Only admins can create tickets for other users
    if user_role != "admin" and current_user.lower() != user.lower():
        return {
            "error": "Access denied",
            "status": 403,
            "message": f"You can only create tickets for yourself. Use 'create a ticket for <operation>' instead.",
            "your_username": current_user,
            "requested_for": user,
            "suggestion": "Use create_my_ticket() or just say 'create a ticket for <operation>'"
        }

    # Admin or creating for self - allow ticket creation
    # Generate new ticket ID
    new_id = max([t['id'] for t in TICKETS_DB]) + 1 if TICKETS_DB else 1

    # Get current timestamp in ISO 8601 format
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    # Create new ticket
    new_ticket = {
        "id": new_id,
        "operation": operation,
        "user": user,
        "status": "pending",
        "created_at": now,
        "updated_at": now
    }

    # Add to database
    TICKETS_DB.append(new_ticket)

    return {
        "success": True,
        "ticket": new_ticket,
        "message": f"Ticket {new_id} created successfully for user {user}"
    }


# =============================================================================
# AUTHENTICATED TOOLS (Task 12 - ADK ToolContext Pattern)
# =============================================================================
# These tools use ADK's ToolContext to access authentication state.
# Authentication is validated centrally by before_tool_callback in callbacks.py


@mcp.tool()
def get_my_tickets() -> List[Dict]:
    """Get tickets for the authenticated user.

    This tool requires authentication via HTTP Authorization header.
    Returns only tickets that belong to the currently authenticated user.

    Authentication is handled automatically by FastMCP middleware:
    1. Middleware extracts Bearer token from Authorization header
    2. Validates token using JWTTokenVerifier
    3. Returns 401 automatically if token is invalid/expired
    4. Injects authenticated user into request.user

    Returns:
        List[Dict]: List of tickets belonging to the authenticated user.

    Example (when authenticated as vishal):
        >>> # HTTP Request includes: Authorization: Bearer <valid_jwt>
        >>> tickets = get_my_tickets()
        >>> all(t['user'] == 'vishal' for t in tickets)
        True
    """
    # Get authenticated user from middleware
    user = get_current_user()
    current_user = user["username"]

    # Return user-specific tickets
    username_lower = current_user.lower()
    return [t for t in TICKETS_DB if t['user'].lower() == username_lower]


@mcp.tool()
def create_my_ticket(operation: str) -> Dict:
    """Create a new ticket for the authenticated user.

    This tool requires authentication via HTTP Authorization header.
    The ticket will be created for the currently authenticated user.

    Authentication is handled automatically by FastMCP middleware.

    Args:
        operation (str): The operation type (e.g., create_ai_key, vpn_access)

    Returns:
        Dict: Response containing:
            - success (bool): Whether ticket creation succeeded
            - ticket (Dict): The created ticket with all fields
            - message (str): Success message with ticket ID

    Example (when authenticated as vishal):
        >>> # HTTP Request includes: Authorization: Bearer <valid_jwt>
        >>> result = create_my_ticket("create_ai_key")
        >>> result['success']
        True
        >>> result['ticket']['user']
        'vishal'
    """
    # Get authenticated user from middleware
    user = get_current_user()
    current_user = user["username"]

    # Generate new ticket ID
    new_id = max([t['id'] for t in TICKETS_DB]) + 1 if TICKETS_DB else 1

    # Get current timestamp in ISO 8601 format
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    # Create new ticket for authenticated user
    new_ticket = {
        "id": new_id,
        "operation": operation,
        "user": current_user,  # Use authenticated user from middleware
        "status": "pending",
        "created_at": now,
        "updated_at": now
    }

    # Add to database
    TICKETS_DB.append(new_ticket)

    return {
        "success": True,
        "ticket": new_ticket,
        "message": f"Ticket {new_id} created successfully for {current_user}"
    }
