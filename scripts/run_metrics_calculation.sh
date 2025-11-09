#!/bin/bash
# Hourly Stock Metrics Calculation Script
# Calculates frequency, TTM, YTD, and other derived metrics for all stocks

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Set up logging
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/metrics_calculation_$(date +%Y%m%d).log"

echo "========================================" >> "$LOG_FILE"
echo "Starting metrics calculation at $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Run the calculation script
cd "$PROJECT_DIR"
python3 scripts/calculate_stock_metrics.py >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

echo "========================================" >> "$LOG_FILE"
echo "Finished at $(date) with exit code $EXIT_CODE" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

exit $EXIT_CODE
