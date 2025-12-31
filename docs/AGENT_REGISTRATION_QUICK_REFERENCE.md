# Agent Registration - Quick Reference Card

**Fast reference for registering agents with Jarvis**

---

## Prerequisites

```bash
# 1. Start Agent Registry Service
./scripts/start_registry_service.sh

# 2. For remote agents: Start the agent
./scripts/start_oxygen_agent.sh  # Example
```

---

## Quick Commands

### Using Helper Script (Easiest)

```bash
# Register all agents
python scripts/register_agents.py --all

# Register local agents only
python scripts/register_agents.py --local

# Register remote agents only
python scripts/register_agents.py --remote

# Register specific agent
python scripts/register_agents.py --agent oxygen_agent

# List registered agents
python scripts/register_agents.py --list
```

---

## Manual Registration

### Local Agent (First-Party)

```bash
curl -X POST http://localhost:8003/registry/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_config": {
      "agent_type": "my_agent",
      "factory_module": "jarvis_agent.mcp_agents.agent_factory",
      "factory_function": "create_my_agent"
    },
    "capabilities": {
      "domains": ["domain1", "domain2"],
      "operations": ["read", "write"],
      "entities": ["entity1"],
      "keywords": ["keyword1", "keyword2"],
      "examples": ["example query"],
      "priority": 10
    },
    "tags": ["first-party", "production"]
  }'
```

### Remote Agent (Third-Party)

```bash
curl -X POST http://localhost:8003/registry/agents/remote \
  -H "Content-Type: application/json" \
  -d '{
    "agent_card_url": "http://localhost:8002/.well-known/agent-card.json",
    "capabilities": {
      "domains": ["learning", "courses"],
      "operations": ["read", "enroll"],
      "entities": ["course", "exam"],
      "keywords": ["course", "exam"],
      "priority": 5
    },
    "tags": ["remote", "learning"],
    "provider": {
      "name": "Provider Name",
      "website": "https://provider.com",
      "support_email": "support@provider.com"
    }
  }'
```

---

## Common Operations

### List All Agents
```bash
curl http://localhost:8003/registry/agents
```

### Get Agent Details
```bash
curl http://localhost:8003/registry/agents/{agent_name}
```

### Delete Agent
```bash
curl -X DELETE http://localhost:8003/registry/agents/{agent_name}
```

### Disable Agent
```bash
curl -X PATCH http://localhost:8003/registry/agents/{agent_name}/status \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

### Update Capabilities
```bash
curl -X PUT http://localhost:8003/registry/agents/{agent_name}/capabilities \
  -H "Content-Type: application/json" \
  -d '{"capabilities": {...}}'
```

---

## Health Checks

```bash
# Registry service health
curl http://localhost:8003/health

# Check if service is running
lsof -i :8003

# View logs
tail -f logs/registry_service.log
```

---

## Agent Types

| Type | Description | Endpoint |
|------|-------------|----------|
| **Local** | Your agents, hosted locally | `POST /registry/agents` |
| **Remote** | Third-party agents via A2A | `POST /registry/agents/remote` |

---

## Priority Levels

| Priority | Use Case |
|----------|----------|
| **10** | Critical system agents |
| **8** | Important business agents |
| **5** | Integration agents |
| **3** | Nice-to-have agents |
| **0** | Experimental/test agents |

---

## Troubleshooting

### Service Not Available
```bash
./scripts/start_registry_service.sh
curl http://localhost:8003/health
```

### Agent Card Not Reachable
```bash
# Check if agent is running
lsof -i :8002

# Start the agent
./scripts/start_oxygen_agent.sh

# Verify agent card
curl http://localhost:8002/.well-known/agent-card.json
```

### Already Registered
```bash
# Delete and re-register
curl -X DELETE http://localhost:8003/registry/agents/{agent_name}
python scripts/register_agents.py --agent {agent_name}
```

---

## Interactive API Docs

Visit: **http://localhost:8003/docs**

---

## Built-in Agents

| Agent | Type | Port | Command |
|-------|------|------|---------|
| **tickets_agent** | Local | N/A | Part of Jarvis |
| **finops_agent** | Local | N/A | Part of Jarvis |
| **oxygen_agent** | Remote | 8002 | `./scripts/start_oxygen_agent.sh` |

---

## Example: Register Oxygen Agent

```bash
# 1. Start Oxygen agent
./scripts/start_oxygen_agent.sh

# 2. Register it
python scripts/register_agents.py --agent oxygen_agent

# 3. Verify
python scripts/register_agents.py --list
```

---

**Full Documentation**: [AGENT_REGISTRATION_GUIDE.md](AGENT_REGISTRATION_GUIDE.md)
