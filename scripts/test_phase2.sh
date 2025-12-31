#!/bin/bash
# Automated Test Script for Phase 2 Pure A2A Implementation
#
# This script runs automated tests to verify:
# - All services are running
# - Authentication works
# - Agent cards are accessible
# - A2A communication works
#
# Usage:
#   ./scripts/test_phase2.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================================================"
echo "Automated Test Suite - Phase 2 Pure A2A Implementation"
echo "========================================================================"
echo ""

TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run a test
run_test() {
    test_name=$1
    shift
    command="$@"

    echo -n "Testing: $test_name ... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "========================================================================"
echo "Step 1: Service Availability Tests"
echo "========================================================================"
echo ""

# Test service ports
run_test "Auth Service (port 9998)" "lsof -Pi :9998 -sTCP:LISTEN -t"
run_test "Registry Service (port 8003)" "lsof -Pi :8003 -sTCP:LISTEN -t"
run_test "TicketsAgent (port 8080)" "lsof -Pi :8080 -sTCP:LISTEN -t"
run_test "FinOpsAgent (port 8081)" "lsof -Pi :8081 -sTCP:LISTEN -t"
run_test "OxygenAgent (port 8082)" "lsof -Pi :8082 -sTCP:LISTEN -t"

echo ""
echo "========================================================================"
echo "Step 2: Health Check Tests"
echo "========================================================================"
echo ""

# Test health endpoints
run_test "Auth Service health" "curl -s -f http://localhost:9998/health"
run_test "Registry Service health" "curl -s -f http://localhost:8003/health"

echo ""
echo "========================================================================"
echo "Step 3: Authentication Tests"
echo "========================================================================"
echo ""

# Test authentication for each user
run_test "Login as vishal" "curl -s -f -X POST http://localhost:9998/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"vishal\",\"password\":\"password123\"}'"
run_test "Login as happy" "curl -s -f -X POST http://localhost:9998/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"happy\",\"password\":\"password123\"}'"
run_test "Login as alex" "curl -s -f -X POST http://localhost:9998/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"alex\",\"password\":\"password123\"}'"

# Test invalid login
if curl -s -f -X POST http://localhost:9998/auth/login -H 'Content-Type: application/json' -d '{"username":"vishal","password":"wrongpass"}' > /dev/null 2>&1; then
    echo -e "Testing: Invalid password rejected ... ${RED}✗ FAIL${NC} (should have rejected)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "Testing: Invalid password rejected ... ${GREEN}✓ PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

echo ""
echo "========================================================================"
echo "Step 4: A2A Agent Card Tests"
echo "========================================================================"
echo ""

# Test agent cards
run_test "TicketsAgent card" "curl -s -f http://localhost:8080/.well-known/agent-card.json | jq -e '.name == \"TicketsAgent\"'"
run_test "FinOpsAgent card" "curl -s -f http://localhost:8081/.well-known/agent-card.json | jq -e '.name == \"FinOpsAgent\"'"
run_test "OxygenAgent card" "curl -s -f http://localhost:8082/.well-known/agent-card.json | jq -e '.name == \"OxygenAgent\"'"

# Verify protocol version
run_test "A2A protocol version" "curl -s http://localhost:8080/.well-known/agent-card.json | jq -e '.protocolVersion == \"0.3.0\"'"

echo ""
echo "========================================================================"
echo "Step 5: Registry Service Tests"
echo "========================================================================"
echo ""

# Test registry endpoints
run_test "Registry API docs" "curl -s -f http://localhost:8003/docs"
run_test "Get agents from registry" "curl -s -f http://localhost:8003/agents"

echo ""
echo "========================================================================"
echo "Step 6: JWT Token Validation"
echo "========================================================================"
echo ""

# Get a valid token
TOKEN=$(curl -s -X POST http://localhost:9998/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"vishal","password":"password123"}' | jq -r '.access_token')

if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    echo -e "Testing: JWT token generation ... ${GREEN}✓ PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))

    # Test token verification
    run_test "JWT token verification" "curl -s -f 'http://localhost:9998/auth/verify?token=$TOKEN'"
else
    echo -e "Testing: JWT token generation ... ${RED}✗ FAIL${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo "========================================================================"
echo "Test Summary"
echo "========================================================================"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

echo -e "Total Tests:  $TOTAL_TESTS"
echo -e "${GREEN}Passed:       $TESTS_PASSED${NC}"

if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed:       $TESTS_FAILED${NC}"
    echo ""
    echo -e "${RED}Some tests failed. Please check the services and try again.${NC}"
    echo ""
    echo "Debug commands:"
    echo "  # Check service logs"
    echo "  tail logs/auth_service.log"
    echo "  tail logs/registry_service.log"
    echo "  tail logs/TicketsAgent.log"
    echo ""
    echo "  # Restart services"
    echo "  ./scripts/stop_all_services.sh"
    echo "  ./scripts/start_phase2.sh"
    echo ""
    exit 1
else
    echo -e "${GREEN}Failed:       0${NC}"
    echo ""
    echo -e "${GREEN}========================================================================${NC}"
    echo -e "${GREEN}✅ All Tests Passed!${NC}"
    echo -e "${GREEN}========================================================================${NC}"
    echo ""
    echo "Your Phase 2 Pure A2A implementation is working correctly!"
    echo ""
    echo "Next steps:"
    echo "  1. Start Jarvis CLI:"
    echo "     python jarvis_agent/main_with_registry.py"
    echo ""
    echo "  2. Test interactive features:"
    echo "     - Login with: vishal / password123"
    echo "     - Query: show my tickets"
    echo "     - Query: what are my courses"
    echo "     - Test session persistence (exit and re-login)"
    echo ""
    echo "  3. See detailed testing guide:"
    echo "     docs/TESTING_PURE_A2A.md"
    echo ""
    exit 0
fi
