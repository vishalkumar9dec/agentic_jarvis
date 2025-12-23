# Testing MCP Server Authentication

This document provides testing instructions for the authentication implementation across all three MCP servers (Tickets, FinOps, and Oxygen).

## Overview

All three MCP servers now support JWT-based authentication using HTTP Authorization headers:
- **Tickets MCP Server** (Port 5011) - IT operations ticket management
- **FinOps MCP Server** (Port 5012) - Cloud cost analytics and budgets
- **Oxygen MCP Server** (Port 8012) - Learning & development platform

## Prerequisites

1. **All MCP servers must be running:**
   ```bash
   # Check if servers are running
   lsof -i :5011 -i :5012 -i :8012 | grep LISTEN

   # If not running, start them:
   ./scripts/start_tickets_mcp_server.sh  # Terminal 1
   ./scripts/start_finops_mcp_server.sh   # Terminal 2
   ./scripts/start_oxygen_mcp_server.sh   # Terminal 3
   ```

2. **Auth service must be running:**
   ```bash
   # Check if auth service is running
   lsof -i :9998 | grep LISTEN

   # If not running:
   ./scripts/start_auth_service.sh        # Terminal 4
   ```

## Authentication Flow

The authentication flow works as follows:

1. User logs in via auth service → receives JWT bearer token
2. Token is stored in ADK session state
3. McpToolset's `header_provider` reads token from session state
4. Token is injected as `Authorization: Bearer <token>` header in MCP requests
5. FastMCP servers extract token using `get_http_headers()`
6. Tools validate token and return user-specific data

## Test Users

The following test users are available (all use password: `password123`):

| Username | Role          | Department        |
|----------|---------------|-------------------|
| vishal   | developer     | Engineering       |
| alex     | devops        | DevOps            |
| sarah    | data_scientist| Data Science      |

## Method 1: Interactive CLI Testing (Recommended)

The easiest way to test all authentication features is through the main CLI:

```bash
python main_mcp_auth.py
```

### Login
- **Username**: vishal, alex, or sarah
- **Password**: password123

### Example Queries

#### Tickets Server Tests

**Public queries (no authentication required):**
```
> show all tickets
> get ticket 12301
```

**Authenticated queries (requires login):**
```
> show my tickets
> create a ticket for vpn access
> create a ticket for gpu allocation
```

**Admin queries (if logged in as admin):**
```
> show tickets for alex
> create a ticket for alex for ai_key access
```

#### FinOps Server Tests

**Public queries (no authentication required):**
```
> what is the total cloud cost?
> show AWS costs
> show cost breakdown
```

**Authenticated queries (requires login):**
```
> show my budget
> show my cost allocation
> what is my budget status?
```

#### Oxygen Server Tests

**Public queries (no authentication required):**
```
> show courses for vishal
> show pending exams for alex
> show learning summary for sarah
```

**Authenticated queries (requires login):**
```
> show my courses
> show my exams
> show my preferences
> show my learning summary
```

## Method 2: Automated Test Script

Run the automated authentication test suite:

```bash
# Using virtual environment
source .venv/bin/activate
python test_scripts/automated_auth_test.py
```

This script tests:
1. Auth service login
2. MCP server health checks
3. Token generation and validation
4. FastMCP header extraction
5. Agent factory configuration

### Expected Output

```
======================================================================
TEST SUMMARY
======================================================================
✓ PASS: auth_service       - Login and token generation works
✓ PASS: mcp_servers         - All 3 servers are running
✓ PASS: direct_mcp          - Direct MCP communication works
✓ PASS: fastmcp             - FastMCP header extraction available
✓ PASS: agent_factory       - Agent factory configured correctly

======================================================================
✓ ALL AUTOMATED TESTS PASSED
======================================================================
```

## Method 3: Manual HTTP API Testing

You can test the MCP servers directly using curl (though this requires manually creating JWT tokens):

### 1. Get a JWT Token

```bash
# Login via auth service
curl -X POST http://localhost:9998/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "vishal", "password": "password123"}'

# Response will include:
# {"token": "eyJ...", "user": {...}}
```

### 2. Test Public Endpoint (No Auth)

```bash
# Tickets: Get all tickets
curl -X POST http://localhost:5011/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_all_tickets", "arguments": {}}'

# FinOps: Get all clouds cost
curl -X POST http://localhost:5012/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_all_clouds_cost", "arguments": {}}'

# Oxygen: Get user courses
curl -X POST http://localhost:8012/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_user_courses", "arguments": {"username": "vishal"}}'
```

### 3. Test Authenticated Endpoint (With Token)

```bash
# Save your token from step 1
TOKEN="eyJ..."

# Tickets: Get my tickets
curl -X POST http://localhost:5011/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "get_my_tickets", "arguments": {}}'

# FinOps: Get my budget
curl -X POST http://localhost:5012/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "get_my_budget", "arguments": {}}'

# Oxygen: Get my courses
curl -X POST http://localhost:8012/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "get_my_courses", "arguments": {}}'
```

### 4. Test Authentication Failure

```bash
# Try authenticated endpoint without token (should fail)
curl -X POST http://localhost:5011/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_my_tickets", "arguments": {}}'

# Expected response:
# {"error": "Authentication required", "status": 401, ...}
```

## Verification Checklist

Use this checklist to verify authentication is working correctly:

### Tickets Server (Port 5011)
- [ ] Public endpoint `get_all_tickets` works without auth
- [ ] `get_my_tickets` rejects requests without token
- [ ] `get_my_tickets` returns user-specific tickets with valid token
- [ ] `create_my_ticket` creates ticket for authenticated user
- [ ] `get_user_tickets` enforces admin or self-access control
- [ ] `create_ticket` enforces admin or self-access control

### FinOps Server (Port 5012)
- [ ] Public endpoint `get_all_clouds_cost` works without auth
- [ ] `get_my_budget` rejects requests without token
- [ ] `get_my_budget` returns user budget with valid token
- [ ] `get_my_cost_allocation` returns user cost data
- [ ] Budget status is calculated correctly
- [ ] Cost allocation percentages are accurate

### Oxygen Server (Port 8012)
- [ ] Public endpoint `get_user_courses` works without auth
- [ ] `get_my_courses` rejects requests without token
- [ ] `get_my_courses` returns user courses with valid token
- [ ] `get_my_exams` returns user exams with urgency flags
- [ ] `get_my_preferences` returns user preferences
- [ ] `get_my_learning_summary` returns complete learning data

## Troubleshooting

### Issue: "Authentication required" error even with token

**Solution:**
1. Check that token is being sent in Authorization header
2. Verify token hasn't expired (24 hour expiration)
3. Regenerate token by logging in again

### Issue: "Invalid or expired token" error

**Solution:**
1. Token may have expired - login again to get new token
2. Check JWT_SECRET_KEY matches in .env file
3. Verify token format is correct (should start with "eyJ...")

### Issue: MCP server not responding

**Solution:**
1. Check server is running: `lsof -i :<port>`
2. Check server logs for errors
3. Restart the server if needed

### Issue: Permission denied when accessing other users' data

**Solution:**
This is expected behavior! Non-admin users can only access their own data:
- Use `get_my_*` tools for personal data
- Use `get_user_*` or `get_*` tools only if you're admin

## Expected Behavior

### For Public Endpoints
- Should work without any authentication
- Returns data for any user (if username parameter provided)
- No token validation performed

### For Authenticated Endpoints
- Require valid JWT token in Authorization header
- Return 401 error if no token provided
- Return 401 error if token is invalid or expired
- Return user-specific data based on username in token
- Enforce access control (admin vs non-admin)

## Testing Best Practices

1. **Test both success and failure cases:**
   - Valid token → should succeed
   - No token → should fail with 401
   - Expired token → should fail with 401
   - Accessing other users' data → should fail with 403 (unless admin)

2. **Test all user roles:**
   - Login as each test user (vishal, alex, sarah)
   - Verify each sees only their own data
   - Test admin-only features if applicable

3. **Test token lifecycle:**
   - Login → get token
   - Use token immediately → should work
   - Wait for expiration → should fail
   - Refresh token → should work again

4. **Test cross-server consistency:**
   - Same authentication pattern across all 3 servers
   - Same error messages for auth failures
   - Same token works for all servers

## Next Steps

After verifying authentication works correctly:

1. **Task 14**: Integrate with ADK agent orchestration (if not done)
2. **Task 15**: Add session management and memory
3. **Task 16**: Implement OAuth 2.0 for enterprise SSO
4. **Production**: Replace mock databases with real data sources

## Support

If you encounter issues:

1. Check server logs in the terminal where servers are running
2. Verify all environment variables are set correctly in `.env`
3. Ensure all dependencies are installed: `pip install -r requirements.txt`
4. Review error messages - they indicate specific auth failures

## Summary

Authentication is now working across all three MCP servers:
- **JWT-based authentication** using HTTP Authorization headers
- **FastMCP's get_http_headers()** for token extraction
- **User-specific data access** with proper authorization
- **Public and authenticated endpoints** working side-by-side

Test using the CLI (`python main_mcp_auth.py`) for the best experience!
