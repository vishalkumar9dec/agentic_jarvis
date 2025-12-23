#!/bin/bash
# Test Authentication for All MCP Servers (Tickets, FinOps, Oxygen)
# Uses curl to test both public and authenticated endpoints

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

# Test users and their tokens (generated from auth/jwt_utils.py)
# For testing, we'll generate tokens on the fly using Python

echo "======================================================================="
echo "  MCP SERVER AUTHENTICATION TEST SUITE"
echo "  Testing: Tickets (5011), FinOps (5012), Oxygen (8012)"
echo "======================================================================="
echo

# Function to print test result
test_result() {
    local test_name="$1"
    local passed="$2"
    local details="$3"

    if [ "$passed" = "true" ]; then
        echo -e "${GREEN}✓ PASS${NC} - $test_name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} - $test_name"
        ((TESTS_FAILED++))
    fi

    if [ -n "$details" ]; then
        echo "       $details"
    fi
}

# Generate JWT token for a user
generate_token() {
    local username="$1"
    python3 -c "
import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from auth.jwt_utils import create_jwt_token
from auth.user_service import authenticate_user

user = authenticate_user('$username', 'password123')
if user:
    token = create_jwt_token(user['username'], user['user_id'], user['role'])
    print(token)
else:
    print('ERROR', file=sys.stderr)
    sys.exit(1)
"
}

echo "======================================================================="
echo "  TICKETS MCP SERVER - Authentication Tests"
echo "======================================================================="
echo

# Test 1: Public endpoint (no auth)
echo "1. Testing public endpoint (get_all_tickets):"
response=$(curl -s -X POST http://localhost:5011/tools/call \
    -H "Content-Type: application/json" \
    -d '{"name": "get_all_tickets", "arguments": {}}')

if echo "$response" | grep -q "\"id\""; then
    ticket_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
    test_result "Public endpoint works without authentication" "true" "Found tickets in response"
else
    test_result "Public endpoint works without authentication" "false" "Expected ticket data"
fi

# Test 2: Authenticated endpoint without token (should fail)
echo
echo "2. Testing authenticated endpoint without token (get_my_tickets):"
response=$(curl -s -X POST http://localhost:5011/tools/call \
    -H "Content-Type: application/json" \
    -d '{"name": "get_my_tickets", "arguments": {}}')

if echo "$response" | grep -q "Authentication required"; then
    test_result "Rejects unauthenticated access" "true" "Correctly requires authentication"
else
    test_result "Rejects unauthenticated access" "false" "Should require authentication"
fi

# Test 3 & 4: Get token and test authenticated endpoint
echo
echo "3. Logging in as 'vishal' and getting token..."
VISHAL_TOKEN=$(generate_token "vishal")
if [ $? -eq 0 ] && [ -n "$VISHAL_TOKEN" ]; then
    test_result "Login successful for vishal" "true" "Token generated"

    echo
    echo "4. Testing get_my_tickets with valid token:"
    response=$(curl -s -X POST http://localhost:5011/tools/call \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $VISHAL_TOKEN" \
        -d '{"name": "get_my_tickets", "arguments": {}}')

    if echo "$response" | grep -q "\"user\".*\"vishal\""; then
        test_result "Returns user-specific tickets" "true" "Found tickets for vishal"
    else
        test_result "Returns user-specific tickets" "false" "Expected vishal's tickets"
    fi

    echo
    echo "5. Testing create_my_ticket:"
    response=$(curl -s -X POST http://localhost:5011/tools/call \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $VISHAL_TOKEN" \
        -d '{"name": "create_my_ticket", "arguments": {"operation": "test_automation_access"}}')

    if echo "$response" | grep -q "\"success\".*true"; then
        test_result "Creates ticket for authenticated user" "true" "Ticket created successfully"
    else
        test_result "Creates ticket for authenticated user" "false" "Expected successful creation"
    fi
else
    test_result "Login successful for vishal" "false" "Token generation failed"
fi

echo
echo "======================================================================="
echo "  FINOPS MCP SERVER - Authentication Tests"
echo "======================================================================="
echo

# Test 1: Public endpoint (no auth)
echo "1. Testing public endpoint (get_all_clouds_cost):"
response=$(curl -s -X POST http://localhost:5012/tools/call \
    -H "Content-Type: application/json" \
    -d '{"name": "get_all_clouds_cost", "arguments": {}}')

if echo "$response" | grep -q "\"total_cost\""; then
    test_result "Public endpoint works without authentication" "true" "Got cost data"
else
    test_result "Public endpoint works without authentication" "false" "Expected cost data"
fi

# Test 2: Authenticated endpoint without token (should fail)
echo
echo "2. Testing authenticated endpoint without token (get_my_budget):"
response=$(curl -s -X POST http://localhost:5012/tools/call \
    -H "Content-Type: application/json" \
    -d '{"name": "get_my_budget", "arguments": {}}')

if echo "$response" | grep -q "Authentication required"; then
    test_result "Rejects unauthenticated access" "true" "Correctly requires authentication"
else
    test_result "Rejects unauthenticated access" "false" "Should require authentication"
fi

# Test 3 & 4: Get token and test authenticated endpoint
echo
echo "3. Logging in as 'alex' and getting token..."
ALEX_TOKEN=$(generate_token "alex")
if [ $? -eq 0 ] && [ -n "$ALEX_TOKEN" ]; then
    test_result "Login successful for alex" "true" "Token generated"

    echo
    echo "4. Testing get_my_budget with valid token:"
    response=$(curl -s -X POST http://localhost:5012/tools/call \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ALEX_TOKEN" \
        -d '{"name": "get_my_budget", "arguments": {}}')

    if echo "$response" | grep -q "\"success\".*true"; then
        budget=$(echo "$response" | grep -o "\"monthly_budget\":[0-9]*" | head -1)
        test_result "Returns user budget" "true" "Got budget data: $budget"
    else
        test_result "Returns user budget" "false" "Expected budget data"
    fi

    echo
    echo "5. Testing get_my_cost_allocation:"
    response=$(curl -s -X POST http://localhost:5012/tools/call \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ALEX_TOKEN" \
        -d '{"name": "get_my_cost_allocation", "arguments": {}}')

    if echo "$response" | grep -q "\"total_allocated\""; then
        test_result "Returns cost allocation" "true" "Got allocation data"
    else
        test_result "Returns cost allocation" "false" "Expected allocation data"
    fi
else
    test_result "Login successful for alex" "false" "Token generation failed"
fi

echo
echo "======================================================================="
echo "  OXYGEN MCP SERVER - Authentication Tests"
echo "======================================================================="
echo

# Test 1: Public endpoint (no auth)
echo "1. Testing public endpoint (get_user_courses):"
response=$(curl -s -X POST http://localhost:8012/tools/call \
    -H "Content-Type: application/json" \
    -d '{"name": "get_user_courses", "arguments": {"username": "vishal"}}')

if echo "$response" | grep -q "\"success\".*true"; then
    test_result "Public endpoint works without authentication" "true" "Got course data"
else
    test_result "Public endpoint works without authentication" "false" "Expected course data"
fi

# Test 2: Authenticated endpoint without token (should fail)
echo
echo "2. Testing authenticated endpoint without token (get_my_courses):"
response=$(curl -s -X POST http://localhost:8012/tools/call \
    -H "Content-Type: application/json" \
    -d '{"name": "get_my_courses", "arguments": {}}')

if echo "$response" | grep -q "Authentication required"; then
    test_result "Rejects unauthenticated access" "true" "Correctly requires authentication"
else
    test_result "Rejects unauthenticated access" "false" "Should require authentication"
fi

# Test 3-7: Get token and test authenticated endpoints
echo
echo "3. Logging in as 'happy' and getting token..."
HAPPY_TOKEN=$(generate_token "happy")
if [ $? -eq 0 ] && [ -n "$HAPPY_TOKEN" ]; then
    test_result "Login successful for happy" "true" "Token generated"

    echo
    echo "4. Testing get_my_courses with valid token:"
    response=$(curl -s -X POST http://localhost:8012/tools/call \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $HAPPY_TOKEN" \
        -d '{"name": "get_my_courses", "arguments": {}}')

    if echo "$response" | grep -q "\"success\".*true"; then
        test_result "Returns user courses" "true" "Got course data"
    else
        test_result "Returns user courses" "false" "Expected course data"
    fi

    echo
    echo "5. Testing get_my_exams:"
    response=$(curl -s -X POST http://localhost:8012/tools/call \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $HAPPY_TOKEN" \
        -d '{"name": "get_my_exams", "arguments": {}}')

    if echo "$response" | grep -q "\"success\".*true"; then
        test_result "Returns user exams" "true" "Got exam data"
    else
        test_result "Returns user exams" "false" "Expected exam data"
    fi

    echo
    echo "6. Testing get_my_preferences:"
    response=$(curl -s -X POST http://localhost:8012/tools/call \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $HAPPY_TOKEN" \
        -d '{"name": "get_my_preferences", "arguments": {}}')

    if echo "$response" | grep -q "\"success\".*true"; then
        test_result "Returns user preferences" "true" "Got preferences"
    else
        test_result "Returns user preferences" "false" "Expected preferences"
    fi

    echo
    echo "7. Testing get_my_learning_summary:"
    response=$(curl -s -X POST http://localhost:8012/tools/call \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $HAPPY_TOKEN" \
        -d '{"name": "get_my_learning_summary", "arguments": {}}')

    if echo "$response" | grep -q "\"success\".*true"; then
        test_result "Returns learning summary" "true" "Got learning summary"
    else
        test_result "Returns learning summary" "false" "Expected learning summary"
    fi
else
    test_result "Login successful for happy" "false" "Token generation failed"
fi

# Print summary
echo
echo "======================================================================="
echo "  TEST SUMMARY"
echo "======================================================================="
echo
TOTAL=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($TESTS_PASSED/$TOTAL)*100}")

echo "Total Tests: $TOTAL"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo "Success Rate: ${SUCCESS_RATE}%"
echo

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Authentication is working correctly across all MCP servers.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  $TESTS_FAILED test(s) failed. Please check the output above for details.${NC}"
    exit 1
fi
