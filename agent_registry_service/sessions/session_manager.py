"""
Session Manager for Agent Registry Service.

This module provides SQLite-based session management with:
- Session creation and tracking
- Conversation history storage
- Agent invocation logging
- Session context management
- Multi-threaded access support

Features:
- Thread-safe database operations
- Automatic session cleanup
- Complete conversation replay
- Agent performance tracking
"""

import logging
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from threading import Lock

from agent_registry_service.sessions.db_init import get_connection, initialize_database

logger = logging.getLogger(__name__)


class SessionManagerError(Exception):
    """Base exception for SessionManager operations."""
    pass


class SessionManager:
    """
    Manages user sessions with SQLite persistence.

    Features:
    - Session lifecycle management (create, retrieve, update, delete)
    - Conversation history tracking
    - Agent invocation logging
    - Session context for continuity
    - Automatic cleanup of old sessions
    - Thread-safe operations

    Example:
        >>> manager = SessionManager("data/sessions.db")
        >>> session_id = manager.create_session("alice")
        >>> manager.add_to_history(session_id, "user", "Show my tickets")
        >>> manager.track_agent_invocation(
        ...     session_id, "tickets_agent", "Show my tickets",
        ...     "You have 3 tickets", True, 150
        ... )
        >>> session = manager.get_session(session_id)
    """

    def __init__(self, db_path: str, auto_init: bool = True):
        """
        Initialize SessionManager.

        Args:
            db_path: Path to SQLite database file
            auto_init: Whether to automatically initialize database if it doesn't exist
        """
        self.db_path = db_path
        self._lock = Lock()  # Thread safety lock

        logger.info(f"SessionManager initialized with database: {db_path}")

        # Auto-initialize database if needed
        if auto_init:
            try:
                initialize_database(db_path, force_recreate=False)
            except Exception as e:
                logger.warning(f"Database initialization skipped: {e}")

    def create_session(self, user_id: str, metadata: Optional[Dict] = None) -> str:
        """
        Create a new session.

        Args:
            user_id: User identifier
            metadata: Optional JSON-serializable metadata

        Returns:
            New session ID (UUID)

        Raises:
            SessionManagerError: If session creation fails
        """
        session_id = str(uuid.uuid4())

        try:
            with self._lock:
                conn = get_connection(self.db_path)

                # Convert metadata to JSON string if provided
                metadata_json = None
                if metadata:
                    import json
                    metadata_json = json.dumps(metadata)

                conn.execute(
                    """
                    INSERT INTO sessions (session_id, user_id, status, metadata)
                    VALUES (?, ?, 'active', ?)
                    """,
                    (session_id, user_id, metadata_json)
                )

                # Initialize session context
                conn.execute(
                    """
                    INSERT INTO session_context (session_id)
                    VALUES (?)
                    """,
                    (session_id,)
                )

                conn.commit()
                conn.close()

            logger.info(f"Created session {session_id} for user {user_id}")
            return session_id

        except sqlite3.Error as e:
            logger.error(f"Failed to create session: {e}", exc_info=True)
            raise SessionManagerError(f"Session creation failed: {e}")

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get complete session data including history and invocations.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session data or None if not found
            Format:
            {
                "session_id": str,
                "user_id": str,
                "created_at": str,
                "updated_at": str,
                "status": str,
                "metadata": dict,
                "conversation_history": [{"role": str, "content": str, "timestamp": str}],
                "agents_invoked": [{"agent_name": str, "query": str, ...}],
                "last_agent_called": str
            }
        """
        try:
            with self._lock:
                conn = get_connection(self.db_path)

                # Get session
                cursor = conn.execute(
                    "SELECT * FROM sessions WHERE session_id = ?",
                    (session_id,)
                )
                session_row = cursor.fetchone()

                if not session_row:
                    conn.close()
                    return None

                # Build session dict
                session = dict(session_row)

                # Parse metadata JSON
                if session.get('metadata'):
                    import json
                    try:
                        session['metadata'] = json.loads(session['metadata'])
                    except json.JSONDecodeError:
                        session['metadata'] = {}

                # Get conversation history
                session['conversation_history'] = self._get_conversation_history(conn, session_id)

                # Get agent invocations
                session['agents_invoked'] = self._get_agent_invocations(conn, session_id)

                # Get context
                cursor = conn.execute(
                    "SELECT last_agent_called FROM session_context WHERE session_id = ?",
                    (session_id,)
                )
                context_row = cursor.fetchone()
                session['last_agent_called'] = context_row['last_agent_called'] if context_row else None

                conn.close()

                return session

        except sqlite3.Error as e:
            logger.error(f"Failed to get session {session_id}: {e}", exc_info=True)
            raise SessionManagerError(f"Failed to retrieve session: {e}")

    def update_session_status(self, session_id: str, status: str) -> bool:
        """
        Update session status.

        Args:
            session_id: Session identifier
            status: New status ('active', 'completed', 'expired')

        Returns:
            True if updated, False if session not found

        Raises:
            SessionManagerError: If update fails or status is invalid
        """
        valid_statuses = ['active', 'completed', 'expired']
        if status not in valid_statuses:
            raise SessionManagerError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        try:
            with self._lock:
                conn = get_connection(self.db_path)

                cursor = conn.execute(
                    "UPDATE sessions SET status = ? WHERE session_id = ?",
                    (status, session_id)
                )

                rows_affected = cursor.rowcount
                conn.commit()
                conn.close()

                if rows_affected > 0:
                    logger.info(f"Updated session {session_id} status to {status}")
                    return True
                else:
                    logger.warning(f"Session {session_id} not found")
                    return False

        except sqlite3.Error as e:
            logger.error(f"Failed to update session status: {e}", exc_info=True)
            raise SessionManagerError(f"Status update failed: {e}")

    def track_agent_invocation(
        self,
        session_id: str,
        agent_name: str,
        query: str,
        response: Optional[str] = None,
        success: bool = True,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Track an agent invocation.

        Args:
            session_id: Session identifier
            agent_name: Name of the agent invoked
            query: User query sent to agent
            response: Agent response
            success: Whether invocation was successful
            duration_ms: Execution duration in milliseconds
            error_message: Error message if failed

        Raises:
            SessionManagerError: If tracking fails
        """
        try:
            with self._lock:
                conn = get_connection(self.db_path)

                conn.execute(
                    """
                    INSERT INTO agent_invocations
                    (session_id, agent_name, query, response, success, duration_ms, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (session_id, agent_name, query, response, success, duration_ms, error_message)
                )

                conn.commit()
                conn.close()

            logger.debug(f"Tracked invocation: {agent_name} for session {session_id}")

        except sqlite3.Error as e:
            logger.error(f"Failed to track agent invocation: {e}", exc_info=True)
            raise SessionManagerError(f"Agent invocation tracking failed: {e}")

    def add_to_history(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to conversation history.

        Args:
            session_id: Session identifier
            role: Message role ('user', 'assistant', 'system')
            content: Message content

        Raises:
            SessionManagerError: If adding message fails or role is invalid
        """
        valid_roles = ['user', 'assistant', 'system']
        if role not in valid_roles:
            raise SessionManagerError(f"Invalid role: {role}. Must be one of {valid_roles}")

        try:
            with self._lock:
                conn = get_connection(self.db_path)

                conn.execute(
                    """
                    INSERT INTO conversation_history (session_id, role, content)
                    VALUES (?, ?, ?)
                    """,
                    (session_id, role, content)
                )

                conn.commit()
                conn.close()

            logger.debug(f"Added {role} message to session {session_id}")

        except sqlite3.Error as e:
            logger.error(f"Failed to add message to history: {e}", exc_info=True)
            raise SessionManagerError(f"Failed to add message: {e}")

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of message dictionaries with role, content, timestamp
        """
        try:
            with self._lock:
                conn = get_connection(self.db_path)
                history = self._get_conversation_history(conn, session_id)
                conn.close()
                return history

        except sqlite3.Error as e:
            logger.error(f"Failed to get conversation history: {e}", exc_info=True)
            raise SessionManagerError(f"Failed to retrieve history: {e}")

    def get_agent_invocations(self, session_id: str) -> List[Dict]:
        """
        Get agent invocations for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of invocation dictionaries
        """
        try:
            with self._lock:
                conn = get_connection(self.db_path)
                invocations = self._get_agent_invocations(conn, session_id)
                conn.close()
                return invocations

        except sqlite3.Error as e:
            logger.error(f"Failed to get agent invocations: {e}", exc_info=True)
            raise SessionManagerError(f"Failed to retrieve invocations: {e}")

    def update_context(
        self,
        session_id: str,
        last_agent: str,
        last_query: str,
        last_response: str
    ) -> None:
        """
        Update session context.

        Args:
            session_id: Session identifier
            last_agent: Name of last agent called
            last_query: Last query sent
            last_response: Last response received

        Raises:
            SessionManagerError: If update fails
        """
        try:
            with self._lock:
                conn = get_connection(self.db_path)

                conn.execute(
                    """
                    UPDATE session_context
                    SET last_agent_called = ?, last_query = ?, last_response = ?
                    WHERE session_id = ?
                    """,
                    (last_agent, last_query, last_response, session_id)
                )

                conn.commit()
                conn.close()

            logger.debug(f"Updated context for session {session_id}")

        except sqlite3.Error as e:
            logger.error(f"Failed to update context: {e}", exc_info=True)
            raise SessionManagerError(f"Context update failed: {e}")

    def get_context(self, session_id: str) -> Dict:
        """
        Get session context.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with last_agent_called, last_query, last_response
        """
        try:
            with self._lock:
                conn = get_connection(self.db_path)

                cursor = conn.execute(
                    "SELECT * FROM session_context WHERE session_id = ?",
                    (session_id,)
                )
                row = cursor.fetchone()
                conn.close()

                return dict(row) if row else {}

        except sqlite3.Error as e:
            logger.error(f"Failed to get context: {e}", exc_info=True)
            raise SessionManagerError(f"Failed to retrieve context: {e}")

    def cleanup_old_sessions(self, days: int = 7) -> int:
        """
        Delete completed or expired sessions older than specified days.

        Args:
            days: Delete sessions older than this many days

        Returns:
            Number of sessions deleted

        Raises:
            SessionManagerError: If cleanup fails
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            with self._lock:
                conn = get_connection(self.db_path)

                # Use datetime() for proper SQLite timestamp comparison
                cursor = conn.execute(
                    """
                    DELETE FROM sessions
                    WHERE status IN ('completed', 'expired')
                    AND datetime(updated_at) < datetime(?)
                    """,
                    (cutoff_date.isoformat(),)
                )

                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()

            logger.info(f"Cleaned up {deleted_count} old sessions (older than {days} days)")
            return deleted_count

        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup old sessions: {e}", exc_info=True)
            raise SessionManagerError(f"Cleanup failed: {e}")

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a specific session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found

        Raises:
            SessionManagerError: If deletion fails
        """
        try:
            with self._lock:
                conn = get_connection(self.db_path)

                cursor = conn.execute(
                    "DELETE FROM sessions WHERE session_id = ?",
                    (session_id,)
                )

                rows_affected = cursor.rowcount
                conn.commit()
                conn.close()

                if rows_affected > 0:
                    logger.info(f"Deleted session {session_id}")
                    return True
                else:
                    logger.warning(f"Session {session_id} not found")
                    return False

        except sqlite3.Error as e:
            logger.error(f"Failed to delete session: {e}", exc_info=True)
            raise SessionManagerError(f"Deletion failed: {e}")

    # =========================================================================
    # Helper methods (internal use)
    # =========================================================================

    def _get_conversation_history(self, conn: sqlite3.Connection, session_id: str) -> List[Dict]:
        """Get conversation history from database connection."""
        cursor = conn.execute(
            """
            SELECT role, content, timestamp
            FROM conversation_history
            WHERE session_id = ?
            ORDER BY timestamp ASC
            """,
            (session_id,)
        )

        return [dict(row) for row in cursor.fetchall()]

    def _get_agent_invocations(self, conn: sqlite3.Connection, session_id: str) -> List[Dict]:
        """Get agent invocations from database connection."""
        cursor = conn.execute(
            """
            SELECT agent_name, query, response, success, error_message, duration_ms, timestamp
            FROM agent_invocations
            WHERE session_id = ?
            ORDER BY timestamp ASC
            """,
            (session_id,)
        )

        return [dict(row) for row in cursor.fetchall()]
