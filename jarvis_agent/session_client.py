"""
Session Client for Jarvis Orchestrator

HTTP client that communicates with the Agent Registry Service's
session management API.

Manages user sessions, conversation history, and agent invocation tracking.

Usage:
    >>> client = SessionClient(base_url="http://localhost:8003")
    >>> session_id = client.create_session(user_id="alice")
    >>> client.track_invocation(session_id, "TicketsAgent", "show my tickets", response, True, 150)
    >>> client.add_message(session_id, "user", "show my tickets")
"""

from typing import Dict, List, Optional, Any
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionClient:
    """
    HTTP client for Session Management Service.

    Provides methods to:
    - Create and manage user sessions
    - Track conversation history
    - Record agent invocations
    - Maintain context for multi-turn conversations

    This client is used by the Jarvis orchestrator to track user
    sessions and maintain conversation context.

    Example:
        >>> client = SessionClient(base_url="http://localhost:8003")
        >>>
        >>> # Create new session
        >>> session_id = client.create_session(user_id="alice")
        >>>
        >>> # Track conversation
        >>> client.add_message(session_id, "user", "show my tickets")
        >>> client.track_invocation(
        >>>     session_id,
        >>>     agent_name="TicketsAgent",
        >>>     query="show my tickets",
        >>>     response="You have 3 tickets...",
        >>>     success=True,
        >>>     duration_ms=150
        >>> )
        >>> client.add_message(session_id, "assistant", "You have 3 tickets...")
        >>>
        >>> # Get session data
        >>> session = client.get_session(session_id)
        >>> print(f"Messages: {len(session['conversation_history'])}")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8003",
        timeout: int = 10
    ):
        """
        Initialize Session Client.

        Args:
            base_url: Base URL of Agent Registry Service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._session = requests.Session()

    def create_session(self, user_id: str, metadata: Optional[Dict] = None) -> str:
        """
        Create a new user session.

        Args:
            user_id: User identifier
            metadata: Optional session metadata (JSON serializable)

        Returns:
            Session ID (UUID string)

        Raises:
            ConnectionError: If session service is unreachable
            requests.HTTPError: If API returns error

        Example:
            >>> session_id = client.create_session(
            >>>     user_id="alice",
            >>>     metadata={"source": "web", "ip": "192.168.1.1"}
            >>> )
            >>> print(f"Created session: {session_id}")
        """
        try:
            payload = {"user_id": user_id}
            if metadata:
                payload["metadata"] = metadata

            response = self._session.post(
                f"{self.base_url}/sessions",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            session_id = data["session_id"]

            logger.info(f"Created session {session_id} for user {user_id}")
            return session_id

        except requests.ConnectionError as e:
            logger.error(f"Failed to connect to session service at {self.base_url}: {e}")
            raise ConnectionError(
                f"Session service not available at {self.base_url}"
            ) from e
        except requests.HTTPError as e:
            logger.error(f"Session API error: {e}")
            raise

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full session data.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session data dict with:
                - session_id: str
                - user_id: str
                - created_at: str (ISO timestamp)
                - updated_at: str (ISO timestamp)
                - status: str (active, completed, expired)
                - conversation_history: List[Dict]
                - agents_invoked: List[Dict]
                - last_agent_called: Optional[str]
                - metadata: Optional[Dict]

            Returns None if session not found.

        Raises:
            ConnectionError: If session service is unreachable
            requests.HTTPError: If API returns error (except 404)

        Example:
            >>> session = client.get_session(session_id)
            >>> if session:
            >>>     print(f"User: {session['user_id']}")
            >>>     print(f"Messages: {len(session['conversation_history'])}")
            >>>     print(f"Agents used: {session['agents_invoked']}")
        """
        try:
            response = self._session.get(
                f"{self.base_url}/sessions/{session_id}",
                timeout=self.timeout
            )

            if response.status_code == 404:
                logger.warning(f"Session '{session_id}' not found")
                return None

            response.raise_for_status()
            return response.json()

        except requests.ConnectionError as e:
            logger.error(f"Failed to connect to session service: {e}")
            raise ConnectionError(
                f"Session service not available at {self.base_url}"
            ) from e
        except requests.HTTPError as e:
            logger.error(f"Session API error for session '{session_id}': {e}")
            raise

    def track_invocation(
        self,
        session_id: str,
        agent_name: str,
        query: str,
        response: str,
        success: bool,
        duration_ms: int,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Track an agent invocation.

        Records that an agent was called with a query and the result.

        Args:
            session_id: Session ID
            agent_name: Name of agent that was invoked
            query: Query sent to the agent
            response: Response from the agent
            success: Whether invocation was successful
            duration_ms: Execution duration in milliseconds
            error_message: Optional error message if success=False

        Returns:
            True if tracking successful

        Raises:
            requests.HTTPError: If tracking fails

        Example:
            >>> client.track_invocation(
            >>>     session_id=session_id,
            >>>     agent_name="TicketsAgent",
            >>>     query="show my tickets",
            >>>     response="You have 3 pending tickets...",
            >>>     success=True,
            >>>     duration_ms=150
            >>> )
        """
        try:
            payload = {
                "agent_name": agent_name,
                "query": query,
                "response": response,
                "success": success,
                "duration_ms": duration_ms
            }

            if error_message:
                payload["error_message"] = error_message

            response = self._session.post(
                f"{self.base_url}/sessions/{session_id}/invocations",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.debug(f"Tracked invocation: {agent_name} in session {session_id}")
            return True

        except requests.HTTPError as e:
            logger.error(f"Failed to track invocation: {e}")
            raise

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> bool:
        """
        Add a message to conversation history.

        Args:
            session_id: Session ID
            role: Message role ("user", "assistant", or "system")
            content: Message content

        Returns:
            True if message added successfully

        Raises:
            requests.HTTPError: If adding message fails

        Example:
            >>> # User message
            >>> client.add_message(session_id, "user", "show my tickets")
            >>>
            >>> # Assistant response
            >>> client.add_message(session_id, "assistant", "You have 3 tickets...")
        """
        try:
            payload = {
                "role": role,
                "content": content
            }

            response = self._session.post(
                f"{self.base_url}/sessions/{session_id}/history",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.debug(f"Added {role} message to session {session_id}")
            return True

        except requests.HTTPError as e:
            logger.error(f"Failed to add message: {e}")
            raise

    def update_session_status(
        self,
        session_id: str,
        status: str
    ) -> bool:
        """
        Update session status.

        Args:
            session_id: Session ID
            status: New status ("active", "completed", or "expired")

        Returns:
            True if update successful

        Raises:
            requests.HTTPError: If update fails

        Example:
            >>> # Mark session as completed
            >>> client.update_session_status(session_id, "completed")
        """
        try:
            payload = {"status": status}

            response = self._session.patch(
                f"{self.base_url}/sessions/{session_id}/status",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.info(f"Updated session {session_id} status to: {status}")
            return True

        except requests.HTTPError as e:
            logger.error(f"Failed to update session status: {e}")
            raise

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all associated data.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deletion successful

        Raises:
            requests.HTTPError: If deletion fails

        Example:
            >>> client.delete_session(session_id)
        """
        try:
            response = self._session.delete(
                f"{self.base_url}/sessions/{session_id}",
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.info(f"Deleted session: {session_id}")
            return True

        except requests.HTTPError as e:
            logger.error(f"Failed to delete session: {e}")
            raise

    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session ID
            limit: Maximum number of messages to return (most recent)

        Returns:
            List of message dicts with:
                - role: str ("user", "assistant", "system")
                - content: str
                - timestamp: str (ISO timestamp)

        Example:
            >>> # Get last 10 messages
            >>> messages = client.get_conversation_history(session_id, limit=10)
            >>> for msg in messages:
            >>>     print(f"{msg['role']}: {msg['content']}")
        """
        session = self.get_session(session_id)
        if not session:
            return []

        history = session.get("conversation_history", [])

        if limit and len(history) > limit:
            # Return most recent messages
            return history[-limit:]

        return history

    def get_agent_invocations(
        self,
        session_id: str,
        agent_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get agent invocations for a session.

        Args:
            session_id: Session ID
            agent_name: Optional filter by agent name

        Returns:
            List of invocation dicts with:
                - agent_name: str
                - query: str
                - response: str
                - success: bool
                - duration_ms: int
                - timestamp: str (ISO timestamp)

        Example:
            >>> # Get all invocations
            >>> invocations = client.get_agent_invocations(session_id)
            >>>
            >>> # Get TicketsAgent invocations only
            >>> ticket_invocations = client.get_agent_invocations(
            >>>     session_id, agent_name="TicketsAgent"
            >>> )
        """
        session = self.get_session(session_id)
        if not session:
            return []

        invocations = session.get("agents_invoked", [])

        if agent_name:
            # Filter by agent name
            invocations = [
                inv for inv in invocations
                if inv.get("agent_name") == agent_name
            ]

        return invocations

    def get_last_agent_called(self, session_id: str) -> Optional[str]:
        """
        Get name of last agent called in this session.

        Useful for context-aware routing.

        Args:
            session_id: Session ID

        Returns:
            Agent name or None

        Example:
            >>> last_agent = client.get_last_agent_called(session_id)
            >>> if last_agent == "TicketsAgent":
            >>>     print("User was previously asking about tickets")
        """
        session = self.get_session(session_id)
        if not session:
            return None

        return session.get("last_agent_called")

    def health_check(self) -> bool:
        """
        Check if session service is healthy.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = self._session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def close(self):
        """Close the HTTP session."""
        self._session.close()
