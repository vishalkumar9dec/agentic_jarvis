"""
Tickets Agent
Manages IT operations tickets using the tickets toolbox server.
"""

from google.adk.agents import LlmAgent
from toolbox_core import ToolboxSyncClient

# Model configuration
GEMINI_2_5_FLASH = "gemini-2.5-flash"

# Connect to tickets toolbox server
toolbox = ToolboxSyncClient("http://localhost:5001")
tools = toolbox.load_toolset('tickets_toolset')

# Create the Tickets agent
tickets_agent = LlmAgent(
    name="TicketsAgent",
    model=GEMINI_2_5_FLASH,
    description="Agent to manage IT operations tickets",
    instruction="""You are a tickets management agent. Your role is to help users:
- View all tickets or specific tickets by ID
- Find tickets for a particular user
- Create new tickets for operations

Always provide clear, concise ticket information with proper formatting.

When showing tickets, include:
- Ticket ID
- Operation type
- User who created it
- Current status
- Creation timestamp

When creating tickets, confirm successful creation with the new ticket ID.""",
    tools=tools,
)
