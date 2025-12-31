q` # Environment Configuration Guide

This document explains how to configure Agentic Jarvis using environment variables.

## Quick Start

1. **Copy the template:**
   ```bash
   cp .env.template .env
   ```

2. **Get Google API Key:**
   - Visit: https://makersuite.google.com/app/apikey
   - Copy your API key

3. **Generate JWT Secret:**
   ```bash
   ./scripts/generate_jwt_secret.sh
   ```

4. **Update .env file:**
   ```bash
   # Edit .env and update:
   GOOGLE_API_KEY=your_actual_api_key
   JWT_SECRET_KEY=your_generated_secret
   ```

5. **Verify configuration:**
   ```bash
   source .venv/bin/activate
   python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('✓ Config loaded' if os.getenv('GOOGLE_API_KEY') else '✗ Missing API key')"
   ```

---

## Required Variables

### GOOGLE_API_KEY (Required)

**Description:** API key for Google's Gemini 2.5 Flash model
**Where to get:** https://makersuite.google.com/app/apikey
**Used by:** All agents for LLM calls
**Example:**
```bash
GOOGLE_API_KEY=AIzaSyABC123...XYZ789
```

### JWT_SECRET_KEY (Required for Phase 2)

**Description:** Secret key for signing JWT tokens
**How to generate:**
```bash
./scripts/generate_jwt_secret.sh
```
**Security:**
- NEVER use the default value in production
- Use different secrets for dev/staging/production
- Minimum 32 characters (256-bit security)
- Rotate periodically

**Example:**
```bash
JWT_SECRET_KEY=_RGYetPQ1NkjgDs9pMPs5Cnyu2VDer7SWao5bzjfRVk
```

---

## Service Ports

### Phase 1: Pure A2A Architecture

| Service | Port | Description |
|---------|------|-------------|
| TicketsAgent | 8080 | IT operations ticket management |
| FinOpsAgent | 8081 | Cloud cost analytics |
| OxygenAgent | 8082 | Learning & development platform |
| Registry Service | 8003 | Agent registry + session management |

### Phase 2: Authentication

| Service | Port | Description |
|---------|------|-------------|
| Auth Service | 9998 | JWT authentication service |
| Web UI | 9999 | Web interface (future) |

### Legacy (Deprecated)

| Service | Port | Description |
|---------|------|-------------|
| Tickets Toolbox | 5001 | Old toolbox server (replaced by 8080) |
| FinOps Toolbox | 5002 | Old toolbox server (replaced by 8081) |

---

## JWT Configuration

### JWT_ALGORITHM

**Description:** Algorithm for JWT signing
**Options:**
- `HS256` - Symmetric (Phase 2, current)
- `RS256` - Asymmetric (Phase 4, OAuth 2.0)

**Default:** `HS256`

### JWT_EXPIRATION_HOURS

**Description:** How long JWT tokens remain valid
**Default:** `24` (24 hours)
**Range:** 1-168 hours (1 hour to 7 days)
**Recommendation:**
- Development: 24 hours
- Production: 8-12 hours

**Example:**
```bash
JWT_EXPIRATION_HOURS=12  # Expires after 12 hours
```

### AUTH_SERVICE_URL

**Description:** URL of the authentication service
**Default:** `http://localhost:9998`
**Production:** Update to your deployed auth service URL

---

## Phase 3: Session & Memory (Future)

Uncomment these when implementing Phase 3:

```bash
# Session storage
SESSION_TYPE=memory              # Options: memory | database | redis
DATABASE_URL=sqlite:///./jarvis.db

# Vector DB for long-term memory
VECTOR_DB_TYPE=chromadb          # Options: chromadb | pinecone | weaviate
CHROMA_PERSIST_DIRECTORY=./data/chroma
```

---

## Phase 4: OAuth 2.0 (Future)

Uncomment these when implementing Phase 4:

```bash
# OAuth Provider
OAUTH_PROVIDER=google            # Options: google | azure | okta | auth0

# OAuth Credentials
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
OAUTH_REDIRECT_URI=http://localhost:9999/callback

# Azure AD specific
AZURE_TENANT_ID=your_tenant_id

# Okta specific
OKTA_DOMAIN=your-domain.okta.com
```

---

## Security Best Practices

### 1. Never Commit .env to Git

The `.env` file contains secrets and should NEVER be committed:

```bash
# Verify .env is in .gitignore
grep ".env" .gitignore
```

### 2. Use Different Secrets Per Environment

```bash
# Development
JWT_SECRET_KEY=dev_secret_...

# Staging
JWT_SECRET_KEY=staging_secret_...

# Production
JWT_SECRET_KEY=prod_secret_...
```

### 3. Rotate Secrets Regularly

```bash
# Generate new secret
./scripts/generate_jwt_secret.sh

# Update .env with new secret
# Invalidates all existing tokens
```

### 4. Secure File Permissions

```bash
# Lock down .env file
chmod 600 .env

# Verify permissions
ls -la .env
# Should show: -rw-------
```

---

## Troubleshooting

### Error: "GOOGLE_API_KEY environment variable not set"

**Solution:**
```bash
# Check if .env exists
ls -la .env

# Verify API key is set
source .venv/bin/activate
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('GOOGLE_API_KEY'))"
```

### Error: "Invalid or expired JWT token"

**Possible causes:**
1. JWT_SECRET_KEY changed (invalidates existing tokens)
2. Token expired (> JWT_EXPIRATION_HOURS)
3. JWT_ALGORITHM mismatch

**Solution:**
```bash
# Login again to get new token
python jarvis_agent/main_with_registry.py
```

### Port Already in Use

**Solution:**
```bash
# Find process using port
lsof -i :8080

# Kill process
lsof -ti:8080 | xargs kill -9

# Or change port in .env
TICKETS_AGENT_PORT=8090
```

---

## Verification Checklist

Before running Jarvis, verify your configuration:

- [ ] `.env` file exists
- [ ] `GOOGLE_API_KEY` is set (not the template value)
- [ ] `JWT_SECRET_KEY` is secure (not the template value)
- [ ] All service ports are available
- [ ] `.env` file has correct permissions (600)
- [ ] `.env` is in `.gitignore`

**Quick verification:**
```bash
./scripts/check_services.sh
```

---

## References

- **Phase 2 Plan:** [PHASE_2_PURE_A2A_PLAN.md](./PHASE_2_PURE_A2A_PLAN.md)
- **Token Propagation:** [TOKEN_PROPAGATION_GUIDE.md](./TOKEN_PROPAGATION_GUIDE.md)
- **Generate JWT Secret:** `./scripts/generate_jwt_secret.sh`
- **Check Services:** `./scripts/check_services.sh`
- **Start Services:** `./scripts/start_all_agents.sh`

---

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your `.env` matches `.env.template` structure
3. Check service logs in `logs/` directory
4. Review [PHASE_2_PURE_A2A_PLAN.md](./PHASE_2_PURE_A2A_PLAN.md)
