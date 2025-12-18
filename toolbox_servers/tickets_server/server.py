"""
Tickets Toolbox Server
Provides IT operations ticket management tools via FastAPI.
Port: 5001
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
from pydantic import BaseModel
import inspect

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
# Toolbox Pattern Implementation
# ============================================================================

# Define toolsets
TOOLSETS = {
    "tickets_toolset": {
        "get_all_tickets": get_all_tickets,
        "get_ticket": get_ticket,
        "get_user_tickets": get_user_tickets,
        "create_ticket": create_ticket
    }
}


def function_to_tool_schema(func: Callable) -> Dict[str, Any]:
    """Convert a Python function to MCP tool schema format.

    Args:
        func: The function to convert

    Returns:
        Tool schema dict with name, description, and parameters
    """
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""

    # Parse docstring for description
    description = doc.split('\n\n')[0].strip() if doc else func.__name__

    # Build parameters schema
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    for param_name, param in sig.parameters.items():
        # Get type annotation
        param_type = "string"  # default
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

        # Extract parameter description from docstring
        param_desc = param_name
        if "Args:" in doc:
            args_section = doc.split("Args:")[1].split("Returns:")[0] if "Returns:" in doc else doc.split("Args:")[1]
            for line in args_section.split('\n'):
                if param_name in line:
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        param_desc = parts[1].strip()
                    break

        parameters["properties"][param_name] = {
            "type": param_type,
            "description": param_desc
        }

        # Mark as required if no default value
        if param.default == inspect.Parameter.empty:
            parameters["required"].append(param_name)

    return {
        "name": func.__name__,
        "description": description,
        "inputSchema": parameters
    }


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Tickets Toolbox Server",
    description="MCP-compatible toolbox server for IT operations ticket management",
    version="1.0.0"
)


class ExecuteRequest(BaseModel):
    """Request model for tool execution."""
    name: str
    arguments: Dict[str, Any] = {}


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


@app.get("/toolsets")
async def list_toolsets():
    """List all available toolsets."""
    return {
        "toolsets": list(TOOLSETS.keys())
    }


@app.get("/toolsets/{toolset_name}")
async def get_toolset(toolset_name: str):
    """Get tools in a specific toolset.

    Args:
        toolset_name: Name of the toolset

    Returns:
        List of tools with their schemas
    """
    if toolset_name not in TOOLSETS:
        raise HTTPException(status_code=404, detail=f"Toolset '{toolset_name}' not found")

    toolset = TOOLSETS[toolset_name]
    tools = []

    for _, tool_func in toolset.items():
        tools.append(function_to_tool_schema(tool_func))

    return {
        "toolset": toolset_name,
        "tools": tools
    }


@app.post("/execute")
async def execute_tool(request: ExecuteRequest):
    """Execute a tool function.

    Args:
        request: Tool execution request with name and arguments

    Returns:
        Result from the tool function
    """
    # Find the tool function
    tool_func = None
    for toolset in TOOLSETS.values():
        if request.name in toolset:
            tool_func = toolset[request.name]
            break

    if not tool_func:
        raise HTTPException(status_code=404, detail=f"Tool '{request.name}' not found")

    try:
        # Execute the function with provided arguments
        result = tool_func(**request.arguments)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5001)
