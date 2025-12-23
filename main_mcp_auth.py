#!/usr/bin/env python3
"""
Agentic Jarvis - MCP Version CLI with Authentication
Phase 2 - Part B: WITH JWT Authentication (Task 13)

This CLI connects to the MCP-based agent architecture with authentication:
- Tickets MCP Server (port 5011)
- FinOps MCP Server (port 5012)
- Oxygen MCP Server (port 8012)
- Auth Service (port 9998)

Features:
- JWT-based authentication
- ADK Runner pattern with session service
- Bearer token passed via HTTP Authorization headers (header_provider)
- Authenticated queries (my tickets, my courses, etc.)

Authentication Flow:
1. User logs in via auth service → receives JWT bearer token
2. Token stored in session state via EventActions with state_delta
3. McpToolset's header_provider reads token from context.session.state
4. Token injected as HTTP Authorization header in MCP requests
5. FastMCP extracts token via get_http_headers()
6. Tools validate token and return user-specific data

Usage:
    python main_mcp_auth.py

Login:
    Username: vishal, alex, or sarah
    Password: password123
"""

import os
import sys
import warnings
import logging
import requests
from getpass import getpass
from dotenv import load_dotenv
from jarvis_agent.mcp_agents.agent_factory import create_root_agent
from jarvis_agent.callbacks import before_tool_callback, after_tool_callback
from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

# Load environment variables
load_dotenv()

# Suppress async cleanup warnings from MCP SSE client
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*coroutine.*was never awaited.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Suppress MCP session cleanup logger warnings
logging.getLogger("google.adk.tools.mcp_tool.mcp_session_manager").setLevel(logging.ERROR)


class StderrFilter:
    """Filter to suppress specific async cleanup errors in stderr."""

    def __init__(self, original_stderr):
        self.original_stderr = original_stderr

    def write(self, text):
        # Filter out async generator cleanup errors
        if any(keyword in text for keyword in [
            "an error occurred during closing of asynchronous generator",
            "asyncgen:",
            "ExceptionGroup: unhandled errors in a TaskGroup",
            "RuntimeError: generator didn't stop after athrow()",
            "RuntimeError: Attempted to exit cancel scope",
            "Error during disconnected session cleanup"
        ]):
            return  # Suppress these errors
        self.original_stderr.write(text)

    def flush(self):
        self.original_stderr.flush()


def login() -> tuple[str, dict] | None:
    """
    Authenticate user via auth service.

    Returns:
        Tuple of (bearer_token, user_info) if successful, None if failed
    """
    print("\n" + "=" * 70)
    print("  LOGIN")
    print("=" * 70)
    print()
    print("  Available users: vishal, alex, sarah")
    print("  Password for all: password123")
    print()

    # Get credentials
    username = input("Username: ").strip()
    password = getpass("Password: ")

    # Call auth service
    try:
        response = requests.post(
            "http://localhost:9998/auth/login",
            json={"username": username, "password": password},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Login successful! Welcome, {data['user']['username']}!")
            print(f"  Role: {data['user']['role']}")
            print(f"  Email: {data['user']['email']}")
            return data['token'], data['user']
        else:
            print(f"\n✗ Login failed: {response.json().get('detail', 'Unknown error')}")
            return None

    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Auth service not running on port 9998")
        print("  Please start it with: ./scripts/start_auth_service.sh")
        return None
    except Exception as e:
        print(f"\n✗ Error during login: {e}")
        return None


def main():
    """Main CLI entry point for MCP version with authentication."""

    # Install stderr filter to suppress async cleanup errors
    original_stderr = sys.stderr
    sys.stderr = StderrFilter(original_stderr)

    print("=" * 70)
    print("  JARVIS - MCP Version with Authentication (Phase 2 - Part B)")
    print("  Task 13: ADK Runner Pattern + JWT Authentication")
    print("=" * 70)
    print()

    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment")
        print()
        print("Please set your Google API key:")
        print("  1. Copy .env.template to .env")
        print("  2. Add your API key to .env: GOOGLE_API_KEY=your_key_here")
        print("  3. Get API key from: https://makersuite.google.com/app/apikey")
        print()
        return 1

    # Login
    auth_result = login()
    if not auth_result:
        print("\n❌ Authentication required. Exiting.")
        return 1

    bearer_token, user_info = auth_result

    print()
    print("=" * 70)
    print("  JARVIS SESSION")
    print("=" * 70)
    print()
    print("  Connected to MCP servers:")
    print("    - Tickets MCP: http://localhost:5011/mcp")
    print("    - FinOps MCP: http://localhost:5012/mcp")
    print("    - Oxygen MCP: http://localhost:8012/mcp")
    print()
    print("  Authenticated as:", user_info['username'])
    print()
    print("  Example queries:")
    print("    PUBLIC (no auth):")
    print("      - 'show all tickets'")
    print("      - 'what is the AWS cost?'")
    print("      - 'show courses for alex'")
    print()
    print("    AUTHENTICATED (use 'my'):")
    print("      - 'show my tickets'")
    print("      - 'create a ticket for vpn access'")
    print("      - 'show my courses'")
    print("      - 'show my pending exams'")
    print()
    print("  Type 'exit' or 'quit' to end session")
    print("-" * 70)
    print()

    # Create MCP-based root agent
    print("Initializing Jarvis MCP agent...", end="", flush=True)
    try:
        root_agent = create_root_agent()
        print(" ✓")
    except Exception as e:
        print(f" ✗\n\n❌ Error: Failed to create agent: {e}")
        print("\nMake sure all MCP servers are running:")
        print("  ./scripts/start_tickets_mcp_server.sh")
        print("  ./scripts/start_finops_mcp_server.sh")
        print("  ./scripts/start_oxygen_mcp_server.sh")
        return 1

    # Create session service
    session_service = InMemorySessionService()
    session_id = f"mcp-cli-{user_info['username']}"
    user_id = user_info['user_id']

    # Create session service and initialize session
    print("Creating session...", end="", flush=True)
    session_service.create_session_sync(
        app_name="jarvis_mcp_auth",
        user_id=user_id,
        session_id=session_id
    )

    # Store bearer token in session state using event state_delta pattern
    session = session_service.get_session_sync(
        app_name="jarvis_mcp_auth",
        user_id=user_id,
        session_id=session_id
    )

    # Create an event with state_delta to update session state
    # This is the correct ADK pattern for modifying session state
    from google.adk.events import Event, EventActions
    from google.genai import types as genai_types

    state_update_event = Event(
        content=genai_types.Content(
            role="user",
            parts=[genai_types.Part(text="[Auth] Session initialized")]
        ),
        author="system",
        actions=EventActions(
            state_delta={
                # No prefix = session state (accessible via context.session.state)
                "bearer_token": bearer_token,
                "username": user_info['username'],
                "role": user_info['role'],
                "user_id": user_info['user_id']
            }
        )
    )

    # Append event to update session state (must use async)
    import asyncio
    asyncio.run(session_service.append_event(session, state_update_event))
    print(" ✓")

    # Create ADK Runner
    print("Creating ADK Runner...", end="", flush=True)
    runner = Runner(
        app_name="jarvis_mcp_auth",
        agent=root_agent,
        session_service=session_service
    )
    print(" ✓")

    print("\nReady! Ask me anything about tickets, costs, or learning.\n")

    # Interactive loop
    while True:
        try:
            user_input = input(f"{user_info['username']}> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break

            # Create message
            new_message = types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            )

            # Run agent via Runner
            print()
            try:
                # Token already stored in session state via EventActions
                # header_provider reads it from context.session.state automatically

                # Use Runner's run method
                for event in runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=new_message
                ):
                    if event.content and event.content.parts and event.author != "user":
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                print(part.text, end='', flush=True)
            except Exception as e:
                # Filter out MCP SSE cleanup errors (they're harmless)
                error_msg = str(e)
                if "generator" not in error_msg.lower() and "cancel scope" not in error_msg.lower():
                    print(f"❌ Error processing request: {e}")

            print()  # Newline after response

            # Small delay to allow async cleanup to complete
            import time
            time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
