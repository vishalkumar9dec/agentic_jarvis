#!/usr/bin/env python3
"""
Agentic Jarvis - CLI Interface
Interactive chat with the Jarvis root orchestrator agent.
"""

import os
import sys
import requests
import getpass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Auth service URL
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:9998")

def check_services():
    """Check if required services are running."""
    import subprocess
    result = subprocess.run(
        ["./scripts/check_services.sh"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def login():
    """
    Authenticate user and return JWT token and user info.

    Returns:
        tuple: (token, user_info) if successful, (None, None) if failed
    """
    print("\n🔐 Please login to continue")
    print("-" * 60)

    # Check if auth service is running
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/health", timeout=2)
        if response.status_code != 200:
            print(f"❌ Auth service is not responding at {AUTH_SERVICE_URL}")
            return None, None
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to auth service at {AUTH_SERVICE_URL}")
        print("\nPlease start the auth service:")
        print("  python auth/auth_server.py")
        return None, None
    except Exception as e:
        print(f"❌ Error checking auth service: {str(e)}")
        return None, None

    # Get demo users for reference
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/auth/demo-users")
        if response.status_code == 200:
            demo_users = response.json().get("demo_users", [])
            if demo_users:
                print("\nDemo accounts available:")
                for user in demo_users:
                    print(f"  • {user['username']} / {user['password']} ({user['role']})")
                print()
    except:
        pass  # Continue even if we can't get demo users

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Get credentials
            username = input("Username: ").strip()
            if not username:
                print("❌ Username cannot be empty\n")
                continue

            password = getpass.getpass("Password: ").strip()
            if not password:
                print("❌ Password cannot be empty\n")
                continue

            # Authenticate with auth service
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/login",
                json={"username": username, "password": password},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    token = data.get("token")
                    user = data.get("user")

                    print(f"\n✅ Login successful!")
                    print(f"   Welcome, {user['username']} ({user['role']})")
                    print()

                    return token, user
                else:
                    print(f"❌ Login failed: {data.get('error', 'Unknown error')}\n")
            elif response.status_code == 401:
                print(f"❌ Invalid username or password")
                if attempt < max_attempts - 1:
                    print(f"   {max_attempts - attempt - 1} attempts remaining\n")
                else:
                    print()
            else:
                print(f"❌ Unexpected error: HTTP {response.status_code}\n")

        except requests.exceptions.Timeout:
            print("❌ Login request timed out\n")
        except Exception as e:
            print(f"❌ Error during login: {str(e)}\n")

        if attempt == max_attempts - 1:
            print(f"❌ Maximum login attempts ({max_attempts}) exceeded")
            return None, None

    return None, None

def main():
    print("=" * 60)
    print("🤖 Agentic Jarvis - Your Intelligent Assistant")
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

    # Login authentication
    token, user_info = login()

    if not token or not user_info:
        print("\n❌ Authentication failed. Exiting...")
        sys.exit(1)

    current_user = user_info["username"]

    print("=" * 60)
    print(f"Logged in as: {current_user} ({user_info['role']})")
    print("=" * 60)
    print("\nCapabilities:")
    print("  • IT Tickets Management (via TicketsAgent)")
    print("  • Cloud Cost Analytics (via FinOpsAgent)")
    print("  • Learning & Development (via OxygenAgent)")
    print("\nType 'exit' or 'quit' to end the session.\n")
    print("=" * 60)

    print("\nInitializing Jarvis agent...")

    try:
        from jarvis_agent.agent import root_agent
        from google.adk.runners import Runner
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.genai import types

        # Create session service
        session_service = InMemorySessionService()

        # Session configuration with authenticated user
        app_name = "jarvis"
        user_id = user_info["user_id"]  # Use authenticated user ID
        session_id = f"cli-session-{current_user}"  # User-specific session

        # Create a new session
        session_service.create_session_sync(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )

        # Store current_user in session state (for agent context)
        # Note: ADK sessions don't directly support custom state in this version,
        # but we can include it in the system message or context

        # Create a runner with the session service
        runner = Runner(
            app_name=app_name,
            agent=root_agent,
            session_service=session_service,
        )

        print(f"✅ Jarvis agent initialized successfully!")
        print(f"   Session ID: {session_id}")
        print(f"   User context: {current_user}")

        # Initialize conversation with user context
        # This sets the authenticated user context for the entire session
        init_message = types.Content(
            role="user",
            parts=[types.Part(text=f"[System: Authenticated user is '{current_user}'. Use user-specific tools when appropriate (get_my_tickets, get_my_courses, etc.). For this session, current_user={current_user}]")]
        )

        # Process initial context (silent - don't display response)
        for _ in runner.run(user_id=user_id, session_id=session_id, new_message=init_message):
            pass  # Consume events without displaying

        print(f"   User-specific tools enabled\n")

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
