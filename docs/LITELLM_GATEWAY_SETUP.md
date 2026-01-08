# LiteLLM Agent Gateway Setup

This guide explains how to set up and use the LiteLLM Agent Gateway with Agentic Jarvis to expose and manage your A2A agents.

## Overview

The LiteLLM Agent Gateway provides a unified interface to discover, invoke, and monitor the three A2A agents in the Agentic Jarvis system:

1. **TicketsAgent** (Port 8080) - IT operations ticket management
2. **FinOpsAgent** (Port 8081) - Cloud cost analytics
3. **OxygenAgent** (Port 8082) - Learning & development platform

### Benefits

- **Unified Discovery**: Single endpoint to discover all available agents
- **Request Logging**: Automatic tracking of all agent invocations
- **Cost Monitoring**: Track LLM usage and costs across all agents
- **Access Control**: Manage which users/keys can access which agents
- **Multi-provider Support**: Fallback to different LLM providers (GPT-4, Claude, etc.)

## Prerequisites

1. Python 3.11+ installed
2. LiteLLM package installed: `pip install 'litellm[proxy]>=1.80.0'`
3. Google API key for Gemini model (set in `.env`)
4. All three A2A agents running (Tickets, FinOps, Oxygen)

## Quick Start

### 1. Configure Environment Variables

Copy `.env.template` to `.env` and configure:

```bash
cp .env.template .env
```

Edit `.env` and set:

```bash
# Google API Key (required for LLM routing)
GOOGLE_API_KEY=your_google_api_key_here

# LiteLLM Gateway Configuration
LITELLM_GATEWAY_PORT=8090
LITELLM_MASTER_KEY=sk-1234
LITELLM_GATEWAY_URL=http://localhost:8090

# JWT Token (if using authentication)
JWT_TOKEN=your-jwt-token-here
```

### 2. Start the A2A Agents (Phase 2)

In separate terminals, start all services:

```bash
# Terminal 1: Start all Phase 2 services (recommended)
./scripts/start_phase2.sh

# This will start:
# - Auth Service (9998)
# - Registry Service (8003)
# - TicketsAgent (8080)
# - FinOpsAgent (8081)
# - OxygenAgent (8082)
```

**Or start agents individually:**

```bash
# Terminal 1: Tickets Agent
cd tickets_agent_service && python agent.py

# Terminal 2: FinOps Agent
cd finops_agent_service && python agent.py

# Terminal 3: Oxygen Agent
cd oxygen_agent_service && python agent.py
```

### 3. Launch the LiteLLM Gateway

In a new terminal:

```bash
# Option 1: Using the startup script (recommended)
./scripts/start_litellm_gateway.sh

# Option 2: Direct command
litellm --config litellm_config.yaml --port 8090
```

The gateway will start on `http://localhost:8090`

### 4. Verify Agents Are Visible

Check that all agents are registered:

```bash
# Get list of available agents
curl http://localhost:8090/agents

# Check agent card for specific agent
curl http://localhost:8080/.well-known/agent-card.json  # Tickets
curl http://localhost:8081/.well-known/agent-card.json  # FinOps
curl http://localhost:8082/.well-known/agent-card.json  # Oxygen
```

### 5. Test Gateway Health

```bash
# Health check
curl http://localhost:8090/health

# Get gateway info
curl http://localhost:8090/

# View models and agents
curl http://localhost:8090/v1/models
```

## Configuration File

The gateway is configured via `litellm_config.yaml`:

```yaml
# Model configuration (for LLM routing)
model_list:
  - model_name: gemini-flash
    litellm_params:
      model: gemini/gemini-2.5-flash
      api_key: os.environ/GOOGLE_API_KEY

# A2A Agent Configuration
agents:
  - agent_id: tickets
    agent_name: TicketsAgent
    description: "IT operations ticket management"
    base_url: http://localhost:8080
    auth_type: bearer
    auth_token: os.environ/JWT_TOKEN

  - agent_id: finops
    agent_name: FinOpsAgent
    description: "Cloud cost analytics"
    base_url: http://localhost:8081
    auth_type: bearer
    auth_token: os.environ/JWT_TOKEN

  - agent_id: oxygen
    agent_name: OxygenAgent
    description: "Learning & development platform"
    base_url: http://localhost:8082
    auth_type: bearer
    auth_token: os.environ/JWT_TOKEN
```

## Using the Gateway

### Discover Available Agents

```bash
# List all agents
curl http://localhost:8090/agents
```

### Invoke Agents via Gateway

```python
from a2a.client import A2AClient

# Create client pointing to gateway
client = A2AClient(
    base_url="http://localhost:8090/a2a/tickets",
    headers={"Authorization": "Bearer sk-1234"}
)

# Send task to agent
response = client.send_task({
    "description": "Create a new ticket for VPN access",
    "parameters": {
        "operation": "vpn_access",
        "user": "john.doe"
    }
})
```

### Monitor Gateway Logs

The gateway provides detailed logging:

```bash
# Start gateway with verbose logging
litellm --config litellm_config.yaml --port 8090 --set_verbose True
```

### Access Admin UI

LiteLLM provides a web UI for management:

```bash
# Access at: http://localhost:8090/ui
# Use master key: sk-1234 (or your configured key)
```

## Troubleshooting

### Port Already in Use

If port 8090 is occupied:

```bash
# Kill existing process
lsof -ti:8090 | xargs kill -9

# Or change port in .env and litellm_config.yaml
```

### Agents Not Visible

1. Verify all A2A agents are running:
   ```bash
   lsof -i :8080  # Tickets
   lsof -i :8081  # FinOps
   lsof -i :8082  # Oxygen
   ```

2. Check agent cards are accessible:
   ```bash
   curl http://localhost:8080/.well-known/agent-card.json
   curl http://localhost:8081/.well-known/agent-card.json
   curl http://localhost:8082/.well-known/agent-card.json
   ```

3. Verify URLs in `litellm_config.yaml` match agent ports

### Authentication Errors

If you get 401/403 errors:

1. Generate JWT token:
   ```bash
   # Login to get token
   curl -X POST http://localhost:9998/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
   ```

2. Update `JWT_TOKEN` in `.env` file

3. Restart gateway: `./scripts/start_litellm_gateway.sh`

### Gateway Won't Start

Check LiteLLM installation:

```bash
# Verify litellm is installed
pip list | grep litellm

# Reinstall if needed
pip install 'litellm[proxy]>=1.80.0' --force-reinstall
```

## Service Ports Summary

| Service | Port | Description |
|---------|------|-------------|
| **LiteLLM Gateway** | 8090 | Agent discovery and routing |
| TicketsAgent | 8080 | IT operations tickets |
| FinOpsAgent | 8081 | Cloud cost analytics |
| OxygenAgent | 8082 | Learning & development |
| Registry Service | 8003 | Agent registry |
| Auth Service | 9998 | JWT authentication |
| Web UI | 9999 | Web interface |

## Advanced Configuration

### Add Fallback Models

Modify `litellm_config.yaml` to add GPT-4 or Claude as fallback:

```yaml
model_list:
  - model_name: gemini-flash
    litellm_params:
      model: gemini/gemini-2.5-flash
      api_key: os.environ/GOOGLE_API_KEY

  - model_name: gpt-4-fallback
    litellm_params:
      model: gpt-4o
      api_key: os.environ/OPENAI_API_KEY
```

### Enable Cost Tracking

Add to `litellm_config.yaml`:

```yaml
litellm_settings:
  success_callback: ["langfuse"]
  drop_params: true
  set_verbose: true
```

### Rate Limiting

Configure per-agent rate limits:

```yaml
agents:
  - agent_id: tickets
    agent_name: TicketsAgent
    base_url: http://localhost:8080
    rate_limit: 100  # requests per minute
```

## Next Steps

1. **Integration**: Update Jarvis orchestrator to route through gateway
2. **Monitoring**: Set up Langfuse or similar for cost tracking
3. **Production**: Configure OAuth 2.0 and secure master keys
4. **Scaling**: Add load balancing for high availability

## References

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [A2A Protocol Spec](https://docs.litellm.ai/docs/a2a)
- [Agentic Jarvis Phase 2 Plan](PHASE_2_PURE_A2A_PLAN.md)
