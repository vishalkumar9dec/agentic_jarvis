# Agentic Jarvis - Quick Start Guide

## 1. Start All Services

```bash
./scripts/restart_all.sh
```

This starts:
- Tickets Toolbox Server (port 5001)
- FinOps Toolbox Server (port 5002)
- Oxygen A2A Agent (port 8002)

## 2. Verify Services

```bash
./scripts/check_services.sh
```

Expected output:
```
✅ Tickets Toolbox Server - Running on port 5001
✅ FinOps Toolbox Server - Running on port 5002
✅ Oxygen A2A Agent - Running on port 8002
```

## 3. Choose Your Interface

### Option A: Web UI (Recommended)

Start the web interface:
```bash
./scripts/start_web.sh
```

Then open in your browser:
- **Chat Interface**: http://localhost:9999/dev-ui
- **API Documentation**: http://localhost:9999/docs

### Option B: Command Line Interface

Run the interactive CLI:
```bash
.venv/bin/python main.py
```

Type your queries and get instant responses.

## Example Queries to Try

### IT Operations (Tickets)
- "Show me all tickets"
- "What tickets does vishal have?"
- "Search for tickets with operation create_ai_key"
- "Create a new ticket for gitlab access for user john"

### Cloud Costs (FinOps)
- "What are our total cloud costs?"
- "Show me AWS costs"
- "Break down costs by service"
- "What's the cost of EC2 on AWS?"

### Learning & Development (Oxygen)
- "Does vishal have any pending exams?"
- "Show me alex's courses"
- "What are vishal's learning preferences?"
- "Give me a learning summary for alex"

### Cross-Agent Queries
- "Show me vishal's tickets and upcoming exams"
- "What are our AWS costs and does vishal have AWS courses?"
- "List all pending tickets and who has pending exams"

## Stopping Services

To stop all services:
```bash
# Stop web UI
lsof -ti:9999 | xargs kill -9

# Stop all backend services
lsof -ti:5001 | xargs kill -9
lsof -ti:5002 | xargs kill -9
lsof -ti:8002 | xargs kill -9
```

Or use the restart script which automatically cleans up:
```bash
./scripts/restart_all.sh
```

## Accessing Different Agents

### Jarvis Root Orchestrator
- The main agent that routes queries to sub-agents
- Automatically determines which sub-agent(s) to use
- Available through Web UI or CLI

### Individual Agents (Direct API Access)

**Tickets Agent:**
```bash
curl -X POST http://localhost:5001/api/tool/get-all-tickets/invoke \
  -H "Content-Type: application/json" -d '{}'
```

**FinOps Agent:**
```bash
curl -X POST http://localhost:5002/api/tool/get-all-clouds-cost/invoke \
  -H "Content-Type: application/json" -d '{}'
```

**Oxygen Agent:**
```bash
curl http://localhost:8002/.well-known/agent-card.json
```

## Troubleshooting

### Services won't start
```bash
# Clean up all ports
lsof -ti:5001 | xargs kill -9
lsof -ti:5002 | xargs kill -9
lsof -ti:8002 | xargs kill -9
lsof -ti:9999 | xargs kill -9

# Restart
./scripts/restart_all.sh
```

### Check logs
```bash
tail -f logs/tickets_server.log
tail -f logs/finops_server.log
tail -f logs/oxygen_agent.log
tail -f logs/web_server.log
```

### Verify environment
```bash
# Check if .env file exists and has GOOGLE_API_KEY
cat .env | grep GOOGLE_API_KEY
```

## Architecture Overview

```
                User Interfaces
                     │
        ┌────────────┼────────────┐
        │            │            │
   Web UI:9999   CLI (main.py)  Direct API
        │            │            │
        └────────────┼────────────┘
                     │
              Jarvis Root
              Orchestrator
                     │
        ┌────────────┼────────────┐
        │            │            │
    Tickets      FinOps       Oxygen
    Agent        Agent        Agent
   (Toolbox)   (Toolbox)      (A2A)
     :5001       :5002        :8002
```

## Next Steps

- See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing instructions
- See [README.md](README.md) for project overview and architecture details
- See [CLAUDE.md](CLAUDE.md) for development guidelines
