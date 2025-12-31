# Web UI Testing Guide - Jarvis

## Overview

This guide provides step-by-step instructions for testing the Jarvis Web UI. The Web UI provides a browser-based chat interface for interacting with Jarvis agents.

---

## Prerequisites

Before testing, ensure all required services are running:

### Required Services:
1. **Auth Service** (Port 9998)
2. **Registry Service** (Port 8003)
3. **Tickets Agent** (Port 8080)
4. **FinOps Agent** (Port 8081)
5. **Oxygen Agent** (Port 8082)
6. **Web UI Server** (Port 9999)

### Quick Start All Services:

```bash
# Terminal 1: Auth Service
cd auth
python auth_service.py

# Terminal 2: Registry Service
cd agent_registry_service
python registry_service.py

# Terminal 3: Tickets Agent
cd agents_phase2/tickets_agent
python start_tickets_agent.py

# Terminal 4: FinOps Agent
cd agents_phase2/finops_agent
python start_finops_agent.py

# Terminal 5: Oxygen Agent
cd agents_phase2/oxygen_agent
python start_oxygen_agent.py

# Terminal 6: Web UI Server
cd web_ui
python server_phase2.py
```

### Verify Services:

```bash
# Check all services are running
curl http://localhost:9998/health  # Auth
curl http://localhost:8003/health  # Registry
curl http://localhost:8080/.well-known/agent-card.json  # Tickets
curl http://localhost:8081/.well-known/agent-card.json  # FinOps
curl http://localhost:8082/.well-known/agent-card.json  # Oxygen
curl http://localhost:9999/health  # Web UI
```

---

## Test Scenarios

### Test 1: Login & Authentication

#### Objective
Verify that users can login with valid credentials.

#### Test Users:
- **vishal** / password123 (developer)
- **happy** / password123 (developer)
- **alex** / password123 (devops)
- **admin** / admin123 (admin)

#### Steps:
1. Open browser: `http://localhost:9999`
2. Should redirect to login page
3. Enter username: `vishal`
4. Enter password: `password123`
5. Click "Login"

#### Expected Results:
- ✅ Redirects to chat page
- ✅ Shows "vishal (developer)" in header
- ✅ Displays welcome message
- ✅ JWT token stored in localStorage
- ✅ User info stored in localStorage

#### Failure Cases:
- ❌ Invalid credentials → Shows error message
- ❌ Missing username → Form validation error
- ❌ Missing password → Form validation error

---

### Test 2: Basic Chat Functionality

#### Objective
Verify that users can send messages and receive responses.

#### Steps:
1. Login as `vishal`
2. Type message: `show my tickets`
3. Press Enter or click "Send"

#### Expected Results:
- ✅ User message appears in chat (right side, blue background)
- ✅ Send button disabled while processing
- ✅ Send button shows "Sending..."
- ✅ Agent response appears (left side, gray background)
- ✅ Response shows vishal's tickets
- ✅ Chat scrolls to bottom automatically

#### Sample Response:
```
You have 2 tickets:

1. Ticket ID: 1
   Operation: create_ai_key
   Status: pending
   Created: 2025-12-30

2. Ticket ID: 2
   Operation: laptop_approval
   Status: completed
   Created: 2025-12-29
```

---

### Test 3: User Data Isolation

#### Objective
Verify that users can only see their own data (no cross-user access).

#### Steps:
1. Login as `happy`
2. Type: `show my tickets`
3. Note the tickets shown
4. Logout
5. Login as `vishal`
6. Type: `show my tickets`
7. Compare tickets

#### Expected Results:
- ✅ Happy sees only Happy's tickets
- ✅ Vishal sees only Vishal's tickets
- ✅ No overlap in data
- ✅ Each user has separate session

#### Security Test:
1. Login as `happy`
2. Try: `show vishal's tickets`

#### Expected Results:
- ✅ Should receive error: "Access denied. You can only view your own data."
- ✅ OR should return empty results (depending on implementation)

---

### Test 4: Admin Privileges

#### Objective
Verify that admin users can access all user data.

#### Steps:
1. Login as `admin`
2. Type: `show vishal's tickets`
3. Verify response shows vishal's data

#### Expected Results:
- ✅ Admin can view vishal's tickets
- ✅ Admin can view any user's data
- ✅ Response shows correct user's information

---

### Test 5: Multi-Agent Routing

#### Objective
Verify that queries are routed to the correct agent.

#### Test Cases:

**Tickets Agent:**
```
Query: "show my tickets"
Expected: Lists user's IT tickets
Agent: TicketsAgent
```

**FinOps Agent:**
```
Query: "show AWS cost"
Expected: Shows AWS cost breakdown
Agent: FinOpsAgent
```

**Oxygen Agent:**
```
Query: "show my courses"
Expected: Lists enrolled courses
Agent: OxygenAgent
```

**Mixed Query:**
```
Query: "show my tickets and pending exams"
Expected:
  - Lists tickets (from TicketsAgent)
  - Lists pending exams (from OxygenAgent)
Agent: Both agents invoked by orchestrator
```

---

### Test 6: Session Persistence

#### Objective
Verify that conversation history persists across page reloads.

#### Steps:
1. Login as `vishal`
2. Send 3 messages:
   - "show my tickets"
   - "show my courses"
   - "show AWS cost"
3. Refresh the page (F5)
4. Check if conversation appears

#### Expected Results:
- ✅ User remains logged in
- ✅ Previous messages NOT shown (fresh session each time)
- ✅ OR previous messages shown if history loading implemented
- ✅ Can continue conversation

---

### Test 7: Logout Functionality

#### Objective
Verify that users can logout securely.

#### Steps:
1. Login as `vishal`
2. Send a message
3. Click "Logout" button

#### Expected Results:
- ✅ Redirects to login page
- ✅ JWT token removed from localStorage
- ✅ User info removed from localStorage
- ✅ Cannot access chat page without logging in again

#### Verification:
1. After logout, try to navigate to: `http://localhost:9999/chat.html`
2. Should redirect to login page

---

### Test 8: Error Handling

#### Objective
Verify that errors are handled gracefully.

#### Test Cases:

**Case 1: Service Down**
1. Stop Tickets Agent server
2. Login and send: `show my tickets`
3. Expected: Error message displayed

**Case 2: Invalid Query**
1. Send: `foobar nonsense query`
2. Expected: Graceful error or "I don't understand" response

**Case 3: Network Error**
1. Stop Web UI server mid-conversation
2. Try to send a message
3. Expected: Connection error message

---

### Test 9: Context-Aware Queries

#### Objective
Verify that user context is automatically injected.

#### Steps:
1. Login as `alex`
2. Send: `show pending exams`
3. Verify response shows Alex's exams (not asking for username)

#### Expected Results:
- ✅ Query automatically becomes "show pending exams for alex"
- ✅ No prompt asking for username
- ✅ Correct user data returned

---

### Test 10: Cross-Browser Testing

#### Objective
Verify that Web UI works across different browsers.

#### Browsers to Test:
- Chrome/Chromium
- Firefox
- Safari (macOS)
- Edge

#### Steps:
1. Open Web UI in each browser
2. Login as `vishal`
3. Send a message
4. Check display and functionality

#### Expected Results:
- ✅ Login works in all browsers
- ✅ Chat interface displays correctly
- ✅ Messages send and receive properly
- ✅ No JavaScript errors in console

---

## Browser Console Checks

Open browser DevTools (F12) and check:

### 1. Check Authentication
```javascript
// Check if token is stored
localStorage.getItem('token')  // Should return JWT token

// Check user info
JSON.parse(localStorage.getItem('user'))
// Should return: {username: "vishal", role: "developer", ...}
```

### 2. Check Network Requests
- Navigate to Network tab
- Send a message
- Verify:
  - POST to `http://localhost:9999/api/chat`
  - Status 200 OK
  - Authorization header present
  - Response contains agent's reply

### 3. Check for JavaScript Errors
- Console should be clean (no red errors)
- Warnings are acceptable

---

## Testing Checklist

### Authentication & Login
- [ ] Login with valid credentials
- [ ] Login fails with invalid credentials
- [ ] Token stored in localStorage
- [ ] User info stored in localStorage
- [ ] Auto-redirect to chat after login

### Chat Functionality
- [ ] Send message and receive response
- [ ] User messages appear on right
- [ ] Agent messages appear on left
- [ ] Chat scrolls to bottom automatically
- [ ] Send button disabled while processing
- [ ] Enter key sends message

### Security & Isolation
- [ ] Users see only their own data
- [ ] Access denied when trying to view others' data
- [ ] Admin can view all users' data
- [ ] JWT token required for chat API

### Agent Routing
- [ ] Tickets queries route to TicketsAgent
- [ ] Cost queries route to FinOpsAgent
- [ ] Course queries route to OxygenAgent
- [ ] Mixed queries invoke multiple agents

### Error Handling
- [ ] Service down → Error message
- [ ] Network error → Error message
- [ ] Invalid token → Redirect to login
- [ ] 500 errors → Graceful error message

### Logout
- [ ] Logout button works
- [ ] Token cleared from localStorage
- [ ] Redirects to login page
- [ ] Cannot access chat without login

---

## Common Issues & Solutions

### Issue 1: "Cannot connect to Jarvis"
**Cause:** Web UI server not running or wrong port
**Solution:**
```bash
cd web_ui
python server_phase2.py
```

### Issue 2: "Service unavailable"
**Cause:** Agent servers not running
**Solution:** Start all required agent servers (see Prerequisites)

### Issue 3: "Session expired"
**Cause:** JWT token expired (24 hours)
**Solution:** Logout and login again

### Issue 4: Blank page after login
**Cause:** JavaScript error or missing files
**Solution:**
- Check browser console for errors
- Verify `chat.html` exists in `web_ui/static/`

### Issue 5: CORS errors
**Cause:** CORS middleware not configured
**Solution:** Check `server_phase2.py` has CORS middleware enabled

---

## Performance Benchmarks

### Response Times:
- Login: < 500ms
- Simple query: 1-3 seconds
- Complex query (multi-agent): 3-5 seconds
- Page load: < 1 second

### Browser Requirements:
- Modern browser (Chrome 90+, Firefox 88+, Safari 14+)
- JavaScript enabled
- LocalStorage enabled
- Cookies enabled

---

## Automated Testing

For automated testing, create test scripts:

```python
# Example: test_webui.py
import requests
import time

# Test 1: Login
response = requests.post(
    "http://localhost:9998/auth/login",
    json={"username": "vishal", "password": "password123"}
)
assert response.status_code == 200
token = response.json()["access_token"]

# Test 2: Chat
response = requests.post(
    "http://localhost:9999/api/chat",
    headers={"Authorization": f"Bearer {token}"},
    json={"message": "show my tickets"}
)
assert response.status_code == 200
assert "tickets" in response.json()["response"].lower()
```

---

## Test Data Reset

To reset test data (clear all sessions):

```bash
# Backup current sessions
cp data/sessions.db data/sessions.db.backup

# Delete sessions database
rm data/sessions.db

# Restart Registry Service to recreate database
cd agent_registry_service
python registry_service.py
```

---

## Reporting Bugs

When reporting issues, include:
1. Browser and version
2. Steps to reproduce
3. Expected vs actual behavior
4. Screenshot (if applicable)
5. Browser console errors
6. Network tab screenshot

---

## Next Steps

After completing basic testing:
1. Test Phase 2 features (if implemented):
   - Token refresh
   - Markdown rendering
   - Loading animations
   - Error recovery with retry
2. Load testing with multiple concurrent users
3. Mobile browser testing
4. Accessibility testing (WCAG compliance)

---

## Success Criteria

Web UI is considered production-ready when:
- ✅ All test scenarios pass
- ✅ No JavaScript errors in console
- ✅ Responsive design works on mobile
- ✅ Security tests pass (user isolation)
- ✅ All agents respond correctly
- ✅ Error handling is graceful
- ✅ Performance meets benchmarks
