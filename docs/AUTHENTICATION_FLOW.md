# Authentication Flow in Agentic Jarvis (Phase 2)

## Overview

Phase 2 implements JWT-based authentication with user-specific data access across all agents and toolbox servers.

## Authentication Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  1. User Login (Web/CLI)                                     │
│     - User provides username/password                        │
│     - Auth Service validates credentials                     │
│     - JWT token issued (24-hour expiration)                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────────┐
│  2. Request with JWT Token                                   │
│     - User makes request with Bearer token                   │
│     - Token validated and current_user extracted             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────────┐
│  3. Root Orchestrator (Jarvis)                               │
│     - Receives current_user context                          │
│     - Routes to appropriate sub-agent                        │
│     - Passes current_user to authenticated tools             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                    ┌─────┴─────┐
                    │           │
                    v           v
┌───────────────────────────────────────┐  ┌─────────────────┐
│  4a. Toolbox Servers                  │  │ 4b. A2A Agents  │
│      (Tickets: 5001, FinOps: 5002)    │  │ (Oxygen: 8002)  │
│                                       │  │                 │
│  - Validate Bearer token              │  │ - Receive       │
│  - Extract current_user               │  │   current_user  │
│  - Inject into authenticated tools    │  │ - Filter data   │
│  - Return user-specific data          │  │   by user       │
└───────────────────────────────────────┘  └─────────────────┘
```

## Component Responsibilities

### 1. Auth Service (Port 9998)

**Location:** `auth/auth_server.py` (Task 22)

**Responsibilities:**
- Validate username/password against user database
- Generate JWT tokens with user_id and username
- Return user info and token

**Endpoints:**
- `POST /auth/login` - Authenticate and get JWT token

**Example:**
```bash
curl -X POST http://localhost:9998/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "vishal", "password": "password123"}'

# Response:
{
  "success": true,
  "token": "eyJhbGc...",
  "user": {
    "user_id": "user_001",
    "username": "vishal",
    "role": "developer",
    "email": "vishal@company.com"
  }
}
```

### 2. JWT Utilities

**Location:** `auth/jwt_utils.py`

**Functions:**
- `create_jwt_token(username, user_id)` - Create JWT with 24h expiration
- `verify_jwt_token(token)` - Validate and decode JWT
- `extract_user_from_token(token)` - Get username from valid token

### 3. User Service

**Location:** `auth/user_service.py`

**Functions:**
- `authenticate_user(username, password)` - Validate credentials
- `get_user_info(username)` - Get user details
- `get_user_by_id(user_id)` - Lookup by ID

**Mock Users:**
- `vishal` / `password123` (developer)
- `alex` / `password123` (devops)
- `sarah` / `password123` (data_scientist)

### 4. Toolbox Servers

**Tickets Server (Port 5001):** `toolbox_servers/tickets_server/server.py`

**Authentication:**
- `get_current_user(authorization)` dependency extracts user from Bearer token
- `AUTHENTICATED_TOOLS` set defines which tools require auth

**Tools:**
```python
# No authentication required
get_all_tickets()        # Returns all tickets
get_ticket(ticket_id)    # Returns specific ticket
get_user_tickets(username)  # Returns tickets for specified user
create_ticket(operation, user)  # Creates ticket for specified user

# Authentication required
get_my_tickets(current_user)  # Returns tickets for authenticated user
create_my_ticket(operation, current_user)  # Creates ticket for authenticated user
```

**FinOps Server (Port 5002):** `toolbox_servers/finops_server/server.py`

**Authentication:**
- Same pattern as Tickets server
- Currently no authenticated tools (costs are organization-wide)
- Infrastructure ready for future user-specific cost features

### 5. Oxygen A2A Agent

**Location:** `remote_agent/oxygen_agent/`

**Tools:**
```python
# Original tools (require username parameter)
get_user_courses(username)
get_pending_exams(username)
get_user_preferences(username)
get_learning_summary(username)

# Authenticated tools (require current_user from JWT)
get_my_courses(current_user)
get_my_exams(current_user)
get_my_preferences(current_user)
get_my_learning_summary(current_user)
```

### 6. Root Orchestrator (Jarvis)

**Location:** `jarvis_agent/agent.py`

**Responsibilities:**
- Receive current_user context from web/CLI layer
- Route queries to appropriate sub-agents
- Use authenticated tools when user context available
- Fall back to general tools when no authentication

**Tool Selection Strategy:**
- **With authentication:** Use `get_my_tickets`, `get_my_courses`, etc.
- **Without authentication:** Use `get_all_tickets`, `get_user_courses(username)`, etc.

## Request Flow Examples

### Example 1: Authenticated Request (Web UI)

```
1. User logs in via /login
   → Auth service validates credentials
   → JWT token returned and stored in browser

2. User asks: "What are my tickets?"
   → Web server extracts current_user from JWT
   → Passes current_user to Jarvis root orchestrator
   → Jarvis calls get_my_tickets(current_user="vishal")
   → Tickets server validates token, returns vishal's tickets

3. Response: "You have 2 tickets: #12301 (pending) and #12303 (in_progress)"
```

### Example 2: Unauthenticated Request (Dev UI)

```
1. User opens /dev-ui (no login required)

2. User asks: "Show tickets for alex"
   → No JWT token (dev mode)
   → Jarvis calls get_user_tickets(username="alex")
   → Tickets server returns alex's tickets (no auth check on this tool)

3. Response: "Alex has 2 tickets: ..."
```

### Example 3: Authentication Failure

```
1. User tries to access authenticated endpoint without token
   → Web server: 401 Unauthorized

2. User tries to access authenticated tool with invalid token
   → Toolbox server: 401 Unauthorized
   → Error: "Authentication required for this tool"
```

## Security Considerations

### Token Security
- JWT tokens expire after 24 hours
- Tokens are signed with JWT_SECRET_KEY
- Tokens include: username, user_id, issued_at, expires_at

### Password Security
- Passwords hashed with SHA256 (mock implementation)
- Production: Use bcrypt or argon2

### Tool Security
- Authenticated tools reject requests without valid tokens
- Tools validate current_user parameter
- User data filtered by authenticated user

### Transport Security
- Production: Use HTTPS for all endpoints
- Development: HTTP on localhost

## Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Service Ports
AUTH_SERVICE_PORT=9998
TICKETS_SERVER_PORT=5001
FINOPS_SERVER_PORT=5002
OXYGEN_AGENT_PORT=8002
WEB_UI_PORT=9999
```

## Testing Authentication

### 1. Test JWT Utilities
```bash
python auth/jwt_utils.py
python auth/user_service.py
python auth/test_auth_flow.py
```

### 2. Test Toolbox Authentication
```bash
# Start servers
python -m uvicorn toolbox_servers.tickets_server.server:app --port 5001 &
python -m uvicorn toolbox_servers.finops_server.server:app --port 5002 &

# Run tests
python test_toolbox_auth.py
```

### 3. Test Oxygen Authentication
```bash
python test_oxygen_auth.py
```

### 4. End-to-End Test (Task 27)
```bash
# Start all services
./scripts/restart_all.sh

# Run comprehensive tests
python test_phase2_e2e.py
```

## Phase 3: Persistent Sessions

In Phase 3, authentication will be enhanced with:
- Session persistence across logins
- Chat history stored per user
- "Continue where you left off" functionality
- Long-term memory with Vector DB
- Proactive notifications based on user context

## Troubleshooting

### Token Validation Fails
- Check JWT_SECRET_KEY matches across services
- Verify token hasn't expired
- Ensure Authorization header format: `Bearer <token>`

### Authenticated Tools Return 401
- Verify tool is listed in AUTHENTICATED_TOOLS set
- Check token is valid and not expired
- Ensure current_user is being injected correctly

### User Not Found
- Check username is in LEARNING_DB (Oxygen) or USERS_DB (Auth)
- Verify username casing (system uses lowercase)

## References

- **Phase 2 Plan:** `PHASE_2_PLAN.md`
- **Phase 2 Summary:** `PHASE_2_SUMMARY.md`
- **Phase 2 vs Phase 3:** `PHASE_2_VS_PHASE_3.md`
- **JWT Documentation:** https://jwt.io/introduction
- **ADK Documentation:** https://cloud.google.com/agent-development-kit
