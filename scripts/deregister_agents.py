#!/usr/bin/env python3
"""
Agent Deregistration Helper Script

This script helps you deregister agents from the Agent Registry Service.

Usage:
    python scripts/deregister_agents.py --all                    # Deregister all agents
    python scripts/deregister_agents.py --local                  # Deregister local agents only
    python scripts/deregister_agents.py --remote                 # Deregister remote agents only
    python scripts/deregister_agents.py --agent oxygen_agent     # Deregister specific agent
    python scripts/deregister_agents.py --list                   # List registered agents
"""

import argparse
import sys
from typing import List, Optional

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
# Helper Functions
# =============================================================================

def check_registry_health() -> bool:
    """Check if registry service is running."""
    try:
        response = requests.get(f"{REGISTRY_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def list_agents() -> List[dict]:
    """Get list of all registered agents."""
    try:
        response = requests.get(f"{REGISTRY_URL}/registry/agents", timeout=DEFAULT_TIMEOUT)
        if response.status_code != 200:
            return []

        data = response.json()
        return data.get("agents", [])
    except requests.RequestException:
        return []


def deregister_agent(agent_name: str) -> bool:
    """Deregister a specific agent."""
    try:
        print(f"  Deregistering agent: {agent_name}...", end=" ")

        response = requests.delete(
            f"{REGISTRY_URL}/registry/agents/{agent_name}",
            timeout=DEFAULT_TIMEOUT
        )

        if response.status_code == 200:
            print("✓ SUCCESS")
            return True
        elif response.status_code == 404:
            print("⚠ NOT FOUND")
            return False
        else:
            print(f"✗ FAILED ({response.status_code})")
            print(f"    Error: {response.json().get('detail', 'Unknown error')}")
            return False

    except requests.RequestException as e:
        print(f"✗ FAILED")
        print(f"    Error: {e}")
        return False


def display_agents_table(agents: List[dict], title: str) -> None:
    """Display agents in a formatted table."""
    if not agents:
        print(f"\n{title}: None found\n")
        return

    print(f"\n{title}:")
    print(f"{'='*80}")

    for agent in agents:
        agent_type = agent.get("type", "local")
        status_emoji = "✓" if agent.get("enabled", True) else "✗"

        print(f"{status_emoji} {agent['name']} ({agent_type})")
        print(f"  Description: {agent.get('description', 'N/A')[:60]}...")
        print(f"  Domains: {', '.join(agent.get('capabilities', {}).get('domains', []))}")

        if agent_type == "remote":
            print(f"  Status: {agent.get('status', 'N/A')}")
            provider = agent.get('provider', {})
            if provider:
                print(f"  Provider: {provider.get('name', 'N/A')}")

        print()


# =============================================================================
# Main Functions
# =============================================================================

def deregister_all_agents() -> None:
    """Deregister all agents."""
    print("\n" + "="*80)
    print("Deregistering All Agents")
    print("="*80 + "\n")

    agents = list_agents()

    if not agents:
        print("No agents registered.\n")
        return

    # Show what will be deregistered
    local_agents = [a for a in agents if a.get("type", "local") == "local"]
    remote_agents = [a for a in agents if a.get("type", "local") == "remote"]

    display_agents_table(local_agents, "Local Agents to Deregister")
    display_agents_table(remote_agents, "Remote Agents to Deregister")

    # Confirm
    print("="*80)
    response = input(f"Are you sure you want to deregister ALL {len(agents)} agents? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("\nDeregistration cancelled.\n")
        return

    print("\nProceeding with deregistration...\n")

    # Deregister all
    success = 0
    for agent in agents:
        if deregister_agent(agent["name"]):
            success += 1

    print(f"\n{'='*80}")
    print(f"Deregistration Complete: {success}/{len(agents)} agents deregistered")
    print("="*80 + "\n")


def deregister_local_agents_only() -> None:
    """Deregister only local agents."""
    print("\n" + "="*80)
    print("Deregistering Local Agents (First-Party)")
    print("="*80 + "\n")

    agents = list_agents()
    local_agents = [a for a in agents if a.get("type", "local") == "local"]

    if not local_agents:
        print("No local agents registered.\n")
        return

    # Show what will be deregistered
    display_agents_table(local_agents, "Local Agents to Deregister")

    # Confirm
    print("="*80)
    response = input(f"Are you sure you want to deregister {len(local_agents)} local agents? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("\nDeregistration cancelled.\n")
        return

    print("\nProceeding with deregistration...\n")

    # Deregister local agents
    success = 0
    for agent in local_agents:
        if deregister_agent(agent["name"]):
            success += 1

    print(f"\n{'='*80}")
    print(f"Deregistration Complete: {success}/{len(local_agents)} local agents deregistered")
    print("="*80 + "\n")


def deregister_remote_agents_only() -> None:
    """Deregister only remote agents."""
    print("\n" + "="*80)
    print("Deregistering Remote Agents (Third-Party)")
    print("="*80 + "\n")

    agents = list_agents()
    remote_agents = [a for a in agents if a.get("type", "local") == "remote"]

    if not remote_agents:
        print("No remote agents registered.\n")
        return

    # Show what will be deregistered
    display_agents_table(remote_agents, "Remote Agents to Deregister")

    # Confirm
    print("="*80)
    response = input(f"Are you sure you want to deregister {len(remote_agents)} remote agents? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("\nDeregistration cancelled.\n")
        return

    print("\nProceeding with deregistration...\n")

    # Deregister remote agents
    success = 0
    for agent in remote_agents:
        if deregister_agent(agent["name"]):
            success += 1

    print(f"\n{'='*80}")
    print(f"Deregistration Complete: {success}/{len(remote_agents)} remote agents deregistered")
    print("="*80 + "\n")


def deregister_specific_agent(agent_name: str) -> None:
    """Deregister a specific agent by name."""
    print(f"\n{'='*80}")
    print(f"Deregistering Agent: {agent_name}")
    print("="*80 + "\n")

    # Check if agent exists
    agents = list_agents()
    agent = next((a for a in agents if a["name"] == agent_name), None)

    if not agent:
        print(f"Error: Agent '{agent_name}' not found in registry")
        print("\nRegistered agents:")
        for a in agents:
            print(f"  - {a['name']} ({a.get('type', 'local')})")
        print()
        return

    # Show agent details
    display_agents_table([agent], f"Agent to Deregister: {agent_name}")

    # Confirm
    print("="*80)
    response = input(f"Are you sure you want to deregister '{agent_name}'? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("\nDeregistration cancelled.\n")
        return

    print("\nProceeding with deregistration...\n")

    success = deregister_agent(agent_name)

    print(f"\n{'='*80}")
    print(f"Deregistration {'Successful' if success else 'Failed'}")
    print("="*80 + "\n")


def list_registered_agents() -> None:
    """List all registered agents."""
    agents = list_agents()

    if not agents:
        print("\nNo agents registered yet.\n")
        return

    print(f"\n{'='*80}")
    print(f"Registered Agents ({len(agents)} total)")
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


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Deregister agents from the Agent Registry Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all                    Deregister all agents
  %(prog)s --local                  Deregister local agents only
  %(prog)s --remote                 Deregister remote agents only
  %(prog)s --agent oxygen_agent     Deregister specific agent
  %(prog)s --list                   List registered agents
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Deregister all agents")
    group.add_argument("--local", action="store_true", help="Deregister local agents only")
    group.add_argument("--remote", action="store_true", help="Deregister remote agents only")
    group.add_argument("--agent", type=str, metavar="NAME", help="Deregister specific agent")
    group.add_argument("--list", action="store_true", help="List registered agents")

    parser.add_argument(
        "--registry-url",
        type=str,
        default=DEFAULT_REGISTRY_URL,
        help=f"Registry service URL (default: {DEFAULT_REGISTRY_URL})"
    )

    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts"
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

        list_registered_agents()
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
        deregister_all_agents()
    elif args.local:
        deregister_local_agents_only()
    elif args.remote:
        deregister_remote_agents_only()
    elif args.agent:
        deregister_specific_agent(args.agent)


if __name__ == "__main__":
    main()
