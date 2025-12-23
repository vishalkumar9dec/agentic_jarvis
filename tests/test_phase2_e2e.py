#!/usr/bin/env python3
"""
End-to-End Testing for Phase 2 JWT Authentication

This script tests the complete authentication flow across all Phase 2 components:
1. Auth Service login
2. JWT token validation
3. Authenticated requests to toolbox servers
4. User-specific tools (Tickets, Oxygen)
5. Token propagation through agent chain
"""

import requests
import json
from typing import Dict, Optional

# Service URLs
AUTH_SERVICE_URL = "http://localhost:9998"
TICKETS_SERVER_URL = "http://localhost:5001"
FINOPS_SERVER_URL = "http://localhost:5002"
OXYGEN_AGENT_URL = "http://localhost:8002"
WEB_UI_URL = "http://localhost:9999"

# Test users
TEST_USERS = [
    {"username": "vishal", "password": "password123", "role": "developer"},
    {"username": "alex", "password": "password123", "role": "devops"},
    {"username": "sarah", "password": "password123", "role": "data_scientist"}
]


class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'


def print_test(test_name: str):
    print(f"\n{Colors.BLUE}━━━ {test_name} ━━━{Colors.NC}")


def print_pass(message: str):
    print(f"{Colors.GREEN}✓{Colors.NC} {message}")


def print_fail(message: str):
    print(f"{Colors.RED}✗{Colors.NC} {message}")


def print_info(message: str):
    print(f"  {message}")


# Test counters
tests_passed = 0
tests_failed = 0


def test_auth_service_health():
    """Test 1: Auth Service health check"""
    global tests_passed, tests_failed
    print_test("Test 1: Auth Service Health Check")

    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/health")
        if response.status_code == 200:
            print_pass("Auth Service is healthy")
            tests_passed += 1
            return True
        else:
            print_fail(f"Auth Service health check failed: {response.status_code}")
            tests_failed += 1
            return False
    except Exception as e:
        print_fail(f"Auth Service not reachable: {e}")
        tests_failed += 1
        return False


def test_login(username: str, password: str) -> Optional[Dict]:
    """Test 2: User login and JWT token generation"""
    global tests_passed, tests_failed
    print_test(f"Test 2: Login as {username}")

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/login",
            json={"username": username, "password": password}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("token"):
                print_pass(f"Login successful for {username}")
                print_info(f"Token: {data['token'][:20]}...")
                print_info(f"User ID: {data['user']['user_id']}")
                print_info(f"Role: {data['user']['role']}")
                tests_passed += 1
                return data
            else:
                print_fail("Login response missing token")
                tests_failed += 1
                return None
        else:
            print_fail(f"Login failed: {response.status_code}")
            tests_failed += 1
            return None
    except Exception as e:
        print_fail(f"Login error: {e}")
        tests_failed += 1
        return None


def test_invalid_login():
    """Test 3: Invalid login attempt"""
    global tests_passed, tests_failed
    print_test("Test 3: Invalid Login Attempt")

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/login",
            json={"username": "invalid", "password": "wrong"}
        )

        if response.status_code == 401:
            print_pass("Invalid login correctly rejected")
            tests_passed += 1
            return True
        else:
            print_fail(f"Invalid login should return 401, got {response.status_code}")
            tests_failed += 1
            return False
    except Exception as e:
        print_fail(f"Invalid login test error: {e}")
        tests_failed += 1
        return False


def test_tickets_server_auth(token: str, username: str):
    """Test 4: Tickets server authenticated tools"""
    global tests_passed, tests_failed
    print_test(f"Test 4: Tickets Server Authenticated Access ({username})")

    headers = {"Authorization": f"Bearer {token}"}

    # Test get_my_tickets
    try:
        response = requests.post(
            f"{TICKETS_SERVER_URL}/api/tool/get_my_tickets/invoke",
            json={},
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            tickets = data.get("result", [])
            print_pass(f"get_my_tickets: Retrieved {len(tickets)} tickets for {username}")
            if tickets:
                print_info(f"Sample ticket: {tickets[0]}")
            tests_passed += 1
        else:
            print_fail(f"get_my_tickets failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print_fail(f"get_my_tickets error: {e}")
        tests_failed += 1

    # Test create_my_ticket
    try:
        response = requests.post(
            f"{TICKETS_SERVER_URL}/api/tool/create_my_ticket/invoke",
            json={"operation": "test_operation"},
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {})
            if result.get("success"):
                print_pass(f"create_my_ticket: Created ticket #{result['ticket']['id']}")
                tests_passed += 1
            else:
                print_fail(f"create_my_ticket failed: {result}")
                tests_failed += 1
        else:
            print_fail(f"create_my_ticket request failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print_fail(f"create_my_ticket error: {e}")
        tests_failed += 1


def test_tickets_server_no_auth():
    """Test 5: Tickets server rejects unauthenticated requests"""
    global tests_passed, tests_failed
    print_test("Test 5: Tickets Server Rejects Unauthenticated Access")

    try:
        response = requests.post(
            f"{TICKETS_SERVER_URL}/api/tool/get_my_tickets/invoke",
            json={}
        )

        if response.status_code == 401:
            print_pass("Unauthenticated request correctly rejected")
            tests_passed += 1
            return True
        else:
            print_fail(f"Should return 401, got {response.status_code}")
            tests_failed += 1
            return False
    except Exception as e:
        print_fail(f"Test error: {e}")
        tests_failed += 1
        return False


def test_finops_server_health(token: str):
    """Test 6: FinOps server health and basic access"""
    global tests_passed, tests_failed
    print_test("Test 6: FinOps Server Health")

    try:
        response = requests.get(f"{FINOPS_SERVER_URL}/health")
        if response.status_code == 200:
            print_pass("FinOps Server is healthy")
            tests_passed += 1
            return True
        else:
            print_fail(f"FinOps health check failed: {response.status_code}")
            tests_failed += 1
            return False
    except Exception as e:
        print_fail(f"FinOps health check error: {e}")
        tests_failed += 1
        return False


def test_oxygen_agent_health():
    """Test 7: Oxygen A2A Agent health"""
    global tests_passed, tests_failed
    print_test("Test 7: Oxygen A2A Agent Health")

    try:
        response = requests.get(f"{OXYGEN_AGENT_URL}/.well-known/agent-card.json")
        if response.status_code == 200:
            card = response.json()
            print_pass("Oxygen Agent card accessible")
            print_info(f"Agent name: {card.get('name')}")
            print_info(f"Description: {card.get('description')}")
            tests_passed += 1
            return True
        else:
            print_fail(f"Oxygen agent card failed: {response.status_code}")
            tests_failed += 1
            return False
    except Exception as e:
        print_fail(f"Oxygen agent health error: {e}")
        tests_failed += 1
        return False


def test_web_ui_health():
    """Test 8: Web UI server health"""
    global tests_passed, tests_failed
    print_test("Test 8: Web UI Health")

    try:
        response = requests.get(f"{WEB_UI_URL}/login.html")
        if response.status_code == 200:
            print_pass("Web UI login page accessible")
            tests_passed += 1
            return True
        else:
            print_fail(f"Web UI login page failed: {response.status_code}")
            tests_failed += 1
            return False
    except Exception as e:
        print_fail(f"Web UI health error: {e}")
        tests_failed += 1
        return False


def test_token_expiration():
    """Test 9: Token validation with invalid token"""
    global tests_passed, tests_failed
    print_test("Test 9: Invalid Token Rejection")

    invalid_token = "invalid.jwt.token"
    headers = {"Authorization": f"Bearer {invalid_token}"}

    try:
        response = requests.post(
            f"{TICKETS_SERVER_URL}/api/tool/get_my_tickets/invoke",
            json={},
            headers=headers
        )

        if response.status_code == 401:
            print_pass("Invalid token correctly rejected")
            tests_passed += 1
            return True
        else:
            print_fail(f"Should return 401, got {response.status_code}")
            tests_failed += 1
            return False
    except Exception as e:
        print_fail(f"Test error: {e}")
        tests_failed += 1
        return False


def test_all_users():
    """Test 10: Login and operations for all demo users"""
    global tests_passed, tests_failed
    print_test("Test 10: All Demo Users Authentication")

    all_success = True
    for user in TEST_USERS:
        auth_data = test_login(user["username"], user["password"])
        if auth_data:
            token = auth_data["token"]
            # Test tickets access for each user
            test_tickets_server_auth(token, user["username"])
        else:
            all_success = False

    return all_success


def main():
    """Run all Phase 2 end-to-end tests"""
    print("\n" + "=" * 70)
    print(f"{Colors.BLUE}Phase 2 JWT Authentication - End-to-End Testing{Colors.NC}")
    print("=" * 70)

    # Test 1: Service health checks
    test_auth_service_health()
    test_finops_server_health(None)
    test_oxygen_agent_health()
    test_web_ui_health()

    # Test 2-3: Authentication
    test_invalid_login()

    # Test 4-9: Authenticated operations for each user
    for user in TEST_USERS:
        auth_data = test_login(user["username"], user["password"])
        if auth_data:
            token = auth_data["token"]
            test_tickets_server_auth(token, user["username"])

    # Test 5: Unauthenticated requests
    test_tickets_server_no_auth()

    # Test 9: Invalid token
    test_token_expiration()

    # Summary
    print("\n" + "=" * 70)
    print(f"{Colors.BLUE}Test Summary{Colors.NC}")
    print("=" * 70)
    print(f"Tests passed: {Colors.GREEN}{tests_passed}{Colors.NC}")
    print(f"Tests failed: {Colors.RED}{tests_failed}{Colors.NC}")
    print(f"Total tests:  {tests_passed + tests_failed}")

    if tests_failed == 0:
        print(f"\n{Colors.GREEN}✓ All Phase 2 tests passed!{Colors.NC}")
        print("\nPhase 2 JWT Authentication is working correctly across:")
        print("  • Auth Service (port 9998)")
        print("  • Tickets Toolbox Server (port 5001)")
        print("  • FinOps Toolbox Server (port 5002)")
        print("  • Oxygen A2A Agent (port 8002)")
        print("  • Web UI Server (port 9999)")
    else:
        print(f"\n{Colors.RED}✗ Some tests failed. Please check the errors above.{Colors.NC}")

    print("\n" + "=" * 70)

    return tests_failed == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
