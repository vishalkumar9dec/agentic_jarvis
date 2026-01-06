# Dockerization Task Checklist - Agentic Jarvis

## Overview
This checklist tracks the implementation progress for Dockerizing all services in the Agentic Jarvis system.

**Goal:** Containerize 7 services with docker-compose, enable integration testing, prepare for Cloud Run deployment.

**Estimated Total Time:** 12-15 hours

---

## Phase 1: Foundation (Est: 10 mins)

### Supporting Files
- [ ] **Task 1.1** - Create `.dockerignore` (5 mins)
  - Excludes unnecessary files from Docker builds
  - Reduces build context by ~50-70%

- [ ] **Task 1.2** - Create `.env.docker.template` (5 mins)
  - Environment variable template
  - Documents required credentials

**Validation:** Build context size reduced, template file created

---

## Phase 2: Agent Service Dockerfiles (Est: 35 mins)

### Dockerfiles for A2A Agents
- [ ] **Task 2.1** - Create `tickets_agent_service/Dockerfile` (15 mins)
  - Multi-stage build, port 8080
  - Health check: agent-card.json endpoint
  - **Critical:** This is the reference pattern

- [ ] **Task 2.2** - Create `finops_agent_service/Dockerfile` (10 mins)
  - Clone tickets Dockerfile, change port to 8081

- [ ] **Task 2.3** - Create `oxygen_agent_service/Dockerfile` (10 mins)
  - Clone tickets Dockerfile, change port to 8082

**Validation:** All 3 agent images build successfully, containers start, agent cards accessible

---

## Phase 3: Supporting Service Dockerfiles (Est: 30 mins)

### Auth and Web UI
- [ ] **Task 3.1** - Create `auth/Dockerfile` (15 mins)
  - Port 9998, JWT authentication
  - Health check: /health endpoint

- [ ] **Task 3.2** - Create `web_ui/Dockerfile` (15 mins)
  - Port 9999, static file serving
  - Health check: /health endpoint

**Validation:** Auth service login works, Web UI static pages load

---

## Phase 4: Jarvis API Service - NEW (Est: 1 hour)

### HTTP Wrapper for Orchestrator
- [ ] **Task 4.1** - Create `jarvis_api_service/` directory (5 mins)
  - New microservice directory structure

- [ ] **Task 4.2** - Create `jarvis_api_service/api.py` (45 mins)
  - **CRITICAL:** FastAPI wrapper around JarvisOrchestrator
  - Endpoints: /health, /invoke
  - Token-based orchestrator caching

- [ ] **Task 4.3** - Create `jarvis_api_service/Dockerfile` (15 mins)
  - Port 8000, longer startup time (40s)

**Validation:** Jarvis API accepts queries, returns responses, maintains sessions

---

## Phase 5: Web UI Modification (Est: 30 mins)

### Decouple Web UI from Orchestrator
- [ ] **Task 5.1** - Modify `web_ui/server_phase2.py` (30 mins)
  - **CRITICAL:** Replace direct import with HTTP calls
  - Remove: `from jarvis_agent.main_with_registry import JarvisOrchestrator`
  - Add: HTTP client calling Jarvis API
  - Update /api/chat endpoint

**Validation:** Web UI successfully calls Jarvis API, chat works end-to-end

---

## Phase 6: Docker Compose (Est: 45 mins)

### Service Orchestration
- [ ] **Task 6.1** - Create `docker-compose.yml` (45 mins)
  - **CRITICAL:** Orchestrate all 7 services
  - Define networks, volumes, dependencies
  - Health check conditions
  - Proper startup order

**Validation:** `docker-compose config` succeeds, `docker-compose up` starts all services

---

## Phase 7: Integration Testing (Est: 55 mins)

### Automated Testing
- [ ] **Task 7.1** - Create `tests/integration/` directory (5 mins)
  - Test structure setup

- [ ] **Task 7.2** - Create `test_docker_deployment.py` (30 mins)
  - 7 test cases covering full flow
  - Health checks, authentication, queries

- [ ] **Task 7.3** - Create `tests/integration/Dockerfile` (10 mins)
  - Test container with pytest

- [ ] **Task 7.4** - Add test service to docker-compose (10 mins)
  - Profile: test (opt-in)

**Validation:** `docker-compose --profile test run integration-tests` passes

---

## Phase 8: Documentation (Est: 55 mins)

### User Documentation
- [ ] **Task 8.1** - Create `docs/DOCKER_QUICKSTART.md` (20 mins)
  - User-friendly quick start guide
  - Prerequisites, setup, troubleshooting

- [ ] **Task 8.2** - Update `README.md` (15 mins)
  - Add Docker deployment section
  - Link to quickstart guide

- [ ] **Task 8.3** - Create helper scripts (20 mins)
  - 6 scripts: build, start, stop, restart, logs, test
  - Make executable

**Validation:** Documentation is clear, scripts work correctly

---

## Phase 9: Validation (Est: 50 mins)

### Final Testing
- [ ] **Task 9.1** - End-to-end manual test (30 mins)
  - **CRITICAL:** Comprehensive validation
  - 10-point checklist covering all functionality
  - Document any issues

- [ ] **Task 9.2** - Performance baseline (20 mins)
  - Measure startup time, memory, response time
  - Document baselines for optimization

**Validation:** All tests pass, system performs within targets

---

## Critical Path Items (Must Complete)

These tasks are essential and block other work:

1. ✅ **Task 2.1** - Tickets Dockerfile (reference pattern for 2.2, 2.3)
2. ✅ **Task 4.2** - Jarvis API implementation (enables 5.1, 6.1)
3. ✅ **Task 5.1** - Web UI HTTP modification (enables end-to-end flow)
4. ✅ **Task 6.1** - docker-compose.yml (enables all testing)
5. ✅ **Task 9.1** - Manual validation (confirms system works)

---

## Deliverables Summary

| Category | Count | Files |
|----------|-------|-------|
| New Dockerfiles | 6 | tickets, finops, oxygen, auth, web-ui, jarvis-api |
| New Python Files | 1 | jarvis_api_service/api.py |
| Modified Files | 2 | web_ui/server_phase2.py, README.md |
| Configuration | 3 | docker-compose.yml, .dockerignore, .env.docker.template |
| Tests | 2 | test_docker_deployment.py, tests/integration/Dockerfile |
| Documentation | 2 | DOCKER_QUICKSTART.md, DOCKERIZATION_IMPLEMENTATION_GUIDE.md |
| Scripts | 6 | docker-{build,start,stop,restart,logs,test}.sh |
| **Total** | **22 files** | |

---

## Success Metrics

### Functional Requirements
- [ ] All 7 services start successfully
- [ ] All health checks pass within 120 seconds
- [ ] User can login via Web UI
- [ ] Single-agent queries work (e.g., "show my tickets")
- [ ] Multi-agent queries work (e.g., "show my tickets and courses")
- [ ] Session persistence across requests
- [ ] Integration tests pass (≥90% success rate)

### Non-Functional Requirements
- [ ] Startup time < 120 seconds
- [ ] Total memory usage < 4GB
- [ ] Query response time < 5 seconds
- [ ] Docker images optimized (multi-stage builds)
- [ ] Security: non-root users in containers
- [ ] Documentation complete and accurate

---

## Known Challenges & Solutions

### Challenge 1: Import Path Issues
**Problem:** Services import shared modules (e.g., `auth.jwt_utils`)
**Solution:** Use `context: .` (project root) in all Dockerfiles, copy entire project

### Challenge 2: Health Check Timing
**Problem:** ADK initialization takes 20-30 seconds
**Solution:** Use `start_period: 40s` for agent services, 20s for others

### Challenge 3: Orchestrator Instance Creation
**Problem:** Creating JarvisOrchestrator on every request is expensive
**Solution:** Cache by JWT token in Jarvis API service

### Challenge 4: Volume Permissions
**Problem:** Non-root user cannot write to volumes
**Solution:** Use named volumes (Docker manages permissions automatically)

---

## Post-Dockerization Tasks (Future)

### Immediate Next Steps
1. **Cloud Run Deployment**
   - Push images to GCR
   - Deploy services to Cloud Run
   - Configure service-to-service auth

2. **CI/CD Pipeline**
   - GitHub Actions for builds
   - Automated testing
   - Deployment automation

3. **Monitoring**
   - Prometheus metrics
   - Centralized logging
   - Distributed tracing

### Long-term Improvements
1. **Kubernetes Migration**
   - Convert to k8s manifests
   - Helm charts
   - Scaling policies

2. **Security Hardening**
   - Secret management
   - Network policies
   - Image scanning

3. **Performance Optimization**
   - Image size reduction
   - Startup time optimization
   - Caching strategies

---

## Quick Commands Reference

### Build
```bash
docker-compose build                    # Build all services
docker-compose build tickets-agent      # Build single service
```

### Start/Stop
```bash
docker-compose up -d                    # Start all (background)
docker-compose down                     # Stop all
docker-compose down -v                  # Stop + remove volumes
```

### Monitor
```bash
docker-compose ps                       # Service status
docker-compose logs -f                  # Follow all logs
docker-compose logs -f jarvis-api       # Follow single service
docker stats                            # Resource usage
```

### Test
```bash
docker-compose --profile test run integration-tests    # Run all tests
docker-compose --profile test run integration-tests \
  pytest tests/integration/test_docker_deployment.py::test_health_checks -v
```

### Debug
```bash
docker exec -it jarvis-orchestrator-api bash    # Shell into container
docker-compose config                           # Validate compose file
docker-compose config --services                # List services
```

---

## Implementation Timeline

### Week 1: Core Development
- **Day 1-2:** Phases 1-3 (Foundation + Agent/Auth Dockerfiles)
- **Day 3:** Phase 4 (Jarvis API Service - most complex)
- **Day 4:** Phase 5 (Web UI modification)

### Week 2: Integration & Testing
- **Day 5:** Phase 6 (docker-compose.yml)
- **Day 6:** Phase 7 (Integration tests)
- **Day 7:** Phase 8 (Documentation)

### Week 3: Validation
- **Day 8:** Phase 9 (Manual testing + performance baseline)
- **Day 9:** Bug fixes and optimization
- **Day 10:** Final validation and handoff

**Total Duration:** 10 working days (~2 weeks calendar time)

---

## Progress Tracking

### Overall Progress
- [ ] Phase 1: Foundation (0/2 tasks)
- [ ] Phase 2: Agent Dockerfiles (0/3 tasks)
- [ ] Phase 3: Supporting Services (0/2 tasks)
- [ ] Phase 4: Jarvis API Service (0/3 tasks)
- [ ] Phase 5: Web UI Modification (0/1 tasks)
- [ ] Phase 6: Docker Compose (0/1 tasks)
- [ ] Phase 7: Integration Testing (0/4 tasks)
- [ ] Phase 8: Documentation (0/3 tasks)
- [ ] Phase 9: Validation (0/2 tasks)

**Total Progress: 0/21 tasks (0%)**

---

## Notes & Decisions

### Architectural Decisions
1. **Jarvis API Service:** Create new microservice instead of modifying Web UI to prevent tight coupling
2. **Multi-stage Builds:** Use for all services to optimize image size
3. **Health Check Strategy:** Service-specific endpoints with generous timeouts
4. **Network:** Single bridge network for simplicity, all services can communicate

### Implementation Decisions
1. **Token Caching:** Cache orchestrators by JWT token to avoid expensive recreation
2. **Service URLs:** Use environment variables for all inter-service communication
3. **Test Strategy:** Docker network-based integration tests (not host-based)
4. **Volume Strategy:** Only agent-registry needs persistence

---

*Last Updated: 2026-01-06*
*Status: Ready for Implementation*
