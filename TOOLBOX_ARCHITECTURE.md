# Toolbox Architecture Pattern

This document explains the toolbox server pattern used in Agentic Jarvis and why it's beneficial for multi-agent systems.

---

## What is the Toolbox Pattern?

The **toolbox pattern** separates tool implementation from agent logic by running tools as independent HTTP services (toolbox servers). Agents connect to these servers via ADK's `ToolboxSyncClient` to load and execute tools.

```
┌─────────────────────────────────────────────────┐
│                Agent Layer                       │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  │
│  │TicketsAgent │  │FinOpsAgent│  │  Jarvis  │  │
│  │             │  │           │  │(Root)    │  │
│  └──────┬──────┘  └─────┬────┘  └────┬─────┘  │
│         │               │              │        │
│    ToolboxSyncClient    │         Routes to    │
│         │               │         Sub-agents   │
└─────────┼───────────────┼─────────────┼────────┘
          │               │              │
          ▼               ▼              │
┌─────────────────────────────────────────────────┐
│            Toolbox Server Layer                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │Tickets Server│  │FinOps Server │            │
│  │   :5001      │  │   :5002      │            │
│  │              │  │              │            │
│  │- get_ticket  │  │- get_costs   │            │
│  │- create_*    │  │- breakdown   │            │
│  └──────┬───────┘  └──────┬───────┘            │
└─────────┼──────────────────┼────────────────────┘
          │                  │
          ▼                  ▼
    ┌──────────┐      ┌──────────┐
    │Tickets DB│      │FinOps DB │
    └──────────┘      └──────────┘
```

---

## Why Use Toolbox Servers?

### 1. **Separation of Concerns**

**Without Toolbox Pattern:**
```python
# Everything mixed in one file
class TicketsAgent:
    def __init__(self):
        self.db = connect_to_database()
        self.agent = LlmAgent(...)

    def get_ticket(self, id):
        # Business logic mixed with agent code
        return self.db.query(...)
```

**With Toolbox Pattern:**
```python
# Toolbox Server (server.py) - Clean business logic
def get_ticket(ticket_id: int) -> Dict:
    """Get ticket by ID."""
    return query_database(ticket_id)

# Agent (agent.py) - Pure AI reasoning
toolbox = ToolboxSyncClient("http://localhost:5001")
tickets_agent = LlmAgent(
    name="TicketsAgent",
    tools=toolbox.load_toolset('tickets_toolset')
)
```

**Benefits:**
- Agent code focuses purely on AI reasoning and orchestration
- Tool code focuses purely on data access and business logic
- Easier to understand, maintain, and debug each component
- Clear boundaries between concerns

---

### 2. **Reusability Across Agents**

Multiple agents can share the same toolbox server:

```python
# Tickets tools used by multiple agents
tickets_agent = LlmAgent(
    tools=toolbox.load_toolset('tickets_toolset')
)

supervisor_agent = LlmAgent(
    tools=toolbox.load_toolset('tickets_toolset')  # Same tools!
)

# Even external systems can call tools via HTTP
curl http://localhost:5001/execute -d '{
    "name": "get_ticket",
    "arguments": {"ticket_id": 12301}
}'
```

**Benefits:**
- No code duplication
- Single source of truth for business logic
- Consistent behavior across all consumers
- Tools become reusable microservices

---

### 3. **Independent Development & Testing**

**Development:**
```bash
# Team A: Develop and test tickets tools independently
cd toolbox_servers/tickets_server
python server.py

# Test tools without starting agents
curl http://localhost:5001/toolsets/tickets_toolset
curl http://localhost:5001/execute -d '{"name": "get_all_tickets"}'

# Team B: Develop agents in parallel
# Agents just connect to running toolbox server
```

**Testing:**
```python
# Unit test tools directly
def test_get_ticket():
    result = get_ticket(12301)
    assert result['status'] == 'pending'

# Integration test via HTTP
def test_toolbox_endpoint():
    response = requests.post('http://localhost:5001/execute', json={
        'name': 'get_ticket',
        'arguments': {'ticket_id': 12301}
    })
    assert response.json()['success'] == True
```

**Benefits:**
- Parallel development (tools vs agents)
- Easy unit testing of business logic
- Test tools via HTTP without LLM calls
- Faster feedback loop during development

---

### 4. **MCP Protocol Compatibility**

The toolbox pattern follows the **Model Context Protocol (MCP)** standard:

```python
# Automatic schema generation from Python functions
def get_ticket(ticket_id: int) -> Optional[Dict]:
    """Get a specific ticket by ID.

    Args:
        ticket_id: The unique ticket identifier

    Returns:
        Ticket details or None if not found
    """
    # Function automatically becomes an MCP tool:
    # {
    #   "name": "get_ticket",
    #   "description": "Get a specific ticket by ID.",
    #   "inputSchema": {
    #     "properties": {
    #       "ticket_id": {"type": "integer", "description": "..."}
    #     },
    #     "required": ["ticket_id"]
    #   }
    # }
```

**Benefits:**
- Standards-compliant tool definitions
- ADK automatically discovers and loads tools
- Type hints become schema validation
- Docstrings become tool descriptions
- Works seamlessly with ADK's `ToolboxSyncClient`

---

### 5. **Flexibility for Future Enhancements**

**Easy to evolve without changing agents:**

```python
# Phase 1: In-memory database
TICKETS_DB = [...]

# Phase 2: Switch to PostgreSQL (no agent changes!)
import psycopg2
def get_ticket(ticket_id: int):
    conn = psycopg2.connect(DATABASE_URL)
    return conn.execute("SELECT * FROM tickets WHERE id = %s", [ticket_id])

# Phase 3: Add caching (no agent changes!)
@cache(ttl=60)
def get_ticket(ticket_id: int):
    return database.query(...)

# Phase 4: Add authentication (no agent changes!)
def get_ticket(ticket_id: int, _auth: HTTPBearer = None):
    validate_user(_auth)
    return database.query(...)
```

**Benefits:**
- Implement data sources progressively
- Add caching, authentication, rate limiting without touching agents
- Switch databases without agent code changes
- Tools can connect to real enterprise systems later

---

### 6. **Operational Benefits**

**Independent Service Management:**
```bash
# Restart only the tickets server (agents keep running)
./scripts/restart_tickets_server.sh

# Scale toolbox servers independently
# Run multiple instances behind a load balancer
./start_tickets_server.sh --port 5001 &
./start_tickets_server.sh --port 5011 &
./start_tickets_server.sh --port 5021 &

# Deploy updates without agent downtime
# Blue-green deployment of toolbox servers
```

**Error Isolation:**
- If a toolbox server crashes, agents can retry or route to other agents
- Errors in tool code don't crash the agent
- Better observability with separate service logs
- Health checks per service

**Benefits:**
- Independent scaling based on load
- Zero-downtime deployments
- Better fault isolation
- Service-level monitoring and alerting

---

### 7. **HTTP API Access**

Toolbox servers expose tools as REST APIs:

```bash
# List available toolsets
curl http://localhost:5001/toolsets
# Response: {"toolsets": ["tickets_toolset"]}

# Get tool schemas
curl http://localhost:5001/toolsets/tickets_toolset
# Response: Full schema with all tools

# Execute tools directly
curl -X POST http://localhost:5001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "create_ticket",
    "arguments": {
      "operation": "create_s3_bucket",
      "user": "john"
    }
  }'
```

**Benefits:**
- Debug tools with curl/Postman
- External systems can call tools
- API documentation auto-generated from schemas
- OpenAPI/Swagger integration possible

---

## Trade-offs

### Advantages ✅
- **Cleaner architecture** with separation of concerns
- **Reusable tools** across agents and systems
- **Independent testing** and development
- **Flexible evolution** (swap data sources, add features)
- **Operational benefits** (scaling, deployment, monitoring)
- **MCP standard compliance**

### Disadvantages ⚠️
- **More complexity** - additional servers to manage
- **Network overhead** - HTTP calls between agents and tools
- **More moving parts** - multiple services must be running
- **Initial setup time** - more code to write upfront

---

## When to Use Toolbox Pattern?

### ✅ **Use Toolbox Pattern When:**
- Building multi-agent systems with shared tools
- Tools need to access databases or external services
- Different teams working on tools vs agents
- Need independent scaling of tools and agents
- Planning to evolve data sources over time
- Following enterprise microservices architecture

### ⚠️ **Consider Direct Tools When:**
- Simple single-agent prototype
- All tools are pure functions with no external dependencies
- Speed of development more important than architecture
- Limited operational infrastructure

---

## Agentic Jarvis Implementation

In our system, we use the toolbox pattern for:

| Agent | Toolbox Server | Port | Tools |
|-------|---------------|------|-------|
| **TicketsAgent** | tickets_server | 5001 | get_all_tickets, get_ticket, get_user_tickets, create_ticket |
| **FinOpsAgent** | finops_server | 5002 | get_all_clouds_cost, get_cloud_cost, get_service_cost, get_cost_breakdown |
| **OxygenAgent** | Direct tools | - | get_user_courses, get_pending_exams, get_user_preferences, get_learning_summary |

**Why Oxygen doesn't use toolbox:**
- Oxygen is a **remote A2A agent** (runs as separate service on port 8002)
- A2A agents already provide HTTP-based communication
- Tools are tightly coupled to the Oxygen learning domain
- Oxygen itself acts like a "toolbox" for learning functions

---

## Code Comparison

### Direct Tools Approach (Simpler)
```python
# tools.py
def get_ticket(ticket_id: int) -> Dict:
    return TICKETS_DB[ticket_id]

# agent.py
from tools import get_ticket, create_ticket

agent = LlmAgent(
    name="TicketsAgent",
    tools=[get_ticket, create_ticket]  # Direct function references
)
```

**Pros:** Simple, fewer files, no HTTP overhead
**Cons:** Not reusable, harder to test, tight coupling

### Toolbox Pattern (Our Approach)
```python
# toolbox_servers/tickets_server/server.py
def get_ticket(ticket_id: int) -> Dict:
    return TICKETS_DB[ticket_id]

app = FastAPI()
# ... expose tools via HTTP endpoints

# jarvis_agent/sub_agents/tickets/agent.py
from toolbox_core import ToolboxSyncClient

toolbox = ToolboxSyncClient("http://localhost:5001")
tools = toolbox.load_toolset('tickets_toolset')

agent = LlmAgent(
    name="TicketsAgent",
    tools=tools  # Tools loaded via HTTP
)
```

**Pros:** Reusable, testable, flexible, scalable
**Cons:** More setup, HTTP overhead, multiple services

---

## Reference Architecture

This pattern is based on Google ADK's supply chain agent demo:
- Location: `/Users/vishalkumar/projects/supply_chain_agent_demo`
- Pattern proven in production ADK applications
- Follows ADK best practices and documentation

---

## Conclusion

The toolbox pattern adds architectural complexity but provides significant benefits for multi-agent systems that need to evolve over time. For Agentic Jarvis, the pattern is justified because:

1. We have **multiple agents** (Tickets, FinOps, Jarvis orchestrator)
2. Tools will eventually connect to **real databases/services**
3. We're following **proven ADK patterns** from reference implementations
4. The system is designed for **enterprise deployment** with Phase 2-4 enhancements

The upfront investment in proper architecture pays off as the system grows in complexity and scale.

---

**See Also:**
- [CLAUDE.md](./CLAUDE.md) - Development guide
- [TASKS.md](./TASKS.md) - Implementation tasks
- [Google ADK Toolbox Documentation](https://google.github.io/adk-docs/tools-custom/toolbox/)
