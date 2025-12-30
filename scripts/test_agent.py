#!/usr/bin/env python3
"""
Test Agent Script

Test registered agents by invoking them with sample queries.

Usage:
    python scripts/test_agent.py OxygenAgent "Show me alice's courses"
    python scripts/test_agent.py --list-agents
"""

import argparse
import sys
import asyncio
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

try:
    from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
    from google.adk.runners import Runner
except ImportError:
    print("Error: Google ADK not found. Install with: pip install google-adk")
    sys.exit(1)


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_REGISTRY_URL = "http://localhost:8003"

# Global variable that can be updated
REGISTRY_URL = DEFAULT_REGISTRY_URL


# =============================================================================
# Helper Functions
# =============================================================================

def get_agent_info(agent_name: str) -> Optional[dict]:
    """Get agent information from registry."""
    try:
        response = requests.get(f"{REGISTRY_URL}/registry/agents/{agent_name}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"Error: Failed to get agent info: {e}")
        return None


def list_registered_agents() -> None:
    """List all registered agents."""
    try:
        response = requests.get(f"{REGISTRY_URL}/registry/agents", timeout=10)
        if response.status_code != 200:
            print("Error: Failed to list agents")
            return

        data = response.json()
        agents = data.get("agents", [])

        if not agents:
            print("\nNo agents registered yet.\n")
            return

        print(f"\n{'='*80}")
        print(f"Registered Agents ({len(agents)} total)")
        print(f"{'='*80}\n")

        for agent in agents:
            agent_type = agent.get("type", "local")
            print(f"✓ {agent['name']} ({agent_type})")
            print(f"  Description: {agent.get('description', 'N/A')}")
            print(f"  Domains: {', '.join(agent.get('capabilities', {}).get('domains', []))}")

            if agent_type == "remote":
                print(f"  Agent Card: {agent.get('agent_card_url', 'N/A')}")

            print()

    except requests.RequestException as e:
        print(f"Error: Failed to list agents: {e}")


async def test_remote_agent(agent_name: str, query: str) -> None:
    """Test a remote agent by invoking it with a query."""
    print(f"\n{'='*80}")
    print(f"Testing Agent: {agent_name}")
    print(f"{'='*80}\n")

    # Get agent info from registry
    print("1. Fetching agent info from registry...", end=" ")
    agent_info = get_agent_info(agent_name)

    if not agent_info:
        print("✗ FAILED")
        print(f"\nError: Agent '{agent_name}' not found in registry")
        print("Use --list-agents to see available agents\n")
        return

    print("✓ OK")

    # Verify it's a remote agent
    if agent_info.get("type") != "remote":
        print(f"\nError: Agent '{agent_name}' is a local agent, not remote.")
        print("This test script only supports remote agents (A2A protocol).\n")
        return

    # Get agent card URL
    agent_card_url = agent_info.get("agent_card_url")
    if not agent_card_url:
        print("\nError: Agent card URL not found in registry\n")
        return

    print(f"   Agent Card: {agent_card_url}")
    print(f"   Description: {agent_info.get('description', 'N/A')}")
    print()

    # Create RemoteA2aAgent instance
    print("2. Creating RemoteA2aAgent instance...", end=" ")
    try:
        remote_agent = RemoteA2aAgent(
            name=agent_info["name"],
            description=agent_info.get("description", "Remote agent"),
            agent_card=agent_card_url
        )
        print("✓ OK")
    except Exception as e:
        print("✗ FAILED")
        print(f"\nError: Failed to create RemoteA2aAgent: {e}\n")
        return

    # Invoke the agent
    print(f"\n3. Invoking agent with query...\n")
    print(f"   Query: \"{query}\"\n")
    print("   Response:\n")
    print("   " + "-"*76)

    try:
        # Create a runner and invoke the agent
        runner = Runner(remote_agent)
        response = await runner.run(query)

        # Print response
        print(f"   {response}")
        print("   " + "-"*76)
        print("\n✓ Test completed successfully!\n")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("   " + "-"*76)
        print("\n✗ Test failed\n")
        import traceback
        traceback.print_exc()


async def test_local_agent(agent_name: str, query: str) -> None:
    """Test a local agent."""
    print(f"\nError: Testing local agents is not yet implemented.")
    print("Local agents need to be tested through the Jarvis orchestrator.\n")


# =============================================================================
# Main
# =============================================================================

async def main_async(args):
    """Async main function."""
    if args.list_agents:
        list_registered_agents()
        return

    if not args.agent_name or not args.query:
        print("Error: Both agent_name and query are required")
        print("Usage: python scripts/test_agent.py AGENT_NAME \"Your query here\"")
        print("       python scripts/test_agent.py --list-agents")
        sys.exit(1)

    # Get agent info to determine type
    agent_info = get_agent_info(args.agent_name)
    if not agent_info:
        print(f"Error: Agent '{args.agent_name}' not found")
        print("Use --list-agents to see available agents")
        sys.exit(1)

    agent_type = agent_info.get("type", "local")

    if agent_type == "remote":
        await test_remote_agent(args.agent_name, args.query)
    else:
        await test_local_agent(args.agent_name, args.query)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test registered agents by invoking them with queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all registered agents
  %(prog)s --list-agents

  # Test Oxygen agent
  %(prog)s OxygenAgent "Show me alice's enrolled courses"

  # Test with different queries
  %(prog)s OxygenAgent "What exams does bob have pending?"
  %(prog)s OxygenAgent "Show learning preferences for alice"
        """
    )

    parser.add_argument(
        "agent_name",
        nargs="?",
        help="Name of the agent to test"
    )

    parser.add_argument(
        "query",
        nargs="?",
        help="Query to send to the agent"
    )

    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List all registered agents"
    )

    parser.add_argument(
        "--registry-url",
        type=str,
        default=DEFAULT_REGISTRY_URL,
        help=f"Registry service URL (default: {DEFAULT_REGISTRY_URL})"
    )

    args = parser.parse_args()

    # Update global registry URL
    global REGISTRY_URL
    REGISTRY_URL = args.registry_url

    # Run async main
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
