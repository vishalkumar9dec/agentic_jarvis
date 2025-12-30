"""
Registry Client for Jarvis Orchestrator

HTTP client that communicates with the Agent Registry Service.
Replaces in-memory AgentRegistry with remote service calls.

This client is used by the dynamic router to discover and fetch
agents from the centralized Agent Registry Service instead of
maintaining an in-memory registry.

Usage:
    >>> client = RegistryClient(base_url="http://localhost:8003")
    >>> agents = client.list_agents()
    >>> agent_info = client.get_agent("TicketsAgent")
"""

from typing import List, Dict, Optional, Any
import requests
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentInfo:
    """Agent information from registry service."""
    name: str
    description: str
    agent_type: str
    enabled: bool
    tags: List[str]
    capabilities: Dict[str, Any]

    # Type-specific fields
    type: str  # "local" or "remote"

    # Local agent fields
    factory_module: Optional[str] = None
    factory_function: Optional[str] = None

    # Remote agent fields
    agent_card_url: Optional[str] = None
    provider: Optional[Dict[str, str]] = None
    status: Optional[str] = None  # pending, approved, suspended


class RegistryClient:
    """
    HTTP client for Agent Registry Service.

    Provides methods to:
    - List all registered agents
    - Get agent details
    - Register new agents (admin)
    - Update agent capabilities (admin)
    - Enable/disable agents (admin)

    This client is used by the Jarvis orchestrator to dynamically
    discover and route queries to registered agents.

    Example:
        >>> client = RegistryClient(base_url="http://localhost:8003")
        >>>
        >>> # List all enabled agents
        >>> agents = client.list_agents(enabled_only=True)
        >>> for agent in agents:
        >>>     print(f"{agent.name}: {agent.description}")
        >>>
        >>> # Get specific agent
        >>> tickets_agent = client.get_agent("TicketsAgent")
        >>> print(f"Domains: {tickets_agent.capabilities['domains']}")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8003",
        timeout: int = 10
    ):
        """
        Initialize Registry Client.

        Args:
            base_url: Base URL of Agent Registry Service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._session = requests.Session()

    def list_agents(
        self,
        enabled_only: bool = True,
        tags: Optional[List[str]] = None
    ) -> List[AgentInfo]:
        """
        List all registered agents.

        Args:
            enabled_only: Only return enabled agents
            tags: Filter by tags (comma-separated)

        Returns:
            List of AgentInfo objects

        Raises:
            ConnectionError: If registry service is unreachable
            requests.HTTPError: If API returns error

        Example:
            >>> agents = client.list_agents(enabled_only=True)
            >>> print(f"Found {len(agents)} enabled agents")
        """
        try:
            params = {}
            if enabled_only:
                params["enabled_only"] = "true"
            if tags:
                params["tags"] = ",".join(tags)

            response = self._session.get(
                f"{self.base_url}/registry/agents",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            agents_data = data.get("agents", [])

            agents = []
            for agent_data in agents_data:
                agents.append(AgentInfo(
                    name=agent_data["name"],
                    description=agent_data["description"],
                    agent_type=agent_data["agent_type"],
                    enabled=agent_data["enabled"],
                    tags=agent_data.get("tags", []),
                    capabilities=agent_data.get("capabilities", {}),
                    type=agent_data.get("type", "local"),
                    factory_module=agent_data.get("factory_module"),
                    factory_function=agent_data.get("factory_function"),
                    agent_card_url=agent_data.get("agent_card_url"),
                    provider=agent_data.get("provider"),
                    status=agent_data.get("status")
                ))

            logger.info(f"Retrieved {len(agents)} agents from registry")
            return agents

        except requests.ConnectionError as e:
            logger.error(f"Failed to connect to registry service at {self.base_url}: {e}")
            raise ConnectionError(
                f"Registry service not available at {self.base_url}. "
                f"Please start it with: ./scripts/start_registry_service.sh"
            ) from e
        except requests.HTTPError as e:
            logger.error(f"Registry API error: {e}")
            raise

    def get_agent(self, agent_name: str) -> Optional[AgentInfo]:
        """
        Get details for a specific agent.

        Args:
            agent_name: Name of the agent to retrieve

        Returns:
            AgentInfo object or None if not found

        Raises:
            ConnectionError: If registry service is unreachable
            requests.HTTPError: If API returns error (except 404)

        Example:
            >>> agent = client.get_agent("TicketsAgent")
            >>> if agent:
            >>>     print(f"Agent type: {agent.type}")
            >>>     print(f"Capabilities: {agent.capabilities}")
        """
        try:
            response = self._session.get(
                f"{self.base_url}/registry/agents/{agent_name}",
                timeout=self.timeout
            )

            if response.status_code == 404:
                logger.warning(f"Agent '{agent_name}' not found in registry")
                return None

            response.raise_for_status()
            agent_data = response.json()

            return AgentInfo(
                name=agent_data["name"],
                description=agent_data["description"],
                agent_type=agent_data["agent_type"],
                enabled=agent_data["enabled"],
                tags=agent_data.get("tags", []),
                capabilities=agent_data.get("capabilities", {}),
                type=agent_data.get("type", "local"),
                factory_module=agent_data.get("factory_module"),
                factory_function=agent_data.get("factory_function"),
                agent_card_url=agent_data.get("agent_card_url"),
                provider=agent_data.get("provider"),
                status=agent_data.get("status")
            )

        except requests.ConnectionError as e:
            logger.error(f"Failed to connect to registry service: {e}")
            raise ConnectionError(
                f"Registry service not available at {self.base_url}"
            ) from e
        except requests.HTTPError as e:
            logger.error(f"Registry API error for agent '{agent_name}': {e}")
            raise

    def get_capabilities(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get capabilities for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Capabilities dict or None if agent not found

        Example:
            >>> caps = client.get_capabilities("TicketsAgent")
            >>> print(f"Domains: {caps['domains']}")
            >>> print(f"Operations: {caps['operations']}")
        """
        agent = self.get_agent(agent_name)
        return agent.capabilities if agent else None

    def health_check(self) -> bool:
        """
        Check if registry service is healthy.

        Returns:
            True if service is healthy, False otherwise

        Example:
            >>> if client.health_check():
            >>>     print("Registry service is healthy")
            >>> else:
            >>>     print("Registry service is down")
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

    # =========================================================================
    # Admin Methods (for agent registration/management)
    # =========================================================================

    def register_agent(
        self,
        agent_config: Dict[str, Any],
        capabilities: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Register a new local agent (admin operation).

        Args:
            agent_config: Agent configuration with factory details
            capabilities: Agent capabilities
            tags: Optional tags for filtering

        Returns:
            True if registration successful

        Raises:
            requests.HTTPError: If registration fails

        Example:
            >>> config = {
            >>>     "agent_type": "tickets",
            >>>     "factory_module": "jarvis_agent.mcp_agents.agent_factory",
            >>>     "factory_function": "create_tickets_agent"
            >>> }
            >>> caps = {
            >>>     "domains": ["tickets", "IT"],
            >>>     "operations": ["create", "read", "update"],
            >>>     "entities": ["ticket"]
            >>> }
            >>> client.register_agent(config, caps, tags=["production"])
        """
        try:
            payload = {
                "agent_config": agent_config,
                "capabilities": capabilities,
                "tags": tags or []
            }

            response = self._session.post(
                f"{self.base_url}/registry/agents",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.info(f"Successfully registered agent: {agent_config.get('agent_type')}")
            return True

        except requests.HTTPError as e:
            logger.error(f"Failed to register agent: {e}")
            raise

    def update_capabilities(
        self,
        agent_name: str,
        capabilities: Dict[str, Any]
    ) -> bool:
        """
        Update agent capabilities (admin operation).

        Args:
            agent_name: Name of agent to update
            capabilities: New capabilities

        Returns:
            True if update successful

        Raises:
            requests.HTTPError: If update fails
        """
        try:
            response = self._session.put(
                f"{self.base_url}/registry/agents/{agent_name}/capabilities",
                json={"capabilities": capabilities},
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.info(f"Successfully updated capabilities for: {agent_name}")
            return True

        except requests.HTTPError as e:
            logger.error(f"Failed to update agent capabilities: {e}")
            raise

    def enable_agent(self, agent_name: str) -> bool:
        """
        Enable an agent (admin operation).

        Args:
            agent_name: Name of agent to enable

        Returns:
            True if successful
        """
        try:
            response = self._session.patch(
                f"{self.base_url}/registry/agents/{agent_name}/status",
                json={"enabled": True},
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.info(f"Successfully enabled agent: {agent_name}")
            return True

        except requests.HTTPError as e:
            logger.error(f"Failed to enable agent: {e}")
            raise

    def disable_agent(self, agent_name: str) -> bool:
        """
        Disable an agent (admin operation).

        Args:
            agent_name: Name of agent to disable

        Returns:
            True if successful
        """
        try:
            response = self._session.patch(
                f"{self.base_url}/registry/agents/{agent_name}/status",
                json={"enabled": False},
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.info(f"Successfully disabled agent: {agent_name}")
            return True

        except requests.HTTPError as e:
            logger.error(f"Failed to disable agent: {e}")
            raise

    def delete_agent(self, agent_name: str) -> bool:
        """
        Delete an agent from registry (admin operation).

        Args:
            agent_name: Name of agent to delete

        Returns:
            True if successful

        Raises:
            requests.HTTPError: If deletion fails
        """
        try:
            response = self._session.delete(
                f"{self.base_url}/registry/agents/{agent_name}",
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.info(f"Successfully deleted agent: {agent_name}")
            return True

        except requests.HTTPError as e:
            logger.error(f"Failed to delete agent: {e}")
            raise

    def close(self):
        """Close the HTTP session."""
        self._session.close()
