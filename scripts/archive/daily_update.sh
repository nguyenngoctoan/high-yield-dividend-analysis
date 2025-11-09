#!/bin/bash

# Daily Stock Data Update Script
# Runs the update_stock.py with discovery and validation
# Designed for cron execution at 10 PM EST daily

# Set script directory and change to it
SCRIPT_DIR="/Users/toan/dev/high-yield-dividend-analysis"
cd "$SCRIPT_DIR" || exit 1

# Set up logging with timestamp
LOG_FILE="$SCRIPT_DIR/daily_update.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S EST')

echo "=================================================================================" >> "$LOG_FILE"
echo "🚀 DAILY STOCK DATA UPDATE STARTED: $TIMESTAMP" >> "$LOG_FILE"
echo "=================================================================================" >> "$LOG_FILE"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo "$1"
}

# Supabase project directory
SUPABASE_PROJECT_DIR="/Users/toan/dev/ai-dividend-tracker"

# Function to check if Supabase is running
check_supabase_running() {
    cd "$SUPABASE_PROJECT_DIR" || return 1
    # Check if Supabase status command returns successfully
    if npx supabase status >/dev/null 2>&1; then
        cd "$SCRIPT_DIR"
        return 0
    fi
    cd "$SCRIPT_DIR"
    return 1
}

# Function to start Supabase
start_supabase() {
    log_message "🚀 Starting Supabase..."
    cd "$SUPABASE_PROJECT_DIR" || return 1

    if npx supabase start >> "$LOG_FILE" 2>&1; then
        log_message "✅ Supabase started successfully"
        cd "$SCRIPT_DIR"
        return 0
    else
        log_message "❌ Failed to start Supabase"
        cd "$SCRIPT_DIR"
        return 1
    fi
}

# Function to check if Supabase is healthy
check_supabase_health() {
    cd "$SUPABASE_PROJECT_DIR" || return 1

    # Use Supabase CLI to check status
    local status_output=$(npx supabase status 2>&1)

    # Check if the status indicates it's running
    if echo "$status_output" | grep -q "supabase local development setup is running"; then
        cd "$SCRIPT_DIR"
        return 0
    fi

    cd "$SCRIPT_DIR"
    return 1
}

# Check Supabase status
log_message "🔍 Checking Supabase status..."
if ! check_supabase_running; then
    log_message "⚠️ Supabase is not running"
    if ! start_supabase; then
        log_message "❌ Failed to start Supabase - exiting"
        exit 1
    fi
else
    log_message "✅ Supabase is running"
fi

# Wait for Supabase to be fully ready
log_message "🏥 Verifying Supabase is ready..."
max_attempts=10
attempt=1
wait_time=2

while [ $attempt -le $max_attempts ]; do
    if check_supabase_health; then
        log_message "✅ Supabase is ready"
        break
    fi
    log_message "⏳ Waiting for Supabase (attempt $attempt/$max_attempts, ${wait_time}s)..."
    sleep $wait_time
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    log_message "⚠️ Supabase may not be fully ready, but continuing..."
fi

# Activate virtual environment
source venv/bin/activate

# Run the discovery update first
log_message "🔍 Step 1: Starting symbol discovery and validation..."
log_message "📝 Command: python update_stock.py --mode discover"

if python update_stock.py --mode discover >> "$LOG_FILE" 2>&1; then
    log_message "✅ Symbol discovery completed successfully"
else
    log_message "❌ Symbol discovery failed"
    exit 1
fi

# Wait a moment between runs
sleep 5

# Run the price update
log_message "💰 Step 2: Starting price update for all symbols..."
log_message "📝 Command: python update_stock.py --mode prices"

if python update_stock.py --mode prices >> "$LOG_FILE" 2>&1; then
    log_message "✅ Price update completed successfully"
else
    log_message "❌ Price update failed"
    exit 1
fi

# Wait a moment between runs
sleep 5

# Run the dividend update
log_message "💵 Step 3: Starting dividend update for all symbols..."
log_message "📝 Command: python update_stock.py --mode dividends"

if python update_stock.py --mode dividends >> "$LOG_FILE" 2>&1; then
    log_message "✅ Dividend update completed successfully"
else
    log_message "❌ Dividend update failed"
    exit 1
fi

# Wait a moment between runs
sleep 5

# Run the stock splits update (only for recently added stocks to save time)
log_message "📊 Step 4: Starting stock splits update (recent stocks only)..."
log_message "📝 Command: python fetch_stock_splits.py --recent-only --workers 10"

if python fetch_stock_splits.py --recent-only --workers 10 >> "$LOG_FILE" 2>&1; then
    log_message "✅ Stock splits update completed successfully"
else
    log_message "⚠️  Stock splits update failed (non-critical, continuing)"
    # Don't exit - this is non-critical
fi

# Database Status Report
log_message "📊 Generating Database Status Report"
source venv/bin/activate
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase = create_client(url, key)

try:
    result = supabase.table('raw_stocks').select('symbol', count='exact').execute()
    print(f'📊 Final Database Status:')
    print(f'   ✅ Total symbols in database: {result.count:,}')

    excluded_result = supabase.table('raw_stocks_excluded').select('symbol', count='exact').execute()
    print(f'   ❌ Excluded symbols: {excluded_result.count:,}')

    # Stock splits stats
    try:
        splits_result = supabase.table('raw_stock_splits').select('symbol', count='exact').execute()
        unique_symbols = len(set(split['symbol'] for split in splits_result.data)) if splits_result.data else 0
        print(f'   📊 Total stock splits: {splits_result.count:,} ({unique_symbols:,} unique symbols)')
    except:
        pass
except Exception as e:
    print(f'❌ Error getting database status: {e}')
" >> "$LOG_FILE" 2>&1

# Completion
COMPLETION_TIME=$(date '+%Y-%m-%d %H:%M:%S EST')
log_message "🎉 DAILY UPDATE COMPLETED: $COMPLETION_TIME"
log_message "================================================================================="

# Rotate log file if it gets too large (keep last 2000 lines)
if [ -f "$LOG_FILE" ] && [ $(wc -l < "$LOG_FILE") -gt 2000 ]; then
    tail -2000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi

echo "Daily update completed. Check $LOG_FILE for details."
