#!/bin/bash
# Health check script for all Jarvis services

echo "=========================================="
echo "Jarvis Services Health Check"
echo "=========================================="
echo ""

# Function to check a service
check_service() {
    local name=$1
    local port=$2
    local endpoint=$3
    local success=true

    # Check if port is in use
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "✅ $name - Running on port $port"

        # Check if endpoint is provided and test HTTP response
        if [ -n "$endpoint" ]; then
            http_status=$(curl -s -o /dev/null -w "%{http_code}" $endpoint 2>/dev/null)

            if [ "$http_status" = "200" ]; then
                echo "   └─ HTTP endpoint responsive (status: $http_status)"
            elif [ "$http_status" = "000" ]; then
                echo "   └─ ⚠️  HTTP endpoint not responding (connection failed)"
                success=false
            else
                echo "   └─ ⚠️  HTTP endpoint returned status: $http_status"
                success=false
            fi
        fi
    else
        echo "❌ $name - NOT running on port $port"
        success=false
    fi

    echo ""

    # Return status
    if $success; then
        return 0
    else
        return 1
    fi
}

# Check all services
tickets_status=0
finops_status=0
oxygen_status=0

check_service "Tickets Toolbox Server" 5001 "http://localhost:5001/"
tickets_status=$?

check_service "FinOps Toolbox Server" 5002 "http://localhost:5002/"
finops_status=$?

check_service "Oxygen A2A Agent" 8002 "http://localhost:8002/.well-known/agent-card.json"
oxygen_status=$?

# Optional: Check web UI (not required for basic operation)
if lsof -ti:9999 > /dev/null 2>&1; then
    check_service "Web UI Server" 9999 "http://localhost:9999/docs"
else
    echo "ℹ️  Web UI Server - Not running (optional)"
    echo "   └─ Start with: ./scripts/start_web.sh"
    echo ""
fi

echo "=========================================="

# Summary
if [ $tickets_status -eq 0 ] && [ $finops_status -eq 0 ] && [ $oxygen_status -eq 0 ]; then
    echo "✅ All core services are healthy and running!"
    echo ""
    echo "You can now:"
    echo "  • Run 'python main.py' to start the CLI interface"
    echo "  • Run './scripts/start_web.sh' to start the Web UI"
    echo "  • Send requests to the agents"
    echo ""
    exit 0
else
    echo "⚠️  Some services are not healthy"
    echo ""
    echo "To start all services, run:"
    echo "  ./scripts/restart_all.sh"
    echo ""

    # Show which services need attention
    if [ $tickets_status -ne 0 ]; then
        echo "  • Tickets Server needs attention"
        echo "    Start: ./scripts/start_tickets_server.sh"
        echo "    Logs: logs/tickets_server.log"
        echo ""
    fi

    if [ $finops_status -ne 0 ]; then
        echo "  • FinOps Server needs attention"
        echo "    Start: ./scripts/start_finops_server.sh"
        echo "    Logs: logs/finops_server.log"
        echo ""
    fi

    if [ $oxygen_status -ne 0 ]; then
        echo "  • Oxygen Agent needs attention"
        echo "    Start: ./scripts/start_oxygen_agent.sh"
        echo "    Logs: logs/oxygen_agent.log"
        echo ""
    fi

    exit 1
fi

echo "=========================================="
