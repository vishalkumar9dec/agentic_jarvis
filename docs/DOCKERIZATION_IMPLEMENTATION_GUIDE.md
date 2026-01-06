# Dockerization Implementation Guide - Agentic Jarvis

## Overview

This document provides a detailed task breakdown with prompts for implementing the complete Dockerization of Agentic Jarvis. Each task includes clear instructions, expected outputs, and validation steps.

---

## Task Breakdown

### Phase 1: Supporting Files (Foundation)

#### Task 1.1: Create .dockerignore
**Priority:** High
**Estimated Time:** 5 minutes
**Dependencies:** None

**Prompt:**
```
Create a .dockerignore file in the project root (/Users/vishalkumar/projects/agentic_jarvis/.dockerignore)
that excludes unnecessary files from Docker builds.

Include:
- Virtual environments (.venv/)
- Python cache (__pycache__/, *.pyc)
- Git files (.git/)
- Test artifacts (.pytest_cache/, .coverage)
- Logs (logs/, *.log)
- Environment files (.env)
- Database files (*.db, *.db-shm, *.db-wal)
- Documentation (docs/)
- macOS files (.DS_Store)
- Data directories (data/)
```

**Expected Output:**
- File: `.dockerignore`
- Size reduction: ~50-70% in Docker build context

**Validation:**
```bash
# Verify file exists
ls -la .dockerignore

# Test context size
docker build --no-cache -t test-context -f tickets_agent_service/Dockerfile . 2>&1 | grep "Sending build context"
```

---

#### Task 1.2: Create Environment Template
**Priority:** High
**Estimated Time:** 5 minutes
**Dependencies:** None

**Prompt:**
```
Create a .env.docker.template file in the project root that serves as a template for Docker environment variables.

Include:
1. GOOGLE_API_KEY (required for LLM calls)
2. JWT_SECRET_KEY (required for authentication, min 32 characters)
3. Comments explaining each variable
4. Warnings about security
```

**Expected Output:**
- File: `.env.docker.template`
- Clear documentation for required env vars

**Validation:**
```bash
# Verify template exists
cat .env.docker.template

# User should copy to .env
cp .env.docker.template .env
# Then edit .env with actual values
```

---

### Phase 2: Agent Service Dockerfiles

#### Task 2.1: Create Tickets Agent Dockerfile
**Priority:** Critical
**Estimated Time:** 15 minutes
**Dependencies:** Task 1.1

**Prompt:**
```
Create a Dockerfile for the Tickets Agent Service at tickets_agent_service/Dockerfile.

Requirements:
- Multi-stage build (builder + runtime)
- Base image: python:3.11-slim
- Builder stage: Install gcc, g++, copy requirements.txt, install Python deps
- Runtime stage: Install curl (for healthcheck), copy Python deps from builder
- Security: Run as non-root user (appuser, uid 1000)
- Port: 8080
- Health check: curl http://localhost:8080/.well-known/agent-card.json
- Health check timing: interval=10s, timeout=5s, start-period=20s, retries=3
- CMD: uvicorn tickets_agent_service.agent:a2a_app --host 0.0.0.0 --port 8080
- ENV: PYTHONUNBUFFERED=1
- Context: Copy entire project (COPY . .) for shared imports

Reference pattern: agent_registry_service/Dockerfile
```

**Expected Output:**
- File: `tickets_agent_service/Dockerfile`
- Multi-stage, ~150-200 lines with comments

**Validation:**
```bash
# Test build
docker build -t jarvis-tickets-agent -f tickets_agent_service/Dockerfile .

# Verify image size (should be < 800MB)
docker images jarvis-tickets-agent

# Test run
docker run -d --name test-tickets -p 8080:8080 \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  jarvis-tickets-agent

# Wait for health check
sleep 25

# Test agent card endpoint
curl http://localhost:8080/.well-known/agent-card.json

# Cleanup
docker stop test-tickets && docker rm test-tickets
```

---

#### Task 2.2: Create FinOps Agent Dockerfile
**Priority:** Critical
**Estimated Time:** 10 minutes
**Dependencies:** Task 2.1

**Prompt:**
```
Create a Dockerfile for the FinOps Agent Service at finops_agent_service/Dockerfile.

This is identical to tickets_agent_service/Dockerfile except for:
- Port: 8081
- Health check URL: http://localhost:8081/.well-known/agent-card.json
- CMD: uvicorn finops_agent_service.agent:a2a_app --host 0.0.0.0 --port 8081

Copy the structure from tickets_agent_service/Dockerfile and modify these three elements.
```

**Expected Output:**
- File: `finops_agent_service/Dockerfile`

**Validation:**
```bash
# Test build
docker build -t jarvis-finops-agent -f finops_agent_service/Dockerfile .

# Test run
docker run -d --name test-finops -p 8081:8081 \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  jarvis-finops-agent

# Wait and test
sleep 25
curl http://localhost:8081/.well-known/agent-card.json

# Cleanup
docker stop test-finops && docker rm test-finops
```

---

#### Task 2.3: Create Oxygen Agent Dockerfile
**Priority:** Critical
**Estimated Time:** 10 minutes
**Dependencies:** Task 2.1

**Prompt:**
```
Create a Dockerfile for the Oxygen Agent Service at oxygen_agent_service/Dockerfile.

This is identical to tickets_agent_service/Dockerfile except for:
- Port: 8082
- Health check URL: http://localhost:8082/.well-known/agent-card.json
- CMD: uvicorn oxygen_agent_service.agent:a2a_app --host 0.0.0.0 --port 8082
```

**Expected Output:**
- File: `oxygen_agent_service/Dockerfile`

**Validation:**
```bash
# Test build
docker build -t jarvis-oxygen-agent -f oxygen_agent_service/Dockerfile .

# Test run
docker run -d --name test-oxygen -p 8082:8082 \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  jarvis-oxygen-agent

# Wait and test
sleep 25
curl http://localhost:8082/.well-known/agent-card.json

# Cleanup
docker stop test-oxygen && docker rm test-oxygen
```

---

### Phase 3: Supporting Service Dockerfiles

#### Task 3.1: Create Auth Service Dockerfile
**Priority:** Critical
**Estimated Time:** 15 minutes
**Dependencies:** Task 1.1

**Prompt:**
```
Create a Dockerfile for the Auth Service at auth/Dockerfile.

Requirements:
- Multi-stage build (same pattern as agent services)
- Base image: python:3.11-slim
- Port: 9998
- Health check: curl http://localhost:9998/health
- Health check timing: interval=10s, timeout=5s, start-period=10s, retries=3
- CMD: uvicorn auth.auth_server:app --host 0.0.0.0 --port 9998
- ENV: JWT_SECRET_KEY, JWT_ALGORITHM=HS256, PYTHONUNBUFFERED=1
- Security: Non-root user (appuser)
```

**Expected Output:**
- File: `auth/Dockerfile`

**Validation:**
```bash
# Test build
docker build -t jarvis-auth -f auth/Dockerfile .

# Test run
docker run -d --name test-auth -p 9998:9998 \
  -e JWT_SECRET_KEY="test-secret-key-min-32-characters-long" \
  jarvis-auth

# Wait and test
sleep 15
curl http://localhost:9998/health

# Test login endpoint
curl -X POST http://localhost:9998/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"vishal","password":"password123"}'

# Cleanup
docker stop test-auth && docker rm test-auth
```

---

#### Task 3.2: Create Web UI Dockerfile
**Priority:** Critical
**Estimated Time:** 15 minutes
**Dependencies:** Task 1.1

**Prompt:**
```
Create a Dockerfile for the Web UI at web_ui/Dockerfile.

Requirements:
- Multi-stage build
- Base image: python:3.11-slim
- Port: 9999
- Health check: curl http://localhost:9999/health
- Health check timing: interval=15s, timeout=5s, start-period=20s, retries=3
- CMD: uvicorn web_ui.server_phase2:app --host 0.0.0.0 --port 9999
- ENV: JARVIS_API_URL, AUTH_SERVICE_URL, PYTHONUNBUFFERED=1
- Security: Non-root user (appuser)
- Note: Copy static files (web_ui/static/) with application code
```

**Expected Output:**
- File: `web_ui/Dockerfile`

**Validation:**
```bash
# Test build
docker build -t jarvis-web-ui -f web_ui/Dockerfile .

# Test run (note: will fail without other services, but should start)
docker run -d --name test-web -p 9999:9999 \
  -e JARVIS_API_URL="http://jarvis-api:8000" \
  -e AUTH_SERVICE_URL="http://auth-service:9998" \
  jarvis-web-ui

# Wait and test
sleep 20
curl http://localhost:9999/health

# Test static files
curl -I http://localhost:9999/login.html

# Cleanup
docker stop test-web && docker rm test-web
```

---

### Phase 4: Jarvis API Service (NEW)

#### Task 4.1: Create Jarvis API Service Directory
**Priority:** Critical
**Estimated Time:** 5 minutes
**Dependencies:** None

**Prompt:**
```
Create a new directory for the Jarvis API Service:

mkdir -p jarvis_api_service
touch jarvis_api_service/__init__.py

This will contain:
- api.py (FastAPI wrapper)
- Dockerfile
```

**Expected Output:**
- Directory: `jarvis_api_service/`
- File: `jarvis_api_service/__init__.py`

**Validation:**
```bash
ls -la jarvis_api_service/
```

---

#### Task 4.2: Create Jarvis API Service Implementation
**Priority:** Critical
**Estimated Time:** 45 minutes
**Dependencies:** Task 4.1

**Prompt:**
```
Create jarvis_api_service/api.py - a FastAPI wrapper around JarvisOrchestrator.

Requirements:

1. Imports:
   - FastAPI, HTTPException, Header
   - Pydantic BaseModel
   - JarvisOrchestrator from jarvis_agent.main_with_registry
   - os, sys for environment and paths

2. Models:
   - InvokeRequest: query (str), session_id (Optional[str])
   - InvokeResponse: response (str), session_id (str)

3. Global state:
   - orchestrators: Dict[str, JarvisOrchestrator] = {}  # Cache by JWT token
   - Reason: Avoid recreating orchestrator on every request (expensive)

4. Endpoints:

   a) GET /health
      - Return: {"status": "healthy", "service": "jarvis_api", "port": 8000}

   b) POST /invoke
      - Accept: InvokeRequest, Authorization header (Bearer token)
      - Extract JWT token from header
      - Get or create orchestrator for this token:
        * If token not in cache: orchestrators[token] = JarvisOrchestrator(
            jwt_token=token,
            registry_url=os.getenv("REGISTRY_SERVICE_URL", "http://agent-registry:8003")
          )
      - Call: orchestrator.handle_query(query=request.query, session_id=request.session_id)
      - Get session_id from orchestrator if not provided
      - Return: InvokeResponse with response and session_id
      - Error handling: 401 for missing/invalid token, 500 for other errors

   c) GET /sessions (optional)
      - List sessions for authenticated user

5. FastAPI app config:
   - CORS enabled for all origins
   - Title: "Jarvis Orchestrator API"
   - Version: "1.0.0"

6. Main block:
   - if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=8000)

Implementation notes:
- Use environment variables for service URLs
- Add detailed docstrings
- Add logging for debugging
- Handle orchestrator cleanup on errors
```

**Expected Output:**
- File: `jarvis_api_service/api.py` (~200-250 lines)

**Validation:**
```bash
# Test syntax
python -m py_compile jarvis_api_service/api.py

# Test imports (without running)
python -c "import jarvis_api_service.api"

# Manual test (requires other services running):
# python -m jarvis_api_service.api
```

---

#### Task 4.3: Create Jarvis API Dockerfile
**Priority:** Critical
**Estimated Time:** 15 minutes
**Dependencies:** Task 4.2

**Prompt:**
```
Create a Dockerfile for the Jarvis API Service at jarvis_api_service/Dockerfile.

Requirements:
- Multi-stage build (same pattern as other services)
- Base image: python:3.11-slim
- Port: 8000
- Health check: curl http://localhost:8000/health
- Health check timing: interval=15s, timeout=10s, start-period=40s, retries=3
  (longer start-period because orchestrator initialization is slow)
- CMD: uvicorn jarvis_api_service.api:app --host 0.0.0.0 --port 8000
- ENV: REGISTRY_SERVICE_URL, AUTH_SERVICE_URL, PYTHONUNBUFFERED=1
- Security: Non-root user (appuser)
```

**Expected Output:**
- File: `jarvis_api_service/Dockerfile`

**Validation:**
```bash
# Test build
docker build -t jarvis-api -f jarvis_api_service/Dockerfile .

# Test run (requires registry service, will fail but should start)
docker run -d --name test-jarvis-api -p 8000:8000 \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  -e REGISTRY_SERVICE_URL="http://agent-registry:8003" \
  jarvis-api

# Wait longer for startup
sleep 45

# Test health (may fail if registry not available)
curl http://localhost:8000/health || echo "Expected failure without registry"

# Cleanup
docker stop test-jarvis-api && docker rm test-jarvis-api
```

---

### Phase 5: Modify Web UI for HTTP Communication

#### Task 5.1: Update Web UI to Call Jarvis API
**Priority:** Critical
**Estimated Time:** 30 minutes
**Dependencies:** Task 4.2

**Prompt:**
```
Modify web_ui/server_phase2.py to call the Jarvis API service via HTTP instead of importing JarvisOrchestrator directly.

Changes needed:

1. Remove direct import (line 21):
   DELETE: from jarvis_agent.main_with_registry import JarvisOrchestrator

2. Add HTTP client import:
   ADD: import httpx

3. Add environment variable for Jarvis API URL (after imports):
   JARVIS_API_URL = os.getenv("JARVIS_API_URL", "http://jarvis-api:8000")

4. Update /api/chat endpoint (lines 177-256):
   - Remove all JarvisOrchestrator instantiation code
   - Replace with HTTP call to Jarvis API:

     async with httpx.AsyncClient() as client:
         response = await client.post(
             f"{JARVIS_API_URL}/invoke",
             json={"query": request.message, "session_id": None},
             headers={"Authorization": authorization},
             timeout=30.0
         )

         if response.status_code != 200:
             raise HTTPException(
                 status_code=response.status_code,
                 detail=f"Jarvis API error: {response.text}"
             )

         data = response.json()
         return ChatResponse(
             response=data["response"],
             session_id=data["session_id"]
         )

5. Update /api/history endpoint (lines 259-323):
   - Keep SessionClient usage for now (direct access)
   - Alternative: Create /api/history endpoint in Jarvis API

6. Keep other endpoints unchanged (/api/suggestions, /api/sessions)

7. Update error handling to properly close HTTP connections

Notes:
- This decouples Web UI from Jarvis orchestrator
- Enables independent scaling
- Web UI becomes a thin client
- Maintain backward compatibility where possible
```

**Expected Output:**
- Modified file: `web_ui/server_phase2.py`
- Reduced imports
- HTTP-based communication with Jarvis API

**Validation:**
```bash
# Test syntax
python -m py_compile web_ui/server_phase2.py

# Test imports
python -c "import web_ui.server_phase2"

# Manual integration test (requires all services):
# 1. Start docker-compose
# 2. Login at http://localhost:9999/login.html
# 3. Send chat message
# 4. Verify response
```

---

### Phase 6: Docker Compose Configuration

#### Task 6.1: Create docker-compose.yml
**Priority:** Critical
**Estimated Time:** 45 minutes
**Dependencies:** All Dockerfile tasks (2.1-2.3, 3.1-3.2, 4.3)

**Prompt:**
```
Create docker-compose.yml in the project root that orchestrates all 7 services.

Services to include:

1. auth-service
   - Container name: jarvis-auth
   - Build: context=., dockerfile=auth/Dockerfile
   - Ports: 9998:9998
   - Environment: JWT_SECRET_KEY, JWT_ALGORITHM, LOG_LEVEL
   - Health check: curl localhost:9998/health
   - Network: jarvis-network
   - Restart: unless-stopped

2. tickets-agent
   - Container name: jarvis-tickets-agent
   - Build: context=., dockerfile=tickets_agent_service/Dockerfile
   - Ports: 8080:8080
   - Environment: GOOGLE_API_KEY, LOG_LEVEL
   - Depends on: auth-service (service_healthy)
   - Health check: curl localhost:8080/.well-known/agent-card.json
   - Network: jarvis-network
   - Restart: unless-stopped

3. finops-agent
   - Container name: jarvis-finops-agent
   - Build: context=., dockerfile=finops_agent_service/Dockerfile
   - Ports: 8081:8081
   - Environment: GOOGLE_API_KEY, LOG_LEVEL
   - Depends on: auth-service (service_healthy)
   - Health check: curl localhost:8081/.well-known/agent-card.json
   - Network: jarvis-network
   - Restart: unless-stopped

4. oxygen-agent
   - Container name: jarvis-oxygen-agent
   - Build: context=., dockerfile=oxygen_agent_service/Dockerfile
   - Ports: 8082:8082
   - Environment: GOOGLE_API_KEY, LOG_LEVEL
   - Depends on: auth-service (service_healthy)
   - Health check: curl localhost:8082/.well-known/agent-card.json
   - Network: jarvis-network
   - Restart: unless-stopped

5. agent-registry
   - Container name: jarvis-agent-registry
   - Build: context=., dockerfile=agent_registry_service/Dockerfile
   - Ports: 8003:8003
   - Environment: GOOGLE_API_KEY, REGISTRY_FILE_PATH, SESSION_DB_PATH, CORS_ORIGINS
   - Volumes: agent-registry-data:/app/data
   - Depends on: tickets-agent, finops-agent, oxygen-agent (all service_healthy)
   - Health check: curl localhost:8003/health
   - Network: jarvis-network
   - Restart: unless-stopped

6. jarvis-api
   - Container name: jarvis-orchestrator-api
   - Build: context=., dockerfile=jarvis_api_service/Dockerfile
   - Ports: 8000:8000
   - Environment: GOOGLE_API_KEY, REGISTRY_SERVICE_URL, AUTH_SERVICE_URL, *_AGENT_URL
   - Depends on: agent-registry (service_healthy)
   - Health check: curl localhost:8000/health
   - Network: jarvis-network
   - Restart: unless-stopped

7. web-ui
   - Container name: jarvis-web-ui
   - Build: context=., dockerfile=web_ui/Dockerfile
   - Ports: 9999:9999
   - Environment: JARVIS_API_URL, AUTH_SERVICE_URL
   - Depends on: jarvis-api, auth-service (service_healthy)
   - Health check: curl localhost:9999/health
   - Network: jarvis-network
   - Restart: unless-stopped

Networks:
- jarvis-network: bridge driver, name: jarvis-network

Volumes:
- agent-registry-data: local driver, name: jarvis-agent-registry-data

Additional:
- Version: 3.8
- Use ${VAR} syntax for environment variables from .env file
- Add comments for each service explaining its purpose
```

**Expected Output:**
- File: `docker-compose.yml` (~250-300 lines)

**Validation:**
```bash
# Validate syntax
docker-compose config

# Check for errors
docker-compose config --quiet && echo "✓ Valid" || echo "✗ Invalid"

# Dry run (shows what would be created)
docker-compose up --no-start

# Cleanup dry run
docker-compose down
```

---

### Phase 7: Integration Testing

#### Task 7.1: Create Integration Test Directory
**Priority:** High
**Estimated Time:** 5 minutes
**Dependencies:** None

**Prompt:**
```
Create directory structure for integration tests:

mkdir -p tests/integration
touch tests/integration/__init__.py
touch tests/integration/test_docker_deployment.py
```

**Expected Output:**
- Directory: `tests/integration/`
- Files: `__init__.py`, `test_docker_deployment.py`

**Validation:**
```bash
ls -la tests/integration/
```

---

#### Task 7.2: Create Integration Test Suite
**Priority:** High
**Estimated Time:** 30 minutes
**Dependencies:** Task 7.1

**Prompt:**
```
Create tests/integration/test_docker_deployment.py with comprehensive integration tests.

Test cases to include:

1. test_all_services_healthy()
   - Check health endpoints for all 7 services
   - Services: auth (9998), tickets (8080), finops (8081), oxygen (8082),
     registry (8003), jarvis-api (8000), web-ui (9999)
   - Assert 200 status for each

2. test_authentication_flow()
   - POST to auth-service login endpoint
   - Verify JWT token received
   - Verify token contains expected claims

3. test_agent_cards_accessible()
   - GET agent-card.json from each agent service
   - Verify JSON structure contains: name, description, capabilities

4. test_single_agent_query()
   - Login to get JWT token
   - POST to jarvis-api /invoke with "show my tickets"
   - Verify response contains ticket information
   - Verify session_id returned

5. test_multi_agent_query()
   - Login to get JWT token
   - POST to jarvis-api /invoke with "show my tickets and courses"
   - Verify response contains both ticket and course information
   - Verify multiple agents were invoked

6. test_session_persistence()
   - Create session with first query
   - Send second query with same session_id
   - Verify session maintained across requests

7. test_web_ui_endpoints()
   - GET /login.html (should return HTML)
   - GET /chat.html (should return HTML)
   - GET /health (should return healthy status)

Requirements:
- Use pytest framework
- Use httpx for HTTP requests
- Add pytest fixture for auth_token
- Use proper timeouts (30s for Jarvis API calls)
- Add descriptive assertions with error messages
- Use environment variables or hardcode service URLs (docker network names)

Service URLs in Docker network:
- AUTH_URL = "http://auth-service:9998"
- JARVIS_API_URL = "http://jarvis-api:8000"
- TICKETS_URL = "http://tickets-agent:8080"
- FINOPS_URL = "http://finops-agent:8081"
- OXYGEN_URL = "http://oxygen-agent:8082"
- REGISTRY_URL = "http://agent-registry:8003"
- WEB_URL = "http://web-ui:9999"
```

**Expected Output:**
- File: `tests/integration/test_docker_deployment.py` (~200-250 lines)

**Validation:**
```bash
# Test syntax
python -m py_compile tests/integration/test_docker_deployment.py

# Run tests (requires services to be running)
# pytest tests/integration/ -v
```

---

#### Task 7.3: Create Test Container Dockerfile
**Priority:** High
**Estimated Time:** 10 minutes
**Dependencies:** Task 7.2

**Prompt:**
```
Create tests/integration/Dockerfile for the test container.

Requirements:
- Base image: python:3.11-slim
- Install: pytest, pytest-asyncio, httpx
- Copy entire project
- CMD: pytest tests/integration/ -v --tb=short
- Minimal image, no security hardening needed (test only)
```

**Expected Output:**
- File: `tests/integration/Dockerfile`

**Validation:**
```bash
# Test build
docker build -t jarvis-tests -f tests/integration/Dockerfile .

# Verify image created
docker images jarvis-tests
```

---

#### Task 7.4: Add Test Service to docker-compose
**Priority:** High
**Estimated Time:** 10 minutes
**Dependencies:** Task 7.3

**Prompt:**
```
Add integration-tests service to docker-compose.yml.

Configuration:
- Service name: integration-tests
- Container name: jarvis-integration-tests
- Build: context=., dockerfile=tests/integration/Dockerfile
- Depends on: web-ui (service_healthy) - ensures all services are up
- Networks: jarvis-network
- Profiles: [test] - only runs when explicitly requested
- No ports needed (internal only)
- No restart policy (runs once)

Add at the end of services section, before networks.
```

**Expected Output:**
- Modified: `docker-compose.yml` (add integration-tests service)

**Validation:**
```bash
# Validate config
docker-compose config

# Verify test profile
docker-compose --profile test config | grep -A 10 integration-tests
```

---

### Phase 8: Documentation and Helper Scripts

#### Task 8.1: Create Docker Quick Start Guide
**Priority:** Medium
**Estimated Time:** 20 minutes
**Dependencies:** Task 6.1

**Prompt:**
```
Create docs/DOCKER_QUICKSTART.md with user-friendly quick start guide.

Sections to include:

1. Prerequisites
   - Docker and Docker Compose installed
   - Google API key
   - JWT secret key

2. Initial Setup
   - Copy .env.docker.template to .env
   - Edit .env with actual credentials
   - Verify environment variables

3. Build and Start
   - docker-compose build
   - docker-compose up -d
   - docker-compose ps
   - docker-compose logs -f

4. Accessing Services
   - List all service URLs
   - Web UI: http://localhost:9999
   - Login credentials (demo accounts)

5. Running Tests
   - docker-compose --profile test run integration-tests
   - Expected output

6. Troubleshooting
   - Service won't start (check logs)
   - Health check failing (increase timeout)
   - Port already in use (change ports or kill process)
   - Volume permission issues

7. Cleanup
   - docker-compose down
   - docker-compose down -v (with volumes)
   - docker-compose down --rmi all (with images)

8. Development Workflow
   - Rebuild single service
   - View logs for one service
   - Execute commands in container
   - Hot reload (volume mounting)

Include command examples for each section.
```

**Expected Output:**
- File: `docs/DOCKER_QUICKSTART.md`

**Validation:**
```bash
# Verify file
cat docs/DOCKER_QUICKSTART.md

# Follow the guide manually to ensure accuracy
```

---

#### Task 8.2: Update Main README with Docker Instructions
**Priority:** Medium
**Estimated Time:** 15 minutes
**Dependencies:** Task 8.1

**Prompt:**
```
Update README.md to include Docker deployment section.

Add new section after "Development Commands":

## Docker Deployment

### Quick Start
```bash
# 1. Setup environment
cp .env.docker.template .env
# Edit .env with your GOOGLE_API_KEY and JWT_SECRET_KEY

# 2. Build and start all services
docker-compose up -d

# 3. Access web UI
open http://localhost:9999
```

### Services
- Web UI: http://localhost:9999
- Jarvis API: http://localhost:8000
- Auth Service: http://localhost:9998
- Agent Registry: http://localhost:8003
- Tickets Agent: http://localhost:8080
- FinOps Agent: http://localhost:8081
- Oxygen Agent: http://localhost:8082

### Testing
```bash
docker-compose --profile test run integration-tests
```

For detailed Docker documentation, see [docs/DOCKER_QUICKSTART.md](docs/DOCKER_QUICKSTART.md)

Update the Technology Stack section to mention Docker and docker-compose.
```

**Expected Output:**
- Modified: `README.md`

**Validation:**
```bash
# Verify section added
grep -A 20 "Docker Deployment" README.md
```

---

#### Task 8.3: Create Helper Scripts
**Priority:** Low
**Estimated Time:** 20 minutes
**Dependencies:** Task 6.1

**Prompt:**
```
Create helper scripts in scripts/ directory for common Docker operations.

1. scripts/docker-build.sh
   - Build all services
   - Show progress
   - Display build summary

2. scripts/docker-start.sh
   - Start all services
   - Wait for health checks
   - Display service status
   - Show URLs

3. scripts/docker-stop.sh
   - Stop all services gracefully
   - Show stopped services

4. scripts/docker-restart.sh
   - Restart all services
   - Useful for applying config changes

5. scripts/docker-logs.sh
   - Tail logs from all services
   - Optional: pass service name for specific logs

6. scripts/docker-test.sh
   - Run integration tests
   - Display results
   - Exit with test status code

Make all scripts executable (chmod +x).
```

**Expected Output:**
- Files: `scripts/docker-*.sh` (6 files)

**Validation:**
```bash
# Verify scripts created
ls -la scripts/docker-*.sh

# Test each script (requires services)
# ./scripts/docker-build.sh
# ./scripts/docker-start.sh
# etc.
```

---

### Phase 9: Validation and Testing

#### Task 9.1: End-to-End Manual Test
**Priority:** Critical
**Estimated Time:** 30 minutes
**Dependencies:** All previous tasks

**Prompt:**
```
Perform comprehensive manual testing of the Dockerized system.

Test Checklist:

1. Environment Setup
   ☐ .env file created with valid credentials
   ☐ No port conflicts on host machine

2. Build Phase
   ☐ docker-compose build completes without errors
   ☐ All 7 images created successfully
   ☐ Image sizes reasonable (< 1GB each)

3. Startup Phase
   ☐ docker-compose up -d starts all services
   ☐ All containers in "running" state within 90 seconds
   ☐ All health checks pass within 120 seconds

4. Service Accessibility
   ☐ Auth service responds: curl http://localhost:9998/health
   ☐ Tickets agent card: curl http://localhost:8080/.well-known/agent-card.json
   ☐ FinOps agent card: curl http://localhost:8081/.well-known/agent-card.json
   ☐ Oxygen agent card: curl http://localhost:8082/.well-known/agent-card.json
   ☐ Registry service: curl http://localhost:8003/health
   ☐ Jarvis API: curl http://localhost:8000/health
   ☐ Web UI: curl http://localhost:9999/health

5. Authentication Flow
   ☐ Login page loads: http://localhost:9999/login.html
   ☐ Login with demo account (vishal/password123)
   ☐ Redirect to chat page
   ☐ JWT token stored in browser

6. Chat Functionality
   ☐ Send query: "show my tickets"
   ☐ Receive response with ticket information
   ☐ Send query: "show my courses"
   ☐ Receive response with course information
   ☐ Send query: "show my tickets and courses"
   ☐ Receive combined response from multiple agents

7. Session Persistence
   ☐ Refresh page, session maintained
   ☐ View conversation history
   ☐ Session ID consistent across requests

8. Error Handling
   ☐ Invalid credentials rejected
   ☐ Malformed query handled gracefully
   ☐ Expired token detected

9. Integration Tests
   ☐ docker-compose --profile test run integration-tests
   ☐ All tests pass
   ☐ No errors in logs

10. Cleanup
    ☐ docker-compose down completes successfully
    ☐ All containers stopped
    ☐ Volumes preserved (agent-registry-data)

Document any failures or issues encountered.
```

**Expected Output:**
- Test report document
- Screenshots of successful operations
- List of any issues found

**Validation:**
```bash
# Save test report
echo "Test Results: $(date)" > test_report.txt
# Append results as you test
```

---

#### Task 9.2: Performance Baseline
**Priority:** Low
**Estimated Time:** 20 minutes
**Dependencies:** Task 9.1

**Prompt:**
```
Establish performance baselines for Dockerized deployment.

Metrics to measure:

1. Startup Time
   - Time from `docker-compose up -d` to all services healthy
   - Target: < 120 seconds

2. Memory Usage
   - docker stats (show memory for each container)
   - Total memory consumption
   - Target: < 4GB total

3. Response Time
   - Single agent query latency
   - Multi-agent query latency
   - Target: < 5 seconds per query

4. Build Time
   - docker-compose build --no-cache (full rebuild)
   - docker-compose build (incremental)

5. Image Sizes
   - docker images | grep jarvis
   - List size of each service image

Document baselines for future comparison.
```

**Expected Output:**
- Performance baseline document
- Metrics for optimization reference

**Validation:**
```bash
# Measure startup time
time docker-compose up -d

# Check memory
docker stats --no-stream

# Test query latency
time curl -X POST http://localhost:8000/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"show my tickets"}'
```

---

## Summary of Deliverables

### Files to Create (11)
1. `.dockerignore` - Build context optimization
2. `.env.docker.template` - Environment variable template
3. `tickets_agent_service/Dockerfile` - Tickets agent container
4. `finops_agent_service/Dockerfile` - FinOps agent container
5. `oxygen_agent_service/Dockerfile` - Oxygen agent container
6. `auth/Dockerfile` - Auth service container
7. `jarvis_api_service/api.py` - Jarvis orchestrator HTTP wrapper
8. `jarvis_api_service/Dockerfile` - Jarvis API container
9. `web_ui/Dockerfile` - Web UI container
10. `docker-compose.yml` - Service orchestration
11. `tests/integration/test_docker_deployment.py` - Integration tests

### Files to Modify (2)
1. `web_ui/server_phase2.py` - HTTP-based Jarvis API calls
2. `README.md` - Docker deployment instructions

### Documentation (2)
1. `docs/DOCKER_QUICKSTART.md` - User guide
2. `docs/DOCKERIZATION_IMPLEMENTATION_GUIDE.md` - This file

### Helper Scripts (6)
1. `scripts/docker-build.sh`
2. `scripts/docker-start.sh`
3. `scripts/docker-stop.sh`
4. `scripts/docker-restart.sh`
5. `scripts/docker-logs.sh`
6. `scripts/docker-test.sh`

---

## Implementation Order

### Week 1: Foundation & Core Services
- Day 1: Tasks 1.1-1.2, 2.1-2.3 (Supporting files, agent Dockerfiles)
- Day 2: Tasks 3.1-3.2, 4.1-4.2 (Auth, Web UI, Jarvis API implementation)
- Day 3: Task 4.3, 5.1 (Jarvis Dockerfile, Web UI modifications)

### Week 2: Integration & Testing
- Day 4: Task 6.1 (docker-compose.yml)
- Day 5: Tasks 7.1-7.4 (Integration tests)
- Day 6: Tasks 8.1-8.3 (Documentation and scripts)

### Week 3: Validation
- Day 7: Tasks 9.1-9.2 (Manual testing, performance baseline)

---

## Success Criteria

✅ All 7 services containerized
✅ docker-compose up succeeds
✅ All health checks pass within 120 seconds
✅ Integration tests pass (90%+ success rate)
✅ Web UI functional end-to-end
✅ Multi-agent queries work correctly
✅ Session persistence across restarts
✅ Documentation complete and accurate

---

## Next Steps After Dockerization

1. **Cloud Run Migration**
   - Push images to Google Container Registry
   - Deploy each service to Cloud Run
   - Configure service-to-service authentication
   - Update URLs to Cloud Run endpoints

2. **CI/CD Pipeline**
   - GitHub Actions for automated builds
   - Automated testing on pull requests
   - Automated deployment to staging/production

3. **Monitoring & Observability**
   - Add Prometheus metrics
   - Centralized logging (Fluentd/ELK)
   - Distributed tracing (OpenTelemetry)

4. **Security Hardening**
   - Docker secrets for sensitive data
   - Network policies
   - Image scanning (Trivy, Clair)
   - Runtime security (Falco)

---

*End of Implementation Guide*
