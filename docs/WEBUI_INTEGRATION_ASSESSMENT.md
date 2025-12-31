# WebUI Integration Assessment - Pure A2A + JWT Authentication

## Executive Summary

**Current State:** Web UI exists but is **NOT integrated** with Phase 2 Pure A2A architecture.

**Complexity Rating:**
- **Phase 1 (Minimal Viable):** ⭐⭐⭐ MEDIUM (4-5 hours)
- **Phase 2 (Full-Featured):** ⭐⭐⭐⭐ MEDIUM-HIGH (8-10 hours total)

**Critical Issues:** 3 major incompatibilities that must be fixed

**Recommendation:** ✅ Proceed in 2 phases - Phase 1 first, then evaluate Phase 2

---

## Current Web UI Files Analysis

### 1. `web.py` (Port 9999)
**Status:** ❌ **OBSOLETE - Do Not Use**
- Uses ADK's generic web UI (`get_fast_api_app`)
- No authentication
- Not connected to Phase 2 architecture
- Meant for Phase 1 toolbox servers
- **Recommendation:** Ignore this file

### 2. `web_ui/server.py` (Port 9999)
**Status:** ⚠️ **INCOMPATIBLE - Needs Major Rewrite**
- Has JWT authentication skeleton ✅
- Has nice login/chat pages ✅
- **BUT** uses OLD Phase 1 architecture:
  - Imports `jarvis_agent.agent.root_agent` (doesn't exist in Phase 2)
  - Uses `InMemorySessionService` (Phase 2 uses Registry Service)
  - No integration with JarvisOrchestrator
  - No connection to A2A agents
- **Critical:** This will NOT work with Phase 2

### 3. `web_ui/server_mcp.py` (Port 9990)
**Status:** ⚠️ **NO AUTHENTICATION**
- Has embedded HTML (all-in-one file)
- No JWT authentication
- Uses MCP agents (different from Pure A2A)
- Created for Phase 2 Part A testing
- **Not suitable** for production

### 4. `web_ui/static/login.html`
**Status:** ⚠️ **NEEDS MINOR FIX**
- Good UI design ✅
- Calls correct auth endpoint (`http://localhost:9998/auth/login`) ✅
- **BUT** expects wrong response format:
  ```javascript
  // Current (WRONG):
  if (data.success && data.token) {
      localStorage.setItem('token', data.token);
  }

  // Should be (CORRECT):
  if (response.ok && data.access_token) {
      localStorage.setItem('token', data.access_token);
  }
  ```
- Missing "happy" and "admin" users in demo list
- **Fix:** 5-10 minutes

### 5. `web_ui/static/chat.html`
**Status:** ⚠️ **NEEDS ENHANCEMENT**
- Good chat UI ✅
- Has JWT token passing ✅
- **Missing features:**
  - No conversation history loading
  - No query suggestions based on history
  - No session resumption indicator
  - Calls wrong endpoint (`/api/chat` which doesn't exist in Phase 2)
- **Fix:** 1-2 hours with suggestions feature

---

## Phase 1: Minimal Viable WebUI (4-5 hours)

### Overview
Get a working WebUI integrated with Phase 2 Pure A2A architecture with all core features.

### What You'll Get
- ✅ Working login with JWT authentication
- ✅ Chat interface connected to Phase 2 Pure A2A
- ✅ Session persistence across logins
- ✅ Conversation history on reload
- ✅ Simple query suggestions (rule-based)
- ✅ Security access control (admin vs regular users)
- ✅ All 4 users working (vishal, happy, alex, admin)

### Tasks Breakdown

| # | Task | Time | Complexity | Priority |
|---|------|------|-----------|----------|
| 1 | Fix login.html API response parsing | 15 min | ⭐ Trivial | P0 |
| 2 | Create new server_phase2.py with JarvisOrchestrator | 2 hours | ⭐⭐⭐ Medium | P0 |
| 3 | Add history loading from registry | 1 hour | ⭐⭐ Easy-Medium | P1 |
| 4 | Add simple suggestion chips (rule-based) | 1 hour | ⭐⭐ Easy-Medium | P2 |
| 5 | Update chat.html UI | 30 min | ⭐ Trivial | P1 |
| 6 | Testing & bug fixes | 30 min | ⭐⭐ Medium | P0 |

**Total Time:** 4 hours 45 minutes

### Detailed Implementation Steps

#### Step 1: Fix login.html (15 minutes) ⚡

**File:** `web_ui/static/login.html`

**Changes:**
```javascript
// Line 174: Update auth endpoint call
const response = await fetch('http://localhost:9998/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ username, password })
});

const data = await response.json();

// Line 184: Fix response parsing
if (response.ok && data.access_token) {  // Changed from data.success && data.token
    localStorage.setItem('token', data.access_token);  // Changed from data.token
    localStorage.setItem('user', JSON.stringify(data.user));
    window.location.href = '/chat.html';
} else {
    errorDiv.textContent = data.detail || 'Invalid username or password';
}
```

**Update demo users:**
```html
<div class="demo-users">
    <h3>Demo Accounts:</h3>
    <ul>
        <li>• vishal / password123 (developer)</li>
        <li>• happy / password123 (developer)</li>
        <li>• alex / password123 (devops)</li>
        <li>• admin / admin123 (admin - full access)</li>
    </ul>
</div>
```

---

#### Step 2: Create server_phase2.py (2 hours) ⚠️

**File:** NEW - `web_ui/server_phase2.py`

**Key Components:**

1. **Import JarvisOrchestrator:**
```python
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.jwt_utils import verify_jwt_token
from jarvis_agent.main_with_registry import JarvisOrchestrator
from jarvis_agent.session_client import RegistrySessionClient
```

2. **Request/Response Models:**
```python
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

class HistoryResponse(BaseModel):
    session_id: str
    messages: list
    message_count: int
```

3. **Authentication Helper:**
```python
def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract and validate user from JWT token."""
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]
    payload = verify_jwt_token(token)

    if not payload:
        return None

    return payload.get("username")

def get_token_from_header(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract token from Authorization header."""
    if not authorization:
        return None
    parts = authorization.split()
    return parts[1] if len(parts) == 2 else None
```

4. **Main Chat Endpoint:**
```python
@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Optional[str] = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """Handle chat requests with Jarvis agent."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # Get JWT token
        token = get_token_from_header(authorization)

        # Create orchestrator with JWT
        orchestrator = JarvisOrchestrator(jwt_token=token)

        # Handle query (automatically uses registry session)
        response = orchestrator.handle_query(request.message)

        # Get session ID
        session_id = orchestrator.session_id

        orchestrator.close()

        return ChatResponse(
            response=response,
            session_id=session_id
        )

    except PermissionError as e:
        # User tried to access unauthorized data
        return ChatResponse(
            response=str(e),
            session_id=orchestrator.session_id if 'orchestrator' in locals() else ""
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )
```

5. **History Endpoint:**
```python
@app.get("/api/history", response_model=HistoryResponse)
async def get_history(
    current_user: Optional[str] = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """Get conversation history for current user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        token = get_token_from_header(authorization)

        # Create orchestrator to get session
        orchestrator = JarvisOrchestrator(jwt_token=token)
        session_id = orchestrator.session_id

        # Get messages from session
        session_client = RegistrySessionClient()
        messages = session_client.get_messages(session_id)

        orchestrator.close()

        return HistoryResponse(
            session_id=session_id,
            messages=messages,
            message_count=len(messages)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching history: {str(e)}"
        )
```

**Full server structure:** See implementation template at end of document.

---

#### Step 3: Add History Loading (1 hour) ⚠️

**File:** `web_ui/static/chat.html`

**Add history loading on page load:**
```javascript
// After authentication check
async function loadHistory() {
    try {
        const response = await fetch('http://localhost:9999/api/history', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();

            if (data.messages && data.messages.length > 0) {
                // Show welcome back message
                const welcomeDiv = messagesDiv.querySelector('.welcome-message');
                if (welcomeDiv) {
                    welcomeDiv.innerHTML = `
                        <h2>Welcome back, ${user.username}!</h2>
                        <p>Resuming session from earlier</p>
                        <p style="font-size: 12px; color: #888;">
                            Session: ${data.session_id}<br>
                            Messages: ${data.message_count}
                        </p>
                    `;
                }

                // Render previous messages
                for (const msg of data.messages) {
                    if (msg.role === 'user') {
                        addMessage('user', msg.content);
                    } else if (msg.role === 'assistant') {
                        addMessage('assistant', msg.content);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Failed to load history:', error);
        // Continue without history
    }
}

// Call on page load
loadHistory();
```

---

#### Step 4: Add Simple Suggestions (1 hour) ⚠️

**File:** `web_ui/static/chat.html`

**Add suggestions HTML:**
```html
<!-- Add before input-container -->
<div class="suggestions-container">
    <div class="suggestions-label">Suggestions:</div>
    <div id="suggestions" class="suggestions-chips"></div>
</div>
```

**Add CSS:**
```css
.suggestions-container {
    padding: 15px 20px;
    border-top: 1px solid #ddd;
    background: #f9f9f9;
}

.suggestions-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 8px;
    font-weight: 600;
}

.suggestions-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.suggestion-chip {
    background: white;
    border: 1px solid #ddd;
    padding: 8px 12px;
    border-radius: 16px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
}

.suggestion-chip:hover {
    background: #4CAF50;
    color: white;
    border-color: #4CAF50;
}
```

**Add JavaScript logic:**
```javascript
function getSuggestions(messageHistory) {
    // Rule-based suggestions based on conversation
    const hasTickets = messageHistory.some(m =>
        m.toLowerCase().includes('ticket')
    );
    const hasCourses = messageHistory.some(m =>
        m.toLowerCase().includes('course') || m.toLowerCase().includes('learn')
    );
    const hasCosts = messageHistory.some(m =>
        m.toLowerCase().includes('cost') || m.toLowerCase().includes('cloud')
    );

    // New user suggestions
    if (messageHistory.length === 0) {
        return [
            "Show my tickets",
            "What are my courses",
            "Check cloud costs"
        ];
    }

    // Contextual suggestions
    const suggestions = [];

    if (hasTickets) {
        suggestions.push("Show my open tickets", "Create a new ticket");
    } else {
        suggestions.push("Show my tickets");
    }

    if (hasCourses) {
        suggestions.push("Show pending exams", "My course progress");
    } else {
        suggestions.push("What courses am I enrolled in");
    }

    if (hasCosts) {
        suggestions.push("Show AWS costs", "Compare cloud spending");
    } else {
        suggestions.push("What's our cloud cost");
    }

    return suggestions.slice(0, 5); // Max 5 suggestions
}

function renderSuggestions(suggestions) {
    const suggestionsDiv = document.getElementById('suggestions');
    suggestionsDiv.innerHTML = '';

    suggestions.forEach(text => {
        const chip = document.createElement('div');
        chip.className = 'suggestion-chip';
        chip.textContent = text;
        chip.onclick = () => {
            messageInput.value = text;
            messageInput.focus();
        };
        suggestionsDiv.appendChild(chip);
    });
}

// Update suggestions after each message
function updateSuggestions() {
    const messageHistory = Array.from(messagesDiv.querySelectorAll('.message.user .message-text'))
        .map(el => el.textContent);

    const suggestions = getSuggestions(messageHistory);
    renderSuggestions(suggestions);
}

// Call after loading history and after each message
updateSuggestions();
```

---

#### Step 5: Update chat.html UI (30 minutes) ⚡

**Changes:**
1. Update API endpoint to `http://localhost:9999/api/chat`
2. Remove `session_id` and `user_id` from request (handled by server)
3. Add error message styling
4. Add loading states

```javascript
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    messageInput.value = '';
    sendButton.disabled = true;
    sendButton.textContent = 'Sending...';

    const welcomeMsg = messagesDiv.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    addMessage('user', message);

    try {
        const response = await fetch('http://localhost:9999/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ message: message })
        });

        if (response.ok) {
            const data = await response.json();
            addMessage('assistant', data.response);
            updateSuggestions(); // Update after each message
        } else if (response.status === 401) {
            addMessage('error', 'Session expired. Please login again.');
            setTimeout(() => logout(), 2000);
        } else {
            addMessage('error', 'Error: Could not get response from Jarvis.');
        }
    } catch (error) {
        addMessage('error', 'Error: Cannot connect to Jarvis. Please ensure all services are running.');
    }

    sendButton.disabled = false;
    sendButton.textContent = 'Send';
}
```

---

#### Step 6: Testing & Bug Fixes (30 minutes) ⚠️

**Test Scenarios:**

1. **Login Flow:**
   - [ ] Test login with vishal/password123
   - [ ] Test login with happy/password123
   - [ ] Test login with alex/password123
   - [ ] Test login with admin/admin123
   - [ ] Test invalid credentials

2. **Chat Functionality:**
   - [ ] Send message "show my tickets"
   - [ ] Verify correct user data shown
   - [ ] Test security: happy tries "show vishal's tickets"
   - [ ] Verify access denied error shown
   - [ ] Test admin: admin queries "show vishal's tickets"
   - [ ] Verify admin can see vishal's data

3. **Session Persistence:**
   - [ ] Login, send 3 messages, logout
   - [ ] Login again with same user
   - [ ] Verify history loads
   - [ ] Verify "Welcome back!" message
   - [ ] Verify suggestions update

4. **Suggestions:**
   - [ ] Verify 3-5 suggestions shown
   - [ ] Click suggestion, verify it fills input
   - [ ] Send message, verify suggestions update

---

## Phase 2: Full-Featured WebUI (8-10 hours total)

### Overview
Add advanced features and polish to the WebUI.

### What You'll Get
- ✅ Everything from Phase 1, plus:
- ✅ AI-generated contextual suggestions (using LLM)
- ✅ Token auto-refresh mechanism
- ✅ Multi-tab session synchronization
- ✅ Better error handling & recovery
- ✅ Loading animations & polish
- ✅ Markdown rendering in responses
- ✅ Message timestamps
- ✅ Session management UI (view/delete old sessions)

### Tasks Breakdown

| # | Task | Time | Complexity | Priority |
|---|------|------|-----------|----------|
| 1 | LLM-based suggestion generation | 2 hours | ⭐⭐⭐⭐ Complex | P1 |
| 2 | Token refresh mechanism | 1 hour | ⭐⭐⭐ Medium | P0 |
| 3 | Session sync across tabs | 1 hour | ⭐⭐⭐ Medium | P2 |
| 4 | Markdown rendering | 1 hour | ⭐⭐ Easy-Medium | P2 |
| 5 | Message timestamps | 30 min | ⭐ Trivial | P3 |
| 6 | Session management UI | 1 hour | ⭐⭐ Easy-Medium | P2 |
| 7 | Loading animations & polish | 1 hour | ⭐⭐ Easy-Medium | P3 |
| 8 | Error recovery improvements | 30 min | ⭐⭐ Easy-Medium | P1 |
| 9 | Testing & refinement | 1 hour | ⭐⭐ Medium | P0 |

**Total Time:** 9 hours

### Detailed Implementation Steps

#### Step 1: AI-Generated Suggestions (2 hours) ⭐⭐⭐⭐

**Backend Endpoint:**
```python
# In server_phase2.py

@app.get("/api/suggestions")
async def get_smart_suggestions(
    current_user: Optional[str] = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """Generate AI-powered contextual suggestions."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        from google import genai
        from google.genai import types

        token = get_token_from_header(authorization)
        orchestrator = JarvisOrchestrator(jwt_token=token)

        # Get recent messages
        session_client = RegistrySessionClient()
        messages = session_client.get_messages(orchestrator.session_id)

        # Build conversation context
        context = "\n".join([
            f"{msg['role']}: {msg['content'][:100]}"
            for msg in messages[-10:]  # Last 10 messages
        ])

        # Generate suggestions using LLM
        api_key = os.getenv("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)

        prompt = f"""Based on this conversation history for user {current_user}, suggest 5 relevant follow-up queries they might want to ask:

Conversation:
{context}

User capabilities:
- View and create IT tickets
- Check cloud costs (AWS, GCP, Azure)
- View learning courses and exams

Generate 5 short, actionable query suggestions (max 10 words each).
Return as JSON array: ["suggestion 1", "suggestion 2", ...]
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT"],
                response_mime_type="application/json"
            )
        )

        suggestions = json.loads(response.text)

        orchestrator.close()

        return {"suggestions": suggestions}

    except Exception as e:
        # Fallback to simple suggestions
        return {
            "suggestions": [
                "Show my tickets",
                "What are my courses",
                "Check cloud costs"
            ]
        }
```

**Frontend Integration:**
```javascript
async function loadSmartSuggestions() {
    try {
        const response = await fetch('http://localhost:9999/api/suggestions', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            renderSuggestions(data.suggestions);
        } else {
            // Fallback to rule-based
            updateSuggestions();
        }
    } catch (error) {
        console.error('Failed to load smart suggestions:', error);
        updateSuggestions();
    }
}

// Call after each message (with debouncing)
let suggestionTimeout;
function updateSmartSuggestions() {
    clearTimeout(suggestionTimeout);
    suggestionTimeout = setTimeout(() => {
        loadSmartSuggestions();
    }, 1000); // Wait 1s after last message
}
```

---

#### Step 2: Token Refresh (1 hour) ⭐⭐⭐

**Backend Endpoint:**
```python
@app.post("/api/auth/refresh")
async def refresh_token(
    current_user: Optional[str] = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """Refresh JWT token before expiration."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        from auth.jwt_utils import create_jwt_token
        from auth.user_service import get_user_info

        # Get user info
        user_info = get_user_info(current_user)
        if not user_info:
            raise HTTPException(status_code=401, detail="User not found")

        # Create new token
        new_token = create_jwt_token(user_info)

        return {
            "access_token": new_token,
            "token_type": "bearer"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Frontend Auto-Refresh:**
```javascript
// Check token expiration and refresh if needed
function checkAndRefreshToken() {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
        // Decode JWT to get expiration
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000; // Convert to milliseconds
        const now = Date.now();
        const timeToExpiry = exp - now;

        // Refresh if less than 5 minutes remaining
        if (timeToExpiry < 5 * 60 * 1000) {
            refreshToken();
        }
    } catch (error) {
        console.error('Failed to check token:', error);
    }
}

async function refreshToken() {
    try {
        const response = await fetch('http://localhost:9999/api/auth/refresh', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            console.log('Token refreshed successfully');
        }
    } catch (error) {
        console.error('Failed to refresh token:', error);
    }
}

// Check every minute
setInterval(checkAndRefreshToken, 60000);
```

---

#### Step 3: Multi-Tab Session Sync (1 hour) ⭐⭐⭐

**Use localStorage events:**
```javascript
// Listen for storage changes from other tabs
window.addEventListener('storage', (e) => {
    if (e.key === 'new_message' && e.newValue) {
        const message = JSON.parse(e.newValue);

        // Add message to current tab if not already present
        const existingMessages = Array.from(
            messagesDiv.querySelectorAll('.message')
        );

        const messageExists = existingMessages.some(msg =>
            msg.textContent.includes(message.text)
        );

        if (!messageExists) {
            addMessage(message.type, message.text);
        }
    }
});

// Broadcast new messages to other tabs
function broadcastMessage(type, text) {
    localStorage.setItem('new_message', JSON.stringify({
        type, text, timestamp: Date.now()
    }));
}

// Update addMessage function
function addMessage(type, text) {
    // ... existing code ...

    // Broadcast to other tabs
    broadcastMessage(type, text);
}
```

---

#### Step 4: Markdown Rendering (1 hour) ⭐⭐

**Add marked.js library:**
```html
<!-- In chat.html head -->
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
```

**Update message rendering:**
```javascript
function addMessage(type, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = type === 'user' ? 'You' : 'Jarvis';

    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';

    // Render markdown for assistant messages
    if (type === 'assistant') {
        textDiv.innerHTML = marked.parse(text);
    } else {
        textDiv.textContent = text;
    }

    messageDiv.appendChild(label);
    messageDiv.appendChild(textDiv);
    messagesDiv.appendChild(messageDiv);

    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
```

**Add CSS for code blocks:**
```css
.message-text pre {
    background: #f5f5f5;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
}

.message-text code {
    background: #f5f5f5;
    padding: 2px 4px;
    border-radius: 2px;
    font-family: 'Courier New', monospace;
}

.message-text ul, .message-text ol {
    margin-left: 20px;
}
```

---

#### Step 5: Message Timestamps (30 min) ⭐

**Update message structure:**
```javascript
function addMessage(type, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const label = document.createElement('div');
    label.className = 'message-label';

    // Add timestamp
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });

    label.innerHTML = `
        <span>${type === 'user' ? 'You' : 'Jarvis'}</span>
        <span class="timestamp">${timeStr}</span>
    `;

    // ... rest of message rendering
}
```

**Add CSS:**
```css
.message-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.timestamp {
    font-size: 10px;
    color: #999;
    font-weight: normal;
}
```

---

#### Step 6: Session Management UI (1 hour) ⭐⭐

**Add sessions sidebar:**
```html
<!-- Add to chat.html -->
<div class="sidebar">
    <div class="sidebar-header">
        <h3>Sessions</h3>
        <button onclick="toggleSidebar()">×</button>
    </div>
    <div id="sessionsList"></div>
    <button class="new-session-btn" onclick="createNewSession()">
        + New Session
    </button>
</div>
```

**Backend endpoint:**
```python
@app.get("/api/sessions")
async def get_user_sessions(
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get all sessions for current user."""
    # Implement using registry client
    pass
```

---

## Critical Issues (Must Fix First)

### Issue 1: Login API Mismatch ⭐
**Severity:** 🔴 BLOCKER
**Fix Time:** 5 minutes

**Problem:** Login expects `data.success` and `data.token`, but auth service returns:
```json
{
    "access_token": "eyJ...",
    "token_type": "bearer",
    "user": {...}
}
```

**Fix:**
```javascript
// In login.html line 184
if (response.ok && data.access_token) {
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    window.location.href = '/chat.html';
}
```

---

### Issue 2: Server Integration ⭐⭐⭐
**Severity:** 🔴 BLOCKER
**Fix Time:** 2 hours

**Problem:** Current server.py imports non-existent modules

**Solution:** Create NEW `server_phase2.py` with JarvisOrchestrator integration (see Step 2 above)

---

### Issue 3: Session Management ⭐⭐
**Severity:** 🟡 MAJOR
**Fix Time:** 1 hour (already covered in Step 3)

**Problem:** Uses InMemorySessionService instead of Registry

**Solution:** Use JarvisOrchestrator which handles this automatically

---

## Files That Need Changes

### Phase 1 (Minimal):

1. ✏️ `web_ui/static/login.html` - Fix API response
2. ✨ `web_ui/server_phase2.py` - NEW FILE
3. ✏️ `web_ui/static/chat.html` - Add history + suggestions
4. ✏️ `.env` - Add `WEB_UI_PORT=9999`
5. ✏️ `scripts/start_phase2.sh` - Add web UI startup

### Phase 2 (Full-Featured):

Everything above, plus:

6. ✏️ `web_ui/server_phase2.py` - Add advanced endpoints
7. ✏️ `web_ui/static/chat.html` - Add Phase 2 features
8. ✨ `web_ui/static/css/style.css` - NEW separate CSS file
9. ✨ `web_ui/static/js/app.js` - NEW separate JS file
10. ✨ `docs/WEBUI_USER_GUIDE.md` - User documentation

---

## Implementation Templates

### Template: server_phase2.py (Complete)

```python
"""
Jarvis Web UI Server - Phase 2 Pure A2A
Integrated with JarvisOrchestrator and Registry Service
Port: 9999
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.jwt_utils import verify_jwt_token
from jarvis_agent.main_with_registry import JarvisOrchestrator
from jarvis_agent.session_client import RegistrySessionClient

# ============================================================================
# Models
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: str

class HistoryResponse(BaseModel):
    """History response model."""
    session_id: str
    messages: list
    message_count: int

# ============================================================================
# Authentication
# ============================================================================

def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract and validate user from JWT token."""
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]
    payload = verify_jwt_token(token)

    if not payload:
        return None

    return payload.get("username")

def get_token_from_header(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract token from Authorization header."""
    if not authorization:
        return None
    parts = authorization.split()
    return parts[1] if len(parts) == 2 else None

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Jarvis Web UI - Phase 2",
    description="Web interface integrated with Pure A2A architecture",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ============================================================================
# Routes
# ============================================================================

@app.get("/")
async def root():
    """Redirect to login page."""
    return FileResponse(os.path.join(static_dir, "login.html"))

@app.get("/login.html")
async def login_page():
    """Serve login page."""
    return FileResponse(os.path.join(static_dir, "login.html"))

@app.get("/chat.html")
async def chat_page():
    """Serve chat page."""
    return FileResponse(os.path.join(static_dir, "chat.html"))

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "web_ui_phase2"}

# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Optional[str] = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Handle chat requests with Jarvis agent.

    Integrates with Phase 2 Pure A2A architecture using JarvisOrchestrator.
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    try:
        # Get JWT token
        token = get_token_from_header(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Create orchestrator with JWT (handles auth, session, routing)
        orchestrator = JarvisOrchestrator(jwt_token=token)

        # Handle query (automatically manages session via registry)
        response_text = orchestrator.handle_query(request.message)

        # Get session ID
        session_id = orchestrator.session_id

        # Close orchestrator
        orchestrator.close()

        return ChatResponse(
            response=response_text,
            session_id=session_id
        )

    except PermissionError as e:
        # User tried to access unauthorized data
        # Return error as part of response (not HTTP error)
        return ChatResponse(
            response=str(e),
            session_id=orchestrator.session_id if 'orchestrator' in locals() else ""
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )

@app.get("/api/history", response_model=HistoryResponse)
async def get_history(
    current_user: Optional[str] = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """Get conversation history for current user's active session."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        token = get_token_from_header(authorization)

        # Create orchestrator to get session info
        orchestrator = JarvisOrchestrator(jwt_token=token)
        session_id = orchestrator.session_id

        # Get messages from registry
        session_client = RegistrySessionClient()
        messages = session_client.get_messages(session_id)

        orchestrator.close()

        # Format messages
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        return HistoryResponse(
            session_id=session_id,
            messages=formatted_messages,
            message_count=len(formatted_messages)
        )

    except Exception as e:
        # Return empty history on error
        return HistoryResponse(
            session_id="",
            messages=[],
            message_count=0
        )

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 70)
    print("Starting Jarvis Web UI Server - Phase 2")
    print("=" * 70)
    print(f"Service: Web Chat Interface (Pure A2A)")
    print(f"Port: 9999")
    print(f"URL: http://localhost:9999")
    print(f"Login: http://localhost:9999/login.html")
    print(f"Chat: http://localhost:9999/chat.html (after login)")
    print()
    print("Integrated Services:")
    print("  - Auth Service (9998)")
    print("  - Registry Service (8003)")
    print("  - TicketsAgent (8080)")
    print("  - FinOpsAgent (8081)")
    print("  - OxygenAgent (8082)")
    print("=" * 70 + "\n")

    uvicorn.run(app, host="localhost", port=9999)
```

---

## Testing Checklist

### Phase 1 Testing:

- [ ] **Login:**
  - [ ] Login with vishal/password123
  - [ ] Login with happy/password123
  - [ ] Login with alex/password123
  - [ ] Login with admin/admin123
  - [ ] Test invalid credentials

- [ ] **Chat:**
  - [ ] Send "show my tickets" as vishal
  - [ ] Verify vishal's tickets shown
  - [ ] Send "show my courses" as happy
  - [ ] Verify happy's courses shown

- [ ] **Security:**
  - [ ] As happy, try "show vishal's tickets"
  - [ ] Verify access denied error
  - [ ] As admin, try "show vishal's tickets"
  - [ ] Verify vishal's tickets shown (admin privilege)

- [ ] **Session Persistence:**
  - [ ] Login, send 3 messages, logout
  - [ ] Login again
  - [ ] Verify conversation history loaded
  - [ ] Verify "Welcome back!" message

- [ ] **Suggestions:**
  - [ ] Verify suggestions appear
  - [ ] Click suggestion
  - [ ] Verify it fills input field
  - [ ] Send message
  - [ ] Verify suggestions update

### Phase 2 Testing:

- [ ] **AI Suggestions:**
  - [ ] Verify suggestions are contextual
  - [ ] Test fallback to simple suggestions on error

- [ ] **Token Refresh:**
  - [ ] Wait for token near expiry
  - [ ] Verify auto-refresh works
  - [ ] Verify no interruption in chat

- [ ] **Multi-Tab:**
  - [ ] Open chat in 2 tabs
  - [ ] Send message in tab 1
  - [ ] Verify message appears in tab 2

- [ ] **Markdown:**
  - [ ] Ask "explain this in markdown with code"
  - [ ] Verify proper rendering of code blocks
  - [ ] Verify lists render correctly

---

## Bottom Line

### Phase 1 (Minimal Viable):
- **Time:** 4-5 hours
- **Complexity:** ⭐⭐⭐ Medium
- **Risk:** Low
- **ROI:** High
- **Verdict:** ✅ **Recommended - Do This First**

### Phase 2 (Full-Featured):
- **Time:** +4-5 hours (8-10 total)
- **Complexity:** ⭐⭐⭐⭐ Medium-High
- **Risk:** Medium
- **ROI:** Medium
- **Verdict:** ⚠️ **Optional - Evaluate After Phase 1**

---

## Recommendation

1. **Start with Phase 1** (4-5 hours focused work)
2. **Test thoroughly** with all users
3. **Deploy and use** for a few days
4. **Then decide** if Phase 2 features are needed

**Phase 1 gives you 90% of the value for 50% of the effort.**

The WebUI integration is **definitely doable** - it's mostly plumbing existing working components together, not building new features from scratch.
