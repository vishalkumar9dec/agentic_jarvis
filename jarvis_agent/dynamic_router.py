"""
Two-Stage Dynamic Agent Router
Efficiently routes queries to relevant agents using a two-stage approach.

Stage 1: Fast Filtering (O(n) capability matching)
   - Uses AgentRegistry to quickly filter to top 5-10 candidates
   - Based on capability scores, domains, keywords
   - Handles 1000+ agents efficiently

Stage 2: LLM Selection (semantic understanding)
   - LLM analyzes query + candidate agent descriptions
   - Makes final selection based on semantic understanding
   - Only processes filtered candidates (not all agents)

This approach combines:
- Speed (fast filtering eliminates 90%+ of agents)
- Accuracy (LLM makes final decision with context)
- Scalability (works with 100+ agents)
"""

from typing import List, Dict, Optional, Tuple
from google.adk.agents import LlmAgent
from google.genai import types
import google.generativeai as genai
from jarvis_agent.agent_registry import AgentRegistry, AgentCapability
import json
import os


class TwoStageRouter:
    """
    Two-stage router for efficient agent discovery at scale.

    Workflow:
    1. User query → Fast Filter (capability matching) → Top candidates
    2. Top candidates + query → LLM Selection → Final agents to invoke
    3. Invoke selected agents → Combine results → Response

    This approach is:
    - Fast: Stage 1 is O(n), handles 1000+ agents in milliseconds
    - Accurate: Stage 2 uses LLM for semantic understanding
    - Scalable: Only sends 5-10 candidates to LLM, not all agents

    Example:
        >>> router = TwoStageRouter(registry)
        >>> agents = router.route("show my tickets and courses")
        >>> # Stage 1: Filters 100 agents down to 5 candidates
        >>> # Stage 2: LLM selects tickets_agent and oxygen_agent
        >>> # Returns: [tickets_agent, oxygen_agent]
    """

    def __init__(
        self,
        registry: AgentRegistry,
        model: str = "gemini-2.0-flash-exp",
        stage1_max_candidates: int = 10,
        stage1_min_score: float = 0.1
    ):
        """
        Initialize two-stage router.

        Args:
            registry: AgentRegistry instance with registered agents
            model: Gemini model to use for Stage 2 LLM selection
            stage1_max_candidates: Max candidates to pass to Stage 2
            stage1_min_score: Minimum score for Stage 1 filtering
        """
        self.registry = registry
        self.model = model
        self.stage1_max_candidates = stage1_max_candidates
        self.stage1_min_score = stage1_min_score

        # Initialize Gemini for Stage 2
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)

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
            require_all_matches: If True, return ALL agents that match (for multi-domain queries)
                                If False, return only the best matching agent
            fallback_to_stage1: If Stage 2 fails, fallback to Stage 1 results

        Returns:
            List of LlmAgent instances that should handle this query

        Example:
            >>> # Multi-domain query
            >>> agents = router.route("show my tickets and courses")
            >>> # Returns: [tickets_agent, oxygen_agent]
            >>>
            >>> # Single-domain query
            >>> agents = router.route("what's the status of ticket 12301?")
            >>> # Returns: [tickets_agent]
        """
        # Stage 1: Fast filtering using capability matching
        candidates = self._stage1_fast_filter(query)

        if not candidates:
            # No candidates found
            return []

        # If only 1-2 candidates, skip Stage 2 (no need for LLM)
        if len(candidates) <= 2:
            return [agent for agent, _ in candidates]

        # Stage 2: LLM-based selection
        try:
            selected_agents = self._stage2_llm_selection(
                query,
                candidates,
                require_all_matches
            )

            if selected_agents:
                return selected_agents

        except Exception as e:
            print(f"Warning: Stage 2 LLM selection failed: {e}")
            if not fallback_to_stage1:
                raise

        # Fallback: Return Stage 1 results
        return [agent for agent, _ in candidates]

    def _stage1_fast_filter(self, query: str) -> List[Tuple[LlmAgent, float]]:
        """
        Stage 1: Fast capability-based filtering.

        Uses AgentRegistry's discover() to quickly filter to top candidates
        based on domain/keyword/entity matching.

        Args:
            query: User query string

        Returns:
            List of (agent, score) tuples sorted by score (descending)
        """
        # Use registry's discover method which already does scoring
        agents = self.registry.discover(
            query=query,
            min_score=self.stage1_min_score,
            max_agents=self.stage1_max_candidates
        )

        # Get scores for each agent
        agent_scores = []
        for agent in agents:
            registered = self.registry.agents.get(agent.name)
            if registered:
                score = registered.matches_query(query)
                agent_scores.append((agent, score))

        # Sort by score (descending)
        agent_scores.sort(key=lambda x: x[1], reverse=True)

        return agent_scores

    def _stage2_llm_selection(
        self,
        query: str,
        candidates: List[Tuple[LlmAgent, float]],
        require_all_matches: bool
    ) -> List[LlmAgent]:
        """
        Stage 2: LLM-based semantic selection.

        Uses Gemini to analyze the query and candidate agents to make
        the final selection based on semantic understanding.

        Args:
            query: User query string
            candidates: List of (agent, score) tuples from Stage 1
            require_all_matches: Whether to select all matching agents

        Returns:
            List of selected LlmAgent instances
        """
        # Build agent descriptions for LLM
        agent_info = []
        for i, (agent, score) in enumerate(candidates):
            agent_info.append({
                "index": i,
                "name": agent.name,
                "description": agent.description or "No description",
                "stage1_score": round(score, 2)
            })

        # Create prompt for LLM
        selection_mode = "all relevant agents" if require_all_matches else "the single best agent"

        prompt = f"""You are an intelligent agent router. Analyze the user query and select {selection_mode} that should handle it.

**User Query:**
{query}

**Available Agents:**
{json.dumps(agent_info, indent=2)}

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
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )

        # Parse response
        try:
            result = json.loads(response.text)
            selected_indices = result.get("selected_agent_indices", [])

            # Map indices back to agents
            selected_agents = []
            for idx in selected_indices:
                if 0 <= idx < len(candidates):
                    agent, _ = candidates[idx]
                    selected_agents.append(agent)

            return selected_agents

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to parse LLM response: {e}")
            return []

    def explain_routing(self, query: str) -> Dict:
        """
        Explain routing decision for debugging/transparency.

        Shows Stage 1 filtering and Stage 2 selection with reasoning.

        Args:
            query: User query to analyze

        Returns:
            Dict with routing explanation and decisions

        Example:
            >>> explanation = router.explain_routing("show my tickets and courses")
            >>> print(json.dumps(explanation, indent=2))
            {
              "query": "show my tickets and courses",
              "stage1_candidates": [
                {"name": "TicketsAgent", "score": 0.85},
                {"name": "OxygenAgent", "score": 0.72},
                {"name": "FinOpsAgent", "score": 0.15}
              ],
              "stage2_selected": ["TicketsAgent", "OxygenAgent"],
              "reasoning": "Multi-domain query requires both agents"
            }
        """
        # Stage 1
        candidates = self._stage1_fast_filter(query)

        stage1_info = [
            {"name": agent.name, "score": round(score, 2)}
            for agent, score in candidates
        ]

        # Stage 2
        if len(candidates) > 2:
            try:
                selected = self._stage2_llm_selection(query, candidates, require_all_matches=True)
                stage2_info = [agent.name for agent in selected]
            except Exception as e:
                stage2_info = f"LLM selection failed: {e}"
        else:
            selected = [agent for agent, _ in candidates]
            stage2_info = [agent.name for agent in selected]

        return {
            "query": query,
            "stage1_candidates": stage1_info,
            "stage2_selected": stage2_info,
            "total_agents_in_registry": len(self.registry.agents)
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_router(registry: AgentRegistry) -> TwoStageRouter:
    """
    Create a two-stage router with default settings.

    Args:
        registry: AgentRegistry with registered agents

    Returns:
        Configured TwoStageRouter instance
    """
    return TwoStageRouter(
        registry=registry,
        stage1_max_candidates=10,
        stage1_min_score=0.1
    )
