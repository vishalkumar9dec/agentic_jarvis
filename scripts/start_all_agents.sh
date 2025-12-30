#!/bin/bash
# Start All A2A Agent Services
#
# This script starts all three A2A agent services in the background:
# - TicketsAgent (port 8080)
# - FinOpsAgent (port 8081)
# - OxygenAgent (port 8082)
#
# Usage:
#   ./scripts/start_all_agents.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================================================"
echo "Starting All A2A Agent Services"
echo "========================================================================"
echo ""

# Check and clean up port if in use
check_port() {
    port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "  ⚠  Port $port is in use. Cleaning up..."
        lsof -ti:$port | xargs kill -9 2>/dev/null
        sleep 1

        # Verify port is now free
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            echo "  ✗ Failed to free port $port"
            return 1
        fi
        echo "  ✓ Port $port cleaned up"
    fi
    return 0
}

# Start agent service
start_agent() {
    name=$1
    port=$2
    script=$3

    echo "Starting $name (port $port)..."

    # Check and clean up port if needed
    if ! check_port $port; then
        echo "  ✗ Cannot start $name - failed to clean up port $port"
        echo ""
        return 1
    fi

    # Start service in background with output redirected to log
    cd "$PROJECT_ROOT"
    nohup .venv/bin/python -m uvicorn ${script}:a2a_app --host 0.0.0.0 --port $port > "logs/${name}.log" 2>&1 &
    pid=$!

    # Wait a moment for service to start
    sleep 2

    # Check if process is still running
    if ps -p $pid > /dev/null; then
        echo "✓ $name started (PID: $pid)"
        echo "  Agent Card: http://localhost:$port/.well-known/agent-card.json"
        echo "  Log: logs/${name}.log"
        echo ""
        return 0
    else
        echo "✗ $name failed to start (check logs/${name}.log)"
        echo ""
        return 1
    fi
}

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Start all agents
start_agent "TicketsAgent" 8080 "tickets_agent_service.agent"
start_agent "FinOpsAgent" 8081 "finops_agent_service.agent"
start_agent "OxygenAgent" 8082 "oxygen_agent_service.agent"

echo "========================================================================"
echo "All A2A Agent Services Started"
echo "========================================================================"
echo ""
echo "Verify services are running:"
echo "  lsof -i :8080,8081,8082"
echo ""
echo "Test agent cards:"
echo "  curl http://localhost:8080/.well-known/agent-card.json | jq ."
echo "  curl http://localhost:8081/.well-known/agent-card.json | jq ."
echo "  curl http://localhost:8082/.well-known/agent-card.json | jq ."
echo ""
echo "Next steps:"
echo "  1. Start Agent Registry Service:"
echo "     python agent_registry_service/main.py"
echo ""
echo "  2. Register agents:"
echo "     python scripts/migrate_to_registry_service.py"
echo ""
echo "  3. Start Jarvis orchestrator:"
echo "     python jarvis_agent/main_with_registry.py"
echo ""
echo "Stop all agents:"
echo "  ./scripts/stop_all_agents.sh"
echo ""
