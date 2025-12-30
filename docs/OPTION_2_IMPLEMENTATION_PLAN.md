# Option 2: Pure A2A Architecture - Implementation Plan

**Date**: 2025-12-30
**Status**: Ready for Implementation
**Effort**: 1-2 days
**Dependencies**: Agent Registry Service running on port 8003

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Changes](#architecture-changes)
3. [Implementation Phases](#implementation-phases)
4. [File Structure](#file-structure)
5. [Detailed Implementation](#detailed-implementation)
6. [Testing Plan](#testing-plan)
7. [Migration Guide](#migration-guide)
8. [Rollback Plan](#rollback-plan)

---

## Overview

### Goal

Convert all agents to **self-contained A2A services** that are discovered dynamically via agent cards, eliminating the factory-based "local" agent pattern.

### Key Principles

1. **All agents are remote A2A services** - No distinction between "local" and "remote"
2. **Registry stores agent card URLs** - No factory references or code
3. **Jarvis uses RemoteA2aAgent uniformly** - Single code path for all agents
4. **Services are independent** - Each agent runs as separate process
5. **MCP servers preserved** - Kept for testing/debugging purposes

### Benefits

- ✅ Clean, uniform architecture
- ✅ True microservices (agents are independent)
- ✅ No code coupling between Jarvis and agents
- ✅ Easy to add third-party agents
- ✅ Aligns with documented vision

---

## Architecture Changes

### Before (Factory-Based)

```
Jarvis Orchestrator
  ↓
Registry returns factory references
  ↓
AgentFactoryResolver loads code
  ↓
Creates LlmAgent with McpToolset
  ↓
McpToolset tries to connect to MCP server ❌
  ↓
Connection fails → "No response"
```

### After (Pure A2A)

```
Jarvis Orchestrator
  ↓
Registry returns agent card URLs
  ↓
Creates RemoteA2aAgent
  ↓
Invokes via A2A protocol
  ↓
Agent service processes request
  ↓
Response returned via A2A
```

---

## Implementation Phases

### Phase 1: Create A2A Agent Services (2-3 hours)

**Tasks:**
- Create `tickets_agent_service/agent.py`
- Create `finops_agent_service/agent.py`
- Create `oxygen_agent_service/agent.py`

**Each service includes:**
- Data layer (in-memory database)
- Tool functions (business logic)
- LlmAgent definition
- A2A server setup via `to_a2a()`

---

### Phase 2: Update Registry Format (30 minutes)

**Tasks:**
- Update registry storage format
- Change from factory references to agent card URLs
- Update `AgentInfo` model if needed

---

### Phase 3: Simplify Router (30 minutes)

**Tasks:**
- Update `_create_agents()` in `dynamic_router_with_registry.py`
- Remove factory-based agent creation logic
- Use RemoteA2aAgent for all agents uniformly

---

### Phase 4: Update Migration Script (30 minutes)

**Tasks:**
- Update `scripts/migrate_to_registry_service.py`
- Register agents with agent card URLs instead of factory references

---

### Phase 5: Create Startup Scripts (15 minutes)

**Tasks:**
- Create `scripts/start_all_agents.sh`
- Create `scripts/stop_all_agents.sh`

---

### Phase 6: Testing & Validation (1-2 hours)

**Tasks:**
- Start all services
- Verify agent cards
- Test single-agent queries
- Test multi-agent queries
- Verify session tracking

---

## File Structure

### New Directories

```
agentic_jarvis/
├── tickets_agent_service/
│   ├── __init__.py
│   └── agent.py          # Self-contained A2A service
├── finops_agent_service/
│   ├── __init__.py
│   └── agent.py          # Self-contained A2A service
├── oxygen_agent_service/
│   ├── __init__.py
│   └── agent.py          # Self-contained A2A service
```

### New Scripts

```
scripts/
├── start_all_agents.sh    # Start all A2A agent services
└── stop_all_agents.sh     # Stop all A2A agent services
```

### Updated Files

```
scripts/
└── migrate_to_registry_service.py   # Register with agent card URLs

jarvis_agent/
└── dynamic_router_with_registry.py  # Simplified agent creation

docs/
├── ARCHITECTURE_VISION.md           # High-level vision (created)
└── OPTION_2_IMPLEMENTATION_PLAN.md  # This document
```

### Preserved Files (NOT deleted)

```
toolbox_servers/          # Keep for testing/debugging
├── tickets_server/
└── finops_server/

scripts/
├── start_tickets_server.sh          # Keep for testing
├── start_finops_server.sh           # Keep for testing
├── start_tickets_mcp_server.sh      # Keep for testing
├── start_finops_mcp_server.sh       # Keep for testing
└── start_oxygen_mcp_server.sh       # Keep for testing

jarvis_agent/mcp_agents/
└── agent_factory.py                 # Keep for reference
```

---

## Detailed Implementation

### Phase 1: Create A2A Agent Services

#### 1.1 Tickets Agent Service

**File:** `tickets_agent_service/agent.py`

**Structure:**
1. Import statements
2. In-memory database (TICKETS_DB)
3. Tool functions (get_all_tickets, get_ticket, get_user_tickets, create_ticket)
4. Create Toolbox and add tools
5. Create LlmAgent with tools
6. Expose via `to_a2a(agent, port=8080)`

**Port:** 8080
**Agent Card:** `http://localhost:8080/.well-known/agent-card.json`

**Tools:**
- `get_all_tickets()` → List all tickets
- `get_ticket(ticket_id)` → Get specific ticket
- `get_user_tickets(username)` → Get user's tickets
- `create_ticket(operation, user)` → Create new ticket

---

#### 1.2 FinOps Agent Service

**File:** `finops_agent_service/agent.py`

**Structure:**
1. Import statements
2. In-memory database (CLOUD_COSTS)
3. Tool functions (get_all_clouds_cost, get_cloud_cost, get_service_cost, get_cost_breakdown)
4. Create Toolbox and add tools
5. Create LlmAgent with tools
6. Expose via `to_a2a(agent, port=8081)`

**Port:** 8081
**Agent Card:** `http://localhost:8081/.well-known/agent-card.json`

**Tools:**
- `get_all_clouds_cost()` → Total across all providers
- `get_cloud_cost(provider)` → Provider-specific costs
- `get_service_cost(service_name)` → Service costs across providers
- `get_cost_breakdown()` → Comprehensive breakdown with percentages

---

#### 1.3 Oxygen Agent Service

**File:** `oxygen_agent_service/agent.py`

**Structure:**
1. Import statements
2. In-memory database (LEARNING_DATA)
3. Tool functions (get_user_courses, get_pending_exams, get_user_preferences, get_learning_summary)
4. Create Toolbox and add tools
5. Create LlmAgent with tools
6. Expose via `to_a2a(agent, port=8082)`

**Port:** 8082
**Agent Card:** `http://localhost:8082/.well-known/agent-card.json`

**Tools:**
- `get_user_courses(username)` → User's courses
- `get_pending_exams(username)` → Pending exams with deadlines
- `get_user_preferences(username)` → Learning preferences
- `get_learning_summary(username)` → Complete learning journey

---

### Phase 2: Update Registry Format

#### 2.1 New Registry Storage Format

**File:** `agent_registry_service/storage/registry_config.json`

```json
{
  "version": "2.0.0",
  "last_updated": "2025-12-30T20:00:00Z",
  "agents": {
    "TicketsAgent": {
      "type": "remote",
      "agent_card_url": "http://localhost:8080/.well-known/agent-card.json",
      "description": "IT operations ticket management",
      "capabilities": {
        "domains": ["tickets", "IT", "operations"],
        "entities": ["ticket", "request", "vpn", "gitlab"],
        "operations": ["create", "read", "update", "list"],
        "keywords": ["ticket", "IT", "operation"],
        "priority": 10
      },
      "status": "enabled",
      "tags": ["core", "production"],
      "registered_at": "2025-12-30T20:00:00Z"
    },
    "FinOpsAgent": {
      "type": "remote",
      "agent_card_url": "http://localhost:8081/.well-known/agent-card.json",
      "description": "Cloud financial operations and cost analytics",
      "capabilities": {
        "domains": ["costs", "finops", "cloud", "budget"],
        "entities": ["cost", "budget", "service", "provider"],
        "operations": ["read", "analyze", "breakdown"],
        "keywords": ["cost", "budget", "aws", "gcp", "azure"],
        "priority": 8
      },
      "status": "enabled",
      "tags": ["core", "production"],
      "registered_at": "2025-12-30T20:00:00Z"
    },
    "OxygenAgent": {
      "type": "remote",
      "agent_card_url": "http://localhost:8082/.well-known/agent-card.json",
      "description": "Learning and development platform",
      "capabilities": {
        "domains": ["learning", "courses", "exams", "education"],
        "entities": ["course", "exam", "preference", "deadline"],
        "operations": ["read", "track", "monitor"],
        "keywords": ["course", "exam", "learning", "education"],
        "priority": 7
      },
      "status": "enabled",
      "tags": ["core", "production"],
      "registered_at": "2025-12-30T20:00:00Z"
    }
  },
  "statistics": {
    "total_agents": 3,
    "enabled_agents": 3,
    "remote_agents": 3,
    "local_agents": 0
  }
}
```

**Key Changes:**
- All agents have `type: "remote"`
- `agent_card_url` replaces `factory_module` and `factory_function`
- NO factory references

---

### Phase 3: Simplify Router

#### 3.1 Update `_create_agents()` Method

**File:** `jarvis_agent/dynamic_router_with_registry.py`

**Location:** Lines 384-428

**Current Implementation:**
```python
def _create_agents(self, agent_infos: List[AgentInfo]) -> List[LlmAgent]:
    agents = []
    for agent_info in agent_infos:
        try:
            if agent_info.type == "local":
                # Create local agent via factory
                agent = self.factory_resolver.create_agent(...)
            elif agent_info.type == "remote":
                # Create remote A2A agent
                agent = RemoteA2aAgent(...)
            else:
                logger.warning(f"Unknown agent type: {agent_info.type}")
        except Exception as e:
            logger.error(f"Failed to create agent '{agent_info.name}': {e}")
            continue
    return agents
```

**New Implementation:**
```python
def _create_agents(self, agent_infos: List[AgentInfo]) -> List[LlmAgent]:
    """
    Create RemoteA2aAgent instances from AgentInfo objects.

    All agents are now remote A2A agents - no local/factory-based agents.

    Args:
        agent_infos: List of AgentInfo from registry

    Returns:
        List of RemoteA2aAgent instances
    """
    from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

    agents = []

    for agent_info in agent_infos:
        try:
            # All agents are remote A2A agents
            agent = RemoteA2aAgent(
                name=agent_info.name,
                description=agent_info.description,
                agent_card=agent_info.agent_card_url
            )
            agents.append(agent)
            logger.debug(f"Created RemoteA2aAgent: {agent_info.name}")

        except Exception as e:
            logger.error(f"Failed to create agent '{agent_info.name}': {e}")
            continue

    logger.debug(f"Created {len(agents)} agent instances")
    return agents
```

**Changes:**
- ✅ Removed factory-based logic
- ✅ Removed type checking (`if agent_info.type == "local"`)
- ✅ Single code path using `RemoteA2aAgent`
- ✅ Simpler, cleaner implementation

---

### Phase 4: Update Migration Script

#### 4.1 Update Agent Registration

**File:** `scripts/migrate_to_registry_service.py`

**New Implementation:**

```python
#!/usr/bin/env python3
"""
Migrate agents to registry service with A2A agent card URLs.

All agents are now registered as remote A2A agents.
"""

import requests
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

REGISTRY_URL = "http://localhost:8003"

AGENTS = [
    {
        "name": "TicketsAgent",
        "type": "remote",
        "agent_card_url": "http://localhost:8080/.well-known/agent-card.json",
        "description": "IT operations ticket management",
        "capabilities": {
            "domains": ["tickets", "IT", "operations"],
            "entities": ["ticket", "request", "vpn", "gitlab"],
            "operations": ["create", "read", "update", "list"],
            "keywords": ["ticket", "IT", "operation"],
            "priority": 10
        },
        "tags": ["core", "production"]
    },
    {
        "name": "FinOpsAgent",
        "type": "remote",
        "agent_card_url": "http://localhost:8081/.well-known/agent-card.json",
        "description": "Cloud financial operations and cost analytics",
        "capabilities": {
            "domains": ["costs", "finops", "cloud", "budget"],
            "entities": ["cost", "budget", "service", "provider"],
            "operations": ["read", "analyze", "breakdown"],
            "keywords": ["cost", "budget", "aws", "gcp", "azure"],
            "priority": 8
        },
        "tags": ["core", "production"]
    },
    {
        "name": "OxygenAgent",
        "type": "remote",
        "agent_card_url": "http://localhost:8082/.well-known/agent-card.json",
        "description": "Learning and development platform",
        "capabilities": {
            "domains": ["learning", "courses", "exams", "education"],
            "entities": ["course", "exam", "preference", "deadline"],
            "operations": ["read", "track", "monitor"],
            "keywords": ["course", "exam", "learning", "education"],
            "priority": 7
        },
        "tags": ["core", "production"]
    }
]

def check_registry_health():
    """Check if registry service is running."""
    try:
        response = requests.get(f"{REGISTRY_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_agent_card(agent_card_url):
    """Check if agent card is accessible."""
    try:
        response = requests.get(agent_card_url, timeout=5)
        return response.status_code == 200
    except:
        return False

def register_agent(agent_config):
    """Register a single agent."""
    try:
        response = requests.post(
            f"{REGISTRY_URL}/registry/agents",
            json=agent_config,
            timeout=10
        )

        if response.status_code in [200, 201]:
            return True, "Success"
        else:
            return False, response.text

    except Exception as e:
        return False, str(e)

def main():
    """Register all agents."""

    print("=" * 80)
    print("Agent Registration (A2A Agent Card URLs)")
    print("=" * 80)
    print()

    # Check registry service
    print("Checking registry service...")
    if not check_registry_health():
        print("✗ ERROR: Registry service not available at", REGISTRY_URL)
        print("  Start with: python agent_registry_service/main.py")
        sys.exit(1)
    print("✓ Registry service is running")
    print()

    # Register each agent
    print("Registering agents...")
    print()

    success_count = 0

    for agent_config in AGENTS:
        agent_name = agent_config["name"]
        agent_card_url = agent_config["agent_card_url"]

        print(f"  {agent_name}:")
        print(f"    Agent Card: {agent_card_url}")

        # Check agent card
        if not check_agent_card(agent_card_url):
            print(f"    ⚠  WARNING: Agent card not accessible (service may not be running)")

        # Register
        success, message = register_agent(agent_config)

        if success:
            print(f"    ✓ Registered successfully")
            success_count += 1
        else:
            print(f"    ✗ Failed: {message}")

        print()

    # Summary
    print("=" * 80)
    print(f"Registration complete: {success_count}/{len(AGENTS)} agents registered")
    print("=" * 80)
    print()

    if success_count < len(AGENTS):
        print("⚠  Some agents failed to register")
        print("  Make sure all agent services are running:")
        print("    ./scripts/start_all_agents.sh")
        print()
        sys.exit(1)
    else:
        print("✓ All agents registered successfully!")
        print()
        print("Next step:")
        print("  python jarvis_agent/main_with_registry.py")
        print()

if __name__ == "__main__":
    main()
```

**Key Changes:**
- ✅ Registers agents with agent card URLs
- ✅ Checks agent card accessibility
- ✅ Provides helpful error messages
- ✅ Clear success/failure reporting

---

### Phase 5: Create Startup Scripts

#### 5.1 Start All Agents Script

**File:** `scripts/start_all_agents.sh`

```bash
#!/bin/bash

echo "========================================="
echo "Starting All Agent Services (A2A)"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "✗ ERROR: Virtual environment not found"
    echo "  Create with: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if agents already running
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠  WARNING: Port 8080 already in use (Tickets Agent)"
    echo "  Stop with: lsof -ti:8080 | xargs kill -9"
    exit 1
fi

if lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠  WARNING: Port 8081 already in use (FinOps Agent)"
    echo "  Stop with: lsof -ti:8081 | xargs kill -9"
    exit 1
fi

if lsof -Pi :8082 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠  WARNING: Port 8082 already in use (Oxygen Agent)"
    echo "  Stop with: lsof -ti:8082 | xargs kill -9"
    exit 1
fi

# Start agents in background
echo "Starting Tickets Agent (port 8080)..."
nohup python tickets_agent_service/agent.py > logs/tickets_agent.log 2>&1 &
TICKETS_PID=$!
sleep 2

echo "Starting FinOps Agent (port 8081)..."
nohup python finops_agent_service/agent.py > logs/finops_agent.log 2>&1 &
FINOPS_PID=$!
sleep 2

echo "Starting Oxygen Agent (port 8082)..."
nohup python oxygen_agent_service/agent.py > logs/oxygen_agent.log 2>&1 &
OXYGEN_PID=$!
sleep 2

echo ""
echo "========================================="
echo "All Agent Services Started!"
echo "========================================="
echo ""
echo "Tickets Agent:  http://localhost:8080"
echo "                http://localhost:8080/.well-known/agent-card.json"
echo ""
echo "FinOps Agent:   http://localhost:8081"
echo "                http://localhost:8081/.well-known/agent-card.json"
echo ""
echo "Oxygen Agent:   http://localhost:8082"
echo "                http://localhost:8082/.well-known/agent-card.json"
echo ""
echo "========================================="
echo "Process IDs:"
echo "  Tickets: $TICKETS_PID"
echo "  FinOps:  $FINOPS_PID"
echo "  Oxygen:  $OXYGEN_PID"
echo "========================================="
echo ""
echo "Logs:"
echo "  tail -f logs/tickets_agent.log"
echo "  tail -f logs/finops_agent.log"
echo "  tail -f logs/oxygen_agent.log"
echo ""
echo "To stop all agents:"
echo "  ./scripts/stop_all_agents.sh"
echo ""
```

**Make executable:**
```bash
chmod +x scripts/start_all_agents.sh
```

---

#### 5.2 Stop All Agents Script

**File:** `scripts/stop_all_agents.sh`

```bash
#!/bin/bash

echo "Stopping all agent services..."
echo ""

# Kill by port
if lsof -ti:8080 >/dev/null 2>&1; then
    lsof -ti:8080 | xargs kill -9 2>/dev/null
    echo "✓ Stopped Tickets Agent (port 8080)"
else
    echo "  Tickets Agent not running"
fi

if lsof -ti:8081 >/dev/null 2>&1; then
    lsof -ti:8081 | xargs kill -9 2>/dev/null
    echo "✓ Stopped FinOps Agent (port 8081)"
else
    echo "  FinOps Agent not running"
fi

if lsof -ti:8082 >/dev/null 2>&1; then
    lsof -ti:8082 | xargs kill -9 2>/dev/null
    echo "✓ Stopped Oxygen Agent (port 8082)"
else
    echo "  Oxygen Agent not running"
fi

echo ""
echo "All agent services stopped."
```

**Make executable:**
```bash
chmod +x scripts/stop_all_agents.sh
```

---

## Testing Plan

### Prerequisites

1. Registry service running on port 8003
2. All agent services running (8080, 8081, 8082)
3. Agents registered in registry

### Test Sequence

#### 1. Start Services

```bash
# Terminal 1: Registry Service
python agent_registry_service/main.py

# Terminal 2: All Agent Services
./scripts/start_all_agents.sh
```

#### 2. Verify Agent Cards

```bash
# Check each agent card
curl http://localhost:8080/.well-known/agent-card.json | jq .
curl http://localhost:8081/.well-known/agent-card.json | jq .
curl http://localhost:8082/.well-known/agent-card.json | jq .

# Expected: Valid agent card JSON with tools, endpoints, etc.
```

#### 3. Register Agents

```bash
python scripts/migrate_to_registry_service.py

# Expected output:
# ✓ All agents registered successfully!
```

#### 4. Verify Registry

```bash
curl http://localhost:8003/registry/agents | jq .

# Expected: JSON with 3 agents, all type="remote"
```

#### 5. Test Jarvis Orchestrator

```bash
python jarvis_agent/main_with_registry.py
```

**Test Cases:**

```
Test 1: Single Agent - Tickets
User: show my tickets
Expected: List of tickets for user

Test 2: Single Agent - FinOps
User: what's our AWS cost?
Expected: AWS cost breakdown

Test 3: Single Agent - Oxygen
User: show courses for vishal
Expected: Vishal's enrolled and completed courses

Test 4: Multi-Agent Query
User: show my tickets and courses
Expected: Combined response from TicketsAgent and OxygenAgent

Test 5: Error Handling
User: show tickets for nonexistent_user
Expected: Graceful error message

Test 6: Session Continuity
User: show my tickets
User: what about alex's tickets?
Expected: Context maintained across queries
```

#### 6. Verify Session Tracking

```bash
# Check session was created
curl http://localhost:8003/sessions | jq .

# Expected: Session with conversation history and agent invocations
```

---

## Migration Guide

### Step-by-Step Migration

#### Step 1: Backup Current State

```bash
# Backup registry config
cp agent_registry_service/storage/registry_config.json \
   agent_registry_service/storage/registry_config.json.backup

# Backup router
cp jarvis_agent/dynamic_router_with_registry.py \
   jarvis_agent/dynamic_router_with_registry.py.backup
```

#### Step 2: Stop Running Services

```bash
# Stop any running agents/servers
./scripts/stop_all_agents.sh

# Stop registry if running
lsof -ti:8003 | xargs kill -9
```

#### Step 3: Create Agent Services

```bash
# Create directories
mkdir -p tickets_agent_service
mkdir -p finops_agent_service
mkdir -p oxygen_agent_service

# Create __init__.py files
touch tickets_agent_service/__init__.py
touch finops_agent_service/__init__.py
touch oxygen_agent_service/__init__.py

# Create agent.py files (use content from Phase 1)
# ... (create each agent service file)
```

#### Step 4: Update Router

```bash
# Edit jarvis_agent/dynamic_router_with_registry.py
# Update _create_agents() method as shown in Phase 3
```

#### Step 5: Update Migration Script

```bash
# Edit scripts/migrate_to_registry_service.py
# Replace with new version from Phase 4
```

#### Step 6: Create Startup Scripts

```bash
# Create scripts
# ... (create start_all_agents.sh and stop_all_agents.sh)

# Make executable
chmod +x scripts/start_all_agents.sh
chmod +x scripts/stop_all_agents.sh

# Create logs directory
mkdir -p logs
```

#### Step 7: Test Migration

```bash
# Start registry
python agent_registry_service/main.py

# Start agents
./scripts/start_all_agents.sh

# Register agents
python scripts/migrate_to_registry_service.py

# Test Jarvis
python jarvis_agent/main_with_registry.py
```

---

## Rollback Plan

### If Migration Fails

#### Option 1: Restore from Backup

```bash
# Restore registry config
cp agent_registry_service/storage/registry_config.json.backup \
   agent_registry_service/storage/registry_config.json

# Restore router
cp jarvis_agent/dynamic_router_with_registry.py.backup \
   jarvis_agent/dynamic_router_with_registry.py

# Restart services with old configuration
```

#### Option 2: Keep Both Implementations

- Keep MCP servers running (already preserved)
- Keep factory-based code (already preserved)
- Run A2A services on different ports (8080-8082)
- Switch between implementations by updating registry config

---

## Success Criteria

### Implementation Complete When:

- ✅ All 3 agent services running (ports 8080, 8081, 8082)
- ✅ All agent cards accessible
- ✅ All agents registered in registry with agent card URLs
- ✅ Jarvis can invoke all agents successfully
- ✅ Single-agent queries work
- ✅ Multi-agent queries work
- ✅ Session tracking works
- ✅ No "No response from agent" errors
- ✅ MCP servers preserved for debugging

---

## Post-Implementation Tasks

### Immediate (Day 1)

- Document any issues encountered
- Update README with new startup instructions
- Create troubleshooting guide

### Short-term (Week 1)

- Add health check endpoints to agent services
- Implement proper logging in agent services
- Add metrics/monitoring

### Medium-term (Month 1)

- Create Dockerfiles for each agent service
- Set up CI/CD for agent services
- Production deployment guide

---

## Appendix

### A. Port Assignments

| Service | Port | Agent Card URL |
|---------|------|----------------|
| Tickets Agent | 8080 | http://localhost:8080/.well-known/agent-card.json |
| FinOps Agent | 8081 | http://localhost:8081/.well-known/agent-card.json |
| Oxygen Agent | 8082 | http://localhost:8082/.well-known/agent-card.json |
| Registry Service | 8003 | http://localhost:8003/health |

### B. Directory Structure (Final)

```
agentic_jarvis/
├── agent_registry_service/      # Registry service
├── tickets_agent_service/       # NEW: Tickets A2A service
├── finops_agent_service/        # NEW: FinOps A2A service
├── oxygen_agent_service/        # NEW: Oxygen A2A service
├── jarvis_agent/                # Orchestrator
├── toolbox_servers/             # PRESERVED: For debugging
├── scripts/
│   ├── start_all_agents.sh     # NEW: Start A2A services
│   ├── stop_all_agents.sh      # NEW: Stop A2A services
│   └── migrate_to_registry_service.py  # UPDATED
└── docs/
    ├── ARCHITECTURE_VISION.md           # Vision doc
    └── OPTION_2_IMPLEMENTATION_PLAN.md  # This doc
```

### C. Environment Variables

No new environment variables required. Existing `.env` with `GOOGLE_API_KEY` is sufficient.

### D. Dependencies

All dependencies already installed. No new packages required.

---

## Questions & Support

**Issues during implementation?**
1. Check agent service logs in `logs/` directory
2. Verify agent cards are accessible
3. Confirm registry service is running
4. Check port conflicts with `lsof -i :8080-8082`

**Need help?**
- Review ARCHITECTURE_VISION.md for high-level understanding
- Check agent service code for implementation details
- Test each component independently before integration

---

**Status**: Ready for implementation
**Estimated time**: 1-2 days
**Risk level**: Low (MCP servers preserved as fallback)

