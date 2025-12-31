"""
FinOps Agent Service - Self-contained A2A service

Port: 8081
Agent Card: http://localhost:8081/.well-known/agent-card.json

This is a complete, self-contained agent service that includes:
- Agent definition (LlmAgent)
- Tools/business logic (cloud cost analytics)
- Data layer (in-memory database)
- A2A server exposure
"""

import os
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from typing import Dict, List

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# In-memory cloud cost database
CLOUD_COSTS = {
    "aws": {
        "total": 15234.50,
        "services": [
            {"name": "ec2", "cost": 8500.00},
            {"name": "s3", "cost": 4234.50},
            {"name": "dynamodb", "cost": 2500.00}
        ]
    },
    "gcp": {
        "total": 12450.75,
        "services": [
            {"name": "compute", "cost": 7200.00},
            {"name": "vault", "cost": 3250.75},
            {"name": "firestore", "cost": 2000.00}
        ]
    },
    "azure": {
        "total": 8920.25,
        "services": [
            {"name": "storage", "cost": 5420.25},
            {"name": "ai_studio", "cost": 3500.00}
        ]
    }
}

# =============================================================================
# Tool Functions (Business Logic)
# =============================================================================

def get_all_clouds_cost() -> Dict:
    """Get total cost across all cloud providers.

    Returns:
        Total cost and breakdown by provider
    """
    total = sum(provider["total"] for provider in CLOUD_COSTS.values())
    return {
        "total_cost": total,
        "providers": CLOUD_COSTS,
        "currency": "USD"
    }


def get_cloud_cost(provider: str) -> Dict:
    """Get detailed costs for a specific cloud provider.

    Args:
        provider: Cloud provider name (aws, gcp, azure)

    Returns:
        Detailed cost breakdown for the provider
    """
    provider = provider.lower()
    if provider not in CLOUD_COSTS:
        return {
            "error": f"Provider '{provider}' not found. Available: aws, gcp, azure"
        }
    return {
        "provider": provider,
        **CLOUD_COSTS[provider],
        "currency": "USD"
    }


def get_service_cost(service_name: str) -> Dict:
    """Get cost for a specific service across all providers.

    Args:
        service_name: Service name (e.g., ec2, s3, compute)

    Returns:
        Service cost across all providers
    """
    results = []
    total = 0.0

    for provider, data in CLOUD_COSTS.items():
        for service in data["services"]:
            if service_name.lower() in service["name"].lower():
                results.append({
                    "provider": provider,
                    "service": service["name"],
                    "cost": service["cost"]
                })
                total += service["cost"]

    if not results:
        return {"error": f"Service '{service_name}' not found"}

    return {
        "service": service_name,
        "total_cost": total,
        "breakdown": results,
        "currency": "USD"
    }


def get_cost_breakdown() -> Dict:
    """Get comprehensive cost breakdown with percentages.

    Returns:
        Complete cost breakdown with provider percentages
    """
    total = sum(p["total"] for p in CLOUD_COSTS.values())

    breakdown = []
    for provider, data in CLOUD_COSTS.items():
        percentage = (data["total"] / total) * 100
        breakdown.append({
            "provider": provider,
            "cost": data["total"],
            "percentage": round(percentage, 2),
            "services": data["services"]
        })

    # Sort by cost descending
    breakdown.sort(key=lambda x: x["cost"], reverse=True)

    return {
        "total_cost": total,
        "breakdown": breakdown,
        "currency": "USD"
    }


# =============================================================================
# Agent Setup
# =============================================================================

# Create agent with tools
finops_agent = LlmAgent(
    name="FinOpsAgent",
    model="gemini-2.5-flash",
    description="Cloud financial operations and cost analytics agent",
    instruction="""You are a specialized FinOps (Financial Operations) assistant for cloud cost analytics.

**Your Responsibilities:**
- Analyze cloud costs across AWS, GCP, and Azure
- Provide cost breakdowns by provider and service
- Help identify cost optimization opportunities
- Answer questions about cloud spending

**Note on User Context:**
- Cloud cost data is organization-wide (not user-specific)
- You'll receive queries from authenticated users
- Provide the same cost information to all users

**Available Tools:**
- get_all_clouds_cost: Total cost across all cloud providers
- get_cloud_cost: Detailed costs for specific provider (aws, gcp, azure)
- get_service_cost: Cost for specific service (e.g., ec2, s3, compute)
- get_cost_breakdown: Comprehensive breakdown with percentages

**Cloud Providers:**
- AWS: EC2, S3, DynamoDB
- GCP: Compute, Vault, Firestore
- Azure: Storage, AI Studio

**Communication Style:**
- Always mention currency (USD)
- Use percentages to show proportions
- Highlight the highest cost items
- Provide context for cost data
- Be specific about which provider or service

**Cost Analysis Tips:**
- Show both absolute costs and percentages
- Compare costs across providers
- Identify largest cost drivers
- Explain service-level details when requested

**Example Queries:**
- "What's our total cloud cost?"
- "Show me AWS costs"
- "How much do we spend on GCP compute?"
- "Give me a complete cost breakdown"
""",
    tools=[get_all_clouds_cost, get_cloud_cost, get_service_cost, get_cost_breakdown]
)

# =============================================================================
# A2A Server
# =============================================================================

# Expose agent via A2A protocol (at module level for uvicorn)
a2a_app = to_a2a(
    finops_agent,
    port=8081,
    host="0.0.0.0"
)

if __name__ == "__main__":
    print("=" * 80)
    print("✅ FinOps Agent Service Started")
    print("=" * 80)
    print(f"Port:        8081")
    print(f"Agent Card:  http://localhost:8081/.well-known/agent-card.json")
    print(f"Health:      http://localhost:8081/health")
    print(f"Invoke:      http://localhost:8081/invoke")
    print("=" * 80)
    print("")
    print("Service is ready to handle requests via A2A protocol")
    print("Press Ctrl+C to stop")
    print("")
