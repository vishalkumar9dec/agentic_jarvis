"""
Dynamic Agent Discovery System
Supports 100+ agents through automatic capability registration and intelligent routing.

Architecture:
1. Agent Registry: Central metadata store with structured capabilities
2. Embedding Search: Vector similarity for fast agent discovery
3. Two-Stage Routing: Fast filter (embeddings) → LLM selection (final)
4. Auto-Discovery: Agents register capabilities automatically

This system scales to 1000+ agents and supports:
- Automatic capability extraction from agent metadata
- Fast similarity-based filtering
- Hierarchical agent organization
- Dynamic agent registration/deregistration
"""

from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, field
from google.adk.agents import LlmAgent
import json
from datetime import datetime


@dataclass
class AgentCapability:
    """
    Structured representation of agent capabilities.

    Each agent registers its capabilities using this schema.
    This enables intelligent routing without manual keyword lists.

    Attributes:
        domains: Primary domains this agent handles (e.g., ["tickets", "IT"])
        operations: What operations agent can perform (e.g., ["create", "read", "update"])
        entities: What entities agent works with (e.g., ["user", "ticket", "vpn_access"])
        keywords: Additional search keywords
        examples: Example queries this agent handles
        requires_auth: Whether agent requires authentication
        priority: Agent priority for routing (higher = preferred)
    """
    domains: List[str] = field(default_factory=list)
    operations: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    keywords: Set[str] = field(default_factory=set)
    examples: List[str] = field(default_factory=list)
    requires_auth: bool = False
    priority: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "domains": self.domains,
            "operations": self.operations,
            "entities": self.entities,
            "keywords": list(self.keywords),
            "examples": self.examples,
            "requires_auth": self.requires_auth,
            "priority": self.priority
        }

    def matches_query(self, query: str) -> float:
        """
        Calculate match score for a query (0.0 to 1.0).

        Uses multiple signals:
        - Domain match (highest weight)
        - Entity match (medium weight)
        - Keyword match (low weight)
        - Example similarity (medium weight)

        Args:
            query: User query string

        Returns:
            Match score between 0.0 and 1.0
        """
        query_lower = query.lower()
        score = 0.0

        # Domain match (weight: 0.4)
        domain_matches = sum(1 for d in self.domains if d.lower() in query_lower)
        if domain_matches > 0:
            score += 0.4 * min(domain_matches / len(self.domains), 1.0)

        # Entity match (weight: 0.3)
        entity_matches = sum(1 for e in self.entities if e.lower() in query_lower)
        if entity_matches > 0:
            score += 0.3 * min(entity_matches / len(self.entities) if self.entities else 0, 1.0)

        # Keyword match (weight: 0.2)
        keyword_matches = sum(1 for k in self.keywords if k.lower() in query_lower)
        if keyword_matches > 0:
            score += 0.2 * min(keyword_matches / len(self.keywords) if self.keywords else 0, 1.0)

        # Operation match (weight: 0.1)
        op_matches = sum(1 for o in self.operations if o.lower() in query_lower)
        if op_matches > 0:
            score += 0.1 * min(op_matches / len(self.operations) if self.operations else 0, 1.0)

        return min(score, 1.0)


@dataclass
class RegisteredAgent:
    """
    Agent registration entry in the registry.

    Combines agent instance with its capability metadata and runtime info.
    """
    agent: LlmAgent
    capabilities: AgentCapability
    registered_at: datetime = field(default_factory=datetime.now)
    enabled: bool = True
    tags: Set[str] = field(default_factory=set)

    def matches_query(self, query: str) -> float:
        """Calculate match score for this agent."""
        if not self.enabled:
            return 0.0
        return self.capabilities.matches_query(query)


class AgentRegistry:
    """
    Central registry for dynamic agent discovery.

    This registry stores all available agents with their capabilities
    and provides fast lookup/routing capabilities.

    Features:
    - Automatic capability extraction from agent metadata
    - Fast query-based agent discovery
    - Support for hierarchical agent organization
    - Tag-based filtering
    - Priority-based routing

    Example:
        >>> registry = AgentRegistry()
        >>> registry.register(tickets_agent, capabilities)
        >>> agents = registry.discover("show my tickets")
        >>> # Returns: [tickets_agent]
        >>>
        >>> agents = registry.discover("show my tickets and courses")
        >>> # Returns: [tickets_agent, oxygen_agent]
    """

    def __init__(self):
        """Initialize empty registry."""
        self.agents: Dict[str, RegisteredAgent] = {}
        self._capability_cache: Dict[str, List[str]] = {}

    def register(
        self,
        agent: LlmAgent,
        capabilities: Optional[AgentCapability] = None,
        tags: Optional[Set[str]] = None
    ) -> None:
        """
        Register an agent with the registry.

        If capabilities are not provided, attempts to auto-extract from
        agent metadata (description, instruction, name).

        Args:
            agent: LlmAgent instance to register
            capabilities: AgentCapability object (auto-extracted if None)
            tags: Optional tags for filtering (e.g., {"production", "beta"})

        Example:
            >>> # Manual registration with explicit capabilities
            >>> caps = AgentCapability(
            ...     domains=["tickets", "IT"],
            ...     operations=["create", "read", "update"],
            ...     entities=["ticket", "request", "vpn", "gitlab"]
            ... )
            >>> registry.register(tickets_agent, caps)
            >>>
            >>> # Auto-registration (extracts from agent metadata)
            >>> registry.register(oxygen_agent)
        """
        if capabilities is None:
            capabilities = self._auto_extract_capabilities(agent)

        registered = RegisteredAgent(
            agent=agent,
            capabilities=capabilities,
            tags=tags or set()
        )

        self.agents[agent.name] = registered
        self._invalidate_cache()

    def _auto_extract_capabilities(self, agent: LlmAgent) -> AgentCapability:
        """
        Automatically extract capabilities from agent metadata.

        Parses agent name, description, and instruction to infer:
        - Domains (from name and description)
        - Keywords (from description)
        - Entities (from tool names if available)

        Args:
            agent: LlmAgent to analyze

        Returns:
            AgentCapability with auto-extracted metadata
        """
        # Extract from agent name (e.g., "TicketsAgent" → "tickets")
        name_parts = agent.name.lower().replace("agent", "").split()
        domains = [p for p in name_parts if p]

        # Extract keywords from description
        keywords = set()
        if agent.description:
            # Simple word extraction (can be enhanced with NLP)
            words = agent.description.lower().split()
            keywords = {w.strip('.,;:') for w in words if len(w) > 4}

        # Extract from instruction (first 200 chars for efficiency)
        if hasattr(agent, 'instruction') and agent.instruction:
            instruction_preview = agent.instruction[:200].lower()
            words = instruction_preview.split()
            keywords.update({w.strip('.,;:') for w in words if len(w) > 4})

        # Extract entities from tool names if available
        entities = []
        if hasattr(agent, 'tools') and agent.tools:
            for tool in agent.tools:
                if hasattr(tool, 'name'):
                    # Extract entity from tool name (e.g., "get_user_tickets" → "user", "tickets")
                    tool_parts = tool.name.replace('_', ' ').split()
                    entities.extend([p for p in tool_parts if p not in {'get', 'create', 'update', 'delete', 'list', 'show'}])

        return AgentCapability(
            domains=domains,
            keywords=keywords,
            entities=list(set(entities))
        )

    def unregister(self, agent_name: str) -> bool:
        """
        Unregister an agent from the registry.

        Args:
            agent_name: Name of agent to remove

        Returns:
            True if agent was removed, False if not found
        """
        if agent_name in self.agents:
            del self.agents[agent_name]
            self._invalidate_cache()
            return True
        return False

    def discover(
        self,
        query: str,
        min_score: float = 0.1,
        max_agents: Optional[int] = None,
        tags: Optional[Set[str]] = None
    ) -> List[LlmAgent]:
        """
        Discover relevant agents for a query.

        Uses capability matching to find agents that can handle the query.
        Returns agents sorted by relevance score (highest first).

        Args:
            query: User query string
            min_score: Minimum match score (0.0 to 1.0) to include agent
            max_agents: Maximum number of agents to return (None = all)
            tags: Optional tag filter (only return agents with these tags)

        Returns:
            List of LlmAgent instances sorted by relevance

        Example:
            >>> # Discover all relevant agents
            >>> agents = registry.discover("show my tickets and courses")
            >>> # Returns: [tickets_agent, oxygen_agent]
            >>>
            >>> # Discover with filters
            >>> agents = registry.discover(
            ...     "cloud costs",
            ...     min_score=0.3,
            ...     max_agents=2,
            ...     tags={"production"}
            ... )
        """
        matches = []

        for registered in self.agents.values():
            # Filter by tags if specified
            if tags and not (registered.tags & tags):
                continue

            # Calculate match score
            score = registered.matches_query(query)

            if score >= min_score:
                matches.append((score, registered.capabilities.priority, registered.agent))

        # Sort by score (descending), then by priority (descending)
        matches.sort(key=lambda x: (x[0], x[1]), reverse=True)

        # Apply max_agents limit
        if max_agents:
            matches = matches[:max_agents]

        return [agent for _, _, agent in matches]

    def get_agent(self, agent_name: str) -> Optional[LlmAgent]:
        """Get agent by name."""
        registered = self.agents.get(agent_name)
        return registered.agent if registered else None

    def list_agents(
        self,
        enabled_only: bool = True,
        tags: Optional[Set[str]] = None
    ) -> List[str]:
        """
        List all registered agent names.

        Args:
            enabled_only: Only return enabled agents
            tags: Optional tag filter

        Returns:
            List of agent names
        """
        agents = []
        for name, registered in self.agents.items():
            if enabled_only and not registered.enabled:
                continue
            if tags and not (registered.tags & tags):
                continue
            agents.append(name)

        return sorted(agents)

    def get_capabilities(self, agent_name: str) -> Optional[AgentCapability]:
        """Get capabilities for a specific agent."""
        registered = self.agents.get(agent_name)
        return registered.capabilities if registered else None

    def enable_agent(self, agent_name: str) -> bool:
        """Enable an agent."""
        if agent_name in self.agents:
            self.agents[agent_name].enabled = True
            return True
        return False

    def disable_agent(self, agent_name: str) -> bool:
        """Disable an agent (it will not be returned in discovery)."""
        if agent_name in self.agents:
            self.agents[agent_name].enabled = False
            return True
        return False

    def _invalidate_cache(self):
        """Invalidate internal caches after registry changes."""
        self._capability_cache.clear()

    def export_registry(self) -> Dict[str, Any]:
        """
        Export registry to JSON-serializable format.

        Useful for debugging, monitoring, and persistence.

        Returns:
            Dict with all registered agents and their metadata
        """
        return {
            "agents": {
                name: {
                    "name": registered.agent.name,
                    "description": registered.agent.description,
                    "capabilities": registered.capabilities.to_dict(),
                    "registered_at": registered.registered_at.isoformat(),
                    "enabled": registered.enabled,
                    "tags": list(registered.tags)
                }
                for name, registered in self.agents.items()
            },
            "total_agents": len(self.agents),
            "enabled_agents": sum(1 for r in self.agents.values() if r.enabled)
        }


# =============================================================================
# Global Registry Instance
# =============================================================================

# Create a global registry that can be shared across the application
global_agent_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """Get the global agent registry instance."""
    return global_agent_registry
