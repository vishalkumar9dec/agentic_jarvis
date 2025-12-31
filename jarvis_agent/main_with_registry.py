"""
Jarvis Main Orchestrator with Registry Service Integration

This is the main entry point for Jarvis that integrates with the
centralized Agent Registry Service and Session Management.

Features:
- Fetches agents dynamically from registry service
- Tracks sessions and conversation history
- Records agent invocations for analytics
- Supports multi-agent routing for complex queries

Architecture:
1. RegistryClient - Fetches agents from http://localhost:8003
2. SessionClient - Manages sessions and conversation history
3. TwoStageRouter - Routes queries to relevant agents
4. Agent invocation and response combination

Usage:
    # Start as CLI
    python jarvis_agent/main_with_registry.py

    # Or import and use programmatically
    from jarvis_agent.main_with_registry import JarvisOrchestrator

    orchestrator = JarvisOrchestrator()
    response = orchestrator.handle_query(
        query="show my tickets and courses",
        user_id="alice"
    )
"""

import os
import sys
import logging
import time
import uuid
import getpass
import requests
from typing import Dict, List, Optional

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, try to load .env manually
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

from jarvis_agent.registry_client import RegistryClient
from jarvis_agent.session_client import SessionClient
from jarvis_agent.dynamic_router_with_registry import TwoStageRouterWithRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JarvisOrchestrator:
    """
    Main Jarvis orchestrator with registry service integration.

    Coordinates:
    - Agent discovery via registry service
    - Query routing via two-stage router
    - Session management
    - Agent invocation tracking
    - Response combination

    Example:
        >>> orchestrator = JarvisOrchestrator(
        >>>     registry_url="http://localhost:8003",
        >>>     session_url="http://localhost:8003"
        >>> )
        >>>
        >>> # Handle single query
        >>> response = orchestrator.handle_query(
        >>>     query="show my tickets and courses",
        >>>     user_id="alice"
        >>> )
        >>> print(response)
        >>>
        >>> # Multi-turn conversation
        >>> session_id = orchestrator.create_session("alice")
        >>> response1 = orchestrator.handle_query_with_session(
        >>>     session_id, "show my tickets"
        >>> )
        >>> response2 = orchestrator.handle_query_with_session(
        >>>     session_id, "show details for ticket 12301"
        >>> )
    """

    def __init__(
        self,
        jwt_token: Optional[str] = None,
        registry_url: str = "http://localhost:8003",
        session_url: str = "http://localhost:8003",
        timeout: int = 10
    ):
        """
        Initialize Jarvis orchestrator.

        Args:
            jwt_token: Optional JWT token for authentication (Phase 2)
            registry_url: URL of Agent Registry Service
            session_url: URL of Session Management Service
            timeout: Request timeout in seconds

        Raises:
            ValueError: If JWT token is invalid or expired
        """
        logger.info("Initializing Jarvis Orchestrator with Registry Service")

        # Validate and decode JWT token (Phase 2)
        if jwt_token:
            self.jwt_token = jwt_token
            self.user_info = self._validate_jwt(jwt_token)
            # Use username for agent data compatibility (agents use username, not sub)
            self.user_id = self.user_info.get("username") or self.user_info.get("sub")
            self.user_role = self.user_info.get("role", "user")

            logger.info(f"Authenticated user: {self.user_id} (role: {self.user_role})")
        else:
            # No authentication (backward compatibility)
            self.jwt_token = None
            self.user_info = None
            self.user_id = None
            self.user_role = None
            logger.warning("No JWT token provided - running without authentication")

        # Initialize clients
        self.registry_client = RegistryClient(
            base_url=registry_url,
            timeout=timeout
        )
        self.session_client = SessionClient(
            base_url=session_url,
            timeout=timeout
        )

        # Initialize router
        self.router = TwoStageRouterWithRegistry(
            registry_client=self.registry_client,
            model="gemini-2.0-flash-exp",
            stage1_max_candidates=10,
            stage1_min_score=0.1
        )

        # Session cache (user_id -> session_id)
        self._user_sessions: Dict[str, str] = {}

        # Verify services are healthy
        self._verify_services()

        logger.info("Jarvis Orchestrator initialized successfully")

    def _validate_jwt(self, token: str) -> dict:
        """
        Validate JWT token and return payload.

        Args:
            token: JWT token string

        Returns:
            Token payload dict

        Raises:
            ValueError: If token is invalid or expired
        """
        from auth.jwt_utils import verify_jwt_token

        payload = verify_jwt_token(token)

        if not payload:
            raise ValueError("Invalid or expired JWT token")

        return payload

    def _verify_services(self):
        """Verify registry and session services are healthy."""
        if not self.registry_client.health_check():
            logger.error("Registry service is not healthy")
            raise ConnectionError(
                "Registry service not available. "
                "Please start it with: ./scripts/start_registry_service.sh"
            )

        if not self.session_client.health_check():
            logger.error("Session service is not healthy")
            raise ConnectionError("Session service not available")

        logger.info("All services healthy")

    def create_session(self, user_id: str, metadata: Optional[Dict] = None) -> str:
        """
        Create a new session for a user.

        Args:
            user_id: User identifier
            metadata: Optional session metadata

        Returns:
            Session ID

        Example:
            >>> session_id = orchestrator.create_session("alice")
        """
        session_id = self.session_client.create_session(user_id, metadata)
        self._user_sessions[user_id] = session_id

        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id

    def get_or_create_session(self, user_id: str) -> str:
        """
        Get existing active session for user or create new one.

        Implements session persistence across logins (Phase 2 Goal 4).
        First checks cache, then queries registry for active sessions,
        finally creates new session if none exists.

        Args:
            user_id: User identifier

        Returns:
            Session ID (existing or new)

        Example:
            >>> session_id = orchestrator.get_or_create_session("alice")
            >>> # Will resume session if active, or create new one
        """
        # Check cache first (in-memory, fast)
        if user_id in self._user_sessions:
            session_id = self._user_sessions[user_id]

            # Verify session still exists and is active
            session_data = self.session_client.get_session(session_id)
            if session_data and session_data.get("status") == "active":
                logger.info(f"Using cached session {session_id} for user {user_id}")
                return session_id

        # Check registry for active session (enables resumption after restart)
        session_id = self.session_client.get_active_session_for_user(user_id)

        if session_id:
            # Found active session - cache it and resume
            self._user_sessions[user_id] = session_id
            logger.info(f"✓ Resuming active session {session_id} for user {user_id}")
            return session_id

        # No active session found - create new one
        session_id = self.create_session(user_id)
        logger.info(f"✓ Created new session {session_id} for user {user_id}")
        return session_id

    def handle_query(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Handle a user query end-to-end.

        Workflow:
        1. Create/resume session
        2. Add user message to history
        3. Route query to relevant agents
        4. Invoke selected agents
        5. Track invocations
        6. Combine responses
        7. Add assistant response to history
        8. Return final response

        Args:
            query: User query string
            user_id: Optional user identifier (defaults to authenticated user from JWT)
            session_id: Optional session ID (creates new if None)

        Returns:
            Combined response string

        Example:
            >>> # With JWT authentication
            >>> response = orchestrator.handle_query("show my tickets")
            >>>
            >>> # Without JWT (legacy)
            >>> response = orchestrator.handle_query(
            >>>     query="show my tickets",
            >>>     user_id="alice"
            >>> )
        """
        start_time = time.time()

        # Use authenticated user if not explicitly provided
        if user_id is None:
            if self.user_id is None:
                raise ValueError("user_id must be provided when not authenticated with JWT")
            user_id = self.user_id

        # Get or create session
        if not session_id:
            session_id = self.get_or_create_session(user_id)

        logger.info(f"Handling query for user {user_id} in session {session_id}")
        logger.info(f"Query: {query}")

        # Add user message to history
        self.session_client.add_message(session_id, "user", query)

        # Route query to agents
        logger.info("Routing query...")
        agents = self.router.route(query, require_all_matches=True)

        if not agents:
            response = (
                "I couldn't find any agents to handle your request. "
                "This could mean:\n"
                "1. No agents are registered in the system\n"
                "2. No agents match your query\n"
                "3. The registry service is not accessible\n\n"
                "Please try rephrasing your query or contact support."
            )
            self.session_client.add_message(session_id, "assistant", response)
            return response

        logger.info(f"Selected {len(agents)} agents: {[a.name for a in agents]}")

        # Decompose query into agent-specific sub-queries with user context
        try:
            sub_queries = self._decompose_query(query, agents, user_id=self.user_id)
        except PermissionError as e:
            # User tried to access data they don't have permission for
            error_message = str(e)
            logger.warning(f"Permission denied for user {user_id}: {error_message}")
            self.session_client.add_message(session_id, "assistant", error_message)
            return error_message

        # Invoke agents and collect responses
        agent_responses = []
        for agent in agents:
            try:
                invoke_start = time.time()

                # Get agent-specific sub-query
                agent_query = sub_queries.get(agent.name, query)
                logger.info(f"Invoking {agent.name} with query: '{agent_query}'")

                # Invoke agent with its specific sub-query
                agent_response = self._invoke_agent(agent, agent_query)
                invoke_duration = int((time.time() - invoke_start) * 1000)

                # Track invocation
                self.session_client.track_invocation(
                    session_id=session_id,
                    agent_name=agent.name,
                    query=agent_query,  # Use agent-specific sub-query
                    response=str(agent_response),
                    success=True,
                    duration_ms=invoke_duration
                )

                agent_responses.append({
                    "agent": agent.name,
                    "response": str(agent_response)
                })

                logger.info(f"{agent.name} completed in {invoke_duration}ms")

            except Exception as e:
                logger.error(f"Failed to invoke {agent.name}: {e}")

                # Get agent-specific query for error tracking
                agent_query = sub_queries.get(agent.name, query)

                # Track failed invocation
                self.session_client.track_invocation(
                    session_id=session_id,
                    agent_name=agent.name,
                    query=agent_query,  # Use agent-specific sub-query
                    response="",
                    success=False,
                    duration_ms=0,
                    error_message=str(e)
                )

                agent_responses.append({
                    "agent": agent.name,
                    "response": f"Error: {str(e)}"
                })

        # Combine responses
        final_response = self._combine_responses(query, agent_responses)

        # Add assistant response to history
        self.session_client.add_message(session_id, "assistant", final_response)

        # Log total duration
        total_duration = int((time.time() - start_time) * 1000)
        logger.info(f"Query handled successfully in {total_duration}ms")

        return final_response

    def _decompose_query(
        self,
        original_query: str,
        agents: List[LlmAgent],
        user_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Decompose a multi-agent query into agent-specific sub-queries with user context.

        Args:
            original_query: The original user query
            agents: List of agents to handle the query
            user_id: Optional authenticated user ID for context injection

        Returns:
            Dict mapping agent names to their specific sub-queries

        Example:
            Query: "show my tickets and aws cost"
            User: "vishal"
            Returns: {
                "TicketsAgent": "show tickets for vishal",
                "FinOpsAgent": "show aws cost"
            }
        """
        # If only one agent, inject user context and return
        if len(agents) == 1:
            query = self._inject_user_context(original_query, user_id) if user_id else original_query
            return {agents[0].name: query}

        # Use LLM to decompose query
        from google import genai
        from google.genai import types

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found. Using original query for all agents.")
            return {agent.name: original_query for agent in agents}

        client = genai.Client(api_key=api_key)

        # Build agent descriptions
        agent_descriptions = []
        for agent in agents:
            agent_descriptions.append(
                f"- {agent.name}: {agent.description}"
            )

        # Build user context section
        user_context = f"""
Authenticated User: {user_id}

IMPORTANT - User Context Injection:
- Replace "my", "I", "me" with the specific username: "{user_id}"
- Make each sub-query explicit about which user's data to retrieve
""" if user_id else ""

        prompt = f"""Given a user query and multiple specialized agents, break down the query into agent-specific sub-queries.

{user_context}
User Query: "{original_query}"

Available Agents:
{chr(10).join(agent_descriptions)}

For each agent, extract ONLY the part of the query relevant to that agent's capabilities.
Return a JSON object mapping agent names to their specific sub-queries.

Important:
- Each sub-query should be a complete, standalone question
- Remove parts that the agent cannot handle
- Keep the sub-query natural and conversational
- If an agent can handle the entire query, use the full query
- Replace possessive pronouns (my, I, me) with the authenticated username

Example 1 (without user context):
Query: "show all tickets and aws cost"
Agents: TicketsAgent (IT operations), FinOpsAgent (cloud costs)
Output:
{{
    "TicketsAgent": "show all tickets",
    "FinOpsAgent": "show aws cost"
}}

Example 2 (with user context):
User: vishal
Query: "show my tickets and courses"
Agents: TicketsAgent (IT operations), OxygenAgent (learning platform)
Output:
{{
    "TicketsAgent": "show tickets for vishal",
    "OxygenAgent": "show courses for vishal"
}}

Now decompose the actual query above."""

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT"],
                    response_mime_type="application/json"
                )
            )

            import json
            decomposed = json.loads(response.text)
            logger.info(f"Query decomposed: {decomposed}")
            return decomposed

        except Exception as e:
            logger.error(f"Failed to decompose query: {e}")
            # Fallback: use original query
            return {agent.name: original_query for agent in agents}

    def _inject_user_context(self, query: str, user_id: Optional[str]) -> str:
        """
        Inject user context into query and enforce access control.

        Security Features:
        1. Checks if user is trying to access another user's data
        2. Raises PermissionError if non-admin tries to access other user's data
        3. Replaces "my", "I", "me" with the authenticated username

        Args:
            query: Original query string
            user_id: Authenticated user ID

        Returns:
            Query with user context injected

        Raises:
            PermissionError: If non-admin user tries to access another user's data

        Example:
            >>> # Regular user trying to access other's data
            >>> query = "show vishal's tickets"
            >>> user_id = "happy"
            >>> result = self._inject_user_context(query, user_id)
            PermissionError: Access Denied: You do not have permission to view vishal's data...

            >>> # Admin user can access any data
            >>> query = "show vishal's tickets"
            >>> user_id = "admin"
            >>> result = self._inject_user_context(query, user_id)
            >>> print(result)
            "show vishal's tickets"  # Admins can see any user's data
        """
        if not user_id:
            return query

        import re

        # SECURITY: Check if non-admin user is trying to access another user's data
        if self.user_role and self.user_role.lower() != "admin":
            # List of known users (expand as needed)
            known_users = ["vishal", "happy", "alex", "sarah"]

            # Check if query contains any other username
            for other_user in known_users:
                if other_user.lower() != user_id.lower():
                    # Check for username in various forms
                    if re.search(rf'\b{other_user}\b', query, flags=re.IGNORECASE):
                        # Unauthorized access attempt detected
                        raise PermissionError(
                            f"Access Denied: You do not have permission to view {other_user}'s data. "
                            f"You can only view your own data. If you need to access other users' data, "
                            f"please contact your administrator."
                        )

        # Replace possessive "my" with "username's"
        query = re.sub(r'\bmy\b', f"{user_id}'s", query, flags=re.IGNORECASE)

        # Replace "I" at word boundaries with username
        query = re.sub(r'\bI\b', user_id, query)

        # Replace "me" with username
        query = re.sub(r'\bme\b', user_id, query, flags=re.IGNORECASE)

        logger.debug(f"User context injected: '{query}' (user: {user_id}, role: {self.user_role})")
        return query

    def _invoke_agent(self, agent: LlmAgent, query: str) -> str:
        """
        Invoke an agent with a query using InMemoryRunner.

        Works for both local LlmAgent and remote RemoteA2aAgent.

        Args:
            agent: Agent instance (LlmAgent or RemoteA2aAgent)
            query: Query string

        Returns:
            Response string
        """
        import asyncio

        logger.debug(f"Invoking agent {agent.name} via InMemoryRunner")

        # Create InMemoryRunner for this agent
        runner = InMemoryRunner(
            agent=agent,
            app_name=f"invoke_{agent.name}"
        )

        # Create unique session for this invocation
        session_id = str(uuid.uuid4())
        user_id = "jarvis_system"

        # Create session in session service
        async def create_session():
            await runner.session_service.create_session(
                app_name=runner.app_name,
                user_id=user_id,
                session_id=session_id
            )

        asyncio.run(create_session())

        # Create message content
        message = types.Content(
            role="user",
            parts=[types.Part(text=query)]
        )

        # Run agent and collect response
        response_text = ""
        try:
            for event in runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=message
            ):
                # Extract text from event content
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text

            return response_text.strip() if response_text else "No response from agent"

        except Exception as e:
            logger.error(f"Error invoking agent {agent.name}: {e}")
            raise

    def _combine_responses(
        self,
        query: str,
        agent_responses: List[Dict[str, str]]
    ) -> str:
        """
        Combine responses from multiple agents into a coherent response.

        Args:
            query: Original user query
            agent_responses: List of dicts with "agent" and "response" keys

        Returns:
            Combined response string

        Example:
            >>> responses = [
            >>>     {"agent": "TicketsAgent", "response": "You have 3 tickets..."},
            >>>     {"agent": "OxygenAgent", "response": "You have 2 courses..."}
            >>> ]
            >>> combined = orchestrator._combine_responses(query, responses)
        """
        if len(agent_responses) == 0:
            return "No agents were able to process your request."

        if len(agent_responses) == 1:
            # Single agent response
            return agent_responses[0]["response"]

        # Multiple agents - format nicely
        lines = [f"I've gathered information from multiple sources:\n"]

        for item in agent_responses:
            agent_name = item["agent"]
            response = item["response"]

            # Format section header
            lines.append(f"\n**{agent_name}:**")
            lines.append(response)

        lines.append("\n---")
        lines.append(
            "This information was provided by multiple specialized agents "
            "working together to answer your query."
        )

        return "\n".join(lines)

    def handle_query_with_session(self, session_id: str, query: str) -> str:
        """
        Handle query with existing session.

        Args:
            session_id: Existing session ID
            query: User query

        Returns:
            Response string

        Example:
            >>> session_id = orchestrator.create_session("alice")
            >>> response = orchestrator.handle_query_with_session(
            >>>     session_id, "show my tickets"
            >>> )
        """
        # Get user_id from session
        session_data = self.session_client.get_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")

        user_id = session_data["user_id"]
        return self.handle_query(query, user_id=user_id, session_id=session_id)

    def get_session_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session ID

        Returns:
            List of message dicts

        Example:
            >>> history = orchestrator.get_session_history(session_id)
            >>> for msg in history:
            >>>     print(f"{msg['role']}: {msg['content']}")
        """
        return self.session_client.get_conversation_history(session_id)

    def explain_routing(self, query: str) -> Dict:
        """
        Explain how a query would be routed (for debugging).

        Args:
            query: Query to analyze

        Returns:
            Dict with routing explanation

        Example:
            >>> explanation = orchestrator.explain_routing(
            >>>     "show my tickets and courses"
            >>> )
            >>> import json
            >>> print(json.dumps(explanation, indent=2))
        """
        return self.router.explain_routing(query)

    def close(self):
        """Clean up resources."""
        self.registry_client.close()
        self.session_client.close()


# =============================================================================
# CLI Interface
# =============================================================================

def authenticate_user() -> tuple[str, str]:
    """
    Authenticate user and return JWT token + user_id.

    Returns:
        (jwt_token, user_id)

    Raises:
        SystemExit: If authentication fails
    """
    print("=" * 80)
    print("Jarvis Authentication")
    print("=" * 80)
    print()

    # Get credentials
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    # Call auth service
    auth_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:9998")

    try:
        response = requests.post(
            f"{auth_url}/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )

        if response.status_code == 401:
            print("✗ Authentication failed: Invalid username or password")
            sys.exit(1)

        response.raise_for_status()

        data = response.json()
        jwt_token = data["access_token"]  # OAuth standard format
        user_info = data["user"]

        print(f"✓ Authenticated as {user_info['username']} ({user_info['role']})")
        print()

        return jwt_token, user_info["username"]

    except requests.ConnectionError:
        print(f"✗ Auth service not available at {auth_url}")
        print("  Start it with: python -m auth.auth_server")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        logger.exception("Authentication failed")
        sys.exit(1)


def main():
    """
    Main CLI interface for Jarvis.

    Usage:
        python jarvis_agent/main_with_registry.py
    """
    print("=" * 80)
    print("Jarvis AI Assistant (Registry Service Version)")
    print("=" * 80)
    print()

    # Check for GOOGLE_API_KEY
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable not set")
        print("Please set it with: export GOOGLE_API_KEY=your_api_key")
        sys.exit(1)

    # Authenticate user
    jwt_token, user_id = authenticate_user()

    # Initialize orchestrator with JWT
    try:
        orchestrator = JarvisOrchestrator(jwt_token=jwt_token)
    except ConnectionError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: Invalid JWT token: {e}")
        sys.exit(1)

    # Get or resume session
    session_id = orchestrator.get_or_create_session(user_id)
    session_data = orchestrator.session_client.get_session(session_id)

    print()

    if session_data:
        history = session_data.get('conversation_history', [])

        if len(history) > 0:
            # Resuming existing session
            print("=" * 80)
            print(f"✓ Welcome back! Resuming session from {session_data['updated_at'][:16]}")
            print(f"  Session ID: {session_id[:8]}...")
            print(f"  Messages: {len(history)}")

            # Show preview of last message
            last_msg = history[-1]
            preview = last_msg['content'][:70]
            if len(last_msg['content']) > 70:
                preview += "..."
            print(f"  Last: {preview}")
            print()
            print("  Type /history to see full conversation")
            print("=" * 80)
        else:
            # New session
            print(f"✓ New session created: {session_id[:8]}...")

    print()
    print("Jarvis is ready! Type your queries below.")
    print("Commands:")
    print("  /help    - Show help")
    print("  /history - Show conversation history")
    print("  /exit    - Exit")
    print()

    # Main loop
    while True:
        try:
            query = input(f"{user_id}> ").strip()

            if not query:
                continue

            if query == "/exit":
                print("Goodbye!")
                break

            if query == "/help":
                print("\nAvailable commands:")
                print("  /help    - Show this help")
                print("  /history - Show conversation history")
                print("  /exit    - Exit Jarvis")
                print("\nExample queries:")
                print("  - Show my tickets")
                print("  - What's our AWS cost?")
                print("  - Show courses for alice")
                print("  - Show my tickets and courses")
                print()
                continue

            if query == "/history":
                history = orchestrator.get_session_history(session_id)
                print("\nConversation History:")
                print("-" * 80)
                for msg in history:
                    role = msg["role"].upper()
                    content = msg["content"]
                    print(f"{role}: {content}")
                    print()
                print("-" * 80)
                print()
                continue

            # Handle query
            response = orchestrator.handle_query_with_session(session_id, query)

            print()
            print("Jarvis>", response)
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"ERROR: {e}")
            logger.exception("Error handling query")

    # Cleanup
    orchestrator.close()


if __name__ == "__main__":
    main()
