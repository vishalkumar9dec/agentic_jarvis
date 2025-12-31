# Token Propagation Guide - Phase 2

**Purpose:** Explain how JWT tokens flow through the Pure A2A architecture
**Date:** 2025-12-30
**Architecture:** Pure A2A (TicketsAgent:8080, FinOpsAgent:8081, OxygenAgent:8082)

---

## Your Question

> "In this implementation, will we be passing token to agents, like from 1 agent to another?
> In token there may be information about access which would be required by some other agents.
> How is this being taken care?"

## Answer: YES - Full Token Propagation

**Short Answer:** Yes, JWT tokens are passed to ALL agents and can be propagated between agents.

**How It Works:**
1. **Orchestrator → Agent:** JWT stored in `session.state["user:bearer_token"]`
2. **Agent → Agent:** JWT can be passed when one agent calls another
3. **Access Control:** Agents can read `user_role` and `permissions` from JWT

---

## Complete Token Flow

### Step 1: User Logs In
```
User enters: vishal / password123
      ↓
Auth Service validates
      ↓
Returns JWT:
{
  "sub": "vishal",
  "role": "developer",
  "permissions": ["tickets:read", "tickets:write", "courses:read"],
  "iat": 1735603200,
  "exp": 1735689600
}
```

### Step 2: Orchestrator Validates JWT
```python
# In JarvisOrchestrator.__init__()
self.jwt_token = jwt_token
self.user_info = verify_token(jwt_token)
self.user_id = self.user_info["sub"]          # "vishal"
self.user_role = self.user_info["role"]       # "developer"
self.user_permissions = self.user_info["permissions"]  # [...]
```

### Step 3: Orchestrator → Agent (JWT Injection)
```python
# In _invoke_agent() method
async def create_session_with_auth():
    await runner.session_service.create_session(
        user_id=self.user_id,
        session_id=session_id
    )

    session = await runner.session_service.get_session(...)

    # INJECT JWT into agent's session state
    session.state["user:bearer_token"] = self.jwt_token
    session.state["user_id"] = self.user_id
    session.state["user_role"] = self.user_role
    session.state["user_permissions"] = self.user_permissions
```

### Step 4: Agent Accesses JWT via ToolContext
```python
# In tickets_agent_service/agent.py

from google.adk.tools import ToolContext

def get_my_tickets(ctx: ToolContext) -> List[Dict]:
    """
    Get tickets for authenticated user.

    The ToolContext provides access to session.state where JWT info is stored.
    """
    # Extract user info from session state (set by orchestrator)
    user_id = ctx.session.state.get("user_id")           # "vishal"
    user_role = ctx.session.state.get("user_role")       # "developer"
    user_permissions = ctx.session.state.get("user_permissions")  # [...]
    jwt_token = ctx.session.state.get("user:bearer_token")  # Full JWT

    # Now filter tickets by authenticated user
    tickets = [t for t in TICKETS_DB if t['user'] == user_id]

    return {
        "user": user_id,
        "role": user_role,
        "tickets": tickets
    }
```

### Step 5: Agent → Agent (JWT Propagation)
```python
# In tickets_agent_service/agent.py - Agent calls another agent

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.runners import InMemoryRunner

def get_tickets_with_learning_info(ctx: ToolContext, username: str) -> Dict:
    """
    Get tickets AND courses by calling OxygenAgent.

    Demonstrates agent-to-agent call with JWT propagation.
    """
    # 1. Get JWT from current context
    jwt_token = ctx.session.state.get("user:bearer_token")
    user_id = ctx.session.state.get("user_id")
    user_role = ctx.session.state.get("user_role")

    # 2. Get tickets locally
    tickets = [t for t in TICKETS_DB if t['user'] == username]

    # 3. Call OxygenAgent to get courses
    oxygen_agent = RemoteA2aAgent(
        name="oxygen_agent",
        description="Learning platform",
        agent_card="http://localhost:8082/.well-known/agent-card.json"
    )

    runner = InMemoryRunner(agent=oxygen_agent)
    session_id = str(uuid.uuid4())

    # 4. Create session and PROPAGATE JWT to OxygenAgent
    async def invoke_oxygen_with_jwt():
        await runner.session_service.create_session(
            app_name="tickets_to_oxygen",
            user_id=user_id,
            session_id=session_id
        )

        session = await runner.session_service.get_session(
            app_name="tickets_to_oxygen",
            user_id=user_id,
            session_id=session_id
        )

        # PROPAGATE JWT: OxygenAgent now has auth context
        session.state["user:bearer_token"] = jwt_token
        session.state["user_id"] = user_id
        session.state["user_role"] = user_role

    asyncio.run(invoke_oxygen_with_jwt())

    # 5. Invoke OxygenAgent (it receives the JWT)
    message = types.Content(
        role="user",
        parts=[types.Part(text=f"get courses for {username}")]
    )

    courses_response = ""
    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=message
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    courses_response += part.text

    # 6. Return combined data
    return {
        "tickets": tickets,
        "courses": courses_response,
        "user": username
    }
```

---

## Use Cases Enabled

### 1. User-Specific Data Access
```python
# TicketsAgent can filter by authenticated user
def get_my_tickets(ctx: ToolContext):
    user_id = ctx.session.state.get("user_id")  # From JWT
    return [t for t in TICKETS_DB if t['user'] == user_id]
```

### 2. Role-Based Access Control (RBAC)
```python
# Only admins can delete tickets
def delete_ticket(ctx: ToolContext, ticket_id: int):
    user_role = ctx.session.state.get("user_role")

    if user_role not in ["admin", "developer"]:
        return {"error": "Permission denied"}

    # Proceed with deletion...
```

### 3. Permission Checking
```python
# Check specific permissions from JWT
def export_financial_data(ctx: ToolContext):
    permissions = ctx.session.state.get("user_permissions", [])

    if "finops:export" not in permissions:
        return {"error": "Missing permission: finops:export"}

    # Export data...
```

### 4. Agent-to-Agent Calls
```python
# TicketsAgent calls OxygenAgent with same auth context
def get_comprehensive_report(ctx: ToolContext):
    jwt = ctx.session.state.get("user:bearer_token")

    # Call multiple agents with same JWT
    courses = call_oxygen_agent(jwt, query)
    costs = call_finops_agent(jwt, query)

    return {"courses": courses, "costs": costs}
```

### 5. Audit Logging
```python
# Track who performed actions
def create_ticket(ctx: ToolContext, operation: str, user: str):
    actor = ctx.session.state.get("user_id")  # Who created the ticket
    actor_role = ctx.session.state.get("user_role")

    new_ticket = {
        "operation": operation,
        "user": user,
        "created_by": actor,
        "created_by_role": actor_role
    }

    log_audit_event(f"{actor} ({actor_role}) created ticket for {user}")
    return new_ticket
```

---

## JWT Token Structure

### Phase 2 Format (Current)
```json
{
  "sub": "vishal",
  "role": "developer",
  "permissions": [
    "tickets:read",
    "tickets:write",
    "tickets:delete",
    "courses:read",
    "finops:read"
  ],
  "iat": 1735603200,
  "exp": 1735689600,
  "iss": "jarvis-auth",
  "aud": "jarvis-api"
}
```

### Phase 4 Format (OAuth 2.0)
```json
{
  "sub": "vishal@company.com",
  "email": "vishal@company.com",
  "name": "Vishal Kumar",
  "preferred_username": "vishal",
  "groups": ["developers", "admins"],
  "scope": "tickets:read tickets:write courses:read finops:read",
  "roles": ["developer"],
  "iat": 1735603200,
  "exp": 1735689600,
  "iss": "https://auth.company.com",
  "aud": "jarvis-production-client"
}
```

**Note:** Phase 2 code will work with Phase 4 tokens (just reads different fields).

---

## Security Considerations

### Phase 2 (Trust Model)
- **Orchestrator validates JWT** → Only valid tokens reach agents
- **Agents trust orchestrator** → Don't re-validate JWT (performance)
- **Session state is safe** → Controlled by ADK, agents can't tamper
- **Single validation point** → Simpler, faster

### Phase 4 (Zero Trust Model)
- **Each agent validates JWT** → Full distributed authentication
- **Public key validation** → RS256 with OAuth provider's JWKS
- **No trust assumptions** → Agents verify independently
- **Service mesh pattern** → Production-ready, enterprise-grade

---

## Implementation Checklist

For Phase 2 to support token propagation:

- [ ] **Auth Service** generates JWT with user_id, role, permissions
- [ ] **Orchestrator** validates JWT and stores in `self.jwt_token`
- [ ] **_invoke_agent()** injects JWT into `session.state["user:bearer_token"]`
- [ ] **Agent tools** accept `ToolContext` parameter to access session state
- [ ] **Agent instructions** updated to use authenticated user context
- [ ] **Agent-to-agent calls** propagate JWT via session state

---

## Example Scenarios

### Scenario 1: User asks "show my tickets"
```
1. vishal logs in → JWT: {"sub": "vishal", "role": "developer"}
2. vishal> show my tickets
3. Orchestrator validates JWT → user_id = "vishal"
4. Query decomposed → "show tickets for vishal"
5. Orchestrator invokes TicketsAgent:
   - Query: "show tickets for vishal"
   - Session state: {"user:bearer_token": "...", "user_id": "vishal"}
6. TicketsAgent tool:
   def get_user_tickets(ctx: ToolContext, username: str):
       # ctx.session.state has user_id="vishal"
       return [t for t in TICKETS_DB if t['user'] == username]
7. Returns vishal's tickets only ✓
```

### Scenario 2: TicketsAgent calls OxygenAgent
```
1. User asks: "show my tickets and courses"
2. Orchestrator decomposes:
   - TicketsAgent: "show tickets for vishal"
   - OxygenAgent: "show courses for vishal"
3. Both agents receive JWT in session state
4. Later, TicketsAgent needs to call OxygenAgent:
   - Reads JWT from ctx.session.state
   - Creates RemoteA2aAgent for OxygenAgent
   - Injects same JWT into OxygenAgent's session state
   - Calls OxygenAgent with auth context preserved
5. OxygenAgent sees same user_id="vishal" in its session state ✓
```

### Scenario 3: Role-based deletion
```
1. Admin logs in → JWT: {"sub": "admin", "role": "admin"}
2. admin> delete ticket 12301
3. Orchestrator → TicketsAgent with JWT
4. TicketsAgent tool:
   def delete_ticket(ctx: ToolContext, ticket_id: int):
       role = ctx.session.state.get("user_role")  # "admin"
       if role not in ["admin"]:
           return {"error": "Permission denied"}
       # Delete ticket...
5. Deletion succeeds ✓

Alternative:
1. Developer tries to delete → JWT: {"role": "developer"}
2. TicketsAgent checks role → "developer" not in ["admin"]
3. Returns error: "Permission denied" ✓
```

---

## Migration to OAuth 2.0

When migrating to OAuth (Phase 4), **only 2 things change:**

### 1. Auth Service Replacement
```python
# OLD (Phase 2): Custom auth service
def login(username, password):
    if validate_credentials(username, password):
        return create_jwt(username, role)

# NEW (Phase 4): OAuth client
def login():
    # Redirect to OAuth provider (Google, Okta, etc.)
    authorization_url = oauth.create_authorization_url(...)
    # User logs in at provider
    # Provider returns JWT (we validate with public key)
    return jwt_from_provider
```

### 2. JWT Validation Method
```python
# OLD (Phase 2): Symmetric key (HS256)
def verify_token(token):
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

# NEW (Phase 4): Public key (RS256)
def verify_token(token):
    # Fetch public keys from OAuth provider
    jwks = requests.get("https://auth.provider.com/.well-known/jwks.json").json()
    public_key = get_key_from_jwks(jwks, token)
    return jwt.decode(token, public_key, algorithms=["RS256"])
```

**Everything else stays the same:**
- Session state still contains `user:bearer_token`
- Agents still read from `ctx.session.state`
- Query decomposition still uses `user_id`
- Agent-to-agent calls still propagate JWT

---

## Summary

✅ **JWT tokens ARE passed to agents**
✅ **Tokens CAN be propagated between agents**
✅ **Access information (role, permissions) IS available to agents**
✅ **Agent-to-agent calls preserve auth context**
✅ **OAuth migration requires NO agent code changes**

**Key Pattern:**
```
JWT in header → Orchestrator validates → JWT in session.state → Agents access via ToolContext
```

This enables:
- User-specific data access
- Role-based access control (RBAC)
- Permission checking
- Agent-to-agent authenticated calls
- Audit logging
- OAuth 2.0 ready architecture

---

## Next Steps

Review the updated **PHASE_2_PURE_A2A_PLAN.md** which now includes:
- Complete token propagation flow diagrams
- Updated `_invoke_agent()` implementation with JWT injection
- ToolContext usage examples
- Agent-to-agent call patterns
- RBAC and permission checking examples

Ready to proceed with implementation?
