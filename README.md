# Agentic Jarvis

Enterprise AI assistant with multi-agent architecture using Google's Agent Development Kit (ADK).

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy template
cp .env.template .env

# Edit .env and add your Google API key
# Get API key from: https://makersuite.google.com/app/apikey
```

### 3. Start Services

Open multiple terminal windows:

```bash
# Terminal 1: Tickets Server
./scripts/start_tickets_server.sh

# Terminal 2: FinOps Server
./scripts/start_finops_server.sh

# Terminal 3: Oxygen Agent
./scripts/start_oxygen_agent.sh

# Terminal 4: Check services are running
./scripts/check_services.sh
```

### 4. Test the System

```bash
# Run CLI interface
python main.py
```

## Documentation

📚 **[Complete Documentation](./docs/)** - All documentation is in the `docs/` folder

**Quick Links:**
- [Quick Start Guide](./docs/QUICK_START.md) - Get started quickly
- [Product Specification](./docs/JARVIS_PRODUCT_SPEC.md) - Complete product vision
- [Phase 2 Plan](./docs/PHASE_2_PLAN.md) - JWT Authentication implementation
- [Authentication Architecture](./docs/AUTHENTICATION_ARCHITECTURE.md) - Authentication design (proposed)
- [Environment Configuration](./docs/ENVIRONMENT.md) - Configuration guide

**Developer:**
- [CLAUDE.md](./CLAUDE.md) - Development guide for Claude Code
- [Toolbox Architecture](./docs/TOOLBOX_ARCHITECTURE.md) - Architecture patterns
- [Testing Guide](./docs/TESTING_GUIDE.md) - Testing documentation

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

## Features

### Phase 1: Core Functionality (Current)
- ✅ Multi-agent orchestration with Google ADK
- ✅ IT Tickets management (TicketsAgent)
- ✅ Cloud cost analytics (FinOpsAgent)
- ✅ Learning & development tracking (OxygenAgent via A2A)
- 🔄 Web UI (In Progress)

### Phase 2: JWT Authentication (Planned)
- Bearer token authentication
- User-specific data access control

### Phase 3: Memory & Context (Planned)
- Session management
- Multi-layer memory system
- Proactive notifications

### Phase 4: OAuth 2.0 (Planned)
- Enterprise SSO integration
- OAuth 2.0 authentication
- Integration connectors

## Technology Stack

- **Google ADK v1.0.0+** - Agent Development Kit
- **A2A Protocol v0.2** - Agent-to-Agent Communication
- **FastAPI** - Toolbox servers and web endpoints
- **Gemini 2.5 Flash** - Language model
- **MCP** - Model Context Protocol for tool integration

## License

[Add your license here]

## Contributing

[Add contributing guidelines]
