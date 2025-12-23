# Tickets MCP Server Authentication Test Plan

**Date**: 2025-12-23
**Task**: Task 13 - Authentication Implementation
**Server**: Tickets MCP Server (Port 5011)

## Prerequisites

Ensure all required services are running:

```bash
# 1. Check Auth Service (Port 9998)
lsof -ti:9998
# Should return a PID if running
# If not running: ./scripts/start_auth_service.sh

# 2. Check Tickets MCP Server (Port 5011)
lsof -ti:5011
# Should return a PID if running
# If not running: ./scripts/start_tickets_mcp_server.sh

# 3. Check FinOps MCP Server (Port 5012)
lsof -ti:5012
# Should return a PID if running
# If not running: ./scripts/start_finops_mcp_server.sh

# 4. Check Oxygen MCP Server (Port 8012)
lsof -ti:8012
# Should return a PID if running
# If not running: ./scripts/start_oxygen_mcp_server.sh
```

## Test Cases

### Test 1: Login Flow
**Objective**: Verify that the CLI can authenticate users via the auth service.

**Steps**:
1. Run: `python main_mcp_auth.py`
2. When prompted, enter username: `vishal`
3. When prompted, enter password: `password123`

**Expected Result**:
```
✓ Login successful! Welcome, vishal!
  Role: engineer
  Email: vishal@company.com
```

**Status**: [ ] Pass [ ] Fail

---

### Test 2: Public Tools (No Authentication Required)
**Objective**: Verify that public tools work without authentication.

**Test Query**: "show all tickets"

**Expected Behavior**:
- Tool used: `tickets_get_all_tickets` (NOT `tickets_get_my_tickets`)
- Returns all 5 tickets in the system
- No authentication errors

**Expected Output**:
```
Here are all the tickets in the system:

1. Ticket #12301 - create_ai_key (vishal) - Status: pending
2. Ticket #12302 - create_gitlab_account (alex) - Status: completed
3. Ticket #12303 - update_budget (vishal) - Status: in_progress
4. Ticket #12304 - vpn_access (alex) - Status: pending
5. Ticket #12305 - gpu_allocation (sarah) - Status: approved
```

**Status**: [ ] Pass [ ] Fail

---

### Test 3: Authenticated Tools - Get My Tickets
**Objective**: Verify that authenticated tools receive bearer token via HTTP headers.

**Test Query**: "show my tickets"

**Expected Behavior**:
1. CLI sets bearer token in context: `set_bearer_token(bearer_token)`
2. McpToolset's header_provider injects: `Authorization: Bearer <token>`
3. FastMCP receives HTTP request with Authorization header
4. Tool extracts token using `get_http_headers()`
5. Token is validated
6. Returns only tickets for authenticated user (vishal)

**Expected Output**:
```
Here are your tickets, vishal:

1. Ticket #12301 - create_ai_key - Status: pending
   Created: 2025-01-10T10:00:00Z

2. Ticket #12303 - update_budget - Status: in_progress
   Created: 2025-01-11T09:15:00Z
```

**Status**: [ ] Pass [ ] Fail

**Failure Indicators**:
- Returns error: "Authentication required" → Token not passed
- Returns all tickets → Used wrong tool (get_all_tickets)
- Returns error: "Invalid token" → Token validation failed

---

### Test 4: Authenticated Tools - Create My Ticket
**Objective**: Verify that ticket creation uses authenticated user from JWT token.

**Test Query**: "create a ticket for VPN access"

**Expected Behavior**:
1. Tool used: `tickets_create_my_ticket`
2. Token extracted from HTTP Authorization header
3. User identity extracted from JWT payload
4. Ticket created with `user: vishal` (from token, not parameter)

**Expected Output**:
```
✓ Ticket created successfully!

Ticket #12306
Operation: vpn_access
User: vishal
Status: pending
Created: [current timestamp]
```

**Verification**:
After creating the ticket, run "show my tickets" again. The new ticket should appear in the list.

**Status**: [ ] Pass [ ] Fail

**Failure Indicators**:
- Ticket created with wrong user → Token not validated correctly
- Error: "Authentication required" → Token not passed in header
- Tool not found → Agent routing issue

---

### Test 5: Cross-User Isolation
**Objective**: Verify that users only see their own tickets.

**Steps**:
1. Exit current session (type `exit`)
2. Restart CLI: `python main_mcp_auth.py`
3. Login as `alex` (password: `password123`)
4. Run query: "show my tickets"

**Expected Output**:
```
Here are your tickets, alex:

1. Ticket #12302 - create_gitlab_account - Status: completed
2. Ticket #12304 - vpn_access - Status: pending
```

**Verification**:
- Should NOT see vishal's tickets (#12301, #12303)
- Should NOT see sarah's ticket (#12305)
- Should ONLY see alex's tickets (#12302, #12304)

**Status**: [ ] Pass [ ] Fail

---

### Test 6: Authentication Error Handling
**Objective**: Verify graceful handling of authentication failures.

**Note**: This test requires manually modifying the code temporarily. Skip for now.

**Scenario A**: Missing Authorization Header
- Modify `auth_context.py` to return empty headers temporarily
- Expected: "Authentication required" error

**Scenario B**: Invalid Token Format
- Modify header to send "InvalidToken123" instead of "Bearer <token>"
- Expected: "Invalid authorization header format" error

**Scenario C**: Expired Token
- Use a token with past expiration time
- Expected: "Your session has expired. Please log in again."

**Status**: [ ] Pass [ ] Fail [ ] Skipped

---

## Test Execution Checklist

**Pre-Test Setup**:
- [x] Auth service running on port 9998
- [x] Tickets MCP server running on port 5011
- [x] FinOps MCP server running on port 5012
- [x] Oxygen MCP server running on port 8012
- [ ] Virtual environment activated
- [ ] GOOGLE_API_KEY set in .env

**Test Execution**:
- [ ] Test 1: Login Flow
- [ ] Test 2: Public Tools
- [ ] Test 3: Get My Tickets
- [ ] Test 4: Create My Ticket
- [ ] Test 5: Cross-User Isolation
- [ ] Test 6: Error Handling (Optional)

**Post-Test Verification**:
- [ ] No Python errors in CLI output
- [ ] No authentication errors in MCP server logs
- [ ] All expected tools called correctly
- [ ] User isolation working properly

---

## Debugging Tips

### If authentication fails:

1. **Check token is being set**:
   - Add debug print in `main_mcp_auth.py` after `set_bearer_token(bearer_token)`:
     ```python
     print(f"DEBUG: Bearer token set: {bearer_token[:20]}...")
     ```

2. **Check header provider is being called**:
   - Add debug print in `auth_context.py` in the `header_provider` function:
     ```python
     def header_provider() -> Dict[str, str]:
         token = get_bearer_token()
         print(f"DEBUG: Header provider called, token: {token[:20] if token else 'None'}...")
         if token:
             return {"Authorization": f"Bearer {token}"}
         return {}
     ```

3. **Check headers received by MCP server**:
   - Add debug print in `tickets_mcp_server/server.py` in `get_my_tickets`:
     ```python
     headers = get_http_headers()
     print(f"DEBUG: Headers received: {headers}")
     auth_header = headers.get("authorization", "")
     ```

4. **Check MCP server logs**:
   ```bash
   tail -f /tmp/tickets_mcp_test.log
   ```

5. **Verify token is valid**:
   - Test token validation separately:
     ```python
     from auth.jwt_utils import verify_jwt_token
     payload = verify_jwt_token(bearer_token)
     print(f"Token payload: {payload}")
     ```

---

## Success Criteria

✅ **All tests pass if**:
1. Login succeeds for all users (vishal, alex, sarah)
2. Public tools work without authentication
3. Authenticated tools receive and validate bearer token
4. Users only see their own tickets
5. Ticket creation uses authenticated user from JWT
6. No authentication errors in normal flow

---

## Next Steps After Successful Testing

Once tickets_mcp_server authentication is confirmed working:

1. **Replicate to FinOps MCP Server**:
   - Update `finops_mcp_server/server.py` (no authenticated tools yet)
   - Verify server starts without errors

2. **Replicate to Oxygen MCP Server**:
   - Update `oxygen_mcp_server/server.py`
   - Update 4 authenticated tools:
     - `get_my_courses()`
     - `get_my_exams()`
     - `get_my_preferences()`
     - `get_my_learning_summary()`
   - Test with queries like "show my courses", "show my pending exams"

3. **Update Documentation**:
   - Update `AUTHENTICATION_FLOW.md`
   - Update `MCP_CORRECT_IMPLEMENTATION.md`
   - Create migration guide

4. **Complete Task 13**:
   - Mark task as complete
   - Proceed to Task 14 (Web UI with authentication)

---

## Notes

- FastMCP `get_http_headers()` returns lowercase header names (e.g., "authorization" not "Authorization")
- Bearer token format: `Authorization: Bearer <token>`
- Token extraction: `auth_header[7:]` removes "Bearer " prefix
- JWT validation uses `auth/jwt_utils.py`
- Tokens expire after 1 hour (configurable in auth service)
