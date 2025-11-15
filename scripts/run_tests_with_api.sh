#!/bin/bash
################################################################################
# Wrapper Script for Unified Test Runner
#
# This script ensures the API server is running before executing tests.
# It will start the API server if it's not already running.
################################################################################

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
API_URL="http://localhost:8000"
API_PORT=8000
API_HOST="0.0.0.0"
MAX_STARTUP_WAIT=30  # seconds
TEST_RUNNER="$SCRIPT_DIR/run_hourly_tests.py"
API_LOG="$PROJECT_DIR/logs/api_server.log"
API_PID_FILE="$PROJECT_DIR/logs/api_server.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Ensure log directory exists
ensure_log_dir() {
    local log_dir="$(dirname "$API_LOG")"
    if [ ! -d "$log_dir" ]; then
        mkdir -p "$log_dir"
        log_info "Created log directory: $log_dir"
    fi
}

# Check if API is running and healthy
check_api_health() {
    local max_retries=3
    local retry_delay=2

    for i in $(seq 1 $max_retries); do
        if curl -s -f "$API_URL/health" > /dev/null 2>&1; then
            return 0
        fi

        if [ $i -lt $max_retries ]; then
            sleep $retry_delay
        fi
    done

    return 1
}

# Check if API process is running (by PID file)
is_api_process_running() {
    if [ -f "$API_PID_FILE" ]; then
        local pid=$(cat "$API_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            # PID file exists but process is dead
            rm -f "$API_PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Start API server
start_api_server() {
    log_info "Starting API server..."

    cd "$PROJECT_DIR"

    # Source environment variables if .env exists
    if [ -f .env ]; then
        set -a
        source .env
        set +a
    fi

    # Start API server in background
    nohup python3 -m uvicorn api.main:app \
        --host "$API_HOST" \
        --port "$API_PORT" \
        >> "$API_LOG" 2>&1 &

    local api_pid=$!
    echo $api_pid > "$API_PID_FILE"

    log_info "API server started with PID: $api_pid"
    log_info "API logs: $API_LOG"

    # Wait for API to be ready
    log_info "Waiting for API to be ready (max ${MAX_STARTUP_WAIT}s)..."

    local elapsed=0
    while [ $elapsed -lt $MAX_STARTUP_WAIT ]; do
        if check_api_health; then
            log_success "API server is ready!"
            return 0
        fi

        sleep 1
        elapsed=$((elapsed + 1))

        # Check if process is still alive
        if ! ps -p $api_pid > /dev/null 2>&1; then
            log_error "API server process died during startup"
            log_error "Check logs: $API_LOG"
            return 1
        fi
    done

    log_error "API server failed to become healthy within ${MAX_STARTUP_WAIT}s"
    log_error "Check logs: $API_LOG"
    return 1
}

# Stop API server
stop_api_server() {
    if [ -f "$API_PID_FILE" ]; then
        local pid=$(cat "$API_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_info "Stopping API server (PID: $pid)..."
            kill "$pid" 2>/dev/null || true

            # Wait for graceful shutdown
            local elapsed=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $elapsed -lt 10 ]; do
                sleep 1
                elapsed=$((elapsed + 1))
            done

            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                log_warning "Force killing API server..."
                kill -9 "$pid" 2>/dev/null || true
            fi

            log_success "API server stopped"
        fi
        rm -f "$API_PID_FILE"
    fi
}

# Main execution
main() {
    echo "================================================================================"
    echo "               API-Aware Test Runner for DIVV Unified Test Suite"
    echo "================================================================================"
    echo ""

    # Ensure log directory exists
    ensure_log_dir

    # Track if we started the API (so we can optionally stop it later)
    local api_started_by_us=false

    # Check if API is already running
    log_info "Checking API server status..."

    if check_api_health; then
        log_success "API server is already running and healthy"
    elif is_api_process_running; then
        log_warning "API process is running but not responding to health checks"
        log_info "Attempting to restart API server..."
        stop_api_server
        if ! start_api_server; then
            log_error "Failed to start API server"
            exit 1
        fi
        api_started_by_us=true
    else
        log_warning "API server is not running"
        if ! start_api_server; then
            log_error "Failed to start API server"
            exit 1
        fi
        api_started_by_us=true
    fi

    echo ""
    echo "================================================================================"
    echo "                          Running Test Suite"
    echo "================================================================================"
    echo ""

    # Run the test suite
    if [ -x "$TEST_RUNNER" ]; then
        "$TEST_RUNNER"
        test_exit_code=$?
    else
        log_error "Test runner not found or not executable: $TEST_RUNNER"
        exit 1
    fi

    echo ""
    echo "================================================================================"
    echo "                          Test Run Complete"
    echo "================================================================================"
    echo ""

    if [ $api_started_by_us = true ]; then
        log_info "API was started by this script"
        log_info "Leaving API running for next test cycle"
        log_info "To stop manually: kill \$(cat $API_PID_FILE)"
    else
        log_info "API was already running before tests"
    fi

    echo ""
    log_info "API Server PID: $(cat $API_PID_FILE 2>/dev/null || echo 'N/A')"
    log_info "API Logs: $API_LOG"
    log_info "Test Logs: $PROJECT_DIR/logs/test_runs/latest.log"
    echo ""

    exit $test_exit_code
}

# Trap to handle interrupts
trap 'echo ""; log_warning "Interrupted by user"; exit 130' INT TERM

# Run main
main "$@"
