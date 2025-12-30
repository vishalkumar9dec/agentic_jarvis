"""
Pydantic models for API request/response validation.

This module defines all data models used in the REST API endpoints
for agent registry and session management.
"""

from typing import Dict, List, Optional, Set, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# =============================================================================
# Agent Registry Models
# =============================================================================

class AgentCapabilityModel(BaseModel):
    """Agent capability definition for API."""

    domains: List[str] = Field(default_factory=list, description="Domain areas (e.g., 'tickets', 'finops')")
    operations: List[str] = Field(default_factory=list, description="Operations (e.g., 'create', 'read', 'update')")
    entities: List[str] = Field(default_factory=list, description="Entity types (e.g., 'ticket', 'user')")
    keywords: List[str] = Field(default_factory=list, description="Keywords for matching")
    examples: List[str] = Field(default_factory=list, description="Example queries")
    requires_auth: bool = Field(default=False, description="Whether authentication is required")
    priority: int = Field(default=0, ge=-100, le=100, description="Priority (-100 to 100)")

    class Config:
        json_schema_extra = {
            "example": {
                "domains": ["tickets"],
                "operations": ["create", "read"],
                "entities": ["ticket"],
                "keywords": ["show", "create", "ticket"],
                "examples": ["Show my tickets", "Create a new ticket"],
                "requires_auth": False,
                "priority": 0
            }
        }


class AgentConfigModel(BaseModel):
    """Agent factory configuration."""

    agent_type: str = Field(..., description="Type of agent (e.g., 'tickets', 'finops')")
    factory_module: str = Field(..., description="Module path for factory function")
    factory_function: str = Field(..., description="Factory function name")
    factory_params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for factory function")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_type": "tickets",
                "factory_module": "jarvis_agent.mcp_agents.agent_factory",
                "factory_function": "create_tickets_agent",
                "factory_params": {}
            }
        }


class RegisterAgentRequest(BaseModel):
    """Request to register a new local agent (first-party)."""

    agent_config: AgentConfigModel
    capabilities: AgentCapabilityModel
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_config": {
                    "agent_type": "tickets",
                    "factory_module": "jarvis_agent.mcp_agents.agent_factory",
                    "factory_function": "create_tickets_agent"
                },
                "capabilities": {
                    "domains": ["tickets"],
                    "operations": ["create", "read"],
                    "entities": ["ticket"]
                },
                "tags": ["production", "it-ops", "first-party"]
            }
        }


class ProviderInfoModel(BaseModel):
    """Third-party provider information."""

    name: str = Field(..., min_length=1, description="Provider/company name")
    website: Optional[str] = Field(default=None, description="Provider website URL")
    support_email: Optional[str] = Field(default=None, description="Support email address")
    documentation: Optional[str] = Field(default=None, description="Documentation URL")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Acme Corp",
                "website": "https://acme.com",
                "support_email": "support@acme.com",
                "documentation": "https://acme.com/docs/agent"
            }
        }


class AuthConfigModel(BaseModel):
    """Authentication configuration for remote agents."""

    type: str = Field(..., description="Auth type: bearer, api_key, oauth2, or none")
    token_endpoint: Optional[str] = Field(default=None, description="Token endpoint URL")
    scopes: List[str] = Field(default_factory=list, description="Required scopes")

    @field_validator('type')
    @classmethod
    def validate_auth_type(cls, v: str) -> str:
        if v not in ['bearer', 'api_key', 'oauth2', 'none']:
            raise ValueError("Auth type must be 'bearer', 'api_key', 'oauth2', or 'none'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": "bearer",
                "token_endpoint": "https://your-agent.com/auth/token",
                "scopes": ["read:customers", "read:deals"]
            }
        }


class RemoteAgentRegistrationRequest(BaseModel):
    """Request to register a new remote agent (third-party)."""

    agent_card_url: str = Field(..., min_length=1, description="URL to agent card (A2A protocol)")
    capabilities: AgentCapabilityModel
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    provider: ProviderInfoModel
    auth_config: Optional[AuthConfigModel] = Field(default=None, description="Authentication configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_card_url": "https://acme-agent.example.com:8080/.well-known/agent-card.json",
                "capabilities": {
                    "domains": ["crm", "sales", "customers"],
                    "operations": ["read", "search", "analyze"],
                    "entities": ["customer", "deal", "pipeline", "contact"],
                    "keywords": ["crm", "sales", "customer", "deal"],
                    "priority": 5
                },
                "tags": ["third-party", "crm", "sales"],
                "provider": {
                    "name": "Acme Corp",
                    "website": "https://acme.com",
                    "support_email": "support@acme.com",
                    "documentation": "https://acme.com/docs/agent"
                },
                "auth_config": {
                    "type": "bearer",
                    "token_endpoint": "https://acme-agent.example.com/auth/token",
                    "scopes": ["read:customers", "read:deals"]
                }
            }
        }


class UpdateCapabilitiesRequest(BaseModel):
    """Request to update agent capabilities."""

    capabilities: AgentCapabilityModel

    class Config:
        json_schema_extra = {
            "example": {
                "capabilities": {
                    "domains": ["tickets", "incidents"],
                    "operations": ["create", "read", "update"],
                    "entities": ["ticket", "incident"]
                }
            }
        }


class UpdateAgentStatusRequest(BaseModel):
    """Request to enable/disable an agent."""

    enabled: bool = Field(..., description="Whether agent should be enabled")

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True
            }
        }


class AgentInfoResponse(BaseModel):
    """Agent information response."""

    name: str
    description: str
    agent_type: str
    enabled: bool
    tags: List[str]
    capabilities: AgentCapabilityModel

    # Type field to differentiate local vs remote
    type: str = Field(default="local", description="Agent type: 'local' or 'remote'")

    # Local agent fields (factory-based)
    factory_module: Optional[str] = None
    factory_function: Optional[str] = None

    # Remote agent fields (A2A-based)
    agent_card_url: Optional[str] = None
    provider: Optional[ProviderInfoModel] = None
    status: Optional[str] = Field(default=None, description="Approval status: pending, approved, suspended")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "tickets_agent",
                "description": "Manages IT support tickets",
                "agent_type": "tickets",
                "enabled": True,
                "tags": ["production", "first-party"],
                "capabilities": {
                    "domains": ["tickets"],
                    "operations": ["create", "read"],
                    "entities": ["ticket"]
                },
                "type": "local",
                "factory_module": "jarvis_agent.mcp_agents.agent_factory",
                "factory_function": "create_tickets_agent"
            }
        }


class ListAgentsResponse(BaseModel):
    """Response for listing agents."""

    agents: List[AgentInfoResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "agents": [
                    {
                        "name": "tickets_agent",
                        "description": "Manages IT support tickets",
                        "agent_type": "tickets",
                        "enabled": True,
                        "tags": ["production"],
                        "capabilities": {
                            "domains": ["tickets"],
                            "operations": ["create", "read"]
                        }
                    }
                ],
                "total": 1
            }
        }


class SuccessResponse(BaseModel):
    """Generic success response."""

    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Operation completed successfully"
            }
        }


class ErrorResponse(BaseModel):
    """Generic error response."""

    status: str = "error"
    error: str
    detail: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error": "Agent not found",
                "detail": "Agent 'unknown_agent' does not exist in registry"
            }
        }


# =============================================================================
# Session Management Models
# =============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    user_id: str = Field(..., min_length=1, description="User identifier")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional session metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "alice",
                "metadata": {
                    "client": "web",
                    "version": "1.0"
                }
            }
        }


class CreateSessionResponse(BaseModel):
    """Response for session creation."""

    session_id: str
    user_id: str
    created_at: str
    status: str

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "alice",
                "created_at": "2025-12-30T10:00:00Z",
                "status": "active"
            }
        }


class AddMessageRequest(BaseModel):
    """Request to add message to conversation history."""

    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., min_length=1, description="Message content")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ['user', 'assistant', 'system']:
            raise ValueError("Role must be 'user', 'assistant', or 'system'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Show my tickets"
            }
        }


class TrackInvocationRequest(BaseModel):
    """Request to track agent invocation."""

    agent_name: str = Field(..., min_length=1, description="Name of agent invoked")
    query: str = Field(..., description="User query sent to agent")
    response: Optional[str] = Field(default=None, description="Agent response")
    success: bool = Field(default=True, description="Whether invocation was successful")
    duration_ms: Optional[int] = Field(default=None, ge=0, description="Execution duration in milliseconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "tickets_agent",
                "query": "Show my tickets",
                "response": "You have 3 open tickets",
                "success": True,
                "duration_ms": 150
            }
        }


class UpdateSessionStatusRequest(BaseModel):
    """Request to update session status."""

    status: str = Field(..., description="New status: active, completed, or expired")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ['active', 'completed', 'expired']:
            raise ValueError("Status must be 'active', 'completed', or 'expired'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed"
            }
        }


class ConversationMessage(BaseModel):
    """Conversation history message."""

    role: str
    content: str
    timestamp: str


class AgentInvocation(BaseModel):
    """Agent invocation record."""

    agent_name: str
    query: str
    response: Optional[str]
    success: bool
    duration_ms: Optional[int]
    error_message: Optional[str]
    timestamp: str


class SessionResponse(BaseModel):
    """Full session data response."""

    session_id: str
    user_id: str
    created_at: str
    updated_at: str
    status: str
    metadata: Optional[Dict[str, Any]]
    conversation_history: List[ConversationMessage]
    agents_invoked: List[AgentInvocation]
    last_agent_called: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "alice",
                "created_at": "2025-12-30T10:00:00Z",
                "updated_at": "2025-12-30T10:05:00Z",
                "status": "active",
                "metadata": {"client": "web"},
                "conversation_history": [
                    {
                        "role": "user",
                        "content": "Show my tickets",
                        "timestamp": "2025-12-30T10:00:00Z"
                    }
                ],
                "agents_invoked": [
                    {
                        "agent_name": "tickets_agent",
                        "query": "Show my tickets",
                        "response": "You have 3 tickets",
                        "success": True,
                        "duration_ms": 150,
                        "error_message": None,
                        "timestamp": "2025-12-30T10:00:01Z"
                    }
                ],
                "last_agent_called": "tickets_agent"
            }
        }
