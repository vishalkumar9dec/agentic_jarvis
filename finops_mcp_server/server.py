"""
FinOps MCP Server - Tool Definitions
Uses FastMCP library for Model Context Protocol.

Port: 5012 (NEW - parallel to existing 5002)
Protocol: MCP (Model Context Protocol)
Phase: 2B - With authentication for user-specific features

This server provides cloud financial operations and cost analytics tools via MCP.
Public tools for organization-wide costs, authenticated tools for user budgets.
"""

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import sys
import os

# Add project root to Python path for auth imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.jwt_utils import verify_jwt_token

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

# User-specific budget allocations (for authenticated features)
USER_BUDGETS_DB: Dict[str, Dict[str, Any]] = {
    "vishal": {
        "monthly_budget": 500,
        "current_spend": 350,
        "departments": ["engineering", "ai_research"],
        "allocated_costs": {
            "aws": 100,
            "gcp": 150,
            "azure": 100
        },
        "alerts_enabled": True
    },
    "alex": {
        "monthly_budget": 300,
        "current_spend": 200,
        "departments": ["devops", "infrastructure"],
        "allocated_costs": {
            "aws": 50,
            "gcp": 100,
            "azure": 50
        },
        "alerts_enabled": True
    },
    "sarah": {
        "monthly_budget": 400,
        "current_spend": 380,
        "departments": ["data_science", "ml"],
        "allocated_costs": {
            "aws": 80,
            "gcp": 200,
            "azure": 100
        },
        "alerts_enabled": False
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
# AUTHENTICATED TOOLS (Task 12 - User-Specific Budget Management)
# =============================================================================
# These tools use HTTP Authorization headers for authentication.
# Authentication is validated using JWT tokens.


@mcp.tool()
def get_my_budget() -> Dict[str, Any]:
    """Get budget allocation and spending for the authenticated user.

    This tool requires authentication via HTTP Authorization header.
    Returns the user's budget information, current spend, and budget utilization.

    Authentication Flow:
    1. CLI sets bearer token in context: set_bearer_token(token)
    2. McpToolset's header_provider injects: Authorization: Bearer <token>
    3. FastMCP receives HTTP request with Authorization header
    4. This tool extracts token using get_http_headers()
    5. Token is validated and user's budget data is returned

    Returns:
        Dict[str, Any]: Budget information with fields:
            - success (bool): Whether operation succeeded
            - username (str): Authenticated user's username
            - budget (Dict): Budget details:
                - monthly_budget (float): Monthly budget allocation
                - current_spend (float): Current month's spending
                - remaining (float): Budget remaining
                - utilization_percentage (float): % of budget used
                - status (str): "within_budget", "near_limit", or "over_budget"
                - departments (List[str]): User's departments
                - allocated_costs (Dict): Cost breakdown by provider
                - alerts_enabled (bool): Budget alert status

        Returns error dict if authentication fails.

    Example (when authenticated as vishal):
        >>> # HTTP Request includes: Authorization: Bearer <valid_jwt>
        >>> result = get_my_budget()
        >>> result['budget']['monthly_budget']
        500
        >>> result['budget']['utilization_percentage']
        70.0
    """
    # Extract bearer token from HTTP Authorization header
    headers = get_http_headers()
    auth_header = headers.get("authorization", "")

    if not auth_header:
        return {
            "success": False,
            "error": "Authentication required",
            "status": 401,
            "message": "Please log in to access your budget information"
        }

    # Extract token from "Bearer <token>" format
    if not auth_header.startswith("Bearer "):
        return {
            "success": False,
            "error": "Invalid authorization header format",
            "status": 401,
            "message": "Authorization header must use Bearer scheme"
        }

    bearer_token = auth_header[7:]  # Remove "Bearer " prefix

    # Validate token
    payload = verify_jwt_token(bearer_token)
    if not payload:
        return {
            "success": False,
            "error": "Invalid or expired token",
            "status": 401,
            "message": "Your session has expired. Please log in again."
        }

    current_user = payload.get("username")
    if not current_user:
        return {
            "success": False,
            "error": "Token missing username claim",
            "status": 401
        }

    # Get user's budget data
    username_lower = current_user.lower()
    if username_lower not in USER_BUDGETS_DB:
        return {
            "success": False,
            "error": f"No budget allocation found for user '{current_user}'",
            "status": 404,
            "message": "Contact your FinOps administrator to set up your budget"
        }

    user_budget = USER_BUDGETS_DB[username_lower]

    # Calculate budget metrics
    monthly_budget = user_budget["monthly_budget"]
    current_spend = user_budget["current_spend"]
    remaining = monthly_budget - current_spend
    utilization = round((current_spend / monthly_budget * 100), 2) if monthly_budget > 0 else 0

    # Determine budget status
    if utilization >= 100:
        status = "over_budget"
    elif utilization >= 80:
        status = "near_limit"
    else:
        status = "within_budget"

    return {
        "success": True,
        "username": username_lower,
        "budget": {
            "monthly_budget": monthly_budget,
            "current_spend": current_spend,
            "remaining": remaining,
            "utilization_percentage": utilization,
            "status": status,
            "departments": user_budget["departments"],
            "allocated_costs": user_budget["allocated_costs"],
            "alerts_enabled": user_budget["alerts_enabled"]
        }
    }


@mcp.tool()
def get_my_cost_allocation() -> Dict[str, Any]:
    """Get detailed cost allocation breakdown for the authenticated user.

    This tool requires authentication via HTTP Authorization header.
    Returns the user's allocated costs across cloud providers with detailed analytics.

    Returns:
        Dict[str, Any]: Cost allocation details with fields:
            - success (bool): Whether operation succeeded
            - username (str): Authenticated user's username
            - total_allocated (float): Total costs allocated to user
            - allocation_by_provider (List[Dict]): Provider breakdown (sorted by cost):
                - provider (str): Cloud provider name
                - allocated_cost (float): Cost allocated to user
                - percentage_of_user_total (float): % of user's total allocation
            - departments (List[str]): User's departments
            - budget_comparison (Dict): Comparison with budget:
                - allocated_vs_budget (float): Difference from budget
                - budget_status (str): Status indicator

        Returns error dict if authentication fails.

    Example (when authenticated as alex):
        >>> result = get_my_cost_allocation()
        >>> result['total_allocated']
        200
        >>> len(result['allocation_by_provider'])
        3
    """
    # Extract bearer token from HTTP Authorization header
    headers = get_http_headers()
    auth_header = headers.get("authorization", "")

    if not auth_header:
        return {
            "success": False,
            "error": "Authentication required",
            "status": 401,
            "message": "Please log in to access your cost allocation"
        }

    if not auth_header.startswith("Bearer "):
        return {
            "success": False,
            "error": "Invalid authorization header format",
            "status": 401,
            "message": "Authorization header must use Bearer scheme"
        }

    bearer_token = auth_header[7:]

    # Validate token
    payload = verify_jwt_token(bearer_token)
    if not payload:
        return {
            "success": False,
            "error": "Invalid or expired token",
            "status": 401,
            "message": "Your session has expired. Please log in again."
        }

    current_user = payload.get("username")
    if not current_user:
        return {
            "success": False,
            "error": "Token missing username claim",
            "status": 401
        }

    # Get user's budget data
    username_lower = current_user.lower()
    if username_lower not in USER_BUDGETS_DB:
        return {
            "success": False,
            "error": f"No cost allocation found for user '{current_user}'",
            "status": 404
        }

    user_budget = USER_BUDGETS_DB[username_lower]
    allocated_costs = user_budget["allocated_costs"]

    # Calculate total allocated
    total_allocated = sum(allocated_costs.values())

    # Build provider breakdown
    allocation_breakdown = []
    for provider, cost in allocated_costs.items():
        percentage = round((cost / total_allocated * 100), 2) if total_allocated > 0 else 0
        allocation_breakdown.append({
            "provider": provider,
            "allocated_cost": cost,
            "percentage_of_user_total": percentage
        })

    # Sort by cost (descending)
    allocation_breakdown.sort(key=lambda x: x["allocated_cost"], reverse=True)

    # Budget comparison
    monthly_budget = user_budget["monthly_budget"]
    current_spend = user_budget["current_spend"]
    allocated_vs_budget = current_spend - monthly_budget

    if allocated_vs_budget > 0:
        budget_status = f"Over budget by ${allocated_vs_budget}"
    elif allocated_vs_budget == 0:
        budget_status = "Exactly at budget limit"
    else:
        budget_status = f"Within budget (${abs(allocated_vs_budget)} remaining)"

    return {
        "success": True,
        "username": username_lower,
        "total_allocated": total_allocated,
        "allocation_by_provider": allocation_breakdown,
        "departments": user_budget["departments"],
        "budget_comparison": {
            "monthly_budget": monthly_budget,
            "current_spend": current_spend,
            "allocated_vs_budget": allocated_vs_budget,
            "budget_status": budget_status
        }
    }
