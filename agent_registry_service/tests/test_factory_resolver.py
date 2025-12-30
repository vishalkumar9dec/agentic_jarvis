"""
Comprehensive unit tests for AgentFactoryResolver.

Tests cover:
- Successful agent creation
- Invalid module handling
- Invalid function handling
- Factory with parameters
- Module caching
- Factory registration
- Configuration validation
- Error scenarios
"""

import os
import pytest
import sys
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent_registry_service.registry.agent_factory_resolver import (
    AgentFactoryResolver,
    AgentFactoryError
)


# =============================================================================
# Test Fixtures and Mock Factories
# =============================================================================

@pytest.fixture
def resolver():
    """Create a fresh AgentFactoryResolver instance."""
    return AgentFactoryResolver()


@pytest.fixture
def mock_agent():
    """Create a mock agent instance."""
    agent = Mock()
    agent.name = "MockAgent"
    agent.description = "Mock agent for testing"
    return agent


def create_mock_agent():
    """Mock factory function that returns a mock agent."""
    agent = Mock()
    agent.name = "MockAgent"
    return agent


def create_parameterized_agent(param1: str = "default", param2: int = 0):
    """Mock factory function that accepts parameters."""
    agent = Mock()
    agent.name = f"Agent_{param1}_{param2}"
    agent.param1 = param1
    agent.param2 = param2
    return agent


# =============================================================================
# Test Configuration Validation
# =============================================================================

class TestConfigurationValidation:
    """Test agent configuration validation."""

    def test_valid_config(self, resolver):
        """Test that valid configuration doesn't raise errors."""
        config = {
            "agent_type": "test",
            "factory_module": "os.path",
            "factory_function": "exists"
        }
        # Should not raise
        resolver._validate_config(config)

    def test_missing_agent_type(self, resolver):
        """Test that missing agent_type raises error."""
        config = {
            "factory_module": "some.module",
            "factory_function": "some_function"
        }
        with pytest.raises(AgentFactoryError, match="Missing required keys"):
            resolver._validate_config(config)

    def test_missing_factory_module(self, resolver):
        """Test that missing factory_module raises error."""
        config = {
            "agent_type": "test",
            "factory_function": "some_function"
        }
        with pytest.raises(AgentFactoryError, match="Missing required keys"):
            resolver._validate_config(config)

    def test_missing_factory_function(self, resolver):
        """Test that missing factory_function raises error."""
        config = {
            "agent_type": "test",
            "factory_module": "some.module"
        }
        with pytest.raises(AgentFactoryError, match="Missing required keys"):
            resolver._validate_config(config)

    def test_config_not_dict(self, resolver):
        """Test that non-dict config raises error."""
        with pytest.raises(AgentFactoryError, match="must be a dictionary"):
            resolver._validate_config("not a dict")

    def test_invalid_agent_type_type(self, resolver):
        """Test that non-string agent_type raises error."""
        config = {
            "agent_type": 123,
            "factory_module": "some.module",
            "factory_function": "some_function"
        }
        with pytest.raises(AgentFactoryError, match="agent_type must be a string"):
            resolver._validate_config(config)

    def test_invalid_factory_params_type(self, resolver):
        """Test that non-dict factory_params raises error."""
        config = {
            "agent_type": "test",
            "factory_module": "some.module",
            "factory_function": "some_function",
            "factory_params": "not a dict"
        }
        with pytest.raises(AgentFactoryError, match="factory_params must be a dictionary"):
            resolver._validate_config(config)


# =============================================================================
# Test Factory Registration
# =============================================================================

class TestFactoryRegistration:
    """Test factory registration functionality."""

    def test_register_factory(self, resolver):
        """Test registering a factory function."""
        resolver.register_factory("test_agent", create_mock_agent)

        assert "test_agent" in resolver._registered_factories
        assert resolver._registered_factories["test_agent"] == create_mock_agent

    def test_register_non_callable_raises_error(self, resolver):
        """Test that registering non-callable raises error."""
        with pytest.raises(AgentFactoryError, match="must be callable"):
            resolver.register_factory("test", "not_callable")

    def test_list_available_factories_empty(self, resolver):
        """Test listing factories when none are registered."""
        assert resolver.list_available_factories() == []

    def test_list_available_factories(self, resolver):
        """Test listing registered factories."""
        resolver.register_factory("factory1", create_mock_agent)
        resolver.register_factory("factory2", create_mock_agent)

        factories = resolver.list_available_factories()
        assert len(factories) == 2
        assert "factory1" in factories
        assert "factory2" in factories

    def test_create_agent_with_registered_factory(self, resolver):
        """Test creating agent using registered factory."""
        resolver.register_factory("test_agent", create_mock_agent)

        config = {
            "agent_type": "test_agent",
            "factory_module": "unused.module",
            "factory_function": "unused_function"
        }

        agent = resolver.create_agent(config)
        assert agent.name == "MockAgent"


# =============================================================================
# Test Module Import
# =============================================================================

class TestModuleImport:
    """Test dynamic module importing."""

    def test_import_valid_module(self, resolver):
        """Test importing a valid module."""
        module = resolver._import_module("os.path")
        assert module is not None
        assert hasattr(module, "exists")

    def test_import_nonexistent_module(self, resolver):
        """Test importing a module that doesn't exist."""
        with pytest.raises(AgentFactoryError, match="Module not found"):
            resolver._import_module("nonexistent.module.that.does.not.exist")

    def test_module_caching(self, resolver):
        """Test that modules are cached after first import."""
        # Import module first time
        module1 = resolver._import_module("os.path")

        # Import same module again
        module2 = resolver._import_module("os.path")

        # Should be the same object (cached)
        assert module1 is module2
        assert len(resolver._module_cache) == 1
        assert "os.path" in resolver._module_cache

    def test_clear_cache(self, resolver):
        """Test clearing the module cache."""
        # Import and cache a module
        resolver._import_module("os.path")
        assert len(resolver._module_cache) == 1

        # Clear cache
        resolver.clear_cache()
        assert len(resolver._module_cache) == 0

    def test_get_cache_stats(self, resolver):
        """Test getting cache statistics."""
        # Initially empty
        stats = resolver.get_cache_stats()
        assert stats["cached_modules"] == 0
        assert stats["registered_factories"] == 0

        # Add some items
        resolver._import_module("os.path")
        resolver.register_factory("test", create_mock_agent)

        stats = resolver.get_cache_stats()
        assert stats["cached_modules"] == 1
        assert stats["registered_factories"] == 1


# =============================================================================
# Test Function Resolution
# =============================================================================

class TestFunctionResolution:
    """Test function resolution from modules."""

    def test_resolve_valid_function(self, resolver):
        """Test resolving a valid function from module."""
        module = resolver._import_module("os.path")
        func = resolver._resolve_function(module, "exists")

        assert callable(func)
        assert func.__name__ == "exists"

    def test_resolve_nonexistent_function(self, resolver):
        """Test resolving a function that doesn't exist."""
        module = resolver._import_module("os.path")

        with pytest.raises(AgentFactoryError, match="Function.*not found"):
            resolver._resolve_function(module, "nonexistent_function")

    def test_resolve_non_callable_attribute(self, resolver):
        """Test resolving an attribute that isn't callable."""
        module = resolver._import_module("os")

        with pytest.raises(AgentFactoryError, match="not callable"):
            resolver._resolve_function(module, "name")


# =============================================================================
# Test Agent Creation
# =============================================================================

class TestAgentCreation:
    """Test end-to-end agent creation."""

    def test_create_agent_from_registered_factory(self, resolver):
        """Test creating agent from registered factory."""
        resolver.register_factory("mock", create_mock_agent)

        config = {
            "agent_type": "mock",
            "factory_module": "dummy",
            "factory_function": "dummy"
        }

        agent = resolver.create_agent(config)
        assert agent.name == "MockAgent"

    def test_create_agent_with_parameters(self, resolver):
        """Test creating agent with factory parameters."""
        resolver.register_factory("param_agent", create_parameterized_agent)

        config = {
            "agent_type": "param_agent",
            "factory_module": "dummy",
            "factory_function": "dummy",
            "factory_params": {
                "param1": "custom",
                "param2": 42
            }
        }

        agent = resolver.create_agent(config)
        assert agent.name == "Agent_custom_42"
        assert agent.param1 == "custom"
        assert agent.param2 == 42

    def test_create_agent_without_parameters(self, resolver):
        """Test creating agent without factory_params."""
        resolver.register_factory("mock", create_mock_agent)

        config = {
            "agent_type": "mock",
            "factory_module": "dummy",
            "factory_function": "dummy"
            # No factory_params
        }

        agent = resolver.create_agent(config)
        assert agent.name == "MockAgent"

    @patch('importlib.import_module')
    def test_create_agent_with_dynamic_import(self, mock_import, resolver):
        """Test creating agent with dynamic module import."""
        # Create a mock module with a factory function
        mock_module = MagicMock()
        mock_module.__name__ = "test.module"
        mock_module.create_test_agent = create_mock_agent
        mock_import.return_value = mock_module

        config = {
            "agent_type": "test",
            "factory_module": "test.module",
            "factory_function": "create_test_agent"
        }

        agent = resolver.create_agent(config)
        assert agent.name == "MockAgent"

        # Verify import was called
        mock_import.assert_called_once_with("test.module")

    def test_create_agent_invalid_config(self, resolver):
        """Test creating agent with invalid config."""
        config = {
            "agent_type": "test"
            # Missing required keys
        }

        with pytest.raises(AgentFactoryError, match="Missing required keys"):
            resolver.create_agent(config)

    @patch('importlib.import_module')
    def test_create_agent_module_not_found(self, mock_import, resolver):
        """Test creating agent when module doesn't exist."""
        mock_import.side_effect = ModuleNotFoundError("No module named 'fake'")

        config = {
            "agent_type": "test",
            "factory_module": "fake.module",
            "factory_function": "create_agent"
        }

        with pytest.raises(AgentFactoryError, match="Module not found"):
            resolver.create_agent(config)

    @patch('importlib.import_module')
    def test_create_agent_function_not_found(self, mock_import, resolver):
        """Test creating agent when function doesn't exist in module."""
        mock_module = Mock(spec=[])  # Empty spec means no attributes
        mock_module.__name__ = "test.module"
        mock_import.return_value = mock_module

        config = {
            "agent_type": "test",
            "factory_module": "test.module",
            "factory_function": "nonexistent_function"
        }

        with pytest.raises(AgentFactoryError, match="not found"):
            resolver.create_agent(config)


# =============================================================================
# Test Integration Scenarios
# =============================================================================

class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_multiple_agent_types(self, resolver):
        """Test creating multiple different agent types."""
        # Register multiple factories
        def create_agent_a():
            agent = Mock()
            agent.name = "AgentA"
            return agent

        def create_agent_b():
            agent = Mock()
            agent.name = "AgentB"
            return agent

        resolver.register_factory("type_a", create_agent_a)
        resolver.register_factory("type_b", create_agent_b)

        # Create agents of different types
        config_a = {
            "agent_type": "type_a",
            "factory_module": "dummy",
            "factory_function": "dummy"
        }
        config_b = {
            "agent_type": "type_b",
            "factory_module": "dummy",
            "factory_function": "dummy"
        }

        agent_a = resolver.create_agent(config_a)
        agent_b = resolver.create_agent(config_b)

        assert agent_a.name == "AgentA"
        assert agent_b.name == "AgentB"

    def test_repeated_agent_creation(self, resolver):
        """Test creating the same agent multiple times."""
        resolver.register_factory("mock", create_mock_agent)

        config = {
            "agent_type": "mock",
            "factory_module": "dummy",
            "factory_function": "dummy"
        }

        # Create same agent multiple times
        agent1 = resolver.create_agent(config)
        agent2 = resolver.create_agent(config)
        agent3 = resolver.create_agent(config)

        # Should all be valid agents
        assert agent1.name == "MockAgent"
        assert agent2.name == "MockAgent"
        assert agent3.name == "MockAgent"

    def test_cache_persists_across_creations(self, resolver):
        """Test that cache persists across multiple agent creations."""
        resolver.register_factory("mock", create_mock_agent)

        config = {
            "agent_type": "mock",
            "factory_module": "dummy",
            "factory_function": "dummy"
        }

        # Create agents multiple times
        for _ in range(5):
            resolver.create_agent(config)

        # Factory should still be cached
        assert "mock" in resolver._registered_factories


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
