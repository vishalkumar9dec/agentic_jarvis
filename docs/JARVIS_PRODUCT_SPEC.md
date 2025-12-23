# Agentic Jarvis - Product Documentation

## Executive Summary

**Agentic Jarvis** is an enterprise AI assistant that unifies IT operations (Jarvis) with learning & development (Oxygen) using Google's Agent Development Kit (ADK). The system provides intelligent automation for ticket management, financial operations monitoring, and personalized learning journeys through a conversational interface.

**Key Features:**
- **Multi-Agent Architecture**: Root orchestrator with specialized sub-agents (Tickets, FinOps) and remote A2A agent (Oxygen)
- **Enterprise Authentication**: JWT bearer tokens (Phase 2) and OAuth 2.0 with SSO support (Phase 4)
- **Intelligent Memory**: Multi-layer memory system with session, short-term, and long-term context management (Phase 3)
- **Secure & Scalable**: Built on proven ADK patterns with enterprise-grade security and integration capabilities

**Technology Stack:**
- Google ADK v1.0.0+ (Agent Development Kit with OAuth 2.0 support)
- A2A Protocol v0.2 (Agent-to-Agent Communication)
- MCP (Model Context Protocol) for tool integration
- FastAPI for service endpoints
- Gemini 2.5 Flash model
- OAuth 2.0 with Auth0/Google/Azure AD support

---

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Agentic Jarvis                          │
│                    (Root Orchestrator)                      │
└──────────────┬──────────────────────────┬──────────────────┘
               │                          │
        ┌──────▼──────┐            ┌──────▼──────┐
        │ Local Agents│            │Remote Agent │
        └─────────────┘            └─────────────┘
               │                          │
    ┌──────────┴──────────┐              │
    │                     │              │
┌───▼────┐         ┌──────▼─────┐  ┌────▼─────┐
│Tickets │         │   FinOps   │  │  Oxygen  │
│ Agent  │         │   Agent    │  │  (A2A)   │
└────────┘         └────────────┘  └──────────┘
    │                     │              │
    │                     │              │
┌───▼────┐         ┌──────▼─────┐  ┌────▼─────┐
│Toolbox │         │  Toolbox   │  │A2A Server│
│Server  │         │  Server    │  │  :8002   │
│ :5001  │         │   :5002    │  └──────────┘
└────────┘         └────────────┘
```

### Agent Responsibilities

| Agent | Type | Port | Purpose |
|-------|------|------|---------|
| **Jarvis** | Root Orchestrator | - | Routes requests to appropriate sub-agents |
| **Tickets** | Local Sub-Agent | 5001 | Manages IT tickets and operations |
| **FinOps** | Local Sub-Agent | 5002 | Provides cloud cost analytics |
| **Oxygen** | Remote A2A Agent | 8002 | Handles learning journeys (remote service) |

---

## Data Models

### 1. Tickets Schema

```python
Ticket = {
    "id": int,              # Unique ticket identifier
    "operation": str,       # Type of operation (e.g., create_ai_key)
    "user": str,           # Username who created ticket
    "status": str,         # pending | in_progress | completed | rejected
    "created_at": datetime,
    "updated_at": datetime
}

# Sample Data
TICKETS_DB = [
    {"id": 12301, "operation": "create_ai_key", "user": "vishal", "status": "pending"},
    {"id": 12302, "operation": "create_gitlab_account", "user": "happy", "status": "completed"},
    {"id": 12303, "operation": "update_budget", "user": "vishal", "status": "in_progress"},
]
```

### 2. FinOps Schema

```python
CloudCost = {
    "provider": str,        # aws | gcp | azure
    "total_cost": float,   # Total monthly cost
    "services": [
        {
            "name": str,   # Service name
            "cost": float  # Service cost
        }
    ],
    "period": str          # Billing period (YYYY-MM)
}

# Sample Data
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

### 3. Oxygen (Learning) Schema

```python
UserLearning = {
    "username": str,
    "courses_enrolled": [str],      # List of enrolled course names
    "pending_exams": [str],         # List of pending exam names
    "completed_courses": [str],     # List of completed courses
    "preferences": [str],           # Learning interests/topics
    "exam_deadlines": {
        "exam_name": datetime
    }
}

# Sample Data
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

---

## Implementation Plan

### Feasibility Analysis

All planned phases have been validated against Google ADK's official documentation and capabilities:

**✅ Phase 1 (Core Functionality)**: Fully supported
- Multi-agent orchestration with sub-agents
- A2A protocol for remote agent communication
- Toolbox integration via HTTP servers
- All patterns proven in the supply chain agent demo

**✅ Phase 2 (Authentication)**: Fully supported via ADK's built-in auth mechanisms
- JWT bearer token authentication via `HTTPBearer` scheme
- Token passing between agents in A2A calls
- User-specific data access control
- [Reference: ADK Authentication Documentation](https://google.github.io/adk-docs/tools-custom/authentication/)

**✅ Phase 3 (Memory & Context)**: Fully supported with multiple storage options
- `InMemorySessionService` for development/testing
- `DatabaseSessionService` for production persistence
- `VertexAIMemoryBankService` for long-term memory with vector search
- Session state management across conversation turns
- [Reference: ADK Session Management](https://google.github.io/adk-docs/sessions/)
- [Reference: Agent State and Memory Tutorial](https://cloud.google.com/blog/topics/developers-practitioners/remember-this-agent-state-and-memory-with-adk)

**✅ Phase 4 (OAuth 2.0)**: Fully supported as of ADK v1.0.0
- OAuth 2.0 integrated into A2A Protocol v0.2 (May 2025 release)
- Auth0 partnership for enterprise authentication
- Integration Connectors for 100+ enterprise systems
- Secure token exchange between agents
- [Reference: OAuth2-Powered ADK Agents](https://medium.com/google-cloud/secure-and-smart-oauth2-powered-google-adk-agents-with-integration-connectors-for-enterprises-8916028b97ca)

---

### Phase 1: Core Functionality (Foundation)

**Goal**: Implement all agents with full CRUD capabilities and A2A communication

#### 1.1 Project Structure

```
jarvis_agentic/
├── .env                           # Environment variables
├── .env.template                  # Template for .env
├── requirements.txt               # Python dependencies
├── web.py                         # Web UI server
├── main.py                        # CLI interface
├── jarvis_agent/                  # Root orchestrator
│   ├── __init__.py
│   ├── agent.py                   # Root agent definition
│   └── sub_agents/
│       ├── tickets/
│       │   ├── __init__.py
│       │   └── agent.py           # Tickets agent
│       └── finops/
│           ├── __init__.py
│           └── agent.py           # FinOps agent
├── toolbox_servers/               # Local toolbox servers
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
    ├── start_web.sh               # Start web UI
    ├── check_services.sh          # Health check script
    └── restart_all.sh             # Clean restart script
```

#### 1.2 Tickets Agent Implementation

**Toolbox Server** (`toolbox_servers/tickets_server/server.py`):

```python
from fastapi import FastAPI
from typing import Dict, List, Optional, Any
import inspect
from datetime import datetime

# In-memory database
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

def get_all_tickets() -> List[Dict]:
    """Retrieve all tickets.

    Returns:
        List of all tickets
    """
    return TICKETS_DB

def get_ticket(ticket_id: int) -> Optional[Dict]:
    """Get a specific ticket by ID.

    Args:
        ticket_id: The ticket ID

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
        operation: The operation type
        user: Username creating the ticket

    Returns:
        Created ticket details
    """
    new_id = max([t['id'] for t in TICKETS_DB]) + 1 if TICKETS_DB else 1

    new_ticket = {
        "id": new_id,
        "operation": operation,
        "user": user,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    TICKETS_DB.append(new_ticket)
    return {
        "success": True,
        "ticket": new_ticket,
        "message": f"Ticket {new_id} created successfully"
    }

# Create FastAPI app with toolbox pattern
app = FastAPI(title="Tickets Toolbox Server")

TOOLSETS = {
    "tickets_toolset": {
        "get_all_tickets": get_all_tickets,
        "get_ticket": get_ticket,
        "get_user_tickets": get_user_tickets,
        "create_ticket": create_ticket
    }
}

# [Include function_to_tool_schema and endpoint functions from supply_chain_agent]
# ... (same pattern as your working toolbox_server/server.py)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5001)
```

**Agent Definition** (`jarvis_agent/sub_agents/tickets/agent.py`):

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

#### 1.3 FinOps Agent Implementation

**Toolbox Server** (`toolbox_servers/finops_server/server.py`):

```python
from fastapi import FastAPI
from typing import Dict, List, Optional, Any

# In-memory database
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

def get_all_clouds_cost() -> Dict:
    """Get cost summary for all cloud providers.

    Returns:
        Dictionary with all cloud costs
    """
    return {
        "total_cost": sum(cloud["cost"] for cloud in FINOPS_DB.values()),
        "clouds": FINOPS_DB
    }

def get_cloud_cost(provider: str) -> Dict:
    """Get cost details for a specific cloud provider.

    Args:
        provider: Cloud provider name (aws, gcp, azure)

    Returns:
        Cost details for the specified provider
    """
    provider = provider.lower()
    if provider not in FINOPS_DB:
        return {
            "success": False,
            "error": f"Provider '{provider}' not found. Available: aws, gcp, azure"
        }

    return {
        "success": True,
        "provider": provider,
        "data": FINOPS_DB[provider]
    }

def get_service_cost(provider: str, service_name: str) -> Dict:
    """Get cost for a specific service in a cloud provider.

    Args:
        provider: Cloud provider name
        service_name: Name of the service

    Returns:
        Service cost details
    """
    provider = provider.lower()
    if provider not in FINOPS_DB:
        return {"success": False, "error": f"Provider '{provider}' not found"}

    for service in FINOPS_DB[provider]["services"]:
        if service["name"].lower() == service_name.lower():
            return {
                "success": True,
                "provider": provider,
                "service": service["name"],
                "cost": service["cost"]
            }

    return {
        "success": False,
        "error": f"Service '{service_name}' not found in {provider}"
    }

def get_cost_breakdown() -> Dict:
    """Get detailed cost breakdown across all clouds and services.

    Returns:
        Detailed cost analysis
    """
    total = 0
    breakdown = []

    for provider, data in FINOPS_DB.items():
        total += data["cost"]
        breakdown.append({
            "provider": provider,
            "cost": data["cost"],
            "percentage": 0  # Will be calculated
        })

    # Calculate percentages
    for item in breakdown:
        item["percentage"] = round((item["cost"] / total) * 100, 2) if total > 0 else 0

    return {
        "total_cost": total,
        "breakdown": breakdown,
        "details": FINOPS_DB
    }

# Create FastAPI app
app = FastAPI(title="FinOps Toolbox Server")

TOOLSETS = {
    "finops_toolset": {
        "get_all_clouds_cost": get_all_clouds_cost,
        "get_cloud_cost": get_cloud_cost,
        "get_service_cost": get_service_cost,
        "get_cost_breakdown": get_cost_breakdown
    }
}

# [Include function_to_tool_schema and endpoint functions]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5002)
```

**Agent Definition** (`jarvis_agent/sub_agents/finops/agent.py`):

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

#### 1.4 Oxygen Remote Agent Implementation

**Tools** (`remote_agent/oxygen_agent/tools.py`):

```python
from typing import Dict, List

# In-memory database
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

def get_user_courses(username: str) -> Dict:
    """Get all courses for a user.

    Args:
        username: The username

    Returns:
        User's course information
    """
    username = username.lower()
    if username not in LEARNING_DB:
        return {
            "success": False,
            "error": f"User '{username}' not found"
        }

    user_data = LEARNING_DB[username]
    return {
        "success": True,
        "username": username,
        "enrolled_courses": user_data["courses_enrolled"],
        "completed_courses": user_data["completed_courses"],
        "total_enrolled": len(user_data["courses_enrolled"]),
        "total_completed": len(user_data["completed_courses"])
    }

def get_pending_exams(username: str) -> Dict:
    """Get pending exams for a user.

    Args:
        username: The username

    Returns:
        List of pending exams with deadlines
    """
    username = username.lower()
    if username not in LEARNING_DB:
        return {
            "success": False,
            "error": f"User '{username}' not found"
        }

    user_data = LEARNING_DB[username]
    exams_with_deadlines = []

    for exam in user_data["pending_exams"]:
        deadline = user_data["exam_deadlines"].get(exam, "Not set")
        exams_with_deadlines.append({
            "exam": exam,
            "deadline": deadline
        })

    return {
        "success": True,
        "username": username,
        "pending_exams": exams_with_deadlines,
        "count": len(exams_with_deadlines)
    }

def get_user_preferences(username: str) -> Dict:
    """Get user's learning preferences.

    Args:
        username: The username

    Returns:
        User's learning preferences
    """
    username = username.lower()
    if username not in LEARNING_DB:
        return {
            "success": False,
            "error": f"User '{username}' not found"
        }

    return {
        "success": True,
        "username": username,
        "preferences": LEARNING_DB[username]["preferences"]
    }

def get_learning_summary(username: str) -> Dict:
    """Get complete learning journey summary for a user.

    Args:
        username: The username

    Returns:
        Complete learning summary
    """
    username = username.lower()
    if username not in LEARNING_DB:
        return {
            "success": False,
            "error": f"User '{username}' not found"
        }

    user_data = LEARNING_DB[username]

    # Calculate progress percentage
    total_courses = len(user_data["completed_courses"]) + len(user_data["courses_enrolled"])
    completion_rate = (len(user_data["completed_courses"]) / total_courses * 100) if total_courses > 0 else 0

    return {
        "success": True,
        "username": username,
        "summary": {
            "enrolled_courses": user_data["courses_enrolled"],
            "completed_courses": user_data["completed_courses"],
            "pending_exams": user_data["pending_exams"],
            "preferences": user_data["preferences"],
            "completion_rate": round(completion_rate, 2),
            "exams_pending_count": len(user_data["pending_exams"])
        }
    }
```

**Agent** (`remote_agent/oxygen_agent/agent.py`):

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

# Convert to A2A app (IMPORTANT: include port parameter)
a2a_app = to_a2a(root_agent, port=8002)
```

#### 1.5 Root Orchestrator Agent

**Agent Definition** (`jarvis_agent/agent.py`):

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

#### 1.6 Startup Scripts

**Start Tickets Server** (`scripts/start_tickets_server.sh`):
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

**Start FinOps Server** (`scripts/start_finops_server.sh`):
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

**Start Oxygen Agent** (`scripts/start_oxygen_agent.sh`):
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

#### 1.7 Phase 1 Testing Scenarios

**Test 1: Tickets Management**
```
User: "Show me all tickets for vishal"
Expected: List of tickets created by vishal

User: "Create a new ticket for creating a new S3 bucket for user john"
Expected: Confirmation of ticket creation with ticket ID

User: "What is the status of ticket 12301?"
Expected: Ticket details including status
```

**Test 2: FinOps Analytics**
```
User: "What is our total cloud spend?"
Expected: Sum of costs across AWS, GCP, and Azure

User: "Show me the cost breakdown for GCP"
Expected: GCP total cost and service-wise breakdown

User: "Which cloud provider is most expensive?"
Expected: Azure ($300) comparison with other clouds
```

**Test 3: Learning Journey (Remote Agent)**
```
User: "What courses is vishal enrolled in?"
Expected: AWS and Terraform courses

User: "Does happy have any pending exams?"
Expected: AWS exam with deadline

User: "Show me vishal's learning progress"
Expected: Complete summary with completion rate
```

**Test 4: Cross-Agent Queries**
```
User: "Show me vishal's tickets and upcoming exams"
Expected: Coordination between TicketsAgent and OxygenAgent

User: "What are the AWS costs and does vishal have AWS-related courses?"
Expected: FinOpsAgent for costs, OxygenAgent for courses
```

---

### Phase 2: Authentication & Authorization

**Goal**: Implement bearer token authentication for user-specific data access

#### 2.1 Authentication Architecture

```
User Login → Generate JWT Token → Store in Session
                                       ↓
User Request → Extract Token → Validate Token
                                       ↓
                              Pass Token to Remote Agent (Oxygen)
                                       ↓
                              Oxygen validates & returns user-specific data
```

#### 2.2 Implementation Components

**JWT Token Generation** (`jarvis_agent/auth/jwt_handler.py`):

```python
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional

SECRET_KEY = "your-secret-key"  # Store in environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(username: str) -> str:
    """Generate JWT token for user."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": username,
        "exp": expire,
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user(token: str) -> Optional[str]:
    """Extract username from token."""
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None
```

**Modified Oxygen Tools with Auth** (`remote_agent/oxygen_agent/tools.py`):

```python
from typing import Dict, Optional

def get_user_courses(username: str, auth_token: Optional[str] = None) -> Dict:
    """Get courses for authenticated user.

    Args:
        username: The username
        auth_token: Bearer token for authentication

    Returns:
        User's course information or error if unauthorized
    """
    # Validate token
    if not auth_token:
        return {
            "success": False,
            "error": "Authentication required. Please create an Oxygen account."
        }

    # Verify token matches username
    token_user = verify_token_and_get_user(auth_token)
    if not token_user:
        return {
            "success": False,
            "error": "Invalid or expired token. Please log in again."
        }

    if token_user.lower() != username.lower():
        return {
            "success": False,
            "error": "Unauthorized: You can only access your own data."
        }

    # Return user data
    # ... (rest of implementation)
```

**Root Agent with Token Passing**:

```python
# The root agent needs to maintain session state and pass tokens
# This will be implemented using ADK's session management capabilities

root_agent = LlmAgent(
    name="JarvisOrchestrator",
    model=GEMINI_2_5_FLASH,
    instruction="""You are Jarvis with authentication capabilities.

When users request learning data from Oxygen:
1. Check if user is authenticated (session has auth token)
2. If not authenticated, inform them to log in
3. Pass the auth token when calling OxygenAgent
4. Handle unauthorized access errors gracefully

For Tickets and FinOps (local agents), no authentication is required in Phase 2.""",
    sub_agents=[tickets_agent, finops_agent, oxygen_agent],
)
```

#### 2.3 Chat UI Implementation

**Goal**: Create a simple, functional chat interface with login/logout capabilities

**UI Structure** (`ui/`):

```
ui/
├── index.html              # Landing page with login
├── chat.html               # Main chat interface
├── static/
│   ├── css/
│   │   └── style.css      # Styling
│   └── js/
│       ├── auth.js        # Authentication logic
│       └── chat.js        # Chat functionality
```

**Landing Page with Login** (`ui/index.html`):

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis - Login</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="login-container">
        <div class="login-box">
            <h1>🤖 Jarvis AI Assistant</h1>
            <p>Your intelligent IT operations and learning companion</p>

            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required
                           placeholder="Enter your username">
                </div>

                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required
                           placeholder="Enter your password">
                </div>

                <button type="submit" class="btn-primary">Login</button>
            </form>

            <div id="errorMessage" class="error-message" style="display: none;"></div>
        </div>
    </div>

    <script src="/static/js/auth.js"></script>
</body>
</html>
```

**Chat Interface** (`ui/chat.html`):

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis - Chat</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="chat-container">
        <!-- Header -->
        <div class="chat-header">
            <div class="header-left">
                <h2>🤖 Jarvis</h2>
                <span class="status-indicator">● Online</span>
            </div>
            <div class="header-right">
                <span id="userInfo" class="user-name"></span>
                <button id="logoutBtn" class="btn-logout">Logout</button>
            </div>
        </div>

        <!-- Chat Messages -->
        <div id="chatMessages" class="chat-messages">
            <div class="message bot">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <p>Hello! I'm Jarvis, your AI assistant. I can help you with:</p>
                    <ul>
                        <li>Managing IT tickets</li>
                        <li>Viewing cloud costs (FinOps)</li>
                        <li>Tracking your learning journey and exams</li>
                    </ul>
                    <p>What can I help you with today?</p>
                </div>
            </div>
        </div>

        <!-- Input Area -->
        <div class="chat-input-container">
            <form id="chatForm">
                <input type="text" id="messageInput" placeholder="Type your message..."
                       autocomplete="off" required>
                <button type="submit" class="btn-send">
                    <span>Send</span> →
                </button>
            </form>
        </div>
    </div>

    <script src="/static/js/chat.js"></script>
</body>
</html>
```

**Authentication JavaScript** (`ui/static/js/auth.js`):

```javascript
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Store token and user info
            localStorage.setItem('auth_token', data.token);
            localStorage.setItem('username', username);

            // Redirect to chat
            window.location.href = '/chat.html';
        } else {
            errorMessage.textContent = data.error || 'Login failed';
            errorMessage.style.display = 'block';
        }
    } catch (error) {
        errorMessage.textContent = 'Network error. Please try again.';
        errorMessage.style.display = 'block';
    }
});
```

**Chat JavaScript** (`ui/static/js/chat.js`):

```javascript
// Check authentication
const authToken = localStorage.getItem('auth_token');
const username = localStorage.getItem('username');

if (!authToken) {
    window.location.href = '/';
}

// Display user info
document.getElementById('userInfo').textContent = `Logged in as: ${username}`;

// Logout handler
document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('username');
    window.location.href = '/';
});

// Send message
document.getElementById('chatForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const messageInput = document.getElementById('messageInput');
    const userMessage = messageInput.value.trim();

    if (!userMessage) return;

    // Display user message
    addMessage(userMessage, 'user');
    messageInput.value = '';

    // Show typing indicator
    const typingIndicator = addTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                message: userMessage,
                username: username
            })
        });

        const data = await response.json();

        // Remove typing indicator
        typingIndicator.remove();

        if (response.ok) {
            addMessage(data.response, 'bot');
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        typingIndicator.remove();
        addMessage('Network error. Please check your connection.', 'bot');
    }
});

function addMessage(text, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? '👤' : '🤖';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = `<p>${text}</p>`;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <p>Typing...</p>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return typingDiv;
}
```

**Backend API Updates** (`web.py`):

```python
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jarvis_agent.auth.jwt_handler import create_access_token, verify_token
import os

app = FastAPI()

# Mount static files and UI
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

security = HTTPBearer()

# Simple user database (replace with real database in production)
USERS_DB = {
    "vishal": {"password": "password123", "email": "vishal@company.com"},
    "happy": {"password": "password123", "email": "happy@company.com"}
}

class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str
    username: str

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve login page."""
    with open("ui/index.html") as f:
        return HTMLResponse(content=f.read())

@app.get("/chat.html", response_class=HTMLResponse)
async def chat_page():
    """Serve chat page."""
    with open("ui/chat.html") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = USERS_DB.get(request.username)

    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(request.username)

    return {
        "token": token,
        "username": request.username,
        "email": user["email"]
    }

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return username."""
    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload.get("sub")

@app.post("/api/chat")
async def chat(request: ChatRequest, current_user: str = Depends(get_current_user)):
    """Handle chat messages - integrate with Jarvis agent."""
    # TODO: Integrate with root_agent here
    # For now, return a simple response

    # Verify user matches token
    if current_user != request.username:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Process message with Jarvis agent
    # response = root_agent.process(request.message, user=request.username)

    return {
        "response": f"I received your message: '{request.message}'. Integration with Jarvis agent coming soon!"
    }
```

**Styling** (`ui/static/css/style.css`):

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
}

/* Login Page */
.login-container {
    width: 100%;
    max-width: 400px;
    padding: 20px;
}

.login-box {
    background: white;
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
    text-align: center;
}

.login-box h1 {
    color: #333;
    margin-bottom: 10px;
}

.login-box p {
    color: #666;
    margin-bottom: 30px;
}

.form-group {
    margin-bottom: 20px;
    text-align: left;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    color: #333;
    font-weight: 500;
}

.form-group input {
    width: 100%;
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
}

.btn-primary {
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
}

.error-message {
    margin-top: 15px;
    padding: 12px;
    background: #fee;
    color: #c33;
    border-radius: 8px;
}

/* Chat Interface */
.chat-container {
    width: 100%;
    height: 100vh;
    background: white;
    display: flex;
    flex-direction: column;
}

.chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.status-indicator {
    color: #4ade80;
    font-size: 12px;
}

.btn-logout {
    padding: 8px 16px;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    border: 1px solid white;
    border-radius: 6px;
    cursor: pointer;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    background: #f5f5f5;
}

.message {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
}

.message.user {
    flex-direction: row-reverse;
}

.message-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #667eea;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}

.message.user .message-avatar {
    background: #764ba2;
}

.message-content {
    max-width: 70%;
    padding: 12px 16px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message.user .message-content {
    background: #667eea;
    color: white;
}

.chat-input-container {
    padding: 20px;
    background: white;
    border-top: 1px solid #e0e0e0;
}

#chatForm {
    display: flex;
    gap: 12px;
}

#messageInput {
    flex: 1;
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
}

.btn-send {
    padding: 12px 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
}
```

#### 2.4 Phase 2 Testing Scenarios

```
User: "Login as vishal"
System: Generates token, stores in session
Expected: "Welcome vishal! You're now logged in."

User: "Show me my enrolled courses"
System: Passes token to Oxygen
Expected: Vishal's courses from Oxygen

User: "Show me happy's courses"
System: Token is for vishal, not happy
Expected: "Unauthorized: You can only access your own data."

User: (No login) "Show me my exams"
Expected: "Please log in to access your learning data."
```

---

### Phase 3: Memory & Context Management

**Goal**: Implement session, short-term, and long-term memory for contextual conversations

#### 3.1 Memory Architecture

```
┌─────────────────────────────────────────┐
│         Memory Layers                   │
├─────────────────────────────────────────┤
│ Session Memory (Current conversation)   │
│  - Active context                       │
│  - Last 5-10 interactions               │
├─────────────────────────────────────────┤
│ Short-term Memory (Recent sessions)     │
│  - Last 24 hours                        │
│  - Incomplete tasks                     │
├─────────────────────────────────────────┤
│ Long-term Memory (Historical)           │
│  - User preferences                     │
│  - Common queries                       │
│  - Task patterns                        │
└─────────────────────────────────────────┘
```

#### 3.2 Implementation Components Using ADK Services

**Session Service Configuration** (`jarvis_agent/session_config.py`):

```python
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from google.adk.memory import VertexAIMemoryBankService
import os

# Choose session service based on environment
def get_session_service():
    """Get appropriate session service based on configuration."""
    session_type = os.getenv('SESSION_TYPE', 'memory')

    if session_type == 'memory':
        # For development - stores in memory
        return InMemorySessionService()

    elif session_type == 'database':
        # For production - persists to database
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./jarvis.db')
        return DatabaseSessionService(database_url=database_url)

    else:
        return InMemorySessionService()

def get_memory_service():
    """Get long-term memory service using Vertex AI."""
    project_id = os.getenv('GCP_PROJECT_ID')

    if project_id:
        # Use Vertex AI for long-term memory with vector search
        return VertexAIMemoryBankService(
            project_id=project_id,
            location=os.getenv('GCP_LOCATION', 'us-central1')
        )

    return None  # Long-term memory is optional

# Initialize services
session_service = get_session_service()
memory_service = get_memory_service()
```

**Context-Aware Root Agent with ADK Session Service**:

```python
from google.adk.agents import LlmAgent
from jarvis_agent.session_config import session_service, memory_service

root_agent = LlmAgent(
    name="JarvisOrchestrator",
    model=GEMINI_2_5_FLASH,
    session_service=session_service,  # ADK manages session state
    memory_service=memory_service,     # Optional: Long-term memory
    instruction="""You are Jarvis with memory and context awareness.

**Session Management (ADK Automatic):**
- The system automatically remembers conversation context
- Reference previous queries in the session naturally
- Maintain continuity across multi-turn conversations

**Task Resumption:**
- Check session state for incomplete tasks when user returns
- Offer to resume: "Welcome back! You were reviewing AWS costs. Continue?"

**Proactive Notifications:**
- Alert users about pending exam deadlines from Oxygen
- Notify about new tickets assigned
- Suggest next actions based on session history

**Context Awareness:**
- "Show me more details" automatically references last query
- User preferences tracked in long-term memory
- Provide personalized recommendations

The session and memory services handle persistence - you focus on the conversation.""",
    sub_agents=[tickets_agent, finops_agent, oxygen_agent],
)
```

#### 3.3 Notification System with ADK Session Integration

**Proactive Notifications** (`jarvis_agent/notifications/notifier.py`):

```python
from datetime import datetime, timedelta
from typing import List, Dict
from google.adk.sessions import SessionService

class NotificationManager:
    def __init__(self, session_service: SessionService):
        self.session_service = session_service

    def check_exam_deadlines(self, username: str, oxygen_agent) -> List[Dict]:
        """Check for upcoming exam deadlines using Oxygen agent."""
        # Get pending exams from Oxygen
        exams = oxygen_agent.get_pending_exams(username)

        notifications = []
        today = datetime.utcnow()

        for exam in exams.get("pending_exams", []):
            deadline = datetime.fromisoformat(exam["deadline"])
            days_until = (deadline - today).days

            if days_until <= 3:
                notifications.append({
                    "type": "urgent_deadline",
                    "message": f"⚠️ Your {exam['exam']} exam is in {days_until} days! ({exam['deadline']})",
                    "priority": "high"
                })
            elif days_until <= 7:
                notifications.append({
                    "type": "upcoming_deadline",
                    "message": f"📅 Reminder: {exam['exam']} exam is in {days_until} days ({exam['deadline']})",
                    "priority": "medium"
                })

        return notifications

    def get_incomplete_tasks_from_session(self, session_id: str) -> List[Dict]:
        """Retrieve incomplete tasks from ADK session."""
        session_data = self.session_service.get_session(session_id)

        if session_data and 'incomplete_tasks' in session_data:
            return session_data['incomplete_tasks']

        return []

    def get_all_notifications(self, username: str, session_id: str, oxygen_agent) -> List[Dict]:
        """Get all notifications for user."""
        notifications = []

        # Exam deadline notifications
        notifications.extend(self.check_exam_deadlines(username, oxygen_agent))

        # Incomplete tasks from session
        incomplete = self.get_incomplete_tasks_from_session(session_id)
        if incomplete:
            notifications.append({
                "type": "incomplete_tasks",
                "message": f"You have {len(incomplete)} incomplete task(s). Would you like to resume?",
                "priority": "medium",
                "tasks": incomplete
            })

        return notifications
```

#### 3.4 Phase 3 Testing Scenarios

**Test 1: Session Memory**
```
User: "Show me AWS costs"
Jarvis: (shows AWS costs)

User: "What about GCP?"
Jarvis: (understands context, shows GCP costs)

User: "And which is cheaper?"
Jarvis: (compares AWS vs GCP from session context)
```

**Test 2: Task Resumption**
```
Session 1:
User: "I want to check my exam deadlines"
Jarvis: Shows deadlines
(User logs out without completing exam prep)

Session 2 (Next day):
User: (logs in)
Jarvis: "Welcome back! Yesterday you were reviewing your exam deadlines.
        Your Snowflake exam is in 2 days. Would you like to continue preparing?"
```

**Test 3: Proactive Notifications**
```
User: (logs in)
Jarvis: "Welcome vishal! Here are your notifications:
        ⚠️ Your Snowflake exam is in 2 days! (2025-01-15)
        📋 You have 1 incomplete task: Update budget ticket
        Would you like to address these?"
```

**Test 4: Context Suggestions**
```
User: "Show my tickets"
Jarvis: (shows tickets)
Jarvis: "I notice you have a pending 'update_budget' ticket.
        Would you like to see the current GCP budget from FinOps?"
```

---

### Phase 4: OAuth 2.0 Authentication (Enterprise Enhancement)

**Goal**: Implement enterprise-grade OAuth 2.0 authentication for seamless integration with identity providers

#### 4.1 OAuth Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  OAuth 2.0 Flow                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  User → Auth Provider (Google/Auth0/Okta)              │
│           ↓                                             │
│  Authorization Code → Access Token                      │
│           ↓                                             │
│  Jarvis validates token → Creates session              │
│           ↓                                             │
│  Token passed to Oxygen via A2A                        │
│           ↓                                             │
│  Oxygen validates with auth provider                   │
│           ↓                                             │
│  User-specific data returned                           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

#### 4.2 OAuth Provider Configuration

**Supported Providers:**
- Google Workspace (OAuth 2.0)
- Microsoft Azure AD
- Auth0
- Okta
- Any OAuth 2.0 compatible provider

**Environment Configuration** (`.env`):
```bash
# OAuth 2.0 Configuration
OAUTH_PROVIDER=google  # google | azure | auth0 | okta
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
OAUTH_REDIRECT_URI=http://localhost:9999/auth/callback
OAUTH_SCOPES=openid email profile

# Auth0 specific (if using Auth0)
AUTH0_DOMAIN=your-tenant.auth0.com

# Azure AD specific (if using Azure)
AZURE_TENANT_ID=your_tenant_id
```

#### 4.3 Implementation Components

**OAuth Handler** (`jarvis_agent/auth/oauth_handler.py`):

```python
from google.adk.auth import HTTPBearer
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from typing import Dict, Optional
import os

class OAuthHandler:
    """Handles OAuth 2.0 authentication flow."""

    def __init__(self):
        self.config = Config(environ=os.environ)
        self.oauth = OAuth(self.config)

        # Register OAuth provider
        self.oauth.register(
            name=os.getenv('OAUTH_PROVIDER', 'google'),
            client_id=os.getenv('OAUTH_CLIENT_ID'),
            client_secret=os.getenv('OAUTH_CLIENT_SECRET'),
            server_metadata_url=self._get_metadata_url(),
            client_kwargs={'scope': os.getenv('OAUTH_SCOPES', 'openid email profile')}
        )

    def _get_metadata_url(self) -> str:
        """Get OAuth provider metadata URL."""
        provider = os.getenv('OAUTH_PROVIDER', 'google')

        metadata_urls = {
            'google': 'https://accounts.google.com/.well-known/openid-configuration',
            'azure': f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}/v2.0/.well-known/openid-configuration",
            'auth0': f"https://{os.getenv('AUTH0_DOMAIN')}/.well-known/openid-configuration",
        }

        return metadata_urls.get(provider)

    async def get_authorization_url(self, redirect_uri: str) -> str:
        """Generate authorization URL for OAuth flow."""
        return await self.oauth.create_client(os.getenv('OAUTH_PROVIDER')).authorize_redirect(
            redirect_uri=redirect_uri
        )

    async def handle_callback(self, code: str) -> Dict:
        """Handle OAuth callback and exchange code for token."""
        client = self.oauth.create_client(os.getenv('OAUTH_PROVIDER'))
        token = await client.authorize_access_token()

        # Get user info
        user_info = await client.parse_id_token(token)

        return {
            'access_token': token['access_token'],
            'refresh_token': token.get('refresh_token'),
            'id_token': token['id_token'],
            'user_info': {
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'sub': user_info.get('sub')  # Unique user ID
            }
        }

    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate OAuth token with provider."""
        # Use provider's token introspection endpoint
        # Implementation depends on provider
        pass
```

**ADK HTTPBearer Integration** (`jarvis_agent/auth/adk_auth.py`):

```python
from google.adk.auth import HTTPBearer
from typing import Optional

class JarvisOAuthAuth(HTTPBearer):
    """Custom OAuth authentication for ADK tools."""

    def __init__(self, oauth_handler: OAuthHandler):
        super().__init__(scheme_name="OAuth2Bearer")
        self.oauth_handler = oauth_handler

    async def __call__(self, token: str) -> Optional[str]:
        """Validate OAuth token and return user identifier."""
        validation_result = await self.oauth_handler.validate_token(token)

        if validation_result and validation_result.get('valid'):
            # Return user email or ID
            return validation_result['user_info']['email']

        return None

# Usage in Oxygen agent tools
oauth_auth = JarvisOAuthAuth(oauth_handler)

def get_user_courses(username: str, _auth: oauth_auth = None) -> Dict:
    """Get courses for authenticated user.

    Args:
        username: The username
        _auth: OAuth authentication (automatically injected by ADK)

    Returns:
        User's course information
    """
    # _auth contains validated user email from OAuth token
    if not _auth:
        return {
            "success": False,
            "error": "Authentication required via OAuth"
        }

    # Verify username matches authenticated user
    if _auth.lower() != username.lower():
        return {
            "success": False,
            "error": "Unauthorized: Can only access own data"
        }

    # Return user data
    # ... implementation
```

#### 4.4 Web UI OAuth Integration

**FastAPI OAuth Endpoints** (`web.py` additions):

```python
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from jarvis_agent.auth.oauth_handler import OAuthHandler

app = FastAPI()
oauth_handler = OAuthHandler()

@app.get("/auth/login")
async def login(request: Request):
    """Initiate OAuth login flow."""
    redirect_uri = request.url_for('auth_callback')
    return await oauth_handler.get_authorization_url(redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    """Handle OAuth callback."""
    code = request.query_params.get('code')

    try:
        token_data = await oauth_handler.handle_callback(code)

        # Store token in session
        request.session['access_token'] = token_data['access_token']
        request.session['user_email'] = token_data['user_info']['email']
        request.session['user_name'] = token_data['user_info']['name']

        # Redirect to chat UI
        return RedirectResponse(url="/dev-ui")

    except Exception as e:
        return {"error": f"Authentication failed: {str(e)}"}

@app.get("/auth/logout")
async def logout(request: Request):
    """Clear session and log out."""
    request.session.clear()
    return RedirectResponse(url="/")
```

#### 4.5 A2A OAuth Token Passing

**Modified Root Agent with OAuth** (`jarvis_agent/agent.py`):

```python
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH

# Oxygen agent with OAuth support
oxygen_agent = RemoteA2aAgent(
    name="oxygen_agent",
    description="Learning platform with OAuth authentication",
    agent_card=f"http://localhost:8002{AGENT_CARD_WELL_KNOWN_PATH}",
    auth_token="${session.access_token}"  # Pass OAuth token from session
)

root_agent = LlmAgent(
    name="JarvisOrchestrator",
    model=GEMINI_2_5_FLASH,
    instruction="""You are Jarvis with OAuth 2.0 authentication.

When users access Oxygen (learning platform):
1. Verify OAuth token exists in session
2. Pass token to Oxygen agent automatically
3. Handle authentication errors gracefully

OAuth tokens are managed by the platform - you don't need to ask users for them.
If authentication fails, inform user to log in via the web UI.""",
    sub_agents=[tickets_agent, finops_agent, oxygen_agent],
)
```

#### 4.6 Integration Connectors (Enterprise)

For enterprise deployments, leverage Google's Integration Connectors:

**Supported Enterprise Systems (100+):**
- Salesforce
- ServiceNow
- SAP
- Workday
- Jira
- Confluence
- Slack
- Microsoft Teams

**Configuration Example** (`jarvis_agent/connectors/salesforce.py`):

```python
from google.cloud import integrations_v1

class SalesforceConnector:
    """Connect Jarvis to Salesforce via Integration Connectors."""

    def __init__(self, project_id: str, location: str):
        self.client = integrations_v1.IntegrationsClient()
        self.project_id = project_id
        self.location = location

    def create_ticket_from_salesforce_case(self, case_id: str) -> Dict:
        """Create Jarvis ticket from Salesforce case."""
        # Use Integration Connector to fetch case details
        # Create ticket in Jarvis system
        pass
```

#### 4.7 Phase 4 Testing Scenarios

**Test 1: OAuth Login Flow**
```
User: Visits http://localhost:9999/auth/login
System: Redirects to Google/Auth0 login
User: Authenticates with provider
System: Redirects back with access token
Expected: User logged in, token stored in session
```

**Test 2: Authenticated Learning Access**
```
User: (Logged in as vishal@company.com)
User: "Show my enrolled courses"
System: Passes OAuth token to Oxygen
Oxygen: Validates token with OAuth provider
Expected: Returns vishal's courses
```

**Test 3: Cross-User Access Prevention**
```
User: (Logged in as vishal@company.com)
User: "Show happy's courses"
System: Passes OAuth token (for vishal)
Oxygen: Validates token, checks authorization
Expected: Error - "Unauthorized: Can only access own data"
```

**Test 4: Token Refresh**
```
User: (Active session, token near expiry)
User: "Check my exam deadlines"
System: Detects token expiration, uses refresh token
System: Gets new access token from OAuth provider
Expected: Seamless continuation without re-login
```

**Test 5: SSO with Multiple Systems**
```
User: Logs in via Google Workspace SSO
System: Creates Jarvis session with Google OAuth token
User: "Create a ticket for ServiceNow integration"
System: Uses Integration Connector with same OAuth token
Expected: Ticket created in both Jarvis and ServiceNow
```

#### 4.8 Security Considerations

**Best Practices:**
1. **Token Storage**: Never store tokens in logs or plain text
2. **HTTPS Only**: Enforce HTTPS in production for OAuth callbacks
3. **Token Expiry**: Implement automatic token refresh
4. **Scope Limitation**: Request minimal OAuth scopes needed
5. **Audit Logging**: Log all authentication events
6. **Rate Limiting**: Prevent token replay attacks

**Security Configuration** (`jarvis_agent/auth/security_config.py`):

```python
from datetime import timedelta

SECURITY_CONFIG = {
    # Token settings
    'access_token_expire_minutes': 60,
    'refresh_token_expire_days': 30,

    # OAuth settings
    'enforce_https': True,  # Set to True in production
    'allowed_redirect_hosts': ['localhost', 'jarvis.company.com'],

    # Rate limiting
    'max_login_attempts': 5,
    'lockout_duration_minutes': 15,

    # Audit logging
    'log_auth_events': True,
    'log_token_usage': True,
}
```

---

## Dependencies (requirements.txt)

```txt
# Google ADK and dependencies
google-adk[a2a]>=1.0.0          # ADK v1.0.0+ includes OAuth 2.0 support
google-genai>=0.1.0

# A2A communication
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0

# Toolbox integration
toolbox-core>=0.1.0

# Authentication (Phase 2)
pyjwt>=2.8.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# OAuth 2.0 (Phase 4)
authlib>=1.2.0                  # OAuth client library
itsdangerous>=2.1.2             # Secure session management
starlette>=0.27.0               # ASGI framework for OAuth
python-multipart>=0.0.6         # Form data parsing

# Google Cloud (for Integration Connectors - Optional)
google-cloud-integrations>=1.0.0

# Environment management
python-dotenv>=1.0.0

# HTTP clients
requests>=2.31.0
httpx>=0.25.0

# Session & Memory (Phase 3)
sqlalchemy>=2.0.0               # Database ORM
aiosqlite>=0.19.0               # Async SQLite driver
redis>=5.0.0                    # Optional: Redis for distributed sessions

# Utilities
python-dateutil>=2.8.2
```

---

## Environment Configuration

**.env.template**:
```bash
# Google API Key (get from https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=your_api_key_here

# JWT Secret (Phase 2 - generate a secure random string)
JWT_SECRET_KEY=your_secret_key_here

# OAuth 2.0 Configuration (Phase 4)
OAUTH_PROVIDER=google                    # google | azure | auth0 | okta
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
OAUTH_REDIRECT_URI=http://localhost:9999/auth/callback
OAUTH_SCOPES=openid email profile

# Auth0 specific (if using Auth0)
AUTH0_DOMAIN=your-tenant.auth0.com

# Azure AD specific (if using Azure)
AZURE_TENANT_ID=your_tenant_id

# Service Ports
TICKETS_SERVER_PORT=5001
FINOPS_SERVER_PORT=5002
OXYGEN_AGENT_PORT=8002
WEB_UI_PORT=9999

# Database (Phase 3 - for session and memory persistence)
DATABASE_URL=sqlite:///./jarvis.db

# Redis (Phase 3 - optional for distributed sessions)
REDIS_URL=redis://localhost:6379/0

# Session Configuration (Phase 3)
SESSION_TYPE=memory                      # memory | database | redis
SESSION_EXPIRE_MINUTES=60

# Security Settings
ENFORCE_HTTPS=false                      # Set to true in production
```

---

## Success Criteria

### Phase 1: Core Functionality
- ✅ All 3 agents (Tickets, FinOps, Oxygen) functional
- ✅ A2A communication working between Jarvis and Oxygen
- ✅ Web UI accessible and responsive
- ✅ All CRUD operations working for tickets and courses
- ✅ Cost analytics accurate across all cloud providers

### Phase 2: JWT Authentication
- ✅ JWT authentication implemented
- ✅ Users can only access their own learning data
- ✅ Unauthorized access properly handled
- ✅ Token passed correctly in A2A calls

### Phase 3: Memory & Context
- ✅ Session memory maintains conversation context
- ✅ Users can resume incomplete tasks
- ✅ Proactive notifications for deadlines
- ✅ Context-aware suggestions
- ✅ Long-term preferences tracked

### Phase 4: OAuth 2.0 (Enterprise)
- ✅ OAuth 2.0 authentication with multiple providers (Google, Azure, Auth0, Okta)
- ✅ Secure token exchange and validation
- ✅ Token refresh mechanism working
- ✅ SSO integration with enterprise identity providers
- ✅ Integration Connectors functional (optional enterprise feature)
- ✅ HTTPS enforced in production
- ✅ Audit logging for all authentication events

---

## Deployment & Operations

### Starting the System (All Phases)

```bash
# Terminal 1: Tickets Server
./scripts/start_tickets_server.sh

# Terminal 2: FinOps Server
./scripts/start_finops_server.sh

# Terminal 3: Oxygen Agent (A2A)
./scripts/start_oxygen_agent.sh

# Terminal 4: Web UI
./scripts/start_web.sh
```

### Health Check
```bash
./scripts/check_services.sh
```

### Logs & Debugging
```bash
# Check if all services are running
lsof -i :5001  # Tickets
lsof -i :5002  # FinOps
lsof -i :8002  # Oxygen
lsof -i :9999  # Web UI

# Test individual endpoints
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:8002/.well-known/agent-card.json
curl http://localhost:9999/health
```

---

## Comparison with Supply Chain Agent

| Aspect | Supply Chain Agent | Agentic Jarvis |
|--------|-------------------|----------------|
| **Domain** | E-commerce operations | IT operations + learning |
| **Local Agents** | Inventory, Logistics | Tickets, FinOps |
| **Remote Agent** | Finance (approval workflow) | Oxygen (learning platform) |
| **Toolbox Servers** | 1 (port 5000) | 2 (ports 5001, 5002) |
| **A2A Port** | 8001 | 8002 |
| **Authentication** | None | Phase 2: JWT + Phase 4: OAuth 2.0 |
| **Memory** | Stateless | Phase 3: Multi-layer memory |
| **Enterprise Features** | Basic | Phase 4: SSO, Integration Connectors |
| **Use Case** | Order processing & approvals | Tickets, costs, learning tracking |

---

## Next Steps After Documentation

1. **Set up project structure** as outlined above
2. **Copy working patterns** from supply_chain_agent:
   - Toolbox server implementation
   - A2A agent setup with `port` parameter
   - Startup scripts with port cleanup
3. **Implement Phase 1** completely before moving to Phase 2
4. **Test each agent individually** before integration
5. **Use `check_services.sh`** to verify all services running
6. **Document any deviations** from this spec as you build

---

## Support & References

### Official Documentation
- **Google ADK Docs**: https://google.github.io/adk-docs/
- **A2A Protocol**: https://google.github.io/adk-docs/a2a/
- **MCP Tools**: https://google.github.io/adk-docs/tools-custom/mcp-tools/

### Authentication & Security (Phases 2 & 4)
- **Authentication Guide**: https://google.github.io/adk-docs/tools-custom/authentication/
- **OAuth2-Powered ADK Agents**: https://medium.com/google-cloud/secure-and-smart-oauth2-powered-google-adk-agents-with-integration-connectors-for-enterprises-8916028b97ca
- **A2A Protocol v0.2 (OAuth)**: https://google.github.io/adk-docs/a2a/ (May 2025 update)

### Memory & Sessions (Phase 3)
- **Session Management**: https://google.github.io/adk-docs/sessions/
- **Agent State and Memory Tutorial**: https://cloud.google.com/blog/topics/developers-practitioners/remember-this-agent-state-and-memory-with-adk

### Working Example
- **Your Supply Chain Agent Demo**: `/Users/vishalkumar/projects/supply_chain_agent_demo`

### Community & Support
- **GitHub Issues**: https://github.com/google/adk/issues
- **Stack Overflow**: Tag `google-adk`

---

*This documentation is based on the working supply chain agent demo and adapted for the Agentic Jarvis product requirements.*
