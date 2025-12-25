# FastMCP Remote OAuth & OAuth Proxy - Complete Analysis

**Date**: 2025-12-25
**Status**: 📘 **ARCHITECTURE GUIDANCE**
**Context**: Analysis of FastMCP's two OAuth integration patterns

---

## Executive Summary

Your existing authentication documents focused on **middleware-based authentication** (JWT validation in MCP servers). This document covers FastMCP's **OAuth client integration** patterns - how MCP clients authenticate users and obtain tokens.

**Key Discovery**: FastMCP provides TWO distinct OAuth patterns based on whether your identity provider supports **Dynamic Client Registration (DCR)**:

| Feature | Remote OAuth | OAuth Proxy |
|---------|--------------|-------------|
| **For Providers** | WITH DCR support | WITHOUT DCR support |
| **Examples** | Descope, WorkOS AuthKit, Scalekit | Google, GitHub, Azure AD, AWS |
| **Client Registration** | Automatic (DCR) | Manual (pre-registered) |
| **Your MCP Server Role** | Resource server (validates tokens) | Proxy (translates DCR to fixed creds) |
| **Implementation Complexity** | Low (just validate) | Medium (proxy layer) |
| **Use in Jarvis** | Phase 4+ (enterprise SSO) | Phase 2-3 (dev/testing with Google) |

---

## Part 1: Remote OAuth (RemoteAuthProvider)

### What Is Remote OAuth?

**Remote OAuth** delegates authentication entirely to an external identity provider that supports **Dynamic Client Registration (DCR)**. Your MCP server becomes a **protected resource server** - it only validates tokens and enforces permissions.

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                MCP Client (Web UI / CLI)                     │
│  1. Discovers auth endpoints via /.well-known/             │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼ DCR: Auto-registers client
┌─────────────────────────────────────────────────────────────┐
│       Identity Provider (Descope/WorkOS/Scalekit)           │
│  2. Issues client_id + client_secret automatically          │
│  3. User authenticates (SSO, MFA, etc.)                     │
│  4. Issues access_token (JWT)                               │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼ Authorization: Bearer <jwt>
┌─────────────────────────────────────────────────────────────┐
│              MCP Server (Tickets/Oxygen/FinOps)             │
│                                                              │
│  RemoteAuthProvider:                                         │
│  5. Validates JWT signature (JWKS)                          │
│  6. Validates issuer, audience, expiration                  │
│  7. Extracts user claims (username, roles)                  │
│  8. Executes tool with user context                         │
└─────────────────────────────────────────────────────────────┘
```

**Key Benefit**: MCP clients don't need pre-registered credentials. They automatically register themselves with the identity provider.

---

### When to Use Remote OAuth

✅ **Use Remote OAuth When**:
- Identity provider supports DCR (check `.well-known/openid-configuration` for `registration_endpoint`)
- Enterprise SSO required (WorkOS AuthKit, Scalekit, Descope)
- Zero-configuration client onboarding needed
- Multiple MCP clients need independent credentials
- Regulatory compliance requires centralized identity management

❌ **Don't Use Remote OAuth When**:
- Provider doesn't support DCR (Google, GitHub, Azure AD standard)
- Simple JWT validation is sufficient (current Jarvis Phase 2)
- Custom auth server with manual client registration

---

### Implementation Pattern

#### Step 1: Configure RemoteAuthProvider

**File**: `auth/remote_oauth_provider.py` (NEW)

```python
"""
Remote OAuth Provider for FastMCP
Uses external identity provider with Dynamic Client Registration (DCR).
"""

from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from pydantic import AnyHttpUrl
import os


def create_workos_auth_provider() -> RemoteAuthProvider:
    """
    Create RemoteAuthProvider for WorkOS AuthKit.

    WorkOS AuthKit supports DCR and provides:
    - Automatic client registration
    - Enterprise SSO (Google Workspace, Azure AD, Okta)
    - Multi-factor authentication
    - Session management
    """

    # JWT verifier validates tokens issued by WorkOS
    token_verifier = JWTVerifier(
        jwks_uri="https://api.workos.com/.well-known/jwks.json",
        issuer="https://api.workos.com",
        audience="mcp-production-api"  # Your MCP server identifier
    )

    # RemoteAuthProvider exposes /.well-known/oauth-protected-resource
    auth = RemoteAuthProvider(
        token_verifier=token_verifier,
        authorization_servers=[
            AnyHttpUrl("https://api.workos.com")
        ],
        base_url=os.getenv("MCP_SERVER_BASE_URL", "https://api.yourcompany.com")
    )

    return auth


def create_descope_auth_provider() -> RemoteAuthProvider:
    """
    Create RemoteAuthProvider for Descope.

    Descope provides:
    - Dynamic Client Registration
    - Passwordless authentication
    - Social login (Google, GitHub, etc.)
    - RBAC and permissions
    """

    project_id = os.getenv("DESCOPE_PROJECT_ID")

    token_verifier = JWTVerifier(
        jwks_uri=f"https://api.descope.com/{project_id}/.well-known/jwks.json",
        issuer=f"https://api.descope.com/{project_id}",
        audience=f"mcp-{project_id}"
    )

    auth = RemoteAuthProvider(
        token_verifier=token_verifier,
        authorization_servers=[
            AnyHttpUrl(f"https://api.descope.com/{project_id}")
        ],
        base_url=os.getenv("MCP_SERVER_BASE_URL")
    )

    return auth
```

---

#### Step 2: Update MCP Server

**File**: `tickets_mcp_server/server.py`

```python
from fastmcp import FastMCP
from auth.remote_oauth_provider import create_workos_auth_provider

# Create MCP server with Remote OAuth
mcp = FastMCP(
    name="Tickets Server",
    auth=create_workos_auth_provider()  # ← Remote OAuth provider
)

# Tools remain unchanged - auth handled by provider
@mcp.tool()
def get_my_tickets() -> List[Dict]:
    """Get tickets for authenticated user."""
    # Access user from auth context
    from fastmcp.server.dependencies import get_http_request
    request = get_http_request()
    current_user = request.user.identity["username"]

    return [t for t in TICKETS_DB if t['user'] == current_user]
```

---

#### Step 3: Client Discovery Flow

**MCP Client Discovers Auth Endpoints**:

```bash
# Client fetches /.well-known/oauth-protected-resource
curl http://localhost:5011/.well-known/oauth-protected-resource

# Response:
{
  "resource": "http://localhost:5011",
  "authorization_servers": ["https://api.workos.com"]
}
```

**Client Registers with Authorization Server** (automatic):

```bash
# Client uses DCR to auto-register
POST https://api.workos.com/oauth/register
{
  "client_name": "Jarvis Web UI",
  "redirect_uris": ["http://localhost:9999/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "token_endpoint_auth_method": "client_secret_post"
}

# Response:
{
  "client_id": "auto_generated_client_id",
  "client_secret": "auto_generated_secret"
}
```

**Client Initiates OAuth Flow** (standard OAuth 2.1 + PKCE):

```bash
# User redirected to WorkOS login
https://api.workos.com/oauth/authorize?
  client_id=auto_generated_client_id&
  redirect_uri=http://localhost:9999/callback&
  response_type=code&
  scope=openid email profile&
  code_challenge=<pkce_challenge>
```

---

### Security Considerations

#### 1. Token Validation Performance

**Problem**: JWKS fetching adds latency to every request

**Solution**: Implement caching with rotation handling

```python
from fastmcp.server.auth.providers.jwt import JWTVerifier
from cachetools import TTLCache
import asyncio

class CachedJWTVerifier(JWTVerifier):
    """JWT verifier with JWKS caching."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache JWKS for 1 hour (keys rotate infrequently)
        self._jwks_cache = TTLCache(maxsize=1, ttl=3600)
        self._cache_lock = asyncio.Lock()

    async def get_jwks(self) -> dict:
        """Fetch JWKS with caching."""
        async with self._cache_lock:
            if "jwks" not in self._jwks_cache:
                self._jwks_cache["jwks"] = await super().get_jwks()
            return self._jwks_cache["jwks"]
```

---

#### 2. Audience Validation

**Problem**: Token from one MCP server used on another

**Solution**: Strict audience validation

```python
token_verifier = JWTVerifier(
    jwks_uri="https://api.workos.com/.well-known/jwks.json",
    issuer="https://api.workos.com",
    audience="tickets-server"  # ← Unique per server!
)

# Oxygen server uses different audience
oxygen_verifier = JWTVerifier(
    jwks_uri="https://api.workos.com/.well-known/jwks.json",
    issuer="https://api.workos.com",
    audience="oxygen-server"  # ← Different audience
)
```

**Best Practice**: Use server-specific audiences to prevent token reuse.

---

#### 3. Scope Management

**Problem**: User has access to features they shouldn't

**Solution**: Map token scopes to permissions

```python
@mcp.tool()
def delete_ticket(ticket_id: int) -> Dict:
    """Delete ticket (admin only)."""
    from fastmcp.server.dependencies import get_http_request
    request = get_http_request()

    # Check scopes from token
    user_scopes = request.user.identity.get("scopes", [])

    if "admin" not in user_scopes:
        return {
            "error": "Access denied",
            "message": "Admin scope required"
        }

    # Delete logic...
```

---

## Part 2: OAuth Proxy (OAuthProxy)

### What Is OAuth Proxy?

**OAuth Proxy** is a **translation layer** that makes traditional OAuth providers (Google, GitHub, Azure) work with MCP's DCR-based authentication flow. It "fakes" DCR support by returning your pre-registered credentials.

**The Problem**: MCP clients expect DCR (auto-registration), but most OAuth providers require manual app registration (fixed client_id/client_secret).

**The Solution**: OAuth Proxy presents a DCR interface to clients while using your fixed credentials with the upstream provider.

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                MCP Client (Web UI / CLI)                     │
│  1. Attempts DCR registration                                │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼ POST /oauth/register (DCR request)
┌─────────────────────────────────────────────────────────────┐
│              OAuth Proxy (FastMCP)                           │
│  2. Returns pre-registered credentials (fakes DCR)          │
│     client_id: "your_google_client_id"                      │
│     client_secret: "your_google_client_secret"              │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼ OAuth flow with fixed credentials
┌─────────────────────────────────────────────────────────────┐
│       Upstream Provider (Google/GitHub/Azure)               │
│  3. User authenticates                                       │
│  4. Issues access_token + refresh_token                     │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼ Returns tokens to proxy
┌─────────────────────────────────────────────────────────────┐
│              OAuth Proxy (FastMCP)                           │
│  5. Encrypts upstream tokens (Fernet encryption)            │
│  6. Issues own JWT to client (HS256)                        │
│  7. Stores encrypted upstream tokens in JWT claims          │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼ Authorization: Bearer <fastmcp_jwt>
┌─────────────────────────────────────────────────────────────┐
│              MCP Server (Tickets/Oxygen/FinOps)             │
│  8. Validates FastMCP JWT                                    │
│  9. Decrypts upstream token if needed                       │
│  10. Executes tool with user context                        │
└─────────────────────────────────────────────────────────────┘
```

**Key Innovation**: Two-layer security with two separate PKCE flows (client ↔ proxy, proxy ↔ provider).

---

### When to Use OAuth Proxy

✅ **Use OAuth Proxy When**:
- Provider doesn't support DCR (Google, GitHub, Azure AD, AWS Cognito, Discord, Facebook)
- You already have OAuth app registered with provider
- Development/testing with real OAuth providers
- Need MCP-compatible interface for traditional OAuth

❌ **Don't Use OAuth Proxy When**:
- Provider supports DCR (use Remote OAuth instead)
- Simple JWT validation is sufficient (use middleware)
- Custom auth server (build DCR support directly)

---

### Implementation Pattern

#### Step 1: Register OAuth App with Provider

**Example: Google OAuth**

1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:9998/oauth/callback`
   - Note down `client_id` and `client_secret`

**Example: GitHub OAuth**

1. Go to https://github.com/settings/developers
2. Register new OAuth App:
   - Authorization callback URL: `http://localhost:9998/oauth/callback`
   - Note down `client_id` and `client_secret`

---

#### Step 2: Configure OAuth Proxy

**File**: `auth/oauth_proxy_server.py` (NEW)

```python
"""
OAuth Proxy Server for Traditional OAuth Providers
Bridges providers without DCR to MCP's DCR-based flow.
"""

from fastmcp.server.auth.proxy import OAuthProxy, OIDCProxy
import os


def create_google_oauth_proxy() -> OIDCProxy:
    """
    Create OAuth Proxy for Google.

    Uses OIDC Proxy variant for automatic endpoint discovery.
    Google supports OIDC discovery but NOT Dynamic Client Registration.
    """

    proxy = OIDCProxy(
        # Your pre-registered Google OAuth app
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),

        # OIDC discovery URL (auto-discovers endpoints)
        discovery_url="https://accounts.google.com/.well-known/openid-configuration",

        # OAuth Proxy server configuration
        proxy_base_url="http://localhost:9998",  # Your proxy server
        redirect_uri="http://localhost:9998/oauth/callback",

        # JWT signing (for tokens issued by proxy)
        jwt_secret=os.getenv("JWT_SECRET_KEY"),
        jwt_algorithm="HS256",
        jwt_expiration=3600,  # 1 hour

        # Scopes to request from Google
        scopes=["openid", "email", "profile"]
    )

    return proxy


def create_github_oauth_proxy() -> OAuthProxy:
    """
    Create OAuth Proxy for GitHub.

    Uses standard OAuthProxy (GitHub doesn't support OIDC discovery).
    """

    proxy = OAuthProxy(
        # Your pre-registered GitHub OAuth app
        client_id=os.getenv("GITHUB_CLIENT_ID"),
        client_secret=os.getenv("GITHUB_CLIENT_SECRET"),

        # Manually specify endpoints (GitHub doesn't have discovery)
        authorization_endpoint="https://github.com/login/oauth/authorize",
        token_endpoint="https://github.com/login/oauth/access_token",
        userinfo_endpoint="https://api.github.com/user",

        # OAuth Proxy server configuration
        proxy_base_url="http://localhost:9998",
        redirect_uri="http://localhost:9998/oauth/callback",

        # JWT signing
        jwt_secret=os.getenv("JWT_SECRET_KEY"),
        jwt_algorithm="HS256",
        jwt_expiration=3600,

        # Scopes
        scopes=["read:user", "user:email"]
    )

    return proxy


def create_azure_oauth_proxy() -> OIDCProxy:
    """
    Create OAuth Proxy for Azure AD.

    Uses OIDC discovery for Azure AD.
    """

    tenant_id = os.getenv("AZURE_TENANT_ID")

    proxy = OIDCProxy(
        client_id=os.getenv("AZURE_CLIENT_ID"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET"),
        discovery_url=f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration",
        proxy_base_url="http://localhost:9998",
        redirect_uri="http://localhost:9998/oauth/callback",
        jwt_secret=os.getenv("JWT_SECRET_KEY"),
        jwt_algorithm="HS256",
        jwt_expiration=3600,
        scopes=["openid", "email", "profile"]
    )

    return proxy
```

---

#### Step 3: Run OAuth Proxy Server

**File**: `auth/proxy_app.py` (NEW)

```python
"""
OAuth Proxy Application
Runs as standalone service on port 9998.
"""

from fastapi import FastAPI
from fastmcp.server.auth.proxy import mount_oauth_proxy_routes
from auth.oauth_proxy_server import create_google_oauth_proxy
import uvicorn

# Create FastAPI app
app = FastAPI(title="OAuth Proxy Server")

# Mount OAuth proxy routes
oauth_proxy = create_google_oauth_proxy()
mount_oauth_proxy_routes(
    app=app,
    proxy=oauth_proxy,
    prefix="/oauth"  # Routes: /oauth/authorize, /oauth/token, /oauth/callback
)

# Health check
@app.get("/health")
def health():
    return {"status": "healthy", "service": "oauth-proxy"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9998,
        log_level="info"
    )
```

**Start OAuth Proxy Server**:

```bash
# Terminal 1: Start OAuth Proxy
python auth/proxy_app.py

# Output:
# INFO:     Uvicorn running on http://0.0.0.0:9998
# INFO:     OAuth Proxy routes mounted at /oauth
```

---

#### Step 4: Update MCP Servers to Validate Proxy JWTs

**File**: `tickets_mcp_server/server.py`

```python
"""
MCP Server validates JWTs issued by OAuth Proxy.
"""

from fastmcp import FastMCP
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from pydantic import AnyHttpUrl
import os

# JWT verifier for tokens issued by OAuth Proxy
token_verifier = JWTVerifier(
    # OAuth Proxy uses symmetric signing (HS256)
    # So we validate with the same secret
    secret=os.getenv("JWT_SECRET_KEY"),
    algorithm="HS256",

    # Issuer is the OAuth Proxy
    issuer="http://localhost:9998",

    # Audience is this MCP server
    audience="tickets-server"
)

# RemoteAuthProvider points to OAuth Proxy
auth = RemoteAuthProvider(
    token_verifier=token_verifier,
    authorization_servers=[
        AnyHttpUrl("http://localhost:9998")  # OAuth Proxy
    ],
    base_url="http://localhost:5011"
)

mcp = FastMCP(name="Tickets Server", auth=auth)

# Tools remain unchanged
@mcp.tool()
def get_my_tickets() -> List[Dict]:
    """Get tickets for authenticated user."""
    from fastmcp.server.dependencies import get_http_request
    request = get_http_request()
    current_user = request.user.identity["email"]  # Google email

    return [t for t in TICKETS_DB if t['user'] == current_user]
```

---

### OAuth Proxy Token Factory Pattern

**Why Two Tokens?**

The OAuth Proxy issues **its own JWT** instead of forwarding the upstream token. This solves several problems:

#### Problem 1: Token Audience Boundaries

**Without Proxy JWT**:
```
Google token (audience: "your_google_client_id")
  ↓
Used directly on MCP server
  ❌ MCP server audience should be "tickets-server", not Google client_id
```

**With Proxy JWT**:
```
Google token (audience: "your_google_client_id")
  ↓ OAuth Proxy encrypts and stores in JWT claim
FastMCP JWT (audience: "tickets-server", claim: encrypted_upstream_token)
  ✅ Proper audience boundaries maintained
```

---

#### Problem 2: Upstream Token Security

**Token Structure**:

```python
# FastMCP JWT issued by proxy
{
  "iss": "http://localhost:9998",  # OAuth Proxy
  "aud": "tickets-server",          # MCP server
  "sub": "user@example.com",        # User identity
  "exp": 1735132800,                # 1 hour from now

  # Encrypted upstream token (Fernet encryption: AES-128-CBC + HMAC-SHA256)
  "upstream_token": "gAAAAABl...encrypted_google_token...",

  # User claims from Google
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://..."
}
```

**Decrypting Upstream Token** (when needed):

```python
from fastmcp.server.auth.proxy import decrypt_upstream_token

@mcp.tool()
def fetch_user_calendar() -> List[Dict]:
    """Fetch user's Google Calendar events."""
    from fastmcp.server.dependencies import get_http_request
    import httpx

    request = get_http_request()

    # Decrypt upstream Google token
    google_token = decrypt_upstream_token(
        encrypted_token=request.user.identity["upstream_token"],
        secret=os.getenv("JWT_SECRET_KEY")
    )

    # Use Google token to call Google Calendar API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={"Authorization": f"Bearer {google_token}"}
        )

    return response.json()
```

---

### OIDC Proxy vs Standard OAuth Proxy

FastMCP provides two proxy variants:

#### OIDCProxy (Recommended for OIDC Providers)

**For**: Google, Azure AD, Auth0, Okta, Keycloak

**Benefits**:
- ✅ Auto-discovers endpoints from `.well-known/openid-configuration`
- ✅ Less configuration required
- ✅ Automatic JWKS endpoint detection
- ✅ Standard claims mapping

**Example**:
```python
proxy = OIDCProxy(
    client_id="...",
    client_secret="...",
    discovery_url="https://accounts.google.com/.well-known/openid-configuration",  # ← Discovers all endpoints
    proxy_base_url="http://localhost:9998",
    redirect_uri="http://localhost:9998/oauth/callback",
    jwt_secret=os.getenv("JWT_SECRET_KEY"),
    scopes=["openid", "email", "profile"]
)
```

---

#### OAuthProxy (For Non-OIDC Providers)

**For**: GitHub, Discord, Slack, Spotify, Twitch

**Requires**: Manual endpoint configuration

**Example**:
```python
proxy = OAuthProxy(
    client_id="...",
    client_secret="...",
    authorization_endpoint="https://github.com/login/oauth/authorize",  # ← Manual
    token_endpoint="https://github.com/login/oauth/access_token",      # ← Manual
    userinfo_endpoint="https://api.github.com/user",                    # ← Manual
    proxy_base_url="http://localhost:9998",
    redirect_uri="http://localhost:9998/oauth/callback",
    jwt_secret=os.getenv("JWT_SECRET_KEY"),
    scopes=["read:user", "user:email"]
)
```

---

## Part 3: Comparison Matrix

### Remote OAuth vs OAuth Proxy vs Middleware (Your Current Approach)

| Feature | Remote OAuth | OAuth Proxy | Middleware (Current) |
|---------|--------------|-------------|----------------------|
| **Purpose** | OAuth client integration | OAuth client integration | Token validation only |
| **Provider Type** | DCR-capable | Non-DCR | Any (you handle auth) |
| **Examples** | WorkOS, Descope, Scalekit | Google, GitHub, Azure | Custom JWT auth |
| **Client Registration** | Automatic (DCR) | Faked (returns fixed creds) | N/A (manual) |
| **MCP Server Role** | Resource server | Token factory | Resource server |
| **Token Issued By** | Identity provider | OAuth Proxy (FastMCP JWT) | Your auth server |
| **Implementation** | RemoteAuthProvider | OAuthProxy + routes | AuthenticationMiddleware |
| **Complexity** | Low | Medium | Low |
| **Use in Jarvis Phase 2** | ❌ No (no DCR provider) | ⚠️ Optional (testing) | ✅ Yes (current plan) |
| **Use in Jarvis Phase 4** | ✅ Yes (enterprise SSO) | ⚠️ If non-DCR provider | ⚠️ Deprecated |

---

### When to Use Each Pattern

```
┌─────────────────────────────────────────────────────────────┐
│              Decision Tree: Which Pattern?                   │
└─────────────────────────────────────────────────────────────┘

Do you need OAuth integration with external providers?
  │
  ├─ NO → Use Middleware (your current approach)
  │        - Custom JWT auth server (Phase 2)
  │        - Simple token validation
  │        - Full control over auth flow
  │
  └─ YES → Do you have a DCR-capable provider?
           │
           ├─ YES → Use Remote OAuth
           │         - WorkOS AuthKit
           │         - Descope
           │         - Scalekit
           │         - Enterprise-grade SSO
           │
           └─ NO → Use OAuth Proxy
                    - Google
                    - GitHub
                    - Azure AD (standard)
                    - AWS Cognito
                    - Development/testing
```

---

## Part 4: Application to Agentic Jarvis

### Current Architecture (Phase 2) - Middleware Pattern ✅

**What You Have**:
```
Custom Auth Server (Port 9998)
  ↓ Issues JWT
ADK App stores token → session.state["bearer_token"]
  ↓ header_provider adds Authorization header
MCP Servers (5011, 5012, 8012)
  ↓ AuthenticationMiddleware validates JWT
Tools access authenticated user
```

**Status**: ✅ **CORRECT** - This is the right pattern for Phase 2!

**Why**: You control the entire auth flow with custom JWT authentication. No external OAuth providers needed yet.

---

### Future Enhancement (Phase 3) - OAuth Proxy for Testing ⚠️

**Use Case**: Test OAuth integration during development

**Example**: Allow developers to login with Google

**Implementation**:

```python
# auth/proxy_app.py - OAuth Proxy for development
from fastmcp.server.auth.proxy import OIDCProxy

google_proxy = OIDCProxy(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    discovery_url="https://accounts.google.com/.well-known/openid-configuration",
    proxy_base_url="http://localhost:9998",
    redirect_uri="http://localhost:9998/oauth/callback",
    jwt_secret=os.getenv("JWT_SECRET_KEY"),
    scopes=["openid", "email", "profile"]
)

# Run on port 9998 (replaces custom auth server)
```

**MCP Servers Update**:
```python
# tickets_mcp_server/server.py
# Change JWT verifier to validate OAuth Proxy JWTs
token_verifier = JWTVerifier(
    secret=os.getenv("JWT_SECRET_KEY"),  # ← Shared with proxy
    algorithm="HS256",
    issuer="http://localhost:9998",      # ← OAuth Proxy
    audience="tickets-server"
)
```

**Benefits**:
- ✅ Test real OAuth flow
- ✅ No manual user/password management
- ✅ Simulates production OAuth

**Drawbacks**:
- ⚠️ Still requires manual Google OAuth app registration
- ⚠️ Not enterprise-grade (single client_id shared by all users)

---

### Production Deployment (Phase 4) - Remote OAuth 🚀

**Use Case**: Enterprise SSO with WorkOS AuthKit

**Why WorkOS**:
- ✅ Supports Dynamic Client Registration (DCR)
- ✅ Enterprise connectors (Google Workspace, Azure AD, Okta)
- ✅ Automatic client registration for MCP clients
- ✅ Production-ready security

**Architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│               Web UI / CLI (MCP Client)                      │
│  Discovers: /.well-known/oauth-protected-resource          │
│  Registers: Auto via DCR with WorkOS                        │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│               WorkOS AuthKit                                 │
│  - Enterprise SSO (Google Workspace, Azure AD)              │
│  - Multi-factor authentication                              │
│  - User directory sync                                       │
│  - Issues JWT tokens                                         │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼ Authorization: Bearer <workos_jwt>
┌─────────────────────────────────────────────────────────────┐
│        MCP Servers (Tickets, Oxygen, FinOps)                │
│                                                              │
│  RemoteAuthProvider:                                         │
│  - Validates WorkOS JWT (JWKS)                              │
│  - Extracts enterprise user claims                          │
│  - Enforces RBAC via scopes                                 │
└─────────────────────────────────────────────────────────────┘
```

**Implementation**:

```python
# auth/remote_oauth_provider.py
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier

def create_workos_auth() -> RemoteAuthProvider:
    token_verifier = JWTVerifier(
        jwks_uri="https://api.workos.com/.well-known/jwks.json",
        issuer="https://api.workos.com",
        audience="jarvis-production"
    )

    return RemoteAuthProvider(
        token_verifier=token_verifier,
        authorization_servers=["https://api.workos.com"],
        base_url="https://jarvis.yourcompany.com"
    )


# tickets_mcp_server/server.py
from fastmcp import FastMCP
from auth.remote_oauth_provider import create_workos_auth

mcp = FastMCP(
    name="Tickets Server",
    auth=create_workos_auth()  # ← One line change from Phase 2!
)

# Tools: NO CHANGES NEEDED ✅
```

**Migration Effort**: Minimal (if you use middleware pattern now)

---

## Part 5: Implementation Recommendations

### Phase 2 (Current): Stick with Middleware ✅

**Recommendation**: Continue with your current `AuthenticationMiddleware` approach

**Why**:
- ✅ You already implemented it
- ✅ Full control over auth logic
- ✅ No external dependencies
- ✅ Perfect for MVP/Phase 2

**No Changes Needed**: Your current architecture is correct.

---

### Phase 3 (Optional): Add OAuth Proxy for Testing

**Recommendation**: Add OAuth Proxy as development tool (optional)

**Use Case**:
- Developers can login with Google instead of managing local accounts
- Test OAuth flow before enterprise SSO

**Effort**: 2-3 days
- Create OAuth Proxy server
- Register Google OAuth app
- Update MCP servers to validate proxy JWTs
- Update Web UI login flow

**Value**: Medium (nice-to-have, not critical)

---

### Phase 4 (Enterprise): Migrate to Remote OAuth

**Recommendation**: Use Remote OAuth with WorkOS AuthKit or Descope

**Prerequisites**:
- ✅ Phase 2 middleware implemented (you have this)
- ✅ Production deployment ready
- ✅ Enterprise SSO requirements confirmed

**Migration Path**:
1. Sign up for WorkOS AuthKit (https://workos.com)
2. Create `auth/remote_oauth_provider.py` (50 lines)
3. Update MCP servers to use `RemoteAuthProvider` (1 line change per server)
4. Update Web UI to support DCR flow
5. Test enterprise SSO connectors (Google Workspace, Azure AD)

**Effort**: 1-2 weeks

**Value**: High (enterprise requirement)

---

## Part 6: Security Best Practices

### For All Patterns

#### 1. Token Storage

**Client Side** (Web UI):
```javascript
// ❌ NEVER store in localStorage (XSS vulnerable)
localStorage.setItem('token', token);

// ✅ Use httpOnly cookies
document.cookie = `token=${token}; HttpOnly; Secure; SameSite=Strict`;

// ✅ Or use secure session storage with encryption
sessionStorage.setItem('token', encryptToken(token));
```

---

#### 2. Token Transmission

**HTTP Only**:
```python
# ❌ NEVER send tokens in query params
https://api.com/tickets?token=eyJhbGc...

# ✅ ALWAYS use Authorization header
headers = {"Authorization": f"Bearer {token}"}
```

---

#### 3. Token Rotation

**Refresh Token Pattern**:
```python
# OAuth Proxy automatically handles refresh tokens
@app.get("/refresh")
async def refresh_token(current_token: str):
    # Decrypt upstream refresh token from FastMCP JWT
    upstream_refresh_token = decrypt_upstream_token(
        current_token,
        secret=JWT_SECRET_KEY
    )

    # Exchange with upstream provider
    new_tokens = await exchange_refresh_token(upstream_refresh_token)

    # Issue new FastMCP JWT
    return issue_fastmcp_jwt(new_tokens)
```

---

#### 4. Scope Validation

**Enforce Least Privilege**:
```python
@mcp.tool()
def delete_all_tickets() -> Dict:
    """Delete all tickets (super admin only)."""
    from fastmcp.server.dependencies import get_http_request
    request = get_http_request()

    required_scopes = ["admin", "tickets:delete:all"]
    user_scopes = request.user.identity.get("scopes", [])

    if not all(scope in user_scopes for scope in required_scopes):
        raise PermissionError("Insufficient scopes")

    # Delete logic...
```

---

## Summary

### Key Takeaways

1. **Remote OAuth** (RemoteAuthProvider):
   - For DCR-capable providers (WorkOS, Descope, Scalekit)
   - Your server just validates tokens
   - Enterprise-grade SSO
   - Use in Phase 4

2. **OAuth Proxy** (OAuthProxy/OIDCProxy):
   - For traditional OAuth providers (Google, GitHub, Azure)
   - Bridges non-DCR providers to MCP's DCR flow
   - Optional for Phase 3 testing
   - Issues own JWTs with encrypted upstream tokens

3. **Middleware Pattern** (Your Current Approach):
   - Custom JWT authentication
   - Full control over auth flow
   - Perfect for Phase 2 MVP
   - ✅ Continue using this now

### Your Action Plan

**Phase 2 (Now)**:
- ✅ Continue with `AuthenticationMiddleware` + JWT
- ✅ Complete migration per `FASTMCP_AUTH_IMPLEMENTATION_GUIDE.md`
- ⏭️ Skip Remote OAuth and OAuth Proxy for now

**Phase 3 (Optional)**:
- ⚠️ Consider OAuth Proxy for development convenience
- ⚠️ Only if team wants Google login for testing

**Phase 4 (Production)**:
- 🚀 Migrate to Remote OAuth with WorkOS AuthKit
- 🚀 Minimal changes due to middleware architecture
- 🚀 Enterprise SSO ready

### Document References

Your existing docs remain valid:
- ✅ `FASTMCP_AUTH_CRITICAL_ANALYSIS.md` - Middleware migration (still correct)
- ✅ `FASTMCP_AUTH_IMPLEMENTATION_GUIDE.md` - Step-by-step middleware setup (still correct)
- ✅ `OAUTH_MIGRATION_PATH.md` - Future OAuth migration (enhanced by this doc)

This document **extends** your authentication strategy with OAuth client integration patterns.

---

**Sources:**
- [FastMCP Remote OAuth Documentation](https://gofastmcp.com/servers/auth/remote-oauth)
- [FastMCP OAuth Proxy Documentation](https://gofastmcp.com/servers/auth/oauth-proxy)
- [Why MCP Bet on Dynamic Client Registration (FastMCP Blog)](https://fastmcp.cloud/blog/why-mcp-bet-on-dynamic-client-registration)
- [Building Secure MCP Servers in 2025: OAuth Authentication](https://martinschroder.substack.com/p/building-secure-mcp-severs-in-2025)
- [Securing FastMCP with Scalekit: Remote OAuth Done Right](https://www.scalekit.com/blog/securing-fastmcp-with-scalekit)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-25
**Status**: 📘 Architecture Guidance - Remote OAuth & OAuth Proxy Analysis
