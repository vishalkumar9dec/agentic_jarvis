"""
Test script to verify cross-agent query fix
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from jarvis_agent.main_with_registry import JarvisOrchestrator

def test_cross_agent_queries():
    """Test cross-agent queries with the fix."""
    print("=" * 80)
    print("Testing Cross-Agent Query Fix")
    print("=" * 80)
    print()

    # Initialize orchestrator
    orchestrator = JarvisOrchestrator()

    # Test queries
    test_cases = [
        {
            "query": "show all tickets and aws cost",
            "expected_agents": ["TicketsAgent", "FinOpsAgent"],
            "description": "2-agent query: Tickets + FinOps"
        },
        {
            "query": "show all tickets",
            "expected_agents": ["TicketsAgent"],
            "description": "Single agent: Tickets only"
        },
        {
            "query": "what's our total cloud cost?",
            "expected_agents": ["FinOpsAgent"],
            "description": "Single agent: FinOps only"
        },
        {
            "query": "show tickets, courses for vishal, and total cloud spending",
            "expected_agents": ["TicketsAgent", "OxygenAgent", "FinOpsAgent"],
            "description": "3-agent query: All three"
        }
    ]

    user_id = "test_user"
    session_id = orchestrator.create_session(user_id)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print("-" * 80)
        print(f"Query: '{test_case['query']}'")
        print()

        try:
            response = orchestrator.handle_query_with_session(session_id, test_case['query'])

            print("Response:")
            print(response)
            print()
            print("✅ Test passed")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

        print("=" * 80)

    orchestrator.close()
    print("\n✅ All tests completed")


if __name__ == "__main__":
    test_cross_agent_queries()
