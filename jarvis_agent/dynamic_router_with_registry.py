"""
Two-Stage Dynamic Agent Router (Registry Service Version)

This is the registry-service version of the two-stage router.
It fetches agents from the centralized Agent Registry Service
instead of using an in-memory registry.

Stage 1: Fast Filtering (capability matching via registry service)
Stage 2: LLM Selection (semantic understanding)

Differences from original dynamic_router.py:
- Uses RegistryClient instead of in-memory AgentRegistry
- Fetches agents from http://localhost:8003 registry service
- Creates actual agent instances using factory resolver
- Otherwise identical routing logic
"""

from typing import List, Dict, Optional, Tuple
from google.adk.agents import LlmAgent
from google import genai
from google.genai import types
from jarvis_agent.registry_client import RegistryClient, AgentInfo
import json
import os
import logging
import importlib

logger = logging.getLogger(__name__)


class AgentFactoryResolver:
    """
    Resolves agent instances from factory configurations.

    The registry service stores factory information (module + function),
    and this resolver creates actual LlmAgent instances on demand.
    """

    def __init__(self):
        """Initialize resolver with module cache."""
        self._module_cache = {}

    def create_agent(
        self,
        factory_module: str,
        factory_function: str,
        factory_params: Optional[Dict] = None
    ) -> LlmAgent:
        """
        Create agent instance from factory.

        Args:
            factory_module: Module path (e.g., "jarvis_agent.mcp_agents.agent_factory")
            factory_function: Function name (e.g., "create_tickets_agent")
            factory_params: Optional parameters to pass to factory

        Returns:
            LlmAgent instance

        Raises:
            ImportError: If module cannot be imported
            AttributeError: If function not found in module
        """
        # Import module (with caching)
        if factory_module not in self._module_cache:
            try:
                module = importlib.import_module(factory_module)
                self._module_cache[factory_module] = module
                logger.debug(f"Imported module: {factory_module}")
            except ImportError as e:
                logger.error(f"Failed to import module '{factory_module}': {e}")
                raise

        module = self._module_cache[factory_module]

        # Get factory function
        if not hasattr(module, factory_function):
            raise AttributeError(
                f"Module '{factory_module}' has no function '{factory_function}'"
            )

        factory = getattr(module, factory_function)

        # Create agent
        if factory_params:
            agent = factory(**factory_params)
        else:
            agent = factory()

        logger.debug(f"Created agent via {factory_module}.{factory_function}")
        return agent


class TwoStageRouterWithRegistry:
    """
    Two-stage router that uses centralized Agent Registry Service.

    Fetches agents from registry service at http://localhost:8003 instead
    of maintaining an in-memory registry.

    Workflow:
    1. User query → Fetch enabled agents from registry service
    2. Fast filter (capability matching) → Top candidates
    3. LLM Selection → Final agents to invoke
    4. Return actual LlmAgent instances (created via factory resolver)

    Example:
        >>> client = RegistryClient(base_url="http://localhost:8003")
        >>> router = TwoStageRouterWithRegistry(registry_client=client)
        >>>
        >>> agents = router.route("show my tickets and courses")
        >>> # Returns: [tickets_agent, oxygen_agent]
        >>>
        >>> for agent in agents:
        >>>     response = agent.run(query)
    """

    def __init__(
        self,
        registry_client: RegistryClient,
        model: str = "gemini-2.0-flash-exp",
        stage1_max_candidates: int = 10,
        stage1_min_score: float = 0.1
    ):
        """
        Initialize router with registry client.

        Args:
            registry_client: RegistryClient connected to registry service
            model: Gemini model for Stage 2 LLM selection
            stage1_max_candidates: Max candidates for Stage 2
            stage1_min_score: Minimum score for Stage 1
        """
        self.registry_client = registry_client
        self.model = model
        self.stage1_max_candidates = stage1_max_candidates
        self.stage1_min_score = stage1_min_score

        # Factory resolver to create agent instances
        self.factory_resolver = AgentFactoryResolver()

        # Initialize Gemini client for Stage 2
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found in environment. Stage 2 LLM selection may fail.")
        self.client = genai.Client(api_key=api_key) if api_key else None

    def route(
        self,
        query: str,
        require_all_matches: bool = True,
        fallback_to_stage1: bool = True
    ) -> List[LlmAgent]:
        """
        Route query to relevant agents using two-stage approach.

        Args:
            query: User query string
            require_all_matches: If True, return ALL matching agents
            fallback_to_stage1: If Stage 2 fails, use Stage 1 results

        Returns:
            List of LlmAgent instances

        Example:
            >>> agents = router.route("show my tickets and courses")
            >>> # Returns: [tickets_agent, oxygen_agent]
        """
        # Stage 1: Fast filtering
        candidates = self._stage1_fast_filter(query)

        if not candidates:
            logger.warning(f"No agents matched query: {query}")
            return []

        # If only 1-2 candidates, skip Stage 2
        if len(candidates) <= 2:
            logger.debug(f"Only {len(candidates)} candidates, skipping Stage 2")
            # Extract AgentInfo from tuples
            agent_infos = [agent_info for agent_info, _ in candidates]
            return self._create_agents(agent_infos)

        # Stage 2: LLM selection
        try:
            selected_agent_infos = self._stage2_llm_selection(
                query,
                candidates,
                require_all_matches
            )

            if selected_agent_infos:
                return self._create_agents(selected_agent_infos)

        except Exception as e:
            logger.error(f"Stage 2 LLM selection failed: {e}")
            if not fallback_to_stage1:
                raise

        # Fallback: Return Stage 1 results
        logger.warning("Falling back to Stage 1 results")
        # Extract AgentInfo from tuples
        agent_infos = [agent_info for agent_info, _ in candidates]
        return self._create_agents(agent_infos)

    def _stage1_fast_filter(self, query: str) -> List[Tuple[AgentInfo, float]]:
        """
        Stage 1: Fast capability-based filtering.

        Fetches agents from registry service and scores them based on
        capability matching.

        Args:
            query: User query string

        Returns:
            List of (AgentInfo, score) tuples sorted by score
        """
        # Fetch enabled agents from registry service
        try:
            agent_infos = self.registry_client.list_agents(enabled_only=True)
        except Exception as e:
            logger.error(f"Failed to fetch agents from registry: {e}")
            return []

        if not agent_infos:
            logger.warning("No agents available in registry")
            return []

        # Score each agent
        agent_scores = []
        for agent_info in agent_infos:
            score = self._calculate_match_score(agent_info, query)

            if score >= self.stage1_min_score:
                agent_scores.append((agent_info, score))

        # Sort by score (descending)
        agent_scores.sort(key=lambda x: x[1], reverse=True)

        # Limit to max candidates
        agent_scores = agent_scores[:self.stage1_max_candidates]

        logger.debug(f"Stage 1: {len(agent_scores)} candidates from {len(agent_infos)} agents")
        return agent_scores

    def _calculate_match_score(self, agent_info: AgentInfo, query: str) -> float:
        """
        Calculate match score for an agent.

        Uses capability matching logic similar to AgentRegistry.

        Args:
            agent_info: Agent information from registry
            query: User query

        Returns:
            Match score (0.0 to 1.0)
        """
        query_lower = query.lower()
        score = 0.0

        capabilities = agent_info.capabilities

        # Domain match (weight: 0.4)
        domains = capabilities.get("domains", [])
        domain_matches = sum(1 for d in domains if d.lower() in query_lower)
        if domain_matches > 0 and domains:
            score += 0.4 * min(domain_matches / len(domains), 1.0)

        # Entity match (weight: 0.3)
        entities = capabilities.get("entities", [])
        entity_matches = sum(1 for e in entities if e.lower() in query_lower)
        if entity_matches > 0 and entities:
            score += 0.3 * min(entity_matches / len(entities), 1.0)

        # Keyword match (weight: 0.2)
        keywords = capabilities.get("keywords", [])
        keyword_matches = sum(1 for k in keywords if k.lower() in query_lower)
        if keyword_matches > 0 and keywords:
            score += 0.2 * min(keyword_matches / len(keywords), 1.0)

        # Operation match (weight: 0.1)
        operations = capabilities.get("operations", [])
        op_matches = sum(1 for o in operations if o.lower() in query_lower)
        if op_matches > 0 and operations:
            score += 0.1 * min(op_matches / len(operations), 1.0)

        return min(score, 1.0)

    def _stage2_llm_selection(
        self,
        query: str,
        candidates: List[Tuple[AgentInfo, float]],
        require_all_matches: bool
    ) -> List[AgentInfo]:
        """
        Stage 2: LLM-based semantic selection.

        Args:
            query: User query
            candidates: List of (AgentInfo, score) from Stage 1
            require_all_matches: Whether to select all matching agents

        Returns:
            List of selected AgentInfo objects
        """
        # Build agent descriptions for LLM
        agent_info_list = []
        for i, (agent_info, score) in enumerate(candidates):
            agent_info_list.append({
                "index": i,
                "name": agent_info.name,
                "description": agent_info.description,
                "stage1_score": round(score, 2),
                "domains": agent_info.capabilities.get("domains", [])
            })

        selection_mode = "all relevant agents" if require_all_matches else "the single best agent"

        prompt = f"""You are an intelligent agent router. Analyze the user query and select {selection_mode} that should handle it.

**User Query:**
{query}

**Available Agents:**
{json.dumps(agent_info_list, indent=2)}

**Instructions:**
1. Carefully analyze the user's query to understand what they're asking for
2. Consider the query may involve multiple domains (e.g., "tickets AND courses")
3. Select ALL agents needed to fully answer the query
4. If query mentions items from different domains, select agents for EACH domain
5. Return response in JSON format

**Response Format:**
{{
    "analysis": "Brief explanation of what the query is asking for",
    "selected_agent_indices": [list of agent indices to invoke],
    "reasoning": "Why these agents were selected"
}}

**Examples:**

Query: "show my tickets"
Response: {{"analysis": "User wants their tickets", "selected_agent_indices": [0], "reasoning": "Only tickets domain involved"}}

Query: "show my tickets and courses"
Response: {{"analysis": "User wants both tickets AND courses", "selected_agent_indices": [0, 2], "reasoning": "Multi-domain query requires both TicketsAgent and OxygenAgent"}}

Query: "what are my pending tickets, upcoming exams, and cloud costs?"
Response: {{"analysis": "User wants data from 3 domains: tickets, learning, costs", "selected_agent_indices": [0, 1, 2], "reasoning": "Multi-domain query requires TicketsAgent, OxygenAgent, and FinOpsAgent"}}

Now analyze the actual query and respond:"""

        # Call Gemini
        if not self.client:
            logger.error("Gemini client not initialized. Cannot perform Stage 2 selection.")
            raise ValueError("GOOGLE_API_KEY not configured")

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT"],
                response_mime_type="application/json"
            )
        )

        # Parse response
        try:
            result = json.loads(response.text)
            selected_indices = result.get("selected_agent_indices", [])

            logger.debug(f"Stage 2 selected indices: {selected_indices}")
            logger.debug(f"Reasoning: {result.get('reasoning')}")

            # Map indices back to AgentInfo objects
            selected_agents = []
            for idx in selected_indices:
                if 0 <= idx < len(candidates):
                    agent_info, _ = candidates[idx]
                    selected_agents.append(agent_info)

            return selected_agents

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []

    def _create_agents(self, agent_infos: List[AgentInfo]) -> List[LlmAgent]:
        """
        Create RemoteA2aAgent instances from AgentInfo objects.

        All agents are now remote A2A agents - no local/factory-based agents.
        Each agent is a self-contained service discovered via agent card URL.

        Args:
            agent_infos: List of AgentInfo from registry

        Returns:
            List of RemoteA2aAgent instances
        """
        from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

        agents = []

        for agent_info in agent_infos:
            try:
                # All agents are remote A2A agents
                agent = RemoteA2aAgent(
                    name=agent_info.name,
                    description=agent_info.description,
                    agent_card=agent_info.agent_card_url
                )
                agents.append(agent)
                logger.debug(f"Created RemoteA2aAgent: {agent_info.name} from {agent_info.agent_card_url}")

            except Exception as e:
                logger.error(f"Failed to create agent '{agent_info.name}': {e}")
                continue

        logger.debug(f"Created {len(agents)} agent instances")
        return agents

    def explain_routing(self, query: str) -> Dict:
        """
        Explain routing decision for debugging/transparency.

        Args:
            query: User query to analyze

        Returns:
            Dict with routing explanation

        Example:
            >>> explanation = router.explain_routing("show my tickets and courses")
            >>> print(json.dumps(explanation, indent=2))
        """
        # Stage 1
        candidates = self._stage1_fast_filter(query)

        stage1_info = [
            {"name": agent_info.name, "score": round(score, 2)}
            for agent_info, score in candidates
        ]

        # Stage 2
        if len(candidates) > 2:
            try:
                selected = self._stage2_llm_selection(query, candidates, require_all_matches=True)
                stage2_info = [agent_info.name for agent_info in selected]
            except Exception as e:
                stage2_info = f"LLM selection failed: {e}"
        else:
            selected = [agent_info for agent_info, _ in candidates]
            stage2_info = [agent_info.name for agent_info in selected]

        # Get total agent count from registry
        try:
            all_agents = self.registry_client.list_agents(enabled_only=False)
            total_agents = len(all_agents)
        except:
            total_agents = "unknown"

        return {
            "query": query,
            "stage1_candidates": stage1_info,
            "stage2_selected": stage2_info,
            "total_agents_in_registry": total_agents
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_router(registry_url: str = "http://localhost:8003") -> TwoStageRouterWithRegistry:
    """
    Create a two-stage router with registry service.

    Args:
        registry_url: URL of Agent Registry Service

    Returns:
        Configured TwoStageRouterWithRegistry instance

    Example:
        >>> router = create_router("http://localhost:8003")
        >>> agents = router.route("show my tickets")
    """
    client = RegistryClient(base_url=registry_url)
    return TwoStageRouterWithRegistry(
        registry_client=client,
        stage1_max_candidates=10,
        stage1_min_score=0.1
    )
