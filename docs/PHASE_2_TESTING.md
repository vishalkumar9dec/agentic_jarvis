# Phase 2 Testing Guide

## Automated Testing

### End-to-End Test Suite

Run the comprehensive automated test suite:

```bash
.venv/bin/python tests/test_phase2_e2e.py
```

**What it tests:**
- Auth Service health and login endpoints
- JWT token generation and validation
- Authenticated access to Tickets server
- User-specific ticket operations
- Unauthenticated request rejection
- Invalid token rejection
- FinOps and Oxygen agent health
- Web UI accessibility
- All three demo users (vishal, alex, sarah)

**Expected Result:** All 16 tests should pass

## Manual Testing

### Prerequisites

1. **Start all Phase 2 services:**
   ```bash
   ./scripts/restart_all_phase2.sh
   ```

2. **Verify services are running:**
   ```bash
   ./scripts/check_phase2_services.sh
   ```

### Test 1: Web UI Authentication Flow

1. **Open login page:**
   ```
   http://localhost:9999/login.html
   ```

2. **Test login with each demo user:**
   - Username: `vishal` / Password: `password123`
   - Username: `alex` / Password: `password123`
   - Username: `sarah` / Password: `password123`

3. **Expected behavior:**
   - Login page displays available demo accounts
   - Successful login redirects to chat page
   - Chat page displays username in header
   - Logout button is visible

4. **Test authentication:**
   - Try accessing chat page without login: `http://localhost:9999/chat.html`
   - Should redirect to login page

5. **Test chat functionality:**
   - Send message: "Show my tickets"
   - Should return user-specific tickets for logged-in user
   - Send message: "Create a ticket for VPN access"
   - Should create ticket under current user's name

6. **Test logout:**
   - Click logout button
   - Should redirect to login page
   - Token should be cleared from localStorage
   - Trying to access chat should redirect to login

### Test 2: CLI Authentication Flow

1. **Start CLI:**
   ```bash
   python main.py
   ```

2. **Login prompt:**
   - CLI should display available demo accounts
   - Enter username: `vishal`
   - Enter password: `password123`
   - Should show "Welcome, vishal!" message

3. **Test user-specific queries:**
   ```
   > Show my tickets
   ```
   - Should return tickets created by vishal
   - Vishal has 2 pending tickets in the mock database

4. **Test ticket creation:**
   ```
   > Create a ticket for AI API key access
   ```
   - Should create ticket under vishal's name
   - Confirm ticket creation response

5. **Test cross-user isolation:**
   - Login as `alex` in a new terminal
   - Query "Show my tickets"
   - Should return 0 tickets (alex has no tickets initially)
   - Should NOT see vishal's tickets

6. **Test learning queries (Oxygen agent):**
   ```
   > What courses am I enrolled in?
   ```
   - Should return user-specific course enrollments
   - Each user has different courses

7. **Test invalid login:**
   - Start CLI
   - Try username: `invalid` / password: `wrong`
   - Should reject after 3 attempts
   - Should exit gracefully

### Test 3: API Endpoint Testing

#### Test Auth Service

1. **Health check:**
   ```bash
   curl http://localhost:9998/health
   ```

2. **Demo users:**
   ```bash
   curl http://localhost:9998/auth/demo-users
   ```

3. **Login:**
   ```bash
   curl -X POST http://localhost:9998/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "vishal", "password": "password123"}'
   ```
   - Save the token from response

4. **Get user info:**
   ```bash
   curl http://localhost:9998/auth/user/vishal
   ```

#### Test Tickets Server with Authentication

1. **Get my tickets (authenticated):**
   ```bash
   TOKEN="your_token_here"
   curl -X POST http://localhost:5001/api/tool/get_my_tickets/invoke \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{}'
   ```

2. **Get my tickets (unauthenticated - should fail):**
   ```bash
   curl -X POST http://localhost:5001/api/tool/get_my_tickets/invoke \
     -H "Content-Type: application/json" \
     -d '{}'
   ```
   - Should return 401 Unauthorized

3. **Create my ticket (authenticated):**
   ```bash
   curl -X POST http://localhost:5001/api/tool/create_my_ticket/invoke \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"operation": "create_gitlab_account"}'
   ```

#### Test FinOps Server

```bash
curl http://localhost:5002/health
curl http://localhost:5002/api/toolset/finops
```

#### Test Oxygen Agent

```bash
curl http://localhost:8002/.well-known/agent-card.json
```

### Test 4: Service Logs

Check logs for any errors:

```bash
# Auth service
tail -f logs/auth_server.log

# Tickets server
tail -f logs/tickets_server.log

# FinOps server
tail -f logs/finops_server.log

# Oxygen agent
tail -f logs/oxygen_agent.log

# Web UI
tail -f logs/web_ui.log
```

## Security Testing

### Test 1: Token Validation

1. **Invalid token format:**
   ```bash
   curl -X POST http://localhost:5001/api/tool/get_my_tickets/invoke \
     -H "Authorization: Bearer invalid_token" \
     -H "Content-Type: application/json" \
     -d '{}'
   ```
   - Should return 401

2. **Missing token:**
   ```bash
   curl -X POST http://localhost:5001/api/tool/get_my_tickets/invoke \
     -H "Content-Type: application/json" \
     -d '{}'
   ```
   - Should return 401

3. **Malformed Authorization header:**
   ```bash
   curl -X POST http://localhost:5001/api/tool/get_my_tickets/invoke \
     -H "Authorization: invalid_format" \
     -H "Content-Type: application/json" \
     -d '{}'
   ```
   - Should return 401

### Test 2: User Isolation

1. Login as `vishal` and get token
2. Create tickets for vishal
3. Login as `alex` and get different token
4. Verify alex cannot see vishal's tickets
5. Verify alex can only create tickets under his own name

### Test 3: CORS

Test from browser console (open http://localhost:9999):

```javascript
fetch('http://localhost:9998/auth/demo-users')
  .then(r => r.json())
  .then(console.log)
```

Should work due to CORS middleware.

## Performance Testing

### Token Generation Performance

```bash
# Run multiple login requests
for i in {1..10}; do
  curl -X POST http://localhost:9998/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "vishal", "password": "password123"}' &
done
wait
```

### Concurrent Requests

```bash
# Test concurrent authenticated requests
TOKEN="your_token_here"
for i in {1..10}; do
  curl -X POST http://localhost:5001/api/tool/get_my_tickets/invoke \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{}' &
done
wait
```

## Troubleshooting

### Issue: Services not starting

**Check:**
```bash
./scripts/check_phase2_services.sh
```

**Fix:**
```bash
./scripts/restart_all_phase2.sh
```

### Issue: Login fails

**Check:**
- Auth service is running: `curl http://localhost:9998/health`
- Demo users endpoint: `curl http://localhost:9998/auth/demo-users`
- Logs: `tail -f logs/auth_server.log`

### Issue: Token not working

**Check:**
- Token is not expired (24 hour default)
- Token is properly formatted in Authorization header
- JWT_SECRET_KEY is consistent across services

### Issue: User-specific tools return empty data

**Check:**
- Username in JWT token matches database entries
- Case sensitivity: usernames are case-insensitive in mock DB
- User has data in mock database

## Test Results

After completing all tests above, you should see:

✓ Auth service healthy and responsive
✓ JWT tokens generated and validated correctly
✓ Authenticated requests succeed
✓ Unauthenticated requests rejected
✓ User isolation working correctly
✓ Web UI login/logout flow working
✓ CLI authentication working
✓ All three demo users can login
✓ User-specific tools return correct data
✓ All services running and logging properly

## Next Steps

Once Phase 2 testing is complete:

1. **Phase 3: Memory & Session Persistence**
   - Database-backed session storage
   - Long-term memory with VertexAI
   - Conversation history persistence

2. **Phase 4: OAuth 2.0 Integration**
   - Google/Azure AD SSO
   - Enterprise identity providers
   - Integration connectors

## References

- **Phase 2 Plan:** `PHASE_2_PLAN.md`
- **Phase 2 Summary:** `PHASE_2_SUMMARY.md`
- **Authentication Flow:** `AUTHENTICATION_FLOW.md`
- **Environment Config:** `ENVIRONMENT.md`
- **Automated Tests:** `tests/test_phase2_e2e.py`
