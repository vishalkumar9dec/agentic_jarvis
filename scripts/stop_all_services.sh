#!/bin/bash
# Stop All Services for Phase 2
#
# This script stops all services started by start_phase2.sh:
# - Auth Service (port 9998)
# - Registry Service (port 8003)
# - TicketsAgent (port 8080)
# - FinOpsAgent (port 8081)
# - OxygenAgent (port 8082)
#
# Usage:
#   ./scripts/stop_all_services.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================================================"
echo "Stopping All Jarvis Services"
echo "========================================================================"
echo ""

# Stop service on port
stop_port() {
    port=$1
    name=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${BLUE}[$name]${NC} Stopping service on port $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1

        # Verify stopped
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "  ${GREEN}✓ $name stopped${NC}"
        else
            echo -e "  ${RED}✗ Failed to stop $name${NC}"
        fi
    else
        echo -e "${YELLOW}[$name]${NC} Not running on port $port"
    fi
    echo ""
}

# Stop all services
stop_port 9998 "Auth Service"
stop_port 8003 "Registry Service"
stop_port 8080 "TicketsAgent"
stop_port 8081 "FinOpsAgent"
stop_port 8082 "OxygenAgent"

echo "========================================================================"
echo "Verify All Services Stopped:"
echo "========================================================================"
echo ""

# Check if any services are still running
if lsof -i :8003,8080,8081,8082,9998 2>/dev/null | grep LISTEN; then
    echo -e "${YELLOW}⚠  Some services are still running${NC}"
    echo ""
else
    echo -e "${GREEN}✓ All services stopped${NC}"
    echo ""
fi

echo "To start services again:"
echo "  ./scripts/start_phase2.sh"
echo ""
