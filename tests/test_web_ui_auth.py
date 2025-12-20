#!/usr/bin/env python3
"""
Test Web UI authentication flow with bearer token
"""

import requests
import json

# Service URLs
AUTH_SERVICE_URL = "http://localhost:9998"
WEB_UI_URL = "http://localhost:9999"

def test_web_ui_auth_flow():
    """Test the complete web UI authentication flow"""

    print("\n" + "=" * 70)
    print("Testing Web UI Authentication Flow")
    print("=" * 70)

    # Step 1: Login
    print("\n1. Logging in as vishal...")
    login_response = requests.post(
        f"{AUTH_SERVICE_URL}/auth/login",
        json={"username": "vishal", "password": "password123"}
    )

    if login_response.status_code != 200:
        print(f"✗ Login failed: {login_response.status_code}")
        return False

    login_data = login_response.json()
    token = login_data.get("token")
    user = login_data.get("user")

    print(f"✓ Login successful")
    print(f"  Username: {user['username']}")
    print(f"  User ID: {user['user_id']}")
    print(f"  Token: {token[:30]}...")

    # Step 2: Send chat message with bearer token
    print("\n2. Sending chat request: 'show my tickets'...")

    chat_response = requests.post(
        f"{WEB_UI_URL}/api/chat",
        json={
            "message": "show my tickets",
            "session_id": f"test-session-{user['user_id']}",
            "user_id": user['user_id']
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )

    if chat_response.status_code != 200:
        print(f"✗ Chat request failed: {chat_response.status_code}")
        print(f"  Response: {chat_response.text}")
        return False

    chat_data = chat_response.json()
    response_text = chat_data.get("response", "")

    print(f"✓ Chat request successful")
    print(f"\nAgent Response:")
    print("-" * 70)
    print(response_text)
    print("-" * 70)

    # Check if we got a valid response (not an error)
    if "error" in response_text.lower() or "permission" in response_text.lower():
        print("\n✗ Response contains error or permission issue")
        return False

    print("\n✓ Web UI authentication flow working correctly!")
    return True

if __name__ == "__main__":
    import sys
    success = test_web_ui_auth_flow()
    sys.exit(0 if success else 1)
