#!/bin/bash

################################################################################
# Test Runner Script for Divv API and DIVV() Integration
#
# This script runs both Python API tests and Google Sheets integration tests
# and generates a combined test report.
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
API_BASE_URL="http://localhost:8000"
API_PID=""
LOG_FILE="$SCRIPT_DIR/test_results_$(date +%Y%m%d_%H%M%S).log"

echo "================================================================================================="
echo "                           Divv Test Suite Runner                                                "
echo "================================================================================================="
echo ""
echo "Test Results Log: $LOG_FILE"
echo ""

# Function to print colored messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if API is running
check_api() {
    print_status "Checking if API is running at $API_BASE_URL..."

    if curl -s -f "$API_BASE_URL/health" > /dev/null 2>&1; then
        print_success "API is running"
        return 0
    else
        print_warning "API is not running"
        return 1
    fi
}

# Function to start API server
start_api() {
    print_status "Starting API server..."

    cd "$PROJECT_ROOT"

    # Check if uvicorn is available
    if ! command -v uvicorn &> /dev/null; then
        print_error "uvicorn not found. Please install: pip3 install uvicorn"
        exit 1
    fi

    # Start API in background
    nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
    API_PID=$!

    print_status "Waiting for API to start (PID: $API_PID)..."

    # Wait for API to be ready (max 30 seconds)
    for i in {1..30}; do
        if check_api; then
            print_success "API started successfully"
            return 0
        fi
        sleep 1
    done

    print_error "API failed to start within 30 seconds"
    return 1
}

# Function to stop API server
stop_api() {
    if [ -n "$API_PID" ]; then
        print_status "Stopping API server (PID: $API_PID)..."
        kill $API_PID 2>/dev/null || true
        wait $API_PID 2>/dev/null || true
        print_success "API server stopped"
    fi
}

# Function to run Python API tests
run_api_tests() {
    print_status "Running Python API tests..."
    echo ""
    echo "================================================================================================="
    echo "                           Python API Endpoint Tests                                            "
    echo "================================================================================================="
    echo ""

    cd "$SCRIPT_DIR"

    # Check if pytest is available
    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found. Please install: pip3 install pytest requests"
        return 1
    fi

    # Run pytest with verbose output
    if pytest test_api_endpoints.py -v --tb=short 2>&1 | tee -a "$LOG_FILE"; then
        print_success "Python API tests completed"
        return 0
    else
        print_error "Python API tests failed"
        return 1
    fi
}

# Function to run Google Sheets integration tests
run_integration_tests() {
    print_status "Google Sheets Integration Tests Available"
    echo ""
    echo "================================================================================================="
    echo "                     Google Sheets Integration Tests (Manual)                                   "
    echo "================================================================================================="
    echo ""
    print_warning "Google Sheets integration tests require Google Apps Script environment"
    echo ""
    echo "To run these tests:"
    echo "  1. Open Google Sheets"
    echo "  2. Go to Extensions > Apps Script"
    echo "  3. Copy contents of: $SCRIPT_DIR/test_divv_integration.js"
    echo "  4. Paste into Apps Script editor"
    echo "  5. Also copy DIVV.gs from: $PROJECT_ROOT/docs-site/public/DIVV.gs"
    echo "  6. Run: runAllTests()"
    echo ""
    echo "Or use clasp (Google Apps Script CLI):"
    echo "  clasp login"
    echo "  clasp create --title 'DIVV Tests' --type sheets"
    echo "  clasp push"
    echo "  clasp run runAllTests"
    echo ""

    return 0
}

# Function to generate summary report
generate_report() {
    echo ""
    echo "================================================================================================="
    echo "                                  Test Summary                                                  "
    echo "================================================================================================="
    echo ""

    if [ -f "$LOG_FILE" ]; then
        # Extract pytest results
        if grep -q "passed" "$LOG_FILE"; then
            PASSED=$(grep -oP '\d+(?= passed)' "$LOG_FILE" | tail -1)
            FAILED=$(grep -oP '\d+(?= failed)' "$LOG_FILE" | tail -1 || echo "0")

            echo "Python API Tests:"
            echo "  ✓ Passed: ${PASSED:-0}"
            if [ "${FAILED:-0}" -gt 0 ]; then
                echo "  ✗ Failed: $FAILED"
            fi
        fi
    fi

    echo ""
    echo "Google Sheets Integration Tests:"
    echo "  ℹ Manual test available at: $SCRIPT_DIR/test_divv_integration.js"
    echo ""
    echo "Test Seed Data:"
    echo "  📁 Location: $SCRIPT_DIR/seed_data.json"
    echo "  📊 Stocks: 5 (AAPL, MSFT, JNJ, PG, T)"
    echo "  📈 Historical Prices: AAPL (5 dates), MSFT (2 dates)"
    echo "  💰 Dividend History: AAPL (5 dividends), JNJ (4 dividends)"
    echo "  🧪 Test Cases: 40+ scenarios"
    echo ""
    echo "Full test log: $LOG_FILE"
    echo ""
}

# Cleanup function
cleanup() {
    stop_api
    generate_report
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Main execution
main() {
    # Check if API is running, start if not
    if ! check_api; then
        if ! start_api; then
            print_error "Failed to start API. Exiting."
            exit 1
        fi
        API_STARTED_BY_SCRIPT=true
    else
        API_STARTED_BY_SCRIPT=false
    fi

    echo ""

    # Run API tests
    API_TESTS_PASSED=false
    if run_api_tests; then
        API_TESTS_PASSED=true
    fi

    echo ""

    # Show integration test info
    run_integration_tests

    echo ""

    # Final status
    if [ "$API_TESTS_PASSED" = true ]; then
        print_success "All automated tests passed!"
        exit 0
    else
        print_error "Some tests failed. Check $LOG_FILE for details."
        exit 1
    fi
}

# Run main
main "$@"
