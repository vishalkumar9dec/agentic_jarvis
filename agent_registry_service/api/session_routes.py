"""
REST API endpoints for Session management.

This module provides FastAPI routes for:
- Creating and retrieving sessions
- Tracking agent invocations
- Managing conversation history
- Updating session status
- Deleting sessions
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status

from agent_registry_service.sessions.session_manager import SessionManager, SessionManagerError
from agent_registry_service.api.models import (
    CreateSessionRequest,
    CreateSessionResponse,
    AddMessageRequest,
    TrackInvocationRequest,
    UpdateSessionStatusRequest,
    SessionResponse,
    ConversationMessage,
    AgentInvocation,
    SuccessResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(prefix="/sessions", tags=["Session Management"])

# Global session manager instance (will be injected via dependency)
_session_manager_instance: Optional[SessionManager] = None


def set_session_manager(session_manager: SessionManager):
    """Set the global session manager instance."""
    global _session_manager_instance
    _session_manager_instance = session_manager


def get_session_manager() -> SessionManager:
    """Dependency to get the session manager."""
    if _session_manager_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session manager not initialized"
        )
    return _session_manager_instance


# =============================================================================
# API Endpoints
# =============================================================================

@router.post(
    "",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
    description="Create a new conversation session for a user"
)
async def create_session(
    request: CreateSessionRequest,
    session_manager: SessionManager = Depends(get_session_manager)
) -> CreateSessionResponse:
    """
    Create a new session.

    **Request Body:**
    - `user_id`: User identifier (required)
    - `metadata`: Optional session metadata (e.g., client info, features)

    **Returns:**
    - Session ID, user ID, creation timestamp, and initial status

    **Example:**
    ```
    POST /sessions
    {
        "user_id": "alice",
        "metadata": {"client": "web", "version": "1.0"}
    }
    ```
    """
    try:
        session_id = session_manager.create_session(
            request.user_id,
            metadata=request.metadata
        )

        # Get the created session
        session = session_manager.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session created but could not be retrieved"
            )

        logger.info(f"Created session {session_id} for user {request.user_id}")

        return CreateSessionResponse(
            session_id=session_id,
            user_id=session["user_id"],
            created_at=session["created_at"],
            status=session["status"]
        )

    except SessionManagerError as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session data",
    description="Retrieve complete session information including history and invocations",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"}
    }
)
async def get_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
) -> SessionResponse:
    """
    Get complete session data.

    **Path Parameters:**
    - `session_id`: Session identifier (UUID)

    **Returns:**
    - Complete session data including:
      - Session metadata
      - Conversation history (all messages)
      - Agent invocations (all agent calls)
      - Current context (last agent called)

    **Raises:**
    - 404: Session not found
    """
    try:
        session = session_manager.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found"
            )

        # Convert conversation history to Pydantic models
        conversation_history = [
            ConversationMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"]
            )
            for msg in session["conversation_history"]
        ]

        # Convert agent invocations to Pydantic models
        agents_invoked = [
            AgentInvocation(
                agent_name=inv["agent_name"],
                query=inv["query"],
                response=inv["response"],
                success=bool(inv["success"]),  # Convert SQLite int to bool
                duration_ms=inv["duration_ms"],
                error_message=inv["error_message"],
                timestamp=inv["timestamp"]
            )
            for inv in session["agents_invoked"]
        ]

        return SessionResponse(
            session_id=session["session_id"],
            user_id=session["user_id"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            status=session["status"],
            metadata=session.get("metadata"),
            conversation_history=conversation_history,
            agents_invoked=agents_invoked,
            last_agent_called=session.get("last_agent_called")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.post(
    "/{session_id}/invocations",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Track agent invocation",
    description="Record an agent invocation with performance metrics",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"}
    }
)
async def track_invocation(
    session_id: str,
    request: TrackInvocationRequest,
    session_manager: SessionManager = Depends(get_session_manager)
) -> SuccessResponse:
    """
    Track an agent invocation.

    **Path Parameters:**
    - `session_id`: Session identifier

    **Request Body:**
    - `agent_name`: Name of agent invoked
    - `query`: User query sent to agent
    - `response`: Agent response (optional)
    - `success`: Whether invocation succeeded (default: true)
    - `duration_ms`: Execution time in milliseconds (optional)
    - `error_message`: Error message if failed (optional)

    **Returns:**
    - Success confirmation

    **Raises:**
    - 404: Session not found
    """
    try:
        # Verify session exists
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found"
            )

        # Track the invocation
        session_manager.track_agent_invocation(
            session_id,
            request.agent_name,
            request.query,
            response=request.response,
            success=request.success,
            duration_ms=request.duration_ms,
            error_message=request.error_message
        )

        logger.info(f"Tracked invocation of {request.agent_name} for session {session_id}")

        return SuccessResponse(
            status="tracked",
            message=f"Agent invocation tracked for session '{session_id}'"
        )

    except HTTPException:
        raise
    except SessionManagerError as e:
        logger.error(f"Error tracking invocation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track invocation: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error tracking invocation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track invocation: {str(e)}"
        )


@router.post(
    "/{session_id}/history",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add message to conversation",
    description="Add a message to the conversation history",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"}
    }
)
async def add_message(
    session_id: str,
    request: AddMessageRequest,
    session_manager: SessionManager = Depends(get_session_manager)
) -> SuccessResponse:
    """
    Add a message to conversation history.

    **Path Parameters:**
    - `session_id`: Session identifier

    **Request Body:**
    - `role`: Message role (user, assistant, or system)
    - `content`: Message content

    **Returns:**
    - Success confirmation

    **Raises:**
    - 404: Session not found
    - 400: Invalid role
    """
    try:
        # Verify session exists
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found"
            )

        # Add message to history
        session_manager.add_to_history(
            session_id,
            request.role,
            request.content
        )

        logger.debug(f"Added {request.role} message to session {session_id}")

        return SuccessResponse(
            status="added",
            message=f"Message added to session '{session_id}'"
        )

    except HTTPException:
        raise
    except SessionManagerError as e:
        # Handle invalid role error
        if "Invalid role" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        logger.error(f"Error adding message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error adding message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )


@router.patch(
    "/{session_id}/status",
    response_model=SuccessResponse,
    summary="Update session status",
    description="Update the status of a session (active, completed, expired)",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        400: {"model": ErrorResponse, "description": "Invalid status"}
    }
)
async def update_session_status(
    session_id: str,
    request: UpdateSessionStatusRequest,
    session_manager: SessionManager = Depends(get_session_manager)
) -> SuccessResponse:
    """
    Update session status.

    **Path Parameters:**
    - `session_id`: Session identifier

    **Request Body:**
    - `status`: New status (active, completed, or expired)

    **Returns:**
    - Success confirmation

    **Raises:**
    - 404: Session not found
    - 400: Invalid status value
    """
    try:
        success = session_manager.update_session_status(session_id, request.status)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found"
            )

        logger.info(f"Updated session {session_id} status to {request.status}")

        return SuccessResponse(
            status="updated",
            message=f"Session status updated to '{request.status}'"
        )

    except HTTPException:
        raise
    except SessionManagerError as e:
        # Handle invalid status error
        if "Invalid status" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        logger.error(f"Error updating session status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session status: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating session status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session status: {str(e)}"
        )


@router.delete(
    "/{session_id}",
    response_model=SuccessResponse,
    summary="Delete session",
    description="Delete a session and all associated data",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"}
    }
)
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
) -> SuccessResponse:
    """
    Delete a session.

    **Path Parameters:**
    - `session_id`: Session identifier

    **Returns:**
    - Success confirmation

    **Raises:**
    - 404: Session not found

    **Warning:**
    This permanently deletes the session and all associated data including
    conversation history, agent invocations, and context. This action cannot
    be undone.
    """
    try:
        success = session_manager.delete_session(session_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found"
            )

        logger.info(f"Deleted session {session_id}")

        return SuccessResponse(
            status="deleted",
            message=f"Session '{session_id}' deleted successfully"
        )

    except HTTPException:
        raise
    except SessionManagerError as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )
