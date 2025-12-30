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
        user_id="alice",
        query="show my tickets and courses"
    )
"""

import os
import sys
import logging
import time
import uuid
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
        >>>     user_id="alice",
        >>>     query="show my tickets and courses"
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
        registry_url: str = "http://localhost:8003",
        session_url: str = "http://localhost:8003",
        timeout: int = 10
    ):
        """
        Initialize Jarvis orchestrator.

        Args:
            registry_url: URL of Agent Registry Service
            session_url: URL of Session Management Service
            timeout: Request timeout in seconds
        """
        logger.info("Initializing Jarvis Orchestrator with Registry Service")

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
        Get existing session for user or create new one.

        Args:
            user_id: User identifier

        Returns:
            Session ID

        Example:
            >>> session_id = orchestrator.get_or_create_session("alice")
        """
        if user_id in self._user_sessions:
            session_id = self._user_sessions[user_id]

            # Verify session still exists
            session_data = self.session_client.get_session(session_id)
            if session_data:
                return session_id

        # Create new session
        return self.create_session(user_id)

    def handle_query(
        self,
        user_id: str,
        query: str,
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
            user_id: User identifier
            query: User query string
            session_id: Optional session ID (creates new if None)

        Returns:
            Combined response string

        Example:
            >>> response = orchestrator.handle_query(
            >>>     user_id="alice",
            >>>     query="show my tickets and courses"
            >>> )
            >>> print(response)
        """
        start_time = time.time()

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

        # Decompose query into agent-specific sub-queries
        sub_queries = self._decompose_query(query, agents)

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
        agents: List[LlmAgent]
    ) -> Dict[str, str]:
        """
        Decompose a multi-agent query into agent-specific sub-queries.

        Args:
            original_query: The original user query
            agents: List of agents to handle the query

        Returns:
            Dict mapping agent names to their specific sub-queries

        Example:
            Query: "show all tickets and aws cost"
            Returns: {
                "TicketsAgent": "show all tickets",
                "FinOpsAgent": "show aws cost"
            }
        """
        # If only one agent, return original query
        if len(agents) == 1:
            return {agents[0].name: original_query}

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

        prompt = f"""Given a user query and multiple specialized agents, break down the query into agent-specific sub-queries.

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

Example:
Query: "show all tickets and aws cost"
Agents: TicketsAgent (IT operations), FinOpsAgent (cloud costs)
Output:
{{
    "TicketsAgent": "show all tickets",
    "FinOpsAgent": "show aws cost"
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
        return self.handle_query(user_id, query, session_id)

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

    # Initialize orchestrator
    try:
        orchestrator = JarvisOrchestrator()
    except ConnectionError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("Jarvis is ready! Type your queries below.")
    print("Commands:")
    print("  /help    - Show help")
    print("  /history - Show conversation history")
    print("  /exit    - Exit")
    print()

    # Get user ID
    user_id = input("Enter your username: ").strip()
    if not user_id:
        user_id = "guest"

    # Create session
    session_id = orchestrator.create_session(user_id)
    print(f"Session created: {session_id}")
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
