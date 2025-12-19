# Phase 2: JWT Authentication - Implementation Plan

## Overview

Phase 2 adds JWT (JSON Web Token) authentication to Agentic Jarvis, enabling:
- **User-specific data access**: Each user sees only their own tickets, courses, and exams
- **Secure API endpoints**: All toolbox servers require valid JWT tokens
- **Token propagation**: Authentication passes through the entire agent chain (Root → Sub-agents → A2A agents)
- **Multi-user support**: Different users can interact with Jarvis simultaneously

## Phase 2 vs Phase 3: Clear Scope Definition

### ⚡ Phase 2: Authentication & Basic Sessions (Current - Simple & Functional)

**Goal:** Showcase login/logout and basic session management

**What's Included:**
- ✅ User login/logout functionality
- ✅ JWT token-based authentication
- ✅ Basic in-memory sessions (lost on logout)
- ✅ User-specific data filtering
- ✅ **Simple web interface** (minimal styling, focus on functionality)

**What's NOT Included:**
- ❌ Conversation history storage
- ❌ Persistent sessions across logins
- ❌ "Welcome back, continue where you left off"
- ❌ Chat history or memory persistence

**User Flow:**
```
Login → Chat → Logout → Session cleared
Next login → Fresh start, no history
```

### 🚀 Phase 3: Memory & Persistent Sessions (Future - Production Ready)

**Goal:** Add conversation continuity and long-term memory

**What Will Be Added:**
- ✅ Database-backed session storage
- ✅ Conversation history saved per user
- ✅ **"Welcome back! Last time you asked about X. Continue?"**
- ✅ Long-term memory with Vector DB
- ✅ Proactive notifications (upcoming exams, pending tickets)
- ✅ Context-aware responses

**User Flow:**
```
Login → "Welcome back! Continue from 'Show my AWS costs'?"
      → Full chat history displayed
      → Context preserved across sessions
Logout → Everything saved to database
```

**Key Difference:**
- **Phase 2** = Temporary sessions, simple UI, demonstrate auth flow
- **Phase 3** = Persistent memory, conversation history, production UX

## Current State (Phase 1)

✅ **Completed:**
- Multi-agent orchestration working (Tickets, FinOps, Oxygen)
- Toolbox servers operational (ports 5001, 5002)
- A2A communication functional (port 8002)
- Web UI and CLI interfaces available
- Mock data accessible without authentication

❌ **Limitations:**
- No user authentication - anyone can access all data
- No user-specific filtering - all queries return all data
- No secure token passing between agents
- Cannot distinguish between different users

## Phase 2 Architecture

```
┌─────────────────────────────────────────────────┐
│              User Login                         │
│         (username + password)                   │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  Auth Service   │
         │  - Validate     │
         │  - Generate JWT │
         └────────┬────────┘
                  │
                  ▼ (JWT Token)
         ┌─────────────────┐
         │   Web UI / CLI  │
         │  (sends token)  │
         └────────┬────────┘
                  │
                  ▼ (Authorization: Bearer <token>)
         ┌─────────────────┐
         │ Jarvis Root     │
         │ - Verify JWT    │
         │ - Extract user  │
         └────────┬────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
   ┌────▼─────┐      ┌─────▼────┐      ┌─────────┐
   │ Tickets  │      │ FinOps   │      │ Oxygen  │
   │ (+ JWT)  │      │ (+ JWT)  │      │ (+ JWT) │
   └──────────┘      └──────────┘      └────┬────┘
        │                  │                 │
   Filter by user    Filter by user    A2A + JWT
```

## Implementation Tasks

### Task 18: JWT Authentication Infrastructure

**Status:** Pending

**Description:**
Create core JWT authentication utilities and user management.

**Files to Create:**

**1. `auth/jwt_utils.py`** - JWT token generation and validation
```python
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def create_jwt_token(username: str, user_id: str) -> str:
    """Create JWT token for authenticated user."""
    payload = {
        "username": username,
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[Dict]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def extract_user_from_token(token: str) -> Optional[str]:
    """Extract username from JWT token."""
    payload = verify_jwt_token(token)
    return payload.get("username") if payload else None
```

**2. `auth/user_service.py`** - Simple user authentication
```python
from typing import Optional, Dict
import hashlib

# Mock user database (replace with real DB in production)
USERS_DB = {
    "vishal": {
        "user_id": "user_001",
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "email": "vishal@company.com",
        "role": "developer"
    },
    "alex": {
        "user_id": "user_002",
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "email": "alex@company.com",
        "role": "devops"
    },
    "sarah": {
        "user_id": "user_003",
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "email": "sarah@company.com",
        "role": "data_scientist"
    }
}

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user with username and password."""
    user = USERS_DB.get(username)
    if not user:
        return None

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != user["password_hash"]:
        return None

    return {
        "username": username,
        "user_id": user["user_id"],
        "email": user["email"],
        "role": user["role"]
    }

def get_user_info(username: str) -> Optional[Dict]:
    """Get user information."""
    user = USERS_DB.get(username)
    if not user:
        return None

    return {
        "username": username,
        "user_id": user["user_id"],
        "email": user["email"],
        "role": user["role"]
    }
```

**Acceptance Criteria:**
- [ ] JWT utilities created and tested
- [ ] User service with mock user database
- [ ] Token generation and validation working
- [ ] User authentication working (username/password)

---

### Task 19: Add Authentication to Toolbox Servers

**Status:** Pending

**Description:**
Update Tickets and FinOps toolbox servers to require JWT authentication and filter data by user.

**Changes Required:**

**1. Update `toolbox_servers/tickets_server/server.py`**

Add JWT middleware:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import sys
sys.path.insert(0, '../..')
from auth.jwt_utils import verify_jwt_token

security = HTTPBearer()

def verify_token(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """Verify JWT token and return username."""
    token = credentials.credentials
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return payload.get("username")
```

Update functions to filter by user:
```python
def get_user_tickets(username: str) -> List[Dict[str, Any]]:
    """Get all tickets for the authenticated user."""
    # Now filters by the authenticated user, not just any username
    user_tickets = [t for t in TICKETS_DB if t["user"] == username]
    return user_tickets
```

Add authenticated endpoints:
```python
@app.post("/api/tool/get-my-tickets/invoke")
async def get_my_tickets(username: str = Depends(verify_token)):
    """Get tickets for authenticated user."""
    result = get_user_tickets(username)
    return {"result": result}
```

**2. Update Sample Data**

Expand `TICKETS_DB` with user-specific data:
```python
TICKETS_DB = [
    # Vishal's tickets
    {"id": 12301, "operation": "create_ai_key", "user": "vishal", "status": "pending", "created_at": "2025-01-10T10:00:00Z"},
    {"id": 12303, "operation": "update_budget", "user": "vishal", "status": "in_progress", "created_at": "2025-01-11T09:15:00Z"},

    # Alex's tickets
    {"id": 12302, "operation": "create_gitlab_account", "user": "alex", "status": "completed", "created_at": "2025-01-09T14:30:00Z"},
    {"id": 12304, "operation": "vpn_access", "user": "alex", "status": "pending", "created_at": "2025-01-12T08:00:00Z"},

    # Sarah's tickets
    {"id": 12305, "operation": "gpu_allocation", "user": "sarah", "status": "approved", "created_at": "2025-01-13T10:30:00Z"},
]
```

**Acceptance Criteria:**
- [ ] JWT verification middleware added to both servers
- [ ] All endpoints require valid JWT token
- [ ] Data filtered by authenticated user
- [ ] Unauthorized requests return 401
- [ ] Sample data expanded for multiple users

---

### Task 20: Update Oxygen Agent with JWT Authentication

**Status:** Pending

**Description:**
Modify Oxygen A2A agent to accept and validate JWT tokens for user-specific learning data.

**Changes Required:**

**1. Update `remote_agent/oxygen_agent/tools.py`**

The tools already accept username parameter, but now we'll ensure they only return data for the authenticated user:

```python
def get_user_courses(username: str) -> Dict[str, Any]:
    """Get all courses for the authenticated user."""
    user_data = LEARNING_DB.get(username)

    if not user_data:
        return {
            "success": False,
            "error": f"No learning data found for user: {username}"
        }

    return {
        "success": True,
        "username": username,
        "courses_enrolled": user_data["courses_enrolled"],
        "completed_courses": user_data["completed_courses"],
        "total_courses": len(user_data["courses_enrolled"]) + len(user_data["completed_courses"])
    }
```

**2. Update `remote_agent/oxygen_agent/agent.py`**

Add JWT verification to A2A agent:
```python
from fastapi import Request, HTTPException
import sys
sys.path.insert(0, '../..')
from auth.jwt_utils import verify_jwt_token

# Add middleware to verify tokens on incoming A2A requests
async def verify_a2a_token(request: Request):
    """Verify JWT token in A2A requests."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header.replace("Bearer ", "")
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload.get("username")
```

**Acceptance Criteria:**
- [ ] Oxygen agent validates JWT tokens
- [ ] A2A requests include authentication
- [ ] Learning data filtered by authenticated user
- [ ] Token verification middleware working

---

### Task 21: Update Root Orchestrator for Token Propagation

**Status:** Pending

**Description:**
Modify Jarvis root orchestrator to accept JWT tokens and propagate them to sub-agents.

**Changes Required:**

**1. Update `jarvis_agent/agent.py`**

The root agent doesn't need to change much - the ADK Runner handles token propagation automatically. However, we need to ensure the session is associated with a user:

```python
# The Runner will handle token verification and user context
# We just need to ensure our agent instructions are updated

root_agent = LlmAgent(
    name="JarvisOrchestrator",
    model=GEMINI_2_5_FLASH,
    description="Jarvis - Your intelligent IT operations and learning assistant",
    instruction="""You are Jarvis, an intelligent assistant that helps users with their personalized data:

**IT Operations:**
- **Tickets**: Use TicketsAgent to view, search, and create IT tickets FOR THE AUTHENTICATED USER
- **FinOps**: Use FinOpsAgent to get cloud cost information and financial analytics

**Learning & Development:**
- **Courses & Exams**: Use OxygenAgent to check the authenticated user's enrolled courses, pending exams, and learning progress

IMPORTANT: All data access is user-specific. Only show data for the currently authenticated user.

Route user requests to the appropriate sub-agent based on the query.
Always provide helpful, clear responses and coordinate between agents when needed.""",
    sub_agents=[tickets_agent, finops_agent, oxygen_agent],
)
```

**Acceptance Criteria:**
- [ ] Root agent instructions updated for user-specific context
- [ ] Token propagation working through agent chain
- [ ] User context maintained across sub-agent calls

---

### Task 22: Add Authentication Endpoints

**Status:** Pending

**Description:**
Create authentication endpoints for login and token management.

**File:** `auth/auth_server.py`

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from auth.jwt_utils import create_jwt_token
from auth.user_service import authenticate_user, get_user_info

app = FastAPI(title="Jarvis Auth Service")

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_jwt_token(user["username"], user["user_id"])

    return {
        "access_token": token,
        "token_type": "Bearer",
        "user_info": {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@app.get("/auth/verify")
async def verify_token(token: str):
    """Verify if token is valid."""
    from auth.jwt_utils import verify_jwt_token
    payload = verify_jwt_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"valid": True, "username": payload.get("username")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9998)
```

**Acceptance Criteria:**
- [ ] Login endpoint created
- [ ] Token verification endpoint working
- [ ] Auth service runs on port 9998
- [ ] Returns JWT token on successful login

---

### Task 23: Update CLI with Authentication

**Status:** Pending

**Description:**
Modify main.py CLI to support user login and token-based requests.

**Changes Required:**

```python
#!/usr/bin/env python3
"""
Agentic Jarvis - CLI Interface with Authentication
"""

import os
import getpass
from dotenv import load_dotenv
from auth.jwt_utils import create_jwt_token
from auth.user_service import authenticate_user

load_dotenv()

def login():
    """Authenticate user and return JWT token."""
    print("\n" + "=" * 60)
    print("🔐 Jarvis Authentication")
    print("=" * 60)

    username = input("\nUsername: ").strip()
    password = getpass.getpass("Password: ")

    user = authenticate_user(username, password)

    if not user:
        print("\n❌ Authentication failed. Invalid username or password.")
        return None, None

    token = create_jwt_token(user["username"], user["user_id"])

    print(f"\n✅ Welcome, {user['username']}!")
    print(f"   Email: {user['email']}")
    print(f"   Role: {user['role']}")

    return token, user["username"]

def main():
    # First, authenticate user
    token, username = login()

    if not token:
        print("\nExiting...")
        return

    # Rest of CLI code with token included in requests...
    print("\n" + "=" * 60)
    print("🤖 Agentic Jarvis - Your Intelligent Assistant")
    print("=" * 60)
    # ... (continue with authenticated session)
```

**Acceptance Criteria:**
- [ ] CLI prompts for username/password
- [ ] Authentication working before chat starts
- [ ] Token included in all agent requests
- [ ] Failed login handled gracefully

---

### Task 24: Create Simple Web Chat Interface with Login

**Status:** Pending

**Description:**
Create a **simple, minimal** web-based chat interface to showcase login/logout and basic session management. Focus on **functionality over design**. ADK's `/dev-ui` remains available for development (no auth required).

**Design Philosophy:**
- Keep it simple - basic HTML/CSS, no fancy animations
- Focus on demonstrating authentication flow
- Phase 2: Basic sessions (in-memory, lost on logout)
- Phase 3 will add: Persistent sessions, conversation history, "continue where you left off"

**Architecture:**
```
Port 9999:
├─ /              → Custom login page (public)
├─ /chat          → Custom chat interface (requires JWT)
├─ /login (POST)  → Login API endpoint
├─ /ws/chat       → WebSocket for real-time chat (requires JWT)
├─ /logout        → Logout endpoint
├─ /dev-ui        → ADK Web UI (NO AUTH - for development only)
└─ /docs          → API docs (public)
```

**Files to Create:**

**1. `web_ui/server.py`** - Custom web server with authentication

```python
"""
Jarvis Custom Web Interface with Authentication
Serves custom chat UI on port 9999 alongside ADK /dev-ui
"""

from fastapi import FastAPI, WebSocket, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from pydantic import BaseModel
import os
import sys

sys.path.insert(0, '..')
from auth.jwt_utils import create_jwt_token, verify_jwt_token
from auth.user_service import authenticate_user
from jarvis_agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

app = FastAPI(title="Jarvis Web Interface")

# Mount static files
app.mount("/static", StaticFiles(directory="web_ui/static"), name="static")

# Security
security = HTTPBearer()

# Session service for agent
session_service = InMemorySessionService()

class LoginRequest(BaseModel):
    username: str
    password: str

class ChatMessage(BaseModel):
    message: str

@app.get("/")
async def root():
    """Serve login page."""
    with open("web_ui/static/login.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/login")
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_jwt_token(user["username"], user["user_id"])

    return {
        "success": True,
        "token": token,
        "user": {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@app.get("/chat")
async def chat_page(request: Request):
    """Serve chat interface (requires authentication)."""
    # Check for token in query params (from redirect after login)
    token = request.query_params.get("token")

    if not token:
        return RedirectResponse(url="/")

    # Verify token
    payload = verify_jwt_token(token)
    if not payload:
        return RedirectResponse(url="/")

    with open("web_ui/static/chat.html", "r") as f:
        return HTMLResponse(content=f.read())

def verify_token_dependency(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """Dependency to verify JWT token."""
    payload = verify_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload.get("username")

@app.post("/api/chat")
async def chat_endpoint(
    chat_message: ChatMessage,
    username: str = Depends(verify_token_dependency)
):
    """Send message to Jarvis and get response."""
    try:
        # Create or get session for user
        session_id = f"web-session-{username}"
        app_name = "jarvis"

        # Create session if not exists
        try:
            session_service.create_session_sync(
                app_name=app_name,
                user_id=username,
                session_id=session_id
            )
        except:
            pass  # Session already exists

        # Create runner
        runner = Runner(
            app_name=app_name,
            agent=root_agent,
            session_service=session_service,
        )

        # Prepare message
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=chat_message.message)]
        )

        # Run agent and collect response
        response_text = ""
        for event in runner.run(
            user_id=username,
            session_id=session_id,
            new_message=new_message
        ):
            if event.content and event.content.parts and event.author != "user":
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text

        return {
            "success": True,
            "response": response_text if response_text else "I'm processing your request...",
            "username": username
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/logout")
async def logout():
    """Logout endpoint (client handles token removal)."""
    return {"success": True, "message": "Logged out successfully"}

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print(" Jarvis Custom Web Interface")
    print("=" * 70)
    print()
    print("Web Interface:")
    print("  → Login Page: http://localhost:9999/")
    print("  → Chat Interface: http://localhost:9999/chat")
    print()
    print("Development:")
    print("  → ADK Dev UI: http://localhost:9999/dev-ui (no auth)")
    print("  → API Docs: http://localhost:9999/docs")
    print()
    print("=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=9999)
```

**2. `web_ui/static/login.html`** - Login page

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis - Login</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="login-container">
        <div class="login-card">
            <div class="logo">
                <h1>🤖 Jarvis</h1>
                <p>Your Intelligent Assistant</p>
            </div>

            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required autofocus>
                </div>

                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>

                <div id="errorMessage" class="error-message" style="display: none;"></div>

                <button type="submit" id="loginButton">Login</button>
            </form>

            <div class="demo-accounts">
                <p><strong>Demo Accounts:</strong></p>
                <ul>
                    <li>vishal / password123</li>
                    <li>alex / password123</li>
                    <li>sarah / password123</li>
                </ul>
            </div>
        </div>
    </div>

    <script src="/static/login.js"></script>
</body>
</html>
```

**3. `web_ui/static/chat.html`** - Chat interface

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis - Chat</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <div class="header-left">
                <h1>🤖 Jarvis</h1>
                <span id="userInfo"></span>
            </div>
            <button id="logoutButton" class="logout-btn">Logout</button>
        </div>

        <div class="chat-messages" id="chatMessages">
            <div class="welcome-message">
                <p>👋 Welcome! I can help you with:</p>
                <ul>
                    <li>IT Tickets Management</li>
                    <li>Cloud Cost Analytics</li>
                    <li>Learning & Development</li>
                </ul>
                <p>What would you like to know?</p>
            </div>
        </div>

        <div class="chat-input">
            <form id="chatForm">
                <input
                    type="text"
                    id="messageInput"
                    placeholder="Type your message..."
                    required
                    autocomplete="off"
                >
                <button type="submit" id="sendButton">Send</button>
            </form>
        </div>
    </div>

    <script src="/static/chat.js"></script>
</body>
</html>
```

**4. `web_ui/static/login.js`** - Login logic

```javascript
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');
    const loginButton = document.getElementById('loginButton');

    // Disable button and show loading
    loginButton.disabled = true;
    loginButton.textContent = 'Logging in...';
    errorMessage.style.display = 'none';

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Store token and user info
            localStorage.setItem('jarvis_token', data.token);
            localStorage.setItem('jarvis_user', JSON.stringify(data.user));

            // Redirect to chat with token
            window.location.href = `/chat?token=${data.token}`;
        } else {
            errorMessage.textContent = data.detail || 'Login failed';
            errorMessage.style.display = 'block';
        }
    } catch (error) {
        errorMessage.textContent = 'Network error. Please try again.';
        errorMessage.style.display = 'block';
    } finally {
        loginButton.disabled = false;
        loginButton.textContent = 'Login';
    }
});
```

**5. `web_ui/static/chat.js`** - Chat logic

```javascript
// Get token from localStorage
const token = localStorage.getItem('jarvis_token');
const user = JSON.parse(localStorage.getItem('jarvis_user') || '{}');

// Redirect to login if no token
if (!token) {
    window.location.href = '/';
}

// Display user info
document.getElementById('userInfo').textContent = `Logged in as ${user.username} (${user.role})`;

// Logout handler
document.getElementById('logoutButton').addEventListener('click', async () => {
    localStorage.removeItem('jarvis_token');
    localStorage.removeItem('jarvis_user');

    await fetch('/logout', { method: 'POST' });
    window.location.href = '/';
});

// Chat message handler
document.getElementById('chatForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';

    // Disable input while processing
    messageInput.disabled = true;
    document.getElementById('sendButton').disabled = true;

    // Show typing indicator
    const typingDiv = addMessage('assistant', 'Typing...');
    typingDiv.classList.add('typing');

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        // Remove typing indicator
        typingDiv.remove();

        if (response.ok) {
            addMessage('assistant', data.response);
        } else {
            if (response.status === 401) {
                // Token expired
                localStorage.removeItem('jarvis_token');
                window.location.href = '/';
            } else {
                addMessage('assistant', `Error: ${data.detail || 'Something went wrong'}`);
            }
        }
    } catch (error) {
        typingDiv.remove();
        addMessage('assistant', 'Network error. Please try again.');
    } finally {
        messageInput.disabled = false;
        document.getElementById('sendButton').disabled = false;
        messageInput.focus();
    }
});

function addMessage(role, text) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;

    const icon = role === 'user' ? '👤' : '🤖';
    messageDiv.innerHTML = `
        <div class="message-icon">${icon}</div>
        <div class="message-content">${escapeHtml(text)}</div>
    `;

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    return messageDiv;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}
```

**6. `web_ui/static/styles.css`** - Simple, minimal styling

```css
/* SIMPLE STYLING - Focus on functionality, not fancy design */

body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f0f0f0;
}

/* Login Page - Keep it simple */
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
}

.login-card {
    background: white;
    padding: 30px;
    border-radius: 5px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    width: 350px;
}

.logo {
    text-align: center;
    margin-bottom: 20px;
}

.logo h1 {
    margin: 0;
    font-size: 32px;
}

.logo p {
    margin: 5px 0 0 0;
    color: #666;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

.form-group input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 3px;
    font-size: 14px;
}

button[type="submit"] {
    width: 100%;
    padding: 12px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 3px;
    cursor: pointer;
    font-size: 16px;
}

button[type="submit"]:hover {
    background-color: #45a049;
}

.error-message {
    background-color: #ffebee;
    color: #c62828;
    padding: 10px;
    border-radius: 3px;
    margin-bottom: 15px;
}

.demo-accounts {
    margin-top: 20px;
    padding-top: 15px;
    border-top: 1px solid #ddd;
    font-size: 13px;
    color: #666;
}

.demo-accounts ul {
    list-style: none;
    padding: 0;
    margin: 10px 0 0 0;
}

/* Chat Page - Simple layout */
.chat-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: white;
}

.chat-header {
    background-color: #4CAF50;
    color: white;
    padding: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-left h1 {
    margin: 0;
    font-size: 20px;
}

.header-left span {
    font-size: 13px;
}

.logout-btn {
    background-color: rgba(0,0,0,0.2);
    color: white;
    border: none;
    padding: 8px 15px;
    border-radius: 3px;
    cursor: pointer;
}

.logout-btn:hover {
    background-color: rgba(0,0,0,0.3);
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 15px;
    background-color: #f9f9f9;
}

.welcome-message {
    background: white;
    padding: 15px;
    border: 1px solid #ddd;
    border-radius: 3px;
    margin-bottom: 15px;
}

.message {
    margin-bottom: 10px;
    display: flex;
}

.message-icon {
    margin-right: 8px;
}

.message-content {
    background: white;
    padding: 10px;
    border-radius: 3px;
    border: 1px solid #ddd;
    max-width: 70%;
}

.user-message {
    justify-content: flex-end;
}

.user-message .message-content {
    background-color: #e3f2fd;
    border-color: #90caf9;
}

.chat-input {
    padding: 15px;
    background: white;
    border-top: 1px solid #ddd;
}

.chat-input form {
    display: flex;
    gap: 10px;
}

.chat-input input {
    flex: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 3px;
}

.chat-input button {
    padding: 10px 20px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 3px;
    cursor: pointer;
}

.chat-input button:hover {
    background-color: #45a049;
}

.chat-input button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}
```

**Note:** This is intentionally minimal - no gradients, no animations, no fancy effects. Focus is on showcasing authentication and session management functionality.

**Acceptance Criteria:**
- [ ] Custom web interface created with login page
- [ ] Chat interface with real-time messaging
- [ ] JWT authentication working
- [ ] User info displayed in chat header
- [ ] Logout functionality working
- [ ] ADK `/dev-ui` remains accessible WITHOUT authentication (for development)
- [ ] Responsive design works on mobile
- [ ] Error handling for failed login and network issues

---

### Task 25: Update Environment Configuration

**Status:** Pending

**Description:**
Update `.env.template` and documentation for JWT configuration.

**Changes:**

**`.env.template`**:
```bash
# Google API Key
GOOGLE_API_KEY=your_api_key_here

# Service Ports
TICKETS_SERVER_PORT=5001
FINOPS_SERVER_PORT=5002
OXYGEN_AGENT_PORT=8002
AUTH_SERVICE_PORT=9998
WEB_UI_PORT=9999

# Phase 2: JWT Authentication
JWT_SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
JWT_EXPIRATION_HOURS=24

# Phase 3: Session/Memory (Future)
# SESSION_TYPE=memory
# DATABASE_URL=sqlite:///./jarvis.db
```

**Acceptance Criteria:**
- [ ] `.env.template` updated with JWT variables
- [ ] Documentation updated with authentication instructions
- [ ] Sample JWT_SECRET_KEY provided (for dev only)

---

### Task 26: Create Startup Scripts for Phase 2

**Status:** Pending

**Description:**
Create startup scripts for auth service and custom web interface. Update existing scripts to support Phase 2 services.

**Files to Create/Update:**

**1. `scripts/start_auth_service.sh`** - Start auth service (port 9998)
```bash
#!/bin/bash

echo "Starting Jarvis Auth Service on port 9998..."
if lsof -ti:9998 > /dev/null 2>&1; then
    echo "Cleaning up existing processes on port 9998..."
    lsof -ti:9998 | xargs kill -9 2>/dev/null
    sleep 1
fi

.venv/bin/python auth/auth_server.py
```

**2. `scripts/start_custom_web.sh`** - Start custom web interface (port 9999)
```bash
#!/bin/bash

echo "========================================"
echo " Starting Jarvis Custom Web Interface"
echo "========================================"
echo ""

# Kill any existing processes on port 9999
if lsof -ti:9999 > /dev/null 2>&1; then
    echo "Cleaning up existing processes on port 9999..."
    lsof -ti:9999 | xargs kill -9 2>/dev/null
    sleep 1
    echo "✓ Port 9999 cleared"
    echo ""
fi

# Check if required services are running
echo "Checking required services..."
echo ""

services_ok=true

if ! lsof -ti:9998 > /dev/null 2>&1; then
    echo "❌ Auth service is not running on port 9998"
    services_ok=false
fi

if ! lsof -ti:5001 > /dev/null 2>&1; then
    echo "❌ Tickets server is not running on port 5001"
    services_ok=false
fi

if ! lsof -ti:5002 > /dev/null 2>&1; then
    echo "❌ FinOps server is not running on port 5002"
    services_ok=false
fi

if ! lsof -ti:8002 > /dev/null 2>&1; then
    echo "❌ Oxygen agent is not running on port 8002"
    services_ok=false
fi

if [ "$services_ok" = false ]; then
    echo ""
    echo "Please start all services first:"
    echo "  ./scripts/restart_all.sh"
    echo ""
    exit 1
fi

echo "✓ All required services are running"
echo ""
echo "========================================"
echo "Starting custom web interface..."
echo ""
echo "Access points:"
echo "  → Login: http://localhost:9999/"
echo "  → Chat: http://localhost:9999/chat"
echo "  → Dev UI: http://localhost:9999/dev-ui (no auth)"
echo "  → API Docs: http://localhost:9999/docs"
echo "========================================"
echo ""

.venv/bin/python web_ui/server.py
```

**3. Update `scripts/restart_all.sh`** - Include Phase 2 services
```bash
#!/bin/bash
echo "========================================"
echo "Restarting All Jarvis Services (Phase 2)"
echo "========================================"
echo ""

echo "Step 1: Stopping all existing services..."

# Kill all services
lsof -ti:9998 | xargs kill -9 2>/dev/null  # Auth service
lsof -ti:5001 | xargs kill -9 2>/dev/null  # Tickets
lsof -ti:5002 | xargs kill -9 2>/dev/null  # FinOps
lsof -ti:8002 | xargs kill -9 2>/dev/null  # Oxygen
lsof -ti:9999 | xargs kill -9 2>/dev/null  # Web UI

echo "  ✓ Stopped Auth service (port 9998)"
echo "  ✓ Stopped Tickets server (port 5001)"
echo "  ✓ Stopped FinOps server (port 5002)"
echo "  ✓ Stopped Oxygen agent (port 8002)"
echo "  ✓ Stopped Web UI (port 9999)"
echo ""

sleep 2

echo "Step 2: Starting all services in background..."
echo ""

# Start Auth Service first
echo "Starting Auth Service (port 9998)..."
nohup .venv/bin/python auth/auth_server.py > logs/auth_service.log 2>&1 &
sleep 1

# Start Toolbox Servers
echo "Starting Tickets Toolbox Server (port 5001)..."
nohup .venv/bin/python toolbox_servers/tickets_server/server.py > logs/tickets_server.log 2>&1 &
sleep 1

echo "Starting FinOps Toolbox Server (port 5002)..."
nohup .venv/bin/python toolbox_servers/finops_server/server.py > logs/finops_server.log 2>&1 &
sleep 1

# Start Oxygen A2A Agent
echo "Starting Oxygen A2A Agent (port 8002)..."
nohup .venv/bin/python -m uvicorn remote_agent.oxygen_agent.agent:a2a_app --host localhost --port 8002 > logs/oxygen_agent.log 2>&1 &
sleep 1

# Start Custom Web Interface
echo "Starting Custom Web Interface (port 9999)..."
nohup .venv/bin/python web_ui/server.py > logs/custom_web.log 2>&1 &
sleep 2

echo ""
echo "Step 3: Verifying services..."
echo ""

# Verify each service
for port in 9998 5001 5002 8002 9999; do
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "✓ Service running on port $port"
    else
        echo "❌ Service failed to start on port $port"
    fi
done

echo ""
echo "========================================"
echo "✓ All services started successfully!"
echo ""
echo "Next steps:"
echo "  1. Run './scripts/check_services.sh' to verify health"
echo "  2. Open http://localhost:9999/ to login and chat"
echo "  3. Or run 'python main.py' for CLI interface"
echo ""
echo "Logs are available in the logs/ directory"
echo "========================================"
```

**Acceptance Criteria:**
- [ ] Auth service startup script created
- [ ] Custom web startup script created
- [ ] restart_all.sh updated to include all Phase 2 services
- [ ] All services start in correct order (auth → toolboxes → oxygen → web)
- [ ] Port cleanup working for all services

---

### Task 27: Testing Phase 2 Authentication

**Status:** Pending

**Description:**
Test all authentication flows and user-specific data access.

**Test Scenarios:**

**1. Login Test:**
```bash
# Test login endpoint
curl -X POST http://localhost:9998/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "vishal", "password": "password123"}'

# Expected: Returns JWT token
```

**2. Authenticated Tickets Access:**
```bash
# Get token first
TOKEN=$(curl -s -X POST http://localhost:9998/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "vishal", "password": "password123"}' | jq -r '.access_token')

# Access tickets with token
curl -X POST http://localhost:5001/api/tool/get-my-tickets/invoke \
  -H "Authorization: Bearer $TOKEN"

# Expected: Only vishal's tickets (12301, 12303)
```

**3. User Isolation Test:**
```bash
# Login as alex
TOKEN_ALEX=$(curl -s -X POST http://localhost:9998/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alex", "password": "password123"}' | jq -r '.access_token')

# Try to access with alex's token
curl -X POST http://localhost:5001/api/tool/get-my-tickets/invoke \
  -H "Authorization: Bearer $TOKEN_ALEX"

# Expected: Only alex's tickets (12302, 12304) - NOT vishal's
```

**4. Invalid Token Test:**
```bash
# Try with invalid token
curl -X POST http://localhost:5001/api/tool/get-my-tickets/invoke \
  -H "Authorization: Bearer invalid-token-xyz"

# Expected: 401 Unauthorized
```

**5. Cross-Agent Authentication:**
```bash
# Test that token propagates through Jarvis → Oxygen
# Login and use CLI to query learning data
python main.py
# Login as vishal
# Query: "What are my pending exams?"
# Expected: Only vishal's exams (snowflake)
```

**Acceptance Criteria:**
- [ ] All 5 test scenarios pass
- [ ] Users can only see their own data
- [ ] Invalid tokens rejected
- [ ] Token propagation works across agents
- [ ] A2A calls include authentication

---

## Phase 2 Summary

### New Capabilities

After Phase 2 completion:

✅ **User Authentication**
- Users must login with username/password
- JWT tokens issued for authenticated sessions
- Tokens expire after 24 hours

✅ **Data Isolation**
- Users see only their own tickets
- Learning data is user-specific
- No cross-user data leakage

✅ **Secure Communication**
- All API endpoints require valid JWT
- Token propagates through agent chain
- A2A calls authenticated

✅ **Dual Web Interface**
- **Custom Web Chat** (http://localhost:9999/) - Production UI with login required
- **ADK Dev UI** (http://localhost:9999/dev-ui) - Development tool, NO AUTH required
- CLI interface with login prompt

### Architecture Changes

```
Before Phase 2:
User → Jarvis → Agents → All Data (no authentication)

After Phase 2:

User Interfaces:
├─ Custom Web (w/ login) → http://localhost:9999/
├─ CLI (w/ login) → python main.py
└─ ADK Dev UI (no auth) → http://localhost:9999/dev-ui
         │
         ▼ (Login → JWT Token)
    ┌─────────┐
    │  Auth   │ Port 9998
    │ Service │
    └────┬────┘
         ▼ (JWT Token)
    ┌─────────┐
    │ Jarvis  │ Verify JWT
    │  Root   │ Extract User
    └────┬────┘
         │
    ┌────┴────┬────────┐
    │         │        │
┌───▼───┐ ┌──▼───┐ ┌──▼────┐
│Tickets│ │FinOps│ │Oxygen │
│Filter │ │Shared│ │Filter │
│by user│ │ Data │ │by user│
└───────┘ └──────┘ └───────┘
```

### Default User Accounts

For testing and development:

| Username | Password    | Role          | Sample Data                          |
|----------|-------------|---------------|--------------------------------------|
| vishal   | password123 | developer     | 2 tickets, AWS/Terraform courses     |
| alex     | password123 | devops        | 2 tickets, Kubernetes courses        |
| sarah    | password123 | data_scientist| 1 ticket, ML/Data Science courses    |

**⚠️ IMPORTANT:** Change these passwords in production!

### Next Phase Preview

**Phase 3: Memory & Context Management**
- Session persistence across conversations
- Long-term memory with Vector DB
- Proactive notifications
- Context-aware recommendations

### Success Metrics

Phase 2 will be considered complete when:
- [ ] 10/10 tasks completed (Tasks 18-27)
- [ ] All authentication tests passing
- [ ] User data properly isolated
- [ ] CLI and Web UI support login
- [ ] Documentation updated

---

**Estimated Effort:** 10-12 tasks
**Recommended Approach:** Implement and test incrementally
- Tasks 18-19: Core auth infrastructure
- Tasks 20-21: Agent authentication
- Tasks 22-24: User interfaces
- Tasks 25-27: Deployment & testing
