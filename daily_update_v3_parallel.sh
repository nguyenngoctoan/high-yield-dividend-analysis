#!/bin/bash

# Daily Stock Data Update Script V3 - Optimized with Parallel Execution
# Uses the modular update_stock_v2.py pipeline
# Includes: discovery, prices, dividends, companies, holdings, and future dividends
# NEW: Parallelized web scrapers and post-update tasks for faster execution
# Designed for cron execution (recommended: daily at 10 PM EST)

# Set script directory and change to it
SCRIPT_DIR="/Users/toan/dev/high-yield-dividend-analysis"
cd "$SCRIPT_DIR" || exit 1

# Set up logging with timestamp
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily_update_v3_$(date '+%Y%m%d').log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Lock file to prevent concurrent runs
LOCK_FILE="$SCRIPT_DIR/.daily_update.lock"
PID_FILE="$SCRIPT_DIR/.daily_update.pid"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to cleanup lock files on exit
cleanup_lock() {
    if [ -f "$LOCK_FILE" ]; then
        rm -f "$LOCK_FILE"
    fi
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
    fi
}

# Set trap to cleanup on exit
trap cleanup_lock EXIT INT TERM

# Check if another instance is already running
if [ -f "$LOCK_FILE" ]; then
    # Check if the PID is still running
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            # Check if it's actually our script
            if ps -p "$OLD_PID" -o command= | grep -q "daily_update_v3_parallel.sh"; then
                echo "=================================================================================" >> "$LOG_FILE"
                echo "⚠️  DAILY UPDATE ALREADY RUNNING" >> "$LOG_FILE"
                echo "=================================================================================" >> "$LOG_FILE"
                log_message "Another instance is already running (PID: $OLD_PID)"
                log_message "Lock file: $LOCK_FILE"
                log_message "If this is incorrect, remove the lock file manually:"
                log_message "  rm $LOCK_FILE $PID_FILE"
                log_message ""
                log_message "Exiting to prevent concurrent runs..."
                echo "=================================================================================" >> "$LOG_FILE"
                exit 0
            else
                # Stale lock file (PID exists but different process)
                log_message "⚠️  Stale lock file detected (PID $OLD_PID is different process)"
                log_message "Removing stale lock and continuing..."
                rm -f "$LOCK_FILE" "$PID_FILE"
            fi
        else
            # Stale lock file (PID doesn't exist)
            log_message "⚠️  Stale lock file detected (PID $OLD_PID not running)"
            log_message "Removing stale lock and continuing..."
            rm -f "$LOCK_FILE" "$PID_FILE"
        fi
    else
        # Lock file exists but no PID file - remove stale lock
        log_message "⚠️  Stale lock file detected (no PID file)"
        log_message "Removing stale lock and continuing..."
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock file with current PID
echo $$ > "$PID_FILE"
touch "$LOCK_FILE"

echo "=================================================================================" >> "$LOG_FILE"
echo "🚀 DAILY STOCK DATA UPDATE V3 (PARALLEL) STARTED: $TIMESTAMP" >> "$LOG_FILE"
echo "=================================================================================" >> "$LOG_FILE"
log_message "Process ID: $$"
log_message "Lock file created: $LOCK_FILE"
log_message ""

# Set Python command
PYTHON_CMD="python3"

# OPTIMIZATION: Check market hours and recommend optimal run time
log_message "🕐 Checking market hours..."
$PYTHON_CMD -c "
from lib.utils.market_hours import MarketHours
from datetime import datetime
import sys

should_run, reason = MarketHours.should_run_daily_update()
status = MarketHours.get_market_status()

print(f'Market Status: {status}')
print(f'Current Time: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')

if should_run:
    print(f'✅ Recommendation: {reason}')
    sys.exit(0)
else:
    print(f'⚠️  Recommendation: Skip - {reason}')
    print(f'💡 Daily updates work best when run after market close (6 PM - 11 PM EST)')
    print(f'💡 To force running during market hours, set FORCE_RUN=true')
    sys.exit(1)
" 2>&1 | tee -a "$LOG_FILE"

MARKET_CHECK_STATUS=$?

# Allow override via environment variable
if [ "$FORCE_RUN" != "true" ] && [ $MARKET_CHECK_STATUS -ne 0 ]; then
    log_message "⏸️  Skipping daily update based on market hours check"
    log_message "💡 To force running, set environment variable: FORCE_RUN=true"
    exit 0
fi

if [ "$FORCE_RUN" = "true" ]; then
    log_message "⚠️  FORCE_RUN=true - proceeding despite market hours check"
fi

# Verify Supabase connectivity
log_message "🔍 Verifying Supabase connectivity..."
if $PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()
    result = supabase.table('raw_stocks').select('symbol', count='exact').limit(1).execute()
    print('✅ Connected to Supabase')
    exit(0)
except Exception as e:
    print(f'❌ Failed to connect to Supabase: {e}')
    exit(1)
" 2>&1 | tee -a "$LOG_FILE"; then
    log_message "✅ Supabase is accessible"
else
    log_message "❌ Failed to connect to Supabase - exiting"
    log_message "💡 Check your .env configuration"
    exit 1
fi

# Load environment variables from .env file
if [ -f "$SCRIPT_DIR/.env" ]; then
    log_message "🔑 Loading environment variables from .env..."
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
else
    log_message "⚠️  .env file not found at $SCRIPT_DIR/.env"
fi

# Track overall success and timing
OVERALL_SUCCESS=true
SCRIPT_START_TIME=$(date +%s)

# Track errors by severity
declare -a CRITICAL_ERRORS
declare -a WARNING_ERRORS
declare -a INFO_MESSAGES

# Capture before-state metrics
log_message ""
log_message "📊 BEFORE STATE SNAPSHOT"
log_message "============================================================"
$PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()
    total = supabase.table('raw_stocks').select('symbol', count='exact').execute()
    with_prices = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('price', 'null').execute()
    with_dividends = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('dividend_yield', 'null').execute()
    print(f'Total symbols: {total.count:,}')
    print(f'Symbols with prices: {with_prices.count:,}')
    print(f'Symbols with dividends: {with_dividends.count:,}')
except: pass
" 2>&1 | tee -a "$LOG_FILE"

# Step 1: Discovery (weekly - only run on Sundays)
if [ "$(date +%u)" -eq 7 ]; then
    log_message ""
    log_message "🔍 STEP 1: Symbol Discovery (Weekly)"
    log_message "============================================================"
    log_message "📝 Command: $PYTHON_CMD update_stock_v2.py --mode discover --validate"

    if $PYTHON_CMD update_stock_v2.py --mode discover --validate >> "$LOG_FILE" 2>&1; then
        log_message "✅ Discovery completed"

        # Discovery metrics
        log_message ""
        log_message "📈 DISCOVERY METRICS:"
        $PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()

    # Get newly discovered symbols (those with recent created_at)
    from datetime import datetime, timedelta
    cutoff = (datetime.now() - timedelta(hours=2)).isoformat()
    new_symbols = supabase.table('raw_stocks').select('symbol, exchange, type').gte('created_at', cutoff).execute()

    if new_symbols.data:
        print(f'  🆕 New symbols discovered: {len(new_symbols.data)}')
        # Group by type
        types = {}
        for s in new_symbols.data:
            t = s.get('type', 'unknown')
            types[t] = types.get(t, 0) + 1
        for t, count in sorted(types.items()):
            print(f'     - {t}: {count}')
        # Show sample
        print(f'  📋 Sample new symbols: {', '.join([s['symbol'] for s in new_symbols.data[:10]])}')
    else:
        print(f'  ℹ️  No new symbols discovered in this run')
except Exception as e:
    print(f'  ⚠️  Could not fetch discovery metrics: {e}')
" 2>&1 | tee -a "$LOG_FILE"

        # Step 1b: Classify newly discovered ETFs
        log_message ""
        log_message "🏷️  STEP 1b: Classify New ETFs"
        log_message "📝 Command: $PYTHON_CMD update_stock_v2.py --mode classify-etfs"

        if $PYTHON_CMD update_stock_v2.py --mode classify-etfs >> "$LOG_FILE" 2>&1; then
            log_message "✅ ETF classification completed"
        else
            log_message "⚠️  ETF classification failed (non-critical)"
        fi

    else
        log_message "❌ Discovery failed"
        OVERALL_SUCCESS=false
    fi
    sleep 5
else
    log_message "⏭️  Skipping discovery (runs weekly on Sundays)"
fi

# ============================================================================
# PHASE 1: PARALLEL WEB SCRAPING
# All web scrapers are independent and write to different tables
# Run them in parallel to save time
# ============================================================================

log_message ""
log_message "🔄 PHASE 1: PARALLEL WEB SCRAPING"
log_message "============================================================"
log_message "Running 5 scrapers in parallel..."
log_message ""

# Create temporary files for each scraper's output
YIELDMAX_LOG="$LOG_DIR/yieldmax_$(date '+%Y%m%d').log"
CBOE_LOG="$LOG_DIR/cboe_$(date '+%Y%m%d').log"
NASDAQ_LOG="$LOG_DIR/nasdaq_$(date '+%Y%m%d').log"
NYSE_LOG="$LOG_DIR/nyse_$(date '+%Y%m%d').log"
SNOWBALL_LOG="$LOG_DIR/snowball_$(date '+%Y%m%d').log"

# Start all scrapers in parallel
PHASE1_START=$(date +%s)

log_message "📰 Starting YieldMax scraper..."
$PYTHON_CMD scripts/scrape_yieldmax.py > "$YIELDMAX_LOG" 2>&1 &
YIELDMAX_PID=$!

log_message "📰 Starting CBOE scraper..."
$PYTHON_CMD scripts/scrape_cboe_dividends.py --years "$(date +%Y)" > "$CBOE_LOG" 2>&1 &
CBOE_PID=$!

log_message "📰 Starting NASDAQ scraper..."
$PYTHON_CMD scripts/scrape_nasdaq_dividends.py --auto-continue > "$NASDAQ_LOG" 2>&1 &
NASDAQ_PID=$!

log_message "📰 Starting NYSE scraper..."
$PYTHON_CMD scripts/scrape_nyse_dividends.py --auto-continue > "$NYSE_LOG" 2>&1 &
NYSE_PID=$!

log_message "📰 Starting Snowball scraper..."
$PYTHON_CMD scripts/scrape_snowball_dividends.py --category us-popular-div > "$SNOWBALL_LOG" 2>&1 &
SNOWBALL_PID=$!

log_message ""
log_message "⏳ Waiting for all scrapers to complete..."
log_message ""

# Monitor scraper progress while waiting
while ps -p $YIELDMAX_PID > /dev/null 2>&1 || \
      ps -p $CBOE_PID > /dev/null 2>&1 || \
      ps -p $NASDAQ_PID > /dev/null 2>&1 || \
      ps -p $NYSE_PID > /dev/null 2>&1 || \
      ps -p $SNOWBALL_PID > /dev/null 2>&1; do

    # Show progress from each scraper
    log_message "📊 Scraper Progress Update:"

    # YieldMax
    if ps -p $YIELDMAX_PID > /dev/null 2>&1; then
        YIELDMAX_LAST=$(tail -1 "$YIELDMAX_LOG" 2>/dev/null | grep -E "✅|🔍|📰|Found|Scraping|Processing" || echo "Running...")
        log_message "  📰 YieldMax: $YIELDMAX_LAST"
    else
        log_message "  ✅ YieldMax: Complete"
    fi

    # CBOE
    if ps -p $CBOE_PID > /dev/null 2>&1; then
        CBOE_LAST=$(tail -1 "$CBOE_LOG" 2>/dev/null | grep -E "✅|🔍|📰|Found|Scraping|Processing" || echo "Running...")
        log_message "  📰 CBOE: $CBOE_LAST"
    else
        log_message "  ✅ CBOE: Complete"
    fi

    # NASDAQ
    if ps -p $NASDAQ_PID > /dev/null 2>&1; then
        NASDAQ_LAST=$(tail -1 "$NASDAQ_LOG" 2>/dev/null | grep -E "✅|🔍|📰|Found|Scraping|Processing" || echo "Running...")
        log_message "  📰 NASDAQ: $NASDAQ_LAST"
    else
        log_message "  ✅ NASDAQ: Complete"
    fi

    # NYSE
    if ps -p $NYSE_PID > /dev/null 2>&1; then
        NYSE_LAST=$(tail -1 "$NYSE_LOG" 2>/dev/null | grep -E "✅|🔍|📰|Found|Scraping|Processing" || echo "Running...")
        log_message "  📰 NYSE: $NYSE_LAST"
    else
        log_message "  ✅ NYSE: Complete"
    fi

    # Snowball
    if ps -p $SNOWBALL_PID > /dev/null 2>&1; then
        SNOWBALL_LAST=$(tail -1 "$SNOWBALL_LOG" 2>/dev/null | grep -E "✅|🔍|📰|Found|Scraping|Processing" || echo "Running...")
        log_message "  📰 Snowball: $SNOWBALL_LAST"
    else
        log_message "  ✅ Snowball: Complete"
    fi

    log_message ""
    sleep 10  # Update every 10 seconds
done

# Wait for all scrapers and track their success
wait $YIELDMAX_PID
YIELDMAX_STATUS=$?
wait $CBOE_PID
CBOE_STATUS=$?
wait $NASDAQ_PID
NASDAQ_STATUS=$?
wait $NYSE_PID
NYSE_STATUS=$?
wait $SNOWBALL_PID
SNOWBALL_STATUS=$?

PHASE1_END=$(date +%s)
PHASE1_DURATION=$((PHASE1_END - PHASE1_START))

log_message ""
log_message "✅ All scrapers completed in ${PHASE1_DURATION}s"
log_message ""

# Report scraper results
log_message "📊 SCRAPER RESULTS:"
if [ $YIELDMAX_STATUS -eq 0 ]; then
    log_message "  ✅ YieldMax: Success"
    cat "$YIELDMAX_LOG" >> "$LOG_FILE"
else
    log_message "  ⚠️  YieldMax: Failed (non-critical)"
fi

if [ $CBOE_STATUS -eq 0 ]; then
    log_message "  ✅ CBOE: Success"
    cat "$CBOE_LOG" >> "$LOG_FILE"
else
    log_message "  ⚠️  CBOE: Failed (non-critical)"
fi

if [ $NASDAQ_STATUS -eq 0 ]; then
    log_message "  ✅ NASDAQ: Success"
    cat "$NASDAQ_LOG" >> "$LOG_FILE"
else
    log_message "  ⚠️  NASDAQ: Failed (non-critical)"
fi

if [ $NYSE_STATUS -eq 0 ]; then
    log_message "  ✅ NYSE: Success"
    cat "$NYSE_LOG" >> "$LOG_FILE"
else
    log_message "  ⚠️  NYSE: Failed (non-critical)"
fi

if [ $SNOWBALL_STATUS -eq 0 ]; then
    log_message "  ✅ Snowball: Success"
    cat "$SNOWBALL_LOG" >> "$LOG_FILE"
else
    log_message "  ⚠️  Snowball: Failed (non-critical)"
fi

log_message ""

# ============================================================================
# STEP 2: MAIN DATA UPDATE (PRICES, DIVIDENDS, COMPANIES)
# This is the critical path - must complete before Phase 2
# ============================================================================

log_message ""
log_message "💰 STEP 2: Main Data Update (Prices, Dividends, Companies)"
log_message "============================================================"
log_message "📝 Command: $PYTHON_CMD update_stock_v2.py --mode update"

STEP2_START=$(date +%s)

if $PYTHON_CMD update_stock_v2.py --mode update >> "$LOG_FILE" 2>&1; then
    STEP2_END=$(date +%s)
    STEP2_DURATION=$((STEP2_END - STEP2_START))
    log_message "✅ Data update completed in ${STEP2_DURATION}s"

    # Detailed update metrics
    log_message ""
    log_message "📊 UPDATE METRICS:"
    $PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
from datetime import datetime, timedelta
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()

    # Price updates
    cutoff = (datetime.now() - timedelta(hours=2)).isoformat()
    recent_prices = supabase.table('raw_stock_prices').select('symbol', count='exact').gte('updated_at', cutoff).execute()
    print(f'  💰 Price records updated: {recent_prices.count:,}')

    # Get unique symbols with recent price updates
    recent_price_symbols = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('price', 'null').gte('updated_at', cutoff).execute()
    print(f'  📈 Symbols with new prices: {recent_price_symbols.count:,}')

    # Dividend updates
    stocks_with_div = supabase.table('raw_stocks').select('symbol, dividend_yield', count='exact').not_.is_('dividend_yield', 'null').gte('updated_at', cutoff).execute()
    print(f'  💵 Symbols with dividend updates: {stocks_with_div.count:,}')

    # Show top dividend yields updated
    if stocks_with_div.data:
        sorted_divs = sorted(stocks_with_div.data, key=lambda x: float(x.get('dividend_yield', 0) or 0), reverse=True)[:5]
        print(f'  🏆 Top 5 dividend yields updated:')
        for s in sorted_divs:
            dy = float(s.get('dividend_yield', 0) or 0)
            print(f'     - {s[\"symbol\"]}: {dy:.2f}%')

    # Company data updates
    company_updates = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('company', 'null').gte('updated_at', cutoff).execute()
    print(f'  🏢 Company info updated: {company_updates.count:,}')

    # Historical dividend records
    div_history = supabase.table('raw_dividends').select('symbol', count='exact').gte('updated_at', cutoff).execute()
    print(f'  📜 Historical dividend records: {div_history.count:,}')

    # Current totals
    print(f'')
    print(f'  📊 Current Database Totals:')
    total = supabase.table('raw_stocks').select('symbol', count='exact').execute()
    with_prices = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('price', 'null').execute()
    with_divs = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('dividend_yield', 'null').execute()
    print(f'     Total symbols: {total.count:,}')
    print(f'     With prices: {with_prices.count:,} ({100*with_prices.count/total.count:.1f}%)')
    print(f'     With dividends: {with_divs.count:,} ({100*with_divs.count/total.count:.1f}%)')

    # Data quality checks
    price_pct = 100*with_prices.count/total.count
    div_pct = 100*with_divs.count/total.count

    if price_pct < 50:
        print(f'EXIT_CODE:CRITICAL:Less than 50% of symbols have price data ({price_pct:.1f}%)')
    elif price_pct < 80:
        print(f'EXIT_CODE:WARNING:Price data coverage below 80% ({price_pct:.1f}%)')

    if div_pct < 30:
        print(f'EXIT_CODE:WARNING:Dividend data coverage below 30% ({div_pct:.1f}%)')

except Exception as e:
    print(f'  ⚠️  Could not fetch update metrics: {e}')
    print(f'EXIT_CODE:WARNING:Failed to fetch update metrics')
" 2>&1 | tee -a "$LOG_FILE" | while IFS=: read -r prefix severity message; do
    if [ "$prefix" = "EXIT_CODE" ]; then
        if [ "$severity" = "CRITICAL" ]; then
            CRITICAL_ERRORS+=("Step 2: $message")
        elif [ "$severity" = "WARNING" ]; then
            WARNING_ERRORS+=("Step 2: $message")
        fi
    fi
done

else
    log_message "❌ Data update failed"
    OVERALL_SUCCESS=false
fi

# ============================================================================
# PHASE 2: PARALLEL POST-UPDATE TASKS
# After main update completes, these tasks are independent and can run in parallel
# ============================================================================

log_message ""
log_message "🔄 PHASE 2: PARALLEL POST-UPDATE TASKS"
log_message "============================================================"
log_message "Running 4 tasks in parallel..."
log_message ""

# Create temporary files for each task's output
COMPANIES_LOG="$LOG_DIR/companies_$(date '+%Y%m%d').log"
HOLDINGS_LOG="$LOG_DIR/holdings_$(date '+%Y%m%d').log"
FUTURE_DIV_LOG="$LOG_DIR/future_div_$(date '+%Y%m%d').log"
BACKUP_LOG="$LOG_DIR/backup_$(date '+%Y%m%d').log"

# Start all tasks in parallel
PHASE2_START=$(date +%s)

log_message "🏢 Starting company data refresh..."
$PYTHON_CMD update_stock_v2.py --mode refresh-companies --limit 100 > "$COMPANIES_LOG" 2>&1 &
COMPANIES_PID=$!

log_message "📊 Starting ETF holdings update..."
$PYTHON_CMD update_stock_v2.py --mode update-holdings > "$HOLDINGS_LOG" 2>&1 &
HOLDINGS_PID=$!

log_message "🔮 Starting future dividends update..."
$PYTHON_CMD update_stock_v2.py --mode future-dividends --days-ahead 90 > "$FUTURE_DIV_LOG" 2>&1 &
FUTURE_DIV_PID=$!

log_message "💾 Starting database backup..."
"$SCRIPT_DIR/scripts/backup_database.sh" > "$BACKUP_LOG" 2>&1 &
BACKUP_PID=$!

log_message ""
log_message "⏳ Waiting for all tasks to complete..."

# Wait for all tasks and track their success
wait $COMPANIES_PID
COMPANIES_STATUS=$?
wait $HOLDINGS_PID
HOLDINGS_STATUS=$?
wait $FUTURE_DIV_PID
FUTURE_DIV_STATUS=$?
wait $BACKUP_PID
BACKUP_STATUS=$?

PHASE2_END=$(date +%s)
PHASE2_DURATION=$((PHASE2_END - PHASE2_START))

log_message ""
log_message "✅ All tasks completed in ${PHASE2_DURATION}s"
log_message ""

# Report task results
log_message "📊 TASK RESULTS:"

if [ $COMPANIES_STATUS -eq 0 ]; then
    log_message "  ✅ Company refresh: Success"
    cat "$COMPANIES_LOG" >> "$LOG_FILE"
else
    log_message "  ⚠️  Company refresh: Failed (non-critical)"
fi

if [ $HOLDINGS_STATUS -eq 0 ]; then
    log_message "  ✅ ETF holdings: Success"
    cat "$HOLDINGS_LOG" >> "$LOG_FILE"
else
    log_message "  ⚠️  ETF holdings: Failed (non-critical)"
fi

if [ $FUTURE_DIV_STATUS -eq 0 ]; then
    log_message "  ✅ Future dividends: Success"
    cat "$FUTURE_DIV_LOG" >> "$LOG_FILE"
else
    log_message "  ⚠️  Future dividends: Failed (non-critical)"
fi

if [ $BACKUP_STATUS -eq 0 ]; then
    log_message "  ✅ Database backup: Success"
    cat "$BACKUP_LOG" >> "$LOG_FILE"
else
    log_message "  ⚠️  Database backup: Failed (non-critical)"
fi

log_message ""

# ============================================================================
# FINAL STATUS REPORT
# ============================================================================

# Database Status Report
log_message ""
log_message "📊 FINAL DATABASE STATUS REPORT"
log_message "============================================================"

$PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
logging.basicConfig(level=logging.ERROR)

try:
    supabase = get_supabase_client()

    # Total symbols
    result = supabase.table('raw_stocks').select('symbol', count='exact').execute()
    print(f'📈 Total symbols in database: {result.count:,}')
    print(f'')

    # Data completeness
    print(f'📊 DATA COMPLETENESS:')
    with_prices = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('price', 'null').execute()
    print(f'  💰 Symbols with prices: {with_prices.count:,} ({100*with_prices.count/result.count:.1f}%)')

    with_dividends = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('dividend_yield', 'null').execute()
    print(f'  💵 Symbols with dividend data: {with_dividends.count:,} ({100*with_dividends.count/result.count:.1f}%)')

    with_companies = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('company', 'null').execute()
    print(f'  🏢 Symbols with company info: {with_companies.count:,} ({100*with_companies.count/result.count:.1f}%)')

    with_sectors = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('sector', 'null').execute()
    print(f'  🏭 Symbols with sector data: {with_sectors.count:,} ({100*with_sectors.count/result.count:.1f}%)')

    with_holdings = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('holdings', 'null').execute()
    print(f'  📊 ETFs with holdings: {with_holdings.count:,}')

    # Breakdown by type
    print(f'')
    print(f'🏷️  BREAKDOWN BY TYPE:')
    stocks = supabase.table('raw_stocks').select('symbol', count='exact').eq('type', 'stock').execute()
    etfs = supabase.table('raw_stocks').select('symbol', count='exact').eq('type', 'etf').execute()
    trusts = supabase.table('raw_stocks').select('symbol', count='exact').eq('type', 'trust').execute()
    print(f'  📈 Stocks: {stocks.count:,}')
    print(f'  📊 ETFs: {etfs.count:,}')
    print(f'  🏛️  Trusts: {trusts.count:,}')

    # Historical data records
    print(f'')
    print(f'📜 HISTORICAL RECORDS:')
    price_records = supabase.table('raw_stock_prices').select('symbol', count='exact').execute()
    print(f'  💰 Price records: {price_records.count:,}')

    div_records = supabase.table('raw_dividends').select('symbol', count='exact').execute()
    print(f'  💵 Dividend records: {div_records.count:,}')

    future_div_records = supabase.table('raw_future_dividends').select('symbol', count='exact').execute()
    print(f'  📅 Future dividend records: {future_div_records.count:,}')

    # Excluded symbols
    print(f'')
    excluded = supabase.table('raw_excluded_symbols').select('symbol', count='exact').execute()
    print(f'❌ Excluded symbols: {excluded.count:,}')

    # Top dividend yielders
    print(f'')
    print(f'🏆 TOP 10 DIVIDEND YIELDERS:')
    top_div = supabase.table('raw_stocks').select('symbol, dividend_yield, company').not_.is_('dividend_yield', 'null').order('dividend_yield', desc=True).limit(10).execute()
    for i, s in enumerate(top_div.data, 1):
        company = s.get('company', 'N/A')[:30]
        print(f'  {i:2d}. {s["symbol"]:8s} {float(s.get("dividend_yield", 0)):6.2f}%  {company}')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
" 2>&1 | tee -a "$LOG_FILE"

# Error Detection and Quality Checks
log_message ""
log_message "🔍 ERROR DETECTION & DATA QUALITY CHECKS"
log_message "============================================================"

$PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
from datetime import datetime, timedelta
logging.basicConfig(level=logging.ERROR)

try:
    supabase = get_supabase_client()

    # Check 1: Price data coverage
    total = supabase.table('raw_stocks').select('symbol', count='exact').execute()
    with_prices = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('price', 'null').execute()
    price_pct = 100 * with_prices.count / max(total.count, 1)

    if price_pct < 50:
        print(f'🔴 CRITICAL: Price data coverage critically low: {price_pct:.1f}%')
        print(f'   ACTION REQUIRED: Investigate price fetching process')
    elif price_pct < 80:
        print(f'🟡 WARNING: Price data coverage below target: {price_pct:.1f}%')
        print(f'   RECOMMENDED: Review failed price updates')
    else:
        print(f'✅ Price data coverage: {price_pct:.1f}%')

    # Check 2: Stale data detection (no updates in 48 hours)
    cutoff = (datetime.now() - timedelta(hours=48)).isoformat()
    stale_symbols = supabase.table('raw_stocks').select('symbol', count='exact').lt('updated_at', cutoff).execute()
    stale_pct = 100 * stale_symbols.count / max(total.count, 1)

    if stale_pct > 50:
        print(f'🔴 CRITICAL: {stale_pct:.1f}% of symbols not updated in 48+ hours')
        print(f'   ACTION REQUIRED: Check if daily updates are running')
    elif stale_pct > 20:
        print(f'🟡 WARNING: {stale_pct:.1f}% of symbols stale (48+ hours old)')
        print(f'   RECOMMENDED: Review update frequency')
    else:
        print(f'✅ Data freshness: {100-stale_pct:.1f}% updated in last 48h')

    # Check 3: Duplicate detection
    symbols = supabase.table('raw_stocks').select('symbol').execute()
    symbol_list = [s['symbol'] for s in symbols.data]
    unique_symbols = set(symbol_list)
    duplicate_count = len(symbol_list) - len(unique_symbols)

    if duplicate_count > 0:
        print(f'🟡 WARNING: {duplicate_count} duplicate symbol(s) detected')
        print(f'   RECOMMENDED: Run deduplication script')
    else:
        print(f'✅ No duplicate symbols detected')

    # Check 4: Null company data
    null_companies = supabase.table('raw_stocks').select('symbol', count='exact').is_('company', 'null').execute()
    null_company_pct = 100 * null_companies.count / max(total.count, 1)

    if null_company_pct > 50:
        print(f'🟡 WARNING: {null_company_pct:.1f}% of symbols missing company data')
        print(f'   RECOMMENDED: Run company data refresh more frequently')
    elif null_company_pct > 0:
        print(f'ℹ️  INFO: {null_companies.count:,} symbols without company data ({null_company_pct:.1f}%)')
    else:
        print(f'✅ All symbols have company data')

    # Check 5: Recent update success rate
    cutoff_2h = (datetime.now() - timedelta(hours=2)).isoformat()
    recent_updates = supabase.table('raw_stocks').select('symbol', count='exact').gte('updated_at', cutoff_2h).execute()

    if recent_updates.count == 0:
        print(f'🔴 CRITICAL: No symbols updated in last 2 hours')
        print(f'   ACTION REQUIRED: Check if update script is running')
    elif recent_updates.count < 100:
        print(f'🟡 WARNING: Only {recent_updates.count} symbols updated in last 2 hours')
        print(f'   RECOMMENDED: Investigate slow update process')
    else:
        print(f'✅ Recent activity: {recent_updates.count:,} symbols updated in last 2h')

    # Check 6: Database size warnings
    price_records = supabase.table('raw_stock_prices').select('symbol', count='exact').execute()
    if price_records.count > 50000000:  # 50M records
        print(f'🟡 WARNING: Price table has {price_records.count:,} records')
        print(f'   RECOMMENDED: Consider archiving old price data')

except Exception as e:
    print(f'🔴 CRITICAL: Error during quality checks: {e}')
    print(f'   ACTION REQUIRED: Investigate database connectivity')
" 2>&1 | tee -a "$LOG_FILE"

# Completion Summary
log_message ""
log_message "============================================================"
SCRIPT_END_TIME=$(date +%s)
TOTAL_DURATION=$((SCRIPT_END_TIME - SCRIPT_START_TIME))
TOTAL_MINUTES=$((TOTAL_DURATION / 60))
TOTAL_SECONDS=$((TOTAL_DURATION % 60))
COMPLETION_TIME=$(date '+%Y-%m-%d %H:%M:%S')

log_message "⏱️  EXECUTION SUMMARY"
log_message "============================================================"
log_message "Total execution time: ${TOTAL_MINUTES}m ${TOTAL_SECONDS}s"
log_message "Completion time: $COMPLETION_TIME"
log_message ""
log_message "⚡ PERFORMANCE BREAKDOWN:"
log_message "  Phase 1 (Parallel Scrapers): ${PHASE1_DURATION}s"
if [ ! -z "$STEP2_DURATION" ]; then
    log_message "  Step 2 (Main Update): ${STEP2_DURATION}s"
fi
log_message "  Phase 2 (Parallel Post-Tasks): ${PHASE2_DURATION}s"
log_message ""

if [ "$OVERALL_SUCCESS" = true ]; then
    log_message "🎉 DAILY UPDATE COMPLETED SUCCESSFULLY"
    EXIT_CODE=0
else
    log_message "⚠️  DAILY UPDATE COMPLETED WITH ERRORS"
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
