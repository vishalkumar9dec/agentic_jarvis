# Specification Updates for Agent Marketplace

**Purpose**: This document outlines the specific updates needed to existing specification documents to support the Agent Marketplace (remote agent registration).

**Date**: 2025-12-26
**Status**: Ready for implementation

---

## Overview of Changes

The Agent Marketplace introduces **two types of agents**:

1. **Local Agents** (existing): Factory-based, code in repository
2. **Remote Agents** (NEW): Discovered via agent card, hosted by third parties

---

## 1. Updates to AGENT_REGISTRY_PERSISTENCE_SPEC.md

### Section 1.2: Add Marketplace Architecture

**INSERT AFTER "Target State (Persistent)"**:

```markdown
### Target State with Marketplace (Enhanced)

```
┌──────────────────────────────────────────────────────────────┐
│         Agent Registry Service (Marketplace Hub)             │
│                   (Dockerized, Port 8003)                     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────┐      ┌─────────────────────┐       │
│  │  AgentRegistry      │      │  SessionManager     │       │
│  │  - Local Agents  ✅ │      │  (ADK Integration)  │       │
│  │  - Remote Agents ⭐  │      │                     │       │
│  └──────┬──────────────┘      └──────┬──────────────┘       │
│         │                              │                      │
│  ┌──────▼──────────────┐      ┌──────▼──────────────┐       │
│  │  FileStore          │      │  SQLite DB          │       │
│  │  registry_config.json│     │  sessions.db        │       │
│  │  - Local agents     │      │  - Session data     │       │
│  │  - Remote agents ⭐  │      │  - Agent invocations│       │
│  └─────────────────────┘      └─────────────────────┘       │
│                                                               │
└──────────────────────────────────────────────────────────────┘
           ▲                              ▲
           │                              │
           │ REST API (CRUD + Discovery)  │ Session API
           │                              │
┌──────────┴──────────────────────────────┴──────────────┐
│              Jarvis Root Orchestrator                   │
│         (Routes to local AND remote agents)             │
└────────────┬────────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼─────┐    ┌─────▼──────────────────────┐
│ Local   │    │ Remote Agents (Third-Party)│
│ Agents  │    │ - acme_crm_agent           │
│         │    │ - partner_analytics_agent  │
└─────────┘    │ (External infrastructure)  │
               └────────────────────────────┘
```

**Key Enhancement**: Support for remote agents hosted by third parties.
```

---

### Section 3.3: Enhance AgentRegistry Component

**REPLACE "AgentRegistry (Enhanced)" section** with:

```markdown
### 3.3 AgentRegistry (Enhanced with Marketplace Support)

**Purpose**: Core registry logic with persistence AND remote agent support.

```python
# agent_registry_service/registry/agent_registry.py

class PersistentAgentRegistry(AgentRegistry):
    """
    Enhanced AgentRegistry with:
    - File-based persistence
    - Support for TWO agent types: local and remote
    """

    def __init__(self, file_store: FileStore):
        super().__init__()
        self.file_store = file_store
        self.factory_resolver = AgentFactoryResolver()  # ⭐ Handles both types
        self._load_from_file()

    def register_local_agent(
        self,
        factory_module: str,
        factory_function: str,
        capabilities: AgentCapability,
        tags: Optional[Set[str]] = None
    ) -> bool:
        """
        Register a local agent (factory-based).

        Args:
            factory_module: Module path (e.g., "jarvis_agent.mcp_agents.agent_factory")
            factory_function: Function name (e.g., "create_tickets_agent")
            capabilities: AgentCapability object
            tags: Optional tags

        Returns:
            True if registered successfully
        """
        # Create agent from factory
        agent = self.factory_resolver.create_local_agent({
            "factory_module": factory_module,
            "factory_function": factory_function
        })

        # Register with metadata
        self.register(agent, capabilities, tags)

        return True

    def register_remote_agent(
        self,
        agent_card_url: str,
        capabilities: Optional[AgentCapability] = None,
        tags: Optional[Set[str]] = None,
        provider_info: Optional[Dict] = None
    ) -> bool:
        """
        Register a remote agent (third-party).

        Args:
            agent_card_url: URL to agent card (/.well-known/agent-card.json)
            capabilities: AgentCapability (auto-extracted if None)
            tags: Optional tags
            provider_info: Third-party provider information

        Returns:
            True if registered successfully
        """
        # Validate agent card
        agent_card = self._fetch_and_validate_card(agent_card_url)

        # Create RemoteA2aAgent
        agent = self.factory_resolver.create_remote_agent({
            "name": agent_card["agentCard"]["name"],
            "agent_card_url": agent_card_url,
            "description": agent_card["agentCard"].get("description", "")
        })

        # Auto-extract capabilities if not provided
        if not capabilities:
            capabilities = self._extract_capabilities_from_card(agent_card)

        # Register with metadata
        self.register(agent, capabilities, tags)

        # Store provider info
        if provider_info:
            self._store_provider_info(agent.name, provider_info)

        return True

    def _fetch_and_validate_card(self, agent_card_url: str) -> dict:
        """Fetch and validate agent card."""
        # HTTP GET to agent_card_url
        # Validate schema
        # Return agent_card JSON

    def _extract_capabilities_from_card(self, agent_card: dict) -> AgentCapability:
        """Auto-extract capabilities from agent card tools."""
        # Parse tool names/descriptions
        # Infer domains, entities, operations
        # Return AgentCapability
```
```

---

### Section 4: Update File Storage Format

**ADD to Section 4** after existing format:

```markdown
### Enhanced Format: Supporting Local AND Remote Agents

```json
{
  "version": "1.0.0",
  "last_updated": "2025-12-26T10:30:00Z",
  "agents": {

    // ========================================
    // LOCAL AGENTS (Factory-based)
    // ========================================
    "tickets_agent": {
      "name": "tickets_agent",
      "type": "local",  // ⭐ Agent type identifier
      "description": "Handles IT operations tickets",
      "factory_module": "jarvis_agent.mcp_agents.agent_factory",
      "factory_function": "create_tickets_agent",
      "capabilities": {
        "domains": ["tickets", "IT", "operations"],
        "operations": ["create", "read", "update", "list"],
        "entities": ["ticket", "request", "vpn", "gitlab"],
        "keywords": ["ticket", "IT", "operation"],
        "priority": 10
      },
      "tags": ["first-party", "production", "core"],
      "enabled": true,
      "registered_at": "2025-12-26T09:00:00Z"
    },

    // ========================================
    // REMOTE AGENTS (Third-Party) ⭐ NEW
    // ========================================
    "acme_crm_agent": {
      "name": "acme_crm_agent",
      "type": "remote",  // ⭐ Remote agent
      "description": "Access Acme CRM data - customers, deals, pipelines",
      "agent_card_url": "https://acme-agent.example.com:8080/.well-known/agent-card.json",
      "capabilities": {
        "domains": ["crm", "sales", "customers"],
        "operations": ["read", "search", "analyze"],
        "entities": ["customer", "deal", "pipeline", "contact"],
        "keywords": ["crm", "sales", "customer"],
        "priority": 5
      },
      "tags": ["third-party", "crm", "verified"],
      "enabled": true,
      "registered_at": "2025-12-26T10:30:00Z",

      // Third-party specific metadata
      "provider": {
        "name": "Acme Corp",
        "website": "https://acme.com",
        "support_email": "support@acme.com",
        "documentation": "https://acme.com/docs/agent"
      },
      "auth_config": {
        "type": "bearer",
        "token_endpoint": "https://acme-agent.example.com/auth/token",
        "scopes": ["read:customers", "read:deals"]
      },
      "status": "approved",  // pending | approved | suspended
      "approved_at": "2025-12-26T11:00:00Z",
      "approved_by": "admin@yourplatform.com"
    }
  },

  "statistics": {
    "total_agents": 2,
    "local_agents": 1,
    "remote_agents": 1,
    "enabled_agents": 2
  }
}
```

**Key Differences**:
- `type` field: "local" vs "remote"
- Local agents: Have `factory_module` + `factory_function`
- Remote agents: Have `agent_card_url` + `provider` + `auth_config`
- Remote agents: Have approval workflow (`status`, `approved_at`)
```

---

### Section 6: Add Marketplace API Endpoints

**ADD NEW Section 6.3**:

```markdown
### 6.3 Marketplace API Endpoints ⭐ NEW

#### Register Remote Agent

```http
POST /registry/agents/remote
Authorization: Bearer {developer_api_key}
Content-Type: application/json

Body:
{
  "agent_card_url": "https://third-party-agent.com/.well-known/agent-card.json",
  "capabilities": {
    "domains": ["crm", "sales"],
    "operations": ["read", "search"],
    "entities": ["customer", "deal"],
    "priority": 5
  },
  "tags": ["third-party", "crm"],
  "provider": {
    "name": "Acme Corp",
    "website": "https://acme.com",
    "support_email": "support@acme.com"
  },
  "auth_config": {
    "type": "bearer",
    "token_endpoint": "https://third-party-agent.com/auth/token"
  }
}

Response (201 Created):
{
  "status": "pending_approval",
  "agent_name": "acme_crm_agent",
  "registration_id": "reg_abc123",
  "submitted_at": "2025-12-26T10:00:00Z",
  "message": "Agent registered. Pending admin approval."
}
```

#### Discover Agent from Card

```http
POST /registry/agents/discover
Content-Type: application/json

Body:
{
  "agent_card_url": "https://third-party-agent.com/.well-known/agent-card.json"
}

Response (200 OK):
{
  "agent_card": {
    "name": "acme_crm_agent",
    "description": "...",
    "capabilities": {...}
  },
  "suggested_capabilities": {
    "domains": ["crm", "sales"],  // Auto-extracted
    "entities": ["customer", "deal"]
  },
  "validation": {
    "passed": true,
    "checks": {
      "card_accessible": true,
      "schema_valid": true,
      "endpoints_reachable": true,
      "https_enabled": true
    }
  }
}
```

#### Approve/Reject Agent (Admin Only)

```http
PATCH /registry/agents/{agent_name}/approval
Authorization: Bearer {admin_token}

Body:
{
  "status": "approved",  // or "rejected"
  "reviewer_notes": "All checks passed. Approved for production."
}

Response (200 OK):
{
  "status": "approved",
  "agent_name": "acme_crm_agent",
  "approved_at": "2025-12-26T11:00:00Z",
  "approved_by": "admin@yourplatform.com"
}
```

#### List Marketplace Agents

```http
GET /registry/agents?type=remote&status=approved

Response (200 OK):
{
  "agents": [
    {
      "name": "acme_crm_agent",
      "type": "remote",
      "description": "...",
      "provider": "Acme Corp",
      "status": "approved",
      "tags": ["third-party", "crm"]
    }
  ],
  "total": 1,
  "filters": {
    "type": "remote",
    "status": "approved"
  }
}
```
```

---

### Section 8: Add Marketplace Implementation Tasks

**ADD NEW Phase: "Phase 6: Marketplace Support"**:

```markdown
## Phase 6: Marketplace Support (Priority 2) ⭐ NEW

### Task 6.1: Agent Factory Resolver Enhancement

**File**: `agent_registry_service/registry/agent_factory_resolver.py`
**Effort**: 4-6 hours
**Dependencies**: Task 1.2

```python
# Enhance to support BOTH local and remote agents

class AgentFactoryResolver:
    """Resolves both local (factory) and remote (agent card) agents."""

    def create_agent(self, config: Dict) -> LlmAgent:
        """
        Create agent based on type.

        Args:
            config: {
                "type": "local" | "remote",
                "factory_module": "..." (if local),
                "factory_function": "..." (if local),
                "agent_card_url": "..." (if remote),
                "name": "..." (if remote)
            }
        """
        agent_type = config.get("type", "local")

        if agent_type == "local":
            return self._create_local_agent(config)
        elif agent_type == "remote":
            return self._create_remote_agent(config)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    def _create_local_agent(self, config: Dict) -> LlmAgent:
        """Create local agent from factory."""
        # Existing implementation

    def _create_remote_agent(self, config: Dict) -> RemoteA2aAgent:
        """Create remote agent from agent card URL."""
        from google.adk.agents import RemoteA2aAgent

        return RemoteA2aAgent(
            name=config["name"],
            description=config.get("description", ""),
            agent_card=config["agent_card_url"]
        )
```

---

### Task 6.2: Agent Card Validation

**File**: `agent_registry_service/registry/agent_card_validator.py`
**Effort**: 6-8 hours
**Dependencies**: None

```python
# Implement agent card validation

class AgentCardValidator:
    """Validates third-party agent cards before registration."""

    async def validate(self, agent_card_url: str) -> dict:
        """
        Validate agent card.

        Returns:
            {
                "valid": True/False,
                "checks": {...},
                "errors": [...]
            }
        """

    async def _check_accessibility(self, url: str) -> bool:
        """Check if agent card is accessible."""

    def _check_schema(self, agent_card: dict) -> bool:
        """Validate against A2A schema."""

    def _detect_malicious_patterns(self, agent_card: dict) -> bool:
        """Detect suspicious tool names/descriptions."""

    async def _check_endpoints(self, agent_card: dict) -> bool:
        """Verify invoke/stream endpoints are reachable."""
```

---

### Task 6.3: Marketplace API Endpoints

**File**: `agent_registry_service/api/marketplace_routes.py`
**Effort**: 8-10 hours
**Dependencies**: Task 6.1, 6.2

```python
# Implement marketplace-specific endpoints

@router.post("/registry/agents/remote")
async def register_remote_agent(request: RemoteAgentRegistration):
    """Register third-party remote agent."""

@router.post("/registry/agents/discover")
async def discover_agent(request: AgentDiscoveryRequest):
    """Discover and validate agent from card URL."""

@router.patch("/registry/agents/{agent_name}/approval")
async def approve_reject_agent(agent_name: str, approval: ApprovalRequest):
    """Approve or reject pending agent (admin only)."""

@router.get("/registry/agents")
async def list_agents(type: Optional[str] = None, status: Optional[str] = None):
    """List agents with filters (type, status, tags)."""
```

---

### Task 6.4: Capability Auto-Extraction

**File**: `agent_registry_service/registry/capability_extractor.py`
**Effort**: 4-6 hours
**Dependencies**: None

```python
# Auto-extract capabilities from agent card

def extract_capabilities_from_card(agent_card: dict) -> AgentCapability:
    """
    Extract capabilities from agent card.

    Analyzes:
    - Agent name and description → domains
    - Tool names → entities and operations
    - Tool descriptions → keywords
    """
```
```

---

## 2. Updates to AGENT_REGISTRY_IMPLEMENTATION_TASKS.md

### Add New Task Section: "Phase 6: Marketplace Support"

**INSERT AFTER Phase 5**:

```markdown
## Phase 6: Marketplace Support (Days 6-7) ⭐ NEW

### Task 6.1: Enhance Agent Factory Resolver for Remote Agents

**Prompt for Claude:**
```
I need to enhance the AgentFactoryResolver to support remote agents in addition to local agents.

Current functionality:
- Creates local agents from factory functions

New requirement:
- Support TWO agent types: "local" and "remote"
- For local agents: Use existing factory pattern
- For remote agents: Create RemoteA2aAgent from agent card URL

Requirements:
1. Update agent_registry_service/registry/agent_factory_resolver.py
2. Add type detection: config.get("type", "local")
3. Implement _create_remote_agent() method:
   ```python
   def _create_remote_agent(self, config: Dict) -> RemoteA2aAgent:
       from google.adk.agents import RemoteA2aAgent

       return RemoteA2aAgent(
           name=config["name"],
           description=config.get("description", ""),
           agent_card=config["agent_card_url"]
       )
   ```

4. Update create_agent() to route based on type
5. Add validation for required fields per type
6. Write tests for both local and remote agent creation

Let's implement this enhancement.
```

**Acceptance Criteria:**
- [ ] Supports both agent types
- [ ] Remote agents created correctly
- [ ] Tests pass for both types
- [ ] Error handling comprehensive

---

### Task 6.2: Implement Agent Card Validation

**Prompt for Claude:**
```
I need to implement agent card validation for third-party agents.

Requirements:
1. Create agent_registry_service/registry/agent_card_validator.py
2. Implement AgentCardValidator class with:
   - validate(agent_card_url: str) -> dict
   - _check_accessibility(): Fetch agent card via HTTP
   - _check_schema(): Validate against A2A protocol spec
   - _detect_malicious_patterns(): Scan for suspicious capabilities
   - _check_endpoints(): Verify invoke/stream endpoints work
   - _require_https(): Ensure HTTPS in production

3. Validation checks:
   ✅ Agent card is accessible (HTTP 200)
   ✅ HTTPS required (not HTTP) for production
   ✅ Valid JSON schema (A2A compliant)
   ✅ Required fields present (name, description, capabilities, endpoints)
   ✅ Endpoints are reachable (/invoke, /stream)
   ✅ No malicious patterns (e.g., "delete_database", "exec", "eval")
   ✅ Tools are properly documented (description + inputSchema)

4. Return validation result:
   {
     "valid": True/False,
     "checks": {
       "card_accessible": True,
       "https_enabled": True,
       "schema_valid": True,
       "endpoints_reachable": True,
       "no_malicious_patterns": True
     },
     "errors": ["list of errors if any"]
   }

5. Write comprehensive tests

Let's implement secure agent card validation.
```

**Acceptance Criteria:**
- [ ] All validation checks implemented
- [ ] Malicious pattern detection working
- [ ] HTTPS enforcement in production
- [ ] Tests cover edge cases

---

### Task 6.3: Implement Marketplace API Endpoints

**Prompt for Claude:**
```
I need to implement REST API endpoints for the agent marketplace.

Requirements:
1. Create agent_registry_service/api/marketplace_routes.py
2. Implement endpoints:

   POST /registry/agents/remote
   - Register third-party remote agent
   - Validate agent card
   - Extract or use provided capabilities
   - Set status to "pending_approval"
   - Return registration_id

   POST /registry/agents/discover
   - Fetch agent card from URL
   - Validate card
   - Auto-extract suggested capabilities
   - Return agent card + validation results

   PATCH /registry/agents/{agent_name}/approval
   - Admin-only endpoint (require admin token)
   - Approve or reject pending agent
   - Update status and timestamps

   GET /registry/agents
   - List agents with filters:
     - type (local, remote, all)
     - status (pending, approved, suspended)
     - tags (comma-separated)

3. Use Pydantic models for request/response validation
4. Integrate with AgentCardValidator
5. Add authentication/authorization checks
6. Write API tests using TestClient

Let's implement the marketplace API.
```

**Acceptance Criteria:**
- [ ] All endpoints implemented
- [ ] Validation working
- [ ] Admin authorization enforced
- [ ] API tests pass

---

### Task 6.4: Implement Capability Auto-Extraction

**Prompt for Claude:**
```
I need to implement automatic capability extraction from agent cards.

Requirements:
1. Create agent_registry_service/registry/capability_extractor.py
2. Implement extract_capabilities_from_card(agent_card: dict) -> AgentCapability
3. Extraction logic:

   Domains:
   - From agent name: "acme_crm_agent" → "crm"
   - From description: keywords like "CRM", "sales", "analytics"

   Entities:
   - From tool names: "get_customer" → "customer", "list_deals" → "deal"
   - Common patterns: get_X, create_X, list_X → extract X

   Operations:
   - From tool verbs: "get_" → "read", "create_" → "create", "list_" → "list"

   Keywords:
   - From description (words > 4 chars)
   - From tool descriptions

4. Return AgentCapability with auto-extracted values
5. Allow user override (manual capabilities take precedence)
6. Write tests with sample agent cards

Let's implement smart capability extraction.
```

**Acceptance Criteria:**
- [ ] Extracts domains accurately
- [ ] Extracts entities from tool names
- [ ] Extracts operations from verbs
- [ ] Manual override works
- [ ] Tests with real agent cards

```

---

## 3. Updates to AGENT_REGISTRY_CALL_FLOW.md

### Add New Section: "Remote Agent Flows"

**INSERT as new Section 9**:

```markdown
## 9. Remote Agent Registration & Invocation Flows

### 9.1 Third-Party Agent Registration

```
┌─────────────────────────────────────────────────────────────────┐
│ Third-Party Developer: Acme Corp                                │
└─────────────────────────────────────────────────────────────────┘

Step 1: Build and deploy agent
  ├─ Create LlmAgent with tools
  ├─ Expose via to_a2a(agent, port=8080)
  └─ Deploy to https://acme-agent.example.com:8080

Step 2: Verify agent card
  ├─ curl https://acme-agent.example.com/.well-known/agent-card.json
  └─ ✅ Agent card accessible

Step 3: Register with marketplace
  ├─ POST https://jarvis-marketplace.com/registry/agents/remote
  │   {
  │     "agent_card_url": "https://acme-agent.example.com/.well-known/agent-card.json",
  │     "capabilities": {...},
  │     "provider": {"name": "Acme Corp", ...}
  │   }
  │
  └─ Response: {"status": "pending_approval", "registration_id": "reg_123"}

┌─────────────────────────────────────────────────────────────────┐
│ Platform Admin Review                                           │
└─────────────────────────────────────────────────────────────────┘

Step 4: Admin reviews
  ├─ GET /registry/agents/acme_crm_agent
  ├─ Review agent card
  ├─ Check validation results
  ├─ Verify provider information
  └─ Decision: Approve

Step 5: Admin approves
  ├─ PATCH /registry/agents/acme_crm_agent/approval
  │   {"status": "approved"}
  │
  └─ Agent status → "approved"
      Agent goes live in marketplace

┌─────────────────────────────────────────────────────────────────┐
│ Agent Now Available for Discovery                               │
└─────────────────────────────────────────────────────────────────┘
```

---

### 9.2 Query Routing with Remote Agent

```
User Query: "Show me customer ABC-123 from Acme CRM"

┌──────────────────────────────────────────────────────────────┐
│ Stage 1: Fast Filter                                         │
└──────────────────────────────────────────────────────────────┘
  │
  ├─ GET /registry/agents
  │   Returns: [tickets_agent (local), acme_crm_agent (remote), finops_agent (local)]
  │
  ├─ Calculate match scores:
  │   acme_crm_agent:
  │     - "customer" in query → entity match +0.3
  │     - "Acme CRM" in query → domain match +0.4
  │     - Total score: 0.7
  │
  │   tickets_agent: score 0.1
  │   finops_agent: score 0.0
  │
  └─ Candidates: [acme_crm_agent(0.7), tickets_agent(0.1)]

┌──────────────────────────────────────────────────────────────┐
│ Stage 2: LLM Selection                                       │
└──────────────────────────────────────────────────────────────┘
  │
  ├─ LLM prompt includes:
  │   Candidate 0: acme_crm_agent (remote) - "Access Acme CRM data"
  │   Candidate 1: tickets_agent (local) - "IT operations tickets"
  │
  ├─ LLM analyzes:
  │   "User wants customer data from Acme CRM"
  │   "Select acme_crm_agent"
  │
  └─ Selected: [acme_crm_agent]

┌──────────────────────────────────────────────────────────────┐
│ Invocation: Remote Agent                                     │
└──────────────────────────────────────────────────────────────┘
  │
  ├─ Jarvis invokes:
  │   response = await acme_crm_agent.run(
  │       query="Show me customer ABC-123",
  │       context={
  │           "auth": {
  │               "type": "bearer",
  │               "token": get_secret("ACME_CRM_API_KEY")
  │           }
  │       }
  │   )
  │
  ├─ Under the hood (ADK A2A):
  │   POST https://acme-agent.example.com:8080/invoke
  │   Authorization: Bearer abc123...
  │   Body: {"query": "Show me customer ABC-123", ...}
  │
  ├─ Acme's agent processes request
  │
  └─ Response: {
        "result": "Customer ABC-123: Acme Industries, Status: Active, ..."
      }

┌──────────────────────────────────────────────────────────────┐
│ Response to User                                             │
└──────────────────────────────────────────────────────────────┘
  │
  └─ "Customer ABC-123: Acme Industries
      Status: Active
      Contact: john@acme.com
      Deals: 2 active deals ($500K total)
      ..."
```

---

### 9.3 Multi-Agent Query (Local + Remote)

```
User Query: "Show customer ABC-123 from Acme and my IT tickets"

Stage 1: Fast Filter
  ├─ acme_crm_agent (remote): score 0.7
  └─ tickets_agent (local): score 0.6

Stage 2: LLM Selection
  └─ Selected: [acme_crm_agent, tickets_agent]

Invocation: PARALLEL
  ├─ Thread 1: acme_crm_agent.run(...)
  │   → HTTP call to https://acme-agent.example.com
  │   → Response: "Customer ABC-123: ..."
  │
  └─ Thread 2: tickets_agent.run(...)
      → Direct local call
      → Response: "You have 3 open tickets: ..."

Combined Response:
  **Acme CRM - Customer ABC-123:**
  [Remote agent response]

  **IT Tickets:**
  [Local agent response]
```
```

---

## 4. New Documentation Created

✅ **AGENT_MARKETPLACE.md** - Comprehensive marketplace guide

**Covers**:
- Marketplace architecture
- Third-party developer guide
- Agent card specification
- Registration methods
- Authentication models
- API reference
- Security considerations
- Implementation roadmap

---

## 5. Summary of Changes

### What's Enhanced

1. **Agent Registry**: Supports local AND remote agents
2. **File Format**: Stores both types with different schemas
3. **Factory Resolver**: Creates RemoteA2aAgent for remote agents
4. **API**: New endpoints for remote registration and discovery
5. **Validation**: Agent card validation for security
6. **Documentation**: Complete marketplace guide

### New Components

- `AgentCardValidator` - Validates third-party agent cards
- `CapabilityExtractor` - Auto-extracts capabilities from cards
- `marketplace_routes.py` - Marketplace-specific API endpoints
- Approval workflow (pending → approved → live)

### Agent Types

| Type | Storage | Creation | Example |
|------|---------|----------|---------|
| **local** | Factory reference | Call factory function | tickets_agent, finops_agent |
| **remote** | Agent card URL | RemoteA2aAgent(card_url) | acme_crm_agent, partner_agent |

---

## 6. Implementation Priority

**High Priority** (Must Have):
1. ✅ Task 6.1: Agent Factory Resolver enhancement
2. ✅ Task 6.2: Agent Card Validation
3. ✅ Task 6.3: Marketplace API endpoints

**Medium Priority** (Should Have):
4. Task 6.4: Capability auto-extraction
5. Admin approval workflow
6. Agent health monitoring

**Low Priority** (Nice to Have):
7. Developer portal UI
8. Usage analytics
9. Monetization features

---

## Next Steps

1. **Review** this update summary
2. **Approve** the marketplace design
3. **Implement** Phase 6 tasks (6.1 → 6.4)
4. **Test** remote agent registration and invocation
5. **Deploy** marketplace-enabled registry

---

**Status**: 🟡 Ready for Review & Approval
**Estimated Effort**: +2-3 days (Phase 6)
**Total Timeline**: 8-12 days (including original 6-9 days)

---

**Questions or concerns? Let's discuss before implementation!** 🚀
