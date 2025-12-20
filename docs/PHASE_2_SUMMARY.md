# Phase 2: JWT Authentication - Quick Summary

## What Phase 2 Adds

### 🔐 Authentication System
- **Auth Service** (port 9998) - Handles login and JWT token generation
- **JWT Tokens** - 24-hour expiration, secure user sessions
- **User Isolation** - Each user sees only their own data

### 🌐 Dual Web Interface

**1. Custom Web Chat** - http://localhost:9999/
- Beautiful login page
- Real-time chat interface
- User authentication REQUIRED
- Shows username and role
- Logout functionality
- **For end users** - production-ready

**2. ADK Dev UI** - http://localhost:9999/dev-ui
- Google's built-in development interface
- NO authentication required
- **For developers** - quick testing and debugging

### 💻 Three Ways to Use Jarvis

| Interface | URL | Auth Required | Purpose |
|-----------|-----|---------------|---------|
| Custom Web | http://localhost:9999/ | ✅ Yes | Production users |
| CLI | `python main.py` | ✅ Yes | Terminal users |
| ADK Dev UI | http://localhost:9999/dev-ui | ❌ No | Developers only |

## Architecture

```
Port 9999 (Custom Web Server):
├─ /              → Login page (public)
├─ /chat          → Chat interface (requires JWT)
├─ /login         → Login API endpoint
├─ /api/chat      → Chat API (requires JWT)
├─ /dev-ui        → ADK Dev UI (NO AUTH - dev only)
└─ /docs          → API documentation (public)

Port 9998 (Auth Service):
└─ /auth/login    → Authentication endpoint
```

## Implementation Tasks (10 Tasks)

### Core Infrastructure (Tasks 18-19)
- Task 18: JWT utilities & user service
- Task 19: Add auth to toolbox servers

### Agent Updates (Tasks 20-21)
- Task 20: Update Oxygen with JWT
- Task 21: Update root orchestrator

### User Interfaces (Tasks 22-24)
- Task 22: Auth service endpoints
- Task 23: Update CLI with login
- Task 24: **Create custom web chat interface** ⭐

### Deployment (Tasks 25-27)
- Task 25: Environment config
- Task 26: Startup scripts
- Task 27: Testing

## Key Features

### Custom Web Interface

**Login Page:**
```
┌─────────────────────────────┐
│      🤖 Jarvis              │
│  Your Intelligent Assistant │
│                             │
│  Username: [________]       │
│  Password: [________]       │
│                             │
│      [Login Button]         │
│                             │
│  Demo Accounts:             │
│  - vishal / password123     │
│  - alex / password123       │
│  - sarah / password123      │
└─────────────────────────────┘
```

**Chat Interface:**
```
┌──────────────────────────────────────┐
│ 🤖 Jarvis    vishal (developer) [Logout] │
├──────────────────────────────────────┤
│  Welcome! I can help you with:       │
│  • IT Tickets Management             │
│  • Cloud Cost Analytics              │
│  • Learning & Development            │
├──────────────────────────────────────┤
│  👤 You: What are my tickets?        │
│  🤖 Jarvis: You have 2 tickets...    │
├──────────────────────────────────────┤
│  [Type your message...] [Send]       │
└──────────────────────────────────────┘
```

### Data Isolation

**Before Phase 2:**
```python
# Anyone can see all tickets
curl http://localhost:5001/api/tool/get-all-tickets/invoke
# Returns: ALL tickets (vishal's, alex's, sarah's)
```

**After Phase 2:**
```python
# Must login first
curl -X POST http://localhost:9998/auth/login \
  -d '{"username": "vishal", "password": "password123"}'
# Returns: {"token": "eyJhbGc...", "user": {...}}

# Use token to access data
curl http://localhost:5001/api/tool/get-my-tickets/invoke \
  -H "Authorization: Bearer eyJhbGc..."
# Returns: ONLY vishal's tickets
```

## Default Test Users

| Username | Password | Role | Data |
|----------|----------|------|------|
| vishal | password123 | developer | 2 tickets, AWS/Terraform courses, 1 exam |
| alex | password123 | devops | 2 tickets, Kubernetes courses, 2 exams |
| sarah | password123 | data_scientist | 1 ticket, ML/Data Science courses |

## Starting Services (Phase 2)

```bash
# Start all services (including auth + custom web)
./scripts/restart_all.sh

# Check health
./scripts/check_services.sh

# Expected output:
✓ Service running on port 9998  (Auth)
✓ Service running on port 5001  (Tickets)
✓ Service running on port 5002  (FinOps)
✓ Service running on port 8002  (Oxygen)
✓ Service running on port 9999  (Custom Web)
```

## User Experience Flow

### Custom Web Interface

1. **User opens** http://localhost:9999/
2. **Sees login page** with username/password fields
3. **Enters credentials** (e.g., vishal / password123)
4. **Server validates** via auth service (port 9998)
5. **JWT token generated** and stored in browser
6. **Redirected to chat** interface at /chat
7. **User chats** with Jarvis - all requests include JWT
8. **Jarvis filters data** based on authenticated user
9. **User clicks logout** - token removed, back to login

### CLI Interface

1. **User runs** `python main.py`
2. **Prompted for login** (username/password)
3. **Authenticated** - JWT token created
4. **Chat begins** - all queries user-specific
5. **User types "exit"** - session ends

### Developer Mode (ADK Dev UI)

1. **Developer opens** http://localhost:9999/dev-ui
2. **No login required** - immediate access
3. **Full access** to all agents and data
4. **For debugging only** - not for production

## File Structure (New in Phase 2)

```
agentic_jarvis/
├── auth/                          # NEW
│   ├── __init__.py
│   ├── jwt_utils.py              # JWT token creation/validation
│   ├── user_service.py           # User authentication
│   └── auth_server.py            # Auth service (port 9998)
│
├── web_ui/                        # NEW
│   ├── __init__.py
│   ├── server.py                 # Custom web server
│   └── static/
│       ├── login.html            # Login page
│       ├── chat.html             # Chat interface
│       ├── login.js              # Login logic
│       ├── chat.js               # Chat logic
│       └── styles.css            # Styling
│
├── scripts/
│   ├── start_auth_service.sh     # NEW
│   ├── start_custom_web.sh       # NEW
│   └── restart_all.sh            # UPDATED
│
└── .env                           # UPDATED
    └── JWT_SECRET_KEY=...        # NEW variable
```

## Success Criteria

Phase 2 is complete when:
- [ ] All 10 tasks implemented (Tasks 18-27)
- [ ] Custom web interface working with login
- [ ] CLI interface requires authentication
- [ ] ADK Dev UI accessible without auth
- [ ] User data properly isolated
- [ ] All authentication tests passing
- [ ] Documentation updated

## Next Steps After Phase 2

**Phase 3: Memory & Context Management**
- Session persistence across conversations
- Long-term memory with Vector DB
- Proactive notifications (exam deadlines, etc.)
- Context-aware recommendations
- Chat history stored per user

---

## Quick Reference

### Start Services
```bash
./scripts/restart_all.sh
```

### Access Points
- **Login**: http://localhost:9999/
- **Chat**: http://localhost:9999/chat (after login)
- **Dev UI**: http://localhost:9999/dev-ui (no auth)
- **API Docs**: http://localhost:9999/docs
- **CLI**: `python main.py`

### Test Credentials
```
vishal / password123
alex / password123
sarah / password123
```

### Ports
- 9998: Auth Service
- 5001: Tickets Toolbox
- 5002: FinOps Toolbox
- 8002: Oxygen A2A Agent
- 9999: Custom Web UI + ADK Dev UI

---

**Ready to implement?** See **PHASE_2_PLAN.md** for detailed task-by-task implementation guide.
