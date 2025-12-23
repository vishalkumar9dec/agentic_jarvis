# Environment Configuration Guide

## Overview

Agentic Jarvis uses environment variables for configuration. This guide explains all available variables and their usage across different phases.

## Quick Start

1. Copy the template file:
```bash
cp .env.template .env
```

2. Edit `.env` and set your values:
```bash
# Minimum required
GOOGLE_API_KEY=your_actual_api_key_here
JWT_SECRET_KEY=your_secret_key_here
```

3. Load environment variables:
```bash
# Automatically loaded by Python scripts using dotenv
python main.py
```

## Environment Variables Reference

### Core Configuration

#### `GOOGLE_API_KEY` (Required)
- **Description:** Google Gemini API key for LLM access
- **Where to get:** https://makersuite.google.com/app/apikey
- **Example:** `GOOGLE_API_KEY=AIzaSyD...`
- **Used by:** All agents (root orchestrator, sub-agents)

### Service Ports

#### `TICKETS_SERVER_PORT`
- **Description:** Port for Tickets Toolbox Server
- **Default:** `5001`
- **Example:** `TICKETS_SERVER_PORT=5001`
- **Used by:** `toolbox_servers/tickets_server/server.py`

#### `FINOPS_SERVER_PORT`
- **Description:** Port for FinOps Toolbox Server
- **Default:** `5002`
- **Example:** `FINOPS_SERVER_PORT=5002`
- **Used by:** `toolbox_servers/finops_server/server.py`

#### `OXYGEN_AGENT_PORT`
- **Description:** Port for Oxygen A2A Agent
- **Default:** `8002`
- **Example:** `OXYGEN_AGENT_PORT=8002`
- **Used by:** `remote_agent/oxygen_agent/agent.py`

#### `AUTH_SERVICE_PORT`
- **Description:** Port for Authentication Service (Phase 2)
- **Default:** `9998`
- **Example:** `AUTH_SERVICE_PORT=9998`
- **Used by:** `auth/auth_server.py`

#### `WEB_UI_PORT`
- **Description:** Port for Web UI Server
- **Default:** `9999`
- **Example:** `WEB_UI_PORT=9999`
- **Used by:** `web_ui/server.py`

### Phase 2: JWT Authentication

#### `JWT_SECRET_KEY` (Required for Phase 2)
- **Description:** Secret key for signing JWT tokens
- **Security:** **CRITICAL** - Must be changed in production
- **Default:** `jarvis-secret-key-change-in-production-2025`
- **Generate:** `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- **Example:** `JWT_SECRET_KEY=xK9mP2vR8wQ...`
- **Used by:** `auth/jwt_utils.py`, all authentication modules

#### `JWT_ALGORITHM`
- **Description:** Algorithm for JWT token signing
- **Default:** `HS256`
- **Options:** `HS256`, `HS384`, `HS512` (symmetric), `RS256`, `RS384`, `RS512` (asymmetric)
- **Example:** `JWT_ALGORITHM=HS256`
- **Used by:** `auth/jwt_utils.py`

#### `JWT_EXPIRATION_HOURS`
- **Description:** JWT token expiration time in hours
- **Default:** `24`
- **Example:** `JWT_EXPIRATION_HOURS=24`
- **Used by:** `auth/jwt_utils.py`

#### `AUTH_SERVICE_URL`
- **Description:** Full URL of the authentication service
- **Default:** `http://localhost:9998`
- **Example:** `AUTH_SERVICE_URL=http://localhost:9998`
- **Used by:** `main.py` (CLI), web UI

### Phase 3: Session/Memory (Future)

#### `SESSION_TYPE`
- **Description:** Session storage backend
- **Options:** `memory`, `database`, `redis`
- **Default:** `memory`
- **Example:** `SESSION_TYPE=database`
- **Status:** Not yet implemented

#### `DATABASE_URL`
- **Description:** Database connection string for session persistence
- **Examples:**
  - SQLite: `DATABASE_URL=sqlite:///./jarvis.db`
  - PostgreSQL: `DATABASE_URL=postgresql://user:pass@localhost/jarvis`
  - MySQL: `DATABASE_URL=mysql://user:pass@localhost/jarvis`
- **Status:** Not yet implemented

### Phase 4: OAuth 2.0 (Future)

#### `OAUTH_PROVIDER`
- **Description:** OAuth 2.0 provider for SSO
- **Options:** `google`, `azure`, `auth0`, `okta`
- **Example:** `OAUTH_PROVIDER=google`
- **Status:** Not yet implemented

#### `OAUTH_CLIENT_ID`
- **Description:** OAuth client ID from provider
- **Example:** `OAUTH_CLIENT_ID=123456789.apps.googleusercontent.com`
- **Status:** Not yet implemented

#### `OAUTH_CLIENT_SECRET`
- **Description:** OAuth client secret from provider
- **Security:** Keep this secret and never commit to version control
- **Example:** `OAUTH_CLIENT_SECRET=GOCSPX-...`
- **Status:** Not yet implemented

## Phase-Specific Configuration

### Phase 1: Core Functionality (Completed)
**Required Variables:**
- `GOOGLE_API_KEY`

**Optional Variables:**
- `TICKETS_SERVER_PORT`
- `FINOPS_SERVER_PORT`
- `OXYGEN_AGENT_PORT`
- `WEB_UI_PORT`

### Phase 2: JWT Authentication (Current)
**Required Variables:**
- `GOOGLE_API_KEY`
- `JWT_SECRET_KEY`

**Recommended Variables:**
- `AUTH_SERVICE_PORT`
- `AUTH_SERVICE_URL`
- `JWT_ALGORITHM`
- `JWT_EXPIRATION_HOURS`

**Optional Variables:**
- All service ports

### Phase 3: Memory & Persistence (Future)
**Additional Variables:**
- `SESSION_TYPE`
- `DATABASE_URL`
- `VECTOR_DB_TYPE`
- `VERTEX_PROJECT_ID`
- `VERTEX_LOCATION`

### Phase 4: OAuth 2.0 (Future)
**Additional Variables:**
- `OAUTH_PROVIDER`
- `OAUTH_CLIENT_ID`
- `OAUTH_CLIENT_SECRET`
- `OAUTH_REDIRECT_URI`

## Security Best Practices

### Development

1. **Use template values for development:**
```bash
cp .env.template .env
# Edit with your dev keys
```

2. **Never commit `.env` to version control:**
```bash
# Already in .gitignore
.env
```

3. **Use different `.env` files per environment:**
```bash
.env.dev      # Development
.env.staging  # Staging
.env.prod     # Production
```

### Production

1. **Generate strong JWT secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Use output for JWT_SECRET_KEY
```

2. **Use environment-specific secrets:**
```bash
# Production .env should have unique values
JWT_SECRET_KEY=<strong-random-value>
GOOGLE_API_KEY=<production-api-key>
```

3. **Rotate secrets regularly:**
- JWT secret: Every 90 days
- API keys: Per provider recommendations
- OAuth secrets: When required by provider

4. **Use secret management services:**
- Google Secret Manager
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault

5. **Enable HTTPS in production:**
```bash
HTTPS_ENABLED=true
DOMAIN=jarvis.example.com
```

## Troubleshooting

### "GOOGLE_API_KEY not found"
**Solution:** Set the API key in `.env`:
```bash
echo "GOOGLE_API_KEY=your_key_here" >> .env
```

### "JWT_SECRET_KEY not set"
**Solution:** The system uses a default dev key. For production, set explicitly:
```bash
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> .env
```

### "Auth service connection failed"
**Solution:** Check `AUTH_SERVICE_URL` points to running auth service:
```bash
# Verify in .env
AUTH_SERVICE_URL=http://localhost:9998

# Test connection
curl http://localhost:9998/health
```

### "Port already in use"
**Solution:** Change port in `.env` or kill existing process:
```bash
# Change port
WEB_UI_PORT=9000

# Or kill existing process
lsof -ti:9999 | xargs kill -9
```

## Loading Environment Variables

### Python (automatic with dotenv)
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env file
api_key = os.getenv("GOOGLE_API_KEY")
```

### Shell Scripts
```bash
# Load from .env
set -a
source .env
set +a

# Use variables
echo $GOOGLE_API_KEY
```

### Docker
```yaml
# docker-compose.yml
services:
  jarvis:
    env_file:
      - .env
```

## Example Configurations

### Minimal Development Setup
```bash
# .env
GOOGLE_API_KEY=AIzaSyD...
JWT_SECRET_KEY=dev-secret-key
```

### Full Development Setup
```bash
# .env
GOOGLE_API_KEY=AIzaSyD...
TICKETS_SERVER_PORT=5001
FINOPS_SERVER_PORT=5002
OXYGEN_AGENT_PORT=8002
AUTH_SERVICE_PORT=9998
WEB_UI_PORT=9999
JWT_SECRET_KEY=dev-secret-key-2025
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
AUTH_SERVICE_URL=http://localhost:9998
```

### Production Setup
```bash
# .env.prod
GOOGLE_API_KEY=<production-key>
TICKETS_SERVER_PORT=5001
FINOPS_SERVER_PORT=5002
OXYGEN_AGENT_PORT=8002
AUTH_SERVICE_PORT=9998
WEB_UI_PORT=9999
JWT_SECRET_KEY=<strong-random-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8
AUTH_SERVICE_URL=https://auth.jarvis.example.com
HTTPS_ENABLED=true
DOMAIN=jarvis.example.com
```

## References

- **Phase 2 Plan:** `PHASE_2_PLAN.md`
- **Phase 2 Summary:** `PHASE_2_SUMMARY.md`
- **Authentication Flow:** `AUTHENTICATION_FLOW.md`
- **Template File:** `.env.template`
