"""
Agent Factory Resolver for dynamic agent creation.

This module provides functionality to dynamically import and execute factory
functions to create LlmAgent instances from configuration dictionaries.

Problem Solved:
- LlmAgent instances cannot be serialized to JSON
- We store factory function references instead
- This resolver recreates agents on demand from config

Features:
- Dynamic module import using importlib
- Factory function resolution
- Module caching for performance
- Comprehensive error handling
- Factory registration for custom factories
"""

import importlib
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentFactoryError(Exception):
    """Base exception for agent factory operations."""
    pass


class AgentFactoryResolver:
    """
    Resolves and executes factory functions to create LlmAgent instances.

    The resolver can:
    1. Import modules dynamically
    2. Resolve factory functions from those modules
    3. Execute factories with optional parameters
    4. Cache modules for performance
    5. Register custom factory functions

    Example Configuration:
        {
            "agent_type": "tickets",
            "factory_module": "jarvis_agent.mcp_agents.agent_factory",
            "factory_function": "create_tickets_agent",
            "factory_params": {}  # Optional
        }

    Example Usage:
        resolver = AgentFactoryResolver()

        config = {
            "agent_type": "tickets",
            "factory_module": "jarvis_agent.mcp_agents.agent_factory",
            "factory_function": "create_tickets_agent",
            "factory_params": {}
        }

        agent = resolver.create_agent(config)
    """

    def __init__(self):
        """Initialize the resolver with empty caches."""
        self._module_cache: Dict[str, Any] = {}
        self._registered_factories: Dict[str, Callable] = {}
        logger.info("AgentFactoryResolver initialized")

    def create_agent(self, agent_config: Dict) -> Any:
        """
        Create an agent instance from configuration.

        Process:
        1. Validate agent configuration
        2. Check for registered factory first
        3. Dynamically import module if needed
        4. Resolve factory function
        5. Execute factory with parameters
        6. Return created agent

        Args:
            agent_config: Dictionary with factory configuration
                Required keys:
                    - agent_type: Type identifier (e.g., "tickets")
                    - factory_module: Module path (e.g., "jarvis_agent.mcp_agents.agent_factory")
                    - factory_function: Function name (e.g., "create_tickets_agent")
                Optional keys:
                    - factory_params: Dict of parameters to pass to factory

        Returns:
            LlmAgent: Created agent instance

        Raises:
            AgentFactoryError: If agent creation fails

        Example:
            >>> config = {
            ...     "agent_type": "tickets",
            ...     "factory_module": "jarvis_agent.mcp_agents.agent_factory",
            ...     "factory_function": "create_tickets_agent",
            ...     "factory_params": {}
            ... }
            >>> agent = resolver.create_agent(config)
        """
        try:
            # Validate configuration
            self._validate_config(agent_config)

            agent_type = agent_config["agent_type"]
            factory_module = agent_config["factory_module"]
            factory_function = agent_config["factory_function"]
            factory_params = agent_config.get("factory_params", {})

            logger.info(f"Creating agent of type '{agent_type}' using {factory_module}.{factory_function}")

            # Check if factory is registered
            if agent_type in self._registered_factories:
                logger.debug(f"Using registered factory for '{agent_type}'")
                factory_func = self._registered_factories[agent_type]
            else:
                # Import module and get factory function
                module = self._import_module(factory_module)
                factory_func = self._resolve_function(module, factory_function)

            # Execute factory function with parameters
            if factory_params:
                logger.debug(f"Calling factory with params: {factory_params}")
                agent = factory_func(**factory_params)
            else:
                agent = factory_func()

            logger.info(f"Successfully created agent of type '{agent_type}'")
            return agent

        except KeyError as e:
            error_msg = f"Missing required configuration key: {e}"
            logger.error(error_msg)
            raise AgentFactoryError(error_msg)
        except Exception as e:
            error_msg = f"Failed to create agent from config: {e}"
            logger.error(error_msg, exc_info=True)
            raise AgentFactoryError(error_msg)

    def register_factory(self, agent_type: str, factory_func: Callable) -> None:
        """
        Register a custom factory function for an agent type.

        Registered factories bypass dynamic import and are called directly.
        Useful for:
        - Testing with mock factories
        - Custom agent types
        - Performance optimization

        Args:
            agent_type: Unique identifier for the agent type
            factory_func: Callable that returns an agent instance

        Example:
            >>> def my_custom_factory():
            ...     return MyCustomAgent()
            >>> resolver.register_factory("custom", my_custom_factory)
        """
        if not callable(factory_func):
            raise AgentFactoryError(f"factory_func must be callable, got {type(factory_func)}")

        self._registered_factories[agent_type] = factory_func
        logger.info(f"Registered factory for agent type '{agent_type}'")

    def list_available_factories(self) -> List[str]:
        """
        List all registered factory types.

        Returns:
            List of agent type identifiers that have registered factories

        Example:
            >>> resolver.list_available_factories()
            ['tickets', 'finops', 'oxygen']
        """
        return list(self._registered_factories.keys())

    def _import_module(self, module_path: str) -> Any:
        """
        Import a module dynamically with caching.

        Modules are cached to avoid repeated imports, improving performance
        for agents that are created multiple times.

        Args:
            module_path: Full module path (e.g., "jarvis_agent.mcp_agents.agent_factory")

        Returns:
            Imported module object

        Raises:
            AgentFactoryError: If module cannot be imported
        """
        # Check cache first
        if module_path in self._module_cache:
            logger.debug(f"Using cached module '{module_path}'")
            return self._module_cache[module_path]

        # Import module
        try:
            logger.debug(f"Importing module '{module_path}'")
            module = importlib.import_module(module_path)

            # Cache the module
            self._module_cache[module_path] = module
            logger.debug(f"Cached module '{module_path}'")

            return module

        except ModuleNotFoundError as e:
            error_msg = f"Module not found: '{module_path}'. Error: {e}"
            logger.error(error_msg)
            raise AgentFactoryError(error_msg)
        except Exception as e:
            error_msg = f"Failed to import module '{module_path}': {e}"
            logger.error(error_msg, exc_info=True)
            raise AgentFactoryError(error_msg)

    def _resolve_function(self, module: Any, function_name: str) -> Callable:
        """
        Resolve a function from a module.

        Args:
            module: Module object containing the function
            function_name: Name of the function to resolve

        Returns:
            Function object

        Raises:
            AgentFactoryError: If function doesn't exist or isn't callable
        """
        try:
            if not hasattr(module, function_name):
                available_funcs = [name for name in dir(module) if not name.startswith('_')]
                error_msg = (
                    f"Function '{function_name}' not found in module '{module.__name__}'. "
                    f"Available functions: {available_funcs}"
                )
                logger.error(error_msg)
                raise AgentFactoryError(error_msg)

            func = getattr(module, function_name)

            if not callable(func):
                error_msg = f"'{function_name}' in module '{module.__name__}' is not callable"
                logger.error(error_msg)
                raise AgentFactoryError(error_msg)

            logger.debug(f"Resolved function '{function_name}' from module '{module.__name__}'")
            return func

        except AgentFactoryError:
            raise
        except Exception as e:
            error_msg = f"Failed to resolve function '{function_name}': {e}"
            logger.error(error_msg, exc_info=True)
            raise AgentFactoryError(error_msg)

    def _validate_config(self, agent_config: Dict) -> None:
        """
        Validate agent configuration.

        Args:
            agent_config: Configuration dictionary to validate

        Raises:
            AgentFactoryError: If configuration is invalid
        """
        required_keys = ["agent_type", "factory_module", "factory_function"]

        if not isinstance(agent_config, dict):
            raise AgentFactoryError(f"agent_config must be a dictionary, got {type(agent_config)}")

        missing_keys = [key for key in required_keys if key not in agent_config]
        if missing_keys:
            raise AgentFactoryError(f"Missing required keys in agent_config: {missing_keys}")

        # Validate types
        if not isinstance(agent_config["agent_type"], str):
            raise AgentFactoryError("agent_type must be a string")
        if not isinstance(agent_config["factory_module"], str):
            raise AgentFactoryError("factory_module must be a string")
        if not isinstance(agent_config["factory_function"], str):
            raise AgentFactoryError("factory_function must be a string")

        if "factory_params" in agent_config and not isinstance(agent_config["factory_params"], dict):
            raise AgentFactoryError("factory_params must be a dictionary")

    def clear_cache(self) -> None:
        """
        Clear the module cache.

        Useful for:
        - Testing scenarios
        - Forcing module reload
        - Memory management in long-running processes
        """
        self._module_cache.clear()
        logger.info("Module cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about the resolver's cache.

        Returns:
            Dictionary with cache statistics

        Example:
            >>> stats = resolver.get_cache_stats()
            >>> print(stats)
            {'cached_modules': 3, 'registered_factories': 2}
        """
        return {
            "cached_modules": len(self._module_cache),
            "registered_factories": len(self._registered_factories)
        }
