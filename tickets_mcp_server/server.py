"""
Tickets MCP Server - Tool Definitions
Uses FastMCP library for Model Context Protocol.

Port: 5011 (NEW - parallel to existing 5001)
Protocol: MCP (Model Context Protocol)
Phase: 2A - No authentication (basic MCP functionality)

This server provides IT operations ticket management tools via MCP.
Authentication will be added in Task 10 (Phase 2B with ADK compliance).
"""

from fastmcp import FastMCP



from fastmcp.server.dependencies import get_http_headers
from typing import List, Dict, Optional
from datetime import datetime, timezone
import sys
import os

# Add project root to Python path for auth imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.jwt_utils import verify_jwt_token

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
# FastMCP Server Instance
# =============================================================================

mcp = FastMCP("tickets-server")


# =============================================================================
# PUBLIC TOOLS (No Authentication - Phase 2A)
# =============================================================================
# Authentication will be added in Task 10 using ADK ToolContext pattern


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
    """Get all tickets for a specific user (Admin only).

    This tool requires admin authorization. Regular users should use get_my_tickets() instead.
    Only admins can view other users' tickets.

    Authorization:
    - If no auth header: Returns public error (use get_all_tickets instead)
    - If auth header present:
      - Admin role: Can view any user's tickets
      - Non-admin role: Can only view their own tickets (redirected to get_my_tickets)

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
    # Extract bearer token from HTTP Authorization header
    headers = get_http_headers()
    auth_header = headers.get("authorization", "")

    # If no auth header, suggest using public endpoints
    if not auth_header:
        return {
            "error": "Authorization recommended",
            "status": 403,
            "message": "To view specific user tickets, please authenticate. Use get_all_tickets() for public access.",
            "suggestion": "Use 'show all tickets' or 'show my tickets' after logging in"
        }

    # Extract and validate token
    if not auth_header.startswith("Bearer "):
        return {
            "error": "Invalid authorization header format",
            "status": 401,
            "message": "Authorization header must use Bearer scheme"
        }

    bearer_token = auth_header[7:]  # Remove "Bearer " prefix

    # Validate token
    payload = verify_jwt_token(bearer_token)
    if not payload:
        return {
            "error": "Invalid or expired token",
            "status": 401,
            "message": "Your session has expired. Please log in again."
        }

    current_user = payload.get("username")
    user_role = payload.get("role", "")

    if not current_user:
        return {
            "error": "Token missing username claim",
            "status": 401
        }

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
    """Create a new IT operations ticket for a specific user (Admin only).

    This tool requires admin authorization. Regular users should use create_my_ticket() instead.
    Only admins can create tickets for other users.

    Authorization:
    - If no auth header: Returns error (authentication required)
    - If auth header present:
      - Admin role: Can create tickets for any user
      - Non-admin role: Can only create tickets for themselves (use create_my_ticket)

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
    # Extract bearer token from HTTP Authorization header
    headers = get_http_headers()
    auth_header = headers.get("authorization", "")

    # Require authentication for ticket creation
    if not auth_header:
        return {
            "error": "Authentication required",
            "status": 401,
            "message": "Please log in to create tickets. Use create_my_ticket() for your own tickets.",
            "suggestion": "Login and use 'create a ticket for <operation>'"
        }

    # Extract and validate token
    if not auth_header.startswith("Bearer "):
        return {
            "error": "Invalid authorization header format",
            "status": 401,
            "message": "Authorization header must use Bearer scheme"
        }

    bearer_token = auth_header[7:]  # Remove "Bearer " prefix

    # Validate token
    payload = verify_jwt_token(bearer_token)
    if not payload:
        return {
            "error": "Invalid or expired token",
            "status": 401,
            "message": "Your session has expired. Please log in again."
        }

    current_user = payload.get("username")
    user_role = payload.get("role", "")

    if not current_user:
        return {
            "error": "Token missing username claim",
            "status": 401
        }

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

    Authentication Flow (Task 13):
    1. CLI sets bearer token in context: set_bearer_token(token)
    2. McpToolset's header_provider injects: Authorization: Bearer <token>
    3. FastMCP receives HTTP request with Authorization header
    4. This tool extracts token using get_http_headers()
    5. Token is validated and user identity is determined

    Returns:
        List[Dict]: List of tickets belonging to the authenticated user.
            Returns error dict if authentication fails.

    Example (when authenticated as vishal):
        >>> # HTTP Request includes: Authorization: Bearer <valid_jwt>
        >>> tickets = get_my_tickets()
        >>> all(t['user'] == 'vishal' for t in tickets)
        True

    Error Response:
        {
            "error": "Authentication required",
            "status": 401,
            "message": "Please log in to access your tickets"
        }
    """
    # Extract bearer token from HTTP Authorization header
    headers = get_http_headers()
    auth_header = headers.get("authorization", "")

    if not auth_header:
        return {
            "error": "Authentication required",
            "status": 401,
            "message": "Please log in to access your tickets"
        }

    # Extract token from "Bearer <token>" format
    if not auth_header.startswith("Bearer "):
        return {
            "error": "Invalid authorization header format",
            "status": 401,
            "message": "Authorization header must use Bearer scheme"
        }

    bearer_token = auth_header[7:]  # Remove "Bearer " prefix

    # Validate token
    payload = verify_jwt_token(bearer_token)
    if not payload:
        return {
            "error": "Invalid or expired token",
            "status": 401,
            "message": "Your session has expired. Please log in again."
        }

    current_user = payload.get("username")
    if not current_user:
        return {
            "error": "Token missing username claim",
            "status": 401
        }

    # Return user-specific tickets
    username_lower = current_user.lower()
    return [t for t in TICKETS_DB if t['user'].lower() == username_lower]


@mcp.tool()
def create_my_ticket(operation: str) -> Dict:
    """Create a new ticket for the authenticated user.

    This tool requires authentication via HTTP Authorization header.
    The ticket will be created for the currently authenticated user.

    Authentication Flow (Task 13):
    1. CLI sets bearer token in context: set_bearer_token(token)
    2. McpToolset's header_provider injects: Authorization: Bearer <token>
    3. FastMCP receives HTTP request with Authorization header
    4. This tool extracts token using get_http_headers()
    5. Token is validated and ticket created for authenticated user

    Args:
        operation (str): The operation type (e.g., create_ai_key, vpn_access)

    Returns:
        Dict: Response containing:
            - success (bool): Whether ticket creation succeeded
            - ticket (Dict): The created ticket with all fields
            - message (str): Success message with ticket ID

        Returns error dict if authentication fails.

    Example (when authenticated as vishal):
        >>> # HTTP Request includes: Authorization: Bearer <valid_jwt>
        >>> result = create_my_ticket("create_ai_key")
        >>> result['success']
        True
        >>> result['ticket']['user']
        'vishal'

    Error Response:
        {
            "error": "Authentication required",
            "status": 401,
            "message": "Please log in to create tickets"
        }
    """
    # Extract bearer token from HTTP Authorization header
    headers = get_http_headers()
    auth_header = headers.get("authorization", "")

    if not auth_header:
        return {
            "error": "Authentication required",
            "status": 401,
            "message": "Please log in to create tickets"
        }

    # Extract token from "Bearer <token>" format
    if not auth_header.startswith("Bearer "):
        return {
            "error": "Invalid authorization header format",
            "status": 401,
            "message": "Authorization header must use Bearer scheme"
        }

    bearer_token = auth_header[7:]  # Remove "Bearer " prefix

    # Validate token
    payload = verify_jwt_token(bearer_token)
    if not payload:
        return {
            "error": "Invalid or expired token",
            "status": 401,
            "message": "Your session has expired. Please log in again."
        }

    current_user = payload.get("username")
    if not current_user:
        return {
            "error": "Token missing username claim",
            "status": 401
        }

    # Generate new ticket ID
    new_id = max([t['id'] for t in TICKETS_DB]) + 1 if TICKETS_DB else 1

    # Get current timestamp in ISO 8601 format
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    # Create new ticket for authenticated user
    new_ticket = {
        "id": new_id,
        "operation": operation,
        "user": current_user,  # Use authenticated user from JWT token
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
