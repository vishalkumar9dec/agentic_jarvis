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

#### Option A: CLI Interface
```bash
# Run CLI interface
python main.py
```

#### Option B: Web UI (Recommended)

**Prerequisites:**
```bash
# Terminal 1: Auth Service
cd auth
python auth_service.py

# Terminal 2: Registry Service
cd agent_registry_service
python registry_service.py

# Terminal 3: Tickets Agent
cd agents_phase2/tickets_agent
python start_tickets_agent.py

# Terminal 4: FinOps Agent
cd agents_phase2/finops_agent
python start_finops_agent.py

# Terminal 5: Oxygen Agent
cd agents_phase2/oxygen_agent
python start_oxygen_agent.py

# Terminal 6: Web UI Server
cd web_ui
python server_phase2.py
```

**Access Web UI:**
1. Open browser: `http://localhost:9999`
2. Login with demo credentials:
   - **vishal** / password123 (developer)
   - **happy** / password123 (developer)
   - **alex** / password123 (devops)
   - **admin** / admin123 (admin)

**Quick Test:**
```
Try these queries in the chat:
- "show my tickets"
- "show my courses"
- "show AWS cost"
- "show my tickets and pending exams"
```

See [Web UI Testing Guide](./docs/WEBUI_TESTING_GUIDE.md) for comprehensive testing instructions.

## Documentation

📚 **[Complete Documentation](./docs/)** - All documentation is in the `docs/` folder

**Quick Links:**
- [Quick Start Guide](./docs/QUICK_START.md) - Get started quickly
- [Product Specification](./docs/JARVIS_PRODUCT_SPEC.md) - Complete product vision
- [Phase 2 Plan](./docs/PHASE_2_PLAN.md) - JWT Authentication implementation
- [Authentication Architecture](./docs/AUTHENTICATION_ARCHITECTURE.md) - Authentication design (proposed)
- [Environment Configuration](./docs/ENVIRONMENT.md) - Configuration guide
- [Web UI Testing Guide](./docs/WEBUI_TESTING_GUIDE.md) - Web UI testing instructions ⭐

**Developer:**
- [CLAUDE.md](./CLAUDE.md) - Development guide for Claude Code
- [Toolbox Architecture](./docs/TOOLBOX_ARCHITECTURE.md) - Architecture patterns
- [Testing Guide](./docs/TESTING_GUIDE.md) - Testing documentation

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Web UI (Browser)                     │
│                   http://localhost:9999                  │
└───────────────────────────┬──────────────────────────────┘
                            │ JWT Auth
                    ┌───────▼────────┐
                    │  Auth Service  │
                    │     :9998      │
                    └────────────────┘
                            │
                    ┌───────▼────────┐
                    │ Registry Service│
                    │     :8003      │
                    └───────┬────────┘
                            │
                ┌───────────▼────────────┐
                │ Jarvis (Orchestrator)  │
                └───────────┬────────────┘
                            │
           ┌────────────────┼────────────────┐
           │                │                │
    ┌──────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
    │   Tickets   │  │   FinOps    │  │   Oxygen   │
    │   Agent     │  │   Agent     │  │   Agent    │
    │   :8080     │  │   :8081     │  │   :8082    │
    └─────────────┘  └─────────────┘  └────────────┘
```

**Ports:**
- **9999:** Web UI Server (FastAPI)
- **9998:** Authentication Service (JWT)
- **8003:** Registry Service (Sessions & History)
- **8080:** Tickets Agent (A2A)
- **8081:** FinOps Agent (A2A)
- **8082:** Oxygen Agent (A2A)

## Features

### Phase 1: Core Functionality (Completed)
- ✅ Multi-agent orchestration with Google ADK
- ✅ IT Tickets management (TicketsAgent)
- ✅ Cloud cost analytics (FinOpsAgent)
- ✅ Learning & development tracking (OxygenAgent via A2A)
- ✅ Web UI with JWT authentication
- ✅ User session management
- ✅ Context-aware user queries

### Phase 2: JWT Authentication (Completed)
- ✅ Bearer token authentication
- ✅ User-specific data access control
- ✅ Admin privileges for cross-user access
- ✅ Secure session management with Registry Service

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
