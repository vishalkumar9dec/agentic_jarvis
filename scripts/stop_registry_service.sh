#!/bin/bash
# =============================================================================
# Stop Agent Registry Service
# =============================================================================
# This script stops the Agent Registry Service running either locally or in Docker.
#
# Usage:
#   ./scripts/stop_registry_service.sh
#   ./scripts/stop_registry_service.sh --docker
# =============================================================================

set -e  # Exit on error

# Configuration
PORT=8003
SERVICE_NAME="Agent Registry Service"
PID_FILE=".registry_service.pid"
DOCKER_MODE=false

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
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --docker    Stop Docker container"
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
# Stop Service
# =============================================================================

log_info "Stopping $SERVICE_NAME..."

if [ "$DOCKER_MODE" = true ]; then
    # Docker mode
    log_info "Stopping Docker container..."

    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose not found"
        exit 1
    fi

    cd agent_registry_service
    docker-compose down

    log_success "$SERVICE_NAME stopped (Docker)"
else
    # Local mode - try PID file first
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        log_info "Found PID file: $PID"

        if ps -p $PID > /dev/null 2>&1; then
            log_info "Stopping process $PID..."
            kill $PID
            sleep 2

            # Force kill if still running
            if ps -p $PID > /dev/null 2>&1; then
                log_warning "Process still running, forcing kill..."
                kill -9 $PID
            fi

            log_success "Process $PID stopped"
        else
            log_warning "Process $PID not running"
        fi

        rm -f "$PID_FILE"
    fi

    # Also check port directly
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_info "Found process on port $PORT, killing..."
        lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
        sleep 1
        log_success "Process on port $PORT killed"
    fi

    # Verify service is stopped
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_error "Failed to stop service on port $PORT"
        exit 1
    else
        log_success "$SERVICE_NAME stopped"
    fi
fi

exit 0
