# Jarvis Architecture Vision

**Date**: 2025-12-30
**Status**: Canonical Reference for All Implementation

---

## Core Principles

### 1. Everything is an Agent Service (No Local Agents)

**Vision**: All functionality, including Jarvis core services, is delivered through **agent services** registered in the Agent Registry.

- ✅ **Tickets Agent** → Separate service (A2A protocol)
- ✅ **FinOps Agent** → Separate service (A2A protocol)
- ✅ **Oxygen Agent** → Separate service (A2A protocol)
- ✅ **Future agents** → All registered via agent cards

**No embedded code** - Jarvis is purely an orchestrator/router.

---

### 2. Agent Services Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Jarvis Orchestrator                            │
│  - Dynamic routing (TwoStageRouter)                         │
│  - Agent discovery from registry                            │
│  - Session management                                       │
│  - Response combination                                     │
│  - NO embedded agents or tools                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           Agent Registry Service (Port 8003)                │
│  - Stores agent metadata (name, card URL, capabilities)     │
│  - Agent discovery API                                      │
│  - Session tracking                                         │
│  - NO agent factories or code references                    │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Tickets      │  │ FinOps       │  │ Oxygen       │
│ Agent        │  │ Agent        │  │ Agent        │
│ Service      │  │ Service      │  │ Service      │
│ (Port 8080)  │  │ (Port 8081)  │  │ (Port 8082)  │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ LlmAgent     │  │ LlmAgent     │  │ LlmAgent     │
│ + Toolbox    │  │ + Toolbox    │  │ + Toolbox    │
│ + A2A Server │  │ + A2A Server │  │ + A2A Server │
└──────────────┘  └──────────────┘  └──────────────┘
 Self-contained    Self-contained    Self-contained
```

---

### 3. Agent Service Structure

Each agent service is **self-contained** with:

1. **Agent Definition** (LlmAgent)
2. **Tools/Toolbox** (business logic)
3. **A2A Server** (protocol exposure via `to_a2a()`)
4. **Agent Card** (auto-generated at `/.well-known/agent-card.json`)

**Example - Tickets Agent Service:**

```python
# tickets_agent_service/agent.py

from google.adk.agents import LlmAgent
from google.adk.toolbox import Toolbox
from google.adk.runners.a2a import to_a2a

# Define tools (business logic)
def get_all_tickets() -> list:
    """Get all IT tickets."""
    return TICKETS_DB

def create_ticket(operation: str, user: str) -> dict:
    """Create new IT ticket."""
    # Implementation...

# Create toolbox
toolbox = Toolbox()
toolbox.add_tool(get_all_tickets)
toolbox.add_tool(create_ticket)

# Create agent
tickets_agent = LlmAgent(
    name="TicketsAgent",
    description="IT operations ticket management",
    instruction="You handle IT tickets...",
    tools=toolbox.tools,
    model="gemini-2.5-flash"
)

# Expose via A2A protocol
if __name__ == "__main__":
    a2a_app = to_a2a(
        tickets_agent,
        port=8080,
        host="0.0.0.0"
    )
    print("✅ Tickets Agent Service running on port 8080")
    print("📋 Agent card: http://localhost:8080/.well-known/agent-card.json")
```

**Running:**
```bash
# Local Development (no Docker)
python tickets_agent_service/agent.py

# Production (Dockerized)
docker run -p 8080:8080 tickets-agent-service
```

---

### 4. Agent Registry Format

Registry stores **only agent card URLs** (no factory references, no code):

```json
{
  "version": "2.0.0",
  "agents": {
    "TicketsAgent": {
      "type": "remote",
      "agent_card_url": "http://localhost:8080/.well-known/agent-card.json",
      "description": "IT operations ticket management",
      "capabilities": {
        "domains": ["tickets", "IT"],
        "entities": ["ticket", "request"],
        "operations": ["create", "read", "list"]
      },
      "status": "enabled",
      "tags": ["core", "production"]
    },
    "FinOpsAgent": {
      "type": "remote",
      "agent_card_url": "http://localhost:8081/.well-known/agent-card.json",
      "description": "Cloud cost analytics",
      "capabilities": {
        "domains": ["costs", "finops"],
        "entities": ["cost", "budget"],
        "operations": ["read", "analyze"]
      },
      "status": "enabled",
      "tags": ["core", "production"]
    },
    "OxygenAgent": {
      "type": "remote",
      "agent_card_url": "http://localhost:8082/.well-known/agent-card.json",
      "description": "Learning and development platform",
      "capabilities": {
        "domains": ["learning", "courses"],
        "entities": ["course", "exam"],
        "operations": ["read", "track"]
      },
      "status": "enabled",
      "tags": ["core", "production"]
    }
  }
}
```

**Key Points:**
- ✅ All agents are `type: "remote"`
- ✅ Only `agent_card_url` is stored
- ✅ NO `factory_module` or `factory_function`
- ✅ Agents are discovered dynamically via agent cards

---

### 5. Jarvis Orchestrator Flow

```
1. User: "show my tickets"
   ↓
2. Jarvis queries registry: GET /registry/agents
   ↓
3. Registry returns: {
     "TicketsAgent": {
       "agent_card_url": "http://localhost:8080/.well-known/agent-card.json"
     }
   }
   ↓
4. Router selects: TicketsAgent
   ↓
5. Jarvis creates RemoteA2aAgent:
   agent = RemoteA2aAgent(
       name="TicketsAgent",
       agent_card="http://localhost:8080/.well-known/agent-card.json"
   )
   ↓
6. Invoke via A2A protocol:
   response = runner.run(agent, query)
   ↓
7. A2A calls: POST http://localhost:8080/invoke
   ↓
8. Tickets service processes and returns response
   ↓
9. Jarvis returns to user
```

**No code loading, no factories, pure discovery!**

---

### 6. Authentication Flow (Phase 2)

```
User logs in → Jarvis gets OAuth token
   ↓
User: "show my tickets"
   ↓
Jarvis invokes TicketsAgent with token:
   POST http://localhost:8080/invoke
   Authorization: Bearer {user_token}
   ↓
TicketsAgent validates token → Returns user-specific data
```

**Authentication is end-to-end:**
- User authenticates with Jarvis (OAuth)
- Jarvis passes token to agents
- Each agent validates token independently
- Agents return only authorized data

---

## Implementation Phases

### Phase 1: Core Agent Services (Current)
- ✅ Convert all agents to A2A services
- ✅ Remove factory-based registration
- ✅ Update registry to store agent card URLs
- ✅ Update Jarvis to use RemoteA2aAgent for everything
- ✅ Test complete flow

### Phase 2: Authentication
- OAuth 2.0 integration in Jarvis
- Token passing to agent services
- Token validation in each agent
- User-specific data access

### Phase 3: Production Deployment
- Dockerize all agent services
- Deploy to cloud (Cloud Run, K8s, etc.)
- HTTPS for all agent cards
- Production registry service

### Phase 4: Agent Marketplace
- Third-party agent registration
- Agent approval workflow
- Agent discovery UI
- Monitoring and analytics

---

## Local Development Setup

**Start Services:**

```bash
# Terminal 1: Registry Service
python agent_registry_service/main.py

# Terminal 2: Tickets Agent Service
python tickets_agent_service/agent.py

# Terminal 3: FinOps Agent Service
python finops_agent_service/agent.py

# Terminal 4: Oxygen Agent Service
python oxygen_agent_service/agent.py

# Terminal 5: Jarvis Orchestrator
python jarvis_agent/main_with_registry.py
```

**Verify Services:**

```bash
# Check agent cards
curl http://localhost:8080/.well-known/agent-card.json  # Tickets
curl http://localhost:8081/.well-known/agent-card.json  # FinOps
curl http://localhost:8082/.well-known/agent-card.json  # Oxygen

# Check registry
curl http://localhost:8003/health
curl http://localhost:8003/registry/agents
```

---

## Production Deployment

**Each agent service has its own Dockerfile:**

```dockerfile
# tickets_agent_service/Dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["python", "agent.py"]
```

**Deploy independently:**

```bash
# Build and deploy each service
docker build -t tickets-agent-service tickets_agent_service/
docker build -t finops-agent-service finops_agent_service/
docker build -t oxygen-agent-service oxygen_agent_service/

# Deploy to cloud
gcloud run deploy tickets-agent --image tickets-agent-service --port 8080
gcloud run deploy finops-agent --image finops-agent-service --port 8081
gcloud run deploy oxygen-agent --image oxygen-agent-service --port 8082
```

**Registry points to production URLs:**

```json
{
  "TicketsAgent": {
    "agent_card_url": "https://tickets-agent-xyz.run.app/.well-known/agent-card.json"
  }
}
```

---

## Key Architectural Decisions

### ✅ DO:
- Store only agent card URLs in registry
- Use RemoteA2aAgent for ALL agents
- Each agent is self-contained (agent + tools + A2A)
- Agents validate authentication independently
- Dynamic discovery via agent cards
- Deploy agents independently (microservices)

### ❌ DON'T:
- Store factory functions or code references in registry
- Create "local" agents via factories
- Use McpToolset pointing to separate MCP servers
- Mix agent code with Jarvis orchestrator
- Hard-code agent endpoints in Jarvis
- Share state between agents

---

## Migration from Old Architecture

### Old (Factory-Based):
```json
{
  "tickets_agent": {
    "type": "local",
    "factory_module": "jarvis_agent.mcp_agents.agent_factory",
    "factory_function": "create_tickets_agent"
  }
}
```
**Problems:**
- Code coupling (factory in Jarvis codebase)
- Split architecture (agent via factory, tools via MCP server)
- Can't deploy agents independently
- Hard to add third-party agents

### New (A2A-Based):
```json
{
  "TicketsAgent": {
    "type": "remote",
    "agent_card_url": "http://localhost:8080/.well-known/agent-card.json"
  }
}
```
**Benefits:**
- ✅ Clean separation (agents are independent services)
- ✅ Self-contained (agent + tools together)
- ✅ Deploy independently (true microservices)
- ✅ Third-party agents work same way
- ✅ Pure discovery (no code loading)

---

## Summary

**Core Vision**: Jarvis is a **pure orchestrator** that discovers and invokes **independent agent services** via the **A2A protocol**. All functionality is delivered through agents registered in the **Agent Registry**. No embedded code, no factories, just **dynamic discovery and invocation**.

This architecture enables:
- **Scalability**: Deploy agents independently
- **Flexibility**: Add/remove agents without changing Jarvis
- **Security**: Each agent validates auth independently
- **Marketplace**: Third-party agents work exactly like core agents
- **Evolution**: Agents can be updated/replaced without affecting Jarvis

**Next Steps**: Implement Phase 1 by converting all agents to A2A services and updating the registry.
