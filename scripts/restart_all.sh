#!/bin/bash
# Restart all Jarvis services (Tickets, FinOps, Oxygen)

echo "========================================"
echo "Restarting All Jarvis Services"
echo "========================================"
echo ""

# Get the project root directory (parent of scripts/)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found at .venv/"
    echo "Please create a virtual environment first: python -m venv .venv"
    exit 1
fi

# Kill all services
echo "Step 1: Stopping all existing services..."
lsof -ti:5001 | xargs kill -9 2>/dev/null && echo "  ✓ Stopped Tickets server (port 5001)" || echo "  • No Tickets server running"
lsof -ti:5002 | xargs kill -9 2>/dev/null && echo "  ✓ Stopped FinOps server (port 5002)" || echo "  • No FinOps server running"
lsof -ti:8002 | xargs kill -9 2>/dev/null && echo "  ✓ Stopped Oxygen agent (port 8002)" || echo "  • No Oxygen agent running"

echo ""
echo "Waiting 2 seconds for ports to be released..."
sleep 2

# Check for .env file for Oxygen
if [ ! -f "remote_agent/oxygen_agent/.env" ]; then
    echo ""
    echo "⚠ Warning: .env file not found for Oxygen agent"
    if [ -f "remote_agent/oxygen_agent/.env.template" ]; then
        echo "Creating .env from template..."
        cp remote_agent/oxygen_agent/.env.template remote_agent/oxygen_agent/.env
        echo "✓ Created remote_agent/oxygen_agent/.env"
        echo ""
        echo "⚠ IMPORTANT: Please edit remote_agent/oxygen_agent/.env and add your GOOGLE_API_KEY"
        echo "Then run this script again."
        exit 1
    fi
fi

echo ""
echo "Step 2: Starting all services in background..."
echo ""

# Start Tickets server
echo "Starting Tickets Toolbox Server (port 5001)..."
nohup .venv/bin/python toolbox_servers/tickets_server/server.py > logs/tickets_server.log 2>&1 &
TICKETS_PID=$!
sleep 1

# Start FinOps server
echo "Starting FinOps Toolbox Server (port 5002)..."
nohup .venv/bin/python toolbox_servers/finops_server/server.py > logs/finops_server.log 2>&1 &
FINOPS_PID=$!
sleep 1

# Start Oxygen agent
echo "Starting Oxygen A2A Agent (port 8002)..."
nohup .venv/bin/python -m uvicorn remote_agent.oxygen_agent.agent:a2a_app --host localhost --port 8002 > logs/oxygen_agent.log 2>&1 &
OXYGEN_PID=$!
sleep 2

echo ""
echo "Step 3: Verifying services..."
echo ""

# Check if services are running
TICKETS_RUNNING=false
FINOPS_RUNNING=false
OXYGEN_RUNNING=false

if lsof -ti:5001 > /dev/null 2>&1; then
    echo "✓ Tickets server is running on port 5001"
    TICKETS_RUNNING=true
else
    echo "❌ Tickets server failed to start (check logs/tickets_server.log)"
fi

if lsof -ti:5002 > /dev/null 2>&1; then
    echo "✓ FinOps server is running on port 5002"
    FINOPS_RUNNING=true
else
    echo "❌ FinOps server failed to start (check logs/finops_server.log)"
fi

if lsof -ti:8002 > /dev/null 2>&1; then
    echo "✓ Oxygen agent is running on port 8002"
    OXYGEN_RUNNING=true
else
    echo "❌ Oxygen agent failed to start (check logs/oxygen_agent.log)"
fi

echo ""
echo "========================================"
if $TICKETS_RUNNING && $FINOPS_RUNNING && $OXYGEN_RUNNING; then
    echo "✓ All services started successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Run './scripts/check_services.sh' to verify health"
    echo "  2. Run 'python main.py' to start the CLI interface"
    echo ""
    echo "Logs are available in the logs/ directory"
else
    echo "⚠ Some services failed to start"
    echo "Check the logs in the logs/ directory for details"
fi
echo "========================================"
