"""
FinOps MCP Server - Tool Definitions
Uses FastMCP library for Model Context Protocol.

Port: 5012 (NEW - parallel to existing 5002)
Protocol: MCP (Model Context Protocol)
Phase: 2A - No authentication (basic MCP functionality)

This server provides cloud financial operations and cost analytics tools via MCP.
Authentication infrastructure will be added in Task 11 (Phase 2B with ADK compliance).
"""

from fastmcp import FastMCP
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

# =============================================================================
# In-Memory Cloud Cost Database (Mock Data - Same as Phase 1)
# =============================================================================
# In production, this would be replaced with real cloud billing API connections

FINOPS_DB: Dict[str, Dict[str, Any]] = {
    "aws": {
        "cost": 100,
        "services": [
            {"name": "ec2", "cost": 50},
            {"name": "s3", "cost": 30},
            {"name": "dynamodb", "cost": 20}
        ]
    },
    "gcp": {
        "cost": 250,
        "services": [
            {"name": "compute", "cost": 100},
            {"name": "vault", "cost": 50},
            {"name": "firestore", "cost": 100}
        ]
    },
    "azure": {
        "cost": 300,
        "services": [
            {"name": "storage", "cost": 100},
            {"name": "AI Studio", "cost": 200}
        ]
    }
}

# =============================================================================
# FastMCP Server Instance
# =============================================================================

mcp = FastMCP("finops-server")


# =============================================================================
# PUBLIC TOOLS (No Authentication - Phase 2A)
# =============================================================================
# Note: FinOps costs are organization-wide, so most tools don't require auth.
# User-specific cost allocation features could be added in future phases.


@mcp.tool()
def get_all_clouds_cost() -> Dict[str, Any]:
    """Get cost summary for all cloud providers.

    Returns comprehensive cost overview across AWS, GCP, and Azure,
    including total cost and percentage breakdown by provider.

    Returns:
        Dict[str, Any]: Cost summary with fields:
            - total_cost (float): Total cost across all providers
            - currency (str): Currency code (USD)
            - providers (Dict): Per-provider breakdown with:
                - cost (float): Provider's total cost
                - percentage (float): Percentage of total cost

    Example:
        >>> result = get_all_clouds_cost()
        >>> result['total_cost']
        650
        >>> result['providers']['aws']['percentage']
        15.38
    """
    total_cost = sum(provider_data["cost"] for provider_data in FINOPS_DB.values())

    providers_summary = {
        provider: {
            "cost": data["cost"],
            "percentage": round((data["cost"] / total_cost * 100), 2)
        }
        for provider, data in FINOPS_DB.items()
    }

    return {
        "total_cost": total_cost,
        "currency": "USD",
        "providers": providers_summary
    }


@mcp.tool()
def get_cloud_cost(provider: str) -> Dict[str, Any]:
    """Get cost details for a specific cloud provider.

    Retrieves detailed cost information for a specific cloud provider,
    including service-level breakdown.

    Args:
        provider (str): Cloud provider name (aws, gcp, or azure).
            Case-insensitive.

    Returns:
        Dict[str, Any]: Provider cost details with fields:
            - provider (str): Provider name (lowercase)
            - total_cost (float): Total cost for this provider
            - currency (str): Currency code (USD)
            - services (List[Dict]): Service breakdown with name and cost
            - service_count (int): Number of services

        Or error dict if provider not found:
            - error (str): Error message
            - available_providers (List[str]): List of valid providers

    Example:
        >>> result = get_cloud_cost("aws")
        >>> result['total_cost']
        100
        >>> len(result['services'])
        3
    """
    provider_lower = provider.lower()

    if provider_lower not in FINOPS_DB:
        return {
            "error": f"Provider '{provider}' not found. Available providers: aws, gcp, azure",
            "available_providers": list(FINOPS_DB.keys())
        }

    provider_data = FINOPS_DB[provider_lower]

    return {
        "provider": provider_lower,
        "total_cost": provider_data["cost"],
        "currency": "USD",
        "services": provider_data["services"],
        "service_count": len(provider_data["services"])
    }


@mcp.tool()
def get_service_cost(provider: str, service_name: str) -> Dict[str, Any]:
    """Get cost for a specific service within a cloud provider.

    Retrieves cost information for a specific service (e.g., EC2, S3)
    within a cloud provider, including its percentage of provider cost.

    Args:
        provider (str): Cloud provider name (aws, gcp, or azure)
        service_name (str): Service name (e.g., ec2, s3, compute).
            Case-insensitive.

    Returns:
        Dict[str, Any]: Service cost details with fields:
            - provider (str): Provider name
            - service (str): Service name
            - cost (float): Service cost
            - currency (str): Currency code (USD)
            - percentage_of_provider (float): Service % of provider total

        Or error dict if not found:
            - error (str): Error message
            - available_services (List[str]): Valid services for provider

    Example:
        >>> result = get_service_cost("aws", "ec2")
        >>> result['cost']
        50
        >>> result['percentage_of_provider']
        50.0
    """
    provider_lower = provider.lower()
    service_lower = service_name.lower()

    if provider_lower not in FINOPS_DB:
        return {
            "error": f"Provider '{provider}' not found",
            "available_providers": list(FINOPS_DB.keys())
        }

    provider_data = FINOPS_DB[provider_lower]

    # Search for the service (case-insensitive)
    for service in provider_data["services"]:
        if service["name"].lower() == service_lower:
            provider_total = provider_data["cost"]
            service_percentage = round((service["cost"] / provider_total * 100), 2)

            return {
                "provider": provider_lower,
                "service": service["name"],
                "cost": service["cost"],
                "currency": "USD",
                "percentage_of_provider": service_percentage
            }

    # Service not found
    available_services = [s["name"] for s in provider_data["services"]]
    return {
        "error": f"Service '{service_name}' not found in {provider}",
        "available_services": available_services
    }


@mcp.tool()
def get_cost_breakdown() -> Dict[str, Any]:
    """Get detailed cost breakdown with percentages across all providers.

    Returns comprehensive cost analysis with multi-level percentages:
    - Provider percentage of total cost
    - Service percentage of provider cost
    - Service percentage of total cost

    Providers are sorted by cost (highest first).

    Returns:
        Dict[str, Any]: Complete breakdown with fields:
            - total_cost (float): Total cost across all providers
            - currency (str): Currency code (USD)
            - providers (List[Dict]): Provider breakdown (sorted by cost):
                - name (str): Provider name
                - total_cost (float): Provider total
                - percentage_of_total (float): % of grand total
                - services (List[Dict]): Service details:
                    - name (str): Service name
                    - cost (float): Service cost
                    - percentage_of_provider (float): % of provider
                    - percentage_of_total (float): % of grand total

    Example:
        >>> result = get_cost_breakdown()
        >>> result['total_cost']
        650
        >>> result['providers'][0]['name']
        'azure'  # Highest cost provider
        >>> len(result['providers'])
        3
    """
    total_cost = sum(provider_data["cost"] for provider_data in FINOPS_DB.values())

    breakdown = {
        "total_cost": total_cost,
        "currency": "USD",
        "providers": []
    }

    for provider, data in FINOPS_DB.items():
        provider_percentage = round((data["cost"] / total_cost * 100), 2)

        services_detail = []
        for service in data["services"]:
            service_percentage_of_total = round((service["cost"] / total_cost * 100), 2)
            service_percentage_of_provider = round((service["cost"] / data["cost"] * 100), 2)

            services_detail.append({
                "name": service["name"],
                "cost": service["cost"],
                "percentage_of_provider": service_percentage_of_provider,
                "percentage_of_total": service_percentage_of_total
            })

        breakdown["providers"].append({
            "name": provider,
            "total_cost": data["cost"],
            "percentage_of_total": provider_percentage,
            "services": services_detail
        })

    # Sort providers by cost (descending)
    breakdown["providers"].sort(key=lambda x: x["total_cost"], reverse=True)

    return breakdown


# =============================================================================
# AUTHENTICATED TOOLS (Will be added in Task 11 - if needed)
# =============================================================================
# FinOps costs are organization-wide, so authentication is optional.
# However, infrastructure will be ready in Task 11 for:
# - User-specific cost allocation
# - Department/team cost filtering
# - Budget alerts per user
#
# These would use ADK's ToolContext pattern:
#   bearer_token = tool_context.state.get("user:bearer_token")
#
# This is the CORRECT ADK-compliant pattern (not bearer_token as parameter).
