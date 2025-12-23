#!/bin/bash
# Start Web UI Server (Port 9999)

echo "Starting Web UI Server..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run 'python -m venv .venv' first."
    exit 1
fi

# Kill existing process on port 9999
echo "Checking for existing processes on port 9999..."
lsof -ti:9999 | xargs kill -9 2>/dev/null
sleep 1

# Create logs directory if it doesn't exist
mkdir -p logs

# Start web UI server
echo "Starting web UI server on port 9999..."
.venv/bin/python -m uvicorn web_ui.server:app --host localhost --port 9999 > logs/web_ui.log 2>&1 &

# Wait a moment for service to start
sleep 2

# Check if service is running
if lsof -i:9999 > /dev/null 2>&1; then
    echo "✓ Web UI Server started successfully on port 9999"
    echo "  Logs: logs/web_ui.log"
    echo "  URL: http://localhost:9999"
    echo "  Login: http://localhost:9999/login.html"
    echo "  Chat: http://localhost:9999/chat.html"
else
    echo "✗ Failed to start Web UI Server"
    echo "  Check logs/web_ui.log for errors"
    exit 1
fi
