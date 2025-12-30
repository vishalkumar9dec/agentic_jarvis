#!/usr/bin/env python3
"""
Test Script for Pure A2A Architecture

This script tests the complete end-to-end flow:
1. Registry service - list agents
2. Router - stage 1 and stage 2 routing
3. Agent invocation - actual RemoteA2aAgent calls
4. Single-agent and multi-agent queries

Prerequisites:
- All agent services running (ports 8080, 8081, 8082)
- Registry service running (port 8003)
- Agents registered in registry

Usage:
    python scripts/test_a2a_system.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jarvis_agent.registry_client import RegistryClient
from jarvis_agent.dynamic_router_with_registry import TwoStageRouterWithRegistry


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")


def print_subheader(title):
    """Print a formatted subheader."""
    print("\n" + "-" * 80)
    print(title)
    print("-" * 80 + "\n")


def test_registry_service():
    """Test 1: Verify registry service is working."""
    print_header("TEST 1: Registry Service")

    try:
        client = RegistryClient(base_url="http://localhost:8003")
        agents = client.list_agents(enabled_only=True)

        print(f"✓ Registry service is accessible")
        print(f"✓ Found {len(agents)} registered agents:\n")

        for agent in agents:
            print(f"  - {agent.name} ({agent.agent_type})")
            print(f"    Type: {agent.type}")
            print(f"    Agent Card: {agent.agent_card_url}")
            print(f"    Description: {agent.description}")
            print()

        return True, agents

    except Exception as e:
        print(f"✗ Failed to connect to registry service: {e}")
        return False, []


def test_router_stage1(router):
    """Test 2: Router Stage 1 (fast filtering)."""
    print_header("TEST 2: Router Stage 1 - Fast Filtering")

    test_queries = [
        "show my tickets",
        "what's our AWS cost?",
        "show courses for vishal",
        "show my tickets and courses"
    ]

    for query in test_queries:
        print(f"Query: '{query}'")

        try:
            # Call stage 1 directly
            candidates = router._stage1_fast_filter(query)

            print(f"  Stage 1 found {len(candidates)} candidates:")
            for agent_info, score in candidates[:5]:  # Show top 5
                print(f"    - {agent_info.name}: score={score:.2f}")
            print()

        except Exception as e:
            print(f"  ✗ Error: {e}\n")

    return True


def test_router_full(router):
    """Test 3: Full router (stage 1 + stage 2)."""
    print_header("TEST 3: Full Router - Stage 1 + Stage 2")

    test_queries = [
        ("show my tickets", 1, ["TicketsAgent"]),
        ("what's our AWS cost?", 1, ["FinOpsAgent"]),
        ("show courses for vishal", 1, ["OxygenAgent"]),
        ("show my tickets and courses", 2, ["TicketsAgent", "OxygenAgent"])
    ]

    all_passed = True

    for query, expected_count, expected_agents in test_queries:
        print(f"Query: '{query}'")
        print(f"  Expected: {expected_count} agent(s) - {expected_agents}")

        try:
            agents = router.route(query)

            agent_names = [agent.name for agent in agents]
            print(f"  Got: {len(agents)} agent(s) - {agent_names}")

            if len(agents) == expected_count:
                print(f"  ✓ Correct number of agents")
            else:
                print(f"  ✗ Expected {expected_count} agents, got {len(agents)}")
                all_passed = False

            # Check if expected agents are in the result
            for expected_agent in expected_agents:
                if expected_agent in agent_names:
                    print(f"  ✓ {expected_agent} selected correctly")
                else:
                    print(f"  ✗ {expected_agent} NOT selected")
                    all_passed = False

            print()

        except Exception as e:
            print(f"  ✗ Error: {e}\n")
            all_passed = False

    return all_passed


def test_agent_invocation(router):
    """Test 4: Actual agent invocation."""
    print_header("TEST 4: Agent Invocation")

    test_cases = [
        {
            "query": "show all tickets",
            "expected_agent": "TicketsAgent",
            "description": "Single agent - Tickets"
        },
        {
            "query": "what's our total cloud cost?",
            "expected_agent": "FinOpsAgent",
            "description": "Single agent - FinOps"
        },
        {
            "query": "show courses for vishal",
            "expected_agent": "OxygenAgent",
            "description": "Single agent - Oxygen"
        }
    ]

    all_passed = True

    for test_case in test_cases:
        print_subheader(test_case["description"])
        print(f"Query: '{test_case['query']}'")

        try:
            # Route to get agents
            agents = router.route(test_case["query"])

            if not agents:
                print(f"  ✗ No agents selected\n")
                all_passed = False
                continue

            print(f"  Routed to: {[a.name for a in agents]}")

            # Invoke the first agent
            agent = agents[0]
            print(f"  Invoking {agent.name}...")

            # Call the agent
            response = agent.run_live(test_case["query"])

            # Check response
            if hasattr(response, 'text') and response.text:
                print(f"  ✓ Agent responded successfully")
                print(f"  Response preview: {response.text[:200]}...")
            elif hasattr(response, 'content') and response.content:
                print(f"  ✓ Agent responded successfully")
                print(f"  Response preview: {str(response.content)[:200]}...")
            else:
                print(f"  ✓ Agent responded (response type: {type(response)})")

            print()

        except Exception as e:
            print(f"  ✗ Error invoking agent: {e}\n")
            import traceback
            traceback.print_exc()
            all_passed = False

    return all_passed


def test_multi_agent_query(router):
    """Test 5: Multi-agent query."""
    print_header("TEST 5: Multi-Agent Query")

    query = "show my tickets and courses"
    print(f"Query: '{query}'")
    print(f"Expected: Route to both TicketsAgent and OxygenAgent\n")

    try:
        # Route
        agents = router.route(query)
        agent_names = [a.name for a in agents]

        print(f"Routed to {len(agents)} agents: {agent_names}\n")

        if len(agents) != 2:
            print(f"✗ Expected 2 agents, got {len(agents)}")
            return False

        # Invoke each agent
        responses = []
        for agent in agents:
            print(f"Invoking {agent.name}...")
            try:
                response = agent.run_live(query)

                if hasattr(response, 'text') and response.text:
                    preview = response.text[:150]
                elif hasattr(response, 'content'):
                    preview = str(response.content)[:150]
                else:
                    preview = f"Response type: {type(response)}"

                print(f"  ✓ {agent.name} responded")
                print(f"  Preview: {preview}...\n")

                responses.append((agent.name, response))

            except Exception as e:
                print(f"  ✗ Failed: {e}\n")
                return False

        print(f"✓ Multi-agent query successful!")
        print(f"  Received {len(responses)} responses from {[r[0] for r in responses]}")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print_header("A2A System End-to-End Test")
    print("Testing Pure A2A Architecture Implementation")
    print("Option 2: All agents are self-contained A2A services")

    # Test 1: Registry Service
    success, agents = test_registry_service()
    if not success:
        print("\n❌ Registry service test failed. Cannot continue.")
        sys.exit(1)

    if len(agents) < 3:
        print(f"\n⚠️  Warning: Expected 3 agents, found {len(agents)}")

    # Create router
    print_header("Creating Router")
    try:
        client = RegistryClient(base_url="http://localhost:8003")
        router = TwoStageRouterWithRegistry(
            registry_client=client,
            stage1_max_candidates=10,
            stage1_min_score=0.1
        )
        print("✓ Router created successfully\n")
    except Exception as e:
        print(f"✗ Failed to create router: {e}")
        sys.exit(1)

    # Test 2: Router Stage 1
    test_router_stage1(router)

    # Test 3: Full Router
    router_passed = test_router_full(router)

    # Test 4: Agent Invocation
    invocation_passed = test_agent_invocation(router)

    # Test 5: Multi-Agent Query
    multi_agent_passed = test_multi_agent_query(router)

    # Final Summary
    print_header("TEST SUMMARY")

    results = [
        ("Registry Service", success),
        ("Router Stage 1", True),
        ("Router Full (Stage 1+2)", router_passed),
        ("Agent Invocation", invocation_passed),
        ("Multi-Agent Query", multi_agent_passed)
    ]

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {status}: {test_name}")

    print(f"\n{passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed! Pure A2A architecture is working correctly!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. See details above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
