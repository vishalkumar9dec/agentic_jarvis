"""
Comprehensive unit tests for AgentRegistry.

Tests cover:
- Persist and reload
- Agent recreation from factory
- Update capabilities and persist
- Rollback on error
- Enable/disable persistence
- All overridden methods
"""

import os
import pytest
import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent_registry_service.registry.agent_registry import (
    AgentCapability,
    RegisteredAgent,
    AgentRegistry
)
from agent_registry_service.registry.file_store import FileStore
from agent_registry_service.registry.agent_factory_resolver import AgentFactoryResolver


# =============================================================================
# Test Fixtures and Mock Factories
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def file_store(temp_dir):
    """Create FileStore instance."""
    file_path = os.path.join(temp_dir, "test_registry.json")
    return FileStore(file_path)


@pytest.fixture
def factory_resolver():
    """Create AgentFactoryResolver instance."""
    return AgentFactoryResolver()


@pytest.fixture
def persistent_registry(file_store, factory_resolver):
    """Create AgentRegistry instance."""
    return AgentRegistry(file_store, factory_resolver, auto_load=False)


@pytest.fixture
def mock_agent():
    """Create a mock LlmAgent."""
    agent = Mock()
    agent.name = "TestAgent"
    agent.description = "Test agent for testing"
    agent.instruction = "Test instruction"
    agent.tools = []
    return agent


@pytest.fixture
def mock_agent_config():
    """Create mock agent factory configuration."""
    return {
        "agent_type": "test",
        "factory_module": "test.module",
        "factory_function": "create_test_agent",
        "factory_params": {}
    }


@pytest.fixture
def mock_capabilities():
    """Create mock agent capabilities."""
    return AgentCapability(
        domains=["test"],
        operations=["create", "read"],
        entities=["entity1"],
        keywords={"test", "mock"},
        examples=["test query"],
        requires_auth=False,
        priority=0
    )


def create_test_agent():
    """Factory function for creating test agents."""
    agent = Mock()
    agent.name = "TestAgent"
    agent.description = "Test agent"
    agent.instruction = "Test instruction"
    agent.tools = []
    return agent


# =============================================================================
# Test AgentCapability
# =============================================================================

class TestAgentCapability:
    """Test AgentCapability data class."""

    def test_to_dict(self):
        """Test converting capabilities to dictionary."""
        cap = AgentCapability(
            domains=["test"],
            operations=["read"],
            entities=["entity"],
            keywords={"key1", "key2"},
            requires_auth=True,
            priority=5
        )

        result = cap.to_dict()

        assert result["domains"] == ["test"]
        assert result["operations"] == ["read"]
        assert result["entities"] == ["entity"]
        assert set(result["keywords"]) == {"key1", "key2"}
        assert result["requires_auth"] is True
        assert result["priority"] == 5

    def test_from_dict(self):
        """Test creating capabilities from dictionary."""
        data = {
            "domains": ["test"],
            "operations": ["read"],
            "entities": ["entity"],
            "keywords": ["key1", "key2"],
            "examples": ["example query"],
            "requires_auth": True,
            "priority": 5
        }

        cap = AgentCapability.from_dict(data)

        assert cap.domains == ["test"]
        assert cap.operations == ["read"]
        assert cap.entities == ["entity"]
        assert cap.keywords == {"key1", "key2"}
        assert cap.requires_auth is True
        assert cap.priority == 5

    def test_matches_query(self):
        """Test query matching."""
        cap = AgentCapability(
            domains=["tickets"],
            entities=["ticket", "user"],
            keywords={"create", "show"}
        )

        # Should match domain
        score = cap.matches_query("show my tickets")
        assert score > 0.0

        # Should not match unrelated query
        score = cap.matches_query("random unrelated query")
        assert score == 0.0


# =============================================================================
# Test Base AgentRegistry
# =============================================================================

class TestAgentRegistry:
    """Test base AgentRegistry functionality."""

    def test_register_agent(self, mock_agent, mock_capabilities):
        """Test registering an agent."""
        registry = AgentRegistry()

        registry.register(mock_agent, mock_capabilities)

        assert "TestAgent" in registry.agents
        assert registry.agents["TestAgent"].agent == mock_agent
        assert registry.agents["TestAgent"].capabilities == mock_capabilities

    def test_unregister_agent(self, mock_agent, mock_capabilities):
        """Test unregistering an agent."""
        registry = AgentRegistry()
        registry.register(mock_agent, mock_capabilities)

        result = registry.unregister("TestAgent")

        assert result is True
        assert "TestAgent" not in registry.agents

    def test_unregister_nonexistent(self):
        """Test unregistering non-existent agent."""
        registry = AgentRegistry()

        result = registry.unregister("NonExistent")

        assert result is False

    def test_enable_disable_agent(self, mock_agent, mock_capabilities):
        """Test enabling and disabling agents."""
        registry = AgentRegistry()
        registry.register(mock_agent, mock_capabilities)

        # Disable
        result = registry.disable_agent("TestAgent")
        assert result is True
        assert registry.agents["TestAgent"].enabled is False

        # Enable
        result = registry.enable_agent("TestAgent")
        assert result is True
        assert registry.agents["TestAgent"].enabled is True


# =============================================================================
# Test AgentRegistry - Basic Operations
# =============================================================================

class TestPersistentRegistryBasics:
    """Test basic AgentRegistry operations."""

    def test_initialization(self, file_store, factory_resolver):
        """Test registry initialization."""
        registry = AgentRegistry(file_store, factory_resolver, auto_load=False)

        assert registry.file_store == file_store
        assert registry.factory_resolver == factory_resolver
        assert len(registry.agents) == 0

    def test_register_with_persist(
        self,
        persistent_registry,
        mock_agent,
        mock_capabilities,
        mock_agent_config
    ):
        """Test registering agent triggers persistence."""
        persistent_registry.register(
            mock_agent,
            mock_capabilities,
            agent_config=mock_agent_config
        )

        # Verify agent is registered
        assert "TestAgent" in persistent_registry.agents

        # Verify config is stored
        assert "TestAgent" in persistent_registry._agent_configs

        # Verify file was created
        assert persistent_registry.file_store.file_path.exists()

    def test_unregister_with_persist(
        self,
        persistent_registry,
        mock_agent,
        mock_capabilities,
        mock_agent_config
    ):
        """Test unregistering agent triggers persistence."""
        persistent_registry.register(
            mock_agent,
            mock_capabilities,
            agent_config=mock_agent_config
        )

        result = persistent_registry.unregister("TestAgent")

        assert result is True
        assert "TestAgent" not in persistent_registry.agents
        assert "TestAgent" not in persistent_registry._agent_configs


# =============================================================================
# Test Persistence and Reload
# =============================================================================

class TestPersistenceAndReload:
    """Test persistence and reload functionality."""

    def test_persist_and_reload_single_agent(
        self,
        file_store,
        factory_resolver,
        mock_capabilities,
        mock_agent_config
    ):
        """Test persisting and reloading a single agent."""
        # Register factory
        factory_resolver.register_factory("test", create_test_agent)

        # Create registry and register agent
        registry1 = AgentRegistry(file_store, factory_resolver, auto_load=False)
        agent1 = create_test_agent()

        registry1.register(
            agent1,
            mock_capabilities,
            tags={"production"},
            agent_config=mock_agent_config
        )

        # Create new registry and auto-load
        registry2 = AgentRegistry(file_store, factory_resolver, auto_load=True)

        # Verify agent was loaded
        assert "TestAgent" in registry2.agents
        assert registry2.agents["TestAgent"].enabled is True
        assert "production" in registry2.agents["TestAgent"].tags

    def test_persist_multiple_agents(
        self,
        file_store,
        factory_resolver,
        mock_capabilities
    ):
        """Test persisting multiple agents."""
        def create_agent_1():
            agent = Mock()
            agent.name = "Agent1"
            agent.description = "First agent"
            agent.instruction = ""
            agent.tools = []
            return agent

        def create_agent_2():
            agent = Mock()
            agent.name = "Agent2"
            agent.description = "Second agent"
            agent.instruction = ""
            agent.tools = []
            return agent

        factory_resolver.register_factory("agent1", create_agent_1)
        factory_resolver.register_factory("agent2", create_agent_2)

        # Register multiple agents
        registry1 = AgentRegistry(file_store, factory_resolver, auto_load=False)

        agent1 = create_agent_1()
        agent2 = create_agent_2()

        registry1.register(
            agent1,
            mock_capabilities,
            agent_config={
                "agent_type": "agent1",
                "factory_module": "test",
                "factory_function": "create_agent_1"
            }
        )

        registry1.register(
            agent2,
            mock_capabilities,
            agent_config={
                "agent_type": "agent2",
                "factory_module": "test",
                "factory_function": "create_agent_2"
            }
        )

        # Reload in new registry
        registry2 = AgentRegistry(file_store, factory_resolver, auto_load=True)

        assert len(registry2.agents) == 2
        assert "Agent1" in registry2.agents
        assert "Agent2" in registry2.agents

    def test_enabled_status_persists(
        self,
        file_store,
        factory_resolver,
        mock_capabilities,
        mock_agent_config
    ):
        """Test that enabled/disabled status persists."""
        factory_resolver.register_factory("test", create_test_agent)

        # Create and disable agent
        registry1 = AgentRegistry(file_store, factory_resolver, auto_load=False)
        agent = create_test_agent()
        registry1.register(agent, mock_capabilities, agent_config=mock_agent_config)
        registry1.disable_agent("TestAgent")

        # Reload
        registry2 = AgentRegistry(file_store, factory_resolver, auto_load=True)

        assert "TestAgent" in registry2.agents
        assert registry2.agents["TestAgent"].enabled is False


# =============================================================================
# Test Update Capabilities
# =============================================================================

class TestUpdateCapabilities:
    """Test updating agent capabilities."""

    def test_update_capabilities(
        self,
        persistent_registry,
        mock_agent,
        mock_capabilities,
        mock_agent_config
    ):
        """Test updating capabilities."""
        persistent_registry.register(
            mock_agent,
            mock_capabilities,
            agent_config=mock_agent_config
        )

        # Update capabilities
        new_capabilities = AgentCapability(
            domains=["new_domain"],
            operations=["new_operation"]
        )

        result = persistent_registry.update_capabilities("TestAgent", new_capabilities)

        assert result is True
        assert persistent_registry.agents["TestAgent"].capabilities == new_capabilities

    def test_update_capabilities_nonexistent(self, persistent_registry):
        """Test updating capabilities of non-existent agent."""
        new_capabilities = AgentCapability(domains=["test"])

        result = persistent_registry.update_capabilities("NonExistent", new_capabilities)

        assert result is False

    def test_update_capabilities_persists(
        self,
        file_store,
        factory_resolver,
        mock_capabilities,
        mock_agent_config
    ):
        """Test that capability updates persist."""
        factory_resolver.register_factory("test", create_test_agent)

        registry1 = AgentRegistry(file_store, factory_resolver, auto_load=False)
        agent = create_test_agent()
        registry1.register(agent, mock_capabilities, agent_config=mock_agent_config)

        # Update capabilities
        new_capabilities = AgentCapability(domains=["updated"])
        registry1.update_capabilities("TestAgent", new_capabilities)

        # Reload and verify
        registry2 = AgentRegistry(file_store, factory_resolver, auto_load=True)

        assert registry2.agents["TestAgent"].capabilities.domains == ["updated"]


# =============================================================================
# Test Enable/Disable Persistence
# =============================================================================

class TestEnableDisablePersistence:
    """Test enable/disable operations trigger persistence."""

    def test_enable_persists(
        self,
        file_store,
        factory_resolver,
        mock_capabilities,
        mock_agent_config
    ):
        """Test that enabling agent persists."""
        factory_resolver.register_factory("test", create_test_agent)

        registry1 = AgentRegistry(file_store, factory_resolver, auto_load=False)
        agent = create_test_agent()
        registry1.register(agent, mock_capabilities, agent_config=mock_agent_config)
        registry1.disable_agent("TestAgent")
        registry1.enable_agent("TestAgent")

        # Reload and verify
        registry2 = AgentRegistry(file_store, factory_resolver, auto_load=True)

        assert registry2.agents["TestAgent"].enabled is True

    def test_disable_persists(
        self,
        file_store,
        factory_resolver,
        mock_capabilities,
        mock_agent_config
    ):
        """Test that disabling agent persists."""
        factory_resolver.register_factory("test", create_test_agent)

        registry1 = AgentRegistry(file_store, factory_resolver, auto_load=False)
        agent = create_test_agent()
        registry1.register(agent, mock_capabilities, agent_config=mock_agent_config)
        registry1.disable_agent("TestAgent")

        # Reload and verify
        registry2 = AgentRegistry(file_store, factory_resolver, auto_load=True)

        assert registry2.agents["TestAgent"].enabled is False


# =============================================================================
# Test Serialization
# =============================================================================

class TestSerialization:
    """Test serialization methods."""

    def test_serialize_registry(
        self,
        persistent_registry,
        mock_agent,
        mock_capabilities,
        mock_agent_config
    ):
        """Test serializing registry."""
        persistent_registry.register(
            mock_agent,
            mock_capabilities,
            tags={"production"},
            agent_config=mock_agent_config
        )

        serialized = persistent_registry._serialize_registry()

        assert "agents" in serialized
        assert "TestAgent" in serialized["agents"]

        agent_data = serialized["agents"]["TestAgent"]
        assert agent_data["name"] == "TestAgent"
        assert agent_data["description"] == "Test agent for testing"
        assert agent_data["agent_type"] == "test"
        assert agent_data["factory_module"] == "test.module"
        assert agent_data["factory_function"] == "create_test_agent"
        assert "production" in agent_data["tags"]
        assert agent_data["enabled"] is True


# =============================================================================
# Test Error Handling and Rollback
# =============================================================================

class TestErrorHandling:
    """Test error handling and rollback."""

    def test_load_with_no_file(self, file_store, factory_resolver):
        """Test loading when no file exists."""
        # Should not raise error
        registry = AgentRegistry(file_store, factory_resolver, auto_load=True)

        assert len(registry.agents) == 0

    def test_load_with_invalid_agent_config(
        self,
        file_store,
        mock_capabilities
    ):
        """Test loading with invalid agent configuration."""
        # Create a fresh factory resolver for this test
        factory_resolver1 = AgentFactoryResolver()
        factory_resolver1.register_factory("test", create_test_agent)

        # Create registry with valid agent
        registry1 = AgentRegistry(file_store, factory_resolver1, auto_load=False)
        agent = create_test_agent()

        registry1.register(
            agent,
            mock_capabilities,
            agent_config={
                "agent_type": "test",
                "factory_module": "nonexistent.module",
                "factory_function": "nonexistent_function"
            }
        )

        # Create NEW factory resolver without the registered factory
        # This simulates trying to load with an invalid config
        factory_resolver2 = AgentFactoryResolver()

        # Try to load - should skip corrupted agent but not crash
        registry2 = AgentRegistry(file_store, factory_resolver2, auto_load=True)

        # Agent should not be loaded due to invalid config
        assert len(registry2.agents) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
