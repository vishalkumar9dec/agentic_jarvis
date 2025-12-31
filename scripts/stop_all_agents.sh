#!/bin/bash
# Stop All A2A Agent Services
#
# This script stops all three A2A agent services:
# - TicketsAgent (port 8080)
# - FinOpsAgent (port 8081)
# - OxygenAgent (port 8082)
#
# Usage:
#   ./scripts/stop_all_agents.sh

echo "========================================================================"
echo "Stopping All A2A Agent Services"
echo "========================================================================"
echo ""

# Stop service by port
stop_service() {
    name=$1
    port=$2

    echo "Stopping $name (port $port)..."

    # Find PIDs listening on port
    pids=$(lsof -ti:$port 2>/dev/null)

    if [ -z "$pids" ]; then
        echo "  No process found on port $port"
    else
        # Kill all processes
        echo "$pids" | xargs kill -9 2>/dev/null
        echo "  ✓ Stopped process(es): $pids"
    fi

    echo ""
}

# Stop all agents
stop_service "TicketsAgent" 8080
stop_service "FinOpsAgent" 8081
stop_service "OxygenAgent" 8082

echo "========================================================================"
echo "All A2A Agent Services Stopped"
echo "========================================================================"
echo ""
echo "Verify services are stopped:"
echo "  lsof -i :8080,8081,8082"
echo ""
