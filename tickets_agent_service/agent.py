"""
Tickets Agent Service - Self-contained A2A service

Port: 8080
Agent Card: http://localhost:8080/.well-known/agent-card.json

This is a complete, self-contained agent service that includes:
- Agent definition (LlmAgent)
- Tools/business logic (ticket management)
- Data layer (in-memory database)
- A2A server exposure
"""

import os
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from datetime import datetime
from typing import List, Dict, Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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

# =============================================================================
# Tool Functions (Business Logic)
# =============================================================================

def get_all_tickets() -> List[Dict]:
    """Retrieve all tickets in the system.

    Returns:
        List of all tickets with their details
    """
    return TICKETS_DB


def get_ticket(ticket_id: int) -> Dict:
    """Get a specific ticket by ID.

    Args:
        ticket_id: The unique ticket identifier

    Returns:
        Ticket details or error message if not found
    """
    for ticket in TICKETS_DB:
        if ticket['id'] == ticket_id:
            return ticket
    return {"error": f"Ticket {ticket_id} not found"}


def get_user_tickets(username: str) -> List[Dict]:
    """Get all tickets for a specific user.

    Args:
        username: The username to filter tickets by

    Returns:
        List of tickets for the specified user
    """
    return [t for t in TICKETS_DB if t['user'] == username]


def create_ticket(operation: str, user: str) -> Dict:
    """Create a new IT operations ticket.

    Args:
        operation: Type of operation (e.g., create_ai_key, vpn_access)
        user: Username who requested the ticket

    Returns:
        The newly created ticket
    """
    new_ticket = {
        "id": max(t['id'] for t in TICKETS_DB) + 1,
        "operation": operation,
        "user": user,
        "status": "pending",
        "created_at": datetime.now().isoformat() + "Z"
    }
    TICKETS_DB.append(new_ticket)
    return new_ticket


# =============================================================================
# Agent Setup
# =============================================================================

# Create agent with tools
tickets_agent = LlmAgent(
    name="TicketsAgent",
    model="gemini-2.5-flash",
    description="IT operations ticket management agent",
    instruction="""You are a specialized IT operations assistant focused on ticket management.

**Your Responsibilities:**
- Help users manage IT operation tickets (create_ai_key, create_gitlab_account, vpn_access, etc.)
- Track ticket status (pending, in_progress, completed, rejected)
- Provide ticket information and updates
- Create new tickets for IT operations

**Available Tools:**
- get_all_tickets: List all tickets in the system
- get_ticket: Get specific ticket by ID
- get_user_tickets: Get tickets for a specific user (by username)
- create_ticket: Create new ticket (specify operation and user)

**Communication Style:**
- Be clear and concise about ticket status
- Always include ticket IDs when referencing tickets
- Explain what each ticket status means
- Help users understand the ticketing process

**Example Queries:**
- "Show all tickets"
- "What's the status of ticket 12301?"
- "Show tickets for user vishal"
- "Create a ticket for alex to get vpn access"
""",
    tools=[get_all_tickets, get_ticket, get_user_tickets, create_ticket]
)

# =============================================================================
# A2A Server
# =============================================================================

# Expose agent via A2A protocol (at module level for uvicorn)
a2a_app = to_a2a(
    tickets_agent,
    port=8080,
    host="0.0.0.0"
)

if __name__ == "__main__":
    print("=" * 80)
    print("✅ Tickets Agent Service Started")
    print("=" * 80)
    print(f"Port:        8080")
    print(f"Agent Card:  http://localhost:8080/.well-known/agent-card.json")
    print(f"Health:      http://localhost:8080/health")
    print(f"Invoke:      http://localhost:8080/invoke")
    print("=" * 80)
    print("")
    print("Service is ready to handle requests via A2A protocol")
    print("Press Ctrl+C to stop")
    print("")
