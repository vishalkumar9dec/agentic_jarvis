# Agentic Jarvis Testing Guide

## Quick Start

### 1. Start All Services
```bash
./scripts/restart_all.sh
```

### 2. Verify Health
```bash
./scripts/check_services.sh
```

### 3. Start Web Interface (Optional)
```bash
./scripts/start_web.sh
```

Then open in your browser:
- **Web UI**: http://localhost:9999/dev-ui
- **API Docs**: http://localhost:9999/docs

### 4. Run Integration Tests (Optional)
```bash
.venv/bin/python test_orchestrator.py
```

## Testing Individual Agents

### Tickets Agent (Port 5001)

**Get all tickets:**
```bash
curl -X POST http://localhost:5001/api/tool/get-all-tickets/invoke \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Get user-specific tickets:**
```bash
curl -X POST http://localhost:5001/api/tool/get-user-tickets/invoke \
  -H "Content-Type: application/json" \
  -d '{"username": "vishal"}'
```

**Search tickets by operation:**
```bash
curl -X POST http://localhost:5001/api/tool/search-tickets/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation": "create_ai_key"}'
```

**Create a new ticket:**
```bash
curl -X POST http://localhost:5001/api/tool/create-ticket/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation": "gitlab_access", "username": "john"}'
```

### FinOps Agent (Port 5002)

**Get all cloud costs:**
```bash
curl -X POST http://localhost:5002/api/tool/get-all-clouds-cost/invoke \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Get AWS costs:**
```bash
curl -X POST http://localhost:5002/api/tool/get-cloud-cost/invoke \
  -H "Content-Type: application/json" \
  -d '{"provider": "aws"}'
```

**Get GCP costs:**
```bash
curl -X POST http://localhost:5002/api/tool/get-cloud-cost/invoke \
  -H "Content-Type: application/json" \
  -d '{"provider": "gcp"}'
```

**Get specific service cost:**
```bash
curl -X POST http://localhost:5002/api/tool/get-service-cost/invoke \
  -H "Content-Type: application/json" \
  -d '{"provider": "aws", "service_name": "ec2"}'
```

**Get detailed cost breakdown:**
```bash
curl -X POST http://localhost:5002/api/tool/get-cost-breakdown/invoke \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Oxygen Agent - A2A (Port 8002)

**Check agent card (discovery):**
```bash
curl http://localhost:8002/.well-known/agent-card.json
```

**Python-based testing (recommended for A2A):**
```python
from remote_agent.oxygen_agent.tools import (
    get_user_courses,
    get_pending_exams,
    get_user_preferences,
    get_learning_summary
)

# Get user courses
courses = get_user_courses("vishal")
print(courses)

# Get pending exams
exams = get_pending_exams("vishal")
print(exams)

# Get complete learning summary
summary = get_learning_summary("vishal")
print(summary)
```

## Sample Test Users

### User: vishal
- **Tickets**: 2 tickets (create_ai_key, update_budget)
- **Courses**: aws, terraform
- **Completed**: docker
- **Pending Exams**: snowflake (deadline: 2025-12-28)
- **Preferences**: software engineering, cloud architecture

### User: alex
- **Tickets**: 1 ticket (create_gitlab_account)
- **Courses**: kubernetes, python advanced, devops
- **Completed**: git, linux, docker
- **Pending Exams**: kubernetes (2025-12-22), azure (2026-01-05)
- **Preferences**: DevOps, automation, container orchestration

### User: sarah
- **Tickets**: 1 ticket (vpn_setup)
- **Courses**: data science, machine learning
- **Completed**: python basics, sql
- **Pending Exams**: None
- **Preferences**: data analytics, AI

## Example Multi-Agent Queries

These queries would route to multiple agents when using the CLI:

1. **"Show me vishal's tickets and upcoming exams"**
   - Routes to: TicketsAgent + OxygenAgent
   - Expected: 2 tickets + 1 pending exam

2. **"What are our AWS costs and does vishal have AWS courses?"**
   - Routes to: FinOpsAgent + OxygenAgent
   - Expected: AWS cost breakdown + course enrollment status

3. **"List all pending tickets and who has pending exams"**
   - Routes to: TicketsAgent + OxygenAgent
   - Expected: All pending tickets + all users with pending exams

## Troubleshooting

### Services won't start
```bash
# Kill all processes on the ports
lsof -ti:5001 | xargs kill -9
lsof -ti:5002 | xargs kill -9
lsof -ti:8002 | xargs kill -9

# Try starting again
./scripts/restart_all.sh
```

### Check service logs
```bash
tail -f logs/tickets_server.log
tail -f logs/finops_server.log
tail -f logs/oxygen_agent.log
```

### Verify endpoints
```bash
# Tickets toolbox
curl http://localhost:5001/

# FinOps toolbox
curl http://localhost:5002/

# Oxygen agent card
curl http://localhost:8002/.well-known/agent-card.json
```

## Architecture Overview

```
┌─────────────────────────────────────────┐
│     Jarvis (Root Orchestrator)          │
│     - Routes queries to sub-agents      │
│     - Coordinates multi-agent responses │
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

## Web UI Usage

The ADK Web UI provides a graphical interface to interact with Jarvis:

### Starting the Web UI

1. Ensure all services are running:
   ```bash
   ./scripts/check_services.sh
   ```

2. Start the web server:
   ```bash
   ./scripts/start_web.sh
   ```

3. Open your browser to:
   - **Chat Interface**: http://localhost:9999/dev-ui
   - **API Documentation**: http://localhost:9999/docs

### Using the Web UI

The web interface provides:
- **Interactive chat**: Chat with Jarvis in a web browser
- **Session management**: Create and manage multiple chat sessions
- **Agent selection**: Choose which agent to interact with
- **Response streaming**: See responses as they're generated

### Example Queries in Web UI

Try these queries in the chat interface:
- "What can you do for me?"
- "Show me vishal's tickets"
- "What are our AWS costs?"
- "Does vishal have any pending exams?"
- "Show me all cloud costs breakdown"

## Interactive CLI Usage

To use the interactive command-line chat interface:

```bash
.venv/bin/python main.py
```

Example conversation:
```
👤 You: What can you do for me?
🤖 Jarvis: I can help you with IT operations, cloud costs, and learning & development...

👤 You: Show me vishal's tickets
🤖 Jarvis: Here are Vishal's tickets:
  • Ticket #12301: create_ai_key (pending)
  • Ticket #12303: update_budget (in_progress)

👤 You: What are our AWS costs?
🤖 Jarvis: Our AWS costs are $100 USD. Here's the breakdown...
```

Type `exit`, `quit`, or `q` to end the session.

## Known Issues

1. **Async Session Warnings**: You may see "Unclosed client session" warnings from aiohttp when running tests. These are harmless cleanup warnings and don't indicate failures.

2. **A2A Experimental Warning**: RemoteA2aAgent shows an experimental warning. This is expected and doesn't affect functionality.

3. **Function Call Warnings**: You may see "Warning: there are non-text parts in the response: ['function_call']" when agents use tools. This is normal and the response text is still extracted correctly.

## Next Steps

- **Phase 2**: JWT authentication for user-specific data
- **Phase 3**: Memory & context management with session services
- **Phase 4**: OAuth 2.0 integration for enterprise SSO
