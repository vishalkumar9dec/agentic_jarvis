#!/bin/bash
# Start Tickets Toolbox Server (Port 5001)

echo "Starting Tickets Toolbox Server..."

# Get the project root directory (parent of scripts/)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run 'python -m venv .venv' first."
    exit 1
fi

# Kill existing process on port 5001
echo "Checking for existing processes on port 5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null
sleep 1

# Create logs directory if it doesn't exist
mkdir -p logs

# Start tickets server
echo "Starting tickets server on port 5001..."
.venv/bin/python -m uvicorn toolbox_servers.tickets_server.server:app --host localhost --port 5001 > logs/tickets_server.log 2>&1 &

# Wait a moment for service to start
sleep 2

# Check if service is running
if lsof -i:5001 > /dev/null 2>&1; then
    echo "✓ Tickets Server started successfully on port 5001"
    echo "  Logs: logs/tickets_server.log"
    echo "  URL: http://localhost:5001"
    echo "  Health: http://localhost:5001/health"
    echo "  Docs: http://localhost:5001/docs"
else
    echo "✗ Failed to start Tickets Server"
    echo "  Check logs/tickets_server.log for errors"
    exit 1
fi
