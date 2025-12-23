# Task 13 - Authentication Testing Instructions

## Overview

This document provides step-by-step instructions to test the JWT authentication implementation in the Jarvis MCP system. The implementation uses the official Google ADK pattern with `EventActions` and session state management.

## What Was Implemented

### Core Components

1. **Session State Management** (`main_mcp_auth.py`)
   - JWT bearer token stored in session state using `EventActions` with `state_delta`
   - Token persists across agent calls within the same session
   - Official ADK pattern from Loop Agents documentation

2. **Header Provider** (`jarvis_agent/mcp_agents/auth_context.py`)
   - Extracts bearer token from `context.session.state`
   - Injects `Authorization: Bearer <token>` header into MCP HTTP requests
   - Thread-safe and async-safe using contextvars

3. **Authenticated MCP Tools** (`tickets_mcp_server/server.py`)
   - `get_my_tickets()` - Returns tickets for authenticated user only
   - `create_my_ticket(operation)` - Creates ticket for authenticated user
   - Token extraction using FastMCP's `get_http_headers()`
   - JWT validation using shared auth utilities

## Prerequisites

Before testing, ensure all services are running:

### 1. Start Auth Service
```bash
# Terminal 1
./scripts/start_auth_service.sh
```

**Verify**: Should see `Auth service running on http://localhost:9998`

### 2. Start Tickets MCP Server
```bash
# Terminal 2
./scripts/start_tickets_mcp_server.sh
```

**Verify**: Should see `FastMCP server running on port 5011`

### 3. Start FinOps MCP Server
```bash
# Terminal 3
./scripts/start_finops_mcp_server.sh
```

**Verify**: Should see `FastMCP server running on port 5012`

### 4. Start Oxygen MCP Server
```bash
# Terminal 4
./scripts/start_oxygen_mcp_server.sh
```

**Verify**: Should see `FastMCP server running on port 8012`

## Test Scenarios

### Test 1: Login Flow

**Objective**: Verify JWT authentication works correctly

**Steps**:
```bash
# Terminal 5
python main_mcp_auth.py
```

**Expected Output**:
```
======================================================================
  JARVIS - MCP Version with Authentication (Phase 2 - Part B)
  Task 13: ADK Runner Pattern + JWT Authentication
======================================================================

======================================================================
  LOGIN
======================================================================

  Available users: vishal, alex, sarah
  Password for all: password123

Username: vishal
Password: [hidden]

✓ Login successful! Welcome, vishal!
  Role: developer
  Email: vishal@company.com

======================================================================
  JARVIS SESSION
======================================================================

  Connected to MCP servers:
    - Tickets MCP: http://localhost:5011/mcp
    - FinOps MCP: http://localhost:5012/mcp
    - Oxygen MCP: http://localhost:8012/mcp

  Authenticated as: vishal

Initializing Jarvis MCP agent... ✓
Creating session... ✓
Creating ADK Runner... ✓

Ready! Ask me anything about tickets, costs, or learning.

vishal>
```

**✅ Pass Criteria**:
- Login succeeds with correct credentials
- Session initialization completes without errors
- All three checkmarks (✓) appear

**❌ Fail Indicators**:
- Login fails with valid credentials
- Connection errors to MCP servers
- Session creation errors

---

### Test 2: Public Tools (No Authentication Required)

**Objective**: Verify public tools work without authentication

**Query**:
```
show all tickets
```

**Expected Behavior**:
- Should return ALL 5 tickets in the system
- Includes tickets from vishal, alex, and sarah
- No authentication errors

**Expected Tickets**:
- Ticket 12301 (vishal) - create_ai_key - pending
- Ticket 12302 (alex) - create_gitlab_account - completed
- Ticket 12303 (vishal) - update_budget - in_progress
- Ticket 12304 (alex) - vpn_access - pending
- Ticket 12305 (sarah) - gpu_allocation - approved

**✅ Pass Criteria**:
- All 5 tickets displayed
- No authentication errors
- Data matches expected values

---

### Test 3: Authenticated Tools - User Isolation

**Objective**: Verify authenticated users only see their own data

**Login as**: vishal

**Query**:
```
show my tickets
```

**Expected Output**:
```
Here are your tickets:

* Ticket ID: 12301
    * Operation: create_ai_key
    * User: vishal
    * Status: pending
* Ticket ID: 12303
    * Operation: update_budget
    * User: vishal
    * Status: in_progress
```

**✅ Pass Criteria**:
- Only 2 tickets returned (12301, 12303)
- Both tickets belong to vishal
- No tickets from alex or sarah visible
- No authentication errors

**❌ Fail Indicators**:
- Returns authentication error
- Shows tickets from other users
- Shows all 5 tickets instead of user-specific

---

### Test 4: Create Authenticated Ticket

**Objective**: Verify ticket creation with authenticated user

**Login as**: vishal

**Query**:
```
create a ticket for vpn access
```

**Expected Behavior**:
- Agent calls `create_my_ticket(operation="vpn_access")`
- Ticket created automatically for vishal (from JWT token)
- New ticket ID assigned (likely 12306)
- Success message displayed

**Expected Output**:
```
I've created a ticket for VPN access.

Ticket Details:
- ID: 12306
- Operation: vpn_access
- User: vishal
- Status: pending
- Created: [timestamp]
```

**Verification**:
```
show my tickets
```

Should now show 3 tickets (12301, 12303, 12306)

**✅ Pass Criteria**:
- Ticket created successfully
- Ticket assigned to vishal (not requiring username parameter)
- New ticket visible in "show my tickets"

---

### Test 5: Cross-User Isolation

**Objective**: Verify different users see different data

**Test Steps**:

1. **Exit current session**: Type `exit`

2. **Login as alex**:
```bash
python main_mcp_auth.py
```
Username: alex
Password: password123

3. **Query**:
```
show my tickets
```

**Expected Output**:
- Ticket 12302 (alex) - create_gitlab_account - completed
- Ticket 12304 (alex) - vpn_access - pending

**✅ Pass Criteria**:
- Only alex's tickets visible
- No vishal or sarah tickets
- Different data than vishal's session

4. **Create ticket for alex**:
```
create a ticket for gpu allocation
```

**Expected Behavior**:
- Ticket created for alex automatically
- Not visible to vishal

5. **Verify isolation**:
- Exit alex's session
- Login as vishal again
- Run `show my tickets`
- Should NOT see alex's new ticket

---

### Test 6: Invalid Token Handling

**Objective**: Verify system handles expired/invalid tokens gracefully

**This test requires manual token manipulation** - For future implementation when tokens have expiration.

Currently, tokens don't expire, so this is N/A for now.

---

### Test 7: Public vs Authenticated Tool Selection

**Objective**: Verify agent correctly selects authenticated vs public tools

**Test Queries**:

| Query | Expected Tool | Notes |
|-------|---------------|-------|
| "show all tickets" | `get_all_tickets()` | Public - no auth |
| "show my tickets" | `get_my_tickets()` | Authenticated |
| "show tickets for alex" | `get_user_tickets(username="alex")` | Public with param |
| "create a ticket for me to get vpn" | `create_my_ticket()` | Authenticated |
| "create a ticket for sarah to get vpn" | `create_ticket(user="sarah")` | Public with params |

**✅ Pass Criteria**:
- Agent selects correct tool based on query intent
- Authenticated tools work when user says "my"
- Public tools work when user specifies other usernames

---

## Success Metrics

### Must Pass (Critical)
- ✅ Login flow works for all users (vishal, alex, sarah)
- ✅ User isolation: Users only see their own tickets via `get_my_tickets()`
- ✅ Token injection: Authorization header present in MCP requests
- ✅ Token validation: Invalid tokens rejected with 401 error
- ✅ Authenticated ticket creation assigns correct username

### Should Pass (Important)
- ✅ Public tools work without authentication
- ✅ Agent selects appropriate tool (public vs authenticated)
- ✅ No errors during session initialization
- ✅ Clean startup without debug logging

### Nice to Have
- ✅ User-friendly error messages
- ✅ Helpful suggestions after responses
- ✅ Proper session cleanup on exit

## Known Limitations

1. **Token Expiration**: Current implementation uses tokens without expiration. Production should implement expiration and refresh logic.

2. **Token Storage**: Tokens stored in memory only. Production should use secure session storage.

3. **HTTPS**: Currently using HTTP. Production must use HTTPS for secure token transmission.

4. **Rate Limiting**: No rate limiting implemented. Production should add rate limiting per user.

## Troubleshooting

### Issue: Login fails with "Auth service not running"
**Solution**:
```bash
# Check if auth service is running
lsof -i :9998

# If not running, start it
./scripts/start_auth_service.sh
```

### Issue: "Failed to create agent" error
**Solution**:
```bash
# Check all MCP servers are running
lsof -i :5011  # Tickets
lsof -i :5012  # FinOps
lsof -i :8012  # Oxygen

# Start missing servers
./scripts/start_tickets_mcp_server.sh
./scripts/start_finops_mcp_server.sh
./scripts/start_oxygen_mcp_server.sh
```

### Issue: "Authentication required" when using authenticated tools
**Possible Causes**:
1. Token not stored in session state correctly
2. Header provider not injecting token
3. FastMCP not receiving Authorization header

**Debug Steps**:
1. Check session state was updated (should see "Creating session... ✓")
2. Verify header_provider is configured in agent_factory.py
3. Check MCP server logs for incoming headers

### Issue: Shows all tickets instead of user-specific
**Problem**: Agent calling wrong tool (get_all_tickets vs get_my_tickets)

**Solution**: Rephrase query to use "my" keyword:
- ❌ "show tickets" → may call get_all_tickets
- ✅ "show my tickets" → calls get_my_tickets

## Next Steps After Successful Testing

Once all tests pass:

1. **Confirm with team**: "Authentication working as expected for Tickets MCP Server"

2. **Replicate to Oxygen MCP Server**: Apply same pattern to oxygen_mcp_server for:
   - `get_my_courses()`
   - `get_my_pending_exams()`
   - `enroll_in_course(course_name)`
   - `get_my_learning_dashboard()`

3. **Update Web UI**: Implement authentication in web UI (Task 14)

4. **Final testing**: End-to-end testing across all MCP servers (Task 15)

5. **Documentation**: Update all authentication docs with final patterns (Task 16)

## Reference Files

- Implementation: `main_mcp_auth.py`
- Auth Context: `jarvis_agent/mcp_agents/auth_context.py`
- Tickets Server: `tickets_mcp_server/server.py`
- Agent Factory: `jarvis_agent/mcp_agents/agent_factory.py`
- Documentation: `docs/AUTHENTICATION_IMPLEMENTATION_DECISION.md`

## Test Evidence

Save test outputs to demonstrate successful implementation:

```bash
# Run authenticated CLI and save output
python main_mcp_auth.py > /tmp/auth_test_output.txt 2>&1

# Test queries to run:
# 1. show all tickets
# 2. show my tickets
# 3. create a ticket for vpn access
# 4. show my tickets (verify new ticket)
# 5. exit
```

Share the output file for verification.
