# OAuth 2.1 Migration Path - After FastMCP Middleware

**Purpose**: Show how OAuth 2.1 migration becomes trivial after implementing FastMCP middleware
**Timeline**: 1-2 weeks (vs 4-6 weeks without middleware)
**Complexity**: Low (swap provider vs complete rewrite)

---

## Executive Summary

**Key Insight**: If you implement FastMCP middleware NOW, OAuth 2.1 migration (Phase 4) becomes **a simple provider swap** instead of a complete rewrite.

### With FastMCP Middleware (Recommended)
```python
# Phase 2: JWT Authentication
verifier = JWTTokenVerifier()  # 30 lines

# Phase 4: OAuth 2.1 (just swap the provider!)
verifier = OAuthProvider(  # 50 lines
    issuer="https://accounts.google.com",
    client_id="...",
    client_secret="..."
)

# MCP servers: NO CHANGES NEEDED ✅
# Tools: NO CHANGES NEEDED ✅
# Middleware config: SAME ✅
```

**Effort**: 1-2 weeks, ~50 lines of code changes

---

### Without FastMCP Middleware (Current)
```python
# Phase 2: Manual JWT in every tool
# tickets_mcp_server/server.py - 60 lines
# oxygen_mcp_server/server.py - 60 lines

# Phase 4: OAuth 2.1 (rewrite EVERYTHING!)
# - Rewrite all 8 authenticated tools ❌
# - Implement OAuth flow in each server ❌
# - Update token validation logic 8+ times ❌
# - Add redirect handling ❌
# - Add state management ❌
# - Test all combinations ❌
```

**Effort**: 4-6 weeks, ~300 lines of code changes

---

## Current State vs OAuth 2.1

### Authentication Flow Comparison

#### Current: JWT (Phase 2)
```
┌─────────────────────────────────────────────┐
│  1. User Login (Custom Auth Server)         │
│     POST /auth/login                         │
│     {"username": "vishal", "password": "..."}│
│     → Returns JWT token                      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼ JWT token
┌─────────────────────────────────────────────┐
│  2. Client Stores Token                      │
│     localStorage / session.state             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼ Authorization: Bearer <jwt>
┌─────────────────────────────────────────────┐
│  3. MCP Servers Validate JWT                 │
│     - Extract from header                    │
│     - Verify signature                       │
│     - Check expiration                       │
│     - Return user claims                     │
└─────────────────────────────────────────────┘
```

---

#### Future: OAuth 2.1 (Phase 4)
```
┌─────────────────────────────────────────────┐
│  1. User Clicks "Login with Google"         │
│     → Redirect to Google/Azure/Okta          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  2. OAuth Provider (Google/Azure/Okta)       │
│     - User authenticates                     │
│     - User grants permissions                │
│     → Returns authorization code             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼ Authorization code
┌─────────────────────────────────────────────┐
│  3. Auth Server Exchanges Code for Token    │
│     POST /oauth/token                        │
│     → Returns access_token + refresh_token   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼ Access token
┌─────────────────────────────────────────────┐
│  4. Client Stores Token                      │
│     localStorage / session.state             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼ Authorization: Bearer <oauth_token>
┌─────────────────────────────────────────────┐
│  5. MCP Servers Validate OAuth Token         │
│     - Extract from header (SAME!)            │
│     - Validate via introspection OR          │
│     - Validate JWT if token is JWT           │
│     - Return user claims                     │
└─────────────────────────────────────────────┘
```

**Key Difference**: OAuth uses external identity provider (Google/Azure/Okta) instead of custom auth server.

**MCP Server Impact**: ✅ **NONE** - Token validation interface stays the same!

---

## FastMCP OAuth 2.1 Support

FastMCP provides built-in OAuth 2.1 implementation in `/fastmcp/server/auth/`:

### Available OAuth Components

#### 1. `OAuthProvider` Base Class
```python
# From fastmcp/server/auth/oauth_provider.py

class OAuthProvider(AuthProvider):
    """
    OAuth 2.1 authorization server provider.

    Supports:
    - Authorization Code Flow (with PKCE)
    - Client Credentials Flow
    - Token introspection
    - Token refresh
    - Token revocation
    """

    def __init__(
        self,
        issuer: str,
        client_id: str,
        client_secret: str,
        authorization_endpoint: str,
        token_endpoint: str,
        introspection_endpoint: str = None,
        revocation_endpoint: str = None,
        scopes: List[str] = None
    ):
        pass

    async def verify_token(self, token: str) -> AccessToken:
        """
        Verify OAuth token via introspection endpoint.

        This supports:
        - Token revocation (can't do with local JWT)
        - Centralized user management
        - Real-time permission changes
        """
        pass
```

---

#### 2. OAuth Endpoints (Auto-generated)
```python
# From fastmcp/server/auth/routes.py

def create_oauth_routes(provider: OAuthProvider):
    """
    Creates OAuth 2.1 compliant endpoints:

    - GET  /oauth/authorize   - Authorization request
    - POST /oauth/token       - Token exchange
    - POST /oauth/revoke      - Token revocation
    - POST /oauth/introspect  - Token introspection
    - GET  /.well-known/oauth-authorization-server - Discovery
    """
    pass
```

---

#### 3. OAuth Middleware (Same as JWT!)
```python
# Middleware configuration is IDENTICAL
mcp.add_middleware(
    AuthenticationMiddleware,
    backend=BearerAuthBackend(
        verifier=OAuthProvider(...)  # ← Just swap provider!
    )
)
```

---

## Migration: JWT → OAuth 2.1

### Scenario A: With FastMCP Middleware (After Migration)

#### Step 1: Create OAuth Provider (1 day)

**File**: `auth/oauth_provider.py` (NEW - replaces `auth/fastmcp_provider.py`)

```python
"""
OAuth 2.1 Provider for Google Workspace SSO
Uses FastMCP's OAuthProvider base class.
"""

from fastmcp.server.auth import OAuthProvider, AccessToken, AuthenticationError
from typing import Optional
import os


class GoogleOAuthProvider(OAuthProvider):
    """
    Google Workspace OAuth 2.1 provider.

    Validates OAuth tokens from Google Identity Platform.
    Supports token introspection and revocation.
    """

    def __init__(self):
        super().__init__(
            issuer="https://accounts.google.com",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            token_endpoint="https://oauth2.googleapis.com/token",
            introspection_endpoint="https://oauth2.googleapis.com/tokeninfo",
            revocation_endpoint="https://oauth2.googleapis.com/revoke",
            scopes=["openid", "email", "profile"]
        )

    async def verify_token(self, token: str) -> AccessToken:
        """
        Verify OAuth token via Google's tokeninfo endpoint.

        This enables:
        - Real-time token revocation
        - Centralized user management in Google Workspace
        - No need to store user passwords
        """
        # FastMCP's OAuthProvider handles introspection automatically
        return await super().verify_token(token)

    async def get_user_info(self, access_token: AccessToken) -> dict:
        """
        Fetch user profile from Google.

        Returns user info like email, name, picture.
        """
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token.token}"}
            )

            if response.status_code != 200:
                raise AuthenticationError("Failed to fetch user info")

            return response.json()
```

---

#### Step 2: Update MCP Servers (30 min total)

**Change Required**: Just swap the import! That's it!

**Before** (JWT):
```python
# tickets_mcp_server/server.py
from auth.fastmcp_provider import JWTTokenVerifier

mcp.add_middleware(
    AuthenticationMiddleware,
    backend=BearerAuthBackend(verifier=JWTTokenVerifier())
)
```

**After** (OAuth):
```python
# tickets_mcp_server/server.py
from auth.oauth_provider import GoogleOAuthProvider  # ← Only change!

mcp.add_middleware(
    AuthenticationMiddleware,
    backend=BearerAuthBackend(verifier=GoogleOAuthProvider())  # ← Only change!
)
```

**Files to Update** (10 min each):
- `tickets_mcp_server/server.py` - Change 1 line
- `oxygen_mcp_server/server.py` - Change 1 line
- `finops_mcp_server/server.py` - Change 1 line

**Tools**: ✅ **NO CHANGES NEEDED**

All authenticated tools continue to work unchanged:
```python
@mcp.tool()
def get_my_tickets() -> List[Dict]:
    # ✅ Still works - no changes needed!
    current_user = get_current_user()
    return [t for t in TICKETS_DB if t['user'] == current_user]
```

---

#### Step 3: Update Auth Service (3-5 days)

**Option A: Use FastMCP's Built-in OAuth Server**

**File**: `auth/oauth_server.py` (NEW)

```python
"""
OAuth 2.1 Authorization Server using FastMCP.
Replaces custom auth server (port 9998).
"""

from fastmcp import FastMCP
from fastmcp.server.auth import OAuthAuthorizationServer
from fastmcp.server.auth.routes import create_oauth_routes

# Create OAuth authorization server
oauth_server = OAuthAuthorizationServer(
    issuer="http://localhost:9998",
    client_id=os.getenv("OAUTH_CLIENT_ID"),
    client_secret=os.getenv("OAUTH_CLIENT_SECRET"),

    # User store (migrate from auth/user_service.py)
    user_store=UserStore(),

    # Token storage (Redis/Database)
    token_store=RedisTokenStore(),

    # Configuration
    token_expiration=3600,  # 1 hour
    refresh_token_expiration=86400 * 30,  # 30 days

    # OAuth flows
    flows=["authorization_code", "refresh_token"]
)

# Create MCP server for OAuth endpoints
mcp = FastMCP("oauth-server")

# Add OAuth routes (automatic!)
oauth_routes = create_oauth_routes(oauth_server)
mcp.mount("/oauth", oauth_routes)

# Now your auth server supports OAuth 2.1!
# Endpoints auto-created:
# - GET  /oauth/authorize
# - POST /oauth/token
# - POST /oauth/revoke
# - POST /oauth/introspect
```

**Option B: Use External OAuth Provider (Google/Azure/Okta)**

This is even simpler - no auth server needed!

```python
# Just configure MCP servers to validate tokens from Google
from auth.oauth_provider import GoogleOAuthProvider

# MCP servers validate Google-issued tokens
mcp.add_middleware(
    AuthenticationMiddleware,
    backend=BearerAuthBackend(verifier=GoogleOAuthProvider())
)
```

---

#### Step 4: Update Web UI (2-3 days)

**Change Required**: Update login flow to use OAuth

**Before** (JWT):
```javascript
// web_ui/static/login.html
async function login() {
    const response = await fetch('http://localhost:9998/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    });

    const data = await response.json();
    localStorage.setItem('token', data.access_token);
}
```

**After** (OAuth - Google Sign-In):
```javascript
// web_ui/static/login.html
async function loginWithGoogle() {
    // Redirect to OAuth authorization endpoint
    const authUrl = new URL('http://localhost:9998/oauth/authorize');
    authUrl.searchParams.set('client_id', CLIENT_ID);
    authUrl.searchParams.set('redirect_uri', 'http://localhost:9999/callback');
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('scope', 'openid email profile');

    window.location.href = authUrl.toString();
}

// web_ui/static/callback.html (NEW - OAuth callback handler)
async function handleCallback() {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');

    // Exchange authorization code for access token
    const response = await fetch('http://localhost:9998/oauth/token', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            grant_type: 'authorization_code',
            code: code,
            redirect_uri: 'http://localhost:9999/callback'
        })
    });

    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);  // NEW!

    window.location.href = '/chat.html';
}
```

**Token in ADK Session** (NO CHANGES!):
```python
# web_ui/server.py - SAME as before!
session.state["bearer_token"] = bearer_token  # ✅ Still works
```

---

#### Step 5: Test & Deploy (1-2 days)

```bash
# Test OAuth flow
1. Click "Login with Google"
2. Authenticate with Google
3. Redirect back with authorization code
4. Exchange code for access token
5. Use token to access MCP tools

# All existing tests still work!
curl -X POST http://localhost:5011/tools/call \
  -H "Authorization: Bearer <oauth_token>" \
  -d '{"name": "get_my_tickets", "arguments": {}}'
```

---

### Scenario B: Without FastMCP Middleware (Current)

If you DON'T implement FastMCP middleware, OAuth migration requires:

#### Changes Required (Nightmare!)

1. **Rewrite All Authenticated Tools** (8 tools × 30 min = 4 hours)
   ```python
   # BEFORE (JWT - manual validation)
   @mcp.tool()
   def get_my_tickets():
       headers = get_http_headers()
       bearer_token = headers.get("authorization", "")[7:]
       payload = verify_jwt_token(bearer_token)  # ← JWT validation
       # ...

   # AFTER (OAuth - manual validation)
   @mcp.tool()
   def get_my_tickets():
       headers = get_http_headers()
       bearer_token = headers.get("authorization", "")[7:]
       payload = verify_oauth_token(bearer_token)  # ← NEW: OAuth validation
       # ...
   ```

   **Problem**: Change same code in 8+ places!

2. **Implement OAuth Validation** (2 days)
   ```python
   # Create new function for every server
   def verify_oauth_token(token: str) -> dict:
       # Call introspection endpoint
       # Handle token revocation
       # Parse user claims
       # Error handling
       # ...
   ```

3. **Update Error Handling** (1 day)
   - OAuth errors different from JWT errors
   - Update 8+ tools with new error messages

4. **Add Token Refresh** (2 days)
   - Implement refresh logic in every tool
   - Or add to session management
   - Test all combinations

5. **Testing** (3 days)
   - Test all 8 tools with OAuth
   - Test token refresh
   - Test revocation
   - Test error cases

**Total Effort**: 4-6 weeks, ~300 lines of changes

---

## Code Comparison: OAuth Migration Effort

### With FastMCP Middleware

**Changes Required**:
```python
# 1. Create OAuth provider (50 lines) - NEW FILE
# auth/oauth_provider.py
class GoogleOAuthProvider(OAuthProvider):
    def __init__(self):
        super().__init__(issuer="https://accounts.google.com", ...)

# 2. Update MCP servers (1 line each × 3 servers = 3 lines)
# tickets_mcp_server/server.py
- from auth.fastmcp_provider import JWTTokenVerifier
+ from auth.oauth_provider import GoogleOAuthProvider

- backend=BearerAuthBackend(verifier=JWTTokenVerifier())
+ backend=BearerAuthBackend(verifier=GoogleOAuthProvider())

# 3. Tools: NO CHANGES (0 lines)
# All tools continue to work unchanged!

# TOTAL: ~55 lines changed
```

**Timeline**: 1-2 weeks

---

### Without FastMCP Middleware

**Changes Required**:
```python
# 1. Create OAuth validation function (100 lines) - NEW
# auth/oauth_utils.py
def verify_oauth_token(token: str) -> dict:
    # Introspection logic
    # Error handling
    # User claim parsing
    # ...

# 2. Update EVERY authenticated tool (8 tools × 25 lines = 200 lines)
# tickets_mcp_server/server.py
@mcp.tool()
def get_my_tickets():
-   payload = verify_jwt_token(bearer_token)
+   payload = verify_oauth_token(bearer_token)
    # Update error handling
    # Update claim parsing
    # Add refresh logic
    # ...

# 3. Duplicate across all servers
# oxygen_mcp_server/server.py - Same changes
# finops_mcp_server/server.py - Same changes

# TOTAL: ~300 lines changed
```

**Timeline**: 4-6 weeks

---

## Benefits Matrix: FastMCP Middleware for OAuth

| Aspect | Without Middleware | With Middleware | Benefit |
|--------|-------------------|-----------------|---------|
| **Code Changes** | ~300 lines | ~55 lines | 📉 82% reduction |
| **Files Modified** | 10+ files | 4 files | 📉 60% reduction |
| **Migration Time** | 4-6 weeks | 1-2 weeks | ⏱️ 75% faster |
| **Testing Effort** | High (8+ tools) | Low (provider only) | ✅ Easier |
| **Risk** | High (many changes) | Low (isolated change) | ✅ Safer |
| **Rollback** | Difficult | Easy (swap provider) | ✅ Flexible |
| **Multi-Provider** | Rewrite per provider | Configure provider | ✅ Scalable |

---

## OAuth 2.1 Providers Supported by FastMCP

### Enterprise SSO Providers

#### 1. Google Workspace
```python
GoogleOAuthProvider(
    issuer="https://accounts.google.com",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
)
```

**Features**:
- ✅ Email-based user identification
- ✅ Profile pictures
- ✅ Organization-wide SSO
- ✅ Multi-factor authentication
- ✅ Admin-managed users

---

#### 2. Microsoft Azure AD
```python
AzureOAuthProvider(
    issuer="https://login.microsoftonline.com/{tenant_id}/v2.0",
    client_id=os.getenv("AZURE_CLIENT_ID"),
    client_secret=os.getenv("AZURE_CLIENT_SECRET")
)
```

**Features**:
- ✅ Active Directory integration
- ✅ Conditional access policies
- ✅ Enterprise groups and roles
- ✅ B2B guest access

---

#### 3. Okta
```python
OktaOAuthProvider(
    issuer=f"https://{domain}.okta.com/oauth2/default",
    client_id=os.getenv("OKTA_CLIENT_ID"),
    client_secret=os.getenv("OKTA_CLIENT_SECRET")
)
```

**Features**:
- ✅ Universal Directory
- ✅ Adaptive MFA
- ✅ Lifecycle management
- ✅ Custom claims

---

#### 4. Auth0
```python
Auth0OAuthProvider(
    issuer=f"https://{domain}.auth0.com",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET")
)
```

**Features**:
- ✅ Social login (Google, GitHub, etc.)
- ✅ Custom databases
- ✅ Passwordless auth
- ✅ Advanced security

---

### Multiple Provider Support

**With FastMCP Middleware**, you can support MULTIPLE OAuth providers simultaneously:

```python
# auth/oauth_providers.py
def get_oauth_provider(provider_name: str) -> OAuthProvider:
    """Factory for multiple OAuth providers."""

    providers = {
        "google": GoogleOAuthProvider(),
        "azure": AzureOAuthProvider(),
        "okta": OktaOAuthProvider(),
        "auth0": Auth0OAuthProvider()
    }

    return providers.get(provider_name)


# MCP server detects provider from token issuer
class MultiOAuthVerifier(TokenVerifier):
    """Supports multiple OAuth providers."""

    async def verify_token(self, token: str) -> AccessToken:
        # Decode token to get issuer (without verification)
        issuer = decode_token_issuer(token)

        # Route to correct provider
        if "google" in issuer:
            return await GoogleOAuthProvider().verify_token(token)
        elif "microsoft" in issuer:
            return await AzureOAuthProvider().verify_token(token)
        elif "okta" in issuer:
            return await OktaOAuthProvider().verify_token(token)

        raise AuthenticationError("Unsupported OAuth provider")
```

**Use in MCP server**:
```python
mcp.add_middleware(
    AuthenticationMiddleware,
    backend=BearerAuthBackend(verifier=MultiOAuthVerifier())
)
```

**Result**: Users can login with Google, Azure, or Okta - MCP servers accept all!

---

## ROI: Implementing FastMCP Middleware NOW

### Investment (Phase 2 - Now)
- **Time**: 2-3 weeks
- **Effort**: Remove 120 lines of boilerplate, add 30 lines of provider
- **Cost**: Medium upfront effort

### Return (Phase 4 - OAuth)
- **Time Saved**: 3-4 weeks (from 4-6 weeks → 1-2 weeks)
- **Effort Saved**: 245 lines of code changes (from 300 → 55)
- **Risk Reduced**: Low-risk provider swap vs high-risk tool rewrites
- **Flexibility**: Easy to switch OAuth providers or support multiple

### Break-Even Analysis

```
Without Middleware:
  Phase 2 (JWT):   2 weeks (manual auth in tools)
  Phase 4 (OAuth): 6 weeks (rewrite everything)
  Total:           8 weeks

With Middleware:
  Phase 2 (JWT):   3 weeks (implement middleware + JWT provider)
  Phase 4 (OAuth): 1 week (swap to OAuth provider)
  Total:           4 weeks

Savings: 4 weeks (50% reduction in total effort)
```

---

## Migration Checklist: JWT → OAuth 2.1

### Prerequisites
- [ ] FastMCP middleware implemented (Phase 2)
- [ ] JWT authentication tested and verified
- [ ] OAuth provider selected (Google/Azure/Okta)
- [ ] OAuth credentials obtained (client_id, client_secret)
- [ ] Redirect URIs configured in OAuth provider

### Week 1: OAuth Provider Setup
- [ ] Create `auth/oauth_provider.py` (50 lines)
- [ ] Configure OAuth endpoints
- [ ] Test token introspection
- [ ] Update environment variables

### Week 2: MCP Server Migration
- [ ] Update Tickets server (1 line change)
- [ ] Update Oxygen server (1 line change)
- [ ] Update FinOps server (1 line change)
- [ ] Test authenticated tools with OAuth tokens

### Week 3: Frontend Updates
- [ ] Implement OAuth login flow in Web UI
- [ ] Add OAuth callback handler
- [ ] Update CLI for OAuth (optional)
- [ ] Test complete flow

### Week 4: Testing & Documentation
- [ ] Test all OAuth flows
- [ ] Test token refresh
- [ ] Test revocation
- [ ] Update documentation
- [ ] Deploy to production

---

## Summary: Why FastMCP Middleware Matters for OAuth

### The Core Benefit

FastMCP middleware provides a **stable authentication interface** that doesn't change when you swap providers:

```python
# MCP servers see this interface (never changes):
mcp.add_middleware(
    AuthenticationMiddleware,
    backend=BearerAuthBackend(verifier=SOME_PROVIDER)
)

# Tools see this interface (never changes):
@mcp.tool()
def get_my_tickets():
    current_user = get_current_user()
    # ...

# Phase 2: SOME_PROVIDER = JWTTokenVerifier()
# Phase 4: SOME_PROVIDER = GoogleOAuthProvider()
# Phase 5: SOME_PROVIDER = MultiOAuthVerifier()  # Support multiple!
```

**Result**: MCP servers and tools are **decoupled** from authentication mechanism.

---

### Without Middleware (Current)

Authentication is **tightly coupled** to every tool:

```python
# Every tool has authentication hardcoded
@mcp.tool()
def get_my_tickets():
    # Phase 2: JWT validation
    payload = verify_jwt_token(bearer_token)

    # Phase 4: Must rewrite to OAuth validation
    payload = verify_oauth_token(bearer_token)  # ← Change in 8+ places!
```

**Result**: Authentication mechanism change = rewrite all tools.

---

## Conclusion: The Strategic Value

### Immediate Benefits (Phase 2)
- ✅ Removes 120 lines of boilerplate
- ✅ Centralizes authentication logic
- ✅ Production-ready security

### Future Benefits (Phase 4)
- ✅ OAuth migration in 1-2 weeks (vs 4-6 weeks)
- ✅ 82% reduction in code changes (55 vs 300 lines)
- ✅ Low-risk provider swap
- ✅ Easy to support multiple OAuth providers
- ✅ Easy to switch providers (Google → Azure)

### Strategic Benefits (Long-term)
- ✅ Enterprise SSO ready
- ✅ Standards-compliant (OAuth 2.1)
- ✅ Maintainable architecture
- ✅ Future-proof authentication

---

**Key Takeaway**: Implementing FastMCP middleware NOW is an **investment** that pays **massive dividends** when you implement OAuth 2.1. It's the difference between a 1-week provider swap and a 6-week rewrite.

---

**Document Version**: 1.0
**Last Updated**: 2025-12-24
**Recommended Action**: ✅ Implement FastMCP middleware in Phase 2
