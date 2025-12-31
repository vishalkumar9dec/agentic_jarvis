# FastMCP Authentication - Implementation Guide

**Purpose**: Step-by-step code changes to migrate from manual auth to FastMCP middleware
**Time Required**: 2-4 hours for Tickets server, then replicate to others
**Difficulty**: Medium (mostly deletions, minimal additions)

---

## Phase 1: Create FastMCP Auth Provider (30 minutes)

### Step 1.1: Create Auth Provider File

**File**: `auth/fastmcp_provider.py` (NEW)

```python
"""
FastMCP Authentication Provider
Wraps existing JWT validation logic in FastMCP-compliant provider.
"""

from fastmcp.server.auth import TokenVerifier, AccessToken, AuthenticationError
from auth.jwt_utils import verify_jwt_token
from typing import Dict, Any


class JWTTokenVerifier(TokenVerifier):
    """
    FastMCP-compliant JWT token verifier.

    Wraps existing verify_jwt_token() from auth/jwt_utils.py.
    Used by BearerAuthBackend middleware to validate JWT tokens.
    """

    async def verify_token(self, token: str) -> AccessToken:
        """
        Verify JWT token and return access token with claims.

        Args:
            token: JWT token string (without "Bearer " prefix)

        Returns:
            AccessToken with user claims

        Raises:
            AuthenticationError: If token is invalid or expired
        """
        # Use existing JWT validation logic
        payload: Dict[str, Any] = verify_jwt_token(token)

        if not payload:
            raise AuthenticationError("Invalid or expired JWT token")

        # Return FastMCP AccessToken
        return AccessToken(
            token=token,
            claims=payload,  # Contains: username, user_id, role, exp
            scopes=[payload.get("role", "user")]  # For RBAC in future
        )
```

**What This Does**:
- ✅ Wraps your existing `verify_jwt_token()` function
- ✅ Converts to FastMCP's `AccessToken` format
- ✅ No changes to existing auth/jwt_utils.py needed
- ✅ Reusable across all MCP servers

---

## Phase 2: Update Tickets MCP Server (2 hours)

### Step 2.1: Add Middleware Imports

**File**: `tickets_mcp_server/server.py`

**Add these imports at the top**:
```python
# ADD these new imports
from starlette.middleware.authentication import AuthenticationMiddleware
from fastmcp.server.auth.middleware import BearerAuthBackend
from starlette.requests import Request
import sys
import os

# Add parent directory to path (if not already there)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your new auth provider
from auth.fastmcp_provider import JWTTokenVerifier
```

---

### Step 2.2: Add Middleware to MCP Server

**File**: `tickets_mcp_server/server.py`

**Find this line** (around line 80):
```python
mcp = FastMCP("tickets-server")
```

**Add middleware AFTER creating mcp**:
```python
mcp = FastMCP("tickets-server")

# ============================================================================
# Authentication Middleware (FastMCP Standard Pattern)
# ============================================================================
# This middleware:
# 1. Extracts Bearer token from Authorization header
# 2. Validates token using JWTTokenVerifier
# 3. Injects user into request.user
# 4. Automatically returns 401 for invalid tokens
# 5. Makes request.user available in all tools

mcp.add_middleware(
    AuthenticationMiddleware,
    backend=BearerAuthBackend(verifier=JWTTokenVerifier())
)
```

---

### Step 2.3: Helper Function to Access Request

**File**: `tickets_mcp_server/server.py`

**Add this helper function** (after middleware, before tools):
```python
def get_current_user() -> str:
    """
    Get authenticated username from current request.

    This helper extracts the username from the authenticated request context.
    FastMCP middleware ensures request.user is populated for authenticated requests.

    Returns:
        Username of authenticated user

    Raises:
        AuthenticationError: If user not authenticated (middleware handles this)
    """
    from starlette.requests import Request
    from fastmcp.server.dependencies import get_http_request

    request: Request = get_http_request()
    return request.user.identity["username"]
```

---

### Step 2.4: Update Authenticated Tools

**File**: `tickets_mcp_server/server.py`

#### Update `get_my_tickets()`

**BEFORE** (15 lines of boilerplate):
```python
@mcp.tool()
def get_my_tickets() -> List[Dict]:
    """Get tickets for the authenticated user."""
    # ❌ DELETE ALL THIS BOILERPLATE (lines 365-403)
    headers = get_http_headers()
    auth_header = headers.get("authorization", "")

    if not auth_header:
        return {"error": "Authentication required", "status": 401}

    if not auth_header.startswith("Bearer "):
        return {"error": "Invalid authorization header format"}

    bearer_token = auth_header[7:]
    payload = verify_jwt_token(bearer_token)

    if not payload:
        return {"error": "Invalid or expired token"}

    current_user = payload.get("username")
    if not current_user:
        return {"error": "Token missing username claim"}

    username_lower = current_user.lower()
    return [t for t in TICKETS_DB if t['user'].lower() == username_lower]
```

**AFTER** (2 lines):
```python
@mcp.tool()
def get_my_tickets() -> List[Dict]:
    """Get tickets for the authenticated user.

    Requires authentication. Middleware automatically validates token.
    Returns 401 if token is missing or invalid.

    Returns:
        List of tickets belonging to the authenticated user
    """
    # ✅ Just get user and filter - middleware handled auth
    current_user = get_current_user()
    return [t for t in TICKETS_DB if t['user'].lower() == current_user.lower()]
```

---

#### Update `create_my_ticket()`

**BEFORE** (15 lines of boilerplate):
```python
@mcp.tool()
def create_my_ticket(operation: str) -> Dict:
    """Create a new ticket for the authenticated user."""
    # ❌ DELETE ALL THIS BOILERPLATE (lines 447-506)
    headers = get_http_headers()
    auth_header = headers.get("authorization", "")

    if not auth_header:
        return {"error": "Authentication required"}

    if not auth_header.startswith("Bearer "):
        return {"error": "Invalid authorization header format"}

    bearer_token = auth_header[7:]
    payload = verify_jwt_token(bearer_token)

    if not payload:
        return {"error": "Invalid or expired token"}

    current_user = payload.get("username")
    if not current_user:
        return {"error": "Token missing username claim"}

    new_id = max([t['id'] for t in TICKETS_DB]) + 1 if TICKETS_DB else 1
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    new_ticket = {
        "id": new_id,
        "operation": operation,
        "user": current_user,
        "status": "pending",
        "created_at": now,
        "updated_at": now
    }

    TICKETS_DB.append(new_ticket)

    return {
        "success": True,
        "ticket": new_ticket,
        "message": f"Ticket {new_id} created successfully for {current_user}"
    }
```

**AFTER** (business logic only):
```python
@mcp.tool()
def create_my_ticket(operation: str) -> Dict:
    """Create a new ticket for the authenticated user.

    Requires authentication. Creates ticket for the authenticated user.

    Args:
        operation: The operation type (e.g., create_ai_key, vpn_access)

    Returns:
        Created ticket details with success status
    """
    # ✅ Get authenticated user
    current_user = get_current_user()

    # Business logic starts here
    new_id = max([t['id'] for t in TICKETS_DB]) + 1 if TICKETS_DB else 1
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    new_ticket = {
        "id": new_id,
        "operation": operation,
        "user": current_user,
        "status": "pending",
        "created_at": now,
        "updated_at": now
    }

    TICKETS_DB.append(new_ticket)

    return {
        "success": True,
        "ticket": new_ticket,
        "message": f"Ticket {new_id} created successfully for {current_user}"
    }
```

---

### Step 2.5: Remove Old Imports (Cleanup)

**File**: `tickets_mcp_server/server.py`

**Remove these imports** (no longer needed):
```python
# ❌ REMOVE - no longer needed
from fastmcp.server.dependencies import get_http_headers
# Note: We still import verify_jwt_token in auth_provider.py, not here
```

---

### Step 2.6: Update Admin Tools (Optional - Better UX)

For `get_user_tickets()` and `create_ticket()`, you can keep the admin checks OR simplify them with middleware. Here's the simplified version:

**BEFORE** (manual auth + admin check):
```python
@mcp.tool()
def get_user_tickets(username: str) -> List[Dict]:
    """Get all tickets for a specific user (Admin only)."""
    headers = get_http_headers()
    auth_header = headers.get("authorization", "")

    # 15 lines of auth boilerplate...

    user_role = payload.get("role", "")
    if user_role != "admin" and current_user.lower() != username.lower():
        return {"error": "Access denied"}

    return [t for t in TICKETS_DB if t['user'].lower() == username.lower()]
```

**AFTER** (middleware + simple admin check):
```python
@mcp.tool()
def get_user_tickets(username: str) -> List[Dict]:
    """Get all tickets for a specific user (Admin or self).

    Requires authentication.
    - Admins can view any user's tickets
    - Regular users can only view their own tickets

    Args:
        username: The username to filter tickets by

    Returns:
        List of tickets for the specified user (if authorized)
    """
    # Get authenticated user from middleware
    from starlette.requests import Request
    from fastmcp.server.dependencies import get_http_request

    request: Request = get_http_request()
    current_user = request.user.identity["username"]
    user_role = request.user.identity.get("role", "")

    # Authorization check (simplified - no boilerplate)
    if user_role != "admin" and current_user.lower() != username.lower():
        return {
            "error": "Access denied",
            "status": 403,
            "message": "You can only view your own tickets. Use 'show my tickets' instead."
        }

    # Business logic
    return [t for t in TICKETS_DB if t['user'].lower() == username.lower()]
```

---

## Phase 3: Test Changes (30 minutes)

### Step 3.1: Start Tickets Server

```bash
# Terminal 1: Start Tickets MCP server
python tickets_mcp_server/app.py

# Should see:
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://localhost:5011
```

### Step 3.2: Test Public Tool (No Auth)

```bash
# Terminal 2: Test public endpoint (should work without token)
curl -X POST http://localhost:5011/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_all_tickets",
    "arguments": {}
  }'

# Expected: Returns all 5 tickets
```

### Step 3.3: Test Authenticated Tool (No Token)

```bash
# Test authenticated endpoint WITHOUT token (should get 401)
curl -X POST http://localhost:5011/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_my_tickets",
    "arguments": {}
  }'

# Expected: 401 Unauthorized (automatic from middleware)
```

### Step 3.4: Test Authenticated Tool (With Token)

```bash
# First, get a valid JWT token
TOKEN=$(curl -X POST http://localhost:9998/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "vishal", "password": "password123"}' \
  | jq -r '.access_token')

# Test authenticated endpoint WITH token (should work)
curl -X POST http://localhost:5011/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "get_my_tickets",
    "arguments": {}
  }'

# Expected: Returns only vishal's tickets (12301, 12303)
```

### Step 3.5: Verify Line Count Reduction

```bash
# Count lines in server.py before and after
wc -l tickets_mcp_server/server.py

# Before: ~508 lines
# After:  ~450 lines (reduction of ~60 lines)
```

---

## Phase 4: Replicate to Other Servers (1-2 hours each)

### Oxygen MCP Server

**Same pattern**:
1. Add imports (Step 2.1)
2. Add middleware (Step 2.2)
3. Add `get_current_user()` helper (Step 2.3)
4. Update 4 authenticated tools:
   - `get_my_courses()`
   - `get_my_exams()`
   - `get_my_preferences()`
   - `get_my_learning_summary()`

**Files to modify**:
- `oxygen_mcp_server/server.py`

**Expected reduction**: ~60 lines

---

### FinOps MCP Server

**Same pattern** (if it has authenticated tools):
1. Add imports
2. Add middleware
3. Update authenticated tools

**Files to modify**:
- `finops_mcp_server/server.py`

---

## Phase 5: Update Agent Factory (Optional - Improved Pattern)

### Current Pattern (Works but can be simplified)

**File**: `jarvis_agent/mcp_agents/auth_context.py`

Your current `header_provider` pattern works with the middleware. No changes required on the ADK side! The middleware handles authentication on the MCP server side.

**Why it still works**:
```
ADK App → header_provider adds Authorization header
    ↓
HTTP Request with Authorization: Bearer <token>
    ↓
FastMCP Middleware extracts & validates token
    ↓
Tools access authenticated user via get_current_user()
```

---

## Validation Checklist

After completing all phases:

### Functionality
- [ ] Public tools work without authentication
- [ ] Authenticated tools require valid token
- [ ] Invalid tokens get automatic 401 response
- [ ] User isolation working (users only see their data)
- [ ] Admin tools check roles correctly

### Code Quality
- [ ] ~120 lines of boilerplate removed
- [ ] No duplicated auth code
- [ ] Centralized auth provider
- [ ] Clean tool implementations

### Security
- [ ] Tokens validated by middleware
- [ ] Automatic 401 for invalid tokens
- [ ] User context properly isolated
- [ ] Admin checks still enforced

### Testing
- [ ] All existing tests pass
- [ ] New middleware tests added
- [ ] Authentication flow tested
- [ ] Cross-user access blocked

---

## Common Issues & Solutions

### Issue 1: `get_http_request()` Not Found

**Error**:
```
NameError: name 'get_http_request' is not defined
```

**Solution**:
```python
# Add import
from fastmcp.server.dependencies import get_http_request
```

---

### Issue 2: `request.user` is None

**Error**:
```
AttributeError: 'AnonymousUser' object has no attribute 'identity'
```

**Cause**: Token not being passed or middleware not configured

**Solution**:
1. Verify middleware is added to MCP server
2. Check Authorization header is present in request
3. Verify token is valid (not expired)

**Debug**:
```python
@mcp.tool()
def debug_auth() -> Dict:
    """Debug tool to check authentication status."""
    from fastmcp.server.dependencies import get_http_request

    request = get_http_request()
    return {
        "authenticated": request.user.is_authenticated,
        "user": str(request.user),
        "identity": request.user.identity if request.user.is_authenticated else None
    }
```

---

### Issue 3: Middleware Returns 401 for Public Tools

**Error**: Public tools like `get_all_tickets()` return 401

**Cause**: Middleware is checking ALL tools, not just authenticated ones

**Solution**: FastMCP middleware should only check authenticated routes. Verify middleware configuration:

```python
# Middleware should use on_error="ignore" for public tools
# Or configure specific routes to require auth
```

**If this is an issue**, you may need to:
1. Keep public and authenticated tools in separate MCP servers, OR
2. Use route-level authentication decorators instead of global middleware

---

## Rollback Plan

If something breaks:

### Step 1: Revert Server File
```bash
git checkout tickets_mcp_server/server.py
```

### Step 2: Remove Auth Provider
```bash
rm auth/fastmcp_provider.py
```

### Step 3: Restart Server
```bash
python tickets_mcp_server/app.py
```

---

## Next Steps After Migration

1. **Add token sanitization** (prevent leakage in logs):
   ```python
   # In jarvis_agent/callbacks.py
   def after_tool_callback(tool_name, result):
       # Mask JWT tokens in results
   ```

2. **Add CORS middleware** (for Web UI):
   ```python
   from fastapi.middleware.cors import CORSMiddleware

   mcp.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:9999"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"]
   )
   ```

3. **Add rate limiting** (optional):
   ```python
   # Create custom middleware for rate limiting per user
   ```

---

## Summary

**What Changed**:
- ❌ Removed: 120 lines of manual auth boilerplate
- ✅ Added: 30 lines of centralized auth provider
- ✅ Added: Middleware configuration (5 lines per server)

**Result**:
- 🎯 75% reduction in auth code
- 🎯 Centralized authentication logic
- 🎯 Production-ready security
- 🎯 FastMCP best practices

**Time Investment**:
- Initial setup: 30 min (auth provider)
- Per server: 1-2 hours (Tickets, Oxygen, FinOps)
- Testing: 30 min per server
- **Total**: 4-6 hours for complete migration

**ROI**:
- Eliminated 120 lines of tech debt
- Production-ready architecture
- Easy OAuth 2.1 migration path (Phase 4)
- Maintainable codebase

---

**Document Version**: 1.0
**Last Updated**: 2025-12-24
**Estimated Completion**: 4-6 hours total
