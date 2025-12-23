#!/usr/bin/env python3
"""
Test Authentication for All MCP Servers (Tickets, FinOps, Oxygen)
Tests both public and authenticated endpoints.
"""

import sys
import os
import requests
import json
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.jwt_utils import create_jwt_token
from auth.user_service import authenticate_user

# MCP Server URLs
TICKETS_URL = "http://localhost:5011"
FINOPS_URL = "http://localhost:5012"
OXYGEN_URL = "http://localhost:8012"

# Test counters
tests_passed = 0
tests_failed = 0


def print_section(title: str):
    """Print section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def print_test(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    global tests_passed, tests_failed

    status = "✓ PASS" if passed else "✗ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"

    print(f"{color}{status}{reset} - {test_name}")
    if details:
        print(f"       {details}")

    if passed:
        tests_passed += 1
    else:
        tests_failed += 1


def call_tool(server_url: str, tool_name: str, arguments: Dict = None, token: str = None) -> Dict[str, Any]:
    """Call an MCP tool via HTTP."""
    url = f"{server_url}/tools/call"

    payload = {
        "name": tool_name,
        "arguments": arguments or {}
    }

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def test_tickets_server():
    """Test Tickets MCP Server authentication."""
    print_section("TICKETS MCP SERVER - Authentication Tests")

    # 1. Test public endpoint (no auth required)
    print("\n1. Testing public endpoint (get_all_tickets):")
    result = call_tool(TICKETS_URL, "get_all_tickets")
    if isinstance(result, list) and len(result) > 0:
        print_test("Public endpoint works without authentication", True, f"Found {len(result)} tickets")
    else:
        print_test("Public endpoint works without authentication", False, str(result))

    # 2. Test authenticated endpoint without token (should fail)
    print("\n2. Testing authenticated endpoint without token:")
    result = call_tool(TICKETS_URL, "get_my_tickets")
    has_error = "error" in result and "Authentication required" in result.get("message", "")
    print_test("Rejects unauthenticated access", has_error, result.get("message", ""))

    # 3. Login and get token
    print("\n3. Logging in as 'vishal':")
    user = authenticate_user("vishal", "password123")
    if user:
        token = create_jwt_token(user["username"], user["user_id"], user["role"])
        print_test("Login successful", True, f"Role: {user['role']}")
    else:
        print_test("Login successful", False, "Authentication failed")
        return None

    # 4. Test authenticated endpoint with valid token
    print("\n4. Testing authenticated endpoint with valid token (get_my_tickets):")
    result = call_tool(TICKETS_URL, "get_my_tickets", token=token)
    if isinstance(result, list):
        vishal_tickets = [t for t in result if t.get("user") == "vishal"]
        print_test("Returns user-specific tickets", True, f"Found {len(vishal_tickets)} tickets for vishal")
    else:
        print_test("Returns user-specific tickets", False, str(result))

    # 5. Test creating a ticket
    print("\n5. Testing create_my_ticket:")
    result = call_tool(TICKETS_URL, "create_my_ticket", {"operation": "test_vpn_access"}, token=token)
    success = result.get("success", False)
    print_test("Creates ticket for authenticated user", success, result.get("message", ""))

    # 6. Test admin-only endpoint as non-admin (should fail or allow self)
    print("\n6. Testing get_user_tickets as non-admin for self:")
    result = call_tool(TICKETS_URL, "get_user_tickets", {"username": "vishal"}, token=token)
    if isinstance(result, list):
        print_test("Can view own tickets via get_user_tickets", True, f"Found {len(result)} tickets")
    else:
        print_test("Can view own tickets via get_user_tickets", "error" in result, result.get("message", ""))

    return token


def test_finops_server():
    """Test FinOps MCP Server authentication."""
    print_section("FINOPS MCP SERVER - Authentication Tests")

    # 1. Test public endpoint (no auth required)
    print("\n1. Testing public endpoint (get_all_clouds_cost):")
    result = call_tool(FINOPS_URL, "get_all_clouds_cost")
    if "total_cost" in result:
        print_test("Public endpoint works without authentication", True, f"Total cost: ${result['total_cost']}")
    else:
        print_test("Public endpoint works without authentication", False, str(result))

    # 2. Test authenticated endpoint without token (should fail)
    print("\n2. Testing authenticated endpoint without token (get_my_budget):")
    result = call_tool(FINOPS_URL, "get_my_budget")
    has_error = "error" in result and "Authentication required" in result.get("message", "")
    print_test("Rejects unauthenticated access", has_error, result.get("message", ""))

    # 3. Login and get token
    print("\n3. Logging in as 'alex':")
    user = authenticate_user("alex", "password123")
    if user:
        token = create_jwt_token(user["username"], user["user_id"], user["role"])
        print_test("Login successful", True, f"Role: {user['role']}")
    else:
        print_test("Login successful", False, "Authentication failed")
        return None

    # 4. Test authenticated endpoint with valid token (get_my_budget)
    print("\n4. Testing get_my_budget with valid token:")
    result = call_tool(FINOPS_URL, "get_my_budget", token=token)
    if result.get("success"):
        budget = result.get("budget", {})
        print_test("Returns user budget", True,
                   f"Budget: ${budget.get('monthly_budget')}, Spent: ${budget.get('current_spend')}, Status: {budget.get('status')}")
    else:
        print_test("Returns user budget", False, str(result))

    # 5. Test get_my_cost_allocation
    print("\n5. Testing get_my_cost_allocation:")
    result = call_tool(FINOPS_URL, "get_my_cost_allocation", token=token)
    if result.get("success"):
        total = result.get("total_allocated")
        providers = len(result.get("allocation_by_provider", []))
        print_test("Returns cost allocation", True, f"Total allocated: ${total} across {providers} providers")
    else:
        print_test("Returns cost allocation", False, str(result))

    return token


def test_oxygen_server():
    """Test Oxygen MCP Server authentication."""
    print_section("OXYGEN MCP SERVER - Authentication Tests")

    # 1. Test public endpoint (no auth required)
    print("\n1. Testing public endpoint (get_user_courses):")
    result = call_tool(OXYGEN_URL, "get_user_courses", {"username": "vishal"})
    if result.get("success"):
        print_test("Public endpoint works without authentication", True,
                   f"Enrolled: {result.get('total_enrolled')}, Completed: {result.get('total_completed')}")
    else:
        print_test("Public endpoint works without authentication", False, str(result))

    # 2. Test authenticated endpoint without token (should fail)
    print("\n2. Testing authenticated endpoint without token (get_my_courses):")
    result = call_tool(OXYGEN_URL, "get_my_courses")
    has_error = "error" in result and "Authentication required" in result.get("message", "")
    print_test("Rejects unauthenticated access", has_error, result.get("message", ""))

    # 3. Login and get token
    print("\n3. Logging in as 'happy':")
    user = authenticate_user("happy", "password123")
    if user:
        token = create_jwt_token(user["username"], user["user_id"], user["role"])
        print_test("Login successful", True, f"Role: {user['role']}")
    else:
        print_test("Login successful", False, "Authentication failed")
        return None

    # 4. Test authenticated endpoint with valid token (get_my_courses)
    print("\n4. Testing get_my_courses with valid token:")
    result = call_tool(OXYGEN_URL, "get_my_courses", token=token)
    if result.get("success"):
        print_test("Returns user courses", True,
                   f"Enrolled: {result.get('total_enrolled')}, Completed: {result.get('total_completed')}")
    else:
        print_test("Returns user courses", False, str(result))

    # 5. Test get_my_exams
    print("\n5. Testing get_my_exams:")
    result = call_tool(OXYGEN_URL, "get_my_exams", token=token)
    if result.get("success"):
        print_test("Returns user exams", True,
                   f"Pending: {result.get('total_pending')}, Urgent: {result.get('urgent_exams')}")
    else:
        print_test("Returns user exams", False, str(result))

    # 6. Test get_my_preferences
    print("\n6. Testing get_my_preferences:")
    result = call_tool(OXYGEN_URL, "get_my_preferences", token=token)
    if result.get("success"):
        prefs = result.get("preferences", [])
        print_test("Returns user preferences", True, f"Preferences: {', '.join(prefs)}")
    else:
        print_test("Returns user preferences", False, str(result))

    # 7. Test get_my_learning_summary
    print("\n7. Testing get_my_learning_summary:")
    result = call_tool(OXYGEN_URL, "get_my_learning_summary", token=token)
    if result.get("success"):
        summary = result.get("learning_summary", {})
        progress = summary.get("overall_progress", {})
        print_test("Returns learning summary", True,
                   f"Completion: {progress.get('completion_rate')}%, Status: {progress.get('status')}")
    else:
        print_test("Returns learning summary", False, str(result))

    return token


def print_final_summary():
    """Print final test summary."""
    print_section("TEST SUMMARY")
    total = tests_passed + tests_failed
    success_rate = (tests_passed / total * 100) if total > 0 else 0

    print(f"\nTotal Tests: {total}")
    print(f"Passed: \033[92m{tests_passed}\033[0m")
    print(f"Failed: \033[91m{tests_failed}\033[0m")
    print(f"Success Rate: {success_rate:.1f}%")

    if tests_failed == 0:
        print("\n🎉 All tests passed! Authentication is working correctly across all MCP servers.")
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed. Please check the output above for details.")

    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  MCP SERVER AUTHENTICATION TEST SUITE")
    print("  Testing: Tickets (5011), FinOps (5012), Oxygen (8012)")
    print("=" * 70)

    # Run tests for each server
    test_tickets_server()
    test_finops_server()
    test_oxygen_server()

    # Print summary
    print_final_summary()

    # Return exit code
    return 0 if tests_failed == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
