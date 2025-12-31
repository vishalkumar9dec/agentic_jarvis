"""
Authentication Service
Provides JWT authentication endpoints for Jarvis.
Port: 9998
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.jwt_utils import create_jwt_token, verify_jwt_token
from auth.user_service import authenticate_user, get_user_info


# ============================================================================
# Request/Response Models
# ============================================================================

class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """OAuth 2.0 compatible login response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours in seconds
    user: Optional[Dict[str, Any]] = None


class UserInfoResponse(BaseModel):
    """User info response model."""
    success: bool
    user: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Jarvis Authentication Service",
    description="JWT authentication service for Agentic Jarvis",
    version="1.0.0"
)

# Add CORS middleware for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Jarvis Authentication Service",
        "version": "2.0.0",
        "status": "running",
        "oauth_compatible": True,
        "endpoints": {
            "login": "POST /auth/login",
            "verify": "GET /auth/verify",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "auth"}


@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.

    Args:
        request: LoginRequest with username and password

    Returns:
        LoginResponse with JWT token and user info if successful

    Raises:
        HTTPException: 401 if authentication fails
    """
    # Authenticate user
    user = authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    token = create_jwt_token(user["username"], user["user_id"], user["role"])

    # Return OAuth 2.0 compatible response
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=86400,  # 24 hours
        user=user
    )


@app.get("/auth/verify")
async def verify_token_endpoint(token: str):
    """
    Verify JWT token and return payload.

    Used by orchestrator to validate tokens.

    Args:
        token: JWT token to verify

    Returns:
        Token payload if valid

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    payload = verify_jwt_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "valid": True,
        "payload": payload
    }


@app.get("/auth/user/{username}", response_model=UserInfoResponse)
async def get_user(username: str):
    """
    Get user information by username.

    Args:
        username: Username to look up

    Returns:
        UserInfoResponse with user info if found

    Raises:
        HTTPException: 404 if user not found
    """
    user = get_user_info(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    return UserInfoResponse(
        success=True,
        user=user
    )


@app.get("/auth/demo-users")
async def demo_users():
    """
    Get list of demo user accounts.

    Returns:
        List of demo usernames and their roles
    """
    return {
        "demo_users": [
            {
                "username": "vishal",
                "password": "password123",
                "role": "developer",
                "description": "Developer with 2 tickets, AWS/Terraform courses, 1 pending exam"
            },
            {
                "username": "alex",
                "password": "password123",
                "role": "devops",
                "description": "DevOps engineer with 2 tickets, Kubernetes courses, 2 pending exams"
            },
            {
                "username": "sarah",
                "password": "password123",
                "role": "data_scientist",
                "description": "Data scientist with 1 ticket, ML/Data Science courses"
            }
        ]
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 70)
    print("Starting Jarvis Authentication Service")
    print("=" * 70)
    print(f"Service: Authentication API")
    print(f"Port: 9998")
    print(f"URL: http://localhost:9998")
    print(f"Docs: http://localhost:9998/docs")
    print(f"Health: http://localhost:9998/health")
    print("=" * 70 + "\n")

    uvicorn.run(app, host="localhost", port=9998)
