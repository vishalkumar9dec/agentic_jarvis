"""
Web UI Server for Jarvis
Serves the simple web chat interface with JWT authentication.
Port: 9999
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.jwt_utils import verify_jwt_token

# ============================================================================
# Models
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: str
    user_id: str


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: str


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


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Jarvis Web UI",
    description="Simple web chat interface for Jarvis with JWT authentication",
    version="1.0.0"
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
    return {"status": "healthy", "service": "web_ui"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Optional[str] = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Handle chat requests with Jarvis agent.

    Args:
        request: ChatRequest with message, session_id, user_id
        current_user: Authenticated username from JWT token
        authorization: Authorization header with Bearer token

    Returns:
        ChatResponse with agent's reply

    Raises:
        HTTPException: 401 if not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    try:
        # Import here to avoid circular dependencies
        from jarvis_agent.agent import root_agent
        from jarvis_agent.auth_context import set_bearer_token
        from google.adk.runners import Runner
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.genai import types

        # Extract bearer token for authentication
        token = authorization.split()[1] if authorization and len(authorization.split()) == 2 else None

        # Set bearer token in context for toolbox clients
        set_bearer_token(token)

        # Create run config with bearer token in custom metadata
        from google.adk.runners import RunConfig
        run_config = RunConfig(custom_metadata={"bearer_token": token}) if token else None

        # Create or get session service (in production, use a shared instance)
        # For simplicity, creating per-request (Phase 2 has no persistence)
        session_service = InMemorySessionService()

        app_name = "jarvis"

        # Try to create session (ignore if exists)
        try:
            session_service.create_session_sync(
                app_name=app_name,
                user_id=request.user_id,
                session_id=request.session_id
            )

            # Initialize user context for new session
            runner = Runner(
                app_name=app_name,
                agent=root_agent,
                session_service=session_service
            )

            # Send initial context message
            init_message = types.Content(
                role="user",
                parts=[types.Part(text=f"[System: Authenticated user is '{current_user}'. Use user-specific tools when appropriate (get_my_tickets, get_my_courses, etc.). For this session, current_user={current_user}]")]
            )

            for _ in runner.run(
                user_id=request.user_id,
                session_id=request.session_id,
                new_message=init_message,
                run_config=run_config
            ):
                pass

        except Exception:
            # Session already exists, create runner
            runner = Runner(
                app_name=app_name,
                agent=root_agent,
                session_service=session_service
            )

        # Process user message
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=request.message)]
        )

        # Collect response
        response_text = ""
        for event in runner.run(
            user_id=request.user_id,
            session_id=request.session_id,
            new_message=new_message,
            run_config=run_config
        ):
            if event.content and event.content.parts and event.author != "user":
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text

        if not response_text:
            response_text = "I apologize, but I couldn't process that request. Please try again."

        return ChatResponse(
            response=response_text,
            session_id=request.session_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 70)
    print("Starting Jarvis Web UI Server")
    print("=" * 70)
    print(f"Service: Web Chat Interface")
    print(f"Port: 9999")
    print(f"URL: http://localhost:9999")
    print(f"Login: http://localhost:9999/login.html")
    print(f"Chat: http://localhost:9999/chat.html (after login)")
    print("=" * 70 + "\n")

    uvicorn.run(app, host="localhost", port=9999)
