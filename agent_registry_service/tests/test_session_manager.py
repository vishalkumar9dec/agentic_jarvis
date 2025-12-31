"""
Comprehensive unit tests for SessionManager.

Tests cover:
- Session creation and retrieval
- Agent invocation tracking
- Conversation history management
- Context tracking and updates
- Session status management
- Session cleanup
- Thread safety and concurrent access
- Error handling and edge cases
"""

import os
import pytest
import tempfile
import shutil
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import List

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent_registry_service.sessions.session_manager import SessionManager, SessionManagerError
from agent_registry_service.sessions.db_init import get_connection, verify_schema, DatabaseInitError


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
def populated_session(session_manager):
    """Create a session with some data."""
    session_id = session_manager.create_session(
        "test_user",
        metadata={"source": "test"}
    )

    # Add conversation history
    session_manager.add_to_history(session_id, "user", "Hello")
    session_manager.add_to_history(session_id, "assistant", "Hi there!")

    # Track an agent invocation
    session_manager.track_agent_invocation(
        session_id,
        "test_agent",
        "Hello",
        "Hi there!",
        success=True,
        duration_ms=100
    )

    # Update context
    session_manager.update_context(
        session_id,
        "test_agent",
        "Hello",
        "Hi there!"
    )

    return session_id


# =============================================================================
# Test SessionManager Initialization
# =============================================================================

class TestSessionManagerInit:
    """Test SessionManager initialization."""

    def test_init_creates_database(self, db_path):
        """Test that initialization creates database."""
        manager = SessionManager(db_path, auto_init=True)

        assert os.path.exists(db_path)

        # Verify schema
        conn = get_connection(db_path)
        assert verify_schema(conn) is True
        conn.close()

    def test_init_without_auto_init(self, db_path):
        """Test initialization without auto_init."""
        manager = SessionManager(db_path, auto_init=False)

        # Database file may not exist yet
        assert manager.db_path == db_path

    def test_multiple_managers_same_db(self, db_path):
        """Test multiple managers can access same database."""
        manager1 = SessionManager(db_path)
        manager2 = SessionManager(db_path)

        session_id = manager1.create_session("user1")

        # Should be retrievable by second manager
        session = manager2.get_session(session_id)
        assert session is not None
        assert session["user_id"] == "user1"


# =============================================================================
# Test Session Creation and Retrieval
# =============================================================================

class TestSessionCreationAndRetrieval:
    """Test session creation and retrieval operations."""

    def test_create_session_basic(self, session_manager):
        """Test basic session creation."""
        session_id = session_manager.create_session("alice")

        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID format

    def test_create_session_with_metadata(self, session_manager):
        """Test session creation with metadata."""
        metadata = {
            "client": "web",
            "version": "1.0",
            "features": ["chat", "voice"]
        }

        session_id = session_manager.create_session("bob", metadata=metadata)
        session = session_manager.get_session(session_id)

        assert session["metadata"] == metadata

    def test_get_session_complete_data(self, session_manager, populated_session):
        """Test getting complete session data."""
        session = session_manager.get_session(populated_session)

        # Verify all fields present
        assert "session_id" in session
        assert "user_id" in session
        assert "created_at" in session
        assert "updated_at" in session
        assert "status" in session
        assert "metadata" in session
        assert "conversation_history" in session
        assert "agents_invoked" in session
        assert "last_agent_called" in session

        # Verify data
        assert session["user_id"] == "test_user"
        assert session["status"] == "active"
        assert len(session["conversation_history"]) == 2
        assert len(session["agents_invoked"]) == 1
        assert session["last_agent_called"] == "test_agent"

    def test_get_nonexistent_session(self, session_manager):
        """Test getting non-existent session returns None."""
        session = session_manager.get_session("nonexistent-id")

        assert session is None

    def test_session_timestamps(self, session_manager):
        """Test that session has valid timestamps."""
        session_id = session_manager.create_session("charlie")
        session = session_manager.get_session(session_id)

        # Verify timestamps exist and are valid ISO format
        assert session["created_at"] is not None
        assert session["updated_at"] is not None

        # Should be parseable as datetime
        created = datetime.fromisoformat(session["created_at"].replace('Z', '+00:00'))
        updated = datetime.fromisoformat(session["updated_at"].replace('Z', '+00:00'))

        assert isinstance(created, datetime)
        assert isinstance(updated, datetime)


# =============================================================================
# Test Session Status Management
# =============================================================================

class TestSessionStatus:
    """Test session status management."""

    def test_update_status_active_to_completed(self, session_manager):
        """Test updating status from active to completed."""
        session_id = session_manager.create_session("user1")

        result = session_manager.update_session_status(session_id, "completed")

        assert result is True

        session = session_manager.get_session(session_id)
        assert session["status"] == "completed"

    def test_update_status_to_expired(self, session_manager):
        """Test updating status to expired."""
        session_id = session_manager.create_session("user2")

        result = session_manager.update_session_status(session_id, "expired")

        assert result is True

        session = session_manager.get_session(session_id)
        assert session["status"] == "expired"

    def test_update_status_invalid(self, session_manager):
        """Test updating to invalid status raises error."""
        session_id = session_manager.create_session("user3")

        with pytest.raises(SessionManagerError) as exc_info:
            session_manager.update_session_status(session_id, "invalid_status")

        assert "Invalid status" in str(exc_info.value)

    def test_update_status_nonexistent_session(self, session_manager):
        """Test updating status of non-existent session."""
        result = session_manager.update_session_status("nonexistent", "completed")

        assert result is False


# =============================================================================
# Test Conversation History
# =============================================================================

class TestConversationHistory:
    """Test conversation history management."""

    def test_add_user_message(self, session_manager):
        """Test adding user message to history."""
        session_id = session_manager.create_session("user1")

        session_manager.add_to_history(session_id, "user", "What is the weather?")

        history = session_manager.get_conversation_history(session_id)

        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "What is the weather?"
        assert "timestamp" in history[0]

    def test_add_assistant_message(self, session_manager):
        """Test adding assistant message to history."""
        session_id = session_manager.create_session("user1")

        session_manager.add_to_history(session_id, "assistant", "It's sunny!")

        history = session_manager.get_conversation_history(session_id)

        assert len(history) == 1
        assert history[0]["role"] == "assistant"
        assert history[0]["content"] == "It's sunny!"

    def test_add_system_message(self, session_manager):
        """Test adding system message to history."""
        session_id = session_manager.create_session("user1")

        session_manager.add_to_history(session_id, "system", "Session started")

        history = session_manager.get_conversation_history(session_id)

        assert len(history) == 1
        assert history[0]["role"] == "system"

    def test_conversation_order(self, session_manager):
        """Test that conversation history maintains order."""
        session_id = session_manager.create_session("user1")

        messages = [
            ("user", "First message"),
            ("assistant", "First response"),
            ("user", "Second message"),
            ("assistant", "Second response"),
        ]

        for role, content in messages:
            session_manager.add_to_history(session_id, role, content)
            time.sleep(0.01)  # Small delay to ensure timestamp order

        history = session_manager.get_conversation_history(session_id)

        assert len(history) == 4
        for i, (role, content) in enumerate(messages):
            assert history[i]["role"] == role
            assert history[i]["content"] == content

    def test_add_invalid_role(self, session_manager):
        """Test adding message with invalid role raises error."""
        session_id = session_manager.create_session("user1")

        with pytest.raises(SessionManagerError) as exc_info:
            session_manager.add_to_history(session_id, "invalid_role", "message")

        assert "Invalid role" in str(exc_info.value)

    def test_long_message_content(self, session_manager):
        """Test adding very long message content."""
        session_id = session_manager.create_session("user1")

        long_content = "A" * 10000  # 10K characters
        session_manager.add_to_history(session_id, "user", long_content)

        history = session_manager.get_conversation_history(session_id)

        assert len(history) == 1
        assert history[0]["content"] == long_content


# =============================================================================
# Test Agent Invocation Tracking
# =============================================================================

class TestAgentInvocations:
    """Test agent invocation tracking."""

    def test_track_successful_invocation(self, session_manager):
        """Test tracking successful agent invocation."""
        session_id = session_manager.create_session("user1")

        session_manager.track_agent_invocation(
            session_id,
            "weather_agent",
            "What's the weather?",
            "It's sunny and 72°F",
            success=True,
            duration_ms=150
        )

        invocations = session_manager.get_agent_invocations(session_id)

        assert len(invocations) == 1
        assert invocations[0]["agent_name"] == "weather_agent"
        assert invocations[0]["query"] == "What's the weather?"
        assert invocations[0]["response"] == "It's sunny and 72°F"
        assert invocations[0]["success"] == 1  # SQLite boolean as int
        assert invocations[0]["duration_ms"] == 150
        assert invocations[0]["error_message"] is None

    def test_track_failed_invocation(self, session_manager):
        """Test tracking failed agent invocation."""
        session_id = session_manager.create_session("user1")

        session_manager.track_agent_invocation(
            session_id,
            "broken_agent",
            "Do something",
            response=None,
            success=False,
            duration_ms=50,
            error_message="Agent timeout"
        )

        invocations = session_manager.get_agent_invocations(session_id)

        assert len(invocations) == 1
        assert invocations[0]["success"] == 0  # SQLite boolean as int
        assert invocations[0]["error_message"] == "Agent timeout"
        assert invocations[0]["response"] is None

    def test_track_multiple_invocations(self, session_manager):
        """Test tracking multiple agent invocations."""
        session_id = session_manager.create_session("user1")

        agents = [
            ("agent1", "query1", "response1"),
            ("agent2", "query2", "response2"),
            ("agent3", "query3", "response3"),
        ]

        for agent_name, query, response in agents:
            session_manager.track_agent_invocation(
                session_id,
                agent_name,
                query,
                response,
                success=True
            )
            time.sleep(0.01)

        invocations = session_manager.get_agent_invocations(session_id)

        assert len(invocations) == 3
        for i, (agent_name, query, response) in enumerate(agents):
            assert invocations[i]["agent_name"] == agent_name
            assert invocations[i]["query"] == query
            assert invocations[i]["response"] == response

    def test_invocation_without_duration(self, session_manager):
        """Test tracking invocation without duration."""
        session_id = session_manager.create_session("user1")

        session_manager.track_agent_invocation(
            session_id,
            "fast_agent",
            "quick query",
            "quick response",
            success=True
        )

        invocations = session_manager.get_agent_invocations(session_id)

        assert len(invocations) == 1
        assert invocations[0]["duration_ms"] is None


# =============================================================================
# Test Session Context
# =============================================================================

class TestSessionContext:
    """Test session context management."""

    def test_update_context(self, session_manager):
        """Test updating session context."""
        session_id = session_manager.create_session("user1")

        session_manager.update_context(
            session_id,
            "tickets_agent",
            "Show my tickets",
            "You have 3 open tickets"
        )

        context = session_manager.get_context(session_id)

        assert context["last_agent_called"] == "tickets_agent"
        assert context["last_query"] == "Show my tickets"
        assert context["last_response"] == "You have 3 open tickets"

    def test_context_in_get_session(self, session_manager):
        """Test that context is included in get_session."""
        session_id = session_manager.create_session("user1")

        session_manager.update_context(
            session_id,
            "finops_agent",
            "Show cloud costs",
            "Total: $1,234"
        )

        session = session_manager.get_session(session_id)

        assert session["last_agent_called"] == "finops_agent"

    def test_update_context_multiple_times(self, session_manager):
        """Test updating context multiple times overwrites."""
        session_id = session_manager.create_session("user1")

        # First update
        session_manager.update_context(session_id, "agent1", "query1", "response1")

        # Second update
        session_manager.update_context(session_id, "agent2", "query2", "response2")

        context = session_manager.get_context(session_id)

        # Should have latest values
        assert context["last_agent_called"] == "agent2"
        assert context["last_query"] == "query2"
        assert context["last_response"] == "response2"

    def test_get_context_empty_session(self, session_manager):
        """Test getting context for new session."""
        session_id = session_manager.create_session("user1")

        context = session_manager.get_context(session_id)

        assert context["last_agent_called"] is None
        assert context["last_query"] is None
        assert context["last_response"] is None


# =============================================================================
# Test Session Cleanup
# =============================================================================

class TestSessionCleanup:
    """Test session cleanup operations."""

    def test_cleanup_old_completed_sessions(self, session_manager):
        """Test cleaning up old completed sessions."""
        # Create old completed session
        session_id1 = session_manager.create_session("user1")
        session_manager.update_session_status(session_id1, "completed")

        # Manually set old timestamp (disable trigger to prevent auto-update)
        conn = get_connection(session_manager.db_path)
        old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()

        # Drop and recreate trigger after update
        conn.execute("DROP TRIGGER IF EXISTS update_sessions_timestamp")
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
            (old_date, session_id1)
        )
        # Recreate trigger
        conn.execute("""
            CREATE TRIGGER update_sessions_timestamp
            AFTER UPDATE ON sessions
            FOR EACH ROW
            BEGIN
                UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
            END
        """)
        conn.commit()
        conn.close()

        # Create recent session
        session_id2 = session_manager.create_session("user2")

        # Cleanup sessions older than 7 days
        deleted = session_manager.cleanup_old_sessions(days=7)

        assert deleted == 1

        # Old session should be gone
        assert session_manager.get_session(session_id1) is None

        # Recent session should remain
        assert session_manager.get_session(session_id2) is not None

    def test_cleanup_old_expired_sessions(self, session_manager):
        """Test cleaning up old expired sessions."""
        session_id = session_manager.create_session("user1")
        session_manager.update_session_status(session_id, "expired")

        # Make it old (disable trigger to prevent auto-update)
        conn = get_connection(session_manager.db_path)
        old_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

        conn.execute("DROP TRIGGER IF EXISTS update_sessions_timestamp")
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
            (old_date, session_id)
        )
        conn.execute("""
            CREATE TRIGGER update_sessions_timestamp
            AFTER UPDATE ON sessions
            FOR EACH ROW
            BEGIN
                UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
            END
        """)
        conn.commit()
        conn.close()

        deleted = session_manager.cleanup_old_sessions(days=7)

        assert deleted == 1

    def test_cleanup_preserves_active_sessions(self, session_manager):
        """Test that cleanup doesn't delete active sessions."""
        session_id = session_manager.create_session("user1")

        # Make it old but keep active (disable trigger to prevent auto-update)
        conn = get_connection(session_manager.db_path)
        old_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

        conn.execute("DROP TRIGGER IF EXISTS update_sessions_timestamp")
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
            (old_date, session_id)
        )
        conn.execute("""
            CREATE TRIGGER update_sessions_timestamp
            AFTER UPDATE ON sessions
            FOR EACH ROW
            BEGIN
                UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
            END
        """)
        conn.commit()
        conn.close()

        deleted = session_manager.cleanup_old_sessions(days=7)

        # Should not delete active sessions
        assert deleted == 0
        assert session_manager.get_session(session_id) is not None

    def test_cleanup_custom_days(self, session_manager):
        """Test cleanup with custom days parameter."""
        session_id = session_manager.create_session("user1")
        session_manager.update_session_status(session_id, "completed")

        # Make it 5 days old (disable trigger to prevent auto-update)
        conn = get_connection(session_manager.db_path)
        old_date = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()

        conn.execute("DROP TRIGGER IF EXISTS update_sessions_timestamp")
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
            (old_date, session_id)
        )
        conn.execute("""
            CREATE TRIGGER update_sessions_timestamp
            AFTER UPDATE ON sessions
            FOR EACH ROW
            BEGIN
                UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
            END
        """)
        conn.commit()
        conn.close()

        # Should not delete with days=7
        deleted = session_manager.cleanup_old_sessions(days=7)
        assert deleted == 0

        # Should delete with days=3
        deleted = session_manager.cleanup_old_sessions(days=3)
        assert deleted == 1


# =============================================================================
# Test Session Deletion
# =============================================================================

class TestSessionDeletion:
    """Test session deletion operations."""

    def test_delete_session(self, session_manager, populated_session):
        """Test deleting a session."""
        result = session_manager.delete_session(populated_session)

        assert result is True
        assert session_manager.get_session(populated_session) is None

    def test_delete_nonexistent_session(self, session_manager):
        """Test deleting non-existent session."""
        result = session_manager.delete_session("nonexistent-id")

        assert result is False

    def test_delete_cascade(self, session_manager, populated_session):
        """Test that deletion cascades to related tables."""
        # Verify data exists
        history = session_manager.get_conversation_history(populated_session)
        invocations = session_manager.get_agent_invocations(populated_session)

        assert len(history) > 0
        assert len(invocations) > 0

        # Delete session
        session_manager.delete_session(populated_session)

        # Verify cascaded deletion
        conn = get_connection(session_manager.db_path)

        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM conversation_history WHERE session_id = ?",
            (populated_session,)
        )
        assert cursor.fetchone()["count"] == 0

        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM agent_invocations WHERE session_id = ?",
            (populated_session,)
        )
        assert cursor.fetchone()["count"] == 0

        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM session_context WHERE session_id = ?",
            (populated_session,)
        )
        assert cursor.fetchone()["count"] == 0

        conn.close()


# =============================================================================
# Test Thread Safety
# =============================================================================

class TestThreadSafety:
    """Test thread-safe concurrent access."""

    def test_concurrent_session_creation(self, session_manager):
        """Test creating sessions concurrently."""
        session_ids = []
        errors = []

        def create_sessions(user_prefix: str, count: int):
            try:
                for i in range(count):
                    session_id = session_manager.create_session(f"{user_prefix}_{i}")
                    session_ids.append(session_id)
            except Exception as e:
                errors.append(e)

        # Create sessions from multiple threads
        threads = [
            threading.Thread(target=create_sessions, args=(f"user{i}", 10))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(session_ids) == 50
        assert len(set(session_ids)) == 50  # All unique

    def test_concurrent_history_updates(self, session_manager):
        """Test concurrent history updates to same session."""
        session_id = session_manager.create_session("user1")
        errors = []

        def add_messages(thread_id: int, count: int):
            try:
                for i in range(count):
                    session_manager.add_to_history(
                        session_id,
                        "user",
                        f"Message {thread_id}-{i}"
                    )
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=add_messages, args=(i, 20))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

        history = session_manager.get_conversation_history(session_id)
        assert len(history) == 100  # 5 threads * 20 messages

    def test_concurrent_invocation_tracking(self, session_manager):
        """Test concurrent agent invocation tracking."""
        session_id = session_manager.create_session("user1")
        errors = []

        def track_invocations(agent_name: str, count: int):
            try:
                for i in range(count):
                    session_manager.track_agent_invocation(
                        session_id,
                        agent_name,
                        f"Query {i}",
                        f"Response {i}",
                        success=True,
                        duration_ms=100
                    )
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=track_invocations, args=(f"agent{i}", 15))
            for i in range(4)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

        invocations = session_manager.get_agent_invocations(session_id)
        assert len(invocations) == 60  # 4 threads * 15 invocations

    def test_concurrent_read_write(self, session_manager):
        """Test concurrent reads and writes."""
        session_id = session_manager.create_session("user1")
        errors = []
        read_results = []

        def writer(count: int):
            try:
                for i in range(count):
                    session_manager.add_to_history(session_id, "user", f"Message {i}")
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        def reader(count: int):
            try:
                for _ in range(count):
                    session = session_manager.get_session(session_id)
                    read_results.append(len(session["conversation_history"]))
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer, args=(10,)),
            threading.Thread(target=writer, args=(10,)),
            threading.Thread(target=reader, args=(10,)),
            threading.Thread(target=reader, args=(10,)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(read_results) == 20


# =============================================================================
# Test Error Handling
# =============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_database_path(self):
        """Test initialization with invalid database path."""
        # Path that can't be created
        with pytest.raises(DatabaseInitError):
            manager = SessionManager("/invalid/path/that/cannot/exist/db.sqlite")
            manager.create_session("user1")

    def test_empty_user_id(self, session_manager):
        """Test creating session with empty user_id."""
        # Should still work - validation is application layer responsibility
        session_id = session_manager.create_session("")
        assert session_id is not None

    def test_none_metadata_handling(self, session_manager):
        """Test that None metadata is handled correctly."""
        session_id = session_manager.create_session("user1", metadata=None)
        session = session_manager.get_session(session_id)

        assert session["metadata"] is None or session["metadata"] == {}

    def test_special_characters_in_content(self, session_manager):
        """Test handling special characters in messages."""
        session_id = session_manager.create_session("user1")

        special_content = "Test with 'quotes', \"double quotes\", and\nnewlines\tand\ttabs"
        session_manager.add_to_history(session_id, "user", special_content)

        history = session_manager.get_conversation_history(session_id)
        assert history[0]["content"] == special_content

    def test_unicode_content(self, session_manager):
        """Test handling unicode content."""
        session_id = session_manager.create_session("user1")

        unicode_content = "Hello 世界! 🌍 Émojis and spëcial çharacters"
        session_manager.add_to_history(session_id, "user", unicode_content)

        history = session_manager.get_conversation_history(session_id)
        assert history[0]["content"] == unicode_content


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
