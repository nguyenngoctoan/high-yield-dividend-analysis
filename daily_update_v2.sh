#!/bin/bash

# Daily Stock Data Update Script V2
# Uses the modular update_stock_v2.py pipeline
# Includes: discovery, prices, dividends, companies, holdings, and future dividends
# Designed for cron execution (recommended: daily at 10 PM EST)

# Set script directory and change to it
SCRIPT_DIR="/Users/toan/dev/high-yield-dividend-analysis"
cd "$SCRIPT_DIR" || exit 1

# Set up logging with timestamp
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily_update_v2_$(date '+%Y%m%d').log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "=================================================================================" >> "$LOG_FILE"
echo "🚀 DAILY STOCK DATA UPDATE V2 STARTED: $TIMESTAMP" >> "$LOG_FILE"
echo "=================================================================================" >> "$LOG_FILE"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
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
log_message "🐍 Activating virtual environment..."
source venv/bin/activate

# Track overall success
OVERALL_SUCCESS=true

# Step 1: Discovery (weekly - only run on Sundays)
if [ "$(date +%u)" -eq 7 ]; then
    log_message ""
    log_message "🔍 STEP 1: Symbol Discovery (Weekly)"
    log_message "📝 Command: python3 update_stock_v2.py --mode discover --validate"

    if python3 update_stock_v2.py --mode discover --validate >> "$LOG_FILE" 2>&1; then
        log_message "✅ Discovery completed"

        # Step 1b: Classify newly discovered ETFs
        log_message ""
        log_message "🏷️  STEP 1b: Classify New ETFs"
        log_message "📝 Command: python3 update_stock_v2.py --mode classify-etfs"

        if python3 update_stock_v2.py --mode classify-etfs >> "$LOG_FILE" 2>&1; then
            log_message "✅ ETF classification completed"
        else
            log_message "⚠️  ETF classification failed (non-critical)"
            # Don't set OVERALL_SUCCESS to false - this is non-critical
        fi
    else
        log_message "❌ Discovery failed"
        OVERALL_SUCCESS=false
    fi
    sleep 5
else
    log_message "⏭️  Skipping discovery (runs weekly on Sundays)"
fi

# Step 2: Update all data (prices, dividends, companies)
log_message ""
log_message "💰 STEP 2: Data Update (Prices, Dividends, Companies)"
log_message "📝 Command: python3 update_stock_v2.py --mode update"

if python3 update_stock_v2.py --mode update >> "$LOG_FILE" 2>&1; then
    log_message "✅ Data update completed"
else
    log_message "❌ Data update failed"
    OVERALL_SUCCESS=false
fi

sleep 5

# Step 3: Refresh NULL companies (only if needed)
log_message ""
log_message "🏢 STEP 3: Refresh NULL Company Data"
log_message "📝 Command: python3 update_stock_v2.py --mode refresh-companies --limit 100"

if python3 update_stock_v2.py --mode refresh-companies --limit 100 >> "$LOG_FILE" 2>&1; then
    log_message "✅ Company refresh completed"
else
    log_message "⚠️  Company refresh had issues (non-critical)"
    # Don't set OVERALL_SUCCESS to false - this is non-critical
fi

sleep 5

# Step 4: Update ETF Holdings (daily)
log_message ""
log_message "📊 STEP 4: ETF Holdings Update (Daily)"
log_message "📝 Command: python3 update_stock_v2.py --mode update-holdings"

if python3 update_stock_v2.py --mode update-holdings >> "$LOG_FILE" 2>&1; then
    log_message "✅ Holdings update completed"
else
    log_message "⚠️  Holdings update failed (non-critical)"
    # Don't set OVERALL_SUCCESS to false - this is non-critical
fi

sleep 5

# Step 5: Future Dividends (daily)
log_message ""
log_message "🔮 STEP 5: Future Dividends Calendar"
log_message "📝 Command: python3 update_stock_v2.py --mode future-dividends --days-ahead 90"

if python3 update_stock_v2.py --mode future-dividends --days-ahead 90 >> "$LOG_FILE" 2>&1; then
    log_message "✅ Future dividends updated"
else
    log_message "⚠️  Future dividends failed (non-critical)"
    # Don't set OVERALL_SUCCESS to false - this is non-critical
fi

sleep 5

# Step 6: Database Backup (daily)
log_message ""
log_message "💾 STEP 6: Database Backup"
log_message "📝 Command: $SCRIPT_DIR/scripts/backup_database.sh"

if "$SCRIPT_DIR/scripts/backup_database.sh" >> "$LOG_FILE" 2>&1; then
    log_message "✅ Database backup completed"
else
    log_message "⚠️  Database backup failed (non-critical)"
    # Don't set OVERALL_SUCCESS to false - this is non-critical
fi

# Database Status Report
log_message ""
log_message "📊 DATABASE STATUS REPORT"
log_message "============================================================"

python3 -c "
from supabase_helpers import get_supabase_client
import logging
logging.basicConfig(level=logging.ERROR)

try:
    supabase = get_supabase_client()

    # Total symbols
    result = supabase.table('raw_stocks').select('symbol', count='exact').execute()
    print(f'📈 Total symbols: {result.count:,}')

    # Symbols with data
    with_prices = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('price', 'null').execute()
    print(f'💰 Symbols with prices: {with_prices.count:,}')

    with_dividends = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('dividend_yield', 'null').execute()
    print(f'💵 Symbols with dividend data: {with_dividends.count:,}')

    with_companies = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('company', 'null').execute()
    print(f'🏢 Symbols with company info: {with_companies.count:,}')

    with_sectors = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('sector', 'null').execute()
    print(f'🏭 Symbols with sector data: {with_sectors.count:,}')

    with_holdings = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('holdings', 'null').execute()
    print(f'📊 ETFs with holdings: {with_holdings.count:,}')

    # Excluded symbols
    excluded = supabase.table('raw_excluded_symbols').select('symbol', count='exact').execute()
    print(f'❌ Excluded symbols: {excluded.count:,}')

except Exception as e:
    print(f'❌ Error: {e}')
" 2>&1 | tee -a "$LOG_FILE"

# Completion
log_message ""
log_message "============================================================"
COMPLETION_TIME=$(date '+%Y-%m-%d %H:%M:%S')

if [ "$OVERALL_SUCCESS" = true ]; then
    log_message "🎉 DAILY UPDATE COMPLETED SUCCESSFULLY: $COMPLETION_TIME"
    EXIT_CODE=0
else
    log_message "⚠️  DAILY UPDATE COMPLETED WITH ERRORS: $COMPLETION_TIME"
    EXIT_CODE=1
fi

log_message "================================================================================="

# Log file management
log_message "📝 Log saved to: $LOG_FILE"

# Clean up old logs (keep last 14 days to match backup retention)
log_message "🧹 Cleaning up old log files..."
DELETED_LOGS=$(find "$LOG_DIR" -name "*.log" -mtime +14 -delete -print 2>/dev/null | wc -l | xargs)
if [ "$DELETED_LOGS" -gt 0 ]; then
    log_message "✅ Deleted $DELETED_LOGS old log file(s)"
else
    log_message "✅ No old logs to clean up"
fi

exit $EXIT_CODE
