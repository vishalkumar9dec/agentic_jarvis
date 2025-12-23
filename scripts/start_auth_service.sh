#!/bin/bash
# Start Auth Service (Port 9998)

echo "Starting Auth Service..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run 'python -m venv .venv' first."
    exit 1
fi

# Kill existing process on port 9998
echo "Checking for existing processes on port 9998..."
lsof -ti:9998 | xargs kill -9 2>/dev/null
sleep 1

# Create logs directory if it doesn't exist
mkdir -p logs

# Start auth service
echo "Starting auth service on port 9998..."
.venv/bin/python -m uvicorn auth.auth_server:app --host localhost --port 9998 > logs/auth_server.log 2>&1 &

# Wait a moment for service to start
sleep 2

# Check if service is running
if lsof -i:9998 > /dev/null 2>&1; then
    echo "✓ Auth Service started successfully on port 9998"
    echo "  Logs: logs/auth_server.log"
    echo "  URL: http://localhost:9998"
    echo "  Health: http://localhost:9998/health"
    echo "  Docs: http://localhost:9998/docs"
else
    echo "✗ Failed to start Auth Service"
    echo "  Check logs/auth_server.log for errors"
    exit 1
fi
