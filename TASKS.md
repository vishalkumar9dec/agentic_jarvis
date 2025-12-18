# Agentic Jarvis - Implementation Tasks

**Phase 1: Core Functionality**

This document tracks all implementation tasks for building the Agentic Jarvis multi-agent system. Each task includes detailed requirements and acceptance criteria.

---

## Project Setup

### Task 1: Create Project Directory Structure
**Status:** Pending

**Description:**
Set up the complete directory structure for the multi-agent system following ADK best practices.

**Required Structure:**
```
agentic_jarvis/
├── .env                           # Environment variables (git-ignored)
├── .env.template                  # Template for environment setup
├── .gitignore                     # Git ignore file
├── requirements.txt               # Python dependencies
├── main.py                        # CLI interface for testing
├── CLAUDE.md                      # ✅ Already created
├── JARVIS_PRODUCT_SPEC.md        # ✅ Already created
├── TASKS.md                       # This file
├── jarvis_agent/                  # Root orchestrator
│   ├── __init__.py
│   ├── agent.py                   # Root agent definition
│   └── sub_agents/
│       ├── __init__.py
│       ├── tickets/
│       │   ├── __init__.py
│       │   └── agent.py           # Tickets agent
│       └── finops/
│           ├── __init__.py
│           └── agent.py           # FinOps agent
├── toolbox_servers/               # Local toolbox servers
│   ├── __init__.py
│   ├── tickets_server/
│   │   ├── __init__.py
│   │   └── server.py              # Tickets toolbox (port 5001)
│   └── finops_server/
│       ├── __init__.py
│       └── server.py              # FinOps toolbox (port 5002)
├── remote_agent/                  # Remote A2A agent
│   └── oxygen_agent/
│       ├── __init__.py
│       ├── .env                   # Oxygen-specific config
│       ├── agent.py               # Oxygen A2A agent
│       └── tools.py               # Learning journey tools
└── scripts/
    ├── start_tickets_server.sh    # Start tickets toolbox
    ├── start_finops_server.sh     # Start finops toolbox
    ├── start_oxygen_agent.sh      # Start oxygen A2A server
    ├── check_services.sh          # Health check script
    └── restart_all.sh             # Clean restart all services
```

**Acceptance Criteria:**
- [ ] All directories created
- [ ] All `__init__.py` files in place
- [ ] Structure matches the specification above

---

### Task 2: Set Up requirements.txt
**Status:** Pending

**Description:**
Create requirements.txt with all necessary dependencies for Phase 1.

**Required Dependencies:**
```txt
# Google ADK and dependencies
google-adk[a2a]>=1.0.0
google-genai>=0.1.0

# A2A communication
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0

# Toolbox integration
toolbox-core>=0.1.0

# Environment management
python-dotenv>=1.0.0

# HTTP clients
requests>=2.31.0
httpx>=0.25.0

# Utilities
python-dateutil>=2.8.2
```

**Acceptance Criteria:**
- [ ] requirements.txt created with all dependencies
- [ ] File can be installed via `pip install -r requirements.txt`
- [ ] All versions specified are compatible

**Commands:**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

---

### Task 3: Create Environment Configuration Files
**Status:** Pending

**Description:**
Create `.env.template` and `.env` files with all required configuration variables.

**Files to Create:**

**`.env.template`** (committed to git):
```bash
# Google API Key (get from https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=your_api_key_here

# Service Ports
TICKETS_SERVER_PORT=5001
FINOPS_SERVER_PORT=5002
OXYGEN_AGENT_PORT=8002
WEB_UI_PORT=9999

# Phase 2: JWT Authentication (Future)
# JWT_SECRET_KEY=your_secret_key_here

# Phase 3: Session/Memory (Future)
# SESSION_TYPE=memory
# DATABASE_URL=sqlite:///./jarvis.db

# Phase 4: OAuth 2.0 (Future)
# OAUTH_PROVIDER=google
# OAUTH_CLIENT_ID=your_client_id
# OAUTH_CLIENT_SECRET=your_client_secret
```

**`.env`** (git-ignored, user creates from template):
User must copy `.env.template` to `.env` and fill in their actual `GOOGLE_API_KEY`.

**`.gitignore`**:
```
# Environment
.env
*.env
!.env.template

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Database (Phase 3)
*.db
*.sqlite
```

**Acceptance Criteria:**
- [ ] `.env.template` created with all variables documented
- [ ] `.gitignore` created with proper exclusions
- [ ] Instructions added for users to create their `.env`
- [ ] `.env` is git-ignored

---

## Tickets Agent Implementation

### Task 4: Implement Tickets Toolbox Server
**Status:** Pending

**Description:**
Create the Tickets toolbox server on port 5001 with CRUD operations for IT ticket management.

**File:** `toolbox_servers/tickets_server/server.py`

**Required Functions:**
1. `get_all_tickets()` - Retrieve all tickets
2. `get_ticket(ticket_id: int)` - Get specific ticket by ID
3. `get_user_tickets(username: str)` - Get all tickets for a user
4. `create_ticket(operation: str, user: str)` - Create new ticket

**Sample Data:**
```python
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
```

**Implementation Pattern:**
- Use FastAPI with toolbox pattern (see CLAUDE.md reference to supply_chain_agent)
- Create TOOLSETS dictionary with `tickets_toolset`
- Implement `function_to_tool_schema` helper
- Create standard endpoints: `/toolsets`, `/toolsets/{name}`, `/execute`
- Run on port 5001 with uvicorn

**Acceptance Criteria:**
- [ ] Server starts on port 5001 without errors
- [ ] All four functions implemented with proper docstrings
- [ ] FastAPI endpoints respond correctly
- [ ] Can curl `http://localhost:5001/toolsets` and get tickets_toolset
- [ ] Sample data accessible via functions

**Test Command:**
```bash
# Start server
cd toolbox_servers/tickets_server
../../.venv/bin/python server.py

# Test in another terminal
curl http://localhost:5001/toolsets
curl http://localhost:5001/toolsets/tickets_toolset
```

---

### Task 5: Create Tickets Agent
**Status:** Pending

**Description:**
Create the Tickets agent that connects to the toolbox server and provides IT operations ticket management.

**File:** `jarvis_agent/sub_agents/tickets/agent.py`

**Implementation:**
```python
from google.adk.agents import LlmAgent
from toolbox_core import ToolboxSyncClient

GEMINI_2_5_FLASH = "gemini-2.5-flash"

toolbox = ToolboxSyncClient("http://localhost:5001")
tools = toolbox.load_toolset('tickets_toolset')

tickets_agent = LlmAgent(
    name="TicketsAgent",
    model=GEMINI_2_5_FLASH,
    description="Agent to manage IT operations tickets",
    instruction="""You are a tickets management agent. Your role is to help users:
- View all tickets or specific tickets by ID
- Find tickets for a particular user
- Create new tickets for operations

Always provide clear, concise ticket information.""",
    tools=tools,
)
```

**Acceptance Criteria:**
- [ ] Agent file created with proper imports
- [ ] Toolbox client connects to port 5001
- [ ] Agent instructions are clear and specific
- [ ] Agent can be imported without errors
- [ ] Tools load successfully from toolbox

**Test:**
```python
# Test import
from jarvis_agent.sub_agents.tickets.agent import tickets_agent
print(f"Agent loaded: {tickets_agent.name}")
```

---

## FinOps Agent Implementation

### Task 6: Implement FinOps Toolbox Server
**Status:** Pending

**Description:**
Create the FinOps toolbox server on port 5002 with cloud cost analytics operations.

**File:** `toolbox_servers/finops_server/server.py`

**Required Functions:**
1. `get_all_clouds_cost()` - Get cost summary for all cloud providers
2. `get_cloud_cost(provider: str)` - Get cost details for specific provider
3. `get_service_cost(provider: str, service_name: str)` - Get cost for specific service
4. `get_cost_breakdown()` - Get detailed cost breakdown with percentages

**Sample Data:**
```python
FINOPS_DB = {
    "aws": {
        "cost": 100,
        "services": [
            {"name": "ec2", "cost": 50},
            {"name": "s3", "cost": 30},
            {"name": "dynamodb", "cost": 20}
        ]
    },
    "gcp": {
        "cost": 250,
        "services": [
            {"name": "compute", "cost": 100},
            {"name": "vault", "cost": 50},
            {"name": "firestore", "cost": 100}
        ]
    },
    "azure": {
        "cost": 300,
        "services": [
            {"name": "storage", "cost": 100},
            {"name": "AI Studio", "cost": 200}
        ]
    }
}
```

**Acceptance Criteria:**
- [ ] Server starts on port 5002 without errors
- [ ] All four functions implemented with proper docstrings
- [ ] FastAPI endpoints respond correctly
- [ ] Cost breakdown calculates percentages correctly
- [ ] Sample data accessible via functions

**Test Command:**
```bash
# Start server
cd toolbox_servers/finops_server
../../.venv/bin/python server.py

# Test in another terminal
curl http://localhost:5002/toolsets
curl http://localhost:5002/toolsets/finops_toolset
```

---

### Task 7: Create FinOps Agent
**Status:** Pending

**Description:**
Create the FinOps agent that connects to the toolbox server and provides cloud cost analytics.

**File:** `jarvis_agent/sub_agents/finops/agent.py`

**Implementation:**
```python
from google.adk.agents import LlmAgent
from toolbox_core import ToolboxSyncClient

GEMINI_2_5_FLASH = "gemini-2.5-flash"

toolbox = ToolboxSyncClient("http://localhost:5002")
tools = toolbox.load_toolset('finops_toolset')

finops_agent = LlmAgent(
    name="FinOpsAgent",
    model=GEMINI_2_5_FLASH,
    description="Agent to provide cloud financial operations data and analytics",
    instruction="""You are a FinOps (Financial Operations) agent. Your role is to:
- Provide cloud cost information across AWS, GCP, and Azure
- Break down costs by services within each cloud provider
- Compare costs across different cloud providers
- Help users understand their cloud spending

Always present cost data clearly with proper formatting (currency symbols, totals, etc.).""",
    tools=tools,
)
```

**Acceptance Criteria:**
- [ ] Agent file created with proper imports
- [ ] Toolbox client connects to port 5002
- [ ] Agent instructions cover cost analytics clearly
- [ ] Agent can be imported without errors
- [ ] Tools load successfully from toolbox

---

## Oxygen Remote Agent Implementation

### Task 8: Implement Oxygen Tools for Learning Journey
**Status:** Pending

**Description:**
Create the tools module for Oxygen agent with learning and development functions.

**File:** `remote_agent/oxygen_agent/tools.py`

**Required Functions:**
1. `get_user_courses(username: str)` - Get all courses for a user
2. `get_pending_exams(username: str)` - Get pending exams with deadlines
3. `get_user_preferences(username: str)` - Get user's learning preferences
4. `get_learning_summary(username: str)` - Get complete learning journey summary

**Sample Data:**
```python
LEARNING_DB = {
    "vishal": {
        "courses_enrolled": ["aws", "terraform"],
        "pending_exams": ["snowflake"],
        "completed_courses": ["docker"],
        "preferences": ["software engineering", "cloud architecture"],
        "exam_deadlines": {"snowflake": "2025-01-15"}
    },
    "happy": {
        "courses_enrolled": ["architecture", "soft skills"],
        "pending_exams": ["aws"],
        "completed_courses": ["python basics"],
        "preferences": ["system design", "leadership"],
        "exam_deadlines": {"aws": "2025-01-20"}
    }
}
```

**Acceptance Criteria:**
- [ ] All four functions implemented with proper docstrings and type hints
- [ ] Functions return properly formatted dictionaries with success/error handling
- [ ] Sample data includes at least 2 users with diverse learning data
- [ ] Functions handle missing users gracefully
- [ ] Learning summary calculates completion rate correctly

---

### Task 9: Create Oxygen A2A Agent
**Status:** Pending

**Description:**
Create the Oxygen remote agent as an A2A-enabled agent running on port 8002.

**File:** `remote_agent/oxygen_agent/agent.py`

**Implementation:**
```python
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from .tools import (
    get_user_courses,
    get_pending_exams,
    get_user_preferences,
    get_learning_summary
)
import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

GEMINI_2_5_FLASH = "gemini-2.5-flash"

root_agent = LlmAgent(
    name="OxygenAgent",
    model=GEMINI_2_5_FLASH,
    instruction="""You are Oxygen, a learning and development assistant. Your role is to:
- Help users track their enrolled courses and completed courses
- Remind users about pending exams and deadlines
- Provide personalized learning recommendations based on preferences
- Track overall learning progress

Always be encouraging and helpful in supporting users' learning journeys.""",
    description="Learning and development platform agent that manages user courses, exams, and preferences",
    tools=[
        get_user_courses,
        get_pending_exams,
        get_user_preferences,
        get_learning_summary
    ],
)

# Convert to A2A app (CRITICAL: include port parameter)
a2a_app = to_a2a(root_agent, port=8002)
```

**CRITICAL:** Must include `port=8002` parameter in `to_a2a()` call!

**Oxygen .env file:** `remote_agent/oxygen_agent/.env`
```bash
GOOGLE_API_KEY=your_api_key_here
```

**Acceptance Criteria:**
- [ ] Agent created with all four tools
- [ ] A2A app configured with explicit port=8002
- [ ] Oxygen .env file created
- [ ] Agent card accessible at `http://localhost:8002/.well-known/agent-card.json`
- [ ] Can start with uvicorn: `python -m uvicorn remote_agent.oxygen_agent.agent:a2a_app --host localhost --port 8002`

---

## Root Orchestrator Implementation

### Task 10: Implement Jarvis Root Orchestrator
**Status:** Pending

**Description:**
Create the root Jarvis agent that orchestrates all sub-agents (Tickets, FinOps, and Oxygen).

**File:** `jarvis_agent/agent.py`

**Implementation:**
```python
from google.adk.agents import LlmAgent
from jarvis_agent.sub_agents.tickets.agent import tickets_agent
from jarvis_agent.sub_agents.finops.agent import finops_agent

# Import Oxygen as remote A2A agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH

oxygen_agent = RemoteA2aAgent(
    name="oxygen_agent",
    description="Learning and development platform for course and exam management",
    agent_card=f"http://localhost:8002{AGENT_CARD_WELL_KNOWN_PATH}"
)

GEMINI_2_5_FLASH = "gemini-2.5-flash"

root_agent = LlmAgent(
    name="JarvisOrchestrator",
    model=GEMINI_2_5_FLASH,
    description="Jarvis - Your intelligent IT operations and learning assistant",
    instruction="""You are Jarvis, an intelligent assistant that helps users with:

**IT Operations:**
- **Tickets**: Use TicketsAgent to view, search, and create IT operation tickets
- **FinOps**: Use FinOpsAgent to get cloud cost information and financial analytics

**Learning & Development:**
- **Courses & Exams**: Use OxygenAgent to check enrolled courses, pending exams, and learning progress

Route user requests to the appropriate sub-agent based on the query:
- Ticket-related queries → TicketsAgent
- Cloud cost/FinOps queries → FinOpsAgent
- Learning/course/exam queries → OxygenAgent

Always provide helpful, clear responses and coordinate between agents when needed.""",
    sub_agents=[tickets_agent, finops_agent, oxygen_agent],
)
```

**Acceptance Criteria:**
- [ ] Root agent imports all three sub-agents
- [ ] Oxygen configured as RemoteA2aAgent with correct agent card URL
- [ ] Instructions clearly define routing logic
- [ ] Agent can be imported and initialized
- [ ] Sub-agents list includes all three agents

---

## DevOps & Scripts

### Task 11: Create Startup Scripts
**Status:** Pending

**Description:**
Create shell scripts to start all services with proper port cleanup.

**Files to Create:**

**`scripts/start_tickets_server.sh`**:
```bash
#!/bin/bash
echo "Starting Tickets Toolbox Server on port 5001..."
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "Cleaning up existing processes on port 5001..."
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    sleep 1
fi

cd toolbox_servers/tickets_server
../../.venv/bin/python server.py
```

**`scripts/start_finops_server.sh`**:
```bash
#!/bin/bash
echo "Starting FinOps Toolbox Server on port 5002..."
if lsof -ti:5002 > /dev/null 2>&1; then
    echo "Cleaning up existing processes on port 5002..."
    lsof -ti:5002 | xargs kill -9 2>/dev/null
    sleep 1
fi

cd toolbox_servers/finops_server
../../.venv/bin/python server.py
```

**`scripts/start_oxygen_agent.sh`**:
```bash
#!/bin/bash
echo "Starting Oxygen A2A Agent on port 8002..."
if lsof -ti:8002 > /dev/null 2>&1; then
    echo "Cleaning up existing processes on port 8002..."
    lsof -ti:8002 | xargs kill -9 2>/dev/null
    sleep 1
fi

.venv/bin/python -m uvicorn remote_agent.oxygen_agent.agent:a2a_app --host localhost --port 8002
```

**`scripts/restart_all.sh`**:
```bash
#!/bin/bash
echo "Restarting all Jarvis services..."

# Kill all services
lsof -ti:5001 | xargs kill -9 2>/dev/null
lsof -ti:5002 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null

sleep 2

echo "Starting all services in background..."
./scripts/start_tickets_server.sh &
sleep 1
./scripts/start_finops_server.sh &
sleep 1
./scripts/start_oxygen_agent.sh &

echo "All services started. Use './scripts/check_services.sh' to verify."
```

**Acceptance Criteria:**
- [ ] All scripts created and executable (`chmod +x scripts/*.sh`)
- [ ] Scripts properly clean up existing processes
- [ ] Scripts start services on correct ports
- [ ] Scripts provide clear status messages

---

### Task 12: Create Health Check Script
**Status:** Pending

**Description:**
Create a script to verify all services are running and healthy.

**File:** `scripts/check_services.sh`

```bash
#!/bin/bash
echo "=========================================="
echo "Jarvis Services Health Check"
echo "=========================================="

check_service() {
    local name=$1
    local port=$2
    local endpoint=$3

    if lsof -ti:$port > /dev/null 2>&1; then
        echo "✅ $name - Running on port $port"
        if [ -n "$endpoint" ]; then
            http_status=$(curl -s -o /dev/null -w "%{http_code}" $endpoint 2>/dev/null)
            if [ "$http_status" = "200" ]; then
                echo "   └─ HTTP endpoint responsive"
            else
                echo "   └─ ⚠️  HTTP endpoint not responding (status: $http_status)"
            fi
        fi
    else
        echo "❌ $name - NOT running on port $port"
    fi
}

echo ""
check_service "Tickets Server" 5001 "http://localhost:5001/toolsets"
echo ""
check_service "FinOps Server" 5002 "http://localhost:5002/toolsets"
echo ""
check_service "Oxygen A2A Agent" 8002 "http://localhost:8002/.well-known/agent-card.json"
echo ""
echo "=========================================="
```

**Acceptance Criteria:**
- [ ] Script checks all three services (5001, 5002, 8002)
- [ ] Script verifies HTTP endpoints are responsive
- [ ] Script provides clear status messages with emojis
- [ ] Script is executable

---

### Task 13: Create CLI Interface
**Status:** Pending

**Description:**
Create a main.py CLI interface for testing the Jarvis agent interactively.

**File:** `main.py`

```python
#!/usr/bin/env python3
"""
Agentic Jarvis - CLI Interface
Interactive chat with the Jarvis root orchestrator agent.
"""

import os
from dotenv import load_dotenv
from jarvis_agent.agent import root_agent

# Load environment variables
load_dotenv()

def main():
    print("=" * 60)
    print("🤖 Agentic Jarvis - Your Intelligent Assistant")
    print("=" * 60)
    print("\nCapabilities:")
    print("  • IT Tickets Management (via TicketsAgent)")
    print("  • Cloud Cost Analytics (via FinOpsAgent)")
    print("  • Learning & Development (via OxygenAgent)")
    print("\nType 'exit' or 'quit' to end the session.\n")
    print("=" * 60)

    session_id = "cli-session-001"

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye! Thanks for using Jarvis.\n")
                break

            # Send message to root agent
            print("\n🤖 Jarvis: ", end="", flush=True)
            response = root_agent.send_message(user_input, session_id=session_id)
            print(response)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using Jarvis.\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please make sure all services are running:")
            print("  - Tickets Server (port 5001)")
            print("  - FinOps Server (port 5002)")
            print("  - Oxygen Agent (port 8002)")

if __name__ == "__main__":
    main()
```

**Acceptance Criteria:**
- [ ] CLI starts without errors
- [ ] User can interact with Jarvis agent
- [ ] Responses from all three sub-agents work correctly
- [ ] Exit commands work properly
- [ ] Error handling provides helpful messages

---

## Testing & Validation

### Task 14: Test Tickets Agent Operations
**Status:** Pending

**Description:**
Test all Tickets agent CRUD operations through the CLI interface.

**Test Scenarios:**

1. **Get all tickets:**
   ```
   User: "Show me all tickets"
   Expected: List of all 3 tickets from sample data
   ```

2. **Get specific ticket:**
   ```
   User: "What is the status of ticket 12301?"
   Expected: Ticket details showing "pending" status
   ```

3. **Get user tickets:**
   ```
   User: "Show me all tickets for vishal"
   Expected: Tickets 12301 and 12303
   ```

4. **Create new ticket:**
   ```
   User: "Create a new ticket for creating a new S3 bucket for user john"
   Expected: Confirmation with new ticket ID (12304)
   ```

**Acceptance Criteria:**
- [ ] All four test scenarios pass
- [ ] Responses are clear and accurate
- [ ] Ticket data is correctly formatted
- [ ] New tickets are assigned sequential IDs

---

### Task 15: Test FinOps Agent Analytics
**Status:** Pending

**Description:**
Test all FinOps agent cost analytics operations.

**Test Scenarios:**

1. **Total cloud spend:**
   ```
   User: "What is our total cloud spend?"
   Expected: $650 total (AWS $100 + GCP $250 + Azure $300)
   ```

2. **Provider breakdown:**
   ```
   User: "Show me the cost breakdown for GCP"
   Expected: Total $250 with services: compute ($100), vault ($50), firestore ($100)
   ```

3. **Service cost:**
   ```
   User: "How much are we spending on Azure AI Studio?"
   Expected: $200
   ```

4. **Cost comparison:**
   ```
   User: "Which cloud provider is most expensive?"
   Expected: Azure at $300
   ```

**Acceptance Criteria:**
- [ ] All four test scenarios pass
- [ ] Cost calculations are accurate
- [ ] Responses include proper currency formatting
- [ ] Percentages calculated correctly in breakdown

---

### Task 16: Test Oxygen A2A Agent Learning Queries
**Status:** Pending

**Description:**
Test Oxygen remote agent learning journey operations via A2A protocol.

**Test Scenarios:**

1. **User courses:**
   ```
   User: "What courses is vishal enrolled in?"
   Expected: AWS and Terraform
   ```

2. **Pending exams:**
   ```
   User: "Does happy have any pending exams?"
   Expected: AWS exam with deadline 2025-01-20
   ```

3. **Learning preferences:**
   ```
   User: "What are vishal's learning preferences?"
   Expected: software engineering, cloud architecture
   ```

4. **Learning summary:**
   ```
   User: "Show me vishal's learning progress"
   Expected: Complete summary with completion rate, enrolled/completed courses, pending exams
   ```

**Acceptance Criteria:**
- [ ] All four test scenarios pass
- [ ] A2A communication works correctly
- [ ] Agent card is accessible at `/.well-known/agent-card.json`
- [ ] Remote agent responses are properly formatted
- [ ] Completion rate calculation is accurate

---

### Task 17: Test Root Orchestrator Cross-Agent Routing
**Status:** Pending

**Description:**
Test Jarvis root orchestrator's ability to route queries to appropriate agents and coordinate responses.

**Test Scenarios:**

1. **Single agent query - Tickets:**
   ```
   User: "Show me vishal's tickets"
   Expected: Routes to TicketsAgent, returns tickets for vishal
   ```

2. **Single agent query - FinOps:**
   ```
   User: "What are our AWS costs?"
   Expected: Routes to FinOpsAgent, returns AWS cost breakdown
   ```

3. **Single agent query - Oxygen:**
   ```
   User: "Does vishal have any upcoming exams?"
   Expected: Routes to OxygenAgent, returns Snowflake exam deadline
   ```

4. **Cross-agent query:**
   ```
   User: "Show me vishal's tickets and upcoming exams"
   Expected: Coordinates between TicketsAgent and OxygenAgent, returns both
   ```

5. **Multi-domain query:**
   ```
   User: "What are the AWS costs and does vishal have AWS-related courses?"
   Expected: Uses FinOpsAgent for costs and OxygenAgent for courses
   ```

**Acceptance Criteria:**
- [ ] All five test scenarios pass
- [ ] Root agent routes queries to correct sub-agents
- [ ] Cross-agent coordination works smoothly
- [ ] Responses combine data from multiple agents coherently
- [ ] No errors in agent communication

---

## Progress Tracking

**Overall Progress:** 0/17 tasks completed (0%)

### Setup Phase: 0/3 ✅
- [ ] Task 1: Project structure
- [ ] Task 2: Requirements
- [ ] Task 3: Environment config

### Tickets Agent: 0/2 ✅
- [ ] Task 4: Toolbox server
- [ ] Task 5: Agent implementation

### FinOps Agent: 0/2 ✅
- [ ] Task 6: Toolbox server
- [ ] Task 7: Agent implementation

### Oxygen Agent: 0/2 ✅
- [ ] Task 8: Tools implementation
- [ ] Task 9: A2A agent

### Orchestrator: 0/1 ✅
- [ ] Task 10: Root agent

### DevOps: 0/3 ✅
- [ ] Task 11: Startup scripts
- [ ] Task 12: Health check
- [ ] Task 13: CLI interface

### Testing: 0/4 ✅
- [ ] Task 14: Tickets tests
- [ ] Task 15: FinOps tests
- [ ] Task 16: Oxygen tests
- [ ] Task 17: Orchestrator tests

---

## Quick Start Guide

Once all tasks are complete, use these commands to start the system:

```bash
# Terminal 1: Start Tickets Server
./scripts/start_tickets_server.sh

# Terminal 2: Start FinOps Server
./scripts/start_finops_server.sh

# Terminal 3: Start Oxygen A2A Agent
./scripts/start_oxygen_agent.sh

# Terminal 4: Verify all services
./scripts/check_services.sh

# Terminal 4: Start CLI interface
python main.py
```

---

## Notes

- **Reference Implementation:** `/Users/vishalkumar/projects/supply_chain_agent_demo`
- **ADK Documentation:** https://google.github.io/adk-docs/
- **Key Pattern:** Always include `port` parameter in `to_a2a()` calls
- **Port Cleanup:** Always kill existing processes before starting services

---

**Last Updated:** 2025-01-18
