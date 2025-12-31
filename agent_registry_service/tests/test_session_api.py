"""
Integration tests for Session REST API.

Tests all endpoints using FastAPI TestClient:
- Create session
- Get session
- Track invocations
- Add messages to history
- Update session status
- Delete session
"""

import os
import pytest
import tempfile
import shutil
from fastapi import FastAPI
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent_registry_service.sessions.session_manager import SessionManager
from agent_registry_service.api.session_routes import router, set_session_manager


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test databases."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def db_path(temp_dir):
    """Create path for test database."""
    return os.path.join(temp_dir, "test_sessions.db")


@pytest.fixture
def session_manager(db_path):
    """Create SessionManager instance."""
    return SessionManager(db_path, auto_init=True)


@pytest.fixture
def app(session_manager):
    """Create FastAPI test application."""
    app = FastAPI()
    app.include_router(router)
    set_session_manager(session_manager)
    return app


@pytest.fixture
def client(app):
    """Create TestClient."""
    return TestClient(app)


@pytest.fixture
def sample_session(client):
    """Create a sample session."""
    response = client.post("/sessions", json={"user_id": "test_user"})
    assert response.status_code == 201
    return response.json()["session_id"]


# =============================================================================
# Test Create Session Endpoint
# =============================================================================

class TestCreateSession:
    """Test POST /sessions endpoint."""

    def test_create_session_basic(self, client):
        """Test creating a basic session."""
        response = client.post("/sessions", json={"user_id": "alice"})

        assert response.status_code == 201
        data = response.json()

        assert "session_id" in data
        assert data["user_id"] == "alice"
        assert data["status"] == "active"
        assert "created_at" in data

    def test_create_session_with_metadata(self, client):
        """Test creating a session with metadata."""
        request_data = {
            "user_id": "bob",
            "metadata": {
                "client": "web",
                "version": "1.0",
                "features": ["chat", "voice"]
            }
        }

        response = client.post("/sessions", json=request_data)

        assert response.status_code == 201
        data = response.json()

        assert data["user_id"] == "bob"
        # Verify session was created with metadata
        session_response = client.get(f"/sessions/{data['session_id']}")
        session_data = session_response.json()
        assert session_data["metadata"] == request_data["metadata"]

    def test_create_session_empty_user_id(self, client):
        """Test creating a session with empty user_id."""
        response = client.post("/sessions", json={"user_id": ""})

        # Pydantic validation should fail
        assert response.status_code == 422

    def test_create_session_missing_user_id(self, client):
        """Test creating a session without user_id."""
        response = client.post("/sessions", json={})

        assert response.status_code == 422


# =============================================================================
# Test Get Session Endpoint
# =============================================================================

class TestGetSession:
    """Test GET /sessions/{session_id} endpoint."""

    def test_get_session_basic(self, client, sample_session):
        """Test getting an existing session."""
        response = client.get(f"/sessions/{sample_session}")

        assert response.status_code == 200
        data = response.json()

        assert data["session_id"] == sample_session
        assert data["user_id"] == "test_user"
        assert data["status"] == "active"
        assert data["conversation_history"] == []
        assert data["agents_invoked"] == []
        assert data["last_agent_called"] is None

    def test_get_session_with_history(self, client, sample_session):
        """Test getting a session with conversation history."""
        # Add messages
        client.post(
            f"/sessions/{sample_session}/history",
            json={"role": "user", "content": "Hello"}
        )
        client.post(
            f"/sessions/{sample_session}/history",
            json={"role": "assistant", "content": "Hi there!"}
        )

        response = client.get(f"/sessions/{sample_session}")

        assert response.status_code == 200
        data = response.json()

        assert len(data["conversation_history"]) == 2
        assert data["conversation_history"][0]["role"] == "user"
        assert data["conversation_history"][0]["content"] == "Hello"
        assert data["conversation_history"][1]["role"] == "assistant"

    def test_get_session_with_invocations(self, client, sample_session):
        """Test getting a session with agent invocations."""
        # Track an invocation
        client.post(
            f"/sessions/{sample_session}/invocations",
            json={
                "agent_name": "test_agent",
                "query": "test query",
                "response": "test response",
                "success": True,
                "duration_ms": 100
            }
        )

        response = client.get(f"/sessions/{sample_session}")

        assert response.status_code == 200
        data = response.json()

        assert len(data["agents_invoked"]) == 1
        assert data["agents_invoked"][0]["agent_name"] == "test_agent"
        assert data["agents_invoked"][0]["success"] is True
        assert data["agents_invoked"][0]["duration_ms"] == 100

    def test_get_nonexistent_session(self, client):
        """Test getting a non-existent session returns 404."""
        response = client.get("/sessions/nonexistent-id")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


# =============================================================================
# Test Track Invocation Endpoint
# =============================================================================

class TestTrackInvocation:
    """Test POST /sessions/{session_id}/invocations endpoint."""

    def test_track_successful_invocation(self, client, sample_session):
        """Test tracking a successful agent invocation."""
        request_data = {
            "agent_name": "tickets_agent",
            "query": "Show my tickets",
            "response": "You have 3 open tickets",
            "success": True,
            "duration_ms": 150
        }

        response = client.post(
            f"/sessions/{sample_session}/invocations",
            json=request_data
        )

        assert response.status_code == 201
        data = response.json()

        assert data["status"] == "tracked"

        # Verify it was tracked
        session_response = client.get(f"/sessions/{sample_session}")
        session_data = session_response.json()

        assert len(session_data["agents_invoked"]) == 1
        inv = session_data["agents_invoked"][0]
        assert inv["agent_name"] == "tickets_agent"
        assert inv["query"] == "Show my tickets"
        assert inv["success"] is True

    def test_track_failed_invocation(self, client, sample_session):
        """Test tracking a failed agent invocation."""
        request_data = {
            "agent_name": "broken_agent",
            "query": "Do something",
            "success": False,
            "error_message": "Agent timeout"
        }

        response = client.post(
            f"/sessions/{sample_session}/invocations",
            json=request_data
        )

        assert response.status_code == 201

        # Verify it was tracked
        session_response = client.get(f"/sessions/{sample_session}")
        session_data = session_response.json()

        inv = session_data["agents_invoked"][0]
        assert inv["success"] is False
        assert inv["error_message"] == "Agent timeout"

    def test_track_invocation_nonexistent_session(self, client):
        """Test tracking invocation for non-existent session."""
        request_data = {
            "agent_name": "test_agent",
            "query": "test",
            "success": True
        }

        response = client.post(
            "/sessions/nonexistent/invocations",
            json=request_data
        )

        assert response.status_code == 404


# =============================================================================
# Test Add Message Endpoint
# =============================================================================

class TestAddMessage:
    """Test POST /sessions/{session_id}/history endpoint."""

    def test_add_user_message(self, client, sample_session):
        """Test adding a user message."""
        request_data = {
            "role": "user",
            "content": "What is the weather?"
        }

        response = client.post(
            f"/sessions/{sample_session}/history",
            json=request_data
        )

        assert response.status_code == 201
        data = response.json()

        assert data["status"] == "added"

        # Verify message was added
        session_response = client.get(f"/sessions/{sample_session}")
        session_data = session_response.json()

        assert len(session_data["conversation_history"]) == 1
        msg = session_data["conversation_history"][0]
        assert msg["role"] == "user"
        assert msg["content"] == "What is the weather?"

    def test_add_assistant_message(self, client, sample_session):
        """Test adding an assistant message."""
        request_data = {
            "role": "assistant",
            "content": "It's sunny and 72°F"
        }

        response = client.post(
            f"/sessions/{sample_session}/history",
            json=request_data
        )

        assert response.status_code == 201

    def test_add_system_message(self, client, sample_session):
        """Test adding a system message."""
        request_data = {
            "role": "system",
            "content": "Session started"
        }

        response = client.post(
            f"/sessions/{sample_session}/history",
            json=request_data
        )

        assert response.status_code == 201

    def test_add_invalid_role(self, client, sample_session):
        """Test adding message with invalid role."""
        request_data = {
            "role": "invalid_role",
            "content": "test"
        }

        response = client.post(
            f"/sessions/{sample_session}/history",
            json=request_data
        )

        # Pydantic validation should fail
        assert response.status_code == 422

    def test_add_message_nonexistent_session(self, client):
        """Test adding message to non-existent session."""
        request_data = {
            "role": "user",
            "content": "test"
        }

        response = client.post(
            "/sessions/nonexistent/history",
            json=request_data
        )

        assert response.status_code == 404

    def test_add_multiple_messages_order(self, client, sample_session):
        """Test that messages maintain order."""
        messages = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Third"}
        ]

        for msg in messages:
            client.post(f"/sessions/{sample_session}/history", json=msg)

        # Verify order
        session_response = client.get(f"/sessions/{sample_session}")
        session_data = session_response.json()

        assert len(session_data["conversation_history"]) == 3
        for i, msg in enumerate(messages):
            assert session_data["conversation_history"][i]["content"] == msg["content"]


# =============================================================================
# Test Update Session Status Endpoint
# =============================================================================

class TestUpdateSessionStatus:
    """Test PATCH /sessions/{session_id}/status endpoint."""

    def test_update_status_to_completed(self, client, sample_session):
        """Test updating status to completed."""
        request_data = {"status": "completed"}

        response = client.patch(
            f"/sessions/{sample_session}/status",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "updated"

        # Verify status was updated
        session_response = client.get(f"/sessions/{sample_session}")
        session_data = session_response.json()

        assert session_data["status"] == "completed"

    def test_update_status_to_expired(self, client, sample_session):
        """Test updating status to expired."""
        request_data = {"status": "expired"}

        response = client.patch(
            f"/sessions/{sample_session}/status",
            json=request_data
        )

        assert response.status_code == 200

        # Verify
        session_response = client.get(f"/sessions/{sample_session}")
        session_data = session_response.json()

        assert session_data["status"] == "expired"

    def test_update_status_invalid(self, client, sample_session):
        """Test updating to invalid status."""
        request_data = {"status": "invalid_status"}

        response = client.patch(
            f"/sessions/{sample_session}/status",
            json=request_data
        )

        # Pydantic validation should fail
        assert response.status_code == 422

    def test_update_status_nonexistent_session(self, client):
        """Test updating status of non-existent session."""
        request_data = {"status": "completed"}

        response = client.patch(
            "/sessions/nonexistent/status",
            json=request_data
        )

        assert response.status_code == 404


# =============================================================================
# Test Delete Session Endpoint
# =============================================================================

class TestDeleteSession:
    """Test DELETE /sessions/{session_id} endpoint."""

    def test_delete_session(self, client, sample_session):
        """Test deleting a session."""
        response = client.delete(f"/sessions/{sample_session}")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "deleted"

        # Verify session is gone
        get_response = client.get(f"/sessions/{sample_session}")
        assert get_response.status_code == 404

    def test_delete_session_with_data(self, client, sample_session):
        """Test deleting a session with history and invocations."""
        # Add some data
        client.post(
            f"/sessions/{sample_session}/history",
            json={"role": "user", "content": "test"}
        )
        client.post(
            f"/sessions/{sample_session}/invocations",
            json={"agent_name": "test", "query": "test", "success": True}
        )

        # Delete session
        response = client.delete(f"/sessions/{sample_session}")

        assert response.status_code == 200

        # Verify it's gone
        get_response = client.get(f"/sessions/{sample_session}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_session(self, client):
        """Test deleting a non-existent session."""
        response = client.delete("/sessions/nonexistent")

        assert response.status_code == 404


# =============================================================================
# Test Error Handling
# =============================================================================

class TestErrorHandling:
    """Test error handling across endpoints."""

    def test_invalid_json_payload(self, client):
        """Test sending invalid JSON."""
        response = client.post(
            "/sessions",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_missing_required_fields(self, client, sample_session):
        """Test request with missing required fields."""
        # Add message without role
        response = client.post(
            f"/sessions/{sample_session}/history",
            json={"content": "test"}
        )

        assert response.status_code == 422


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
