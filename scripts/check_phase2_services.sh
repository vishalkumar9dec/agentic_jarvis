#!/bin/bash
# Check Phase 2 Services Health
# Verifies all Phase 2 services are running and responsive

echo "========================================"
echo "  Phase 2 Services Health Check"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
ALL_OK=true

# Function to check if port is listening
check_port() {
    local port=$1
    local service=$2

    if lsof -i:$port > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $service (port $port) - Running"
        return 0
    else
        echo -e "${RED}✗${NC} $service (port $port) - Not running"
        ALL_OK=false
        return 1
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local service=$2

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)

    if [ "$response" == "200" ]; then
        echo -e "  ${GREEN}✓${NC} Health endpoint responds: $url"
        return 0
    else
        echo -e "  ${YELLOW}⚠${NC}  Health endpoint status $response: $url"
        return 1
    fi
}

# Check each service
echo "Checking services..."
echo ""

# Auth Service (Port 9998)
echo "1. Auth Service:"
if check_port 9998 "Auth Service"; then
    check_endpoint "http://localhost:9998/health" "Auth Service"
fi
echo ""

# Tickets Server (Port 5001)
echo "2. Tickets Toolbox Server:"
if check_port 5001 "Tickets Server"; then
    check_endpoint "http://localhost:5001/health" "Tickets Server"
fi
echo ""

# FinOps Server (Port 5002)
echo "3. FinOps Toolbox Server:"
if check_port 5002 "FinOps Server"; then
    check_endpoint "http://localhost:5002/health" "FinOps Server"
fi
echo ""

# Oxygen Agent (Port 8002)
echo "4. Oxygen A2A Agent:"
if check_port 8002 "Oxygen Agent"; then
    check_endpoint "http://localhost:8002/.well-known/agent-card.json" "Oxygen Agent"
fi
echo ""

# Web UI (Port 9999)
echo "5. Web UI Server:"
if check_port 9999 "Web UI"; then
    # Web UI doesn't have a /health endpoint, just check if it responds
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:9999/login.html" 2>/dev/null)
    if [ "$response" == "200" ]; then
        echo -e "  ${GREEN}✓${NC} Login page accessible: http://localhost:9999/login.html"
    else
        echo -e "  ${YELLOW}⚠${NC}  Login page status $response"
    fi
fi
echo ""

# Summary
echo "========================================"
if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}All Phase 2 services are running!${NC}"
    echo ""
    echo "Quick links:"
    echo "  • Web UI:       http://localhost:9999/login.html"
    echo "  • Auth Service: http://localhost:9998/docs"
    echo "  • Tickets API:  http://localhost:5001/docs"
    echo "  • FinOps API:   http://localhost:5002/docs"
    echo "  • Oxygen Card:  http://localhost:8002/.well-known/agent-card.json"
    echo ""
    echo "Demo accounts:"
    echo "  • vishal / password123 (developer)"
    echo "  • alex / password123 (devops)"
    echo "  • sarah / password123 (data_scientist)"
else
    echo -e "${RED}Some services are not running!${NC}"
    echo ""
    echo "To start all services:"
    echo "  ./scripts/restart_all_phase2.sh"
    echo ""
    echo "To start individual services:"
    echo "  ./scripts/start_auth_service.sh"
    echo "  ./scripts/start_tickets_server.sh"
    echo "  ./scripts/start_finops_server.sh"
    echo "  ./scripts/start_oxygen_agent.sh"
    echo "  ./scripts/start_web_ui.sh"
    echo ""
    echo "Check logs in logs/ directory for errors"
fi
echo "========================================"
