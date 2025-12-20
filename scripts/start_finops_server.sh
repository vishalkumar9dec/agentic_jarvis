#!/bin/bash
# Start FinOps Toolbox Server (Port 5002)

echo "Starting FinOps Toolbox Server..."

# Get the project root directory (parent of scripts/)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run 'python -m venv .venv' first."
    exit 1
fi

# Kill existing process on port 5002
echo "Checking for existing processes on port 5002..."
lsof -ti:5002 | xargs kill -9 2>/dev/null
sleep 1

# Create logs directory if it doesn't exist
mkdir -p logs

# Start finops server
echo "Starting finops server on port 5002..."
.venv/bin/python -m uvicorn toolbox_servers.finops_server.server:app --host localhost --port 5002 > logs/finops_server.log 2>&1 &

# Wait a moment for service to start
sleep 2

# Check if service is running
if lsof -i:5002 > /dev/null 2>&1; then
    echo "✓ FinOps Server started successfully on port 5002"
    echo "  Logs: logs/finops_server.log"
    echo "  URL: http://localhost:5002"
    echo "  Health: http://localhost:5002/health"
    echo "  Docs: http://localhost:5002/docs"
else
    echo "✗ Failed to start FinOps Server"
    echo "  Check logs/finops_server.log for errors"
    exit 1
fi
