"""
Integration tests for Registry REST API.

Tests all endpoints using FastAPI TestClient:
- List agents
- Get agent details
- Register agents
- Update capabilities
- Enable/disable agents
- Delete agents
- Export registry
"""

import os
import pytest
import tempfile
import shutil
from unittest.mock import Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent_registry_service.registry.agent_registry import (
    AgentRegistry,
    AgentCapability
)
from agent_registry_service.registry.file_store import FileStore
from agent_registry_service.registry.agent_factory_resolver import AgentFactoryResolver
from agent_registry_service.api.registry_routes import router, set_registry


# =============================================================================
# Test Fixtures
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
    resolver = AgentFactoryResolver()

    # Register test factory
    def create_test_agent():
        agent = Mock()
        agent.name = "test_agent"
        agent.description = "Test agent for API testing"
        agent.instruction = ""
        agent.tools = []
        return agent

    resolver.register_factory("test", create_test_agent)

    return resolver


@pytest.fixture
def registry(file_store, factory_resolver):
    """Create AgentRegistry instance."""
    return AgentRegistry(file_store, factory_resolver, auto_load=False)


@pytest.fixture
def app(registry):
    """Create FastAPI test application."""
    app = FastAPI()
    app.include_router(router)
    set_registry(registry)
    return app


@pytest.fixture
def client(app):
    """Create TestClient."""
    return TestClient(app)


@pytest.fixture
def sample_agent(registry, factory_resolver):
    """Create and register a sample agent."""
    agent = factory_resolver._registered_factories["test"]()

    capabilities = AgentCapability(
        domains=["test"],
        operations=["create", "read"],
        entities=["test_entity"],
        keywords={"test", "sample"},
        examples=["test query"],
        requires_auth=False,
        priority=0
    )

    agent_config = {
        "agent_type": "test",
        "factory_module": "test.module",
        "factory_function": "create_test_agent"
    }

    registry.register(agent, capabilities, tags={"testing"}, agent_config=agent_config)

    return agent.name


# =============================================================================
# Test List Agents Endpoint
# =============================================================================

class TestListAgents:
    """Test GET /registry/agents endpoint."""

    def test_list_agents_empty_registry(self, client):
        """Test listing agents when registry is empty."""
        response = client.get("/registry/agents")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert data["agents"] == []

    def test_list_agents_with_agents(self, client, sample_agent):
        """Test listing agents when agents are registered."""
        response = client.get("/registry/agents")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["agents"]) == 1
        assert data["agents"][0]["name"] == "test_agent"
        assert data["agents"][0]["enabled"] is True

    def test_list_agents_enabled_only_filter(self, client, registry, factory_resolver):
        """Test filtering by enabled status."""
        # Register two agents
        agent1 = factory_resolver._registered_factories["test"]()
        agent1.name = "enabled_agent"

        agent2 = factory_resolver._registered_factories["test"]()
        agent2.name = "disabled_agent"

        capabilities = AgentCapability(domains=["test"])
        config = {"agent_type": "test", "factory_module": "test", "factory_function": "create"}

        registry.register(agent1, capabilities, agent_config=config)
        registry.register(agent2, capabilities, agent_config=config)

        # Disable one agent
        registry.disable_agent("disabled_agent")

        # Test enabled_only filter
        response = client.get("/registry/agents?enabled_only=true")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert data["agents"][0]["name"] == "enabled_agent"

    def test_list_agents_tags_filter(self, client, registry, factory_resolver):
        """Test filtering by tags."""
        # Register agents with different tags
        agent1 = factory_resolver._registered_factories["test"]()
        agent1.name = "prod_agent"

        agent2 = factory_resolver._registered_factories["test"]()
        agent2.name = "dev_agent"

        capabilities = AgentCapability(domains=["test"])
        config = {"agent_type": "test", "factory_module": "test", "factory_function": "create"}

        registry.register(agent1, capabilities, tags={"production"}, agent_config=config)
        registry.register(agent2, capabilities, tags={"development"}, agent_config=config)

        # Filter by production tag
        response = client.get("/registry/agents?tags=production")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert data["agents"][0]["name"] == "prod_agent"

    def test_list_agents_multiple_tags_filter(self, client, registry, factory_resolver):
        """Test filtering by multiple tags."""
        agent = factory_resolver._registered_factories["test"]()
        capabilities = AgentCapability(domains=["test"])
        config = {"agent_type": "test", "factory_module": "test", "factory_function": "create"}

        registry.register(agent, capabilities, tags={"production", "critical"}, agent_config=config)

        # Filter by multiple tags
        response = client.get("/registry/agents?tags=production,critical")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1


# =============================================================================
# Test Get Agent Endpoint
# =============================================================================

class TestGetAgent:
    """Test GET /registry/agents/{agent_name} endpoint."""

    def test_get_existing_agent(self, client, sample_agent):
        """Test getting an existing agent."""
        response = client.get(f"/registry/agents/{sample_agent}")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "test_agent"
        assert data["description"] == "Test agent for API testing"
        assert data["enabled"] is True
        assert "capabilities" in data
        assert data["capabilities"]["domains"] == ["test"]

    def test_get_nonexistent_agent(self, client):
        """Test getting a non-existent agent returns 404."""
        response = client.get("/registry/agents/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


# =============================================================================
# Test Register Agent Endpoint
# =============================================================================

class TestRegisterAgent:
    """Test POST /registry/agents endpoint."""

    def test_register_agent_success(self, client, factory_resolver):
        """Test successfully registering a new agent."""
        request_data = {
            "agent_config": {
                "agent_type": "test",
                "factory_module": "test.module",
                "factory_function": "create_test_agent",
                "factory_params": {}
            },
            "capabilities": {
                "domains": ["tickets"],
                "operations": ["create", "read"],
                "entities": ["ticket"],
                "keywords": ["ticket", "create"],
                "examples": ["Create a ticket"],
                "requires_auth": False,
                "priority": 0
            },
            "tags": ["production"]
        }

        response = client.post("/registry/agents", json=request_data)

        assert response.status_code == 201
        data = response.json()

        assert data["status"] == "registered"
        assert "agent_name" in data["data"]

    def test_register_agent_invalid_config(self, client):
        """Test registering with invalid configuration."""
        request_data = {
            "agent_config": {
                "agent_type": "invalid",
                "factory_module": "nonexistent.module",
                "factory_function": "nonexistent_function"
            },
            "capabilities": {
                "domains": ["test"]
            },
            "tags": []
        }

        response = client.post("/registry/agents", json=request_data)

        assert response.status_code in [400, 500]  # Either bad request or server error


# =============================================================================
# Test Update Capabilities Endpoint
# =============================================================================

class TestUpdateCapabilities:
    """Test PUT /registry/agents/{agent_name}/capabilities endpoint."""

    def test_update_capabilities_success(self, client, sample_agent):
        """Test successfully updating agent capabilities."""
        request_data = {
            "capabilities": {
                "domains": ["updated_domain"],
                "operations": ["update"],
                "entities": ["updated_entity"],
                "keywords": ["updated"],
                "examples": [],
                "requires_auth": True,
                "priority": 5
            }
        }

        response = client.put(
            f"/registry/agents/{sample_agent}/capabilities",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "updated"

        # Verify the update
        get_response = client.get(f"/registry/agents/{sample_agent}")
        agent_data = get_response.json()

        assert agent_data["capabilities"]["domains"] == ["updated_domain"]
        assert agent_data["capabilities"]["priority"] == 5

    def test_update_capabilities_nonexistent_agent(self, client):
        """Test updating capabilities for non-existent agent."""
        request_data = {
            "capabilities": {
                "domains": ["test"]
            }
        }

        response = client.put(
            "/registry/agents/nonexistent/capabilities",
            json=request_data
        )

        assert response.status_code == 404


# =============================================================================
# Test Update Agent Status Endpoint
# =============================================================================

class TestUpdateAgentStatus:
    """Test PATCH /registry/agents/{agent_name}/status endpoint."""

    def test_disable_agent(self, client, sample_agent):
        """Test disabling an agent."""
        request_data = {"enabled": False}

        response = client.patch(
            f"/registry/agents/{sample_agent}/status",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "disabled"

        # Verify the agent is disabled
        get_response = client.get(f"/registry/agents/{sample_agent}")
        agent_data = get_response.json()

        assert agent_data["enabled"] is False

    def test_enable_agent(self, client, sample_agent, registry):
        """Test enabling a disabled agent."""
        # First disable the agent
        registry.disable_agent(sample_agent)

        # Now enable it via API
        request_data = {"enabled": True}

        response = client.patch(
            f"/registry/agents/{sample_agent}/status",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "enabled"

        # Verify the agent is enabled
        get_response = client.get(f"/registry/agents/{sample_agent}")
        agent_data = get_response.json()

        assert agent_data["enabled"] is True

    def test_update_status_nonexistent_agent(self, client):
        """Test updating status for non-existent agent."""
        request_data = {"enabled": True}

        response = client.patch(
            "/registry/agents/nonexistent/status",
            json=request_data
        )

        assert response.status_code == 404


# =============================================================================
# Test Delete Agent Endpoint
# =============================================================================

class TestDeleteAgent:
    """Test DELETE /registry/agents/{agent_name} endpoint."""

    def test_delete_agent_success(self, client, sample_agent):
        """Test successfully deleting an agent."""
        response = client.delete(f"/registry/agents/{sample_agent}")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "deleted"

        # Verify the agent is gone
        get_response = client.get(f"/registry/agents/{sample_agent}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_agent(self, client):
        """Test deleting a non-existent agent."""
        response = client.delete("/registry/agents/nonexistent")

        assert response.status_code == 404


# =============================================================================
# Test Export Registry Endpoint
# =============================================================================

class TestExportRegistry:
    """Test GET /registry/export endpoint."""

    def test_export_empty_registry(self, client):
        """Test exporting an empty registry."""
        response = client.get("/registry/export")

        assert response.status_code == 200
        data = response.json()

        assert "version" in data
        assert data["total_agents"] == 0
        assert data["agents"] == {}

    def test_export_with_agents(self, client, sample_agent):
        """Test exporting registry with agents."""
        response = client.get("/registry/export")

        assert response.status_code == 200
        data = response.json()

        assert data["total_agents"] == 1
        assert "test_agent" in data["agents"]
        assert data["agents"]["test_agent"]["name"] == "test_agent"
        assert "capabilities" in data["agents"]["test_agent"]


# =============================================================================
# Test Error Handling
# =============================================================================

class TestErrorHandling:
    """Test error handling across endpoints."""

    def test_invalid_json_payload(self, client):
        """Test sending invalid JSON."""
        response = client.post(
            "/registry/agents",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Unprocessable Entity

    def test_missing_required_fields(self, client):
        """Test request with missing required fields."""
        request_data = {
            "capabilities": {
                "domains": ["test"]
            }
            # Missing agent_config
        }

        response = client.post("/registry/agents", json=request_data)

        assert response.status_code == 422  # Validation error


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
