# Phase 2 Implementation Tasks - CORRECT ORDER

**Phase:** 2 (MCP Migration + JWT Authentication)
**Strategy:** Parallel Implementation (NEW MCP solution alongside existing Toolbox solution)
**Order:** MCP First → Chat UI → Authentication
**Risk:** Zero (existing system untouched, different ports)
**Last Updated:** 2025-12-21

---

## ⚠️ CRITICAL: Implementation Order

**DO NOT start with authentication**. The documented order is:

1. **Part A (Tasks 1-8):** Build NEW MCP solution (ports 5011, 5012, 8012, 9990) - WITHOUT authentication
2. **Part B (Tasks 9-16):** Add ADK-compliant JWT authentication to MCP solution
3. **Part C (Tasks 17-20):** Testing, comparison, documentation

**✅ ADK-COMPLIANT FROM THE START:**
All authentication tasks (9-16) use the correct ADK pattern:
- **ToolContext** for tool authentication (NOT bearer_token parameters)
- **Session state** for token storage (`session.state["user:bearer_token"]`)
- **Callbacks** for centralized auth enforcement (`before_tool_callback`)
- **App** pattern for agent lifecycle management (agents created ONCE, not per-request)

**Why MCP First?**
- MCP has native OAuth 2.1 support (better than custom toolbox)
- Automatic tool discovery (no manual registration)
- Per-request auth pattern built-in (fixes current auth bug)
- Keycloak-ready from day one
- Industry-standard protocol (not custom)

**Why Parallel Implementation?**
- Zero risk to existing working system (ports 5001, 5002, 8002, 9999)
- NEW MCP system on different ports (5011, 5012, 8012, 9990)
- Both run simultaneously for comparison
- Easy rollback if needed

---

## Prerequisites

Before starting, ensure:
- [ ] Phase 1 complete and running (existing toolbox solution)
- [ ] Read `docs/MCP_CORRECT_IMPLEMENTATION.md` (technical details)
- [ ] Read `docs/PARALLEL_IMPLEMENTATION.md` (parallel strategy)
- [ ] Read `docs/PHASE_2_PLAN.md` (overall plan)
- [ ] Install FastMCP: `pip install fastmcp`
- [ ] Existing system running on ports 5001, 5002, 8002, 9999 (UNCHANGED)

---

## Part A: Build MCP Solution (Tasks 1-8) - NO AUTHENTICATION YET

### **Task 1: Install FastMCP and Update Requirements**

**Priority:** Critical
**Dependencies:** None
**Estimated Time:** 30 minutes

**Objective:**
Install FastMCP library and update project dependencies.

**Implementation:**

1. **Update `requirements.txt`:**
```txt
# Existing dependencies (keep all)
google-genai-adk>=1.21.0
fastapi
uvicorn
pydantic
python-jose[cryptography]
passlib[bcrypt]

# NEW for Phase 2: MCP Protocol
fastmcp>=0.1.0          # FastMCP library for MCP servers
mcp>=0.1.0              # MCP Python SDK (dependency)
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Verify installation:**
```python
python3 << EOF
try:
    from fastmcp import FastMCP
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
    print("✓ FastMCP and ADK MCP tools installed correctly")
except ImportError as e:
    print(f"✗ Import error: {e}")
EOF
```

**Success Criteria:**
- [ ] FastMCP imported successfully
- [ ] ADK McpToolset imported successfully
- [ ] No import errors

**Notes:**
- FastMCP is CORRECT library (not invented `mcp.server.fastapi.MCPServer`)
- Refer to: https://gofastmcp.com for documentation

---

### **Task 2: Build Tickets MCP Server (Port 5011)**

**Priority:** Critical
**Dependencies:** Task 1
**Estimated Time:** 3 hours

**Objective:**
Create Tickets MCP server using FastMCP pattern on port 5011 (parallel to existing 5001).

**Implementation:**

1. **Create directory structure:**
```bash
mkdir -p tickets_mcp_server
touch tickets_mcp_server/__init__.py
touch tickets_mcp_server/server.py
touch tickets_mcp_server/app.py
```

2. **Create `tickets_mcp_server/server.py`** (FastMCP tool definitions):

```python
"""
Tickets MCP Server - Tool Definitions
Uses FastMCP library for MCP protocol.
Port: 5011 (NEW - parallel to 5001)
"""

from fastmcp import FastMCP
from typing import List, Dict, Optional
from datetime import datetime, timezone

# In-memory ticket database (same data as port 5001)
TICKETS_DB = [
    {"id": 12301, "operation": "create_ai_key", "user": "vishal", "status": "pending", "created_at": "2025-01-10T10:00:00Z"},
    {"id": 12302, "operation": "create_gitlab_account", "user": "alex", "status": "completed", "created_at": "2025-01-09T14:30:00Z"},
    {"id": 12303, "operation": "update_budget", "user": "vishal", "status": "in_progress", "created_at": "2025-01-11T09:15:00Z"},
    {"id": 12304, "operation": "vpn_access", "user": "alex", "status": "pending", "created_at": "2025-01-12T08:00:00Z"},
    {"id": 12305, "operation": "gpu_allocation", "user": "sarah", "status": "approved", "created_at": "2025-01-13T10:30:00Z"},
]

# Create FastMCP server
mcp = FastMCP("tickets-server")


# ===================================================================
# PUBLIC TOOLS (No authentication - Phase 2A)
# ===================================================================

@mcp.tool()
def get_all_tickets() -> List[Dict]:
    """Retrieve all tickets in the system.

    Returns:
        List of all tickets with id, operation, user, status, created_at
    """
    return TICKETS_DB


@mcp.tool()
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


@mcp.tool()
def get_user_tickets(username: str) -> List[Dict]:
    """Get all tickets for a specific user.

    Args:
        username: The username to filter tickets

    Returns:
        List of tickets belonging to the user
    """
    return [t for t in TICKETS_DB if t['user'].lower() == username.lower()]


@mcp.tool()
def create_ticket(operation: str, user: str) -> Dict:
    """Create a new ticket.

    Args:
        operation: The operation type (e.g., create_ai_key, create_gitlab_account)
        user: Username creating the ticket

    Returns:
        Created ticket details with success status
    """
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


# NOTE: Authenticated tools (get_my_tickets, create_my_ticket) will be added in Part B (Task 9)
```

3. **Create `tickets_mcp_server/app.py`** (FastAPI mounting):

```python
"""
Tickets MCP Server - FastAPI Application
Mounts FastMCP server to HTTP endpoint.
Port: 5011
"""

from fastapi import FastAPI
from tickets_mcp_server.server import mcp
import uvicorn

# Create MCP HTTP app
mcp_app = mcp.http_app(path='/mcp')

# Create main FastAPI app
app = FastAPI(
    title="Tickets MCP Server",
    description="Model Context Protocol server for IT operations ticket management",
    version="2.0.0-mcp",
    lifespan=mcp_app.lifespan  # CRITICAL: Share lifespan
)

# Mount MCP endpoints
app.mount("/mcp", mcp_app)


# ===================================================================
# Health Check Endpoints
# ===================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Tickets MCP Server",
        "protocol": "Model Context Protocol (MCP)",
        "version": "2.0.0-mcp",
        "port": 5011,
        "status": "running",
        "mcp_endpoint": "/mcp",
        "note": "Part of Phase 2 parallel implementation (existing server on port 5001 unchanged)"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "protocol": "mcp", "port": 5011}


if __name__ == "__main__":
    print("=" * 70)
    print(" Tickets MCP Server (Phase 2 - Parallel Implementation)")
    print("=" * 70)
    print()
    print("  Port: 5011 (NEW - parallel to 5001)")
    print("  Protocol: Model Context Protocol (MCP)")
    print("  MCP Endpoint: http://localhost:5011/mcp")
    print("  Health: http://localhost:5011/health")
    print()
    print("  NOTE: Existing toolbox server on port 5001 is UNCHANGED")
    print("=" * 70)
    print()

    uvicorn.run(app, host="localhost", port=5011)
```

4. **Create startup script `scripts/start_tickets_mcp_server.sh`:**

```bash
#!/bin/bash

echo "========================================"
echo " Tickets MCP Server (Port 5011)"
echo " Phase 2 - Parallel Implementation"
echo "========================================"
echo ""

# Kill existing process on port 5011
if lsof -ti:5011 > /dev/null 2>&1; then
    echo "Cleaning up existing process on port 5011..."
    lsof -ti:5011 | xargs kill -9 2>/dev/null
    sleep 1
fi

echo "Starting Tickets MCP Server..."
echo "  → MCP Endpoint: http://localhost:5011/mcp"
echo "  → Health Check: http://localhost:5011/health"
echo ""

python tickets_mcp_server/app.py
```

5. **Make script executable:**
```bash
chmod +x scripts/start_tickets_mcp_server.sh
```

6. **Test the MCP server:**

```bash
# Terminal 1: Start server
./scripts/start_tickets_mcp_server.sh

# Terminal 2: Test endpoints
curl http://localhost:5011/health
curl http://localhost:5011/mcp/tools/list
curl -X POST http://localhost:5011/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_all_tickets", "arguments": {}}'
```

**Success Criteria:**
- [ ] MCP server starts on port 5011
- [ ] Health endpoint returns 200
- [ ] MCP tools/list shows 4 tools
- [ ] get_all_tickets returns ticket data
- [ ] Existing server on 5001 still running

**Critical Notes:**
- Use FastMCP (CORRECT), not invented APIs
- Port 5011 (NEW), not 5001 (existing unchanged)
- No authentication in Part A - focus on getting MCP working first

---

### **Task 3: Build FinOps MCP Server (Port 5012)**

**Priority:** Critical
**Dependencies:** Task 1
**Estimated Time:** 2.5 hours

**Objective:**
Create FinOps MCP server using same FastMCP pattern on port 5012.

**Implementation:**

Follow same pattern as Task 2:

1. Create `finops_mcp_server/` directory structure
2. Create `server.py` with FastMCP tools:
   - `get_all_clouds_cost()`
   - `get_cloud_cost(provider: str)`
   - `get_service_cost(provider: str, service_name: str)`
   - `get_cost_breakdown()`
3. Create `app.py` mounting MCP to FastAPI (port 5012)
4. Create `scripts/start_finops_mcp_server.sh`
5. Test MCP server independently

**Success Criteria:**
- [ ] MCP server runs on port 5012
- [ ] All FinOps tools discoverable via MCP
- [ ] Health check working
- [ ] Existing port 5002 untouched

**Notes:**
- Same data as existing FinOps server
- FinOps is organization-wide (no user filtering in Part A)

---

### **Task 4: Build Oxygen MCP Server (Port 8012)**

**Priority:** Critical
**Dependencies:** Task 1
**Estimated Time:** 3 hours

**Objective:**
Create Oxygen MCP server on port 8012 (parallel to existing A2A agent on 8002).

**Implementation:**

1. Create `oxygen_mcp_server/` directory
2. Create `server.py` with tools:
   - `get_user_courses(username: str)`
   - `get_pending_exams(username: str)`
   - `get_user_preferences(username: str)`
   - `get_learning_summary(username: str)`
3. Create `app.py` (port 8012)
4. Create startup script
5. Test MCP server

**Success Criteria:**
- [ ] MCP server runs on port 8012
- [ ] Learning tools accessible via MCP
- [ ] Existing A2A agent on 8002 untouched

**Notes:**
- This REPLACES A2A for MCP solution
- Oxygen will be MCP server, not A2A agent
- Simpler than A2A for this use case

---

### **Task 5: Create MCP Agent Factory Pattern**

**Priority:** Critical
**Dependencies:** Tasks 2, 3, 4
**Estimated Time:** 4 hours

**Objective:**
Create agent factory functions that use ADK's McpToolset to connect to MCP servers.

**Implementation:**

1. **Create `jarvis_agent/mcp_agents/` directory:**
```bash
mkdir -p jarvis_agent/mcp_agents
touch jarvis_agent/mcp_agents/__init__.py
```

2. **Create `jarvis_agent/mcp_agents/tickets_agent.py`:**

```python
"""
Tickets Agent using MCP Client (McpToolset).
Connects to Tickets MCP Server on port 5011.
"""

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

GEMINI_2_5_FLASH = "gemini-2.5-flash"


def create_tickets_agent() -> LlmAgent:
    """
    Create Tickets agent with MCP client (NO AUTH in Part A).

    Returns:
        Configured LlmAgent with MCP toolset
    """

    # Create MCP toolset connected to tickets MCP server
    # Using SSE connection for HTTP-based MCP server
    tickets_toolset = McpToolset(
        connection_params=SseConnectionParams(
            url="http://localhost:5011/mcp",  # FastMCP HTTP endpoint
            # NOTE: No headers needed! Authentication uses ADK state management.
            #
            # Why no headers?
            # - Task 5 (here): No auth yet
            # - Tasks 10-16: Auth uses ADK session state pattern
            #   * HTTP layer extracts Bearer token from request
            #   * Token stored in session.state["user:bearer_token"]
            #   * Tools access via tool_context.state.get("user:bearer_token")
            #   * McpToolset just provides transport - doesn't need token!
            #
            # This is the CORRECT ADK pattern from the start.
        ),
        tool_name_prefix="tickets_"  # Optional: prefix tool names for clarity
    )

    # Create agent with MCP tools
    agent = LlmAgent(
        name="TicketsAgent",
        model=GEMINI_2_5_FLASH,
        description="Agent to manage IT operations tickets via MCP protocol",
        instruction="""You are a tickets management agent using MCP tools.

Your MCP tools (auto-discovered from MCP server):
- tickets_get_all_tickets: List all tickets in the system
- tickets_get_ticket: Get specific ticket by ID
- tickets_get_user_tickets: Get tickets for a specific user
- tickets_create_ticket: Create new ticket

When users ask about tickets:
1. Use tickets_get_all_tickets to see all tickets
2. Use tickets_get_user_tickets(username) to filter by user
3. Use tickets_create_ticket(operation, user) to create tickets

Always provide clear, helpful responses.""",
        tools=[tickets_toolset],  # MCP toolset auto-discovers all tools
    )

    return agent
```

3. **Create `jarvis_agent/mcp_agents/finops_agent.py`:**
```python
"""FinOps Agent using MCP Client."""

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

GEMINI_2_5_FLASH = "gemini-2.5-flash"


def create_finops_agent() -> LlmAgent:
    """Create FinOps agent with MCP client (NO AUTH in Part A)."""

    finops_toolset = McpToolset(
        connection_params=SseConnectionParams(
            url="http://localhost:5012/mcp",
        ),
        tool_name_prefix="finops_"
    )

    agent = LlmAgent(
        name="FinOpsAgent",
        model=GEMINI_2_5_FLASH,
        description="Agent to provide cloud financial operations data via MCP",
        instruction="""You are a FinOps agent using MCP tools.

Your MCP tools:
- finops_get_all_clouds_cost: Get total cost across all cloud providers
- finops_get_cloud_cost: Get cost for specific provider (aws, gcp, azure)
- finops_get_service_cost: Get cost for specific service
- finops_get_cost_breakdown: Get detailed cost breakdown

Always provide cost data with context and insights.""",
        tools=[finops_toolset],
    )

    return agent
```

4. **Create `jarvis_agent/mcp_agents/oxygen_agent.py`:**
```python
"""Oxygen Agent using MCP Client."""

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

GEMINI_2_5_FLASH = "gemini-2.5-flash"


def create_oxygen_agent() -> LlmAgent:
    """Create Oxygen agent with MCP client (NO AUTH in Part A)."""

    oxygen_toolset = McpToolset(
        connection_params=SseConnectionParams(
            url="http://localhost:8012/mcp",
        ),
        tool_name_prefix="oxygen_"
    )

    agent = LlmAgent(
        name="OxygenAgent",
        model=GEMINI_2_5_FLASH,
        description="Agent for learning and development platform via MCP",
        instruction="""You are an Oxygen learning platform agent using MCP tools.

Your MCP tools:
- oxygen_get_user_courses: Get enrolled and completed courses for a user
- oxygen_get_pending_exams: Get pending exams with deadlines
- oxygen_get_user_preferences: Get learning preferences
- oxygen_get_learning_summary: Get complete learning journey

Always ask for username when needed in Part A.""",
        tools=[oxygen_toolset],
    )

    return agent
```

5. **Create `jarvis_agent/mcp_agents/agent_factory.py`:**
```python
"""
Root Agent Factory - MCP Version
Creates Jarvis root orchestrator with MCP-based sub-agents.
Part A: No authentication (will be added in Part B)
"""

from google.adk.agents import LlmAgent
from jarvis_agent.mcp_agents.tickets_agent import create_tickets_agent
from jarvis_agent.mcp_agents.finops_agent import create_finops_agent
from jarvis_agent.mcp_agents.oxygen_agent import create_oxygen_agent

GEMINI_2_5_FLASH = "gemini-2.5-flash"


def create_root_agent() -> LlmAgent:
    """
    Create root orchestrator agent with MCP-based sub-agents.
    Part A: No authentication (auth added in Part B)

    Returns:
        Configured Jarvis root orchestrator
    """

    # Create MCP-based sub-agents
    tickets_agent = create_tickets_agent()
    finops_agent = create_finops_agent()
    oxygen_agent = create_oxygen_agent()

    # Create root orchestrator
    root_agent = LlmAgent(
        name="JarvisOrchestrator",
        model=GEMINI_2_5_FLASH,
        description="Jarvis - Your intelligent IT operations and learning assistant (MCP version)",
        instruction="""You are Jarvis, an intelligent assistant using MCP protocol.

**IT Operations:**
- **Tickets**: Use TicketsAgent to view, search, and create IT tickets
- **FinOps**: Use FinOpsAgent to get cloud cost information

**Learning & Development:**
- **Courses & Exams**: Use OxygenAgent to check user's courses and exams

Route user requests to the appropriate sub-agent based on the query.
Always provide helpful, clear responses.""",
        sub_agents=[tickets_agent, finops_agent, oxygen_agent],
    )

    return root_agent
```

**Success Criteria:**
- [ ] Agent factory functions created
- [ ] McpToolset connects to all 3 MCP servers
- [ ] Tools auto-discovered from MCP servers
- [ ] Root agent can delegate to sub-agents

**Critical Notes:**
- This is the CORRECT pattern (McpToolset + SseConnectionParams)
- No headers/auth in Part A - focus on getting connectivity working
- Tool discovery is automatic (no manual registration)

---

### **Task 6: Create MCP CLI (main_mcp.py)**

**Priority:** High
**Dependencies:** Task 5
**Estimated Time:** 2 hours

**Objective:**
Create NEW CLI entry point for MCP solution (parallel to existing main.py).

**Implementation:**

Create `main_mcp.py`:

```python
#!/usr/bin/env python3
"""
Agentic Jarvis - MCP Version CLI
Phase 2 - Part A: NO authentication yet (basic testing)
"""

from jarvis_agent.mcp_agents.agent_factory import create_root_agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types


def main():
    """Main CLI entry point for MCP version (no auth in Part A)."""

    print("=" * 60)
    print("  JARVIS - MCP Version (Phase 2 - Part A)")
    print("  NO Authentication Yet (Testing MCP Connectivity)")
    print("=" * 60)
    print()
    print("  Connected to MCP servers:")
    print("    - Tickets MCP: http://localhost:5011/mcp")
    print("    - FinOps MCP: http://localhost:5012/mcp")
    print("    - Oxygen MCP: http://localhost:8012/mcp")
    print()
    print("  Type 'exit' or 'quit' to end session")
    print("-" * 60)
    print()

    # Create MCP-based root agent
    root_agent = create_root_agent()

    # Create session service
    session_service = InMemorySessionService()
    session_id = "mcp-cli-session"
    user_id = "test_user"  # Hardcoded for Part A

    # Create session
    session_service.create_session_sync(
        app_name="jarvis_mcp",
        user_id=user_id,
        session_id=session_id
    )

    # Create runner
    runner = Runner(
        app_name="jarvis_mcp",
        agent=root_agent,
        session_service=session_service
    )

    # Interactive loop
    while True:
        try:
            user_input = input("\nmcp> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break

            # Create message
            new_message = types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            )

            # Run agent and print response
            print()
            for event in runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message
            ):
                if event.content and event.content.parts and event.author != "user":
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(part.text, end='', flush=True)

            print()  # Newline after response

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
```

**Success Criteria:**
- [ ] MCP CLI starts successfully
- [ ] Can query MCP-based agents
- [ ] Test queries: "show all tickets", "what is AWS cost?", "show courses for vishal"
- [ ] Existing main.py CLI still works

---

### **Task 7: Create MCP Web UI (Port 9990)**

**Priority:** High
**Dependencies:** Task 5
**Estimated Time:** 3 hours

**Objective:**
Create simple web UI for MCP solution on port 9990 (NO AUTH in Part A).

**Implementation:**

Create `web_ui/server_mcp.py`:

```python
"""
Jarvis MCP Web Interface (NO AUTH - Part A)
Phase 2 - Parallel Implementation
Port: 9990 (NEW - parallel to 9999)
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from jarvis_agent.mcp_agents.agent_factory import create_root_agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
import uvicorn

app = FastAPI(title="Jarvis MCP Web Interface (No Auth)")

# Session service
session_service = InMemorySessionService()

# Create MCP agent once for Part A (no per-request creation yet)
root_agent = create_root_agent()

class ChatMessage(BaseModel):
    message: str
    session_id: str = "web-session-default"


@app.get("/")
async def root():
    """Serve simple chat page (no login in Part A)."""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Jarvis MCP (Part A - No Auth)</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        #messages { border: 1px solid #ccc; height: 400px; overflow-y: scroll; padding: 10px; }
        #input { width: 80%; padding: 10px; }
        button { padding: 10px 20px; }
        .user { color: blue; }
        .assistant { color: green; }
    </style>
</head>
<body>
    <h1>🤖 Jarvis MCP (Phase 2 - Part A)</h1>
    <p><strong>NOTE:</strong> No authentication yet. Testing MCP connectivity.</p>
    <p>Connected to: Tickets (5011), FinOps (5012), Oxygen (8012)</p>
    <hr>
    <div id="messages"></div>
    <br>
    <input type="text" id="input" placeholder="Type your message...">
    <button onclick="send()">Send</button>

    <script>
        const messages = document.getElementById('messages');
        const input = document.getElementById('input');

        async function send() {
            const msg = input.value.trim();
            if (!msg) return;

            // Add user message
            messages.innerHTML += `<p class="user"><strong>You:</strong> ${msg}</p>`;
            input.value = '';

            // Send to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg})
            });

            const data = await response.json();
            messages.innerHTML += `<p class="assistant"><strong>Jarvis:</strong> ${data.response}</p>`;
            messages.scrollTop = messages.scrollHeight;
        }

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') send();
        });
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


@app.post("/api/chat")
async def chat(chat_message: ChatMessage):
    """Send message to Jarvis MCP version (no auth in Part A)."""
    try:
        session_id = chat_message.session_id
        user_id = "web_user"  # Hardcoded for Part A

        # Create session if not exists
        try:
            session_service.create_session_sync(
                app_name="jarvis_mcp",
                user_id=user_id,
                session_id=session_id
            )
        except:
            pass  # Session already exists

        # Create runner
        runner = Runner(
            app_name="jarvis_mcp",
            agent=root_agent,
            session_service=session_service
        )

        # Prepare message
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=chat_message.message)]
        )

        # Run agent and collect response
        response_text = ""
        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
        ):
            if event.content and event.content.parts and event.author != "user":
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text

        return {
            "success": True,
            "response": response_text if response_text else "Processing..."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "version": "mcp", "port": 9990}


if __name__ == "__main__":
    print("=" * 70)
    print(" Jarvis MCP Web Interface (Phase 2 - Part A: No Auth)")
    print("=" * 70)
    print()
    print("  Web UI: http://localhost:9990/")
    print("  Health: http://localhost:9990/health")
    print()
    print("  NOTE: No authentication in Part A (testing MCP only)")
    print("  NOTE: Existing web UI on port 9999 is UNCHANGED")
    print("=" * 70)
    print()

    uvicorn.run(app, host="0.0.0.0", port=9990)
```

Create startup script `scripts/start_web_mcp.sh`:

```bash
#!/bin/bash

echo "========================================"
echo " Jarvis MCP Web UI (Port 9990)"
echo " Phase 2 - Part A: No Auth"
echo "========================================"
echo ""

# Kill existing process on port 9990
if lsof -ti:9990 > /dev/null 2>&1; then
    echo "Cleaning up existing process on port 9990..."
    lsof -ti:9990 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Check if MCP servers are running
echo "Checking MCP servers..."
services_ok=true

if ! lsof -ti:5011 > /dev/null 2>&1; then
    echo "❌ Tickets MCP server not running on port 5011"
    services_ok=false
fi

if ! lsof -ti:5012 > /dev/null 2>&1; then
    echo "❌ FinOps MCP server not running on port 5012"
    services_ok=false
fi

if ! lsof -ti:8012 > /dev/null 2>&1; then
    echo "❌ Oxygen MCP server not running on port 8012"
    services_ok=false
fi

if [ "$services_ok" = false ]; then
    echo ""
    echo "Please start MCP servers first:"
    echo "  ./scripts/restart_all_mcp.sh"
    exit 1
fi

echo "✓ All MCP servers running"
echo ""
echo "Starting MCP Web UI..."
echo "  → http://localhost:9990/"
echo ""

python web_ui/server_mcp.py
```

**Success Criteria:**
- [ ] MCP Web UI runs on port 9990
- [ ] Can chat with Jarvis via web interface
- [ ] MCP tool calls work through UI
- [ ] Existing web UI on 9999 untouched

---

### **Task 8: Create All-In-One Startup Script for MCP**

**Priority:** Medium
**Dependencies:** Tasks 2-7
**Estimated Time:** 1 hour

**Objective:**
Create script to start all MCP services in background.

**Implementation:**

Create `scripts/restart_all_mcp.sh`:

```bash
#!/bin/bash

echo "================================================================"
echo " Jarvis MCP Solution - All Services (Phase 2 - Part A)"
echo " Parallel Implementation (Existing system on 5001/5002/8002 unchanged)"
echo "================================================================"
echo ""

echo "Step 1: Stopping existing MCP services..."
lsof -ti:5011 | xargs kill -9 2>/dev/null  # Tickets MCP
lsof -ti:5012 | xargs kill -9 2>/dev/null  # FinOps MCP
lsof -ti:8012 | xargs kill -9 2>/dev/null  # Oxygen MCP
lsof -ti:9990 | xargs kill -9 2>/dev/null  # Web MCP

echo "  ✓ Stopped MCP services"
echo ""

sleep 2

echo "Step 2: Starting MCP services in background..."
echo ""

# Create logs directory
mkdir -p logs

# Start MCP Servers
echo "Starting Tickets MCP Server (port 5011)..."
nohup python tickets_mcp_server/app.py > logs/tickets_mcp.log 2>&1 &
sleep 2

echo "Starting FinOps MCP Server (port 5012)..."
nohup python finops_mcp_server/app.py > logs/finops_mcp.log 2>&1 &
sleep 2

echo "Starting Oxygen MCP Server (port 8012)..."
nohup python oxygen_mcp_server/app.py > logs/oxygen_mcp.log 2>&1 &
sleep 2

# Start MCP Web UI
echo "Starting MCP Web UI (port 9990)..."
nohup python web_ui/server_mcp.py > logs/web_mcp.log 2>&1 &
sleep 2

echo ""
echo "Step 3: Verifying MCP services..."
echo ""

# Verify each MCP service
for port in 5011 5012 8012 9990; do
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "✓ MCP service running on port $port"
    else
        echo "❌ MCP service failed to start on port $port"
    fi
done

echo ""
echo "================================================================"
echo "✓ MCP Solution Started!"
echo ""
echo "MCP Services (NEW):"
echo "  • Tickets MCP:  http://localhost:5011/mcp"
echo "  • FinOps MCP:   http://localhost:5012/mcp"
echo "  • Oxygen MCP:   http://localhost:8012/mcp"
echo "  • Web UI (MCP): http://localhost:9990/"
echo ""
echo "Existing Services (UNCHANGED):"
echo "  • Tickets:      http://localhost:5001/"
echo "  • FinOps:       http://localhost:5002/"
echo "  • Oxygen:       http://localhost:8002/"
echo "  • Web UI:       http://localhost:9999/"
echo ""
echo "Test MCP CLI:"
echo "  python main_mcp.py"
echo ""
echo "Logs: logs/*_mcp.log"
echo "================================================================"
```

Make executable:
```bash
chmod +x scripts/restart_all_mcp.sh
```

**Success Criteria:**
- [ ] Script starts all 4 MCP services
- [ ] All services verified running
- [ ] Can access MCP Web UI on 9990
- [ ] Existing services on 5001/5002/8002/9999 still running

---

## Part B: Add JWT Authentication (Tasks 9-16)

### **Task 9: Create JWT Authentication Infrastructure (Shared)**

**Priority:** Critical
**Dependencies:** Part A complete
**Estimated Time:** 2 hours

**Objective:**
Create shared JWT utilities and user service (used by both solutions).

**Implementation:**

**Already exists from existing implementation - VERIFY and DOCUMENT:**

1. Verify `auth/jwt_utils.py` exists with:
   - `create_jwt_token(username, user_id)`
   - `verify_jwt_token(token)`
   - `extract_user_from_token(token)`

2. Verify `auth/user_service.py` exists with:
   - `authenticate_user(username, password)`
   - `get_user_info(username)`
   - Mock users: vishal, alex, sarah

3. Verify `auth/auth_server.py` exists (port 9998)

4. Test auth service:
```bash
# Start auth service
./scripts/start_auth_service.sh

# Test login
curl -X POST http://localhost:9998/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "vishal", "password": "password123"}'
```

**Success Criteria:**
- [ ] Auth service running on 9998
- [ ] Login returns JWT token
- [ ] Token verification works
- [ ] Shared by both solutions

---

### **Task 10: Add ADK-Compliant Authentication to Tickets MCP Server**

**Priority:** Critical
**Dependencies:** Task 9
**Estimated Time:** 2.5 hours

**Objective:**
Add JWT validation and authenticated tools using ADK's ToolContext pattern.

**✅ ADK-COMPLIANT PATTERN:** This task uses `ToolContext` (NOT `bearer_token` parameter) from the start.

**Implementation:**

Update `tickets_mcp_server/server.py`:

```python
# Add at top
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from auth.jwt_utils import verify_jwt_token
from google.adk.tools import ToolContext

# Add authenticated tools (ADK pattern)
@mcp.tool()
def get_my_tickets(tool_context: ToolContext) -> List[Dict]:
    """Get tickets for the authenticated user.

    This tool requires authentication via ADK session state.
    Returns tickets that belong to the authenticated user.

    Args:
        tool_context: Automatically injected by ADK framework

    Returns:
        List of tickets belonging to the authenticated user, or error dict
    """
    # Get bearer token from session state (ADK pattern)
    bearer_token = tool_context.state.get("user:bearer_token")

    if not bearer_token:
        return {
            "error": "Authentication required",
            "status": 401,
            "message": "Please log in to access your tickets"
        }

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
    return [t for t in TICKETS_DB if t['user'].lower() == current_user.lower()]


@mcp.tool()
def create_my_ticket(operation: str, tool_context: ToolContext) -> Dict:
    """Create a new ticket for the authenticated user.

    Args:
        operation: The operation type
        tool_context: Automatically injected by ADK framework

    Returns:
        Created ticket details or error dict
    """
    # Get bearer token from session state (ADK pattern)
    bearer_token = tool_context.state.get("user:bearer_token")

    if not bearer_token:
        return {
            "error": "Authentication required",
            "status": 401
        }

    payload = verify_jwt_token(bearer_token)
    if not payload:
        return {
            "error": "Invalid or expired token",
            "status": 401
        }

    current_user = payload.get("username")
    if not current_user:
        return {
            "error": "Token missing username claim",
            "status": 401
        }

    new_id = max([t['id'] for t in TICKETS_DB]) + 1 if TICKETS_DB else 1

    new_ticket = {
        "id": new_id,
        "operation": operation,
        "user": current_user,  # Use authenticated user
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }

    TICKETS_DB.append(new_ticket)

    return {
        "success": True,
        "ticket": new_ticket,
        "message": f"Ticket {new_id} created for {current_user}"
    }
```

Update agent instructions in `jarvis_agent/mcp_agents/tickets_agent.py`:

```python
instruction="""You are a tickets management agent using MCP tools.

**Public tools** (no authentication):
- tickets_get_all_tickets: List all tickets
- tickets_get_ticket: Get specific ticket by ID
- tickets_get_user_tickets: Get tickets for specified user
- tickets_create_ticket: Create ticket for specified user

**Authenticated tools** (require login):
- tickets_get_my_tickets: Get tickets for authenticated user
- tickets_create_my_ticket: Create ticket for authenticated user

Authentication is handled automatically via ADK session state.
When user says "my tickets" or "create a ticket", use authenticated tools."""
```

**Success Criteria:**
- [ ] `get_my_tickets` uses `tool_context: ToolContext` (NOT bearer_token parameter)
- [ ] `create_my_ticket` uses `tool_context: ToolContext`
- [ ] Tools access token via `tool_context.state.get("user:bearer_token")`
- [ ] Invalid/missing tokens return proper error dicts
- [ ] Tool discovery shows 6 tools (4 public + 2 auth)
- [ ] ADK-compliant from the start (no refactoring needed later)

---

### **Task 11: Add ADK-Compliant Authentication to FinOps and Oxygen MCP Servers**

**Priority:** High
**Dependencies:** Task 10
**Estimated Time:** 2.5 hours

**Objective:**
Add authenticated tools using ADK ToolContext pattern to remaining MCP servers.

**✅ ADK-COMPLIANT PATTERN:** Uses `ToolContext` (NOT `bearer_token` parameters).

**Implementation:**

1. **FinOps:** (Optional - FinOps is organization-wide)
   - Add JWT validation infrastructure using ToolContext pattern
   - No authenticated tools needed yet (costs are global)
   - Infrastructure ready for future user-specific cost features

2. **Oxygen:** Add authenticated tools using ToolContext:

```python
from google.adk.tools import ToolContext
from auth.jwt_utils import verify_jwt_token

@mcp.tool()
def get_my_courses(tool_context: ToolContext) -> Dict:
    """Get courses for authenticated user."""
    bearer_token = tool_context.state.get("user:bearer_token")
    if not bearer_token:
        return {"error": "Authentication required", "status": 401}

    payload = verify_jwt_token(bearer_token)
    if not payload:
        return {"error": "Invalid or expired token", "status": 401}

    current_user = payload.get("username")
    # Return user-specific data...

@mcp.tool()
def get_my_exams(tool_context: ToolContext) -> Dict:
    """Get pending exams for authenticated user."""
    # Same ToolContext pattern...

@mcp.tool()
def get_my_preferences(tool_context: ToolContext) -> Dict:
    """Get learning preferences for authenticated user."""
    # Same ToolContext pattern...

@mcp.tool()
def get_my_learning_summary(tool_context: ToolContext) -> Dict:
    """Get complete learning summary for authenticated user."""
    # Same ToolContext pattern...
```

**Success Criteria:**
- [ ] Oxygen has 4 public + 4 auth tools
- [ ] All authenticated tools use `tool_context: ToolContext` (NOT bearer_token parameter)
- [ ] Tools access token via `tool_context.state.get("user:bearer_token")`
- [ ] FinOps ready for future auth tools with ToolContext pattern
- [ ] All tools validate JWT correctly
- [ ] ADK-compliant from the start

---

### **Task 12: Create ADK Callbacks for Centralized Authentication**

**Priority:** Critical
**Dependencies:** Tasks 10, 11
**Estimated Time:** 3 hours

**Objective:**
Create ADK callbacks module for centralized authentication enforcement using `before_tool_callback`.

**✅ ADK-COMPLIANT PATTERN:** Uses callbacks + App pattern (NOT per-request agent creation).

**Implementation:**

**Create:** `jarvis_agent/callbacks.py`

```python
"""
ADK Callbacks for Authentication and Policy Enforcement.
Implements centralized authentication via before_tool_callback.

See: https://google.github.io/adk-docs/callbacks/
"""

from google.adk.callbacks import CallbackContext
from auth.jwt_utils import verify_jwt_token
from typing import Optional

# Tools that require authentication (ADK pattern)
AUTHENTICATED_TOOLS = {
    "tickets_get_my_tickets",
    "tickets_create_my_ticket",
    "oxygen_get_my_courses",
    "oxygen_get_my_exams",
    "oxygen_get_my_preferences",
    "oxygen_get_my_learning_summary"
}


def before_tool_callback(context: CallbackContext) -> Optional[dict]:
    """
    Validate authentication before tool execution.

    This callback intercepts tool calls BEFORE execution to:
    1. Validate authentication for sensitive tools
    2. Enforce policy (block unauthenticated access)
    3. Cache user info for this invocation

    IMPORTANT: This callback reads bearer token from context.state,
    which was populated by the Web UI/CLI layer before agent execution.

    Args:
        context: Callback context with state and function call info

    Returns:
        None: Allow tool execution
        dict: Return this result instead (blocks tool execution)
    """

    tool_name = context.function_call.name

    # Check if tool requires authentication
    if tool_name in AUTHENTICATED_TOOLS:
        bearer_token = context.state.get("user:bearer_token")

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
                "message": "Your session has expired. Please log in again."
            }

        # Store current user info in temporary state (this invocation only)
        context.state["temp:current_user"] = payload.get("username")
        context.state["temp:user_id"] = payload.get("user_id")

    # Allow tool to execute normally
    return None


def after_tool_callback(context: CallbackContext, result: dict) -> dict:
    """
    Post-process tool results for security (optional).

    Args:
        context: Callback context
        result: Tool execution result

    Returns:
        Modified result (with sensitive data masked if needed)
    """

    # Mask any bearer tokens that might have leaked into results
    result_str = str(result)

    if "bearer" in result_str.lower() or "eyJ" in result_str:
        print(f"⚠️ WARNING: Tool {context.function_call.name} returned sensitive data")

        # In production, mask the token
        # result = mask_sensitive_data(result)

    return result
```

Update `jarvis_agent/mcp_agents/agent_factory.py` to create agents ONCE:

```python
def create_root_agent() -> LlmAgent:
    """
    Create root agent ONCE (NO bearer_token parameter).

    Authentication handled via ADK callbacks and session state.
    Agents are created ONCE at startup, not per-request.

    Returns:
        Jarvis root orchestrator
    """

    # Create sub-agents ONCE (not per-request)
    # No bearer_token parameters - auth uses state management
    tickets_agent = create_tickets_agent()
    finops_agent = create_finops_agent()
    oxygen_agent = create_oxygen_agent()

    root_agent = LlmAgent(
        name="JarvisOrchestrator",
        model=GEMINI_2_5_FLASH,
        description="Jarvis AI Assistant",
        instruction="""...""",
        sub_agents=[tickets_agent, finops_agent, oxygen_agent]
    )

    return root_agent


# Create root agent ONCE at module import (not per-request!)
root_agent = create_root_agent()
```

**Success Criteria:**
- [ ] `jarvis_agent/callbacks.py` created with `before_tool_callback`
- [ ] Callback validates authentication for AUTHENTICATED_TOOLS
- [ ] Callback blocks execution and returns error dict if auth fails
- [ ] Agents created ONCE (no bearer_token parameters in agent factory)
- [ ] Performance: No per-request agent creation overhead
- [ ] Security: Bearer token never exposed as agent parameter
- [ ] ADK-compliant from the start

---

### **Task 13: Update MCP CLI with ADK App Pattern**

**Priority:** High
**Dependencies:** Task 12
**Estimated Time:** 2.5 hours

**Objective:**
Add login flow to MCP CLI using ADK App pattern with callbacks and session state.

**✅ ADK-COMPLIANT PATTERN:** Uses `App` with callbacks (NOT per-request agent creation).

**Implementation:**

Update `main_mcp.py`:

```python
#!/usr/bin/env python3
"""
Agentic Jarvis - MCP Version CLI with ADK-Compliant Authentication
Uses App pattern with callbacks and session state.
"""

import requests
import getpass
from google.adk.apps import App
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from jarvis_agent.callbacks import before_tool_callback, after_tool_callback
from jarvis_agent.mcp_agents.agent_factory import root_agent  # Created once at import
from google.genai import types


def login():
    """Authenticate user and return JWT token."""
    print("\n" + "=" * 60)
    print("🔐 Jarvis MCP Authentication (ADK Pattern)")
    print("=" * 60)

    username = input("\nUsername: ").strip()
    password = getpass.getpass("Password: ")

    try:
        response = requests.post(
            "http://localhost:9998/auth/login",
            json={"username": username, "password": password}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Welcome, {username}!")
            # Return both token and user info
            return data.get("access_token") or data.get("token"), username, data.get("user", {})
        else:
            print("\n❌ Authentication failed.")
            return None, None, None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None, None, None


def main():
    """Main CLI entry point using ADK App pattern."""

    # Create App ONCE with callbacks
    # Agents are created ONCE at module import (NOT per-request)
    adk_app = App(
        name="jarvis_mcp",
        root_agent=root_agent,  # Single instance from agent_factory
        session_service=InMemorySessionService(),
        before_tool_callback=before_tool_callback,
        after_tool_callback=after_tool_callback
    )

    # Login first
    token, username, user_info = login()

    if not token or not username:
        print("\nExiting...")
        return

    # Get user_id from user_info or use username as fallback
    user_id = user_info.get("user_id", username)
    session_id = f"cli-{user_id}"

    # Create session
    session = adk_app.session_service.create_session_sync(
        app_name="jarvis_mcp",
        user_id=user_id,
        session_id=session_id
    )

    # CRITICAL: Store bearer token in SESSION STATE (ADK pattern)
    session.state["user:bearer_token"] = token
    session.state["user:username"] = username
    session.state["user:user_id"] = user_id

    # Update session with authentication state
    adk_app.session_service.update_session_sync(session)

    print("\n" + "=" * 60)
    print(f"  Session initialized for {username}")
    print("  Authentication stored in session state")
    print("  Type 'exit' or 'quit' to end session")
    print("=" * 60 + "\n")

    # Interactive chat loop (NO per-request agent creation!)
    while True:
        try:
            user_input = input(f"{username}> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break

            # Run agent using App (reads token from session state)
            # before_tool_callback will validate auth for sensitive tools
            response_text = ""
            for event in adk_app.run(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=user_input)]
                )
            ):
                if event.content and event.content.parts and event.author != "user":
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(part.text, end='', flush=True)
                            response_text += part.text

            print()  # Newline after response

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
```

**Success Criteria:**
- [ ] CLI uses `App` pattern (NOT `Runner`)
- [ ] Callbacks registered (`before_tool_callback`, `after_tool_callback`)
- [ ] Login flow obtains JWT token
- [ ] Bearer token stored in `session.state["user:bearer_token"]` (NOT passed to agent)
- [ ] Agents created ONCE (imported from agent_factory, NOT created per-request)
- [ ] Authenticated queries work ("show my tickets")
- [ ] before_tool_callback validates auth automatically
- [ ] ADK-compliant from the start

---

### **Task 14: Update MCP Web UI with ADK App Pattern**

**Priority:** High
**Dependencies:** Task 12
**Estimated Time:** 4 hours

**Objective:**
Add login page and ADK-compliant authentication to MCP Web UI using App pattern with callbacks.

**✅ ADK-COMPLIANT PATTERN:** Uses `App` with callbacks and session state (NOT per-request agent creation).

**Implementation:**

Update `web_ui/server_mcp.py`:

```python
"""
Jarvis MCP Web Interface with ADK-Compliant Authentication
Uses App pattern with callbacks and session state.
Port: 9990
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google.adk.apps import App
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from jarvis_agent.callbacks import before_tool_callback, after_tool_callback
from jarvis_agent.mcp_agents.agent_factory import root_agent  # Created once at import
from auth.jwt_utils import verify_jwt_token
from google.genai import types
import uvicorn

app = FastAPI(title="Jarvis MCP Web Interface")

# Create App ONCE with callbacks
# Agents created ONCE at module import (NOT per-request)
adk_app = App(
    name="jarvis_mcp",
    root_agent=root_agent,  # Single instance
    session_service=InMemorySessionService(),
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback
)


class ChatMessage(BaseModel):
    message: str
    session_id: str = "web-session-default"


@app.get("/")
async def root():
    """Serve login/chat page."""
    # HTML with login and chat interface
    # (Similar to existing web UI, but uses ADK pattern)
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Jarvis MCP (ADK Pattern)</title>
    <!-- Include login page and chat interface -->
</head>
</html>
"""
    return HTMLResponse(content=html)


@app.post("/api/chat")
async def chat(
    chat_message: ChatMessage,
    authorization: str = Header(None)
):
    """
    Chat endpoint with ADK-compliant authentication.

    CRITICAL: This endpoint does NOT create agents per-request!
    Instead, it:
    1. Extracts bearer token from HTTP header
    2. Stores token in session state
    3. Runs agent (which reads token from state via callbacks)
    """

    # Extract bearer token from Authorization header
    bearer_token = None
    if authorization and authorization.startswith("Bearer "):
        bearer_token = authorization.split(" ")[1]

    # Validate token and extract user info
    user_id = "anonymous"
    username = "anonymous"
    if bearer_token:
        payload = verify_jwt_token(bearer_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_id = payload.get("user_id", "anonymous")
        username = payload.get("username", "anonymous")

    session_id = f"web-{user_id}"

    # Get or create session
    try:
        session = adk_app.session_service.get_session_sync(
            app_name="jarvis_mcp",
            user_id=user_id,
            session_id=session_id
        )
    except:
        session = adk_app.session_service.create_session_sync(
            app_name="jarvis_mcp",
            user_id=user_id,
            session_id=session_id
        )

    # CRITICAL: Store bearer token in SESSION STATE (ADK pattern)
    # This is how authentication flows to tools via ToolContext
    if bearer_token:
        session.state["user:bearer_token"] = bearer_token
        session.state["user:username"] = username
        session.state["user:user_id"] = user_id

    adk_app.session_service.update_session_sync(session)

    # Run agent (NO per-request agent creation!)
    # before_tool_callback reads token from session.state and validates
    try:
        response_text = ""
        for event in adk_app.run(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=chat_message.message)]
            )
        ):
            if event.content and event.content.parts and event.author != "user":
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text

        return {
            "success": True,
            "response": response_text if response_text else "Processing...",
            "session_id": session_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "version": "mcp_adk", "port": 9990}


if __name__ == "__main__":
    print("=" * 70)
    print(" Jarvis MCP Web Interface (ADK-Compliant Authentication)")
    print("=" * 70)
    print()
    print("  Web UI: http://localhost:9990/")
    print("  Health: http://localhost:9990/health")
    print()
    print("  Pattern: App + Callbacks + Session State")
    print("  Agents: Created ONCE (not per-request)")
    print("  Auth: via session.state['user:bearer_token']")
    print("=" * 70)
    print()

    uvicorn.run(app, host="0.0.0.0", port=9990)
```

Add login page HTML (similar to existing web UI but using ADK pattern).

**Success Criteria:**
- [ ] Web UI uses `App` pattern (NOT `Runner`)
- [ ] Callbacks registered (`before_tool_callback`, `after_tool_callback`)
- [ ] Login page on http://localhost:9990/
- [ ] JWT token stored in localStorage (client-side)
- [ ] Bearer token extracted from Authorization header (server-side)
- [ ] Bearer token stored in `session.state["user:bearer_token"]` (NOT passed to agent)
- [ ] Agents created ONCE (imported from agent_factory, NOT per-request)
- [ ] Authenticated queries work ("show my tickets")
- [ ] before_tool_callback validates auth automatically
- [ ] ADK-compliant from the start

---

### **Task 15: End-to-End Testing of MCP Authentication**

**Priority:** Critical
**Dependencies:** Tasks 13, 14
**Estimated Time:** 3 hours

**Objective:**
Comprehensive testing of MCP solution with authentication.

**Test Scenarios:**

1. **Test MCP CLI:**
```bash
python main_mcp.py
# Login as vishal
# Query: "show my tickets"
# Expected: Only vishal's tickets (12301, 12303)
```

2. **Test MCP Web UI:**
```
1. Open http://localhost:9990/
2. Login as alex
3. Query: "show my tickets"
4. Expected: Only alex's tickets (12302, 12304)
```

3. **Test User Isolation:**
```bash
# Login as vishal in one browser
# Login as alex in another browser
# Both should see only their own data
```

4. **Test Invalid Token:**
```bash
curl -X POST http://localhost:9990/api/chat \
  -H "Authorization: Bearer invalid-token" \
  -H "Content-Type: application/json" \
  -d '{"message": "show my tickets"}'
# Expected: 401 Unauthorized
```

**Success Criteria:**
- [ ] All test scenarios pass
- [ ] User-specific data correctly filtered
- [ ] No authentication bug (tokens reach MCP servers)
- [ ] Invalid tokens rejected

---

### **Task 16: Document MCP vs Toolbox Comparison**

**Priority:** Medium
**Dependencies:** Task 15
**Estimated Time:** 2 hours

**Objective:**
Document differences between MCP and Toolbox solutions.

**Create `docs/MCP_VS_TOOLBOX_COMPARISON.md`:**

```markdown
# MCP vs Toolbox Implementation Comparison

## Architecture

| Aspect | Toolbox (Current) | MCP (New) |
|--------|-------------------|-----------|
| Protocol | Custom | Industry Standard (MCP) |
| Tool Discovery | Manual registration | Automatic |
| Authentication | Context vars (broken) | Per-request headers (working) |
| Server Library | Custom FastAPI | FastMCP |
| Client Library | ToolboxSyncClient | McpToolset |
| Ports | 5001, 5002, 8002 | 5011, 5012, 8012 |

## Authentication Flow

### Toolbox (Broken)
```
User → JWT Token → Agent (static) → ToolboxClient (no token) → Server ❌
```

### MCP (Working)
```
User → JWT Token → Agent Factory → McpToolset (with token) → MCP Server ✅
```

## Code Complexity

**MCP Wins:**
- Less code (FastMCP handles schema generation)
- Auto tool discovery (no manual registration)
- Standard protocol (easier to integrate)

## Recommendation

**Switch to MCP** because:
1. ✅ Authentication works (per-request pattern)
2. ✅ Industry standard protocol
3. ✅ Auto tool discovery
4. ✅ Keycloak-ready
5. ✅ Less maintenance burden
```

**Success Criteria:**
- [ ] Comparison documented
- [ ] Technical differences explained
- [ ] Recommendation provided

---

## Part C: Testing & Documentation (Tasks 17-20)

### **Task 17: Run Both Solutions Simultaneously**

**Priority:** High
**Dependencies:** Part B complete
**Estimated Time:** 1 hour

**Objective:**
Demonstrate parallel implementation - both solutions running side-by-side.

**Implementation:**

1. **Start existing solution:**
```bash
./scripts/restart_all_phase2.sh  # Ports 5001, 5002, 8002, 9999
```

2. **Start MCP solution:**
```bash
./scripts/restart_all_mcp.sh  # Ports 5011, 5012, 8012, 9990
```

3. **Verify both running:**
```bash
# Check existing
curl http://localhost:5001/health
curl http://localhost:9999/  # Should work

# Check MCP
curl http://localhost:5011/health
curl http://localhost:9990/  # Should work
```

4. **Compare in browser:**
```
Tab 1: http://localhost:9999/ (Existing - auth bug)
Tab 2: http://localhost:9990/ (MCP - auth working)

Login to both as vishal
Query: "show my tickets"

Tab 1: ❌ Error or all tickets (auth bug)
Tab 2: ✅ Only vishal's tickets
```

**Success Criteria:**
- [ ] Both solutions running simultaneously
- [ ] No port conflicts
- [ ] Can compare side-by-side
- [ ] MCP auth works, existing fails

---

### **Task 18: Update Environment Configuration**

**Priority:** Medium
**Dependencies:** None
**Estimated Time:** 30 minutes

**Objective:**
Update .env.template with MCP ports.

**Implementation:**

Update `.env.template`:

```bash
# Existing solution ports
TICKETS_SERVER_PORT=5001
FINOPS_SERVER_PORT=5002
OXYGEN_AGENT_PORT=8002
WEB_UI_PORT=9999

# MCP solution ports (Phase 2)
TICKETS_MCP_PORT=5011
FINOPS_MCP_PORT=5012
OXYGEN_MCP_PORT=8012
WEB_UI_MCP_PORT=9990

# Shared
AUTH_SERVICE_PORT=9998
JWT_SECRET_KEY=your-secret-key-change-in-production
```

**Success Criteria:**
- [ ] .env.template updated
- [ ] Both port sets documented
- [ ] Clear labeling of each solution

---

### **Task 19: Create Comprehensive Documentation**

**Priority:** High
**Dependencies:** Tasks 16, 17
**Estimated Time:** 3 hours

**Objective:**
Document Phase 2 implementation, comparison, and next steps.

**Create/Update:**

1. **`PHASE_2_COMPLETE.md`** - Mark Phase 2 as complete
2. **`docs/MCP_MIGRATION_GUIDE.md`** - How to migrate from Toolbox to MCP
3. **`README.md`** - Update with Phase 2 status and MCP info
4. **`CLAUDE.md`** - Update Phase 2 section to "Completed"

**Success Criteria:**
- [ ] All documentation updated
- [ ] Migration guide provided
- [ ] Clear comparison available
- [ ] Next steps documented

---

### **Task 20: Final Validation and Decision**

**Priority:** Critical
**Dependencies:** All previous tasks
**Estimated Time:** 2 hours

**Objective:**
Final validation of Phase 2 and recommendation for production.

**Validation Checklist:**

**MCP Solution:**
- [ ] All 3 MCP servers running (5011, 5012, 8012)
- [ ] MCP Web UI working (9990)
- [ ] MCP CLI working
- [ ] Authentication working correctly
- [ ] User isolation working
- [ ] No authentication bugs

**Existing Solution:**
- [ ] Still running unchanged (5001, 5002, 8002, 9999)
- [ ] Can be used as fallback
- [ ] No code changes made

**Comparison:**
- [ ] Side-by-side testing complete
- [ ] Performance measured
- [ ] Feature parity verified
- [ ] Recommendation documented

**Recommendation:**

Create `PHASE_2_RECOMMENDATION.md`:

```markdown
# Phase 2: Recommendation

## Summary

Phase 2 implemented a **parallel MCP solution** alongside the existing Toolbox solution.

## Results

**MCP Solution (Recommended for Production):**
- ✅ Authentication works correctly (per-request pattern)
- ✅ Industry standard protocol
- ✅ Auto tool discovery
- ✅ Keycloak-ready
- ✅ Cleaner code

**Existing Solution (Deprecated):**
- ❌ Authentication bug (tokens don't reach servers)
- ❌ Custom protocol (maintenance burden)
- ❌ Manual tool registration
- ✅ But still working as fallback

## Recommendation

**Use MCP Solution for Production (Port 9990)**

**Rationale:**
1. Authentication works (critical requirement)
2. Industry standard (better long-term)
3. Lower maintenance burden
4. Ready for Phase 3 (Memory) and Phase 4 (OAuth)

**Migration Path:**
1. Test MCP solution thoroughly in staging
2. Update client apps to use port 9990
3. Deprecate ports 9999, 5001, 5002, 8002
4. Remove old Toolbox code in Phase 3
```

**Success Criteria:**
- [ ] Final validation complete
- [ ] Recommendation documented
- [ ] Migration path clear
- [ ] Phase 2 COMPLETE

---

## Summary

### Task Overview

**Part A: Build MCP Solution (NO AUTH) - 8 tasks**
1. Install FastMCP
2. Build Tickets MCP Server (5011)
3. Build FinOps MCP Server (5012)
4. Build Oxygen MCP Server (8012)
5. Create MCP Agent Factory
6. Create MCP CLI
7. Create MCP Web UI (9990)
8. All-in-one startup script

**Part B: Add ADK-Compliant JWT Authentication - 8 tasks**
9. JWT Infrastructure (shared)
10. Add ToolContext-based auth to Tickets MCP
11. Add ToolContext-based auth to FinOps/Oxygen MCP
12. Create ADK callbacks for centralized authentication
13. Update MCP CLI with App pattern
14. Update MCP Web UI with App pattern
15. End-to-end testing
16. MCP vs Toolbox comparison

**Part C: Testing & Documentation - 4 tasks**
17. Run both solutions simultaneously
18. Update environment config
19. Comprehensive documentation
20. Final validation and recommendation

**Total: 20 tasks**
**Estimated Time: 45-50 hours (~2 weeks)**

---

## ✅ ADK-COMPLIANT FROM THE START

**All authentication tasks (10-16) use the correct ADK pattern:**
- ✅ `ToolContext` for tool authentication (NOT bearer_token parameters)
- ✅ Session state for token storage (`session.state["user:bearer_token"]`)
- ✅ Callbacks for centralized auth enforcement (`before_tool_callback`)
- ✅ App pattern for agent lifecycle (agents created ONCE, not per-request)
- ✅ OAuth 2.0 ready from day one (Phase 4)
- ✅ Production-ready authentication architecture

**No refactoring needed** - the implementation is ADK-compliant throughout.

### Critical Success Factors

1. **Follow the order:** MCP First → Chat UI → ADK-Compliant Authentication
2. **Parallel implementation:** Never modify existing code
3. **Use FastMCP:** Not invented APIs
4. **ADK-compliant from start:** ToolContext + callbacks + session state (no bearer_token parameters)
5. **Test incrementally:** Validate each part before moving on
6. **Production-ready:** No refactoring needed - OAuth 2.0 ready from day one

### References

- `AUTHENTICATION_ADK_ANALYSIS.md` - **CRITICAL: ADK compliance analysis** ⚠️
- `docs/MCP_CORRECT_IMPLEMENTATION.md` - Technical details
- `docs/PARALLEL_IMPLEMENTATION.md` - Parallel strategy
- `docs/PHASE_2_PLAN.md` - Overall plan
- `CLAUDE.md` - Project overview
- [ADK Authentication Docs](https://google.github.io/adk-docs/tools-custom/authentication/)
- [ADK Context Docs](https://google.github.io/adk-docs/context/)
- [ADK Callbacks Docs](https://google.github.io/adk-docs/callbacks/)

---

**Status:** Ready for Implementation
**Last Updated:** 2025-12-22
**Implementation Order:** CRITICAL - Follow documented order
**Risk Level:** Zero (parallel implementation, existing code untouched)
**✅ PRODUCTION-READY:** All tasks use ADK-compliant authentication from the start (ToolContext + callbacks + session state)
