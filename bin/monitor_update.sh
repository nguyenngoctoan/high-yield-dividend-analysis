#!/bin/bash
#
# Daily Update Monitor Script
# Shows real-time progress of the daily update process
#

LOG_FILE="logs/daily_update_v3_$(date '+%Y%m%d').log"

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "💡 The daily update may not be running yet"
    exit 1
fi

# Clear screen for clean display
clear

echo "================================================================================"
echo "📊 DAILY UPDATE MONITOR"
echo "================================================================================"
echo ""
echo "Log file: $LOG_FILE"
echo "Last updated: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check if update is still running
if pgrep -f "daily_update_v3_parallel.sh" > /dev/null; then
    echo "Status: 🟢 RUNNING"
else
    echo "Status: ⚪ COMPLETED or NOT RUNNING"
fi

echo ""
echo "================================================================================"
echo "📈 CURRENT PROGRESS"
echo "================================================================================"
echo ""

# Extract key progress indicators
START_TIME=$(grep "STARTED:" "$LOG_FILE" | tail -1 | cut -d' ' -f6)
CURRENT_TIME=$(date '+%H:%M:%S')

if [ ! -z "$START_TIME" ]; then
    echo "⏰ Started: $START_TIME"
    echo "⏰ Current: $CURRENT_TIME"
    echo ""
fi

# Phase 1 Status
echo "🔄 PHASE 1: Parallel Web Scraping"
if grep -q "All scrapers completed" "$LOG_FILE" 2>/dev/null; then
    PHASE1_TIME=$(grep "All scrapers completed in" "$LOG_FILE" | tail -1 | awk '{print $6}')
    echo "   ✅ Complete in ${PHASE1_TIME}"

    # Show scraper results
    echo ""
    echo "   Scraper Results:"
    grep -A 20 "SCRAPER RESULTS:" "$LOG_FILE" | grep -E "✅|⚠️" | tail -5
else
    echo "   ⏳ In progress..."
fi

echo ""

# Step 2 Status
echo "💰 STEP 2: Main Data Update"
if grep -q "STALENESS FILTER" "$LOG_FILE" 2>/dev/null; then
    STALENESS_INFO=$(grep "STALENESS FILTER" "$LOG_FILE" | tail -1)
    echo "   $STALENESS_INFO"
fi

# Check current processing step
if grep -q "Processing prices:" "$LOG_FILE" 2>/dev/null; then
    PRICE_PROGRESS=$(grep "Processing prices:" "$LOG_FILE" | tail -1 | grep -oP '\d+%' | head -1)
    PRICE_SYMBOLS=$(grep "Processing prices:" "$LOG_FILE" | tail -1 | grep -oP '\d+/\d+' | head -1)
    if [ ! -z "$PRICE_PROGRESS" ]; then
        echo "   📊 Price updates: $PRICE_PROGRESS ($PRICE_SYMBOLS symbols)"
    fi
elif grep -q "Processing dividends:" "$LOG_FILE" 2>/dev/null; then
    echo "   💵 Processing dividends..."
elif grep -q "Processing company info:" "$LOG_FILE" 2>/dev/null; then
    echo "   🏢 Processing company info..."
elif grep -q "Data update completed" "$LOG_FILE" 2>/dev/null; then
    STEP2_TIME=$(grep "Data update completed in" "$LOG_FILE" | tail -1 | awk '{print $6}')
    echo "   ✅ Complete in ${STEP2_TIME}"
else
    echo "   ⏳ Waiting to start..."
fi

echo ""

# Phase 2 Status
echo "🔄 PHASE 2: Parallel Post-Update Tasks"
if grep -q "All tasks completed" "$LOG_FILE" 2>/dev/null; then
    PHASE2_TIME=$(grep "All tasks completed in" "$LOG_FILE" | tail -1 | awk '{print $6}')
    echo "   ✅ Complete in ${PHASE2_TIME}"
else
    echo "   ⏳ Waiting or in progress..."
fi

echo ""

# Final Status
if grep -q "DAILY UPDATE COMPLETED" "$LOG_FILE" 2>/dev/null; then
    echo "================================================================================"
    echo "✅ UPDATE COMPLETE!"
    echo "================================================================================"
    echo ""

    TOTAL_TIME=$(grep "Total execution time:" "$LOG_FILE" | tail -1 | awk '{print $4, $5}')
    echo "⏱️  Total execution time: $TOTAL_TIME"
    echo ""

    # Show summary
    echo "📊 Summary:"
    grep -A 5 "UPDATE METRICS:" "$LOG_FILE" | tail -5
fi

echo ""
echo "================================================================================"
echo "⚡ OPTIMIZATION STATS"
echo "================================================================================"
echo ""

# Check for optimization messages
if grep -q "Estimated time saved:" "$LOG_FILE" 2>/dev/null; then
    TIME_SAVED=$(grep "Estimated time saved:" "$LOG_FILE" | tail -1)
    echo "$TIME_SAVED"
fi

# Show recent errors (if any)
ERROR_COUNT=$(grep -c "❌\|ERROR" "$LOG_FILE" 2>/dev/null || echo "0")
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo ""
    echo "⚠️  Errors detected: $ERROR_COUNT"
    echo "   Recent errors:"
    grep "❌\|ERROR" "$LOG_FILE" | tail -3 | sed 's/^/   /'
fi

echo ""
echo "================================================================================"
echo ""
echo "💡 Commands:"
echo "   Watch live:     tail -f $LOG_FILE"
echo "   Refresh:        ./monitor_update.sh"
echo "   Full log:       cat $LOG_FILE"
echo "   Last 50 lines:  tail -50 $LOG_FILE"
echo ""

# Auto-refresh option
if [ "$1" == "--watch" ] || [ "$1" == "-w" ]; then
    echo "🔄 Auto-refreshing every 10 seconds... (Press Ctrl+C to stop)"
    echo ""
    sleep 10
    exec "$0" "$@"
fi

echo "💡 Tip: Run with --watch for auto-refresh"
echo ""
