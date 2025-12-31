#!/bin/bash
# =============================================================================
# Start Agent Registry Service
# =============================================================================
# This script starts the Agent Registry Service either locally or via Docker.
#
# Usage:
#   ./scripts/start_registry_service.sh           # Local mode
#   ./scripts/start_registry_service.sh --docker  # Docker mode
#   ./scripts/start_registry_service.sh --reload  # Development mode with auto-reload
#
# Requirements:
#   - Python 3.11+
#   - Virtual environment at .venv/
#   - GOOGLE_API_KEY environment variable (recommended)
# =============================================================================

set -e  # Exit on error

# Configuration
PORT=8003
SERVICE_NAME="Agent Registry Service"
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/registry_service.log"
DATA_DIR="data"
DOCKER_MODE=false
RELOAD_MODE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Parse Arguments
# =============================================================================

for arg in "$@"; do
    case $arg in
        --docker)
            DOCKER_MODE=true
            shift
            ;;
        --reload)
            RELOAD_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --docker    Run in Docker mode"
            echo "  --reload    Run in development mode with auto-reload"
            echo "  --help      Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# =============================================================================
# Environment Checks
# =============================================================================

log_info "Starting $SERVICE_NAME..."

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
    log_warning "GOOGLE_API_KEY not set in environment"
    log_warning "Some features may not work correctly"
fi

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    log_warning "Port $PORT is already in use"
    read -p "Kill existing process? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Killing process on port $PORT..."
        lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
        sleep 2
        log_success "Process killed"
    else
        log_error "Cannot start service - port $PORT is in use"
        exit 1
    fi
fi

# =============================================================================
# Docker Mode
# =============================================================================

if [ "$DOCKER_MODE" = true ]; then
    log_info "Starting in Docker mode..."

    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose not found. Please install Docker Compose."
        exit 1
    fi

    # Navigate to service directory
    cd agent_registry_service

    # Build and start
    log_info "Building Docker image..."
    docker-compose build

    log_info "Starting container..."
    docker-compose up -d

    # Wait for service to be ready
    log_info "Waiting for service to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
            log_success "$SERVICE_NAME started successfully in Docker!"
            log_info "Health check: http://localhost:$PORT/health"
            log_info "API Docs: http://localhost:$PORT/docs"
            log_info ""
            log_info "View logs: docker-compose logs -f"
            log_info "Stop service: docker-compose down"
            exit 0
        fi
        sleep 1
    done

    log_error "Service failed to start within 30 seconds"
    log_info "Check logs: docker-compose logs"
    exit 1
fi

# =============================================================================
# Local Mode
# =============================================================================

log_info "Starting in local mode..."

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$DATA_DIR"
log_success "Created directories: $LOG_DIR, $DATA_DIR"

# Check for virtual environment
if [ ! -d ".venv" ]; then
    log_error "Virtual environment not found at .venv/"
    log_info "Create it with: python3 -m venv .venv"
    exit 1
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source .venv/bin/activate

# Install/update dependencies
log_info "Checking dependencies..."
if [ -f "agent_registry_service/requirements.txt" ]; then
    pip install -q -r agent_registry_service/requirements.txt
    log_success "Dependencies installed"
fi

# Build uvicorn command
UVICORN_CMD="uvicorn agent_registry_service.app:app --host 0.0.0.0 --port $PORT"

if [ "$RELOAD_MODE" = true ]; then
    log_info "Development mode: Auto-reload enabled"
    UVICORN_CMD="$UVICORN_CMD --reload"
fi

# Start service
log_info "Starting $SERVICE_NAME on port $PORT..."
log_info "Logs will be written to: $LOG_FILE"
log_info ""

# Run in background and log to file
nohup $UVICORN_CMD > "$LOG_FILE" 2>&1 &
SERVICE_PID=$!

# Save PID for stop script
echo $SERVICE_PID > ".registry_service.pid"

# Wait for service to be ready
log_info "Waiting for service to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        log_success "$SERVICE_NAME started successfully!"
        log_success "PID: $SERVICE_PID"
        log_info ""
        log_info "Service URLs:"
        log_info "  Health Check: http://localhost:$PORT/health"
        log_info "  API Docs:     http://localhost:$PORT/docs"
        log_info "  Service Info: http://localhost:$PORT"
        log_info ""
        log_info "View logs: tail -f $LOG_FILE"
        log_info "Stop service: ./scripts/stop_registry_service.sh"
        exit 0
    fi
    sleep 1
done

# If we get here, service failed to start
log_error "Service failed to start within 30 seconds"
log_info "Check logs: tail $LOG_FILE"

# Kill the process
kill $SERVICE_PID 2>/dev/null || true
rm -f ".registry_service.pid"

exit 1
