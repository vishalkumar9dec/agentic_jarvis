# Agent Registry Persistence - Implementation Task Prompts

**Based on**: AGENT_REGISTRY_PERSISTENCE_SPEC.md v1.0.0
**Status**: Ready for implementation after spec approval
**Workflow**: Copy each task prompt → Paste to Claude → Review & commit

---

## Quick Start Guide

1. **Review** the main specification: `AGENT_REGISTRY_PERSISTENCE_SPEC.md`
2. **Approve** architecture and design decisions
3. **Execute** tasks in order (some can be parallelized)
4. **Test** after each phase
5. **Deploy** after Phase 4 completion

---

## Phase 1: Core Persistence (Days 1-2)

### Task 1.1: Implement File Storage System

**Prompt for Claude:**
```
I need to implement a file-based persistence system for the agent registry.

Requirements:
1. Create agent_registry_service/registry/file_store.py
2. Implement FileStore class with:
   - save(registry_data: Dict) -> bool: Save registry to JSON file with atomic writes
   - load() -> Dict: Load registry from JSON file with validation
   - backup() -> bool: Create backup before modifications
   - restore_from_backup() -> bool: Restore from last backup
3. Use atomic writes (write to temp file, then rename)
4. Thread-safe operations using threading.Lock
5. Handle corrupted files gracefully (try backup, then create new)
6. JSON schema validation on load

File format should be:
{
  "version": "1.0.0",
  "last_updated": "ISO timestamp",
  "agents": {...}
}

Default path: agent_registry_service/data/registry_config.json

Include comprehensive error handling and logging.
Write unit tests in tests/test_file_store.py for:
- Save and load
- Atomic writes
- Backup and restore
- Corrupted file handling
- Concurrent access

Let's implement this step by step.
```

**Acceptance Criteria:**
- [ ] FileStore class implemented
- [ ] Atomic writes working (no partial writes)
- [ ] Backup created before each save
- [ ] Corrupted file recovery works
- [ ] All unit tests pass
- [ ] Thread-safe verified

**Files Created:**
- `agent_registry_service/registry/file_store.py`
- `agent_registry_service/tests/test_file_store.py`

---

### Task 1.2: Implement Agent Factory Resolver

**Prompt for Claude:**
```
I need to implement an agent factory resolver that can recreate LlmAgent instances from configuration.

Problem: LlmAgent instances can't be serialized to JSON. We need to store factory function references and recreate agents on load.

Requirements:
1. Create agent_registry_service/registry/agent_factory_resolver.py
2. Implement AgentFactoryResolver class with:
   - create_agent(agent_config: Dict) -> LlmAgent
   - register_factory(agent_type: str, factory_func: Callable)
   - list_available_factories() -> List[str]

3. agent_config format:
{
  "agent_type": "tickets",
  "factory_module": "jarvis_agent.mcp_agents.agent_factory",
  "factory_function": "create_tickets_agent",
  "factory_params": {}  // Optional parameters
}

4. Use importlib to dynamically import modules
5. Use getattr to resolve factory functions
6. Handle import errors and missing functions gracefully
7. Cache imported modules for performance

Write unit tests in tests/test_factory_resolver.py for:
- Successful agent creation
- Invalid module handling
- Invalid function handling
- Factory with parameters
- Module caching

Let's implement this.
```

**Acceptance Criteria:**
- [ ] AgentFactoryResolver implemented
- [ ] Dynamic import working
- [ ] Error handling for missing modules/functions
- [ ] Module caching implemented
- [ ] All unit tests pass

**Files Created:**
- `agent_registry_service/registry/agent_factory_resolver.py`
- `agent_registry_service/tests/test_factory_resolver.py`

---

### Task 1.3: Enhance AgentRegistry with Persistence

**Prompt for Claude:**
```
I need to enhance the existing AgentRegistry class with persistence capabilities.

Current code: jarvis_agent/agent_registry.py
Move to: agent_registry_service/registry/agent_registry.py

Requirements:
1. Create PersistentAgentRegistry(AgentRegistry) that extends the base class
2. Add FileStore and AgentFactoryResolver dependencies
3. Implement:
   - _persist(): Save current state to file after any modification
   - _load_from_file(): Load registry state from file on startup
   - _serialize_registry() -> Dict: Convert registry to JSON format
   - _deserialize_registry(data: Dict): Rebuild registry from JSON

4. Override these methods to auto-persist:
   - register(agent, capabilities, tags)
   - unregister(agent_name)
   - update_capabilities(agent_name, capabilities) [NEW METHOD]
   - enable_agent(agent_name)
   - disable_agent(agent_name)

5. Serialization format (only store metadata, not agent instances):
{
  "agents": {
    "tickets_agent": {
      "name": "tickets_agent",
      "description": "...",
      "agent_type": "tickets",
      "factory_module": "jarvis_agent.mcp_agents.agent_factory",
      "factory_function": "create_tickets_agent",
      "capabilities": {...},
      "tags": ["production"],
      "enabled": true,
      "registered_at": "ISO timestamp"
    }
  }
}

6. On load:
   - Read JSON file
   - For each agent config:
     - Use AgentFactoryResolver to recreate LlmAgent instance
     - Register in memory with saved capabilities/tags/enabled status

7. Add rollback on failure (restore from backup if persist fails)

Write unit tests in tests/test_persistent_registry.py for:
- Persist and reload
- Agent recreation from factory
- Update capabilities and persist
- Rollback on error
- Enable/disable persistence

Let's implement this carefully.
```

**Acceptance Criteria:**
- [ ] PersistentAgentRegistry implemented
- [ ] Auto-persist on all modifications
- [ ] Serialization/deserialization working
- [ ] Agent recreation from config working
- [ ] Rollback on failure implemented
- [ ] All unit tests pass

**Files Created:**
- `agent_registry_service/registry/agent_registry.py` (moved + enhanced)
- `agent_registry_service/tests/test_persistent_registry.py`

---

## Phase 2: Session Management (Days 2-3)

### Task 2.1: Create SQLite Database Schema

**Prompt for Claude:**
```
I need to create a SQLite database schema for session management.

Requirements:
1. Create agent_registry_service/sessions/schema.sql with tables:

   - sessions: Store session metadata
     - session_id TEXT PRIMARY KEY
     - user_id TEXT NOT NULL
     - created_at TIMESTAMP
     - updated_at TIMESTAMP
     - status TEXT (active, completed, expired)
     - metadata TEXT (JSON blob)

   - conversation_history: Store all messages
     - id INTEGER PRIMARY KEY AUTOINCREMENT
     - session_id TEXT FOREIGN KEY
     - role TEXT (user, assistant, system)
     - content TEXT
     - timestamp TIMESTAMP

   - agent_invocations: Track which agents were called
     - id INTEGER PRIMARY KEY AUTOINCREMENT
     - session_id TEXT FOREIGN KEY
     - agent_name TEXT
     - query TEXT
     - response TEXT
     - success BOOLEAN
     - error_message TEXT
     - duration_ms INTEGER
     - timestamp TIMESTAMP

   - session_context: Track last agent called for context continuity
     - session_id TEXT PRIMARY KEY FOREIGN KEY
     - last_agent_called TEXT
     - last_query TEXT
     - last_response TEXT
     - updated_at TIMESTAMP

2. Add appropriate indexes for performance:
   - idx_sessions_user on sessions(user_id)
   - idx_sessions_created on sessions(created_at)
   - idx_history_session on conversation_history(session_id)
   - idx_invocations_session on agent_invocations(session_id)
   - idx_invocations_agent on agent_invocations(agent_name)

3. Add CASCADE deletes for foreign keys

4. Create agent_registry_service/sessions/db_init.py to initialize database

Let's create this schema.
```

**Acceptance Criteria:**
- [ ] schema.sql created with all tables
- [ ] Indexes added for performance
- [ ] Foreign keys with CASCADE
- [ ] db_init.py can create database
- [ ] Schema validated with SQLite

**Files Created:**
- `agent_registry_service/sessions/schema.sql`
- `agent_registry_service/sessions/db_init.py`

---

### Task 2.2: Implement SessionManager

**Prompt for Claude:**
```
I need to implement a SessionManager for SQLite-based session persistence.

Requirements:
1. Create agent_registry_service/sessions/session_manager.py
2. Implement SessionManager class with:
   - __init__(db_path: str): Initialize SQLite connection
   - create_session(user_id: str) -> str: Create new session, return session_id
   - get_session(session_id: str) -> Optional[Dict]: Get full session data
   - update_session_status(session_id: str, status: str)
   - track_agent_invocation(session_id, agent_name, query, response, success, duration_ms)
   - add_to_history(session_id: str, role: str, content: str)
   - get_conversation_history(session_id: str) -> List[Dict]
   - get_agent_invocations(session_id: str) -> List[Dict]
   - update_context(session_id, last_agent, last_query, last_response)
   - get_context(session_id: str) -> Dict
   - cleanup_old_sessions(days: int = 7): Delete old completed sessions

3. Use connection pooling or check_same_thread=False for multi-threaded access
4. Add proper error handling and logging
5. Return data in format:
{
  "session_id": "abc123",
  "user_id": "alice",
  "created_at": "...",
  "status": "active",
  "conversation_history": [
    {"role": "user", "content": "...", "timestamp": "..."}
  ],
  "agents_invoked": [
    {"agent_name": "tickets_agent", "query": "...", "success": true, "timestamp": "..."}
  ],
  "last_agent_called": "tickets_agent"
}

Write unit tests in tests/test_session_manager.py for:
- Create and retrieve session
- Track invocations
- Conversation history
- Context tracking
- Session cleanup
- Concurrent access

Let's implement this.
```

**Acceptance Criteria:**
- [ ] SessionManager implemented
- [ ] All CRUD operations working
- [ ] Thread-safe database access
- [ ] Cleanup function working
- [ ] All unit tests pass

**Files Created:**
- `agent_registry_service/sessions/session_manager.py`
- `agent_registry_service/tests/test_session_manager.py`

---

## Phase 3: REST API (Days 3-4)

### Task 3.1: Implement Registry REST API

**Prompt for Claude:**
```
I need to implement REST API endpoints for agent registry management using FastAPI.

Requirements:
1. Create agent_registry_service/api/registry_routes.py
2. Use FastAPI router with prefix="/registry"
3. Implement endpoints:

   GET /registry/agents
   - List all agents
   - Query params: enabled_only (bool), tags (comma-separated)
   - Response: {"agents": [...], "total": int}

   GET /registry/agents/{agent_name}
   - Get specific agent details
   - Response: {agent metadata + capabilities}

   POST /registry/agents
   - Register new agent
   - Body: {agent_type, factory_module, factory_function, capabilities, tags}
   - Response: {"status": "registered", "agent_name": "..."}

   PUT /registry/agents/{agent_name}/capabilities
   - Update agent capabilities
   - Body: {"capabilities": {...}}
   - Response: {"status": "updated"}

   PATCH /registry/agents/{agent_name}/status
   - Enable/disable agent
   - Body: {"enabled": true/false}
   - Response: {"status": "enabled"/"disabled"}

   DELETE /registry/agents/{agent_name}
   - Delete agent
   - Response: {"status": "deleted"}

   GET /registry/export
   - Export full registry as JSON
   - Response: {full registry data}

4. Use Pydantic models for request/response validation
5. Add proper error handling (404, 400, 500)
6. Add OpenAPI documentation with examples
7. Inject PersistentAgentRegistry as dependency

Write integration tests in tests/test_registry_api.py using TestClient.

Let's implement this API.
```

**Acceptance Criteria:**
- [ ] All endpoints implemented
- [ ] Pydantic validation working
- [ ] Error handling comprehensive
- [ ] OpenAPI docs generated
- [ ] Integration tests pass

**Files Created:**
- `agent_registry_service/api/registry_routes.py`
- `agent_registry_service/api/models.py` (Pydantic models)
- `agent_registry_service/tests/test_registry_api.py`

---

### Task 3.2: Implement Session REST API

**Prompt for Claude:**
```
I need to implement REST API endpoints for session management using FastAPI.

Requirements:
1. Create agent_registry_service/api/session_routes.py
2. Use FastAPI router with prefix="/sessions"
3. Implement endpoints:

   POST /sessions
   - Create new session
   - Body: {"user_id": "alice"}
   - Response: {"session_id": "..."}

   GET /sessions/{session_id}
   - Get full session data
   - Response: {session, conversation_history, agents_invoked, context}

   POST /sessions/{session_id}/invocations
   - Track agent invocation
   - Body: {agent_name, query, response, success, duration_ms}
   - Response: {"status": "tracked"}

   POST /sessions/{session_id}/history
   - Add message to conversation
   - Body: {role, content}
   - Response: {"status": "added"}

   PATCH /sessions/{session_id}/status
   - Update session status
   - Body: {"status": "completed"}
   - Response: {"status": "updated"}

   DELETE /sessions/{session_id}
   - Delete session
   - Response: {"status": "deleted"}

4. Use Pydantic models for validation
5. Error handling for invalid session_id
6. Inject SessionManager as dependency

Write integration tests in tests/test_session_api.py.

Let's implement this.
```

**Acceptance Criteria:**
- [ ] All endpoints implemented
- [ ] Pydantic validation working
- [ ] Error handling for invalid sessions
- [ ] Integration tests pass

**Files Created:**
- `agent_registry_service/api/session_routes.py`
- `agent_registry_service/tests/test_session_api.py`

---

### Task 3.3: Create Main FastAPI Application

**Prompt for Claude:**
```
I need to create the main FastAPI application that ties everything together.

Requirements:
1. Create agent_registry_service/app.py
2. Initialize FastAPI app with metadata
3. Include routers:
   - registry_routes (prefix="/registry")
   - session_routes (prefix="/sessions")
4. Add endpoints:
   - GET /health: Health check
   - GET /: Service info and links to docs
5. Add startup event to:
   - Initialize PersistentAgentRegistry
   - Load registry from file
   - Initialize SessionManager
   - Initialize database schema
   - Log startup info
6. Add shutdown event to:
   - Close database connections
   - Final registry save
7. Add middleware:
   - CORS (for web UI)
   - Request logging
   - Error handling
8. Configure OpenAPI docs at /docs

Create requirements.txt with:
- fastapi
- uvicorn[standard]
- pydantic
- google-adk
- google-generativeai

Let's implement the main app.
```

**Acceptance Criteria:**
- [ ] FastAPI app configured
- [ ] All routers included
- [ ] Startup/shutdown events working
- [ ] Health endpoint working
- [ ] OpenAPI docs accessible
- [ ] requirements.txt complete

**Files Created:**
- `agent_registry_service/app.py`
- `agent_registry_service/requirements.txt`

---

## Phase 4: Integration & Deployment (Days 4-5)

### Task 4.1: Create Dockerfile

**Prompt for Claude:**
```
I need to create a Dockerfile for the Agent Registry Service.

Requirements:
1. Create agent_registry_service/Dockerfile
2. Base image: python:3.11-slim
3. Create /app/data directory for persistent storage
4. Install dependencies from requirements.txt
5. Copy application code
6. Expose port 8003
7. Use uvicorn to run app
8. Add healthcheck using curl
9. Run as non-root user for security
10. Use multi-stage build for smaller image size

Also create:
- docker-compose.yml for easy local development
- .dockerignore to exclude unnecessary files

Let's create the Docker setup.
```

**Acceptance Criteria:**
- [ ] Dockerfile builds successfully
- [ ] Image size reasonable (<500MB)
- [ ] Healthcheck working
- [ ] Non-root user configured
- [ ] docker-compose.yml working

**Files Created:**
- `agent_registry_service/Dockerfile`
- `agent_registry_service/docker-compose.yml`
- `agent_registry_service/.dockerignore`

---

### Task 4.2: Create Startup Script

**Prompt for Claude:**
```
I need to create a startup script for the agent registry service.

Requirements:
1. Create scripts/start_registry_service.sh
2. Check if port 8003 is already in use (kill if needed)
3. Create data directory if it doesn't exist
4. Check for GOOGLE_API_KEY environment variable
5. Option to run in Docker or locally
6. Support for --reload flag for development
7. Log output to both console and file

Usage:
  ./scripts/start_registry_service.sh         # Local mode
  ./scripts/start_registry_service.sh --docker # Docker mode
  ./scripts/start_registry_service.sh --reload # Development mode

Let's create this script.
```

**Acceptance Criteria:**
- [ ] Script handles port conflicts
- [ ] Creates necessary directories
- [ ] Environment checks working
- [ ] Both local and Docker modes work
- [ ] Logging configured

**Files Created:**
- `scripts/start_registry_service.sh`
- `scripts/stop_registry_service.sh`

---

### Task 4.3: Update Jarvis Orchestrator Integration

**Prompt for Claude:**
```
I need to update the Jarvis orchestrator to use the new Agent Registry Service.

Requirements:
1. Create jarvis_agent/registry_client.py - HTTP client for registry service
   - list_agents()
   - get_agent(agent_name)
   - (Admin methods: register_agent, update_agent, delete_agent)

2. Update jarvis_agent/dynamic_router.py:
   - Replace in-memory AgentRegistry with RegistryClient
   - Fetch agents from registry service instead of local dict
   - Keep TwoStageRouter logic the same

3. Update main_mcp_auth.py or create new main_with_registry.py:
   - Initialize RegistryClient(base_url="http://localhost:8003")
   - Initialize SessionManager client
   - On user query:
     a. Create/resume session
     b. Route query using dynamic router
     c. Invoke selected agents
     d. Track invocations in SessionManager
     e. Add to conversation history
     f. Return combined response

4. Create migration script: scripts/migrate_to_registry_service.py
   - Register existing agents (tickets, finops, oxygen) via API
   - Validate registration
   - Test routing

Let's implement these integrations step by step.
```

**Acceptance Criteria:**
- [ ] RegistryClient implemented
- [ ] DynamicRouter updated to use client
- [ ] Jarvis orchestrator integrated
- [ ] Session tracking working
- [ ] Migration script successful

**Files Created:**
- `jarvis_agent/registry_client.py`
- `jarvis_agent/session_client.py`
- `jarvis_agent/main_with_registry.py`
- `scripts/migrate_to_registry_service.py`

---

## Phase 5: Testing & Documentation (Day 5)

### Task 5.1: Integration Tests

**Prompt for Claude:**
```
I need comprehensive integration tests for the complete system.

Requirements:
1. Create agent_registry_service/tests/test_integration.py
2. Test scenarios:

   test_full_startup_flow():
   - Start registry service
   - Load default agents from config
   - Verify agents registered
   - Verify database initialized

   test_agent_lifecycle():
   - Register new agent via API
   - Update capabilities
   - Disable agent
   - Re-enable agent
   - Delete agent
   - Verify persistence across service restart

   test_session_lifecycle():
   - Create session
   - Add conversation history
   - Track multiple agent invocations
   - Get session data
   - Verify all data persisted

   test_query_routing_with_session():
   - Create session
   - Route query "show my tickets"
   - Mock agent invocation
   - Track invocation
   - Route follow-up query "show details"
   - Verify context used for routing

   test_concurrent_sessions():
   - Create 10 concurrent sessions
   - Each makes 5 queries
   - Verify no data corruption
   - Verify correct session isolation

   test_failure_recovery():
   - Corrupt registry file
   - Verify recovery from backup
   - Corrupt database
   - Verify recreation

3. Use pytest fixtures for setup/teardown
4. Mock external dependencies (LLM calls)
5. Use temporary directories for test data

Let's write comprehensive integration tests.
```

**Acceptance Criteria:**
- [ ] All integration tests pass
- [ ] Coverage >90%
- [ ] Concurrent access tested
- [ ] Failure scenarios covered

**Files Created:**
- `agent_registry_service/tests/test_integration.py`
- `agent_registry_service/tests/conftest.py` (pytest fixtures)

---

### Task 5.2: API Documentation

**Prompt for Claude:**
```
I need comprehensive API documentation for the registry service.

Requirements:
1. Create docs/AGENT_REGISTRY_API.md
2. Document all endpoints with:
   - HTTP method and path
   - Description
   - Request parameters/body (with examples)
   - Response format (with examples)
   - Error codes and meanings
   - cURL examples

3. Add usage examples:
   - Registering a new agent
   - Updating capabilities
   - Creating and managing sessions
   - Querying agent invocations

4. Add architecture diagram
5. Add troubleshooting section

Let's create comprehensive API documentation.
```

**Acceptance Criteria:**
- [ ] All endpoints documented
- [ ] Examples provided for each
- [ ] Error codes documented
- [ ] Troubleshooting guide included

**Files Created:**
- `docs/AGENT_REGISTRY_API.md`

---

### Task 5.3: Performance Testing

**Prompt for Claude:**
```
I need to verify the system meets performance requirements.

Requirements:
1. Create agent_registry_service/tests/test_performance.py
2. Test scenarios:

   test_registry_with_100_agents():
   - Register 100 agents
   - Measure registration time
   - Measure query routing time
   - Assert: routing < 500ms per query

   test_file_save_performance():
   - Save registry with 100 agents
   - Measure save time
   - Assert: save < 100ms

   test_session_query_performance():
   - Create session with 1000 messages
   - Query full session
   - Assert: query < 200ms

   test_concurrent_routing():
   - 50 concurrent route requests
   - Measure throughput (queries/sec)
   - Verify no deadlocks

3. Use pytest-benchmark for measurements
4. Generate performance report

Let's create performance tests.
```

**Acceptance Criteria:**
- [ ] Performance tests pass
- [ ] Routing <500ms for 100 agents
- [ ] File save <100ms
- [ ] Session query <200ms
- [ ] Concurrent access working

**Files Created:**
- `agent_registry_service/tests/test_performance.py`

---

## Validation Checklist

After all tasks complete, validate:

### Functional Requirements
- [ ] Registry persists to file and survives restarts
- [ ] Agents can be registered/updated/deleted via API
- [ ] Sessions persist to SQLite with full history
- [ ] Agent invocations tracked per session
- [ ] Query routing works with 100+ agents
- [ ] Multi-user concurrent sessions work

### Non-Functional Requirements
- [ ] Performance: <500ms routing for 100 agents
- [ ] Docker deployment works
- [ ] All tests pass (unit + integration + performance)
- [ ] Test coverage >90%
- [ ] API documentation complete
- [ ] Error handling comprehensive

### Production Readiness
- [ ] Logging configured
- [ ] Healthcheck endpoint working
- [ ] Backup/restore working
- [ ] Failure recovery tested
- [ ] Security: No hardcoded secrets
- [ ] Database migrations documented

---

## Deployment Steps

```bash
# 1. Build and start registry service
cd agent_registry_service
docker build -t agent-registry:1.0.0 .
docker run -d -p 8003:8003 -v $(pwd)/data:/app/data --name agent-registry agent-registry:1.0.0

# 2. Verify health
curl http://localhost:8003/health

# 3. Register default agents
python ../scripts/migrate_to_registry_service.py

# 4. Verify registration
curl http://localhost:8003/registry/agents

# 5. Start Jarvis with registry integration
cd ..
python jarvis_agent/main_with_registry.py

# 6. Test end-to-end
curl -X POST http://localhost:9999/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "message": "show my tickets"}'
```

---

## Troubleshooting Common Issues

### Issue: Port 8003 already in use
```bash
lsof -ti:8003 | xargs kill -9
```

### Issue: Database locked
```bash
rm agent_registry_service/data/sessions.db
# Will be recreated on startup
```

### Issue: Registry file corrupted
```bash
cp agent_registry_service/data/registry_config.json.backup \
   agent_registry_service/data/registry_config.json
```

### Issue: Agent factory import fails
```bash
# Check PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:/Users/vishalkumar/projects/agentic_jarvis"
```

---

## Success Metrics

After completion, you should have:

✅ Persistent agent registry (survives restarts)
✅ SQLite session management with full history
✅ REST API for all CRUD operations
✅ Docker deployment ready
✅ Comprehensive tests with >90% coverage
✅ Complete API documentation
✅ Production-ready error handling

**Total Effort**: ~51-71 hours (~2-3 weeks)
**Complexity**: Medium-High
**Risk Level**: Low (with good testing)

---

**Ready to start? Get approval on the spec, then execute tasks in order!**
