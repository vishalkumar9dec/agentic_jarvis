# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Agentic Jarvis** is an enterprise AI assistant built on Google's Agent Development Kit (ADK) that unifies IT operations with learning & development through a multi-agent architecture. The system consists of:

- **Root Orchestrator (Jarvis)**: Routes requests to specialized sub-agents
- **Local Sub-Agents**: Tickets (IT operations) and FinOps (cloud cost analytics)
- **Remote A2A Agent**: Oxygen (learning & development platform)

**Technology Stack:**
- Google ADK v1.0.0+ with A2A Protocol v0.2
- FastAPI for toolbox servers and web endpoints
- Gemini 2.5 Flash model
- JWT/OAuth 2.0 authentication (planned phases)

## Architecture

```
┌─────────────────────────────────────────┐
│     Jarvis (Root Orchestrator)          │
└──────────┬──────────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐   ┌───▼─────┐   ┌──────────┐
│Tickets │   │ FinOps  │   │ Oxygen   │
│Agent   │   │ Agent   │   │ (A2A)    │
└───┬────┘   └───┬─────┘   └────┬─────┘
    │            │               │
┌───▼────┐   ┌──▼──────┐   ┌────▼─────┐
│Toolbox │   │Toolbox  │   │A2A Server│
│:5001   │   │:5002    │   │:8002     │
└────────┘   └─────────┘   └──────────┘
```

## Development Commands

### Starting Services (Phase 1)

Services must be started in separate terminal windows:

```bash
# Terminal 1: Tickets Toolbox Server
./scripts/start_tickets_server.sh

# Terminal 2: FinOps Toolbox Server
./scripts/start_finops_server.sh

# Terminal 3: Oxygen A2A Agent
./scripts/start_oxygen_agent.sh

# Terminal 4: Web UI (if implemented)
./scripts/start_web.sh
```

### Health Checks

```bash
# Verify all services are running
./scripts/check_services.sh

# Check individual ports
lsof -i :5001  # Tickets
lsof -i :5002  # FinOps
lsof -i :8002  # Oxygen A2A
lsof -i :9999  # Web UI

# Test endpoints
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:8002/.well-known/agent-card.json
```

### Service Port Cleanup

If ports are already in use:
```bash
lsof -ti:5001 | xargs kill -9  # Kill Tickets server
lsof -ti:5002 | xargs kill -9  # Kill FinOps server
lsof -ti:8002 | xargs kill -9  # Kill Oxygen agent
```

## Key Implementation Patterns

### Toolbox Server Pattern

Toolbox servers expose Python functions as MCP-compatible tools via FastAPI. Critical implementation details:

1. **Function Schema Generation**: Each Python function's docstring and type hints are converted to tool schemas
2. **Endpoint Structure**:
   - `GET /toolsets` - List available toolsets
   - `GET /toolsets/{name}` - Get specific toolset schema
   - `POST /execute` - Execute tool functions
3. **Port Cleanup**: Always check and kill existing processes before starting servers to avoid "address already in use" errors

### A2A Agent Pattern

The Oxygen agent demonstrates remote agent communication via A2A Protocol:

1. **Agent Card**: Exposed at `/.well-known/agent-card.json` for agent discovery
2. **Port Parameter**: CRITICAL - Always include `port` parameter when calling `to_a2a()`:
   ```python
   a2a_app = to_a2a(root_agent, port=8002)
   ```
3. **Remote Agent Registration**: Use `RemoteA2aAgent` in root orchestrator:
   ```python
   oxygen_agent = RemoteA2aAgent(
       name="oxygen_agent",
       description="Learning platform",
       agent_card=f"http://localhost:8002{AGENT_CARD_WELL_KNOWN_PATH}"
   )
   ```

### Agent Instruction Guidelines

Agents should have clear, specific instructions that:
- Define their domain and responsibilities
- Explain when to delegate to sub-agents
- Provide context on data formatting expectations
- Include examples of typical user queries

## Data Models

### Tickets Schema
```python
{
    "id": int,              # Unique identifier
    "operation": str,       # Operation type (create_ai_key, create_gitlab_account, etc.)
    "user": str,           # Username who created ticket
    "status": str,         # pending | in_progress | completed | rejected
    "created_at": datetime,
    "updated_at": datetime
}
```

### FinOps Schema
```python
{
    "provider": str,        # aws | gcp | azure
    "total_cost": float,
    "services": [
        {"name": str, "cost": float}
    ],
    "period": str
}
```

### Oxygen (Learning) Schema
```python
{
    "username": str,
    "courses_enrolled": [str],
    "pending_exams": [str],
    "completed_courses": [str],
    "preferences": [str],
    "exam_deadlines": {exam_name: datetime}
}
```

## Planned Phases

This project follows a phased implementation approach:

### Phase 1: Core Functionality (Foundation)
- Multi-agent orchestration with local and remote agents
- Toolbox integration for Tickets and FinOps
- A2A communication for Oxygen
- Basic web UI

### Phase 2: JWT Authentication
- Bearer token authentication for user-specific data
- Token passing in A2A calls
- User data access control in Oxygen agent

### Phase 3: Memory & Context Management
- Session memory using ADK's `InMemorySessionService` or `DatabaseSessionService`
- Long-term memory with `VertexAIMemoryBankService`
- Proactive notifications for exam deadlines and incomplete tasks
- Context-aware conversation continuity

### Phase 4: OAuth 2.0 (Enterprise)
- OAuth 2.0 integration (Google, Azure AD, Auth0, Okta)
- SSO support with enterprise identity providers
- Integration Connectors for enterprise systems (100+ supported)
- Secure token exchange between agents

## Environment Configuration

Required environment variables (see `.env.template`):

```bash
# Core
GOOGLE_API_KEY=your_api_key_here

# Service Ports
TICKETS_SERVER_PORT=5001
FINOPS_SERVER_PORT=5002
OXYGEN_AGENT_PORT=8002
WEB_UI_PORT=9999

# Phase 2: JWT (when implemented)
JWT_SECRET_KEY=your_secret_key

# Phase 4: OAuth (when implemented)
OAUTH_PROVIDER=google
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret

# Phase 3: Session/Memory (when implemented)
SESSION_TYPE=memory  # memory | database | redis
DATABASE_URL=sqlite:///./jarvis.db
```

## Important Notes

1. **Port Parameters in A2A**: Always explicitly set the `port` parameter when converting agents to A2A apps. Omitting this can cause binding issues.

2. **Service Startup Order**: Start toolbox servers before the root agent to ensure tools are available when agents initialize.

3. **Sample Data**: All three agents (Tickets, FinOps, Oxygen) use in-memory mock databases. Replace with real data sources in production.

4. **Agent Orchestration**: The root agent (Jarvis) is responsible for routing queries to the appropriate sub-agent based on user intent.

5. **Authentication Phases**: When implementing Phase 2/4, ensure tokens are properly validated and passed through the entire agent chain, especially for A2A calls.

6. **Session Management**: Phase 3 memory implementation should leverage ADK's built-in session services rather than custom solutions.

## Reference Implementation

This project is modeled after the supply chain agent demo located at `/Users/vishalkumar/projects/supply_chain_agent_demo`. Refer to that implementation for working examples of:
- Toolbox server setup with FastAPI
- A2A agent configuration and startup
- Port cleanup scripts
- Agent instruction patterns
