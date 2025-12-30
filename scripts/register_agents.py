#!/usr/bin/env python3
"""
Agent Registration Helper Script

This script helps you register agents with the Agent Registry Service.
Supports both local agents (first-party) and remote agents (third-party).

Usage:
    python scripts/register_agents.py --all                    # Register all agents
    python scripts/register_agents.py --local                  # Register local agents only
    python scripts/register_agents.py --remote                 # Register remote agents only
    python scripts/register_agents.py --agent oxygen_agent     # Register specific agent
    python scripts/register_agents.py --list                   # List registered agents
"""

import argparse
import sys
import time
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_REGISTRY_URL = "http://localhost:8003"
DEFAULT_TIMEOUT = 10

# Global variable that can be updated
REGISTRY_URL = DEFAULT_REGISTRY_URL


# =============================================================================
# Agent Definitions
# =============================================================================

LOCAL_AGENTS = [
    {
        "name": "tickets_agent",
        "agent_config": {
            "agent_type": "tickets",
            "factory_module": "jarvis_agent.mcp_agents.agent_factory",
            "factory_function": "create_tickets_agent",
            "factory_params": {}
        },
        "capabilities": {
            "domains": ["tickets", "IT", "support"],
            "operations": ["create", "read", "update", "delete", "search"],
            "entities": ["ticket", "vpn_access", "ai_key", "gitlab_account"],
            "keywords": ["ticket", "vpn", "ai key", "gitlab", "create", "show", "list"],
            "examples": [
                "Show my tickets",
                "Create a VPN access ticket",
                "List all pending tickets"
            ],
            "priority": 10
        },
        "tags": ["first-party", "production", "it-ops"]
    },
    {
        "name": "finops_agent",
        "agent_config": {
            "agent_type": "finops",
            "factory_module": "jarvis_agent.mcp_agents.agent_factory",
            "factory_function": "create_finops_agent",
            "factory_params": {}
        },
        "capabilities": {
            "domains": ["finops", "cloud", "cost", "billing"],
            "operations": ["read", "analyze", "report"],
            "entities": ["cost", "service", "provider", "bill"],
            "keywords": ["cost", "billing", "cloud", "aws", "gcp", "azure", "spend"],
            "examples": [
                "Show cloud costs for this month",
                "Compare AWS and GCP spending",
                "What are the top cost services?"
            ],
            "priority": 8
        },
        "tags": ["first-party", "production", "finops"]
    }
]

REMOTE_AGENTS = [
    {
        "name": "oxygen_agent",
        "agent_card_url": "http://localhost:8002/.well-known/agent-card.json",
        "capabilities": {
            "domains": ["learning", "education", "courses", "training"],
            "operations": ["read", "search", "enroll", "schedule"],
            "entities": ["course", "exam", "enrollment", "user", "deadline"],
            "keywords": ["course", "exam", "learning", "enroll", "study", "training"],
            "examples": [
                "Show my enrolled courses",
                "What exams do I have pending?",
                "Enroll me in Python course",
                "When is my next exam deadline?"
            ],
            "priority": 7
        },
        "tags": ["remote", "a2a", "learning", "education"],
        "provider": {
            "name": "Oxygen Learning Platform",
            "website": "http://localhost:8002",
            "support_email": "support@oxygen.example.com",
            "documentation": "http://localhost:8002/docs"
        },
        "auth_config": {
            "type": "bearer",
            "token_endpoint": "http://localhost:8002/auth/token",
            "scopes": ["read:courses", "read:exams", "write:enrollments"]
        }
    }
]


# =============================================================================
# Helper Functions
# =============================================================================

def check_registry_health() -> bool:
    """Check if registry service is running."""
    try:
        response = requests.get(f"{REGISTRY_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def register_local_agent(agent_def: Dict) -> bool:
    """Register a local agent."""
    try:
        print(f"  Registering local agent: {agent_def['name']}...", end=" ")

        response = requests.post(
            f"{REGISTRY_URL}/registry/agents",
            json={
                "agent_config": agent_def["agent_config"],
                "capabilities": agent_def["capabilities"],
                "tags": agent_def["tags"]
            },
            timeout=DEFAULT_TIMEOUT
        )

        if response.status_code == 201:
            print("✓ SUCCESS")
            return True
        elif response.status_code == 400 and "already registered" in response.text.lower():
            print("⚠ ALREADY EXISTS")
            return True
        else:
            print(f"✗ FAILED ({response.status_code})")
            print(f"    Error: {response.json().get('detail', 'Unknown error')}")
            return False

    except requests.RequestException as e:
        print(f"✗ FAILED")
        print(f"    Error: {e}")
        return False


def register_remote_agent(agent_def: Dict) -> bool:
    """Register a remote agent."""
    try:
        print(f"  Registering remote agent: {agent_def['name']}...", end=" ")

        # First, verify agent card is accessible
        try:
            card_response = requests.get(agent_def["agent_card_url"], timeout=5)
            if card_response.status_code != 200:
                print(f"✗ FAILED")
                print(f"    Error: Cannot reach agent card URL")
                return False
        except requests.RequestException:
            print(f"✗ FAILED")
            print(f"    Error: Agent card URL not accessible. Is the agent running?")
            return False

        # Register the agent
        response = requests.post(
            f"{REGISTRY_URL}/registry/agents/remote",
            json={
                "agent_card_url": agent_def["agent_card_url"],
                "capabilities": agent_def["capabilities"],
                "tags": agent_def["tags"],
                "provider": agent_def["provider"],
                "auth_config": agent_def.get("auth_config")
            },
            timeout=DEFAULT_TIMEOUT
        )

        if response.status_code == 201:
            result = response.json()
            status = result.get("data", {}).get("status", "pending")
            print(f"✓ SUCCESS (status: {status})")
            return True
        elif response.status_code == 400 and "already registered" in response.text.lower():
            print("⚠ ALREADY EXISTS")
            return True
        else:
            print(f"✗ FAILED ({response.status_code})")
            print(f"    Error: {response.json().get('detail', 'Unknown error')}")
            return False

    except requests.RequestException as e:
        print(f"✗ FAILED")
        print(f"    Error: {e}")
        return False


def list_agents() -> None:
    """List all registered agents."""
    try:
        response = requests.get(f"{REGISTRY_URL}/registry/agents", timeout=DEFAULT_TIMEOUT)

        if response.status_code != 200:
            print(f"Error: Failed to list agents ({response.status_code})")
            return

        data = response.json()
        agents = data.get("agents", [])

        if not agents:
            print("\nNo agents registered yet.")
            return

        print(f"\n{'='*80}")
        print(f"Registered Agents ({data.get('total', 0)} total)")
        print(f"{'='*80}\n")

        for agent in agents:
            agent_type = agent.get("type", "local")
            status_emoji = "✓" if agent.get("enabled", True) else "✗"

            print(f"{status_emoji} {agent['name']} ({agent_type})")
            print(f"  Description: {agent.get('description', 'N/A')}")
            print(f"  Domains: {', '.join(agent.get('capabilities', {}).get('domains', []))}")
            print(f"  Tags: {', '.join(agent.get('tags', []))}")

            if agent_type == "remote":
                print(f"  Agent Card: {agent.get('agent_card_url', 'N/A')}")
                print(f"  Status: {agent.get('status', 'N/A')}")
                provider = agent.get('provider', {})
                if provider:
                    print(f"  Provider: {provider.get('name', 'N/A')}")
            else:
                print(f"  Factory: {agent.get('factory_module', 'N/A')}.{agent.get('factory_function', 'N/A')}")

            print()

    except requests.RequestException as e:
        print(f"Error: Failed to list agents: {e}")


def get_agent_by_name(name: str) -> Optional[Dict]:
    """Get agent definition by name."""
    for agent in LOCAL_AGENTS:
        if agent["name"] == name:
            return {"type": "local", "data": agent}

    for agent in REMOTE_AGENTS:
        if agent["name"] == name:
            return {"type": "remote", "data": agent}

    return None


# =============================================================================
# Main Functions
# =============================================================================

def register_all_agents() -> None:
    """Register all agents (local + remote)."""
    print("\n" + "="*80)
    print("Registering All Agents")
    print("="*80 + "\n")

    # Register local agents
    print("Local Agents (First-Party):")
    local_success = 0
    for agent in LOCAL_AGENTS:
        if register_local_agent(agent):
            local_success += 1

    print(f"\n  Summary: {local_success}/{len(LOCAL_AGENTS)} local agents registered\n")

    # Register remote agents
    print("Remote Agents (Third-Party):")
    remote_success = 0
    for agent in REMOTE_AGENTS:
        if register_remote_agent(agent):
            remote_success += 1

    print(f"\n  Summary: {remote_success}/{len(REMOTE_AGENTS)} remote agents registered\n")

    # Overall summary
    total_success = local_success + remote_success
    total_agents = len(LOCAL_AGENTS) + len(REMOTE_AGENTS)

    print("="*80)
    print(f"Registration Complete: {total_success}/{total_agents} agents registered successfully")
    print("="*80 + "\n")


def register_local_agents_only() -> None:
    """Register only local agents."""
    print("\n" + "="*80)
    print("Registering Local Agents (First-Party)")
    print("="*80 + "\n")

    success = 0
    for agent in LOCAL_AGENTS:
        if register_local_agent(agent):
            success += 1

    print(f"\n{'='*80}")
    print(f"Registration Complete: {success}/{len(LOCAL_AGENTS)} local agents registered")
    print("="*80 + "\n")


def register_remote_agents_only() -> None:
    """Register only remote agents."""
    print("\n" + "="*80)
    print("Registering Remote Agents (Third-Party)")
    print("="*80 + "\n")

    success = 0
    for agent in REMOTE_AGENTS:
        if register_remote_agent(agent):
            success += 1

    print(f"\n{'='*80}")
    print(f"Registration Complete: {success}/{len(REMOTE_AGENTS)} remote agents registered")
    print("="*80 + "\n")


def register_specific_agent(agent_name: str) -> None:
    """Register a specific agent by name."""
    print(f"\n{'='*80}")
    print(f"Registering Agent: {agent_name}")
    print("="*80 + "\n")

    agent = get_agent_by_name(agent_name)

    if not agent:
        print(f"Error: Agent '{agent_name}' not found in configuration")
        print("\nAvailable agents:")
        for a in LOCAL_AGENTS:
            print(f"  - {a['name']} (local)")
        for a in REMOTE_AGENTS:
            print(f"  - {a['name']} (remote)")
        print()
        return

    if agent["type"] == "local":
        success = register_local_agent(agent["data"])
    else:
        success = register_remote_agent(agent["data"])

    print(f"\n{'='*80}")
    print(f"Registration {'Successful' if success else 'Failed'}")
    print("="*80 + "\n")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Register agents with the Agent Registry Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all                    Register all agents
  %(prog)s --local                  Register local agents only
  %(prog)s --remote                 Register remote agents only
  %(prog)s --agent oxygen_agent     Register specific agent
  %(prog)s --list                   List registered agents
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Register all agents")
    group.add_argument("--local", action="store_true", help="Register local agents only")
    group.add_argument("--remote", action="store_true", help="Register remote agents only")
    group.add_argument("--agent", type=str, metavar="NAME", help="Register specific agent")
    group.add_argument("--list", action="store_true", help="List registered agents")

    parser.add_argument(
        "--registry-url",
        type=str,
        default=DEFAULT_REGISTRY_URL,
        help=f"Registry service URL (default: {DEFAULT_REGISTRY_URL})"
    )

    args = parser.parse_args()

    # Update global registry URL if provided
    global REGISTRY_URL
    REGISTRY_URL = args.registry_url

    # Handle list command
    if args.list:
        print("\nChecking registry service...", end=" ")
        if not check_registry_health():
            print("✗ FAILED")
            print(f"\nError: Registry service not available at {REGISTRY_URL}")
            print("Please start the service with: ./scripts/start_registry_service.sh\n")
            sys.exit(1)
        print("✓ OK")

        list_agents()
        return

    # Check if registry service is running
    print("\nChecking registry service...", end=" ")
    if not check_registry_health():
        print("✗ FAILED")
        print(f"\nError: Registry service not available at {REGISTRY_URL}")
        print("Please start the service with: ./scripts/start_registry_service.sh\n")
        sys.exit(1)
    print("✓ OK")

    # Execute requested action
    if args.all:
        register_all_agents()
    elif args.local:
        register_local_agents_only()
    elif args.remote:
        register_remote_agents_only()
    elif args.agent:
        register_specific_agent(args.agent)


if __name__ == "__main__":
    main()
