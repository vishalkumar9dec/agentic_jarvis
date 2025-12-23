"""
Tickets Toolbox Server
Provides IT operations ticket management tools via FastAPI.
Port: 5001
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
from pydantic import BaseModel
import inspect
import sys
import os

# Add parent directory to path to import auth modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from auth.jwt_utils import verify_jwt_token

# In-memory ticket database
TICKETS_DB = [
    {
        "id": 12301,
        "operation": "create_ai_key",
        "user": "vishal",
        "status": "pending",
        "created_at": "2025-01-10T10:00:00Z"
    },
    {
        "id": 12302,
        "operation": "create_gitlab_account",
        "user": "happy",
        "status": "completed",
        "created_at": "2025-01-09T14:30:00Z"
    },
    {
        "id": 12303,
        "operation": "update_budget",
        "user": "vishal",
        "status": "in_progress",
        "created_at": "2025-01-11T09:15:00Z"
    }
]


# ============================================================================
# Authentication
# ============================================================================

def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract and validate user from JWT token in Authorization header.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Username if token is valid, None otherwise
    """
    if not authorization:
        return None

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]
    payload = verify_jwt_token(token)

    if not payload:
        return None

    return payload.get("username")


# ============================================================================
# Tool Functions
# ============================================================================

def get_all_tickets() -> List[Dict]:
    """Retrieve all tickets.

    Returns:
        List of all tickets in the system
    """
    return TICKETS_DB


def get_ticket(ticket_id: int) -> Optional[Dict]:
    """Get a specific ticket by ID.

    Args:
        ticket_id: The unique ticket identifier

    Returns:
        Ticket details or None if not found
    """
    for ticket in TICKETS_DB:
        if ticket['id'] == ticket_id:
            return ticket
    return None


def get_user_tickets(username: str) -> List[Dict]:
    """Get all tickets for a specific user.

    Args:
        username: The username to filter tickets

    Returns:
        List of tickets belonging to the user
    """
    return [t for t in TICKETS_DB if t['user'].lower() == username.lower()]


def create_ticket(operation: str, user: str) -> Dict:
    """Create a new ticket.

    Args:
        operation: The operation type (e.g., create_ai_key, create_gitlab_account)
        user: Username creating the ticket

    Returns:
        Created ticket details with success status
    """
    # Generate new ticket ID
    new_id = max([t['id'] for t in TICKETS_DB]) + 1 if TICKETS_DB else 1

    new_ticket = {
        "id": new_id,
        "operation": operation,
        "user": user,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }

    TICKETS_DB.append(new_ticket)

    return {
        "success": True,
        "ticket": new_ticket,
        "message": f"Ticket {new_id} created successfully"
    }


# ============================================================================
# Authenticated Tool Functions (User-Specific)
# ============================================================================

def get_my_tickets(current_user: str) -> List[Dict]:
    """Get tickets for the authenticated user.

    Args:
        current_user: The authenticated username (from JWT token)

    Returns:
        List of tickets belonging to the authenticated user
    """
    if not current_user:
        return []
    return [t for t in TICKETS_DB if t['user'].lower() == current_user.lower()]


def create_my_ticket(operation: str, current_user: str) -> Dict:
    """Create a new ticket for the authenticated user.

    Args:
        operation: The operation type (e.g., create_ai_key, create_gitlab_account)
        current_user: The authenticated username (from JWT token)

    Returns:
        Created ticket details with success status
    """
    if not current_user:
        return {"success": False, "error": "Authentication required"}

    # Generate new ticket ID
    new_id = max([t['id'] for t in TICKETS_DB]) + 1 if TICKETS_DB else 1

    new_ticket = {
        "id": new_id,
        "operation": operation,
        "user": current_user,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }

    TICKETS_DB.append(new_ticket)

    return {
        "success": True,
        "ticket": new_ticket,
        "message": f"Ticket {new_id} created successfully for {current_user}"
    }


# ============================================================================
# Toolbox Pattern Implementation
# ============================================================================

# Define toolsets
TOOLSETS = {
    "tickets_toolset": {
        "get_all_tickets": get_all_tickets,
        "get_ticket": get_ticket,
        "get_user_tickets": get_user_tickets,
        "create_ticket": create_ticket,
        "get_my_tickets": get_my_tickets,
        "create_my_ticket": create_my_ticket
    }
}

# Tools that require authentication
AUTHENTICATED_TOOLS = {
    "get_my_tickets",
    "create_my_ticket"
}


def function_to_tool_schema(func: Callable, func_name: str = None) -> Dict[str, Any]:
    """Convert a Python function to Toolbox tool schema format.

    Args:
        func: The function to convert
        func_name: Optional function name for auth check

    Returns:
        Tool schema dict with description and parameters
    """
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""

    # Parse docstring for description
    lines = doc.split('\n')
    description = lines[0] if lines else func.__name__

    # Extract parameter descriptions from docstring
    param_descriptions = {}
    in_args_section = False
    for line in lines:
        line = line.strip()
        if line.lower().startswith('args:'):
            in_args_section = True
            continue
        if line.lower().startswith('returns:'):
            in_args_section = False
            continue
        if in_args_section and ':' in line:
            parts = line.split(':', 1)
            param_name = parts[0].strip()
            param_desc = parts[1].strip() if len(parts) > 1 else ""
            param_descriptions[param_name] = param_desc

    # Build parameter list (not a JSON Schema object)
    parameters = []

    for param_name, param in sig.parameters.items():
        # Skip current_user parameter - it's injected by auth
        if param_name == "current_user":
            continue

        param_type = "string"  # Default type
        is_required = param.default == inspect.Parameter.empty

        if param.annotation != inspect.Parameter.empty:
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == list or param.annotation == List:
                param_type = "array"
            elif param.annotation == dict or param.annotation == Dict:
                param_type = "object"

        param_schema = {
            "name": param_name,
            "type": param_type,
            "required": is_required,
            "description": param_descriptions.get(param_name, f"The {param_name} parameter")
        }

        parameters.append(param_schema)

    # Check if this tool requires authentication
    auth_required = []
    if func_name and func_name in AUTHENTICATED_TOOLS:
        auth_required = ["bearer_token"]

    return {
        "description": description,
        "parameters": parameters,
        "authRequired": auth_required
    }


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Tickets Toolbox Server",
    description="MCP-compatible toolbox server for IT operations ticket management",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Tickets Toolbox Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/toolset/{toolset_name}")
async def get_toolset(toolset_name: str):
    """Get toolset manifest with all tools in the toolset."""
    if toolset_name not in TOOLSETS:
        return {"error": f"Toolset '{toolset_name}' not found"}, 404

    toolset = TOOLSETS[toolset_name]
    tools = {}

    for func_name, tool_func in toolset.items():
        tool_schema = function_to_tool_schema(tool_func, func_name)
        # Use the function name (converted to kebab-case) as the key
        tool_key = func_name.replace('_', '-')
        tools[tool_key] = tool_schema

    return {
        "serverVersion": "1.0.0",
        "name": toolset_name,
        "tools": tools
    }


@app.get("/api/tool/{tool_name}")
async def get_tool(tool_name: str):
    """Get individual tool schema."""
    # Search for tool in all toolsets
    for toolset_name, toolset in TOOLSETS.items():
        for func_name, tool_func in toolset.items():
            if func_name.replace('_', '-') == tool_name or func_name == tool_name:
                return function_to_tool_schema(tool_func, func_name)

    return {"error": f"Tool '{tool_name}' not found"}, 404


@app.post("/api/tool/{tool_name}/invoke")
async def execute_tool(
    tool_name: str,
    params: Dict[str, Any],
    current_user: Optional[str] = Depends(get_current_user)
):
    """Execute a tool with given parameters."""
    # Search for tool in all toolsets
    for toolset_name, toolset in TOOLSETS.items():
        for func_name, tool_func in toolset.items():
            if func_name.replace('_', '-') == tool_name or func_name == tool_name:
                try:
                    # Check if tool requires authentication
                    if func_name in AUTHENTICATED_TOOLS:
                        if not current_user:
                            raise HTTPException(
                                status_code=401,
                                detail="Authentication required for this tool"
                            )
                        # Inject current_user into params
                        params["current_user"] = current_user

                    result = tool_func(**params)
                    return {"result": result}
                except HTTPException:
                    raise
                except Exception as e:
                    return {"error": str(e)}, 500

    return {"error": f"Tool '{tool_name}' not found"}, 404


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5001)
