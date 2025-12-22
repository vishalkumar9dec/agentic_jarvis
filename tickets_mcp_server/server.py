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
from typing import List, Dict, Optional
from datetime import datetime, timezone

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
    """Get all tickets for a specific user.

    This is a public tool that accepts a username parameter.
    Useful for admins or when username is known.

    Args:
        username (str): The username to filter tickets by

    Returns:
        List[Dict]: List of tickets belonging to the specified user.
            Empty list if user has no tickets.

    Example:
        >>> tickets = get_user_tickets("vishal")
        >>> len(tickets)
        2
        >>> all(t['user'] == 'vishal' for t in tickets)
        True
    """
    # Case-insensitive username matching
    username_lower = username.lower()
    return [t for t in TICKETS_DB if t['user'].lower() == username_lower]


@mcp.tool()
def create_ticket(operation: str, user: str) -> Dict:
    """Create a new IT operations ticket.

    This is a public tool that accepts both operation and user as parameters.
    Useful for admin ticket creation or when creating tickets for others.

    Args:
        operation (str): The operation type (e.g., create_ai_key, vpn_access)
        user (str): Username for whom the ticket is being created

    Returns:
        Dict: Response containing:
            - success (bool): Whether ticket creation succeeded
            - ticket (Dict): The created ticket with all fields
            - message (str): Success message with ticket ID

    Example:
        >>> result = create_ticket("create_ai_key", "vishal")
        >>> result['success']
        True
        >>> result['ticket']['status']
        'pending'
    """
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
# AUTHENTICATED TOOLS (Will be added in Task 10)
# =============================================================================
# The following authenticated tools will be added in Task 10:
# - get_my_tickets(tool_context: ToolContext) -> List[Dict]
# - create_my_ticket(operation: str, tool_context: ToolContext) -> Dict
#
# These will use ADK's ToolContext pattern to access authentication state:
#   bearer_token = tool_context.state.get("user:bearer_token")
#
# This is the CORRECT ADK-compliant pattern (not bearer_token as parameter).
