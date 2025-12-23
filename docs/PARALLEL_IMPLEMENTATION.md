# Parallel Implementation Strategy

## Overview

Agentic Jarvis will have **TWO independent solutions running side-by-side**:

1. **Current Agentic Solution** (Toolbox pattern) - Unchanged
2. **New MCP Solution** (MCP protocol) - New implementation

This allows for:
- ✅ Direct comparison between approaches
- ✅ Zero risk to existing working system
- ✅ Easy rollback if MCP has issues
- ✅ Gradual validation and migration when ready

## Port Allocation

### Current Solution Ports (Unchanged)
| Service | Port | Status |
|---------|------|--------|
| Tickets Toolbox | 5001 | Keep as-is |
| FinOps Toolbox | 5002 | Keep as-is |
| Oxygen A2A Agent | 8002 | Keep as-is |
| Auth Service | 9998 | Shared (both solutions use same auth) |
| Web UI (Current) | 9999 | Keep as-is |

### New MCP Solution Ports
| Service | Port | Status |
|---------|------|--------|
| Tickets MCP Server | 5011 | New |
| FinOps MCP Server | 5012 | New |
| Oxygen MCP Server | 8012 | New |
| Auth Service | 9998 | Shared |
| Web UI (MCP) | 9990 | New |

**Different ports = Zero conflicts = Both run simultaneously**

## Directory Structure

```
agentic_jarvis/
│
├── # ============================================
├── # CURRENT SOLUTION (Unchanged)
├── # ============================================
│
├── tickets_toolbox/                  # Port 5001 (Keep)
│   ├── __init__.py
│   ├── server.py
│   └── tools.py
│
├── finops_toolbox/                   # Port 5002 (Keep)
│   ├── __init__.py
│   ├── server.py
│   └── tools.py
│
├── oxygen_agent/                     # Port 8002 (Keep)
│   ├── __init__.py
│   ├── agent.py
│   └── tools.py
│
├── jarvis_agent/
│   ├── agent.py                      # Root orchestrator (current)
│   ├── auth_context.py               # Context vars (current approach)
│   └── sub_agents/
│       ├── tickets/
│       │   └── agent.py              # Module-level agent (current)
│       ├── finops/
│       │   └── agent.py              # Module-level agent (current)
│       └── oxygen/
│           └── agent.py              # Module-level agent (current)
│
├── web_ui/
│   └── server.py                     # Port 9999 (current web UI)
│
├── main.py                           # Current CLI entry point
│
├── # ============================================
├── # NEW MCP SOLUTION (New files only)
├── # ============================================
│
├── tickets_mcp_server/               # Port 5011 (NEW)
│   ├── __init__.py
│   ├── server.py                     # FastMCP tool definitions
│   ├── app.py                        # FastAPI mounting
│   └── tools.py                      # Tool implementations
│
├── finops_mcp_server/                # Port 5012 (NEW)
│   ├── __init__.py
│   ├── server.py                     # FastMCP tool definitions
│   ├── app.py                        # FastAPI mounting
│   └── tools.py                      # Tool implementations
│
├── oxygen_mcp_server/                # Port 8012 (NEW)
│   ├── __init__.py
│   ├── server.py                     # FastMCP tool definitions
│   ├── app.py                        # FastAPI mounting
│   └── tools.py                      # Tool implementations
│
├── jarvis_agent/
│   └── mcp_agents/                   # NEW folder for MCP agents
│       ├── __init__.py
│       ├── agent_factory.py          # Root orchestrator factory
│       ├── tickets_agent.py          # create_tickets_agent(token)
│       ├── finops_agent.py           # create_finops_agent(token)
│       └── oxygen_agent.py           # create_oxygen_agent(token)
│
├── web_ui/
│   └── server_mcp.py                 # Port 9990 (NEW web UI for MCP)
│
├── main_mcp.py                       # NEW CLI entry point for MCP
│
├── # ============================================
├── # SHARED (Both solutions use)
├── # ============================================
│
├── auth/                             # Shared auth service
│   ├── __init__.py
│   ├── auth_server.py                # Port 9998 (shared)
│   ├── jwt_utils.py                  # Shared JWT functions
│   └── user_service.py               # Shared user database
│
├── scripts/
│   ├── # Current solution scripts (unchanged)
│   ├── start_tickets_server.sh       # Port 5001
│   ├── start_finops_server.sh        # Port 5002
│   ├── start_oxygen_agent.sh         # Port 8002
│   ├── start_web.sh                  # Port 9999
│   ├── restart_all_phase2.sh         # Current solution
│   │
│   ├── # New MCP solution scripts
│   ├── start_tickets_mcp_server.sh   # Port 5011 (NEW)
│   ├── start_finops_mcp_server.sh    # Port 5012 (NEW)
│   ├── start_oxygen_mcp_server.sh    # Port 8012 (NEW)
│   ├── start_web_mcp.sh              # Port 9990 (NEW)
│   └── restart_all_mcp.sh            # NEW - Start all MCP services
│
└── tests/
    ├── # Current solution tests (unchanged)
    ├── test_phase2_e2e.py
    ├── test_web_ui_auth.py
    │
    ├── # New MCP solution tests
    ├── test_mcp_tickets_server.py    # NEW
    ├── test_mcp_finops_server.py     # NEW
    ├── test_mcp_oxygen_server.py     # NEW
    ├── test_mcp_integration.py       # NEW
    └── test_mcp_e2e.py               # NEW
```

## Running Both Solutions Simultaneously

### Terminal Setup

**Current Solution** (5 terminals):
```bash
# Terminal 1: Auth Service (shared)
./scripts/start_auth_service.sh         # Port 9998

# Terminal 2-4: Current toolbox servers
./scripts/start_tickets_server.sh       # Port 5001
./scripts/start_finops_server.sh        # Port 5002
./scripts/start_oxygen_agent.sh         # Port 8002

# Terminal 5: Current Web UI
./scripts/start_web.sh                  # Port 9999
```

**MCP Solution** (4 additional terminals):
```bash
# Terminal 6-8: MCP servers
./scripts/start_tickets_mcp_server.sh   # Port 5011
./scripts/start_finops_mcp_server.sh    # Port 5012
./scripts/start_oxygen_mcp_server.sh    # Port 8012

# Terminal 9: MCP Web UI
./scripts/start_web_mcp.sh              # Port 9990
```

Or use the all-in-one scripts:
```bash
# Start current solution
./scripts/restart_all_phase2.sh

# Start MCP solution (in separate terminal)
./scripts/restart_all_mcp.sh
```

## Comparison Testing

### Test Current Solution
```bash
# CLI
python main.py

# Web UI
open http://localhost:9999
```

### Test MCP Solution
```bash
# CLI
python main_mcp.py

# Web UI
open http://localhost:9990
```

## Authentication Flow

Both solutions share the **same auth service** (port 9998):

```
User → Login → Auth Service (9998) → JWT Token
  ↓
  ├─→ Current Web UI (9999) → Toolbox (5001, 5002, 8002)
  │   Status: Has auth bug (tokens don't reach servers)
  │
  └─→ MCP Web UI (9990) → MCP Servers (5011, 5012, 8012)
      Status: Auth bug FIXED (per-request agents + header_provider)
```

**Key Point**: Same user can log in once and test both UIs with the same token.

## Implementation Strategy

### Phase 1: Build MCP (Parallel) - Weeks 1-2
1. Create all MCP servers on ports 5011, 5012, 8012
2. Create MCP agent factories
3. Create MCP CLI and Web UI
4. Test MCP solution end-to-end
5. **Current solution continues to run unchanged**

### Phase 2: Add Authentication - Week 3
1. Add JWT validation to MCP servers
2. Implement per-request agent creation
3. Test authenticated user-specific data
4. Verify auth bug is fixed

### Phase 3: Compare & Decide
1. Run both solutions side-by-side
2. Test same queries on both UIs
3. Verify MCP auth works, current auth fails
4. Performance comparison
5. Feature parity check
6. Make decision: switch to MCP or keep both

## File Changes Summary

### Files UNCHANGED (Current Solution)
```
✅ No changes to:
- tickets_toolbox/*
- finops_toolbox/*
- oxygen_agent/*
- jarvis_agent/sub_agents/*/agent.py
- jarvis_agent/agent.py
- web_ui/server.py
- main.py
- All current scripts
- All current tests
```

### Files CREATED (MCP Solution)
```
⭐ New files only:
- tickets_mcp_server/*
- finops_mcp_server/*
- oxygen_mcp_server/*
- jarvis_agent/mcp_agents/*
- web_ui/server_mcp.py
- main_mcp.py
- scripts/*_mcp_server.sh
- scripts/start_web_mcp.sh
- scripts/restart_all_mcp.sh
- tests/test_mcp_*.py
```

### Files SHARED (Both Solutions)
```
🔄 Both use:
- auth/* (same auth service)
- .env (same config, add MCP ports)
- requirements.txt (add MCP dependencies)
```

## Environment Variables

Add to `.env` (MCP-specific):

```bash
# Current solution ports (existing)
TICKETS_SERVER_PORT=5001
FINOPS_SERVER_PORT=5002
OXYGEN_AGENT_PORT=8002
WEB_UI_PORT=9999
AUTH_SERVICE_PORT=9998

# MCP solution ports (new)
TICKETS_MCP_PORT=5011
FINOPS_MCP_PORT=5012
OXYGEN_MCP_PORT=8012
WEB_UI_MCP_PORT=9990

# Shared
JWT_SECRET_KEY=your-secret-key-change-in-production
```

## Success Criteria

### Both Solutions Working
- [ ] Current solution still works (CLI + Web UI)
- [ ] MCP solution works (CLI + Web UI)
- [ ] Both can run simultaneously
- [ ] Same auth token works for both

### MCP Authentication Fixed
- [ ] "show my tickets" works in MCP Web UI
- [ ] Bearer token reaches MCP servers
- [ ] User-specific data returned correctly
- [ ] No `PermissionError` in MCP solution

### Comparison Complete
- [ ] Feature parity verified
- [ ] Performance measured
- [ ] Code complexity compared
- [ ] Decision documented (switch or keep both)

## Risk Mitigation

### Zero Risk to Current System
- ✅ Current solution files never modified
- ✅ Different ports (no conflicts)
- ✅ Independent startup scripts
- ✅ Separate test suites

### Easy Rollback
- ✅ Stop MCP servers (current continues)
- ✅ Delete MCP directories (no impact)
- ✅ Remove MCP tests (current tests work)

### Gradual Validation
- ✅ Validate one service at a time
- ✅ Compare side-by-side
- ✅ Switch when confident

---

## Confirmation

**YES, confirmed:**

1. ✅ Two independent solutions (current + MCP)
2. ✅ MCP implementation is completely separate
3. ✅ Current solution will NOT be modified
4. ✅ Different ports to avoid conflicts
5. ✅ Both can run simultaneously
6. ✅ Easy to compare and decide
7. ✅ Zero risk to existing system

---

**Status**: Parallel implementation strategy
**Created**: 2025-12-20
**Risk Level**: Zero (independent implementation)
**Reference**: See [MCP_CORRECT_IMPLEMENTATION.md](./MCP_CORRECT_IMPLEMENTATION.md) for MCP technical details
