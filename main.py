#!/usr/bin/env python3
"""
Agentic Jarvis - CLI Interface
Interactive chat with the Jarvis root orchestrator agent.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_services():
    """Check if required services are running."""
    import subprocess
    result = subprocess.run(
        ["./scripts/check_services.sh"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def main():
    print("=" * 60)
    print("🤖 Agentic Jarvis - Your Intelligent Assistant")
    print("=" * 60)
    print("\nCapabilities:")
    print("  • IT Tickets Management (via TicketsAgent)")
    print("  • Cloud Cost Analytics (via FinOpsAgent)")
    print("  • Learning & Development (via OxygenAgent)")
    print("\nType 'exit' or 'quit' to end the session.\n")
    print("=" * 60)

    # Check if services are running
    print("\n🔍 Checking service health...")
    if not check_services():
        print("\n⚠️  Error: Some services are not running!")
        print("\nPlease start all services first:")
        print("  ./scripts/restart_all.sh")
        print("\nThen verify with:")
        print("  ./scripts/check_services.sh")
        print("")
        sys.exit(1)

    print("✅ All services are healthy!")
    print("\nInitializing Jarvis agent...")

    try:
        from jarvis_agent.agent import root_agent
        from google.adk.runners import Runner
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.genai import types

        # Create session service
        session_service = InMemorySessionService()

        # Session configuration
        app_name = "jarvis"
        user_id = "user-001"
        session_id = "cli-session-001"

        # Create a new session
        session_service.create_session_sync(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )

        # Create a runner with the session service
        runner = Runner(
            app_name=app_name,
            agent=root_agent,
            session_service=session_service,
        )

        print("✅ Jarvis agent initialized successfully!\n")
    except Exception as e:
        print(f"\n❌ Error initializing Jarvis agent: {str(e)}")
        print("\nPlease ensure:")
        print("  1. Virtual environment is activated")
        print("  2. All dependencies are installed: pip install -r requirements.txt")
        print("  3. All services are running: ./scripts/restart_all.sh")
        print("")
        sys.exit(1)

    # Interactive chat loop
    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye! Thanks for using Jarvis.\n")
                break

            # Send message to root agent using Runner
            print("\n🤖 Jarvis: ", end="", flush=True)

            try:
                # Convert user input to Content object
                new_message = types.Content(
                    role="user",
                    parts=[types.Part(text=user_input)]
                )

                # Run the agent and collect response
                response_text = ""
                for event in runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=new_message
                ):
                    # Extract text from model response events
                    if event.content and event.content.parts and event.author != "user":
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
                                print(part.text, end="", flush=True)

                if response_text:
                    print()  # New line after response
                else:
                    print("(No response)")  # Indicate no response was received

            except Exception as e:
                print(f"\n❌ Error processing request: {str(e)}")
                print("\nPossible issues:")
                print("  • One or more services may have stopped")
                print("  • Network connectivity issues")
                print("  • API key issues (check .env files)")
                print("\nRun './scripts/check_services.sh' to verify service health")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using Jarvis.\n")
            break
        except EOFError:
            print("\n\n👋 Goodbye! Thanks for using Jarvis.\n")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            print("Continuing session...\n")

if __name__ == "__main__":
    main()
