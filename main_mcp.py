#!/usr/bin/env python3
"""
Agentic Jarvis - MCP Version CLI
Phase 2 - Part A: NO authentication yet (basic testing)

This CLI connects to the MCP-based agent architecture:
- Tickets MCP Server (port 5011)
- FinOps MCP Server (port 5012)
- Oxygen MCP Server (port 8012)

Usage:
    python main_mcp.py

Example queries:
    - "show all tickets"
    - "what is the AWS cost?"
    - "show courses for vishal"
    - "create a ticket for alex to get vpn access"
    - "what exams does happy have pending?"
"""

import os
import sys
import warnings
import contextlib
import io
import logging
from dotenv import load_dotenv
from jarvis_agent.mcp_agents.agent_factory import create_root_agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

# Load environment variables
load_dotenv()

# Suppress async cleanup warnings from MCP SSE client
# These are harmless warnings that occur during connection cleanup
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*coroutine.*was never awaited.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Suppress MCP session cleanup logger warnings
logging.getLogger("google.adk.tools.mcp_tool.mcp_session_manager").setLevel(logging.ERROR)


class StderrFilter:
    """Filter to suppress specific async cleanup errors in stderr."""

    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.buffer = ""

    def write(self, text):
        # Filter out async generator cleanup errors
        if any(keyword in text for keyword in [
            "an error occurred during closing of asynchronous generator",
            "asyncgen:",
            "ExceptionGroup: unhandled errors in a TaskGroup",
            "RuntimeError: generator didn't stop after athrow()",
            "RuntimeError: Attempted to exit cancel scope"
        ]):
            return  # Suppress these errors
        self.original_stderr.write(text)

    def flush(self):
        self.original_stderr.flush()


def main():
    """Main CLI entry point for MCP version (no auth in Part A)."""

    # Install stderr filter to suppress async cleanup errors
    original_stderr = sys.stderr
    sys.stderr = StderrFilter(original_stderr)

    print("=" * 70)
    print("  JARVIS - MCP Version (Phase 2 - Part A)")
    print("  NO Authentication Yet (Testing MCP Connectivity)")
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

    print("  Connected to MCP servers:")
    print("    - Tickets MCP: http://localhost:5011/mcp")
    print("    - FinOps MCP: http://localhost:5012/mcp")
    print("    - Oxygen MCP: http://localhost:8012/mcp")
    print()
    print("  Example queries:")
    print("    - 'show all tickets'")
    print("    - 'what is the AWS cost?'")
    print("    - 'show courses for vishal'")
    print("    - 'create a ticket for alex to get vpn access'")
    print("    - 'what exams does happy have pending?'")
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

    # Create session service and initialize session
    session_service = InMemorySessionService()
    session_id = "mcp-cli-session"
    user_id = "test_user"  # Hardcoded for Part A

    # Create session explicitly
    session_service.create_session_sync(
        app_name="jarvis_mcp",
        user_id=user_id,
        session_id=session_id
    )

    # Create runner
    runner = Runner(
        app_name="jarvis_mcp",
        agent=root_agent,
        session_service=session_service
    )

    print("Ready! Ask me anything about tickets, costs, or learning.\n")

    # Interactive loop
    while True:
        try:
            user_input = input("mcp> ").strip()

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

            # Run agent and print response
            print()
            try:
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
