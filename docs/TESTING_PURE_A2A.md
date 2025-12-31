# Testing Guide: Pure A2A Implementation (Phase 2)

This guide walks you through testing all features of the Pure A2A implementation with JWT authentication and session persistence.

---

## Prerequisites

Before testing, ensure:
- [ ] `.env` file is configured (see [ENVIRONMENT_CONFIGURATION.md](./ENVIRONMENT_CONFIGURATION.md))
- [ ] Virtual environment is activated: `source .venv/bin/activate`
- [ ] Google API key is set in `.env`
- [ ] JWT secret is configured in `.env`

---

## Quick Test (5 minutes)

### 1. Start All Services

```bash
./scripts/start_phase2.sh
```

**Expected Output:**
```
========================================================================
✅ All Services Started Successfully!
========================================================================

Running Services:
  Authentication:
    • Auth Service:      http://localhost:9998

  Core Services:
    • Registry Service:  http://localhost:8003

  A2A Agents:
    • TicketsAgent:      http://localhost:8080
    • FinOpsAgent:       http://localhost:8081
    • OxygenAgent:       http://localhost:8082
```

**Verify Services:**
```bash
lsof -i :8003,8080,8081,8082,9998 | grep LISTEN
```

You should see 5 processes listening.

---

### 2. Start Jarvis CLI

```bash
python jarvis_agent/main_with_registry.py
```

**Expected Output:**
```
================================================================================
Jarvis AI Assistant (Registry Service Version)
================================================================================

Username: _
```

---

### 3. Login

```
Username: vishal
Password: password123
```

**Expected Output:**
```
✓ Authenticated successfully as vishal

✓ New session created: a1b2c3d4...

Jarvis is ready! Type your queries below.
Commands:
  /help    - Show help
  /history - Show conversation history
  /exit    - Exit

vishal> _
```

---

### 4. Test Single-Agent Queries

**Test 1: TicketsAgent (IT Operations)**
```
vishal> show my tickets
```

**Expected:**
- Should show only vishal's tickets (IDs: 12301, 12303)
- Response formatted with ticket details
- Status, operation type, and timestamps

**Test 2: OxygenAgent (Learning & Development)**
```
vishal> what are my pending exams
```

**Expected:**
- Shows vishal's 2 pending exams
- Includes deadlines and days remaining
- Flags urgent exams (≤7 days)

**Test 3: FinOpsAgent (Cloud Costs)**
```
vishal> what is our total cloud cost
```

**Expected:**
- Shows organization-wide costs ($36,605.50 USD)
- Breakdown by provider (AWS, GCP, Azure)
- Same data for all users (not user-specific)

---

### 5. Test Multi-Agent Query

```
vishal> show my tickets and my pending exams
```

**Expected:**
- Orchestrator routes to both TicketsAgent AND OxygenAgent
- Combined response with tickets + exams
- Both sets of data are user-specific (vishal only)

---

### 6. Test Session Persistence

**Step 1:** Exit Jarvis
```
vishal> /exit
```

**Step 2:** Start Jarvis again
```bash
python jarvis_agent/main_with_registry.py
```

**Step 3:** Login as same user
```
Username: vishal
Password: password123
```

**Expected Output:**
```
================================================================================
✓ Welcome back! Resuming session from 2025-12-31 14:30
  Session ID: a1b2c3d4...
  Messages: 6
  Last: Here are the tickets for vishal: * Ticket ID: 12301...

  Type /history to see full conversation
================================================================================
```

**Step 4:** Verify history preserved
```
vishal> /history
```

**Expected:**
- Shows all previous messages from earlier session
- Conversation continuity maintained

---

### 7. Test User-Specific Data Isolation

**Step 1:** Exit and login as different user
```
vishal> /exit
```

Start Jarvis again and login as **happy**:
```
Username: happy
Password: password123
```

**Step 2:** Query tickets
```
happy> show my tickets
```

**Expected:**
- Shows ONLY happy's ticket (ID: 12302)
- Does NOT show vishal's tickets
- Different data than vishal saw

**Step 3:** Query courses
```
happy> what are my courses
```

**Expected:**
- Shows happy's courses (Data Science, SQL Mastery)
- Different from vishal's courses
- User-specific data isolation working

---

## Comprehensive Test Suite (20 minutes)

### Test 1: Authentication

#### 1.1 Valid Credentials
```bash
curl -X POST http://localhost:9998/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"vishal","password":"password123"}'
```

**Expected:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "user_id": "user_001",
    "username": "vishal",
    "role": "developer"
  }
}
```

#### 1.2 Invalid Credentials
```bash
curl -X POST http://localhost:9998/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"vishal","password":"wrongpass"}'
```

**Expected:** HTTP 401 with error message

---

### Test 2: A2A Agent Communication

#### 2.1 Test Agent Cards

**TicketsAgent:**
```bash
curl http://localhost:8080/.well-known/agent-card.json | jq .
```

**Expected:**
```json
{
  "name": "TicketsAgent",
  "description": "IT operations ticket management agent",
  "protocolVersion": "0.3.0",
  "skills": [...]
}
```

**Repeat for other agents:**
```bash
curl http://localhost:8081/.well-known/agent-card.json | jq .name  # FinOpsAgent
curl http://localhost:8082/.well-known/agent-card.json | jq .name  # OxygenAgent
```

#### 2.2 Direct A2A Invocation (Advanced)

You can test A2A communication directly using curl, but it's complex. The CLI does this automatically.

---

### Test 3: Session Management

#### 3.1 Check Session Created

After logging in and making a query, check session exists:
```bash
# Get your session ID from CLI output (shown as "Session: <id>")
# Then query registry:
curl http://localhost:8003/sessions/<your-session-id> | jq .
```

**Expected:**
```json
{
  "session_id": "a1b2c3d4-...",
  "user_id": "vishal",
  "status": "active",
  "conversation_history": [...],
  "agents_invoked": [...]
}
```

#### 3.2 Check Active Session Lookup

```bash
curl http://localhost:8003/sessions/user/vishal/active | jq .
```

**Expected:**
- Returns most recent active session for vishal
- Same session ID as current session

---

### Test 4: Query Routing

Test that queries route to correct agents:

| Query | Expected Agent(s) | How to Verify |
|-------|-------------------|---------------|
| "show my tickets" | TicketsAgent only | Check logs/TicketsAgent.log |
| "what are my courses" | OxygenAgent only | Check logs/OxygenAgent.log |
| "total cloud cost" | FinOpsAgent only | Check logs/FinOpsAgent.log |
| "show tickets and exams" | TicketsAgent + OxygenAgent | Both log files updated |

**Check logs in real-time:**
```bash
# Terminal 1: Watch TicketsAgent
tail -f logs/TicketsAgent.log

# Terminal 2: Watch OxygenAgent
tail -f logs/OxygenAgent.log

# Terminal 3: Run Jarvis CLI
python jarvis_agent/main_with_registry.py
```

---

### Test 5: User Context Injection

Test that "my" gets replaced with username:

**Query:** `"show my tickets"`

**What happens:**
1. User query: `"show my tickets"`
2. Context injection: `"show vishal's tickets"` (username injected)
3. Agent receives: `"show vishal's tickets"` (explicit)
4. Agent response: Only vishal's data returned

**Verify in logs:**
```bash
grep "show vishal" logs/TicketsAgent.log
```

Should see the injected query with username.

---

### Test 6: Session Expiration

Sessions expire after 24 hours of inactivity.

**To test (simulated):**
1. Login and create session
2. Note the session ID
3. Wait 24+ hours OR manually update session in database
4. Try to resume session
5. Should create new session instead

**Quick test (for development):**
Edit `agent_registry_service/api/session_routes.py` line 280:
```python
# Change from 24 hours to 1 minute for testing
if now - updated > timedelta(minutes=1):  # Was: hours=24
```

Then test session expiration after 1 minute.

---

## Test Scenarios by User

### Test User: vishal

**Data:**
- Tickets: 2 (IDs: 12301, 12303)
- Courses: Python Advanced, Cloud Architecture, Machine Learning
- Completed: Python Basics
- Exams: 2 pending (Python Advanced Final, Cloud Arch Cert)

**Test Queries:**
```
show my tickets
what are my courses
what are my pending exams
show my learning progress
```

---

### Test User: happy

**Data:**
- Tickets: 1 (ID: 12302)
- Courses: Data Science, SQL Mastery
- Completed: Excel Basics, Statistics 101
- Exams: 1 pending (Data Science Midterm)

**Test Queries:**
```
show my tickets
what courses am I taking
when is my next exam
show my completed courses
```

---

### Test User: alex

**Data:**
- Tickets: 0
- Courses: DevOps Fundamentals, Kubernetes
- Completed: None
- Exams: 1 pending (DevOps Quiz)

**Test Queries:**
```
show my tickets          # Should say "no tickets"
what courses do I have
show my exam schedule
```

---

## Advanced Testing

### Test 1: Concurrent Users

**Terminal 1:**
```bash
python jarvis_agent/main_with_registry.py
# Login as: vishal
vishal> show my tickets
```

**Terminal 2:**
```bash
python jarvis_agent/main_with_registry.py
# Login as: happy
happy> show my tickets
```

**Expected:**
- Each user sees ONLY their own tickets
- Sessions are independent
- No data leakage between users

---

### Test 2: Multi-Agent Query Decomposition

**Query:**
```
vishal> show my tickets, courses, and our cloud costs
```

**Expected:**
- Orchestrator routes to all 3 agents
- TicketsAgent: Returns vishal's tickets
- OxygenAgent: Returns vishal's courses
- FinOpsAgent: Returns org-wide costs
- Response combines all three

**Verify in logs:**
```bash
grep "Invoking" logs/jarvis_agent.log
```

Should show 3 agent invocations.

---

### Test 3: Session History Across Agents

Make queries to different agents, then check history:

```
vishal> show my tickets
vishal> what are my courses
vishal> show cloud costs
vishal> /history
```

**Expected:**
- History shows all 3 queries + responses
- Conversation flow preserved
- Agent names visible in history

---

## Troubleshooting

### Issue: "Authentication failed"

**Cause:** Wrong username/password

**Solution:**
- Use test users: vishal, happy, alex
- Password for all: password123

---

### Issue: "No active session found"

**Cause:** Session expired (>24 hours old)

**Solution:**
- This is expected behavior
- New session will be created automatically
- Previous conversation history is lost (by design)

---

### Issue: "Service not available"

**Cause:** One or more services not running

**Solution:**
```bash
# Check which services are down
lsof -i :8003,8080,8081,8082,9998 | grep LISTEN

# Restart all services
./scripts/stop_all_services.sh
./scripts/start_phase2.sh
```

---

### Issue: Agent returns wrong user's data

**Cause:** User context not being injected

**Solution:**
- Check `jarvis_agent/main_with_registry.py` line 261-262
- Verify `_inject_user_context()` is being called
- Check logs for injected query

**Debug:**
```bash
grep "Invoking" logs/jarvis_agent.log
# Should show: "Invoking TicketsAgent with query: 'show vishal's tickets'"
# NOT: "show my tickets"
```

---

## Verification Checklist

After testing, verify:

- [ ] All 5 services start successfully
- [ ] Authentication works for all 3 test users
- [ ] Each user sees ONLY their own data
- [ ] Multi-agent queries work (routes to multiple agents)
- [ ] Session persists across login/logout
- [ ] Conversation history is preserved
- [ ] "Welcome back!" message shows on re-login
- [ ] All agent cards are accessible
- [ ] Logs show agent invocations
- [ ] No errors in service logs

---

## Test Results Template

Use this template to document your test results:

```
# Pure A2A Testing Results
Date: ___________
Tester: ___________

## Services Started
- [ ] Auth Service (9998)
- [ ] Registry Service (8003)
- [ ] TicketsAgent (8080)
- [ ] FinOpsAgent (8081)
- [ ] OxygenAgent (8082)

## Authentication
- [ ] Login as vishal: _____ (Pass/Fail)
- [ ] Login as happy: _____ (Pass/Fail)
- [ ] Login as alex: _____ (Pass/Fail)
- [ ] Invalid password rejected: _____ (Pass/Fail)

## Single-Agent Queries
- [ ] Show tickets (TicketsAgent): _____ (Pass/Fail)
- [ ] Show courses (OxygenAgent): _____ (Pass/Fail)
- [ ] Show costs (FinOpsAgent): _____ (Pass/Fail)

## Multi-Agent Queries
- [ ] Combined query routes to multiple agents: _____ (Pass/Fail)

## User Data Isolation
- [ ] vishal sees only vishal's data: _____ (Pass/Fail)
- [ ] happy sees only happy's data: _____ (Pass/Fail)

## Session Persistence
- [ ] Session ID same after re-login: _____ (Pass/Fail)
- [ ] Conversation history preserved: _____ (Pass/Fail)
- [ ] "Welcome back!" message shown: _____ (Pass/Fail)

## Issues Found
1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

## Overall Result
[ ] All tests passed
[ ] Some issues found (see above)
[ ] Major issues - needs fixing
```

---

## Next Steps

After successful testing:

1. **Document any issues** found during testing
2. **Performance testing** - Test with larger datasets
3. **Security testing** - Test JWT expiration, token tampering
4. **Load testing** - Test concurrent users
5. **Move to Phase 3** - Implement long-term memory

---

## Getting Help

If tests fail:
1. Check service logs in `logs/` directory
2. Review [PHASE_2_PURE_A2A_PLAN.md](./PHASE_2_PURE_A2A_PLAN.md)
3. Check [ENVIRONMENT_CONFIGURATION.md](./ENVIRONMENT_CONFIGURATION.md)
4. Verify .env file is configured correctly

---

## Quick Reference

**Start Services:**
```bash
./scripts/start_phase2.sh
```

**Stop Services:**
```bash
./scripts/stop_all_services.sh
```

**Start CLI:**
```bash
python jarvis_agent/main_with_registry.py
```

**Test Users:**
- vishal / password123
- happy / password123
- alex / password123

**Service URLs:**
- Auth: http://localhost:9998
- Registry: http://localhost:8003
- Tickets: http://localhost:8080
- FinOps: http://localhost:8081
- Oxygen: http://localhost:8082
