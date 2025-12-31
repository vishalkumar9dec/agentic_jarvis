"""
Agent Registry with optional persistence capabilities.

This module provides a unified AgentRegistry class that supports:
- Dynamic agent discovery and routing
- Optional persistence to disk (when FileStore provided)
- Automatic agent recreation from factory configurations
- Rollback on persistence failure

Key Features:
- In-memory agent storage
- Capability-based agent discovery
- Optional FileStore-based persistence
- Agent recreation from factory configurations
- Auto-persist on all modifications (when enabled)

Architecture:
- AgentCapability: Structured capability representation
- RegisteredAgent: Agent registration entry
- AgentRegistry: Unified registry with optional persistence
"""

import logging
from typing import List, Dict, Optional, Set, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timezone
from google.adk.agents import LlmAgent

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from agent_registry_service.registry.file_store import FileStore
    from agent_registry_service.registry.agent_factory_resolver import AgentFactoryResolver

logger = logging.getLogger(__name__)


# =============================================================================
# Base Classes (from original agent_registry.py)
# =============================================================================

@dataclass
class AgentCapability:
    """
    Structured representation of agent capabilities.

    Attributes:
        domains: Primary domains this agent handles
        operations: What operations agent can perform
        entities: What entities agent works with
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

    @classmethod
    def from_dict(cls, data: Dict) -> "AgentCapability":
        """Create from dictionary."""
        data = data.copy()
        data["keywords"] = set(data.get("keywords", []))
        return cls(**data)

    def matches_query(self, query: str) -> float:
        """Calculate match score for a query (0.0 to 1.0)."""
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
    """Agent registration entry in the registry."""
    agent: LlmAgent
    capabilities: AgentCapability
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    enabled: bool = True
    tags: Set[str] = field(default_factory=set)

    def matches_query(self, query: str) -> float:
        """Calculate match score for this agent."""
        if not self.enabled:
            return 0.0
        return self.capabilities.matches_query(query)


class AgentRegistry:
    """
    Central registry for dynamic agent discovery with optional persistence.

    Features:
    - In-memory agent storage and discovery
    - Optional file-based persistence (when FileStore provided)
    - Automatic agent recreation from factory configs
    - Auto-persist on modifications (when persistence enabled)

    Example (In-memory only):
        >>> registry = AgentRegistry()
        >>> registry.register(agent, capabilities)

    Example (With persistence):
        >>> from agent_registry_service.registry.file_store import FileStore
        >>> from agent_registry_service.registry.agent_factory_resolver import AgentFactoryResolver
        >>>
        >>> store = FileStore("data/registry.json")
        >>> resolver = AgentFactoryResolver()
        >>> registry = AgentRegistry(file_store=store, factory_resolver=resolver)
        >>> # Auto-loads existing agents and auto-saves on modifications
    """

    def __init__(
        self,
        file_store: Optional['FileStore'] = None,
        factory_resolver: Optional['AgentFactoryResolver'] = None,
        auto_load: bool = True
    ):
        """
        Initialize agent registry.

        Args:
            file_store: Optional FileStore for persistence
            factory_resolver: Optional AgentFactoryResolver for agent recreation
            auto_load: Whether to load existing registry on startup (requires file_store and factory_resolver)
        """
        self.agents: Dict[str, RegisteredAgent] = {}
        self._capability_cache: Dict[str, List[str]] = {}

        # Persistence dependencies (optional)
        self.file_store = file_store
        self.factory_resolver = factory_resolver
        self._agent_configs: Dict[str, Dict] = {}  # Store factory configs for persistence

        # Validate dependencies
        if file_store and not factory_resolver:
            logger.warning("FileStore provided without AgentFactoryResolver - agents won't be reloaded on startup")
        if factory_resolver and not file_store:
            logger.warning("AgentFactoryResolver provided without FileStore - persistence disabled")

        logger.info(f"AgentRegistry initialized (persistence: {self._persistence_enabled()})")

        # Auto-load existing agents if persistence enabled
        if auto_load and self._persistence_enabled():
            self._load_from_file()

    def _persistence_enabled(self) -> bool:
        """Check if persistence is enabled."""
        return self.file_store is not None and self.factory_resolver is not None

    def register(
        self,
        agent: LlmAgent,
        capabilities: Optional[AgentCapability] = None,
        tags: Optional[Set[str]] = None,
        agent_config: Optional[Dict] = None
    ) -> None:
        """
        Register an agent with the registry.

        Args:
            agent: LlmAgent instance to register
            capabilities: Agent capabilities (auto-extracted if None)
            tags: Optional tags for filtering
            agent_config: Factory configuration for persistence (required if persistence enabled)
                Format: {
                    "agent_type": "tickets",
                    "factory_module": "jarvis_agent.mcp_agents.agent_factory",
                    "factory_function": "create_tickets_agent",
                    "factory_params": {}
                }
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

        # Store agent config for persistence
        if agent_config:
            self._agent_configs[agent.name] = agent_config

        # Auto-persist if enabled
        if self._persistence_enabled():
            self._persist()

    def _auto_extract_capabilities(self, agent: LlmAgent) -> AgentCapability:
        """Automatically extract capabilities from agent metadata."""
        name_parts = agent.name.lower().replace("agent", "").split()
        domains = [p for p in name_parts if p]

        keywords = set()
        if agent.description:
            words = agent.description.lower().split()
            keywords = {w.strip('.,;:') for w in words if len(w) > 4}

        if hasattr(agent, 'instruction') and agent.instruction:
            instruction_preview = agent.instruction[:200].lower()
            words = instruction_preview.split()
            keywords.update({w.strip('.,;:') for w in words if len(w) > 4})

        entities = []
        if hasattr(agent, 'tools') and agent.tools:
            for tool in agent.tools:
                if hasattr(tool, 'name'):
                    tool_parts = tool.name.replace('_', ' ').split()
                    entities.extend([p for p in tool_parts if p not in {'get', 'create', 'update', 'delete', 'list', 'show'}])

        return AgentCapability(
            domains=domains,
            keywords=keywords,
            entities=list(set(entities))
        )

    def unregister(self, agent_name: str) -> bool:
        """Unregister an agent from the registry."""
        if agent_name in self.agents:
            del self.agents[agent_name]
            if agent_name in self._agent_configs:
                del self._agent_configs[agent_name]
            self._invalidate_cache()

            # Auto-persist if enabled
            if self._persistence_enabled():
                self._persist()

            return True
        return False

    def discover(
        self,
        query: str,
        min_score: float = 0.1,
        max_agents: Optional[int] = None,
        tags: Optional[Set[str]] = None
    ) -> List[LlmAgent]:
        """Discover relevant agents for a query."""
        matches = []

        for registered in self.agents.values():
            if tags and not (registered.tags & tags):
                continue

            score = registered.matches_query(query)

            if score >= min_score:
                matches.append((score, registered.capabilities.priority, registered.agent))

        matches.sort(key=lambda x: (x[0], x[1]), reverse=True)

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
        """List all registered agent names."""
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

            # Auto-persist if enabled
            if self._persistence_enabled():
                self._persist()

            return True
        return False

    def disable_agent(self, agent_name: str) -> bool:
        """Disable an agent."""
        if agent_name in self.agents:
            self.agents[agent_name].enabled = False

            # Auto-persist if enabled
            if self._persistence_enabled():
                self._persist()

            return True
        return False

    def update_capabilities(
        self,
        agent_name: str,
        capabilities: AgentCapability
    ) -> bool:
        """
        Update agent capabilities.

        Args:
            agent_name: Name of agent to update
            capabilities: New capabilities

        Returns:
            True if updated, False if agent not found
        """
        if agent_name not in self.agents:
            return False

        self.agents[agent_name].capabilities = capabilities

        # Auto-persist if enabled
        if self._persistence_enabled():
            self._persist()

        return True

    def _invalidate_cache(self):
        """Invalidate internal caches after registry changes."""
        self._capability_cache.clear()

    def export_registry(self) -> Dict[str, Any]:
        """Export registry to JSON-serializable format."""
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

    # =========================================================================
    # Persistence Methods (when FileStore + AgentFactoryResolver provided)
    # =========================================================================

    def _persist(self) -> None:
        """
        Save current registry state to file.

        Only called when persistence is enabled.
        Implements rollback: if save fails, attempts to restore from backup.
        """
        if not self._persistence_enabled():
            return

        # Import here to avoid circular dependency
        from agent_registry_service.registry.file_store import FileStoreError

        try:
            registry_data = self._serialize_registry()
            self.file_store.save(registry_data)
            logger.debug("Registry persisted successfully")

        except FileStoreError as e:
            logger.error(f"Failed to persist registry: {e}")
            # Attempt rollback
            logger.info("Attempting rollback from backup")
            try:
                self.file_store.restore_from_backup()
                logger.info("Rollback successful")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
            raise

    def _load_from_file(self) -> None:
        """
        Load registry from file on startup.

        Only called when persistence is enabled.

        Process:
        1. Load JSON from FileStore
        2. For each agent config:
           - For local agents: Use AgentFactoryResolver to create agent instance
           - For remote agents: Create RemoteA2aAgent from agent card URL
           - Register with saved capabilities/tags/enabled status
        """
        if not self._persistence_enabled():
            return

        # Import here to avoid circular dependency
        from agent_registry_service.registry.file_store import FileStoreError
        from agent_registry_service.registry.agent_factory_resolver import AgentFactoryError

        try:
            data = self.file_store.load()

            if not data.get("agents"):
                logger.info("No agents to load from file")
                return

            agents_data = data["agents"]
            loaded_count = 0

            for agent_name, agent_data in agents_data.items():
                try:
                    agent_type = agent_data.get("type", "local")

                    if agent_type == "remote":
                        # Recreate remote agent from agent card URL
                        from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

                        agent_config = {
                            "type": "remote",
                            "agent_type": agent_data["agent_type"],
                            "agent_card_url": agent_data["agent_card_url"],
                            "status": agent_data.get("status", "pending"),
                            "provider": agent_data.get("provider", {})
                        }

                        # Add auth_config if present
                        if "auth_config" in agent_data:
                            agent_config["auth_config"] = agent_data["auth_config"]

                        agent = RemoteA2aAgent(
                            name=agent_data["name"],
                            description=agent_data.get("description", "Remote agent"),
                            agent_card=agent_data["agent_card_url"]
                        )

                    else:
                        # Recreate local agent from factory config
                        agent_config = {
                            "type": "local",
                            "agent_type": agent_data["agent_type"],
                            "factory_module": agent_data["factory_module"],
                            "factory_function": agent_data["factory_function"],
                            "factory_params": agent_data.get("factory_params", {})
                        }

                        agent = self.factory_resolver.create_agent(agent_config)

                    # Recreate capabilities
                    capabilities = AgentCapability.from_dict(agent_data["capabilities"])

                    # Temporarily disable persistence during load
                    temp_file_store = self.file_store
                    self.file_store = None

                    # Register agent
                    self.register(
                        agent,
                        capabilities,
                        tags=set(agent_data.get("tags", [])),
                        agent_config=agent_config
                    )

                    # Restore enabled status
                    self.agents[agent_name].enabled = agent_data.get("enabled", True)

                    # Restore file_store
                    self.file_store = temp_file_store

                    loaded_count += 1
                    logger.debug(f"Loaded {agent_type} agent '{agent_name}'")

                except (AgentFactoryError, KeyError) as e:
                    logger.error(f"Failed to load agent '{agent_name}': {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error loading agent '{agent_name}': {e}")
                    continue

            logger.info(f"Loaded {loaded_count}/{len(agents_data)} agents from file")

        except FileStoreError as e:
            logger.error(f"Failed to load registry from file: {e}")
            # Continue with empty registry

    def _serialize_registry(self) -> Dict:
        """
        Serialize registry to JSON format.

        Stores only metadata, not agent instances.
        Supports both local agents (factory-based) and remote agents (A2A-based).

        Returns:
            Dictionary with agents metadata and factory configs
        """
        serialized = {
            "agents": {}
        }

        for agent_name, registered in self.agents.items():
            agent_config = self._agent_configs.get(agent_name, {})

            # Base fields common to all agents
            agent_data = {
                "name": registered.agent.name,
                "description": registered.agent.description or "",
                "agent_type": agent_config.get("agent_type", "unknown"),
                "type": agent_config.get("type", "local"),  # local or remote
                "capabilities": registered.capabilities.to_dict(),
                "tags": list(registered.tags),
                "enabled": registered.enabled,
                "registered_at": registered.registered_at.isoformat()
            }

            # Add type-specific fields
            if agent_config.get("type") == "remote":
                # Remote agent fields
                agent_data["agent_card_url"] = agent_config.get("agent_card_url", "")
                agent_data["status"] = agent_config.get("status", "pending")
                agent_data["provider"] = agent_config.get("provider", {})
                if "auth_config" in agent_config:
                    agent_data["auth_config"] = agent_config.get("auth_config")
            else:
                # Local agent fields (factory-based)
                agent_data["factory_module"] = agent_config.get("factory_module", "")
                agent_data["factory_function"] = agent_config.get("factory_function", "")
                agent_data["factory_params"] = agent_config.get("factory_params", {})

            serialized["agents"][agent_name] = agent_data

        return serialized
