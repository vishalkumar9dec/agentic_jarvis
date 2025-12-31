#!/bin/bash
# Start All Services for Phase 2 (Pure A2A + JWT Auth + Session Persistence)
#
# This script starts all services required for Phase 2:
# 1. Auth Service (port 9998) - JWT authentication
# 2. Registry Service (port 8003) - Agent registry + session management
# 3. TicketsAgent (port 8080) - IT operations
# 4. FinOpsAgent (port 8081) - Cloud cost analytics
# 5. OxygenAgent (port 8082) - Learning & development
#
# Usage:
#   ./scripts/start_phase2.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================================================"
echo "Starting Jarvis - Phase 2 (Pure A2A + JWT Auth + Session Persistence)"
echo "========================================================================"
echo ""

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}✗ Error: .env file not found${NC}"
    echo ""
    echo "Please create .env from template:"
    echo "  cp .env.template .env"
    echo ""
    echo "Then configure:"
    echo "  1. Get Google API key: https://makersuite.google.com/app/apikey"
    echo "  2. Generate JWT secret: ./scripts/generate_jwt_secret.sh"
    echo "  3. Update .env with your values"
    echo ""
    exit 1
fi

# Check and clean up port if in use
check_port() {
    port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "  ${YELLOW}⚠  Port $port is in use. Cleaning up...${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1

        # Verify port is now free
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            echo -e "  ${RED}✗ Failed to free port $port${NC}"
            return 1
        fi
        echo -e "  ${GREEN}✓ Port $port cleaned up${NC}"
    fi
    return 0
}

# Health check for a service
health_check() {
    url=$1
    max_attempts=10
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    return 1
}

# Start a generic service
start_service() {
    name=$1
    port=$2
    command=$3
    health_url=$4

    echo -e "${BLUE}[$name]${NC} Starting on port $port..."

    # Check and clean up port if needed
    if ! check_port $port; then
        echo -e "  ${RED}✗ Cannot start $name - failed to clean up port $port${NC}"
        echo ""
        return 1
    fi

    # Create logs directory
    mkdir -p "$PROJECT_ROOT/logs"

    # Start service in background
    cd "$PROJECT_ROOT"
    eval "$command > logs/${name}.log 2>&1 &"
    pid=$!

    # Wait for health check
    echo -e "  ${BLUE}Waiting for health check...${NC}"
    if health_check "$health_url"; then
        echo -e "  ${GREEN}✓ $name started successfully (PID: $pid)${NC}"
        echo -e "  ${BLUE}Health: $health_url${NC}"
        echo -e "  ${BLUE}Log: logs/${name}.log${NC}"
        echo ""
        return 0
    else
        echo -e "  ${RED}✗ $name health check failed${NC}"
        echo -e "  ${YELLOW}Check logs/${name}.log for details${NC}"
        echo ""
        return 1
    fi
}

# Start A2A agent
start_agent() {
    name=$1
    port=$2
    module=$3

    command=".venv/bin/python -m uvicorn ${module}:a2a_app --host 0.0.0.0 --port $port"
    health_url="http://localhost:$port/.well-known/agent-card.json"

    start_service "$name" "$port" "$command" "$health_url"
}

echo "========================================================================"
echo "Step 1: Starting Core Services"
echo "========================================================================"
echo ""

# Start Auth Service first (required for authentication)
echo -e "${BLUE}[AuthService]${NC} Starting authentication service..."
if ! check_port 9998; then
    echo -e "${RED}✗ Cannot start Auth Service${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"
source .venv/bin/activate
nohup python -m auth.auth_server > logs/auth_service.log 2>&1 &
auth_pid=$!

echo -e "  ${BLUE}Waiting for health check...${NC}"
if health_check "http://localhost:9998/health"; then
    echo -e "  ${GREEN}✓ Auth Service started (PID: $auth_pid)${NC}"
    echo -e "  ${BLUE}Health: http://localhost:9998/health${NC}"
    echo -e "  ${BLUE}Login: http://localhost:9998/auth/login${NC}"
    echo -e "  ${BLUE}Log: logs/auth_service.log${NC}"
    echo ""
else
    echo -e "  ${RED}✗ Auth Service health check failed${NC}"
    echo -e "  ${YELLOW}Check logs/auth_service.log${NC}"
    exit 1
fi

# Start Registry Service (required for session management)
if ! ./scripts/start_registry_service.sh > /dev/null 2>&1; then
    echo -e "${RED}✗ Failed to start Registry Service${NC}"
    echo -e "${YELLOW}Check logs/registry_service.log${NC}"
    exit 1
fi

# Wait for registry to be ready
sleep 3
if health_check "http://localhost:8003/health"; then
    echo -e "${GREEN}✓ Registry Service started${NC}"
    echo -e "  ${BLUE}Health: http://localhost:8003/health${NC}"
    echo -e "  ${BLUE}Docs: http://localhost:8003/docs${NC}"
    echo ""
else
    echo -e "${RED}✗ Registry Service health check failed${NC}"
    exit 1
fi

echo "========================================================================"
echo "Step 2: Starting A2A Agent Services"
echo "========================================================================"
echo ""

# Start all A2A agents
start_agent "TicketsAgent" 8080 "tickets_agent_service.agent"
start_agent "FinOpsAgent" 8081 "finops_agent_service.agent"
start_agent "OxygenAgent" 8082 "oxygen_agent_service.agent"

echo "========================================================================"
echo "✅ All Services Started Successfully!"
echo "========================================================================"
echo ""

# Show service summary
echo -e "${GREEN}Running Services:${NC}"
echo ""
echo "  Authentication:"
echo "    • Auth Service:      http://localhost:9998"
echo ""
echo "  Core Services:"
echo "    • Registry Service:  http://localhost:8003"
echo "    • API Docs:          http://localhost:8003/docs"
echo ""
echo "  A2A Agents:"
echo "    • TicketsAgent:      http://localhost:8080 (IT Operations)"
echo "    • FinOpsAgent:       http://localhost:8081 (Cloud Costs)"
echo "    • OxygenAgent:       http://localhost:8082 (Learning & Dev)"
echo ""

echo -e "${BLUE}Test Users (for authentication):${NC}"
echo "  • vishal / password123  (2 tickets, 3 courses, 2 pending exams)"
echo "  • happy / password123   (1 ticket, 2 courses, 1 pending exam)"
echo "  • alex / password123    (0 tickets, 2 courses, 1 pending exam)"
echo ""

echo -e "${BLUE}Quick Start:${NC}"
echo "  1. Start Jarvis CLI:"
echo "     python jarvis_agent/main_with_registry.py"
echo ""
echo "  2. Login with test user:"
echo "     Username: vishal"
echo "     Password: password123"
echo ""
echo "  3. Try queries:"
echo "     • show my tickets"
echo "     • what are my courses"
echo "     • what is our total cloud cost"
echo ""

echo -e "${BLUE}Verify Services:${NC}"
echo "  # Check all services are running"
echo "  lsof -i :8003,8080,8081,8082,9998 | grep LISTEN"
echo ""
echo "  # Test agent cards"
echo "  curl http://localhost:8080/.well-known/agent-card.json | jq .name"
echo "  curl http://localhost:8081/.well-known/agent-card.json | jq .name"
echo "  curl http://localhost:8082/.well-known/agent-card.json | jq .name"
echo ""
echo "  # Test authentication"
echo "  curl -X POST http://localhost:9998/auth/login \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"username\":\"vishal\",\"password\":\"password123\"}' | jq ."
echo ""

echo -e "${BLUE}Stop Services:${NC}"
echo "  ./scripts/stop_all_services.sh"
echo ""

echo -e "${BLUE}Logs:${NC}"
echo "  tail -f logs/auth_service.log      # Auth service"
echo "  tail -f logs/registry_service.log  # Registry service"
echo "  tail -f logs/TicketsAgent.log      # Tickets agent"
echo "  tail -f logs/FinOpsAgent.log       # FinOps agent"
echo "  tail -f logs/OxygenAgent.log       # Oxygen agent"
echo ""

echo "========================================================================"
