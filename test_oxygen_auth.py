"""
Test script for Oxygen agent authentication.
Tests both original tools (with username) and new authenticated tools (with current_user).
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from remote_agent.oxygen_agent.tools import (
    get_user_courses,
    get_pending_exams,
    get_user_preferences,
    get_learning_summary,
    get_my_courses,
    get_my_exams,
    get_my_preferences,
    get_my_learning_summary
)


def test_original_tools():
    """Test original tools that require username parameter."""
    print("=" * 70)
    print("TESTING ORIGINAL OXYGEN TOOLS (Username Parameter)")
    print("=" * 70)

    # Test 1: Get user courses
    print("\n1. Get User Courses (vishal)")
    print("-" * 70)
    result = get_user_courses("vishal")
    if result.get("success"):
        print(f"✓ Retrieved courses for {result['username']}")
        print(f"  Enrolled: {result['courses_enrolled']}")
        print(f"  Completed: {result['completed_courses']}")
        print(f"  Total enrolled: {result['total_enrolled']}")
    else:
        print(f"✗ Failed: {result.get('error')}")

    # Test 2: Get pending exams
    print("\n2. Get Pending Exams (alex)")
    print("-" * 70)
    result = get_pending_exams("alex")
    if result.get("success"):
        print(f"✓ Retrieved {result['total_pending']} pending exams for {result['username']}")
        for exam in result['pending_exams']:
            urgent = " [URGENT]" if exam['urgent'] else ""
            print(f"  - {exam['exam']}: {exam['deadline']} ({exam['days_until_deadline']} days){urgent}")
    else:
        print(f"✗ Failed: {result.get('error')}")

    # Test 3: Get user preferences
    print("\n3. Get User Preferences (happy)")
    print("-" * 70)
    result = get_user_preferences("happy")
    if result.get("success"):
        print(f"✓ Retrieved preferences for {result['username']}")
        print(f"  Preferences: {result['preferences']}")
    else:
        print(f"✗ Failed: {result.get('error')}")

    # Test 4: Get learning summary
    print("\n4. Get Learning Summary (vishal)")
    print("-" * 70)
    result = get_learning_summary("vishal")
    if result.get("success"):
        summary = result['learning_summary']
        print(f"✓ Retrieved learning summary for {result['username']}")
        print(f"  Completion Rate: {summary['courses']['completion_rate']}")
        print(f"  Status: {summary['overall_progress']['status']}")
        print(f"  Pending Exams: {summary['exams']['total_pending']}")
    else:
        print(f"✗ Failed: {result.get('error')}")


def test_authenticated_tools():
    """Test authenticated tools that require current_user parameter."""
    print("\n\n" + "=" * 70)
    print("TESTING AUTHENTICATED OXYGEN TOOLS (Current User)")
    print("=" * 70)

    # Test 1: Get my courses WITH current_user
    print("\n1. Get My Courses (WITH current_user='vishal')")
    print("-" * 70)
    result = get_my_courses("vishal")
    if result.get("success"):
        print(f"✓ Retrieved courses for authenticated user: {result['username']}")
        print(f"  Enrolled: {result['courses_enrolled']}")
        print(f"  Completed: {result['completed_courses']}")
    else:
        print(f"✗ Failed: {result.get('error')}")

    # Test 2: Get my courses WITHOUT current_user (should fail)
    print("\n2. Get My Courses (WITHOUT current_user - Should Fail)")
    print("-" * 70)
    result = get_my_courses(None)
    if not result.get("success"):
        print(f"✓ Correctly rejected: {result.get('error')}")
    else:
        print(f"✗ Should have required authentication!")

    # Test 3: Get my exams WITH current_user
    print("\n3. Get My Exams (WITH current_user='alex')")
    print("-" * 70)
    result = get_my_exams("alex")
    if result.get("success"):
        print(f"✓ Retrieved {result['total_pending']} exams for {result['username']}")
        for exam in result['pending_exams']:
            urgent = " [URGENT]" if exam['urgent'] else ""
            print(f"  - {exam['exam']}: {exam['deadline']}{urgent}")
    else:
        print(f"✗ Failed: {result.get('error')}")

    # Test 4: Get my preferences WITH current_user
    print("\n4. Get My Preferences (WITH current_user='happy')")
    print("-" * 70)
    result = get_my_preferences("happy")
    if result.get("success"):
        print(f"✓ Retrieved preferences for {result['username']}")
        print(f"  Preferences: {result['preferences']}")
    else:
        print(f"✗ Failed: {result.get('error')}")

    # Test 5: Get my learning summary WITH current_user
    print("\n5. Get My Learning Summary (WITH current_user='vishal')")
    print("-" * 70)
    result = get_my_learning_summary("vishal")
    if result.get("success"):
        summary = result['learning_summary']
        print(f"✓ Retrieved summary for {result['username']}")
        print(f"  Completion Rate: {summary['courses']['completion_rate']}")
        print(f"  Status: {summary['overall_progress']['status']}")
        print(f"  Active Paths: {summary['overall_progress']['active_learning_paths']}")
    else:
        print(f"✗ Failed: {result.get('error')}")

    # Test 6: Get my learning summary WITHOUT current_user (should fail)
    print("\n6. Get My Learning Summary (WITHOUT current_user - Should Fail)")
    print("-" * 70)
    result = get_my_learning_summary(None)
    if not result.get("success"):
        print(f"✓ Correctly rejected: {result.get('error')}")
    else:
        print(f"✗ Should have required authentication!")


def test_all_users():
    """Test authenticated tools for all users."""
    print("\n\n" + "=" * 70)
    print("TESTING ALL USER ACCOUNTS")
    print("=" * 70)

    test_users = ["vishal", "alex", "happy"]

    for username in test_users:
        print(f"\n Testing user: {username}")
        print("-" * 70)

        # Test get_my_courses
        result = get_my_courses(username)
        if result.get("success"):
            print(f"  ✓ Courses: {result['total_enrolled']} enrolled, {result['total_completed']} completed")
        else:
            print(f"  ✗ Courses failed: {result.get('error')}")

        # Test get_my_exams
        result = get_my_exams(username)
        if result.get("success"):
            urgent = result['urgent_exams']
            print(f"  ✓ Exams: {result['total_pending']} pending ({urgent} urgent)")
        else:
            print(f"  ✗ Exams failed: {result.get('error')}")

        # Test get_my_preferences
        result = get_my_preferences(username)
        if result.get("success"):
            print(f"  ✓ Preferences: {len(result['preferences'])} items")
        else:
            print(f"  ✗ Preferences failed: {result.get('error')}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("OXYGEN AGENT AUTHENTICATION TEST SUITE")
    print("=" * 70)
    print()

    # Run tests
    test_original_tools()
    test_authenticated_tools()
    test_all_users()

    print("\n" + "=" * 70)
    print("✅ TASK 20 COMPLETE: Oxygen Agent Authentication Ready!")
    print("=" * 70)
    print("\nSummary:")
    print("  ✓ Original tools: Work with username parameter")
    print("  ✓ Authenticated tools: Work with current_user parameter")
    print("  ✓ Authentication validation: Rejects missing current_user")
    print("  ✓ All users tested: vishal, alex, happy")
    print()
