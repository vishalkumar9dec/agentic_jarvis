# Agent Marketplace - Complete Guide

**Transform your agent registry into a marketplace where third parties can register and host their own agents**

---

## Table of Contents

1. [Overview](#overview)
2. [Marketplace Architecture](#marketplace-architecture)
3. [Agent Types](#agent-types)
4. [Third-Party Developer Guide](#third-party-developer-guide)
5. [Agent Card Specification](#agent-card-specification)
6. [Registration Methods](#registration-methods)
7. [Discovery & Routing](#discovery--routing)
8. [Authentication & Authorization](#authentication--authorization)
9. [API Reference](#api-reference)
10. [Security Considerations](#security-considerations)
11. [Monetization (Optional)](#monetization-optional)
12. [Implementation Roadmap](#implementation-roadmap)

---

## 1. Overview

### What is the Agent Marketplace?

The Agent Marketplace transforms your agent registry into an **open platform** where:

- ✅ **Third-party developers** can register their agents without code access
- ✅ **Agents are discovered** dynamically via A2A protocol
- ✅ **Users benefit** from a growing ecosystem of specialized agents
- ✅ **You maintain control** through approval, monitoring, and governance

### Key Benefits

**For You (Platform Owner):**
- Rapidly expand capabilities without building every agent
- Create an ecosystem around your platform
- Maintain security through agent isolation
- Optional monetization opportunities

**For Third-Party Developers:**
- Reach your user base with their specialized agents
- No need to understand your entire codebase
- Standard A2A protocol integration
- Self-service registration

**For End Users:**
- Access to specialized agents (CRM, analytics, industry-specific)
- Seamless multi-agent experiences
- Single interface for all agents

---

## 2. Marketplace Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT MARKETPLACE ECOSYSTEM                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         End Users                               │
│  "Show me customer ABC-123 from Acme CRM and my IT tickets"    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Jarvis Orchestrator (Your Platform)                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  TwoStageRouter - Routes to any registered agent        │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            Agent Registry Service (Marketplace Hub)             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Agent Directory:                                        │   │
│  │  - Local Agents (Your agents)                           │   │
│  │  - Remote Agents (Third-party agents)                   │   │
│  │  - Discovery, Validation, Monitoring                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────┬────────────────────────────────────┬────────────────────┘
        │                                    │
        │ Your Agents                        │ Third-Party Agents
        ▼                                    ▼
┌──────────────────────┐          ┌──────────────────────────────┐
│ Local Agents         │          │ Remote Agents (A2A)          │
│ - tickets_agent      │          │ ┌──────────────────────────┐ │
│ - finops_agent       │          │ │ Acme CRM Agent           │ │
│ - oxygen_agent       │          │ │ acme-agent.example.com   │ │
│ (Your infrastructure)│          │ └──────────────────────────┘ │
└──────────────────────┘          │ ┌──────────────────────────┐ │
                                  │ │ Analytics Partner Agent  │ │
                                  │ │ analytics.partner.io     │ │
                                  │ └──────────────────────────┘ │
                                  │ (Third-party infra)          │
                                  └──────────────────────────────┘
```

---

## 3. Agent Types

### Type 1: Local Agents (First-Party)

**Ownership**: You own and operate these agents
**Hosting**: Your infrastructure
**Code**: In your repository
**Registration**: Via factory functions

**Example**: tickets_agent, finops_agent, oxygen_agent

**Storage Format**:
```json
{
  "name": "tickets_agent",
  "type": "local",
  "factory_module": "jarvis_agent.mcp_agents.agent_factory",
  "factory_function": "create_tickets_agent",
  "capabilities": {...},
  "tags": ["first-party", "production"]
}
```

---

### Type 2: Remote Agents (Third-Party)

**Ownership**: Third-party developers
**Hosting**: Third-party infrastructure
**Code**: Not in your repository
**Registration**: Via agent card URL (A2A protocol)

**Example**: acme_crm_agent, partner_analytics_agent

**Storage Format**:
```json
{
  "name": "acme_crm_agent",
  "type": "remote",
  "agent_card_url": "https://acme-agent.example.com:8080/.well-known/agent-card.json",
  "capabilities": {...},
  "tags": ["third-party", "crm", "verified"],
  "provider": {
    "name": "Acme Corp",
    "website": "https://acme.com",
    "support_email": "support@acme.com"
  },
  "status": "approved"  // pending | approved | suspended
}
```

---

## 4. Third-Party Developer Guide

### How to Register Your Agent with the Marketplace

#### Step 1: Build Your Agent

Create your agent using Google ADK:

```python
# your_agent/app.py

from google.adk.agents import LlmAgent
from google.adk.toolbox import Toolbox
from google.adk.runners.a2a import to_a2a
import os

# Define your tools
def get_customer(customer_id: str) -> dict:
    """Retrieve customer information from your CRM."""
    # Your implementation
    return {"customer_id": customer_id, "name": "..."}

def list_deals() -> list:
    """List all active deals."""
    # Your implementation
    return [{"deal_id": "D123", "value": 50000}]

# Create toolbox
toolbox = Toolbox()
toolbox.add_tool(get_customer)
toolbox.add_tool(list_deals)

# Create your agent
your_agent = LlmAgent(
    name="acme_crm_agent",
    description="Access Acme CRM data - customers, deals, sales pipelines",
    instruction="""
    You are the Acme CRM agent. You provide access to:
    - Customer information
    - Deal tracking
    - Sales pipeline analytics

    Always verify customer IDs before retrieving data.
    Format responses clearly with relevant details.
    """,
    tools=toolbox.tools,
    model="gemini-2.0-flash-exp"
)

# Expose via A2A protocol
if __name__ == "__main__":
    a2a_app = to_a2a(
        your_agent,
        port=8080,
        host="0.0.0.0"
    )

    print("✅ Acme CRM Agent running at http://0.0.0.0:8080")
    print("📋 Agent card: http://0.0.0.0:8080/.well-known/agent-card.json")
```

#### Step 2: Deploy Your Agent

```bash
# Option 1: Docker
docker build -t acme-crm-agent .
docker run -p 8080:8080 acme-crm-agent

# Option 2: Cloud Run / App Engine / Any PaaS
gcloud run deploy acme-crm-agent --port 8080

# Option 3: Kubernetes
kubectl apply -f agent-deployment.yaml
```

**Requirements**:
- Must be publicly accessible (or via VPN with platform owner)
- HTTPS recommended for production
- Stable endpoint (agent card URL shouldn't change)

#### Step 3: Verify Agent Card

Your agent automatically exposes an agent card:

```bash
curl https://your-agent.example.com:8080/.well-known/agent-card.json
```

**Expected Response**:
```json
{
  "agentCard": {
    "name": "acme_crm_agent",
    "description": "Access Acme CRM data - customers, deals, sales pipelines",
    "version": "1.0.0",
    "supportedProtocols": ["a2a"],
    "capabilities": {
      "tools": [
        {
          "name": "get_customer",
          "description": "Retrieve customer information from your CRM",
          "inputSchema": {
            "type": "object",
            "properties": {
              "customer_id": {"type": "string"}
            },
            "required": ["customer_id"]
          }
        },
        {
          "name": "list_deals",
          "description": "List all active deals",
          "inputSchema": {"type": "object"}
        }
      ]
    },
    "endpoints": {
      "invoke": "https://your-agent.example.com:8080/invoke",
      "stream": "https://your-agent.example.com:8080/stream"
    },
    "authentication": {
      "type": "bearer",
      "required": true
    }
  }
}
```

#### Step 4: Register with Marketplace

**Option A: Self-Service API**

```bash
curl -X POST https://jarvis-marketplace.example.com/registry/agents/remote \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_DEV_API_KEY" \
  -d '{
    "agent_card_url": "https://your-agent.example.com:8080/.well-known/agent-card.json",
    "capabilities": {
      "domains": ["crm", "sales", "customers"],
      "operations": ["read", "search", "analyze"],
      "entities": ["customer", "deal", "pipeline", "contact"],
      "keywords": ["crm", "sales", "customer", "deal"],
      "priority": 5
    },
    "tags": ["third-party", "crm", "sales"],
    "provider": {
      "name": "Acme Corp",
      "website": "https://acme.com",
      "support_email": "support@acme.com",
      "documentation": "https://acme.com/docs/agent"
    },
    "auth_config": {
      "type": "bearer",
      "token_endpoint": "https://your-agent.example.com/auth/token",
      "scopes": ["read:customers", "read:deals"]
    }
  }'
```

**Response**:
```json
{
  "status": "pending_approval",
  "agent_name": "acme_crm_agent",
  "registration_id": "reg_abc123",
  "message": "Agent registered successfully. Pending marketplace approval.",
  "next_steps": [
    "Wait for approval email (typically 24-48 hours)",
    "Complete authentication setup",
    "Test agent invocation"
  ]
}
```

**Option B: Developer Portal (Future)**

1. Visit https://jarvis-marketplace.example.com/developers
2. Click "Register New Agent"
3. Enter agent card URL
4. Configure capabilities
5. Submit for review

#### Step 5: Approval Process

**Marketplace Admin Reviews**:
1. ✅ Agent card is valid and accessible
2. ✅ Tools are properly documented
3. ✅ No malicious capabilities detected
4. ✅ Provider information is legitimate
5. ✅ Authentication is properly configured

**Possible Outcomes**:
- **Approved**: Agent goes live in marketplace
- **Rejected**: Reason provided, can resubmit
- **Needs Changes**: Specific modifications requested

#### Step 6: Go Live

Once approved:

```json
{
  "status": "approved",
  "agent_name": "acme_crm_agent",
  "live_since": "2025-12-26T15:00:00Z",
  "marketplace_url": "https://jarvis-marketplace.example.com/agents/acme_crm_agent"
}
```

**Your agent is now discoverable!** Users can invoke it via natural language:

```
User: "Show me customer ABC-123 from Acme CRM"
→ Jarvis routes to acme_crm_agent
→ Your agent receives the query
→ Response returned to user
```

---

## 5. Agent Card Specification

### Standard Agent Card Format (A2A Protocol)

```json
{
  "agentCard": {
    // Required fields
    "name": "agent_unique_name",
    "description": "Clear description of what this agent does",
    "version": "1.0.0",
    "supportedProtocols": ["a2a"],

    // Capabilities
    "capabilities": {
      "tools": [
        {
          "name": "tool_name",
          "description": "What this tool does",
          "inputSchema": {
            "type": "object",
            "properties": {
              "param1": {"type": "string", "description": "..."}
            },
            "required": ["param1"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "result": {"type": "string"}
            }
          }
        }
      ],
      "features": ["streaming", "context_aware", "multi_turn"]
    },

    // Endpoints
    "endpoints": {
      "invoke": "https://your-agent.com/invoke",
      "stream": "https://your-agent.com/stream",
      "health": "https://your-agent.com/health"
    },

    // Authentication
    "authentication": {
      "type": "bearer",  // or "api_key", "oauth2", "none"
      "required": true,
      "scopes": ["read", "write"],
      "documentation": "https://your-agent.com/docs/auth"
    },

    // Rate limits (optional)
    "rateLimits": {
      "requests_per_minute": 60,
      "requests_per_day": 10000
    },

    // Provider info (optional)
    "provider": {
      "name": "Your Company",
      "url": "https://yourcompany.com",
      "contact": "support@yourcompany.com"
    },

    // Additional metadata
    "metadata": {
      "tags": ["crm", "sales", "enterprise"],
      "category": "business_tools",
      "pricing": "free",  // or "paid", "freemium"
      "license": "proprietary"
    }
  }
}
```

### Marketplace-Enhanced Agent Card

In addition to standard A2A fields, marketplace adds:

```json
{
  "marketplace": {
    "registered_at": "2025-12-26T10:00:00Z",
    "status": "approved",
    "verification": {
      "verified": true,
      "verified_at": "2025-12-26T12:00:00Z",
      "verified_by": "marketplace_admin"
    },
    "stats": {
      "total_invocations": 15234,
      "success_rate": 0.98,
      "avg_response_time_ms": 245,
      "active_users": 127
    },
    "support": {
      "documentation": "https://acme.com/docs",
      "examples": "https://acme.com/examples",
      "changelog": "https://acme.com/changelog"
    }
  }
}
```

---

## 6. Registration Methods

### Method 1: API Registration (Programmatic)

```python
# Third-party developer code

import requests

def register_agent_with_marketplace():
    """Register our agent with Jarvis Marketplace."""

    marketplace_url = "https://jarvis-marketplace.example.com"
    api_key = "dev_your_api_key_here"

    registration_data = {
        "agent_card_url": "https://our-agent.example.com/.well-known/agent-card.json",
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
        }
    }

    response = requests.post(
        f"{marketplace_url}/registry/agents/remote",
        json=registration_data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )

    if response.status_code == 201:
        print("✅ Agent registered successfully!")
        print(f"Registration ID: {response.json()['registration_id']}")
    else:
        print(f"❌ Registration failed: {response.json()['error']}")

if __name__ == "__main__":
    register_agent_with_marketplace()
```

---

### Method 2: CLI Registration

```bash
# Install marketplace CLI
pip install jarvis-marketplace-cli

# Configure credentials
jarvis-marketplace configure --api-key YOUR_API_KEY

# Register agent
jarvis-marketplace register \
  --agent-card-url https://your-agent.com/.well-known/agent-card.json \
  --domains crm,sales \
  --tags third-party,crm \
  --provider-name "Acme Corp"

# Output:
# ✅ Agent registered successfully!
# Registration ID: reg_abc123
# Status: pending_approval
```

---

### Method 3: Discovery Endpoint (Auto-Registration)

```http
POST /registry/agents/discover
Content-Type: application/json

{
  "agent_card_url": "https://your-agent.com/.well-known/agent-card.json"
}
```

**Response**:
```json
{
  "agent_card": {
    "name": "acme_crm_agent",
    "description": "...",
    "capabilities": {...}
  },
  "suggested_capabilities": {
    "domains": ["crm", "sales"],  // Auto-extracted
    "entities": ["customer", "deal"],  // From tool names
    "operations": ["read", "search"]  // From tool verbs
  },
  "validation": {
    "passed": true,
    "checks": {
      "card_accessible": true,
      "schema_valid": true,
      "endpoints_reachable": true,
      "auth_configured": true
    }
  },
  "next_step": "confirm_registration"
}
```

---

## 7. Discovery & Routing

### How Remote Agents Are Discovered

#### Stage 1: Capability Matching (Local)

Registry maintains capabilities for ALL agents (local + remote):

```python
# All agents stored with same capability structure

registry.agents = {
    "tickets_agent": {
        "type": "local",
        "capabilities": {
            "domains": ["tickets", "IT"],
            "entities": ["ticket", "vpn"]
        }
    },
    "acme_crm_agent": {
        "type": "remote",
        "capabilities": {
            "domains": ["crm", "sales"],
            "entities": ["customer", "deal"]
        }
    }
}

# Query: "show customer ABC-123"
# Stage 1 matches: acme_crm_agent (score: 0.8)
```

#### Stage 2: LLM Selection

LLM sees both local and remote agents equally:

```
Candidates:
- tickets_agent (local): Handles IT tickets
- acme_crm_agent (remote): Access Acme CRM data

Query: "show customer ABC-123"
LLM selects: [acme_crm_agent]
```

#### Invocation: Transparent Routing

```python
# Jarvis invokes the selected agent

if agent.type == "local":
    # Direct function call
    response = await agent.run(query)

elif agent.type == "remote":
    # HTTP call via A2A protocol
    response = await agent.run(query)
    # Under the hood: POST https://acme-agent.com/invoke

# User doesn't see the difference!
```

---

### Multi-Agent Queries (Local + Remote)

```
User: "Show me customer ABC-123 from Acme CRM and my IT tickets"

Stage 1: Capability matching
  - "customer" + "Acme" + "CRM" → acme_crm_agent (remote)
  - "tickets" + "IT" → tickets_agent (local)

Stage 2: LLM selection
  Selected: [acme_crm_agent, tickets_agent]

Invocation: Parallel execution
  ├─ acme_crm_agent (remote) → HTTP call
  └─ tickets_agent (local) → Direct call

Response: Combined
  **Acme CRM - Customer ABC-123:**
  [Data from remote agent]

  **IT Tickets:**
  [Data from local agent]
```

---

## 8. Authentication & Authorization

### Authentication Models

#### Model 1: Platform-Level Auth (Recommended)

**How it works**:
1. Third-party agent requires API key/token
2. Platform admin obtains token from third party
3. Token stored securely in registry
4. Platform includes token when invoking remote agent

**Configuration**:
```json
{
  "acme_crm_agent": {
    "type": "remote",
    "auth_config": {
      "type": "bearer",
      "token": "${ACME_CRM_API_KEY}",  // Stored in secrets manager
      "header": "Authorization",
      "format": "Bearer {token}"
    }
  }
}
```

**Invocation**:
```python
# Jarvis includes auth when calling remote agent

response = await acme_agent.run(
    query="show customer ABC-123",
    context={
        "auth": {
            "type": "bearer",
            "token": get_secret("ACME_CRM_API_KEY")
        }
    }
)

# A2A SDK includes token in HTTP request:
# POST https://acme-agent.com/invoke
# Authorization: Bearer abc123...
```

---

#### Model 2: User-Level Auth (OAuth)

**How it works**:
1. User clicks "Connect Acme CRM"
2. OAuth flow redirects to third-party auth
3. User authorizes access
4. Platform stores user's token
5. Platform uses user's token when invoking agent

**Configuration**:
```json
{
  "acme_crm_agent": {
    "auth_config": {
      "type": "oauth2",
      "authorization_url": "https://acme.com/oauth/authorize",
      "token_url": "https://acme.com/oauth/token",
      "scopes": ["read:customers", "read:deals"],
      "user_tokens": {
        "alice": "user_token_alice_xyz",
        "bob": "user_token_bob_abc"
      }
    }
  }
}
```

**User Flow**:
```
1. User asks: "show customer ABC-123"
2. Jarvis checks: Does user have Acme CRM connected?
   - NO → Return: "Please connect your Acme CRM account: [Connect Button]"
   - YES → Use user's token to invoke agent
```

---

#### Model 3: No Auth (Public Agents)

Some agents may be public (e.g., weather, news):

```json
{
  "public_weather_agent": {
    "type": "remote",
    "auth_config": {
      "type": "none",
      "required": false
    }
  }
}
```

---

### Token Management

**Storage Options**:

1. **Environment Variables** (simple, single-tenant)
   ```bash
   ACME_CRM_API_KEY=abc123
   PARTNER_ANALYTICS_KEY=xyz789
   ```

2. **Secrets Manager** (production, multi-tenant)
   ```python
   from google.cloud import secretmanager

   def get_third_party_token(agent_name: str, user_id: str = None):
       client = secretmanager.SecretManagerServiceClient()

       if user_id:
           secret_name = f"agents/{agent_name}/users/{user_id}/token"
       else:
           secret_name = f"agents/{agent_name}/platform_token"

       response = client.access_secret_version(name=secret_name)
       return response.payload.data.decode('UTF-8')
   ```

3. **Database** (encrypted)
   ```sql
   CREATE TABLE agent_credentials (
       agent_name TEXT,
       user_id TEXT,  -- NULL for platform-level
       token_encrypted TEXT,
       expires_at TIMESTAMP
   );
   ```

---

## 9. API Reference

### Marketplace API Endpoints

#### Register Remote Agent

```http
POST /registry/agents/remote
Authorization: Bearer {developer_api_key}
Content-Type: application/json

{
  "agent_card_url": "https://your-agent.com/.well-known/agent-card.json",
  "capabilities": {
    "domains": ["domain1", "domain2"],
    "operations": ["read", "create"],
    "entities": ["entity1", "entity2"],
    "priority": 5
  },
  "tags": ["third-party", "category"],
  "provider": {
    "name": "Your Company",
    "website": "https://yourcompany.com",
    "support_email": "support@yourcompany.com"
  },
  "auth_config": {
    "type": "bearer",
    "token_endpoint": "https://your-agent.com/auth/token"
  }
}

Response (201 Created):
{
  "status": "pending_approval",
  "agent_name": "your_agent_name",
  "registration_id": "reg_abc123",
  "submitted_at": "2025-12-26T10:00:00Z"
}
```

---

#### Discover Agent from Card

```http
POST /registry/agents/discover
Content-Type: application/json

{
  "agent_card_url": "https://your-agent.com/.well-known/agent-card.json"
}

Response (200 OK):
{
  "agent_card": {...},
  "suggested_capabilities": {
    "domains": ["crm"],
    "entities": ["customer", "deal"]
  },
  "validation": {
    "passed": true,
    "checks": {...}
  }
}
```

---

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
      "stats": {
        "invocations": 15234,
        "success_rate": 0.98
      }
    }
  ],
  "total": 1
}
```

---

#### Get Agent Details

```http
GET /registry/agents/acme_crm_agent

Response (200 OK):
{
  "name": "acme_crm_agent",
  "type": "remote",
  "agent_card_url": "...",
  "capabilities": {...},
  "provider": {...},
  "status": "approved",
  "approved_at": "2025-12-26T12:00:00Z",
  "stats": {...}
}
```

---

#### Update Agent Status (Admin Only)

```http
PATCH /registry/agents/acme_crm_agent/status
Authorization: Bearer {admin_token}

{
  "status": "approved",
  "reviewer_notes": "All checks passed"
}

Response (200 OK):
{
  "status": "approved",
  "updated_at": "2025-12-26T12:00:00Z"
}
```

---

#### Suspend Agent (Admin Only)

```http
PATCH /registry/agents/acme_crm_agent/status
Authorization: Bearer {admin_token}

{
  "status": "suspended",
  "reason": "Repeated failures / Security concern"
}
```

---

## 10. Security Considerations

### Validation & Verification

**Agent Card Validation**:
```python
def validate_agent_card(agent_card_url: str) -> dict:
    """Validate agent card before registration."""

    checks = {
        "card_accessible": False,
        "https_required": False,
        "schema_valid": False,
        "endpoints_reachable": False,
        "tools_documented": False,
        "no_malicious_patterns": False
    }

    try:
        # 1. Fetch agent card
        response = requests.get(agent_card_url, timeout=10)
        response.raise_for_status()
        checks["card_accessible"] = True

        # 2. Require HTTPS in production
        if agent_card_url.startswith("https://"):
            checks["https_required"] = True

        # 3. Validate schema
        agent_card = response.json()
        if validate_a2a_schema(agent_card):
            checks["schema_valid"] = True

        # 4. Check endpoints
        invoke_url = agent_card["agentCard"]["endpoints"]["invoke"]
        health_check = requests.get(invoke_url.replace("/invoke", "/health"))
        if health_check.ok:
            checks["endpoints_reachable"] = True

        # 5. Validate tools are documented
        tools = agent_card["agentCard"]["capabilities"]["tools"]
        if all("description" in t and "inputSchema" in t for t in tools):
            checks["tools_documented"] = True

        # 6. Scan for malicious patterns
        if not detect_malicious_patterns(agent_card):
            checks["no_malicious_patterns"] = True

    except Exception as e:
        checks["error"] = str(e)

    return checks
```

---

### Malicious Pattern Detection

```python
def detect_malicious_patterns(agent_card: dict) -> bool:
    """Detect potentially malicious agent capabilities."""

    suspicious_keywords = [
        "delete_database", "drop_table", "exec", "eval",
        "system", "rm -rf", "sudo", "privilege_escalation"
    ]

    tools = agent_card["agentCard"]["capabilities"]["tools"]

    for tool in tools:
        tool_name = tool.get("name", "").lower()
        tool_desc = tool.get("description", "").lower()

        for keyword in suspicious_keywords:
            if keyword in tool_name or keyword in tool_desc:
                return True  # Malicious pattern detected

    return False
```

---

### Rate Limiting

```python
# Per-agent rate limits

@app.post("/invoke/{agent_name}")
async def invoke_agent(agent_name: str):
    """Invoke agent with rate limiting."""

    # Check rate limit
    rate_limit = get_agent_rate_limit(agent_name)

    if not rate_limit.check():
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {rate_limit.requests_per_minute} req/min"
        )

    # Invoke agent
    response = await agent.run(query)

    # Track invocation
    rate_limit.increment()

    return response
```

---

### Monitoring & Alerting

```python
# Monitor third-party agent health

class AgentHealthMonitor:
    """Monitor remote agent availability and performance."""

    async def monitor_agent(self, agent_name: str):
        """Continuous health monitoring."""

        agent = registry.get_agent(agent_name)

        # Check 1: Health endpoint
        try:
            health_url = agent.agent_card_url.replace("/agent-card.json", "/health")
            response = await httpx.get(health_url, timeout=5)

            if response.status_code != 200:
                await self.alert_unhealthy(agent_name, "Health check failed")

        except Exception as e:
            await self.alert_unhealthy(agent_name, f"Health check error: {e}")

        # Check 2: Response time
        stats = get_agent_stats(agent_name)
        if stats.avg_response_time_ms > 5000:  # 5 second threshold
            await self.alert_slow(agent_name, stats.avg_response_time_ms)

        # Check 3: Error rate
        if stats.error_rate > 0.1:  # 10% threshold
            await self.alert_high_errors(agent_name, stats.error_rate)

    async def alert_unhealthy(self, agent_name: str, reason: str):
        """Alert when agent is unhealthy."""

        # Auto-suspend if unhealthy for > 1 hour
        if time_unhealthy(agent_name) > 3600:
            registry.disable_agent(agent_name)
            send_notification(f"Agent {agent_name} auto-suspended: {reason}")
```

---

### Sandboxing (Advanced)

For high-security environments, run third-party agents through a proxy:

```
User Query
    ↓
Jarvis
    ↓
Agent Proxy (Sandbox)  ← Validates requests/responses
    ↓
Third-Party Agent
```

```python
class AgentProxy:
    """Proxy for third-party agents with sandboxing."""

    async def invoke(self, agent_name: str, query: str) -> str:
        """Invoke agent through sandbox."""

        # Validate input
        if not self.validate_input(query):
            raise ValueError("Invalid input")

        # Call remote agent
        response = await self.call_remote_agent(agent_name, query)

        # Validate output
        if not self.validate_output(response):
            raise ValueError("Invalid output from agent")

        # Sanitize response
        sanitized = self.sanitize_response(response)

        return sanitized
```

---

## 11. Monetization (Optional)

### Revenue Models

#### Model 1: Free Marketplace
- All agents free to register and use
- Platform monetizes through other means

#### Model 2: Listing Fees
- Third-party developers pay to list agents
- Example: $50/month per agent

#### Model 3: Usage-Based Pricing
- Platform charges per agent invocation
- Third-party developer gets revenue share
- Example: $0.01 per invocation, 70/30 split

#### Model 4: Premium Tier
- Basic agents: Free
- Premium agents: Require subscription
- Example: $19/month for premium agent access

---

### Implementation: Usage Tracking

```python
# Track invocations for billing

@app.post("/invoke/{agent_name}")
async def invoke_agent(agent_name: str, user_id: str):
    """Invoke agent with usage tracking."""

    # Invoke agent
    start = time.time()
    response = await agent.run(query)
    duration_ms = (time.time() - start) * 1000

    # Track usage
    await track_invocation(
        agent_name=agent_name,
        user_id=user_id,
        duration_ms=duration_ms,
        success=True,
        timestamp=datetime.now()
    )

    # Billing (if monetized)
    if is_paid_agent(agent_name):
        await record_billable_event(
            agent_name=agent_name,
            user_id=user_id,
            amount=0.01  # $0.01 per invocation
        )

    return response
```

---

## 12. Implementation Roadmap

### Phase 1: Core Marketplace (Week 1-2)

**Tasks**:
1. ✅ Enhance AgentRegistry to support `type: "remote"`
2. ✅ Add AgentFactoryResolver support for RemoteA2aAgent
3. ✅ Implement `/registry/agents/remote` endpoint
4. ✅ Implement agent card validation
5. ✅ Update storage format (JSON)
6. ✅ Add approval workflow (pending → approved)

**Deliverables**:
- Third-party agents can register via API
- Admin can approve/reject agents
- Remote agents appear in routing

---

### Phase 2: Developer Experience (Week 3)

**Tasks**:
1. Create developer documentation
2. Build CLI tool for registration
3. Add `/registry/agents/discover` endpoint
4. Auto-extract capabilities from agent card
5. Create developer portal (web UI)

**Deliverables**:
- Developer docs published
- CLI tool available
- Self-service registration

---

### Phase 3: Security & Monitoring (Week 4)

**Tasks**:
1. Implement malicious pattern detection
2. Add rate limiting per agent
3. Build health monitoring system
4. Add alerting for unhealthy agents
5. Implement auto-suspension

**Deliverables**:
- Secure marketplace
- Real-time monitoring
- Automated health checks

---

### Phase 4: Advanced Features (Month 2)

**Tasks**:
1. OAuth integration for user-level auth
2. Usage analytics dashboard
3. Agent versioning support
4. Marketplace search/filtering
5. Agent categories and tags

**Deliverables**:
- Advanced auth options
- Rich marketplace UI
- Analytics and insights

---

### Phase 5: Monetization (Optional, Month 3)

**Tasks**:
1. Usage tracking system
2. Billing integration (Stripe)
3. Developer payout system
4. Pricing tiers
5. Subscription management

**Deliverables**:
- Monetized marketplace
- Revenue sharing operational

---

## Example: Complete Third-Party Integration

### Scenario: Acme Corp Integrates Their CRM

#### 1. Acme Builds Agent

```python
# acme_agent/app.py
from google.adk.agents import LlmAgent
from google.adk.runners.a2a import to_a2a

agent = LlmAgent(
    name="acme_crm_agent",
    description="Access Acme CRM - customers, deals, pipelines",
    tools=acme_toolbox.tools
)

a2a_app = to_a2a(agent, port=8080)
```

#### 2. Acme Deploys

```bash
docker build -t acme-crm-agent .
docker run -p 8080:8080 acme-crm-agent
```

#### 3. Acme Registers

```bash
curl -X POST https://jarvis-marketplace.com/registry/agents/remote \
  -H "Authorization: Bearer acme_dev_key" \
  -d '{
    "agent_card_url": "https://acme-agent.com/.well-known/agent-card.json",
    "capabilities": {
      "domains": ["crm", "sales"],
      "entities": ["customer", "deal"]
    }
  }'
```

#### 4. Platform Admin Approves

```bash
# Admin reviews and approves
PATCH /registry/agents/acme_crm_agent/status
{"status": "approved"}
```

#### 5. End User Uses It

```
User: "Show me customer ABC-123 from Acme CRM"

Jarvis:
  ├─ Routes to acme_crm_agent (discovered from marketplace)
  ├─ Invokes via A2A protocol
  └─ Returns: "Customer ABC-123: Acme Industries, Active, ..."
```

**Success!** Third-party agent fully integrated with zero code changes to Jarvis. 🎉

---

## Summary

The Agent Marketplace transforms your registry into an **ecosystem** where:

✅ **Third parties** can register agents without code access
✅ **Discovery** happens automatically via A2A protocol
✅ **Routing** treats local and remote agents equally
✅ **Security** is maintained through validation and monitoring
✅ **Monetization** is possible (optional)

**Key Files to Update**:
1. `AGENT_REGISTRY_PERSISTENCE_SPEC.md` - Add remote agent support
2. `AGENT_REGISTRY_IMPLEMENTATION_TASKS.md` - Add marketplace tasks
3. `AGENT_REGISTRY_CALL_FLOW.md` - Add remote agent flows

**Next Step**: Review this marketplace design and approve for implementation! 🚀
