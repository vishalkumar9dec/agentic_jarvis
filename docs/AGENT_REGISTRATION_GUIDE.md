# Agent Registration Guide

**Complete guide to registering agents with the Jarvis Agent Registry Service**

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Agent Types](#agent-types)
5. [Registration Methods](#registration-methods)
6. [Step-by-Step Tutorials](#step-by-step-tutorials)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

The Agent Registry Service provides a centralized platform for registering and managing AI agents. It supports two types of agents:

- **Local Agents (First-Party)**: Agents you own and operate, hosted on your infrastructure
- **Remote Agents (Third-Party)**: Agents hosted externally, accessible via A2A protocol

### Benefits

✅ **Centralized Management**: Single registry for all your agents
✅ **Dynamic Discovery**: Automatically route requests to the right agent
✅ **Capability Matching**: Intelligent agent selection based on user queries
✅ **Marketplace Ready**: Support for third-party agent integration
✅ **Approval Workflow**: Control which agents are active in your system

---

## Prerequisites

### Required Services

1. **Agent Registry Service** must be running:
   ```bash
   ./scripts/start_registry_service.sh
   ```

2. **For Remote Agents**: The remote agent must be running and accessible:
   ```bash
   ./scripts/start_oxygen_agent.sh  # Example for Oxygen agent
   ```

### Required Python Packages

```bash
# If using the helper script
pip install requests

# If using the API directly
pip install httpx  # or requests
```

---

## Quick Start

### Using the Helper Script (Recommended)

The easiest way to register agents is using our helper script:

```bash
# Register all agents (local + remote)
python scripts/register_agents.py --all

# Register only local agents
python scripts/register_agents.py --local

# Register only remote agents
python scripts/register_agents.py --remote

# Register a specific agent
python scripts/register_agents.py --agent oxygen_agent

# List all registered agents
python scripts/register_agents.py --list
```

### Expected Output

```
================================================================================
Registering All Agents
================================================================================

Local Agents (First-Party):
  Registering local agent: tickets_agent... ✓ SUCCESS
  Registering local agent: finops_agent... ✓ SUCCESS

  Summary: 2/2 local agents registered

Remote Agents (Third-Party):
  Registering remote agent: oxygen_agent... ✓ SUCCESS (status: pending)

  Summary: 1/1 remote agents registered

================================================================================
Registration Complete: 3/3 agents registered successfully
================================================================================
```

---

## Agent Types

### Type 1: Local Agents (First-Party)

**What are they?**
- Agents you build and host on your infrastructure
- Code is in your repository
- Created via factory functions

**Examples:**
- `tickets_agent` - IT support ticket management
- `finops_agent` - Cloud cost analytics

**When to use:**
- Internal agents you fully control
- Agents with access to your internal systems
- Agents that require your proprietary code

### Type 2: Remote Agents (Third-Party)

**What are they?**
- Agents hosted externally by third parties
- Communicate via A2A protocol
- No code in your repository

**Examples:**
- `oxygen_agent` - Learning & development platform
- External CRM agents
- Partner analytics agents

**When to use:**
- Integrating with external services
- Marketplace agents from third-party developers
- SaaS agent integrations

---

## Registration Methods

### Method 1: Helper Script (Easiest)

**Pros:** Simple, handles errors, validates configuration
**Cons:** Requires predefined configuration in script

```bash
python scripts/register_agents.py --all
```

### Method 2: curl (Manual)

**Pros:** Direct control, scriptable
**Cons:** More verbose, manual error handling

```bash
curl -X POST http://localhost:8003/registry/agents/remote \
  -H "Content-Type: application/json" \
  -d @agent_config.json
```

### Method 3: Python Code

**Pros:** Programmatic integration, custom logic
**Cons:** Requires writing code

```python
import requests

response = requests.post(
    "http://localhost:8003/registry/agents/remote",
    json={...}
)
```

### Method 4: API Docs (Testing)

**Pros:** Interactive, great for testing
**Cons:** Not suitable for automation

Visit: `http://localhost:8003/docs`

---

## Step-by-Step Tutorials

### Tutorial 1: Register a Local Agent

**Scenario:** You have a new local agent for handling HR requests.

#### Step 1: Define Agent Configuration

Create a file `hr_agent_config.json`:

```json
{
  "agent_config": {
    "agent_type": "hr",
    "factory_module": "jarvis_agent.mcp_agents.agent_factory",
    "factory_function": "create_hr_agent",
    "factory_params": {}
  },
  "capabilities": {
    "domains": ["hr", "human resources", "employee"],
    "operations": ["read", "search", "request"],
    "entities": ["employee", "leave", "payslip", "policy"],
    "keywords": ["leave", "payslip", "hr", "employee", "policy"],
    "examples": [
      "Request annual leave",
      "Download my payslip",
      "What is the WFH policy?"
    ],
    "priority": 8
  },
  "tags": ["first-party", "production", "hr"]
}
```

#### Step 2: Register the Agent

```bash
curl -X POST http://localhost:8003/registry/agents \
  -H "Content-Type: application/json" \
  -d @hr_agent_config.json
```

#### Step 3: Verify Registration

```bash
curl http://localhost:8003/registry/agents/hr_agent
```

#### Expected Response

```json
{
  "name": "hr_agent",
  "description": "Handles HR and employee requests",
  "agent_type": "hr",
  "type": "local",
  "enabled": true,
  "tags": ["first-party", "production", "hr"],
  "capabilities": {
    "domains": ["hr", "human resources"],
    ...
  },
  "factory_module": "jarvis_agent.mcp_agents.agent_factory",
  "factory_function": "create_hr_agent"
}
```

---

### Tutorial 2: Register a Remote Agent (Third-Party)

**Scenario:** You want to integrate an external CRM agent from Acme Corp.

#### Step 1: Verify Agent Card is Accessible

```bash
# Check if the agent card is reachable
curl https://acme-crm-agent.example.com/.well-known/agent-card.json
```

Expected response:
```json
{
  "agentCard": {
    "name": "acme_crm_agent",
    "description": "Access Acme CRM data - customers, deals, pipelines",
    "version": "1.0.0",
    "supportedProtocols": ["a2a"],
    ...
  }
}
```

#### Step 2: Create Registration Request

Create `acme_crm_registration.json`:

```json
{
  "agent_card_url": "https://acme-crm-agent.example.com/.well-known/agent-card.json",
  "capabilities": {
    "domains": ["crm", "sales", "customers"],
    "operations": ["read", "search", "analyze"],
    "entities": ["customer", "deal", "pipeline", "contact"],
    "keywords": ["crm", "customer", "deal", "sales", "pipeline"],
    "examples": [
      "Show customer ABC-123",
      "List all active deals",
      "What's in the sales pipeline?"
    ],
    "priority": 5
  },
  "tags": ["third-party", "crm", "sales", "verified"],
  "provider": {
    "name": "Acme Corp",
    "website": "https://acme.com",
    "support_email": "support@acme.com",
    "documentation": "https://acme.com/docs/agent"
  },
  "auth_config": {
    "type": "bearer",
    "token_endpoint": "https://acme-crm-agent.example.com/auth/token",
    "scopes": ["read:customers", "read:deals"]
  }
}
```

#### Step 3: Register the Agent

```bash
curl -X POST http://localhost:8003/registry/agents/remote \
  -H "Content-Type: application/json" \
  -d @acme_crm_registration.json
```

#### Step 4: Verify Registration

```bash
curl http://localhost:8003/registry/agents/acme_crm_agent
```

#### Expected Response

```json
{
  "status": "pending_approval",
  "message": "Remote agent 'acme_crm_agent' registered successfully. Pending marketplace approval.",
  "data": {
    "agent_name": "acme_crm_agent",
    "status": "pending",
    "provider": "Acme Corp"
  }
}
```

---

### Tutorial 3: Register Oxygen Agent (Built-in Example)

**Scenario:** Register the Oxygen learning platform agent.

#### Step 1: Start Oxygen Agent

```bash
./scripts/start_oxygen_agent.sh
```

Wait for:
```
✅ Oxygen Agent running at http://0.0.0.0:8002
📋 Agent card: http://0.0.0.0:8002/.well-known/agent-card.json
```

#### Step 2: Register Using Helper Script

```bash
python scripts/register_agents.py --agent oxygen_agent
```

#### Step 3: Verify Registration

```bash
python scripts/register_agents.py --list
```

Expected output:
```
================================================================================
Registered Agents (1 total)
================================================================================

✓ oxygen_agent (remote)
  Description: Learning & development platform
  Domains: learning, education, courses, training
  Tags: remote, a2a, learning, education
  Agent Card: http://localhost:8002/.well-known/agent-card.json
  Status: pending
  Provider: Oxygen Learning Platform
```

---

## API Reference

### Endpoints

#### 1. Register Local Agent

**Endpoint:** `POST /registry/agents`

**Request Body:**
```json
{
  "agent_config": {
    "agent_type": "string",
    "factory_module": "string",
    "factory_function": "string",
    "factory_params": {}
  },
  "capabilities": {
    "domains": ["string"],
    "operations": ["string"],
    "entities": ["string"],
    "keywords": ["string"],
    "examples": ["string"],
    "priority": 0
  },
  "tags": ["string"]
}
```

**Response (201 Created):**
```json
{
  "status": "registered",
  "message": "Agent 'agent_name' registered successfully",
  "data": {
    "agent_name": "string"
  }
}
```

---

#### 2. Register Remote Agent

**Endpoint:** `POST /registry/agents/remote`

**Request Body:**
```json
{
  "agent_card_url": "string",
  "capabilities": {
    "domains": ["string"],
    "operations": ["string"],
    "entities": ["string"],
    "keywords": ["string"],
    "examples": ["string"],
    "priority": 0
  },
  "tags": ["string"],
  "provider": {
    "name": "string",
    "website": "string",
    "support_email": "string",
    "documentation": "string"
  },
  "auth_config": {
    "type": "bearer | api_key | oauth2 | none",
    "token_endpoint": "string",
    "scopes": ["string"]
  }
}
```

**Response (201 Created):**
```json
{
  "status": "pending_approval",
  "message": "Remote agent 'agent_name' registered successfully. Pending marketplace approval.",
  "data": {
    "agent_name": "string",
    "status": "pending",
    "provider": "string"
  }
}
```

---

#### 3. List Agents

**Endpoint:** `GET /registry/agents`

**Query Parameters:**
- `enabled_only` (boolean): Only return enabled agents
- `tags` (string): Comma-separated tags to filter by

**Response (200 OK):**
```json
{
  "agents": [
    {
      "name": "string",
      "description": "string",
      "agent_type": "string",
      "type": "local | remote",
      "enabled": true,
      "tags": ["string"],
      "capabilities": {...}
    }
  ],
  "total": 0
}
```

---

#### 4. Get Agent Details

**Endpoint:** `GET /registry/agents/{agent_name}`

**Response (200 OK):**
```json
{
  "name": "string",
  "description": "string",
  "agent_type": "string",
  "type": "local | remote",
  "enabled": true,
  "tags": ["string"],
  "capabilities": {...},

  // Local agents only:
  "factory_module": "string",
  "factory_function": "string",

  // Remote agents only:
  "agent_card_url": "string",
  "provider": {...},
  "status": "pending | approved | suspended"
}
```

---

## Troubleshooting

### Issue 1: "Registry service not available"

**Problem:**
```
Error: Registry service not available at http://localhost:8003
```

**Solution:**
```bash
# Start the registry service
./scripts/start_registry_service.sh

# Verify it's running
curl http://localhost:8003/health
```

---

### Issue 2: "Cannot reach agent card URL"

**Problem:**
```
Error: Cannot reach agent card URL
```

**Solutions:**

1. **Check if agent is running:**
   ```bash
   # For Oxygen agent
   lsof -i :8002

   # If not running, start it
   ./scripts/start_oxygen_agent.sh
   ```

2. **Verify agent card is accessible:**
   ```bash
   curl http://localhost:8002/.well-known/agent-card.json
   ```

3. **Check firewall settings:**
   - Ensure port is not blocked
   - For remote agents, ensure HTTPS is configured

---

### Issue 3: "Agent already registered"

**Problem:**
```
Error: Agent already registered
```

**Solution:**

Option 1 - Delete and re-register:
```bash
# Delete existing agent
curl -X DELETE http://localhost:8003/registry/agents/agent_name

# Re-register
python scripts/register_agents.py --agent agent_name
```

Option 2 - Update capabilities instead:
```bash
curl -X PUT http://localhost:8003/registry/agents/agent_name/capabilities \
  -H "Content-Type: application/json" \
  -d '{"capabilities": {...}}'
```

---

### Issue 4: "Invalid agent card format"

**Problem:**
```
Error: Invalid agent card structure
```

**Solution:**

Verify agent card has required fields:
```json
{
  "agentCard": {
    "name": "required",
    "description": "required",
    "version": "optional",
    "supportedProtocols": ["a2a"],
    "capabilities": {...},
    "endpoints": {...}
  }
}
```

---

### Issue 5: "Factory module not found"

**Problem:**
```
Error: Failed to create agent: No module named 'jarvis_agent.mcp_agents.agent_factory'
```

**Solution:**

1. **Verify module exists:**
   ```bash
   ls jarvis_agent/mcp_agents/agent_factory.py
   ```

2. **Check factory function exists:**
   ```python
   # In jarvis_agent/mcp_agents/agent_factory.py
   def create_tickets_agent():
       ...
   ```

3. **Ensure PYTHONPATH is set:**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/agentic_jarvis"
   ```

---

## Best Practices

### 1. Capability Definition

**DO:**
```json
{
  "domains": ["tickets", "IT", "support"],
  "operations": ["create", "read", "update", "delete"],
  "entities": ["ticket", "vpn_access"],
  "keywords": ["ticket", "vpn", "create", "show"],
  "examples": [
    "Show my tickets",
    "Create a VPN ticket"
  ],
  "priority": 10
}
```

**DON'T:**
```json
{
  "domains": ["everything"],
  "operations": ["do_stuff"],
  "entities": [],
  "keywords": [],
  "examples": [],
  "priority": 0
}
```

### 2. Agent Naming

**DO:**
- Use descriptive names: `tickets_agent`, `finops_agent`, `acme_crm_agent`
- Use snake_case
- Keep it concise

**DON'T:**
- Generic names: `agent1`, `test_agent`
- Special characters: `agent-name`, `agent.name`
- Too long: `customer_relationship_management_agent_for_sales`

### 3. Tags

**DO:**
```json
{
  "tags": ["first-party", "production", "it-ops", "critical"]
}
```

**DON'T:**
```json
{
  "tags": ["tag1", "tag2", "misc"]
}
```

### 4. Priority

**Guidelines:**
- **10**: Critical system agents (tickets, auth)
- **8**: Important business agents (finops, hr)
- **5**: Integration agents (third-party CRM)
- **3**: Nice-to-have agents (analytics)
- **0**: Experimental/test agents

### 5. Remote Agent Security

**For Production:**
1. ✅ Always use HTTPS for agent card URLs
2. ✅ Validate agent cards before registration
3. ✅ Use authentication (bearer tokens, OAuth)
4. ✅ Set appropriate scopes
5. ✅ Monitor agent health and performance

**Example:**
```json
{
  "agent_card_url": "https://verified-agent.com/.well-known/agent-card.json",
  "auth_config": {
    "type": "bearer",
    "token_endpoint": "https://verified-agent.com/auth/token",
    "scopes": ["read:limited"]
  }
}
```

---

## Complete Examples

### Example 1: Full Workflow - Local Agent

```bash
# 1. Start registry service
./scripts/start_registry_service.sh

# 2. Create agent configuration
cat > new_agent.json <<EOF
{
  "agent_config": {
    "agent_type": "analytics",
    "factory_module": "jarvis_agent.mcp_agents.agent_factory",
    "factory_function": "create_analytics_agent"
  },
  "capabilities": {
    "domains": ["analytics", "reporting"],
    "operations": ["read", "analyze", "report"],
    "entities": ["report", "dashboard", "metric"],
    "keywords": ["analytics", "report", "dashboard"],
    "examples": ["Show analytics dashboard"],
    "priority": 7
  },
  "tags": ["first-party", "analytics"]
}
EOF

# 3. Register agent
curl -X POST http://localhost:8003/registry/agents \
  -H "Content-Type: application/json" \
  -d @new_agent.json

# 4. Verify registration
curl http://localhost:8003/registry/agents/analytics_agent

# 5. List all agents
curl http://localhost:8003/registry/agents
```

---

### Example 2: Full Workflow - Remote Agent

```bash
# 1. Start registry service
./scripts/start_registry_service.sh

# 2. Start your remote agent
./scripts/start_my_remote_agent.sh

# 3. Verify agent card
curl http://localhost:9000/.well-known/agent-card.json

# 4. Register using helper script
python scripts/register_agents.py --agent my_remote_agent

# 5. List agents to verify
python scripts/register_agents.py --list
```

---

## Next Steps

- **API Documentation**: Visit `http://localhost:8003/docs` for interactive API docs
- **Marketplace Guide**: See [AGENT_MARKETPLACE.md](AGENT_MARKETPLACE.md) for marketplace features
- **Development**: See [AGENT_REGISTRY_IMPLEMENTATION_TASKS.md](AGENT_REGISTRY_IMPLEMENTATION_TASKS.md) for implementation details

---

## Support

**Questions?** Check:
- API Docs: http://localhost:8003/docs
- Health Check: http://localhost:8003/health
- Service Logs: `tail -f logs/registry_service.log`

**Issues?** Report at: https://github.com/your-org/agentic_jarvis/issues
