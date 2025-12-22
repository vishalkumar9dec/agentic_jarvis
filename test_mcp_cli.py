#!/usr/bin/env python3
"""
Test script for MCP CLI
Runs sample queries to test the MCP agent system
"""

import os
from dotenv import load_dotenv
from jarvis_agent.mcp_agents.agent_factory import create_root_agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

# Load environment variables
load_dotenv()

# Sample test queries
TEST_QUERIES = [
    ("Show all tickets", "Testing Tickets agent"),
    ("What is the AWS cost?", "Testing FinOps agent"),
    ("Show courses for vishal", "Testing Oxygen agent"),
]


def test_mcp_cli():
    """Test the MCP CLI with sample queries."""

    print("=" * 70)
    print("  MCP CLI TEST SCRIPT")
    print("=" * 70)
    print()

    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found")
        return 1

    print("Initializing Jarvis MCP agent...")
    try:
        root_agent = create_root_agent()
        print("✓ Agent created successfully")
    except Exception as e:
        print(f"✗ Failed to create agent: {e}")
        return 1

    # Create session service
    session_service = InMemorySessionService()
    user_id = "test_user"

    # Create runner
    runner = Runner(
        app_name="jarvis_mcp_test",
        agent=root_agent,
        session_service=session_service
    )

    print()
    print("-" * 70)
    print()

    # Run test queries (use unique session ID per query to avoid threading issues)
    for i, (query, description) in enumerate(TEST_QUERIES, 1):
        session_id = f"test-session-{i}"
        print(f"Test {i}/{len(TEST_QUERIES)}: {description}")
        print(f"Query: {query}")
        print()

        try:
            # Create message
            new_message = types.Content(
                role="user",
                parts=[types.Part(text=query)]
            )

            # Run agent
            print("Response: ", end="", flush=True)
            response_text = ""
            for event in runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message
            ):
                if event.content and event.content.parts and event.author != "user":
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(part.text, end='', flush=True)
                            response_text += part.text

            print()
            print()

            # Validate response
            if response_text:
                print(f"✓ Test {i} passed - Got response ({len(response_text)} chars)")
            else:
                print(f"✗ Test {i} failed - No response received")

        except Exception as e:
            print(f"\n✗ Test {i} failed with error: {e}")

        print("-" * 70)
        print()

    print("=" * 70)
    print("  TEST COMPLETE")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(test_mcp_cli())
