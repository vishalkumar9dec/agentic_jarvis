#!/usr/bin/env python3
"""
Agent Verification Script

Verify that agents are properly registered and accessible.

Usage:
    python scripts/verify_agent.py OxygenAgent
    python scripts/verify_agent.py --all
"""

import argparse
import sys

try:
    import requests
except ImportError:
    print("Error: requests library not found")
    sys.exit(1)


REGISTRY_URL = "http://localhost:8003"


def verify_agent(agent_name: str) -> bool:
    """Verify an agent is registered and accessible."""
    print(f"\n{'='*80}")
    print(f"Verifying Agent: {agent_name}")
    print(f"{'='*80}\n")

    success = True

    # Step 1: Check if agent is in registry
    print("1. Checking registry...", end=" ")
    try:
        response = requests.get(f"{REGISTRY_URL}/registry/agents/{agent_name}", timeout=5)
        if response.status_code == 200:
            agent_info = response.json()
            print("✓ OK")
            print(f"   Type: {agent_info.get('type', 'unknown')}")
            print(f"   Description: {agent_info.get('description', 'N/A')[:60]}...")
        else:
            print("✗ NOT FOUND")
            print(f"   Agent '{agent_name}' not registered")
            return False
    except Exception as e:
        print("✗ FAILED")
        print(f"   Error: {e}")
        return False

    # Step 2: If remote agent, check agent card
    if agent_info.get('type') == 'remote':
        agent_card_url = agent_info.get('agent_card_url')
        print(f"\n2. Checking agent card...", end=" ")
        try:
            response = requests.get(agent_card_url, timeout=5)
            if response.status_code == 200:
                card = response.json()
                print("✓ OK")
                print(f"   Agent Name: {card.get('name', 'N/A')}")
                print(f"   Protocol: {card.get('protocolVersion', 'N/A')}")
                print(f"   URL: {card.get('url', 'N/A')}")
            else:
                print("✗ UNREACHABLE")
                print(f"   Agent card URL: {agent_card_url}")
                print(f"   Status: {response.status_code}")
                success = False
        except Exception as e:
            print("✗ FAILED")
            print(f"   Error: {e}")
            print(f"   Is the agent running? Check with: lsof -i :<port>")
            success = False

    # Step 3: Check agent status
    print(f"\n3. Checking agent status...", end=" ")
    if agent_info.get('enabled', True):
        print("✓ ENABLED")
    else:
        print("⚠ DISABLED")
        print("   Enable with: curl -X PATCH http://localhost:8003/registry/agents/{agent_name}/status -d '{\"enabled\": true}'")
        success = False

    # Step 4: Check capabilities
    print(f"\n4. Checking capabilities...", end=" ")
    capabilities = agent_info.get('capabilities', {})
    domains = capabilities.get('domains', [])
    if domains:
        print("✓ OK")
        print(f"   Domains: {', '.join(domains)}")
        print(f"   Operations: {', '.join(capabilities.get('operations', []))}")
    else:
        print("⚠ NO CAPABILITIES")
        success = False

    # Summary
    print(f"\n{'='*80}")
    if success:
        print(f"✓ Agent '{agent_name}' is properly configured and accessible")
    else:
        print(f"⚠ Agent '{agent_name}' has issues (see above)")
    print(f"{'='*80}\n")

    return success


def verify_all_agents() -> None:
    """Verify all registered agents."""
    print("\nFetching all agents...", end=" ")
    try:
        response = requests.get(f"{REGISTRY_URL}/registry/agents", timeout=5)
        agents = response.json().get('agents', [])
        print(f"✓ Found {len(agents)} agents\n")

        if not agents:
            print("No agents registered.\n")
            return

        results = []
        for agent in agents:
            success = verify_agent(agent['name'])
            results.append((agent['name'], success))

        # Final summary
        print(f"\n{'='*80}")
        print("Summary")
        print(f"{'='*80}\n")

        for name, success in results:
            status = "✓ OK" if success else "⚠ Issues"
            print(f"  {status:12} {name}")

        print()

    except Exception as e:
        print("✗ FAILED")
        print(f"Error: {e}\n")


def main():
    parser = argparse.ArgumentParser(description="Verify agents are registered and accessible")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("agent_name", nargs="?", help="Name of agent to verify")
    group.add_argument("--all", action="store_true", help="Verify all agents")

    args = parser.parse_args()

    # Check registry service
    print("\nChecking registry service...", end=" ")
    try:
        response = requests.get(f"{REGISTRY_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ OK")
        else:
            print("✗ FAILED")
            sys.exit(1)
    except:
        print("✗ FAILED")
        print(f"Registry service not available at {REGISTRY_URL}")
        print("Start with: ./scripts/start_registry_service.sh\n")
        sys.exit(1)

    if args.all:
        verify_all_agents()
    else:
        if not args.agent_name:
            print("Error: agent_name required")
            sys.exit(1)
        verify_agent(args.agent_name)


if __name__ == "__main__":
    main()
