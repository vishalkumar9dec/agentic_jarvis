# Phase 2: Authentication for Pure A2A Architecture

**Date:** 2025-12-30 (Updated: 2025-12-31)
**Architecture:** Pure A2A (all agents as self-contained services)
**Ports:** TicketsAgent:8080, FinOpsAgent:8081, OxygenAgent:8082, Registry:8003, Auth:9998
**OAuth Ready:** Yes - JWT pattern compatible with OAuth 2.0
**Auth Service:** ✅ Already 90% complete in `auth/` folder!

## 📚 Reference Documents

Before implementing, read:
- **This document** - Implementation plan and task breakdown
- **[TOKEN_PROPAGATION_GUIDE.md](./TOKEN_PROPAGATION_GUIDE.md)** - Detailed guide on how JWT tokens flow through the system (answers "how do tokens pass between agents?")

---

## 🎉 Key Update (2025-12-31)

**Good News:** The auth service is already 90% complete!

During plan review, we discovered an existing `auth/` folder with:
- ✅ FastAPI auth service on port 9998
- ✅ JWT token creation and validation
- ✅ User database (vishal, alex, sarah)
- ✅ Password hashing (SHA256)
- ✅ Login endpoint (/auth/login)

**What This Means:**
- **Reduced implementation time:** 8-11 hours (instead of 10-13 hours)
- **Task 1 simplified:** Just update JWT format to OAuth standard (1-2 hours instead of 3-4 hours)
- **No new code needed:** Update existing `auth/` folder instead of creating `auth_service/`

**Changes Needed for OAuth Compatibility:**
1. Update JWT payload to include `sub`, `iss`, `aud` claims
2. Update response format to OAuth standard (`access_token`, `token_type`, `expires_in`)
3. Add `/auth/verify` endpoint for token validation

---

## Executive Summary

Add JWT-based authentication to the existing Pure A2A architecture while maintaining OAuth 2.0 compatibility for future enterprise integration.

### Goals

1. **User Authentication** - Login with username/password, receive JWT token
2. **User Context Passing** - Agents know WHO is asking ("show my tickets" works)
3. **Data Isolation** - Each user sees only their own data
4. **Session Persistence** - History survives across logins
5. **OAuth Ready** - JWT infrastructure that OAuth 2.0 can extend

### Non-Goals (Phase 3)

- Long-term memory persistence (vector DB)
- Proactive notifications
- OAuth 2.0 integration (Phase 4)
- SSO with enterprise identity providers

---

## Current State Analysis

### What Works (Phase 1) ✅

```
Ports:
- 8080: TicketsAgent (A2A service)
- 8081: FinOpsAgent (A2A service)
- 8082: OxygenAgent (A2A service)
- 8003: Registry + Session Service

Features:
✓ Multi-agent routing (TwoStageRouterWithRegistry)
✓ Query decomposition (splits cross-agent queries)
✓ Session tracking (conversation history, agent invocations)
✓ Dynamic agent discovery (registry service)
✓ A2A protocol communication (RemoteA2aAgent)
```

### What's Missing (Phase 2) ❌

```
Problems:
✗ No authentication - anyone can claim any username
✗ No user context - agents don't know WHO is asking
✗ Session not resumed - new session on each login
✗ "show my tickets" fails - agent asks "which user?"
✗ No password validation
✗ No JWT tokens
```

---

## Architecture

### Phase 2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Authentication                      │
│                  username + password                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Auth Service :9998  │
              │  - Validate password │
              │  - Generate JWT      │
              │  - 24h expiration    │
              └──────────┬───────────┘
                         │
                         ▼ JWT Token (eyJhbGc...)
              ┌──────────────────────┐
              │   CLI / Web Client   │
              │  - Store JWT token   │
              │  - Pass in requests  │
              └──────────┬───────────┘
                         │
                         ▼ Authorization: Bearer <token>
              ┌──────────────────────────────┐
              │  Jarvis Orchestrator :8003   │
              │  - Verify JWT signature      │
              │  - Extract user_id from JWT  │
              │  - Resume/create session     │
              │  - Pass user_id to router    │
              └──────────┬───────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Tickets     │  │ FinOps      │  │ Oxygen      │
│ Agent :8080 │  │ Agent :8081 │  │ Agent :8082 │
│             │  │             │  │             │
│ Receives:   │  │ Receives:   │  │ Receives:   │
│ "show       │  │ "show aws   │  │ "show       │
│  tickets    │  │  cost"      │  │  courses    │
│  for vishal"│  │             │  │  for vishal"│
└─────────────┘  └─────────────┘  └─────────────┘
```

### Key Design Decisions

**1. JWT Over Sessions**
- **Why:** OAuth 2.0 compatible, stateless, scalable
- **Format:** `{"user_id": "vishal", "role": "developer", "exp": 1735689600}`
- **Algorithm:** HS256 (symmetric) for Phase 2, RS256 (asymmetric) for OAuth Phase 4

**2. User Context in Query Decomposition**
- **Current:** "show my tickets" → sent as-is to agent (fails)
- **Phase 2:** "show my tickets" → "show tickets for vishal" (works)
- **How:** Query decomposition includes user_id from JWT

**3. Session Resumption**
- **Current:** New session on each login
- **Phase 2:** Resume active session if exists, create new if expired
- **Expiration:** 24 hours from last activity

**4. Token Propagation to Agents**
- **Phase 2:** Jarvis validates JWT, then passes JWT to agents via session state
- **Agents receive:** JWT token in `session.state["user:bearer_token"]`
- **Agents can:** Extract user_id, check roles, pass to other agents
- **Phase 4 (OAuth):** Agents validate JWT independently (full distributed auth)
- **Rationale:** Enables agent-to-agent calls with auth context

---

## Token Propagation Flow

**📖 For detailed examples and code snippets, see [TOKEN_PROPAGATION_GUIDE.md](./TOKEN_PROPAGATION_GUIDE.md)**

This section provides a high-level overview. The guide contains:
- Complete code examples for agent-to-agent calls
- ToolContext usage patterns
- Permission checking (RBAC)
- Security considerations

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  User Login                                                      │
│  POST /auth/login {username, password}                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Auth Service :9998  │
              │  Returns JWT:        │
              │  {                   │
              │    "sub": "vishal",  │
              │    "role": "dev",    │
              │    "permissions": [] │
              │  }                   │
              └──────────┬───────────┘
                         │
                         ▼ JWT stored in CLI
              ┌──────────────────────────┐
              │  Jarvis Orchestrator     │
              │  1. Validates JWT        │
              │  2. Extracts user_id     │
              │  3. Creates session      │
              └──────────┬───────────────┘
                         │
        Query: "show my tickets and courses"
                         │
                         ▼
              ┌──────────────────────────┐
              │  Query Decomposition     │
              │  with user context       │
              └──────────┬───────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│ TicketsAgent     │            │ OxygenAgent      │
│                  │            │                  │
│ Receives:        │            │ Receives:        │
│ 1. Query         │            │ 1. Query         │
│ 2. JWT Token (*) │            │ 2. JWT Token (*) │
│                  │            │                  │
│ Session State:   │            │ Session State:   │
│ {                │            │ {                │
│   "user:bearer_  │            │   "user:bearer_  │
│    token": "..." │            │    token": "..." │
│   "user_id":     │            │   "user_id":     │
│    "vishal",     │            │    "vishal",     │
│   "user_role":   │            │   "user_role":   │
│    "developer"   │            │    "developer"   │
│ }                │            │ }                │
│                  │            │                  │
│ Can now:         │            │ Can now:         │
│ - Check role     │            │ - Check role     │
│ - Call other     │────────────▶ - Validate token │
│   agents with    │  JWT prop  │ - Return user    │
│   JWT            │            │   data           │
└──────────────────┘            └──────────────────┘
```

### Token Access in Tools (ToolContext)

```python
from google.adk.tools import ToolContext

def get_user_tickets(ctx: ToolContext) -> List[Dict]:
    """
    Tool with access to JWT via ToolContext.

    ctx.session.state contains:
      - user:bearer_token: JWT token string
      - user_id: Extracted from JWT
      - user_role: User's role
    """
    # Get user info from session state
    user_id = ctx.session.state.get("user_id")
    user_role = ctx.session.state.get("user_role")
    jwt_token = ctx.session.state.get("user:bearer_token")

    # Use user_id to filter data
    return [t for t in TICKETS_DB if t['user'] == user_id]
```

### Agent-to-Agent Calls with JWT

```python
# In TicketsAgent - calling OxygenAgent
def get_tickets_and_courses(ctx: ToolContext, username: str) -> Dict:
    """Tool that calls another agent with JWT propagation."""

    # Get JWT from context
    jwt_token = ctx.session.state.get("user:bearer_token")

    # Create RemoteA2aAgent for OxygenAgent
    oxygen = RemoteA2aAgent(
        name="oxygen_agent",
        agent_card="http://localhost:8082/.well-known/agent-card.json"
    )

    # Create runner and pass JWT in session state
    runner = InMemoryRunner(agent=oxygen)
    session_id = str(uuid.uuid4())

    async def invoke_with_jwt():
        await runner.session_service.create_session(...)
        session = await runner.session_service.get_session(...)

        # KEY: Propagate JWT to OxygenAgent
        session.state["user:bearer_token"] = jwt_token
        session.state["user_id"] = username

    asyncio.run(invoke_with_jwt())

    # Now invoke OxygenAgent - it receives the JWT
    message = types.Content(role="user", parts=[...])
    for event in runner.run(...):
        # Process response
        pass
```

### Permission Checking (RBAC)

```python
def delete_ticket(ctx: ToolContext, ticket_id: int) -> Dict:
    """Delete ticket - requires admin or developer role."""

    user_role = ctx.session.state.get("user_role")
    user_id = ctx.session.state.get("user_id")

    # Check permissions based on role
    if user_role not in ["admin", "developer"]:
        return {
            "error": f"Permission denied. Role '{user_role}' cannot delete tickets."
        }

    # Proceed with deletion
    # ...
```

---

## Implementation Tasks

### Task 1: Update Existing Auth Service to OAuth Format (Day 1)

**Status:** Auth service is 90% complete! Just needs OAuth-compatible updates.

**Existing Directory:** `auth/` (already implemented)

**Existing Files:**
```
auth/
├── __init__.py
├── auth_server.py     # FastAPI service on port 9998 ✅
├── jwt_utils.py       # JWT creation/validation ✅
└── user_service.py    # User authentication ✅
```

**What's Already Working:**
- ✅ FastAPI auth service on port 9998
- ✅ POST /auth/login endpoint
- ✅ User database (vishal, alex, sarah)
- ✅ Password hashing (SHA256)
- ✅ JWT token creation and validation
- ✅ Health check endpoint

**Changes Needed for OAuth Compatibility:**

#### Change 1: Update JWT Format (`auth/jwt_utils.py`)

**Location:** Lines 32-38 in `create_jwt_token()`

**Current Format:**
```python
payload = {
    "username": username,  # ❌ Not OAuth standard
    "user_id": user_id,
    "role": role,
    "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    "iat": datetime.now(timezone.utc)
}
```

**Update To:**
```python
payload = {
    "sub": user_id,           # ✅ OAuth standard: subject
    "username": username,     # Keep for convenience
    "role": role,
    "iat": datetime.now(timezone.utc),
    "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    "iss": "jarvis-auth",     # ✅ Issuer
    "aud": "jarvis-api"       # ✅ Audience
}
```

**Why:** OAuth 2.0 uses `sub` (subject) as the standard claim for user ID. Adding `iss` (issuer) and `aud` (audience) prepares for OAuth provider integration in Phase 4.

---

#### Change 2: Update Login Response Format (`auth/auth_server.py`)

**Location:** Lines 114-118 in `/auth/login` endpoint

**Current Response:**
```python
return LoginResponse(
    success=True,
    token=token,      # ❌ Should be "access_token"
    user=user
)
```

**Update To:**
```python
return {
    "access_token": token,    # ✅ OAuth standard
    "token_type": "bearer",   # ✅ OAuth standard
    "expires_in": 86400,      # ✅ OAuth standard (24 hours in seconds)
    "user": user              # Keep for convenience
}
```

**Also Update LoginResponse Model (lines 31-36):**
```python
class LoginResponse(BaseModel):
    """OAuth 2.0 compatible login response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours
    user: Optional[Dict[str, Any]] = None
```

**Why:** OAuth 2.0 token endpoints return `access_token`, `token_type`, and `expires_in`. This makes the response compatible with OAuth clients.

---

#### Change 3: Add Token Verification Endpoint (`auth/auth_server.py`)

**Location:** Add new endpoint after `/auth/login` (around line 120)

**Add This Endpoint:**
```python
@app.get("/auth/verify")
async def verify_token_endpoint(token: str):
    """
    Verify JWT token and return payload.

    Used by orchestrator to validate tokens.

    Args:
        token: JWT token to verify

    Returns:
        Token payload if valid

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    from auth.jwt_utils import verify_jwt_token

    payload = verify_jwt_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "valid": True,
        "payload": payload
    }
```

**Why:** The orchestrator needs to verify JWT tokens. This endpoint provides a centralized validation service.

---

#### Change 4: Update JWT Utilities Function Signature (`auth/jwt_utils.py`)

**Location:** Line 20 - `create_jwt_token()` function signature

**Current:**
```python
def create_jwt_token(username: str, user_id: str, role: str = "user") -> str:
```

**Update To:**
```python
def create_jwt_token(username: str, user_id: str, role: str = "user") -> str:
    """
    Create OAuth 2.0 compatible JWT token.

    Phase 2: Uses HS256 (symmetric key)
    Phase 4: Will use RS256 (asymmetric key) for OAuth

    Args:
        username: Username of the authenticated user
        user_id: Unique user identifier (becomes 'sub' claim)
        role: User role (custom claim)

    Returns:
        JWT token string
    """
```

**No signature change needed** - just update the docstring to clarify OAuth compatibility.

---

**Existing Code That Needs NO Changes:**

✅ **`auth/user_service.py`** - User database and authentication logic is perfect
- `authenticate_user()` validates credentials ✅
- `get_user_info()` retrieves user data ✅
- SHA256 password hashing ✅

✅ **`auth/auth_server.py`** endpoints:
- `/health` - Already working ✅
- `/auth/user/{username}` - Already working ✅
- `/auth/demo-users` - Already working ✅

---

**Startup Script** (already exists):
```bash
# Start auth service (already works)
cd auth/
python auth_server.py

# OR from project root:
python -m auth.auth_server
```

---

**Testing Updated Auth Service:**

```bash
# Test 1: Login
curl -X POST http://localhost:9998/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "vishal", "password": "password123"}'

# Expected response (OAuth format):
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "username": "vishal",
    "user_id": "user_001",
    "role": "developer",
    "email": "vishal@company.com"
  }
}

# Test 2: Verify token
curl "http://localhost:9998/auth/verify?token=eyJhbGc..."

# Expected response:
{
  "valid": true,
  "payload": {
    "sub": "user_001",
    "username": "vishal",
    "role": "developer",
    "iat": 1735603200,
    "exp": 1735689600,
    "iss": "jarvis-auth",
    "aud": "jarvis-api"
  }
}
```

**Estimated Time:** 1-2 hours (reduced from 3-4 hours since code already exists)

---

### Task 2: Update CLI with Login (Day 1)

**Update:** `jarvis_agent/main_with_registry.py`

**Changes:**

1. Add login flow before creating orchestrator
2. Store JWT token
3. Pass token to orchestrator

```python
# At top of file
import getpass
import requests

def authenticate_user() -> tuple[str, str]:
    """
    Authenticate user and return JWT token + user_id.

    Returns:
        (jwt_token, user_id)
    """
    print("=" * 80)
    print("Jarvis Authentication")
    print("=" * 80)
    print()

    # Get credentials
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    # Call auth service
    try:
        response = requests.post(
            "http://localhost:9998/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )

        if response.status_code == 401:
            print("✗ Authentication failed: Invalid username or password")
            sys.exit(1)

        response.raise_for_status()

        data = response.json()
        jwt_token = data["access_token"]  # ✅ OAuth standard format
        user_info = data["user"]

        print(f"✓ Authenticated as {user_info['username']} ({user_info['role']})")
        print()

        return jwt_token, user_info["username"]

    except requests.ConnectionError:
        print("✗ Auth service not available at http://localhost:9998")
        print("  Start it with: ./scripts/start_auth_service.sh")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        sys.exit(1)

def main():
    # ... existing code ...

    # Authenticate user
    jwt_token, user_id = authenticate_user()

    # Initialize orchestrator with JWT
    try:
        orchestrator = JarvisOrchestrator(jwt_token=jwt_token)
    except ConnectionError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Resume or create session
    session_id = orchestrator.get_or_resume_session(user_id)
    session_data = orchestrator.session_client.get_session(session_id)

    if session_data and session_data.get('conversation_history'):
        print(f"Welcome back! Resuming session: {session_id}")
        print(f"Last message: {session_data['conversation_history'][-1]['content'][:50]}...")
    else:
        print(f"New session created: {session_id}")

    print()

    # ... rest of main loop ...
```

---

### Task 3: Update Orchestrator with JWT (Day 2)

**Update:** `jarvis_agent/main_with_registry.py` - `JarvisOrchestrator` class

**📖 Reference:** See [TOKEN_PROPAGATION_GUIDE.md](./TOKEN_PROPAGATION_GUIDE.md) for detailed explanation of how JWT flows from orchestrator to agents.

**Changes:**

1. Accept JWT token in constructor
2. Validate JWT on initialization
3. Extract user_id from JWT
4. **Pass JWT to agents via session.state** (enables agent-to-agent calls)
5. Pass user_id to query decomposition
6. Add session resumption logic

```python
class JarvisOrchestrator:
    def __init__(
        self,
        jwt_token: str,  # NEW: Required JWT token
        registry_url: str = "http://localhost:8003",
        session_url: str = "http://localhost:8003",
        timeout: int = 10
    ):
        logger.info("Initializing Jarvis Orchestrator with JWT authentication")

        # Validate and decode JWT
        self.jwt_token = jwt_token
        self.user_info = self._validate_jwt(jwt_token)
        self.user_id = self.user_info["sub"]
        self.user_role = self.user_info.get("role", "user")

        logger.info(f"Authenticated user: {self.user_id} (role: {self.user_role})")

        # ... rest of initialization ...

    def _validate_jwt(self, token: str) -> dict:
        """Validate JWT token and return payload."""
        # Import jwt_utils from auth folder
        from auth.jwt_utils import verify_jwt_token

        payload = verify_jwt_token(token)

        if not payload:
            raise ValueError("Invalid or expired JWT token")

        return payload

    def get_or_resume_session(self, user_id: str) -> str:
        """
        Get existing active session or create new one.

        This fixes the session persistence issue.
        """
        # Check if user already in cache
        if user_id in self._user_sessions:
            session_id = self._user_sessions[user_id]
            session_data = self.session_client.get_session(session_id)

            # Verify session is still active
            if session_data and session_data.get("status") == "active":
                logger.info(f"Resuming active session {session_id} for user {user_id}")
                return session_id

        # No active session - create new one
        session_id = self.create_session(user_id)
        logger.info(f"Created new session {session_id} for user {user_id}")
        return session_id

    def handle_query(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None
    ) -> str:
        # ... existing code ...

        # Decompose query with user context
        sub_queries = self._decompose_query(query, agents, user_id)  # Pass user_id!

        # ... rest of method ...

    def _decompose_query(
        self,
        original_query: str,
        agents: List[LlmAgent],
        user_id: str  # NEW: User context
    ) -> Dict[str, str]:
        """
        Decompose multi-agent query with user context.

        This fixes "show my tickets" by replacing "my" with "vishal".
        """
        if len(agents) == 1:
            # Single agent - inject user context if query contains "my" or "I"
            query = self._inject_user_context(original_query, user_id)
            return {agents[0].name: query}

        # Multi-agent decomposition with user context
        prompt = f"""Given a user query and multiple specialized agents, break down the query into agent-specific sub-queries.

User: {user_id}
Query: "{original_query}"

Available Agents:
{chr(10).join([f"- {agent.name}: {agent.description}" for agent in agents])}

IMPORTANT:
1. Replace "my", "I", "me" with the specific username: "{user_id}"
2. Each sub-query should be standalone and clear
3. Return JSON mapping agent names to their sub-queries

Example:
User: vishal
Query: "show my tickets and aws cost"
Output:
{{
    "TicketsAgent": "show tickets for vishal",
    "FinOpsAgent": "show aws cost"
}}

Now decompose the actual query above."""

        # ... rest of existing LLM call ...

    def _inject_user_context(self, query: str, user_id: str) -> str:
        """
        Inject user context into query.

        Replaces "my", "I", "me" with specific username.
        """
        import re

        # Replace possessive "my"
        query = re.sub(r'\bmy\b', f"{user_id}'s", query, flags=re.IGNORECASE)

        # Replace "I" at word boundaries
        query = re.sub(r'\bI\b', user_id, query)

        # Replace "me"
        query = re.sub(r'\bme\b', user_id, query, flags=re.IGNORECASE)

        return query
```

---

### Task 4: Update Agent Instructions (Day 2)

**Update all three agents** to handle user-specific queries better:

**TicketsAgent** (`tickets_agent_service/agent.py`):
```python
instruction="""You are a specialized IT operations assistant focused on ticket management.

**Your Responsibilities:**
- Help users manage IT operation tickets
- Track ticket status and provide updates
- Create new tickets for IT operations

**User Context Handling:**
- Queries will include specific usernames (e.g., "show tickets for vishal")
- Use get_user_tickets(username) for user-specific queries
- Use get_all_tickets() only when explicitly asked for "all tickets"

**Available Tools:**
- get_all_tickets: List ALL tickets in the system
- get_ticket: Get specific ticket by ID
- get_user_tickets: Get tickets for a specific user (by username)
- create_ticket: Create new ticket (specify operation and user)

**Example Queries You'll Receive:**
- "show tickets for vishal" → Use get_user_tickets("vishal")
- "what's the status of ticket 12301?" → Use get_ticket(12301)
- "show all tickets" → Use get_all_tickets()
- "create ticket for alex to get vpn access" → Use create_ticket("vpn_access", "alex")
"""
```

**OxygenAgent** (`oxygen_agent_service/agent.py`):
```python
instruction="""You are Oxygen, a learning and development assistant.

**User Context Handling:**
- Queries will include specific usernames (e.g., "show courses for vishal")
- Always use the provided username in tool calls
- All learning data is user-specific

**Available Users:** vishal, happy, alex

**Available Tools:**
- get_user_courses: Get courses for a specific user (by username)
- get_pending_exams: Get pending exams with deadlines (by username)
- get_user_preferences: Get learning preferences (by username)
- get_learning_summary: Complete learning journey (by username)

**Example Queries You'll Receive:**
- "show courses for vishal" → Use get_user_courses("vishal")
- "what exams does alex have pending?" → Use get_pending_exams("alex")
- "show learning summary for happy" → Use get_learning_summary("happy")
"""
```

---

### Task 5: Enable Data Isolation via Agent Intelligence (Day 2)

**Priority:** Critical (Goal 3: Data Isolation)
**Dependencies:** Task 3 (Query decomposition with user context)
**Estimated Time:** 30 minutes

**Objective:**
Ensure agents understand user-specific queries and automatically filter data.
NO new tools needed - leverage AI intelligence!

**Why This Works:**
- Query decomposition already injects user_id: "show my tickets" → "show tickets for vishal"
- Existing tools already have username parameters: `get_user_tickets(username)`
- Agent just needs clear instructions to USE the username from the query

**Implementation:**

**Update Agent Instructions Only** - No code changes to tools!

**1. TicketsAgent** (`tickets_agent_service/agent.py`):
```python
tickets_agent = LlmAgent(
    name="TicketsAgent",
    model="gemini-2.5-flash",
    description="IT operations ticket management agent",
    instruction="""You are a specialized IT operations assistant focused on ticket management.

**IMPORTANT - User Context:**
Queries will include the authenticated username (e.g., "show tickets for vishal").
The system automatically provides the username - you don't need to ask for it.
Just use the username mentioned in the query when calling tools.

**Available Tools:**
- get_all_tickets: List ALL tickets in the system (use only when asked for "all tickets")
- get_ticket: Get specific ticket by ID
- get_user_tickets: Get tickets for a specific user (by username)
- create_ticket: Create new ticket (specify operation and user)

**Examples:**
Query: "show tickets for vishal"
→ Call: get_user_tickets("vishal")

Query: "what's the status of ticket 12301?"
→ Call: get_ticket(12301)

Query: "show all tickets"
→ Call: get_all_tickets()

Query: "create ticket for alex to get vpn access"
→ Call: create_ticket("vpn_access", "alex")

**Communication Style:**
- Be clear and concise about ticket status
- Always include ticket IDs when referencing tickets
- Explain what each ticket status means
""",
    tools=[get_all_tickets, get_ticket, get_user_tickets, create_ticket]  # UNCHANGED
)
```

**2. OxygenAgent** (`oxygen_agent_service/agent.py`):
```python
oxygen_agent = LlmAgent(
    name="OxygenAgent",
    model="gemini-2.5-flash",
    description="Learning and development platform agent",
    instruction="""You are Oxygen, a learning and development assistant.

**IMPORTANT - User Context:**
Queries will include the authenticated username (e.g., "show courses for vishal").
Always use the username mentioned in the query when calling tools.

**Available Users:** vishal, happy, alex

**Available Tools:**
- get_user_courses: Get courses for a specific user (by username)
- get_pending_exams: Get pending exams with deadlines (by username)
- get_user_preferences: Get learning preferences (by username)
- get_learning_summary: Complete learning journey (by username)

**Examples:**
Query: "show courses for vishal"
→ Call: get_user_courses("vishal")

Query: "what exams does alex have pending?"
→ Call: get_pending_exams("alex")

Query: "show learning summary for happy"
→ Call: get_learning_summary("happy")

**Communication Style:**
Always be encouraging and supportive in your responses.
""",
    tools=[get_user_courses, get_pending_exams, get_user_preferences, get_learning_summary]  # UNCHANGED
)
```

**3. FinOpsAgent** (`finops_agent_service/agent.py`):
```python
finops_agent = LlmAgent(
    name="FinOpsAgent",
    model="gemini-2.5-flash",
    description="Cloud financial operations and cost analytics agent",
    instruction="""You are a specialized FinOps (Financial Operations) assistant for cloud cost analytics.

**Your Responsibilities:**
- Analyze cloud costs across AWS, GCP, and Azure
- Provide cost breakdowns by provider and service
- Help identify cost optimization opportunities

**Available Tools:**
- get_all_clouds_cost: Total cost across all cloud providers
- get_cloud_cost: Detailed costs for specific provider (aws, gcp, azure)
- get_service_cost: Cost for specific service (e.g., ec2, s3, compute)
- get_cost_breakdown: Comprehensive breakdown with percentages

**Cloud Providers:**
- AWS: EC2, S3, DynamoDB
- GCP: Compute, Vault, Firestore
- Azure: Storage, AI Studio

**Communication Style:**
- Always mention currency (USD)
- Use percentages to show proportions
- Highlight the highest cost items
""",
    tools=[get_all_clouds_cost, get_cloud_cost, get_service_cost, get_cost_breakdown]  # UNCHANGED
)
```

**That's It!** No tool changes, no ToolContext, no manual filtering.

**How Data Isolation Works:**
```
1. User "vishal" logs in
2. User asks: "show my tickets"
3. Orchestrator decomposes: "show my tickets" → "show tickets for vishal"
4. TicketsAgent receives: "show tickets for vishal"
5. Agent (AI) understands and calls: get_user_tickets("vishal")
6. Returns: Only vishal's tickets ✓
```

**Success Criteria:**
- [ ] Agent instructions updated with user context guidance
- [ ] Test: "show my tickets" returns only authenticated user's tickets
- [ ] Test: "show my courses" returns only authenticated user's courses
- [ ] No changes to tool function signatures
- [ ] AI agent correctly extracts username from query

---

### Task 6: Implement Session Persistence (Day 2)

**Priority:** High (Goal 4: Session Persistence)
**Dependencies:** Task 3 (Session service integration)
**Estimated Time:** 1-2 hours

**Objective:**
Enable session resumption so users see their conversation history when they log back in.

**Current Problem:**
```bash
# First login
vishal> show my tickets
vishal> /exit

# Second login
vishal> /history
# Shows: EMPTY ❌ (new session created)
```

**Desired Behavior:**
```bash
# Second login
Welcome back! Resuming session from Dec 30, 22:00
vishal> /history
# Shows: Previous conversation ✓
```

**Implementation:**

**1. Add Session Lookup to SessionClient** (`jarvis_agent/session_client.py`):

Add one new method:

```python
def get_active_session_for_user(self, user_id: str) -> Optional[str]:
    """
    Get active session ID for a user.

    Calls registry API to find user's most recent active session.

    Returns:
        Session ID if active session exists, None otherwise
    """
    try:
        response = self._session.get(
            f"{self.base_url}/sessions/user/{user_id}/active",
            timeout=self.timeout
        )

        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")

            if session_id:
                logger.info(f"Found active session {session_id} for user {user_id}")
                return session_id

        return None

    except requests.ConnectionError:
        logger.warning(f"Cannot reach session service to check for active session")
        return None
    except Exception as e:
        logger.error(f"Error getting active session for {user_id}: {e}")
        return None
```

**2. Add Registry API Endpoint** (`agent_registry_service/api/session_routes.py`):

Add endpoint to find active session by user_id:

```python
@router.get("/sessions/user/{user_id}/active")
async def get_active_session_for_user(user_id: str):
    """
    Get active session for a user.

    Returns the most recent active session (updated within last 24 hours).
    """
    # Query database for active sessions
    query = """
        SELECT session_id, updated_at
        FROM sessions
        WHERE user_id = ? AND status = 'active'
        ORDER BY updated_at DESC
        LIMIT 1
    """

    result = db.execute(query, (user_id,)).fetchone()

    if result:
        session_id, updated_at = result

        # Check if session is still valid (< 24 hours old)
        from datetime import datetime, timedelta
        updated = datetime.fromisoformat(updated_at)

        if datetime.now() - updated < timedelta(hours=24):
            # Session is still active
            session = session_manager.get_session(session_id)
            return session

    # No active session
    return {
        "session_id": None,
        "message": "No active session found"
    }
```

**3. Update Orchestrator's get_or_resume_session()** (`jarvis_agent/main_with_registry.py`):

This method already exists from Task 3, just ensure it uses the new API:

```python
def get_or_resume_session(self, user_id: str) -> str:
    """
    Resume active session or create new one.

    Implements session persistence across logins (Goal 4).
    """
    # Check cache first
    if user_id in self._user_sessions:
        session_id = self._user_sessions[user_id]
        session_data = self.session_client.get_session(session_id)

        if session_data and session_data.get("status") == "active":
            logger.info(f"Resuming cached session {session_id}")
            return session_id

    # Check registry for active session
    session_id = self.session_client.get_active_session_for_user(user_id)

    if session_id:
        # Resume existing session
        self._user_sessions[user_id] = session_id
        logger.info(f"✓ Resuming active session {session_id} for user {user_id}")
        return session_id

    # Create new session
    session_id = self.create_session(user_id)
    logger.info(f"✓ Created new session {session_id} for user {user_id}")
    return session_id
```

**4. Update CLI to Show Session Info** (`jarvis_agent/main_with_registry.py` in main()):

Update the main function to show session resumption:

```python
def main():
    # ... authentication code ...

    # Resume or create session
    session_id = orchestrator.get_or_resume_session(user_id)
    session_data = orchestrator.session_client.get_session(session_id)

    if session_data:
        history = session_data.get('conversation_history', [])

        if len(history) > 0:
            # Resuming existing session
            print(f"✓ Welcome back! Resuming session from {session_data['updated_at']}")
            print(f"  Messages: {len(history)}")

            # Show preview of last message
            last_msg = history[-1]
            preview = last_msg['content'][:60]
            if len(last_msg['content']) > 60:
                preview += "..."
            print(f"  Last: {preview}")
            print()
            print("  Type /history to see full conversation")
        else:
            # New session
            print(f"✓ New session created: {session_id}")

    print()

    # ... rest of main loop ...
```

**Expected Output:**

```bash
# First login
Username: vishal
Password: ******
✓ Authenticated as vishal (developer)
✓ New session created: abc-123

vishal> show my tickets
Jarvis> Here are your tickets: ...
vishal> /exit

# Second login (same day)
Username: vishal
Password: ******
✓ Authenticated as vishal (developer)
✓ Welcome back! Resuming session from 2025-12-30 22:00
  Messages: 2
  Last: Here are your tickets: Ticket ID: 12301, 12303

  Type /history to see full conversation

vishal> /history
# Shows:
USER: show my tickets
ASSISTANT: Here are your tickets: ...
```

**Success Criteria:**
- [ ] SessionClient can get active session for user
- [ ] Registry API returns active session by user_id
- [ ] Orchestrator resumes active sessions on login
- [ ] CLI shows "Welcome back!" with session preview
- [ ] /history shows previous conversation after re-login
- [ ] Sessions expire after 24 hours (create new if expired)

---

### Task 7: Environment Configuration (Day 2)

**Update `.env`:**
```bash
# Existing
GOOGLE_API_KEY=your_api_key_here

# NEW for Phase 2
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Service ports
TICKETS_AGENT_PORT=8080
FINOPS_AGENT_PORT=8081
OXYGEN_AGENT_PORT=8082
REGISTRY_SERVICE_PORT=8003
AUTH_SERVICE_PORT=9998
```

**Generate secure JWT secret:**
```bash
# Add to scripts/generate_jwt_secret.sh
#!/bin/bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### Task 8: Update Startup Scripts (Day 3)

**Update `scripts/start_all_agents.sh`:**
```bash
#!/bin/bash

# ... existing agent startup code ...

echo ""
echo "Starting Auth Service..."
python -m auth.auth_server &
sleep 2

if lsof -Pi :9998 -sTCP:LISTEN -t >/dev/null; then
    echo "  ✓ Auth Service started on port 9998"
else
    echo "  ✗ Failed to start Auth Service"
    exit 1
fi

echo ""
echo "All services started successfully!"
echo ""
echo "  TicketsAgent:    http://localhost:8080"
echo "  FinOpsAgent:     http://localhost:8081"
echo "  OxygenAgent:     http://localhost:8082"
echo "  Registry:        http://localhost:8003"
echo "  Auth Service:    http://localhost:9998"
echo ""
echo "To use Jarvis:"
echo "  python jarvis_agent/main_with_registry.py"
echo ""
echo "Test users:"
echo "  vishal / password123 (developer)"
echo "  alex / password123 (devops)"
echo "  sarah / password123 (data_scientist)"
```

---

## Testing Plan

### Test 1: Authentication Flow

```bash
# Start all services
./scripts/start_all_agents.sh

# Run Jarvis CLI
python jarvis_agent/main_with_registry.py

# Expected:
Username: vishal
Password: ******
✓ Authenticated as vishal (developer)
Welcome back! Resuming session: abc-123
```

### Test 2: User-Specific Queries

```bash
vishal> show my tickets

# Expected response:
Here are the tickets for vishal:
* Ticket ID: 12301 (create_ai_key, pending)
* Ticket ID: 12303 (update_budget, in_progress)
```

### Test 3: Session Persistence

```bash
# First session
vishal> show my tickets
vishal> what's our aws cost?
vishal> /exit

# Login again
python jarvis_agent/main_with_registry.py
Username: vishal
Password: ******
Welcome back! Resuming session: abc-123

vishal> /history

# Expected: Shows previous conversation
USER: show my tickets
ASSISTANT: Here are the tickets for vishal...
USER: what's our aws cost?
ASSISTANT: AWS cost is $15,234.50...
```

### Test 4: Invalid Credentials

```bash
Username: hacker
Password: wrong
✗ Authentication failed: Invalid username or password
```

---

## OAuth 2.0 Migration Path

**📖 See [TOKEN_PROPAGATION_GUIDE.md](./TOKEN_PROPAGATION_GUIDE.md#migration-to-oauth-20) for detailed OAuth migration strategy**

### Current JWT Format (Phase 2)
```json
{
  "sub": "vishal",
  "role": "developer",
  "iat": 1735603200,
  "exp": 1735689600,
  "iss": "jarvis-auth",
  "aud": "jarvis-api"
}
```

### Future OAuth 2.0 Format (Phase 4)
```json
{
  "sub": "vishal@company.com",
  "email": "vishal@company.com",
  "name": "Vishal Kumar",
  "role": "developer",
  "groups": ["developers", "admins"],
  "iat": 1735603200,
  "exp": 1735689600,
  "iss": "https://auth.company.com",
  "aud": "jarvis-production-client"
}
```

### Migration Strategy

**Phase 2 → Phase 4 Changes:**

1. **Auth Service Replacement**
   - Replace `auth_service/server.py` with OAuth 2.0 client
   - Use library: `authlib` or `python-oauth2`
   - Configure OAuth provider (Google, Okta, Auth0, etc.)

2. **JWT Validation Update**
   - Current: Symmetric key (HS256)
   - OAuth: Public key validation (RS256)
   - Fetch public keys from OAuth provider JWKS endpoint

3. **No Changes Needed:**
   - Query decomposition (still uses `user_id` from JWT)
   - Session management (still tracks by `user_id`)
   - Agent invocation (still passes user context)

**Example OAuth Integration:**
```python
# Future: auth_service/oauth_client.py
from authlib.integrations.requests_client import OAuth2Session

oauth = OAuth2Session(
    client_id=os.getenv("OAUTH_CLIENT_ID"),
    client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
    redirect_uri="http://localhost:9999/callback"
)

# Authorization URL
authorization_url, state = oauth.create_authorization_url(
    "https://accounts.google.com/o/oauth2/v2/auth"
)

# Token exchange
token = oauth.fetch_token(
    "https://oauth2.googleapis.com/token",
    authorization_response=callback_url
)

# JWT is in token['access_token']
# Validate using Google's public keys
```

---

## Implementation Timeline

### Day 1 (2-3 hours)
- [ ] **Task 1: Update Existing Auth Service to OAuth Format** (1-2 hours)
  - ✅ Auth service already 90% complete!
  - Update JWT format in `auth/jwt_utils.py` (add `sub`, `iss`, `aud`)
  - Update response format in `auth/auth_server.py` (OAuth standard)
  - Add `/auth/verify` endpoint
  - Update LoginResponse model
  - Test auth service

- [ ] **Task 2: Update CLI with Login** (1 hour)
  - Add login flow with username/password
  - Handle authentication errors
  - Store JWT token (use OAuth `access_token` field)
  - Test login process

### Day 2 (4-5 hours)
- [ ] **Task 3: Update Orchestrator with JWT** (2-3 hours)
  - Add JWT validation in constructor
  - Extract user_id from JWT
  - Pass JWT to agents via session.state
  - Update query decomposition to inject user_id
  - Test with CLI

- [ ] **Task 4: Update Agent Instructions** (30 min)
  - Update TicketsAgent instructions (user context guidance)
  - Update OxygenAgent instructions (user context guidance)
  - Update FinOpsAgent instructions
  - **NO CODE CHANGES** - just instruction text!

- [ ] **Task 5: Enable Data Isolation** (30 min)
  - Verify query decomposition works ("my tickets" → "tickets for vishal")
  - Test agent AI correctly extracts username from query
  - **LEVERAGES AI** - no manual filtering code!

- [ ] **Task 6: Implement Session Persistence** (1-2 hours)
  - Add get_active_session_for_user() to SessionClient
  - Add registry API endpoint for session lookup
  - Update CLI to show session resumption
  - Test /history across logins

### Day 3 (2-3 hours)
- [ ] **Task 7: Environment Configuration** (30 min)
  - Update .env with JWT_SECRET_KEY
  - Generate secure JWT secret
  - Document configuration

- [ ] **Task 8: Update Startup Scripts** (30 min)
  - Update start_all_agents.sh to include auth service
  - Test full system startup

- [ ] **Testing** (1-2 hours)
  - Test 1: Authentication flow
  - Test 2: User-specific queries ("show my tickets")
  - Test 3: Session persistence (/history after re-login)
  - Test 4: Invalid credentials
  - Test 5: Token propagation (JWT in session.state)
  - Test 6: Cross-agent queries

- [ ] **Documentation** (30 min)
  - Update README with Phase 2 features
  - Add testing guide
  - Document OAuth migration path

**Total Estimated Time:** 8-11 hours (1-1.5 days)

**Key Simplifications:**
- ✅ Auth service already 90% complete (saves 2 hours!)
- ✅ No ToolContext refactoring
- ✅ No manual filtering code
- ✅ Leverage AI for user context extraction
- ✅ OAuth-ready from day one

---

## Success Criteria

Phase 2 is complete when:

- [ ] Auth service running on port 9998
- [ ] CLI requires login with username/password
- [ ] Invalid credentials are rejected
- [ ] JWT tokens generated and validated
- [ ] "show my tickets" works (returns user-specific data)
- [ ] Session persists across logins
- [ ] /history shows previous conversations
- [ ] All three agents receive user context correctly
- [ ] No code changes needed for OAuth migration (just config)

---

## Rollback Plan

If Phase 2 causes issues:

1. **Stop auth service:** `lsof -ti:9998 | xargs kill -9`
2. **Revert auth/ files:** `git checkout auth/`
3. **Revert main_with_registry.py:** `git checkout main_with_registry.py`
4. **Use Phase 1 CLI:** Username prompt without password

All agent services (8080, 8081, 8082, 8003) remain unchanged and continue working.

**Note:** The `auth/` folder already exists, so rollback just reverts the OAuth format changes.

---

## Next Steps (Phase 3)

After Phase 2 is complete and stable:

**Phase 3: Memory & Context Management**
- Vector DB integration for long-term memory
- Proactive notifications (exam deadlines, pending tickets)
- Context-aware recommendations
- "You asked about X last week, here's an update"
- Chat history search

**Phase 4: OAuth 2.0**
- Replace auth_service with OAuth 2.0 client
- SSO with Google, Azure AD, Okta, Auth0
- RS256 JWT validation with public keys
- Enterprise identity provider integration

---

## Questions?

Before proceeding with implementation, confirm:

1. ✅ Use existing `auth/` folder (90% complete) instead of creating new `auth_service/`?
2. ✅ Update JWT format to OAuth standard (`sub`, `iss`, `aud` claims)?
3. ✅ Use HS256 (symmetric) JWT for Phase 2?
4. ✅ Session resumption based on user_id + active status?
5. ✅ User context injection in query decomposition?
6. ✅ No agent-side JWT validation (orchestrator validates)?
7. ✅ In-memory user database (not production DB)?

**Key Discovery:** Found existing `auth/` folder with FastAPI service, JWT utilities, and user authentication already implemented! This saves 2 hours of implementation time.

If all confirmed, we can start implementation!
