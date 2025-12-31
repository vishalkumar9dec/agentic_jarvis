#!/usr/bin/env python3
"""
Integration Test for Registry Service + Jarvis Orchestrator

Tests the complete integration:
1. Registry service is running
2. Agents are registered correctly
3. Jarvis can fetch agents from registry
4. Router can create local and remote agents
5. Sessions are tracked properly

Usage:
    python scripts/test_registry_integration.py

Prerequisites:
    1. Registry service running on port 8003
    2. Oxygen A2A agent running on port 8002 (optional, for remote agent test)
    3. Agents registered via migrate_to_registry_service.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, try to load .env manually
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

from jarvis_agent.registry_client import RegistryClient
from jarvis_agent.session_client import SessionClient
from jarvis_agent.dynamic_router_with_registry import TwoStageRouterWithRegistry


def test_registry_connection():
    """Test 1: Registry service connection"""
    print("\n" + "="*80)
    print("Test 1: Registry Service Connection")
    print("="*80)

    client = RegistryClient(base_url="http://localhost:8003")

    print("\nChecking registry service health...", end=" ")
    if not client.health_check():
        print("✗ FAILED")
        print("ERROR: Registry service not available")
        print("Start with: ./scripts/start_registry_service.sh")
        return False

    print("✓ OK")
    return True


def test_agent_listing():
    """Test 2: List registered agents"""
    print("\n" + "="*80)
    print("Test 2: List Registered Agents")
    print("="*80)

    client = RegistryClient(base_url="http://localhost:8003")

    print("\nFetching registered agents...", end=" ")
    try:
        agents = client.list_agents(enabled_only=True)
        print(f"✓ OK ({len(agents)} agents)")

        if len(agents) == 0:
            print("\n⚠ WARNING: No agents registered")
            print("Run migration script: python scripts/migrate_to_registry_service.py")
            return False

        print("\nRegistered Agents:")
        print("-" * 80)
        for agent in agents:
            print(f"\n✓ {agent.name}")
            print(f"  Type: {agent.type}")
            print(f"  Description: {agent.description}")
            print(f"  Domains: {', '.join(agent.capabilities.get('domains', []))}")

            if agent.type == "local":
                print(f"  Factory: {agent.factory_module}.{agent.factory_function}")
            else:
                print(f"  Agent Card: {agent.agent_card_url}")
                print(f"  Status: {agent.status}")

        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_agent_creation():
    """Test 3: Dynamic agent creation"""
    print("\n" + "="*80)
    print("Test 3: Dynamic Agent Creation")
    print("="*80)

    client = RegistryClient(base_url="http://localhost:8003")
    router = TwoStageRouterWithRegistry(registry_client=client)

    print("\nTesting agent creation from registry...")

    # Test local agent
    print("\n1. Creating local agent (TicketsAgent)...", end=" ")
    try:
        agent_info = client.get_agent("TicketsAgent")
        if not agent_info:
            print("✗ NOT FOUND")
            print("   TicketsAgent not registered")
            return False

        if agent_info.type != "local":
            print(f"✗ WRONG TYPE ({agent_info.type})")
            return False

        # Create agent via factory
        agent = router.factory_resolver.create_agent(
            factory_module=agent_info.factory_module,
            factory_function=agent_info.factory_function
        )

        print("✓ OK")
        print(f"   Created: {agent.name}")
        print(f"   Type: {type(agent).__name__}")

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

    # Test remote agent (if available)
    print("\n2. Creating remote agent (OxygenAgent)...", end=" ")
    try:
        agent_info = client.get_agent("OxygenAgent")
        if not agent_info:
            print("⚠ NOT FOUND")
            print("   OxygenAgent not registered (optional)")
        elif agent_info.type != "remote":
            print(f"⚠ WRONG TYPE ({agent_info.type})")
            print("   OxygenAgent should be remote")
        else:
            from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

            agent = RemoteA2aAgent(
                name=agent_info.name,
                description=agent_info.description,
                agent_card=agent_info.agent_card_url
            )

            print("✓ OK")
            print(f"   Created: {agent.name}")
            print(f"   Type: RemoteA2aAgent")
            print(f"   Agent Card: {agent_info.agent_card_url}")

    except Exception as e:
        print(f"✗ FAILED: {e}")
        print(f"   Error: {e}")
        print("   (This is OK if Oxygen agent is not running)")

    return True


def test_routing():
    """Test 4: Query routing"""
    print("\n" + "="*80)
    print("Test 4: Query Routing")
    print("="*80)

    client = RegistryClient(base_url="http://localhost:8003")
    router = TwoStageRouterWithRegistry(registry_client=client)

    test_cases = [
        {
            "query": "show my tickets",
            "expected_count": 1,
            "expected_agents": ["TicketsAgent"]
        },
        {
            "query": "what's our cloud cost",
            "expected_count": 1,
            "expected_agents": ["FinOpsAgent"]
        }
    ]

    print("\nTesting query routing...")

    all_passed = True
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        expected_count = test["expected_count"]
        expected_agents = test["expected_agents"]

        print(f"\n{i}. Query: \"{query}\"")
        print(f"   Expected: {', '.join(expected_agents)}")
        print(f"   Routing...", end=" ")

        try:
            agents = router.route(query, require_all_matches=True)

            if len(agents) != expected_count:
                print(f"✗ WRONG COUNT (got {len(agents)}, expected {expected_count})")
                all_passed = False
                continue

            agent_names = [a.name for a in agents]
            if set(agent_names) != set(expected_agents):
                print(f"✗ WRONG AGENTS")
                print(f"      Got: {', '.join(agent_names)}")
                print(f"      Expected: {', '.join(expected_agents)}")
                all_passed = False
                continue

            print("✓ OK")
            print(f"   Selected: {', '.join(agent_names)}")

            # Verify agents are actual LlmAgent instances, not tuples
            for agent in agents:
                if not hasattr(agent, 'name'):
                    print(f"✗ INVALID AGENT TYPE: {type(agent)}")
                    all_passed = False
                    break

        except Exception as e:
            print(f"✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    return all_passed


def test_session_management():
    """Test 5: Session management"""
    print("\n" + "="*80)
    print("Test 5: Session Management")
    print("="*80)

    session_client = SessionClient(base_url="http://localhost:8003")

    print("\n1. Creating session...", end=" ")
    try:
        session_id = session_client.create_session(
            user_id="test_user",
            metadata={"test": "integration_test"}
        )
        print(f"✓ OK")
        print(f"   Session ID: {session_id}")

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

    print("\n2. Adding messages...", end=" ")
    try:
        session_client.add_message(session_id, "user", "test query")
        session_client.add_message(session_id, "assistant", "test response")
        print("✓ OK")

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

    print("\n3. Tracking invocation...", end=" ")
    try:
        session_client.track_invocation(
            session_id=session_id,
            agent_name="TicketsAgent",
            query="test query",
            response="test response",
            success=True,
            duration_ms=100
        )
        print("✓ OK")

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

    print("\n4. Retrieving session...", end=" ")
    try:
        session_data = session_client.get_session(session_id)

        if not session_data:
            print("✗ NOT FOUND")
            return False

        history = session_data.get("conversation_history", [])
        invocations = session_data.get("agents_invoked", [])

        print("✓ OK")
        print(f"   Messages: {len(history)}")
        print(f"   Invocations: {len(invocations)}")

        if len(history) != 2:
            print(f"   ✗ Wrong message count (expected 2, got {len(history)})")
            return False

        if len(invocations) != 1:
            print(f"   ✗ Wrong invocation count (expected 1, got {len(invocations)})")
            return False

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

    # Cleanup
    print("\n5. Deleting test session...", end=" ")
    try:
        session_client.delete_session(session_id)
        print("✓ OK")
    except Exception as e:
        print(f"⚠ WARNING: {e}")

    return True


def main():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("Registry Service Integration Tests")
    print("="*80)

    # Check GOOGLE_API_KEY
    if not os.getenv("GOOGLE_API_KEY"):
        print("\n✗ ERROR: GOOGLE_API_KEY environment variable not set")
        print("Please set it with: export GOOGLE_API_KEY=your_api_key")
        sys.exit(1)

    tests = [
        ("Registry Connection", test_registry_connection),
        ("Agent Listing", test_agent_listing),
        ("Agent Creation", test_agent_creation),
        ("Query Routing", test_routing),
        ("Session Management", test_session_management)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print()
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status:12} {test_name}")

    print()
    print("="*80)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print("="*80)

    if passed_count == total_count:
        print("\n✓ All tests passed! Registry integration is working correctly.")
        print("\nNext step:")
        print("  python jarvis_agent/main_with_registry.py")
        print()
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please review the output above.")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
