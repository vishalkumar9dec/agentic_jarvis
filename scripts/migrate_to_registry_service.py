#!/usr/bin/env python3
"""
Agent Registration Script - A2A Agent Card URLs

This script registers all agents with the Agent Registry Service using
agent card URLs. All agents are now remote A2A agents.

Agent Services:
- TicketsAgent: http://localhost:8080
- FinOpsAgent: http://localhost:8081
- OxygenAgent: http://localhost:8082

Usage:
    python scripts/migrate_to_registry_service.py

Prerequisites:
    1. Agent Registry Service must be running on port 8003
       Start with: python agent_registry_service/main.py

    2. All agent services must be running:
       Start with: ./scripts/start_all_agents.sh
"""

import requests
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# =============================================================================
# Configuration
# =============================================================================

REGISTRY_URL = "http://localhost:8003"

AGENTS = [
    {
        "agent_config": {
            "agent_type": "tickets",
            "agent_card_url": "http://localhost:8080/.well-known/agent-card.json",
            "name": "TicketsAgent",
            "description": "IT operations ticket management"
        },
        "capabilities": {
            "domains": ["tickets", "IT", "operations"],
            "entities": ["ticket", "request", "vpn", "gitlab"],
            "operations": ["create", "read", "update", "list"],
            "keywords": ["ticket", "IT", "operation"],
            "priority": 10
        },
        "tags": ["core", "production", "a2a"]
    },
    {
        "agent_config": {
            "agent_type": "finops",
            "agent_card_url": "http://localhost:8081/.well-known/agent-card.json",
            "name": "FinOpsAgent",
            "description": "Cloud financial operations and cost analytics"
        },
        "capabilities": {
            "domains": ["costs", "finops", "cloud", "budget"],
            "entities": ["cost", "budget", "service", "provider"],
            "operations": ["read", "analyze", "breakdown"],
            "keywords": ["cost", "budget", "aws", "gcp", "azure"],
            "priority": 8
        },
        "tags": ["core", "production", "a2a"]
    },
    {
        "agent_config": {
            "agent_type": "oxygen",
            "agent_card_url": "http://localhost:8082/.well-known/agent-card.json",
            "name": "OxygenAgent",
            "description": "Learning and development platform"
        },
        "capabilities": {
            "domains": ["learning", "courses", "exams", "education"],
            "entities": ["course", "exam", "preference", "deadline"],
            "operations": ["read", "track", "monitor"],
            "keywords": ["course", "exam", "learning", "education"],
            "priority": 7
        },
        "tags": ["core", "production", "a2a"]
    }
]

# =============================================================================
# Helper Functions
# =============================================================================

def check_registry_health():
    """Check if registry service is running."""
    try:
        response = requests.get(f"{REGISTRY_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_agent_card(agent_card_url):
    """Check if agent card is accessible."""
    try:
        response = requests.get(agent_card_url, timeout=5)
        return response.status_code == 200
    except:
        return False


def register_agent(agent_config):
    """Register a single agent."""
    try:
        response = requests.post(
            f"{REGISTRY_URL}/registry/agents",
            json=agent_config,
            timeout=10
        )

        if response.status_code in [200, 201]:
            return True, "Success"
        else:
            return False, response.text

    except Exception as e:
        return False, str(e)


# =============================================================================
# Main
# =============================================================================

def main():
    """Register all agents."""

    print("=" * 80)
    print("Agent Registration (A2A Agent Card URLs)")
    print("=" * 80)
    print()

    # Check registry service
    print("Checking registry service...")
    if not check_registry_health():
        print("✗ ERROR: Registry service not available at", REGISTRY_URL)
        print("  Start with: python agent_registry_service/main.py")
        sys.exit(1)
    print("✓ Registry service is running")
    print()

    # Register each agent
    print("Registering agents...")
    print()

    success_count = 0

    for agent_data in AGENTS:
        agent_name = agent_data["agent_config"]["name"]
        agent_card_url = agent_data["agent_config"]["agent_card_url"]

        print(f"  {agent_name}:")
        print(f"    Agent Card: {agent_card_url}")

        # Check agent card
        if not check_agent_card(agent_card_url):
            print(f"    ⚠  WARNING: Agent card not accessible (service may not be running)")

        # Register
        success, message = register_agent(agent_data)

        if success:
            print(f"    ✓ Registered successfully")
            success_count += 1
        else:
            print(f"    ✗ Failed: {message}")

        print()

    # Summary
    print("=" * 80)
    print(f"Registration complete: {success_count}/{len(AGENTS)} agents registered")
    print("=" * 80)
    print()

    if success_count < len(AGENTS):
        print("⚠  Some agents failed to register")
        print("  Make sure all agent services are running:")
        print("    ./scripts/start_all_agents.sh")
        print()
        sys.exit(1)
    else:
        print("✓ All agents registered successfully!")
        print()
        print("Verify registration:")
        print("  curl http://localhost:8003/registry/agents | jq .")
        print()
        print("Test agent cards:")
        print("  curl http://localhost:8080/.well-known/agent-card.json | jq .")
        print("  curl http://localhost:8081/.well-known/agent-card.json | jq .")
        print("  curl http://localhost:8082/.well-known/agent-card.json | jq .")
        print()
        print("Next step:")
        print("  python jarvis_agent/main_with_registry.py")
        print()


if __name__ == "__main__":
    main()
