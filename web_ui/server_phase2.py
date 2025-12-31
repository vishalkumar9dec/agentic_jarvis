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
from typing import Optional, List, Dict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.jwt_utils import verify_jwt_token
from jarvis_agent.main_with_registry import JarvisOrchestrator
from jarvis_agent.session_client import SessionClient

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
    messages: List[Dict]
    message_count: int


# ============================================================================
# Authentication
# ============================================================================

def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Extract and validate user from JWT token.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Username if valid token, None otherwise
    """
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
    """
    Extract token from Authorization header.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        JWT token string if valid format, None otherwise
    """
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
def root():
    """Redirect to login page."""
    return FileResponse(os.path.join(static_dir, "login.html"))


@app.get("/login.html")
def login_page():
    """Serve login page."""
    return FileResponse(os.path.join(static_dir, "login.html"))


@app.get("/chat.html")
def chat_page():
    """Serve chat page."""
    return FileResponse(os.path.join(static_dir, "chat.html"))


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "web_ui_phase2", "port": 9999}


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: Optional[str] = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Handle chat requests with Jarvis agent.

    Integrates with Phase 2 Pure A2A architecture using JarvisOrchestrator.
    Automatically manages:
    - User authentication via JWT
    - Session persistence via Registry Service
    - Query routing to A2A agents
    - Security access control

    Args:
        request: ChatRequest with user message
        current_user: Authenticated username from JWT token
        authorization: Authorization header

    Returns:
        ChatResponse with agent's reply and session ID

    Raises:
        HTTPException: 401 if not authenticated, 500 on error
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    orchestrator = None
    try:
        # Get JWT token
        token = get_token_from_header(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Create orchestrator with JWT (handles auth, session, routing)
        orchestrator = JarvisOrchestrator(jwt_token=token)

        # Get or create session for this user
        session_id = orchestrator.get_or_create_session(orchestrator.user_id)

        # Handle query (pass session_id to maintain context)
        response_text = orchestrator.handle_query(
            query=request.message,
            session_id=session_id
        )

        # Close orchestrator
        orchestrator.close()

        return ChatResponse(
            response=response_text,
            session_id=session_id
        )

    except PermissionError as e:
        # User tried to access unauthorized data
        # Return error as part of response (not HTTP error)
        error_session_id = session_id if 'session_id' in locals() else ""
        if orchestrator:
            orchestrator.close()

        return ChatResponse(
            response=str(e),
            session_id=error_session_id
        )

    except Exception as e:
        if orchestrator:
            orchestrator.close()

        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@app.get("/api/history", response_model=HistoryResponse)
def get_history(
    current_user: Optional[str] = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Get conversation history for current user's active session.

    Fetches messages from the Registry Service for the user's current session.

    Args:
        current_user: Authenticated username from JWT token
        authorization: Authorization header

    Returns:
        HistoryResponse with session ID, messages, and message count

    Raises:
        HTTPException: 401 if not authenticated
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    orchestrator = None
    try:
        token = get_token_from_header(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Create orchestrator to get user info
        orchestrator = JarvisOrchestrator(jwt_token=token)

        # Get or create session for this user
        session_id = orchestrator.get_or_create_session(orchestrator.user_id)

        # Get messages from registry
        session_client = SessionClient()
        messages = session_client.get_conversation_history(session_id)

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
        if orchestrator:
            orchestrator.close()

        # Return empty history on error (don't fail the UI)
        return HistoryResponse(
            session_id="",
            messages=[],
            message_count=0
        )


@app.post("/api/auth/refresh")
def refresh_token(
    current_user: Optional[str] = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Refresh JWT token before expiration.

    Allows users to continue their session without interruption by
    refreshing the token before it expires.
    """
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
        new_token = create_jwt_token(
            username=user_info["username"],
            user_id=user_info["user_id"],
            role=user_info["role"]
        )

        return {
            "access_token": new_token,
            "token_type": "bearer"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing token: {str(e)}"
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
