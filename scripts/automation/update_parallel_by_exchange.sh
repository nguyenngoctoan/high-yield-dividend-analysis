#!/bin/bash
#
# Parallel Update Script - By Exchange Groups
#
# Runs stock updates for different exchange groups in parallel to maximize throughput.
# This can reduce Step 2 runtime from 90 minutes to 30-45 minutes.
#
# Usage:
#   ./scripts/update_parallel_by_exchange.sh
#
# Or from daily_update script:
#   bash scripts/update_parallel_by_exchange.sh

SCRIPT_DIR="/Users/toan/dev/high-yield-dividend-analysis"
cd "$SCRIPT_DIR" || exit 1

PYTHON_CMD="python3"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

echo "============================================================================="
echo "🚀 PARALLEL UPDATE BY EXCHANGE GROUPS"
echo "============================================================================="
echo ""

# Create log files for each exchange group
NASDAQ_LOG="$LOG_DIR/update_nasdaq_${TIMESTAMP}.log"
NYSE_LOG="$LOG_DIR/update_nyse_${TIMESTAMP}.log"
OTHERS_LOG="$LOG_DIR/update_others_${TIMESTAMP}.log"

echo "📊 Starting parallel updates for 3 exchange groups..."
echo "  Group 1: NASDAQ exchanges"
echo "  Group 2: NYSE exchanges"
echo "  Group 3: Other exchanges"
echo ""

START_TIME=$(date +%s)

# Start Group 1: NASDAQ exchanges (largest group, ~50% of symbols)
echo "🔵 Starting NASDAQ group..."
$PYTHON_CMD -c "
from update_stock_v2 import StockDataPipeline
import logging
logging.basicConfig(level=logging.INFO)

pipeline = StockDataPipeline()
pipeline.run_update_by_exchange(
    exchange_groups=[['NASDAQ', 'NGM']],
    skip_recently_updated=True,
    staleness_hours=20
)
" > "$NASDAQ_LOG" 2>&1 &
NASDAQ_PID=$!

# Start Group 2: NYSE exchanges (~30% of symbols)
echo "🟢 Starting NYSE group..."
$PYTHON_CMD -c "
from update_stock_v2 import StockDataPipeline
import logging
logging.basicConfig(level=logging.INFO)

pipeline = StockDataPipeline()
pipeline.run_update_by_exchange(
    exchange_groups=[['NYSE', 'AMEX']],
    skip_recently_updated=True,
    staleness_hours=20
)
" > "$NYSE_LOG" 2>&1 &
NYSE_PID=$!

# Start Group 3: Other exchanges (~20% of symbols)
echo "🟡 Starting Other exchanges group..."
$PYTHON_CMD -c "
from update_stock_v2 import StockDataPipeline
import logging
logging.basicConfig(level=logging.INFO)

pipeline = StockDataPipeline()
pipeline.run_update_by_exchange(
    exchange_groups=[
        ['CBOE', 'BATS', 'BTS', 'BYX', 'BZX', 'EDGA', 'EDGX', 'PCX'],
        ['OTCM', 'OTCX'],
        ['TSX', 'TSXV', 'CSE', 'TSE']
    ],
    skip_recently_updated=True,
    staleness_hours=20
)
" > "$OTHERS_LOG" 2>&1 &
OTHERS_PID=$!

echo ""
echo "⏳ Waiting for all exchange groups to complete..."
echo "   Process IDs: NASDAQ=$NASDAQ_PID, NYSE=$NYSE_PID, OTHERS=$OTHERS_PID"
echo ""

# Wait for all processes
wait $NASDAQ_PID
NASDAQ_STATUS=$?
wait $NYSE_PID
NYSE_STATUS=$?
wait $OTHERS_PID
OTHERS_STATUS=$?

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "============================================================================="
echo "📊 PARALLEL UPDATE COMPLETE"
echo "============================================================================="
echo "Total time: ${MINUTES}m ${SECONDS}s"
echo ""
echo "Group Results:"

if [ $NASDAQ_STATUS -eq 0 ]; then
    echo "  ✅ NASDAQ: Success"
    echo "     Log: $NASDAQ_LOG"
else
    echo "  ❌ NASDAQ: Failed (exit code: $NASDAQ_STATUS)"
    echo "     Log: $NASDAQ_LOG"
fi

if [ $NYSE_STATUS -eq 0 ]; then
    echo "  ✅ NYSE: Success"
    echo "     Log: $NYSE_LOG"
else
    echo "  ❌ NYSE: Failed (exit code: $NYSE_STATUS)"
    echo "     Log: $NYSE_LOG"
fi

if [ $OTHERS_STATUS -eq 0 ]; then
    echo "  ✅ Others: Success"
    echo "     Log: $OTHERS_LOG"
else
    echo "  ❌ Others: Failed (exit code: $OTHERS_STATUS)"
    echo "     Log: $OTHERS_LOG"
fi

echo ""
echo "💡 Check individual logs for detailed results"
echo "============================================================================="

# Return success if at least one group succeeded
if [ $NASDAQ_STATUS -eq 0 ] || [ $NYSE_STATUS -eq 0 ] || [ $OTHERS_STATUS -eq 0 ]; then
    exit 0
else
    exit 1
fi
