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

# Set Python command
PYTHON_CMD="python3"

# Remote Supabase configuration (no local setup needed)
# All scripts now connect to remote Supabase via environment variables

# Verify remote Supabase connectivity
log_message "🔍 Verifying remote Supabase connectivity..."
if $PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()
    result = supabase.table('raw_stocks').select('symbol', count='exact').limit(1).execute()
    print('✅ Connected to remote Supabase')
    exit(0)
except Exception as e:
    print(f'❌ Failed to connect to remote Supabase: {e}')
    exit(1)
" 2>&1 | tee -a "$LOG_FILE"; then
    log_message "✅ Remote Supabase is accessible"
else
    log_message "❌ Failed to connect to remote Supabase - exiting"
    log_message "💡 Check your internet connection and .env configuration"
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

# Step 1d: YieldMax Scraper (runs daily)
log_message ""
log_message "📰 STEP 1d: YieldMax Dividend Scraper (Daily)"
log_message "============================================================"
log_message "📝 Command: $PYTHON_CMD scripts/scrape_yieldmax.py"

if $PYTHON_CMD scripts/scrape_yieldmax.py >> "$LOG_FILE" 2>&1; then
    log_message "✅ YieldMax scraping completed"

    # YieldMax metrics
    log_message ""
    log_message "📈 YIELDMAX METRICS:"
    $PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
from datetime import datetime, timedelta
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()

    # Total YieldMax dividend records
    total_yieldmax = supabase.table('raw_yieldmax_dividends').select('symbol', count='exact').execute()
    print(f'  📊 Total YieldMax dividend records: {total_yieldmax.count:,}')

    # Recently added (last 24 hours)
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    recent_yieldmax = supabase.table('raw_yieldmax_dividends').select('symbol, ex_date, amount_per_share', count='exact').gte('created_at', cutoff).execute()
    print(f'  🆕 New records today: {recent_yieldmax.count:,}')

    # Show sample recent dividends
    if recent_yieldmax.data and recent_yieldmax.count > 0:
        print(f'  💰 Sample recent YieldMax dividends:')
        for d in recent_yieldmax.data[:5]:
            amount = float(d.get('amount_per_share', 0))
            print(f'     - {d[\"symbol\"]}: \${amount:.4f} (Ex: {d[\"ex_date\"]})')

    # Unique YieldMax symbols
    unique_symbols = supabase.table('raw_yieldmax_dividends').select('symbol').execute()
    unique_count = len(set([s['symbol'] for s in unique_symbols.data])) if unique_symbols.data else 0
    print(f'  🏢 Unique YieldMax ETF symbols: {unique_count:,}')

except Exception as e:
    print(f'  ⚠️  Could not fetch YieldMax metrics: {e}')
" 2>&1 | tee -a "$LOG_FILE"

else
    log_message "⚠️  YieldMax scraping failed (non-critical)"
fi

sleep 5

# Step 1e: CBOE Dividend Scraper (runs daily)
log_message ""
log_message "📰 STEP 1e: CBOE Dividend Scraper (Daily)"
log_message "============================================================"
log_message "📝 Command: $PYTHON_CMD scripts/scrape_cboe_dividends.py --years $(date +%Y)"

if $PYTHON_CMD scripts/scrape_cboe_dividends.py --years "$(date +%Y)" >> "$LOG_FILE" 2>&1; then
    log_message "✅ CBOE scraping completed"

    # CBOE metrics
    log_message ""
    log_message "📈 CBOE METRICS:"
    $PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
from datetime import datetime, timedelta
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()

    # Total CBOE dividend records
    total_cboe = supabase.table('raw_dividends_cboe').select('symbol', count='exact').execute()
    print(f'  📊 Total CBOE dividend records: {total_cboe.count:,}')

    # Recently added (last 24 hours)
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    recent_cboe = supabase.table('raw_dividends_cboe').select('symbol, ex_date, amount', count='exact').gte('created_at', cutoff).execute()
    print(f'  🆕 New records today: {recent_cboe.count:,}')

    # Show sample recent dividends
    if recent_cboe.data and recent_cboe.count > 0:
        print(f'  💰 Sample recent CBOE dividends:')
        for d in recent_cboe.data[:5]:
            amount = float(d.get('amount', 0)) if d.get('amount') else 0
            print(f'     - {d[\"symbol\"]}: \${amount:.4f} (Ex: {d[\"ex_date\"]})')

    # Unique CBOE symbols
    unique_symbols = supabase.table('raw_dividends_cboe').select('symbol').execute()
    unique_count = len(set([s['symbol'] for s in unique_symbols.data])) if unique_symbols.data else 0
    print(f'  🏢 Unique CBOE symbols: {unique_count:,}')

except Exception as e:
    print(f'  ⚠️  Could not fetch CBOE metrics: {e}')
" 2>&1 | tee -a "$LOG_FILE"

else
    log_message "⚠️  CBOE scraping failed (non-critical)"
fi

sleep 5

# Step 1f: Nasdaq Dividend Scraper (runs daily with auto-continue)
log_message ""
log_message "📰 STEP 1f: Nasdaq Dividend Scraper (Daily)"
log_message "============================================================"
log_message "📝 Command: $PYTHON_CMD scripts/scrape_nasdaq_dividends.py --auto-continue"

if $PYTHON_CMD scripts/scrape_nasdaq_dividends.py --auto-continue >> "$LOG_FILE" 2>&1; then
    log_message "✅ Nasdaq scraping completed"

    # Nasdaq metrics
    log_message ""
    log_message "📈 NASDAQ METRICS:"
    $PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
from datetime import datetime, timedelta
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()

    # Total Nasdaq dividend records
    total_nasdaq = supabase.table('raw_dividends_nasdaq').select('symbol', count='exact').execute()
    print(f'  📊 Total Nasdaq dividend records: {total_nasdaq.count:,}')

    # Recently added (last 24 hours)
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    recent_nasdaq = supabase.table('raw_dividends_nasdaq').select('symbol, ex_date, dividend_rate', count='exact').gte('created_at', cutoff).execute()
    print(f'  🆕 New records today: {recent_nasdaq.count:,}')

    # Show sample recent dividends
    if recent_nasdaq.data and recent_nasdaq.count > 0:
        print(f'  💰 Sample recent Nasdaq dividends:')
        for d in recent_nasdaq.data[:5]:
            rate = float(d.get('dividend_rate', 0)) if d.get('dividend_rate') else 0
            print(f'     - {d[\"symbol\"]}: \${rate:.4f} (Ex: {d[\"ex_date\"]})')

    # Unique Nasdaq symbols
    unique_symbols = supabase.table('raw_dividends_nasdaq').select('symbol').execute()
    unique_count = len(set([s['symbol'] for s in unique_symbols.data])) if unique_symbols.data else 0
    print(f'  🏢 Unique Nasdaq symbols: {unique_count:,}')

except Exception as e:
    print(f'  ⚠️  Could not fetch Nasdaq metrics: {e}')
" 2>&1 | tee -a "$LOG_FILE"

else
    log_message "⚠️  Nasdaq scraping failed (non-critical)"
fi

sleep 5

# Step 1g: NYSE Dividend Scraper (runs daily with auto-continue)
log_message ""
log_message "📰 STEP 1g: NYSE Dividend Scraper (Daily)"
log_message "============================================================"
log_message "📝 Command: $PYTHON_CMD scripts/scrape_nyse_dividends.py --auto-continue"

if $PYTHON_CMD scripts/scrape_nyse_dividends.py --auto-continue >> "$LOG_FILE" 2>&1; then
    log_message "✅ NYSE scraping completed"

    # NYSE metrics
    log_message ""
    log_message "📈 NYSE METRICS:"
    $PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
from datetime import datetime, timedelta
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()

    # Total NYSE dividend records
    total_nyse = supabase.table('raw_dividends_nyse').select('symbol', count='exact').execute()
    print(f'  📊 Total NYSE dividend records: {total_nyse.count:,}')

    # Recently added (last 24 hours)
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    recent_nyse = supabase.table('raw_dividends_nyse').select('symbol, ex_date', count='exact').gte('created_at', cutoff).execute()
    print(f'  🆕 New records today: {recent_nyse.count:,}')

    # Show sample recent dividends
    if recent_nyse.data and recent_nyse.count > 0:
        print(f'  💰 Sample recent NYSE dividends:')
        for d in recent_nyse.data[:5]:
            print(f'     - {d[\"symbol\"]} (Ex: {d[\"ex_date\"]})')

    # Unique NYSE symbols
    unique_symbols = supabase.table('raw_dividends_nyse').select('symbol').execute()
    unique_count = len(set([s['symbol'] for s in unique_symbols.data])) if unique_symbols.data else 0
    print(f'  🏢 Unique NYSE symbols: {unique_count:,}')

except Exception as e:
    print(f'  ⚠️  Could not fetch NYSE metrics: {e}')
" 2>&1 | tee -a "$LOG_FILE"

else
    log_message "⚠️  NYSE scraping failed (non-critical)"
fi

sleep 5

# Step 1h: Snowball Analytics Scraper (runs daily - US popular dividends only)
log_message ""
log_message "📰 STEP 1h: Snowball Analytics Scraper (Daily)"
log_message "============================================================"
log_message "📝 Command: $PYTHON_CMD scripts/scrape_snowball_dividends.py --category us-popular-div"

if $PYTHON_CMD scripts/scrape_snowball_dividends.py --category us-popular-div >> "$LOG_FILE" 2>&1; then
    log_message "✅ Snowball scraping completed"

    # Snowball metrics
    log_message ""
    log_message "📈 SNOWBALL METRICS:"
    $PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
from datetime import datetime, timedelta
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()

    # Total Snowball dividend records
    total_snowball = supabase.table('raw_dividends_snowball').select('symbol', count='exact').execute()
    print(f'  📊 Total Snowball dividend records: {total_snowball.count:,}')

    # Recently added (last 24 hours)
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    recent_snowball = supabase.table('raw_dividends_snowball').select('symbol, ex_date, amount, dividend_yield', count='exact').gte('created_at', cutoff).execute()
    print(f'  🆕 New records today: {recent_snowball.count:,}')

    # Show sample recent dividends
    if recent_snowball.data and recent_snowball.count > 0:
        print(f'  💰 Sample recent Snowball dividends:')
        for d in recent_snowball.data[:5]:
            amount = float(d.get('amount', 0)) if d.get('amount') else 0
            div_yield = float(d.get('dividend_yield', 0)) if d.get('dividend_yield') else 0
            print(f'     - {d[\"symbol\"]}: \${amount:.4f} / {div_yield:.2f}% (Ex: {d[\"ex_date\"]})')

    # Unique Snowball symbols
    unique_symbols = supabase.table('raw_dividends_snowball').select('symbol').execute()
    unique_count = len(set([s['symbol'] for s in unique_symbols.data])) if unique_symbols.data else 0
    print(f'  🏢 Unique Snowball symbols: {unique_count:,}')

except Exception as e:
    print(f'  ⚠️  Could not fetch Snowball metrics: {e}')
" 2>&1 | tee -a "$LOG_FILE"

else
    log_message "⚠️  Snowball scraping failed (non-critical)"
fi

sleep 5

# Step 2: Update all data (prices, dividends, companies)
log_message ""
log_message "💰 STEP 2: Data Update (Prices, Dividends, Companies)"
log_message "============================================================"
log_message "📝 Command: $PYTHON_CMD update_stock_v2.py --mode update"

if $PYTHON_CMD update_stock_v2.py --mode update >> "$LOG_FILE" 2>&1; then
    log_message "✅ Data update completed"

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

sleep 5

# Step 3: Refresh NULL companies (only if needed)
log_message ""
log_message "🏢 STEP 3: Refresh NULL Company Data"
log_message "============================================================"

# Check how many NULL companies exist before
NULL_BEFORE=$($PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()
    result = supabase.table('raw_stocks').select('symbol', count='exact').is_('company', 'null').execute()
    print(result.count)
except: print(0)
" 2>/dev/null)

log_message "📊 Symbols with NULL company data: $NULL_BEFORE"
log_message "📝 Command: $PYTHON_CMD update_stock_v2.py --mode refresh-companies --limit 100"

if $PYTHON_CMD update_stock_v2.py --mode refresh-companies --limit 100 >> "$LOG_FILE" 2>&1; then
    log_message "✅ Company refresh completed"

    # Show results
    NULL_AFTER=$($PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()
    result = supabase.table('raw_stocks').select('symbol', count='exact').is_('company', 'null').execute()
    print(result.count)
except: print(0)
" 2>/dev/null)

    FILLED=$((NULL_BEFORE - NULL_AFTER))
    log_message "  📈 Company data filled: $FILLED symbols"
    log_message "  📊 Remaining NULL companies: $NULL_AFTER"
else
    log_message "⚠️  Company refresh had issues (non-critical)"
fi

sleep 5

# Step 4: Update ETF Holdings (daily)
log_message ""
log_message "📊 STEP 4: ETF Holdings Update (Daily)"
log_message "============================================================"
log_message "📝 Command: $PYTHON_CMD update_stock_v2.py --mode update-holdings"

if $PYTHON_CMD update_stock_v2.py --mode update-holdings >> "$LOG_FILE" 2>&1; then
    log_message "✅ Holdings update completed"

    # Holdings metrics
    log_message ""
    log_message "📈 HOLDINGS METRICS:"
    $PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
from datetime import datetime, timedelta
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()

    # Total ETFs with holdings
    etfs_with_holdings = supabase.table('raw_stocks').select('symbol, holdings', count='exact').eq('type', 'etf').not_.is_('holdings', 'null').execute()
    total_etfs = supabase.table('raw_stocks').select('symbol', count='exact').eq('type', 'etf').execute()

    print(f'  📊 ETFs with holdings data: {etfs_with_holdings.count:,} / {total_etfs.count:,} ({100*etfs_with_holdings.count/max(total_etfs.count,1):.1f}%)')

    # Recently updated
    cutoff = (datetime.now() - timedelta(hours=2)).isoformat()
    recent_updates = supabase.table('raw_stocks').select('symbol, holdings', count='exact').eq('type', 'etf').gte('updated_at', cutoff).not_.is_('holdings', 'null').execute()
    print(f'  🆕 Holdings updated in this run: {recent_updates.count:,}')

    # Sample holdings
    if recent_updates.data and recent_updates.count > 0:
        import json
        sample = recent_updates.data[0]
        holdings = json.loads(sample.get('holdings', '[]'))
        print(f'  📋 Sample ETF: {sample[\"symbol\"]} ({len(holdings)} holdings)')
        if holdings:
            print(f'     Top 3 holdings:')
            for h in holdings[:3]:
                print(f'       - {h.get(\"symbol\", \"N/A\")}: {h.get(\"weight\", 0):.2f}%')

except Exception as e:
    print(f'  ⚠️  Could not fetch holdings metrics: {e}')
" 2>&1 | tee -a "$LOG_FILE"

else
    log_message "⚠️  Holdings update failed (non-critical)"
fi

sleep 5

# Step 5: Future Dividends (daily)
log_message ""
log_message "🔮 STEP 5: Future Dividends Calendar"
log_message "============================================================"
log_message "📝 Command: $PYTHON_CMD update_stock_v2.py --mode future-dividends --days-ahead 90"

if $PYTHON_CMD update_stock_v2.py --mode future-dividends --days-ahead 90 >> "$LOG_FILE" 2>&1; then
    log_message "✅ Future dividends updated"

    # Future dividend metrics
    log_message ""
    log_message "📅 FUTURE DIVIDENDS METRICS:"
    $PYTHON_CMD -c "
from supabase_helpers import get_supabase_client
import logging
from datetime import datetime, timedelta
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()

    # Total future dividends
    total_future = supabase.table('raw_future_dividends').select('symbol', count='exact').execute()
    print(f'  📊 Total future dividend records: {total_future.count:,}')

    # Future dividends by time period
    now = datetime.now()
    next_7_days = (now + timedelta(days=7)).date().isoformat()
    next_30_days = (now + timedelta(days=30)).date().isoformat()
    next_90_days = (now + timedelta(days=90)).date().isoformat()

    div_7d = supabase.table('raw_future_dividends').select('symbol', count='exact').gte('payment_date', now.date().isoformat()).lte('payment_date', next_7_days).execute()
    div_30d = supabase.table('raw_future_dividends').select('symbol', count='exact').gte('payment_date', now.date().isoformat()).lte('payment_date', next_30_days).execute()
    div_90d = supabase.table('raw_future_dividends').select('symbol', count='exact').gte('payment_date', now.date().isoformat()).lte('payment_date', next_90_days).execute()

    print(f'  📅 Upcoming dividends:')
    print(f'     Next 7 days: {div_7d.count:,}')
    print(f'     Next 30 days: {div_30d.count:,}')
    print(f'     Next 90 days: {div_90d.count:,}')

    # Show sample upcoming dividends
    upcoming = supabase.table('raw_future_dividends').select('symbol, payment_date, amount').gte('payment_date', now.date().isoformat()).order('payment_date').limit(5).execute()
    if upcoming.data:
        print(f'  💰 Next 5 dividend payments:')
        for d in upcoming.data:
            print(f'     - {d[\"symbol\"]}: \${d.get(\"amount\", 0):.4f} on {d[\"payment_date\"]}')

    # Unique symbols with future dividends
    unique_symbols = supabase.rpc('count_distinct_future_div_symbols').execute() if False else None
    # Fallback: approximate by getting all symbols
    symbols_with_future = supabase.table('raw_future_dividends').select('symbol').gte('payment_date', now.date().isoformat()).execute()
    unique_count = len(set([s['symbol'] for s in symbols_with_future.data])) if symbols_with_future.data else 0
    print(f'  🏢 Unique symbols with upcoming dividends: {unique_count:,}')

except Exception as e:
    print(f'  ⚠️  Could not fetch future dividend metrics: {e}')
" 2>&1 | tee -a "$LOG_FILE"

else
    log_message "⚠️  Future dividends failed (non-critical)"
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
        print(f'  {i:2d}. {s[\"symbol\"]:8s} {float(s.get(\"dividend_yield\", 0)):6.2f}%  {company}')

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
    duplicates = supabase.rpc('check_duplicate_symbols').execute() if False else None
    # Simple duplicate check
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
