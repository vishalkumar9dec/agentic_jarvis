"""
FinOps Toolbox Server
Provides cloud financial operations data and analytics tools via FastAPI.
Port: 5002
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel
import inspect

# In-memory cloud cost database
FINOPS_DB = {
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


# ============================================================================
# Tool Functions
# ============================================================================

def get_all_clouds_cost() -> Dict[str, Any]:
    """Get cost summary for all cloud providers.

    Returns:
        Dictionary with total cost and breakdown by provider
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


def get_cloud_cost(provider: str) -> Optional[Dict[str, Any]]:
    """Get cost details for a specific cloud provider.

    Args:
        provider: Cloud provider name (aws, gcp, or azure)

    Returns:
        Provider cost details with service breakdown or None if not found
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


def get_service_cost(provider: str, service_name: str) -> Optional[Dict[str, Any]]:
    """Get cost for a specific service within a cloud provider.

    Args:
        provider: Cloud provider name (aws, gcp, or azure)
        service_name: Name of the service (e.g., ec2, s3, compute)

    Returns:
        Service cost details or error if not found
    """
    provider_lower = provider.lower()
    service_lower = service_name.lower()

    if provider_lower not in FINOPS_DB:
        return {
            "error": f"Provider '{provider}' not found",
            "available_providers": list(FINOPS_DB.keys())
        }

    provider_data = FINOPS_DB[provider_lower]

    # Search for the service
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


def get_cost_breakdown() -> Dict[str, Any]:
    """Get detailed cost breakdown with percentages across all providers.

    Returns:
        Complete breakdown with totals, percentages, and service-level details
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


# ============================================================================
# Toolbox Pattern Implementation
# ============================================================================

# Define toolsets
TOOLSETS = {
    "finops_toolset": {
        "get_all_clouds_cost": get_all_clouds_cost,
        "get_cloud_cost": get_cloud_cost,
        "get_service_cost": get_service_cost,
        "get_cost_breakdown": get_cost_breakdown
    }
}


def function_to_tool_schema(func: Callable) -> Dict[str, Any]:
    """Convert a Python function to Toolbox tool schema format.

    Args:
        func: The function to convert

    Returns:
        Tool schema dict with description and parameters
    """
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""

    # Parse docstring for description
    lines = doc.split('\n')
    description = lines[0] if lines else func.__name__

    # Extract parameter descriptions from docstring
    param_descriptions = {}
    in_args_section = False
    for line in lines:
        line = line.strip()
        if line.lower().startswith('args:'):
            in_args_section = True
            continue
        if line.lower().startswith('returns:'):
            in_args_section = False
            continue
        if in_args_section and ':' in line:
            parts = line.split(':', 1)
            param_name = parts[0].strip()
            param_desc = parts[1].strip() if len(parts) > 1 else ""
            param_descriptions[param_name] = param_desc

    # Build parameter list (not a JSON Schema object)
    parameters = []

    for param_name, param in sig.parameters.items():
        param_type = "string"  # Default type
        is_required = param.default == inspect.Parameter.empty

        if param.annotation != inspect.Parameter.empty:
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == list or param.annotation == List:
                param_type = "array"
            elif param.annotation == dict or param.annotation == Dict:
                param_type = "object"

        param_schema = {
            "name": param_name,
            "type": param_type,
            "required": is_required,
            "description": param_descriptions.get(param_name, f"The {param_name} parameter")
        }

        parameters.append(param_schema)

    return {
        "description": description,
        "parameters": parameters,
        "authRequired": []  # No auth required for these tools
    }


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="FinOps Toolbox Server",
    description="MCP-compatible toolbox server for cloud financial operations analytics",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "FinOps Toolbox Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/toolset/{toolset_name}")
async def get_toolset(toolset_name: str):
    """Get toolset manifest with all tools in the toolset."""
    if toolset_name not in TOOLSETS:
        return {"error": f"Toolset '{toolset_name}' not found"}, 404

    toolset = TOOLSETS[toolset_name]
    tools = {}

    for func_name, tool_func in toolset.items():
        tool_schema = function_to_tool_schema(tool_func)
        # Use the function name (converted to kebab-case) as the key
        tool_key = func_name.replace('_', '-')
        tools[tool_key] = tool_schema

    return {
        "serverVersion": "1.0.0",
        "name": toolset_name,
        "tools": tools
    }


@app.get("/api/tool/{tool_name}")
async def get_tool(tool_name: str):
    """Get individual tool schema."""
    # Search for tool in all toolsets
    for toolset_name, toolset in TOOLSETS.items():
        for func_name, tool_func in toolset.items():
            if func_name.replace('_', '-') == tool_name or func_name == tool_name:
                return function_to_tool_schema(tool_func)

    return {"error": f"Tool '{tool_name}' not found"}, 404


@app.post("/api/tool/{tool_name}/invoke")
async def execute_tool(tool_name: str, params: Dict[str, Any]):
    """Execute a tool with given parameters."""
    # Search for tool in all toolsets
    for toolset_name, toolset in TOOLSETS.items():
        for func_name, tool_func in toolset.items():
            if func_name.replace('_', '-') == tool_name or func_name == tool_name:
                try:
                    result = tool_func(**params)
                    return {"result": result}
                except Exception as e:
                    return {"error": str(e)}, 500

    return {"error": f"Tool '{tool_name}' not found"}, 404


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5002)
