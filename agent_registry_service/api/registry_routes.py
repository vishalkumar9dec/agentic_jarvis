"""
REST API endpoints for Agent Registry management.

This module provides FastAPI routes for:
- Listing and querying agents
- Registering new agents
- Updating agent capabilities
- Enabling/disabling agents
- Deleting agents
- Exporting registry data
"""

import logging
import httpx
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status

from agent_registry_service.registry.agent_registry import (
    AgentRegistry,
    AgentCapability,
    RegisteredAgent
)
from agent_registry_service.api.models import (
    RegisterAgentRequest,
    RemoteAgentRegistrationRequest,
    ProviderInfoModel,
    UpdateCapabilitiesRequest,
    UpdateAgentStatusRequest,
    AgentInfoResponse,
    AgentCapabilityModel,
    ListAgentsResponse,
    SuccessResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(prefix="/registry", tags=["Agent Registry"])

# Global registry instance (will be injected via dependency)
_registry_instance: Optional[AgentRegistry] = None


def set_registry(registry: AgentRegistry):
    """Set the global registry instance."""
    global _registry_instance
    _registry_instance = registry


def get_registry() -> AgentRegistry:
    """Dependency to get the agent registry."""
    if _registry_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent registry not initialized"
        )
    return _registry_instance


# =============================================================================
# Helper Functions
# =============================================================================

def _capability_to_model(capability: AgentCapability) -> AgentCapabilityModel:
    """Convert AgentCapability to Pydantic model."""
    return AgentCapabilityModel(
        domains=capability.domains,
        operations=capability.operations,
        entities=capability.entities,
        keywords=list(capability.keywords),
        examples=capability.examples,
        requires_auth=capability.requires_auth,
        priority=capability.priority
    )


def _model_to_capability(model: AgentCapabilityModel) -> AgentCapability:
    """Convert Pydantic model to AgentCapability."""
    return AgentCapability(
        domains=model.domains,
        operations=model.operations,
        entities=model.entities,
        keywords=set(model.keywords),
        examples=model.examples,
        requires_auth=model.requires_auth,
        priority=model.priority
    )


def _registered_agent_to_response(reg_agent: RegisteredAgent, agent_config: Optional[dict] = None) -> AgentInfoResponse:
    """Convert RegisteredAgent to API response."""
    # Default values
    factory_module = None
    factory_function = None
    agent_card_url = None
    provider = None
    status_value = None
    agent_type = "unknown"
    type_value = "local"

    if agent_config:
        # Get type field to differentiate local vs remote
        type_value = agent_config.get('type', 'local')
        agent_type = agent_config.get('agent_type', 'unknown')

        if type_value == "local":
            # Local agent fields
            factory_module = agent_config.get('factory_module')
            factory_function = agent_config.get('factory_function')
        elif type_value == "remote":
            # Remote agent fields
            agent_card_url = agent_config.get('agent_card_url')
            status_value = agent_config.get('status', 'pending')

            # Provider info
            provider_data = agent_config.get('provider')
            if provider_data:
                provider = ProviderInfoModel(**provider_data)

    return AgentInfoResponse(
        name=reg_agent.agent.name,
        description=reg_agent.agent.description,
        agent_type=agent_type,
        enabled=reg_agent.enabled,
        tags=list(reg_agent.tags),
        capabilities=_capability_to_model(reg_agent.capabilities),
        type=type_value,
        factory_module=factory_module,
        factory_function=factory_function,
        agent_card_url=agent_card_url,
        provider=provider,
        status=status_value
    )


# =============================================================================
# API Endpoints
# =============================================================================

@router.get(
    "/agents",
    response_model=ListAgentsResponse,
    summary="List all agents",
    description="Get a list of all registered agents with optional filtering"
)
async def list_agents(
    enabled_only: bool = Query(False, description="Only return enabled agents"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter by"),
    registry: AgentRegistry = Depends(get_registry)
) -> ListAgentsResponse:
    """
    List all registered agents.

    **Query Parameters:**
    - `enabled_only`: If true, only return enabled agents
    - `tags`: Comma-separated tags for filtering (e.g., "production,it-ops")

    **Returns:**
    - List of agents with their metadata and capabilities
    """
    try:
        # Parse tags
        tag_set = None
        if tags:
            tag_set = {tag.strip() for tag in tags.split(',') if tag.strip()}

        # Use registry's list_agents method with filters
        agent_names = registry.list_agents(enabled_only=enabled_only, tags=tag_set)

        # Convert to response format
        filtered_agents = []
        for agent_name in agent_names:
            reg_agent = registry.agents.get(agent_name)
            if reg_agent:
                agent_config = registry._agent_configs.get(agent_name)
                filtered_agents.append(_registered_agent_to_response(reg_agent, agent_config))

        return ListAgentsResponse(
            agents=filtered_agents,
            total=len(filtered_agents)
        )

    except Exception as e:
        logger.error(f"Error listing agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.get(
    "/agents/{agent_name}",
    response_model=AgentInfoResponse,
    summary="Get agent details",
    description="Get detailed information about a specific agent",
    responses={
        404: {"model": ErrorResponse, "description": "Agent not found"}
    }
)
async def get_agent(
    agent_name: str,
    registry: AgentRegistry = Depends(get_registry)
) -> AgentInfoResponse:
    """
    Get detailed information about a specific agent.

    **Path Parameters:**
    - `agent_name`: Name of the agent to retrieve

    **Returns:**
    - Complete agent information including capabilities

    **Raises:**
    - 404: Agent not found
    """
    try:
        reg_agent = registry.agents.get(agent_name)

        if not reg_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found"
            )

        agent_config = registry._agent_configs.get(agent_name)
        return _registered_agent_to_response(reg_agent, agent_config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve agent: {str(e)}"
        )


@router.post(
    "/agents",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new agent",
    description="Register a new agent with capabilities",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"}
    }
)
async def register_agent(
    request: RegisterAgentRequest,
    registry: AgentRegistry = Depends(get_registry)
) -> SuccessResponse:
    """
    Register a new agent.

    **Request Body:**
    - `agent_config`: Factory configuration for creating the agent
    - `capabilities`: Agent capabilities and matching criteria
    - `tags`: Optional tags for categorization

    **Returns:**
    - Success response with registered agent name

    **Raises:**
    - 400: Invalid configuration or agent already exists
    """
    try:
        # Convert config to dict
        agent_config = {
            "type": "local",  # Mark as local agent
            "agent_type": request.agent_config.agent_type,
            "factory_module": request.agent_config.factory_module,
            "factory_function": request.agent_config.factory_function,
            "factory_params": request.agent_config.factory_params
        }

        # Check if registry has factory resolver
        if not hasattr(registry, 'factory_resolver') or registry.factory_resolver is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent registration requires factory resolver. Registry not configured for dynamic agent creation."
            )

        # Create agent from factory
        agent = registry.factory_resolver.create_agent(agent_config)

        # Convert capabilities
        capabilities = _model_to_capability(request.capabilities)

        # Register agent
        registry.register(
            agent,
            capabilities,
            tags=set(request.tags),
            agent_config=agent_config
        )

        logger.info(f"Successfully registered agent: {agent.name}")

        return SuccessResponse(
            status="registered",
            message=f"Agent '{agent.name}' registered successfully",
            data={"agent_name": agent.name}
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register agent: {str(e)}"
        )


@router.post(
    "/agents/remote",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a remote agent (third-party)",
    description="Register a remote agent via agent card URL (A2A protocol)",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request or agent card"},
        503: {"model": ErrorResponse, "description": "Cannot reach agent card URL"}
    }
)
async def register_remote_agent(
    request: RemoteAgentRegistrationRequest,
    registry: AgentRegistry = Depends(get_registry)
) -> SuccessResponse:
    """
    Register a remote agent (third-party).

    Remote agents are hosted externally and communicate via A2A protocol.
    They are registered using their agent card URL, not factory functions.

    **Request Body:**
    - `agent_card_url`: URL to agent card (.well-known/agent-card.json)
    - `capabilities`: Agent capabilities and matching criteria
    - `tags`: Optional tags for categorization
    - `provider`: Provider/company information
    - `auth_config`: Optional authentication configuration

    **Returns:**
    - Success response with registration ID and pending approval status

    **Raises:**
    - 400: Invalid agent card or malformed request
    - 503: Cannot reach agent card URL
    """
    try:
        # Step 1: Validate and fetch agent card
        logger.info(f"Fetching agent card from: {request.agent_card_url}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(request.agent_card_url)
                response.raise_for_status()
                agent_card = response.json()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Cannot reach agent card URL: {str(e)}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid agent card format: {str(e)}"
                )

        # Step 2: Extract agent information from card
        try:
            card_data = agent_card.get("agentCard", {})
            agent_name = card_data.get("name")
            agent_description = card_data.get("description", "Remote agent")

            if not agent_name:
                raise ValueError("Agent card missing required field: 'name'")

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent card structure: {str(e)}"
            )

        # Step 3: Create RemoteA2aAgent instance
        try:
            from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

            remote_agent = RemoteA2aAgent(
                name=agent_name,
                description=agent_description,
                agent_card=request.agent_card_url
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create remote agent: {str(e)}"
            )

        # Step 4: Build remote agent configuration
        agent_config = {
            "type": "remote",
            "agent_type": agent_name,
            "agent_card_url": request.agent_card_url,
            "status": "pending",  # Default status
            "provider": {
                "name": request.provider.name,
                "website": request.provider.website,
                "support_email": request.provider.support_email,
                "documentation": request.provider.documentation
            }
        }

        # Add auth config if provided
        if request.auth_config:
            agent_config["auth_config"] = {
                "type": request.auth_config.type,
                "token_endpoint": request.auth_config.token_endpoint,
                "scopes": request.auth_config.scopes
            }

        # Step 5: Convert capabilities
        capabilities = _model_to_capability(request.capabilities)

        # Step 6: Register remote agent
        registry.register(
            remote_agent,
            capabilities,
            tags=set(request.tags),
            agent_config=agent_config
        )

        logger.info(f"Successfully registered remote agent: {agent_name} (status: pending)")

        return SuccessResponse(
            status="pending_approval",
            message=f"Remote agent '{agent_name}' registered successfully. Pending marketplace approval.",
            data={
                "agent_name": agent_name,
                "status": "pending",
                "provider": request.provider.name
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering remote agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register remote agent: {str(e)}"
        )


@router.put(
    "/agents/{agent_name}/capabilities",
    response_model=SuccessResponse,
    summary="Update agent capabilities",
    description="Update capabilities for an existing agent",
    responses={
        404: {"model": ErrorResponse, "description": "Agent not found"}
    }
)
async def update_capabilities(
    agent_name: str,
    request: UpdateCapabilitiesRequest,
    registry: AgentRegistry = Depends(get_registry)
) -> SuccessResponse:
    """
    Update agent capabilities.

    **Path Parameters:**
    - `agent_name`: Name of the agent to update

    **Request Body:**
    - `capabilities`: New capabilities configuration

    **Returns:**
    - Success response

    **Raises:**
    - 404: Agent not found
    """
    try:
        # Convert capabilities
        capabilities = _model_to_capability(request.capabilities)

        # Update capabilities
        success = registry.update_capabilities(agent_name, capabilities)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found"
            )

        logger.info(f"Updated capabilities for agent: {agent_name}")

        return SuccessResponse(
            status="updated",
            message=f"Capabilities updated for agent '{agent_name}'"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating capabilities for {agent_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update capabilities: {str(e)}"
        )


@router.patch(
    "/agents/{agent_name}/status",
    response_model=SuccessResponse,
    summary="Enable or disable an agent",
    description="Change the enabled status of an agent",
    responses={
        404: {"model": ErrorResponse, "description": "Agent not found"}
    }
)
async def update_agent_status(
    agent_name: str,
    request: UpdateAgentStatusRequest,
    registry: AgentRegistry = Depends(get_registry)
) -> SuccessResponse:
    """
    Enable or disable an agent.

    **Path Parameters:**
    - `agent_name`: Name of the agent to update

    **Request Body:**
    - `enabled`: True to enable, False to disable

    **Returns:**
    - Success response

    **Raises:**
    - 404: Agent not found
    """
    try:
        if request.enabled:
            success = registry.enable_agent(agent_name)
            action = "enabled"
        else:
            success = registry.disable_agent(agent_name)
            action = "disabled"

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found"
            )

        logger.info(f"Agent {agent_name} {action}")

        return SuccessResponse(
            status=action,
            message=f"Agent '{agent_name}' {action}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating status for {agent_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent status: {str(e)}"
        )


@router.delete(
    "/agents/{agent_name}",
    response_model=SuccessResponse,
    summary="Delete an agent",
    description="Remove an agent from the registry",
    responses={
        404: {"model": ErrorResponse, "description": "Agent not found"}
    }
)
async def delete_agent(
    agent_name: str,
    registry: AgentRegistry = Depends(get_registry)
) -> SuccessResponse:
    """
    Delete an agent from the registry.

    **Path Parameters:**
    - `agent_name`: Name of the agent to delete

    **Returns:**
    - Success response

    **Raises:**
    - 404: Agent not found
    """
    try:
        success = registry.unregister(agent_name)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found"
            )

        logger.info(f"Deleted agent: {agent_name}")

        return SuccessResponse(
            status="deleted",
            message=f"Agent '{agent_name}' deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent: {str(e)}"
        )


@router.get(
    "/export",
    response_model=dict,
    summary="Export full registry",
    description="Export the complete registry data as JSON"
)
async def export_registry(
    registry: AgentRegistry = Depends(get_registry)
) -> dict:
    """
    Export the complete registry data.

    **Returns:**
    - Complete registry data including all agents and their configurations

    This is useful for backup, migration, or inspection purposes.
    """
    try:
        # Get all agents (including disabled ones)
        all_agents = {}

        for agent_name, reg_agent in registry.agents.items():
            agent_config = registry._agent_configs.get(agent_name, {})

            # Convert to serializable format
            all_agents[agent_name] = {
                "name": reg_agent.agent.name,
                "description": reg_agent.agent.description,
                "agent_type": agent_config.get("agent_type", "unknown"),
                "enabled": reg_agent.enabled,
                "tags": list(reg_agent.tags),
                "capabilities": reg_agent.capabilities.to_dict(),
                "factory_module": agent_config.get("factory_module"),
                "factory_function": agent_config.get("factory_function")
            }

        export_data = {
            "version": "1.0",
            "total_agents": len(all_agents),
            "agents": all_agents
        }

        logger.info(f"Exported registry with {len(all_agents)} agents")

        return export_data

    except Exception as e:
        logger.error(f"Error exporting registry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export registry: {str(e)}"
        )
