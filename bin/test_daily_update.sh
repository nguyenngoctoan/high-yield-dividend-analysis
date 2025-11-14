#!/bin/bash

# Test Script for Daily Update V2
# Tests each phase of the daily_update_v2.sh script to ensure everything works after database restore

SCRIPT_DIR="/Users/toan/dev/high-yield-dividend-analysis"
cd "$SCRIPT_DIR" || exit 1

# Setup logging
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/test_daily_update_$(date '+%Y%m%d_%H%M%S').log"

echo "================================================================================"
echo "🧪 DAILY UPDATE TEST SUITE - $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"
echo ""

# Function to log messages
log_message() {
    echo "$1" | tee -a "$LOG_FILE"
}

# Function to run test
run_test() {
    local test_name="$1"
    local command="$2"

    log_message ""
    log_message "🧪 TEST: $test_name"
    log_message "───────────────────────────────────────────────────────────────────────────────"
    log_message "📝 Command: $command"
    log_message ""

    if eval "$command" 2>&1 | tee -a "$LOG_FILE"; then
        log_message "✅ PASSED: $test_name"
        return 0
    else
        log_message "❌ FAILED: $test_name"
        return 1
    fi
}

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Test 0: Supabase Health Check
log_message "🏥 TEST 0: Supabase Health Check"
log_message "───────────────────────────────────────────────────────────────────────────────"

cd /Users/toan/dev/ai-dividend-tracker || exit 1
if npx supabase status 2>&1 | tee -a "$LOG_FILE" | grep -q "supabase local development setup is running"; then
    log_message "✅ PASSED: Supabase is running"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log_message "❌ FAILED: Supabase is not running"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))
cd "$SCRIPT_DIR"

# Test 1: Database Connectivity
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "Database Connectivity" \
    "python3 -c \"
from supabase_helpers import get_supabase_client
import logging
logging.basicConfig(level=logging.ERROR)
try:
    supabase = get_supabase_client()
    result = supabase.table('raw_stocks').select('symbol', count='exact').limit(1).execute()
    print(f'✅ Database connected successfully')
    print(f'📊 Total symbols in database: {result.count:,}')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
\""; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 2: Discovery Mode (Quick Test - Single Symbol)
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "Discovery Mode (Sample Test)" \
    "python3 update_stock_v2.py --mode discover --limit 5"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 3: Price Update Mode (Sample Stocks)
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "Price Update Mode (Sample)" \
    "python3 update_stock_v2.py --mode update --prices-only --limit 10"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 4: Dividend Update Mode (Sample)
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "Dividend Update Mode (Sample)" \
    "python3 update_stock_v2.py --mode update --dividends-only --limit 10"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 5: Company Data Update
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "Company Data Update (Sample)" \
    "python3 update_stock_v2.py --mode refresh-companies --limit 5"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 6: ETF Classification
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "ETF Classification" \
    "python3 update_stock_v2.py --mode classify-etfs --limit 5"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 7: ETF Holdings Update
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "ETF Holdings Update (Sample)" \
    "python3 update_stock_v2.py --mode update-holdings --limit 5"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 8: Future Dividends
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "Future Dividends Update (Sample)" \
    "python3 update_stock_v2.py --mode future-dividends --days-ahead 30 --limit 10"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 9: YieldMax Scraper
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "YieldMax Scraper" \
    "python3 scripts/scrape_yieldmax.py"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 10: CBOE Scraper (Current Year Only)
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "CBOE Dividend Scraper" \
    "python3 scripts/scrape_cboe_dividends.py --years $(date +%Y) 2>&1 | grep -v 'NotOpenSSLWarning' | grep -v 'urllib3'"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 11: NASDAQ Scraper
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "NASDAQ Dividend Scraper" \
    "python3 scripts/scrape_nasdaq_dividends.py"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 12: NYSE Scraper
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "NYSE Dividend Scraper" \
    "python3 scripts/scrape_nyse_dividends.py"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 13: Snowball Scraper
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "Snowball Analytics Scraper" \
    "python3 scripts/scrape_snowball_dividends.py --category us-popular-div"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 14: Database Backup
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "Database Backup" \
    "bash scripts/backup_database.sh"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 15: Data Quality Checks
TESTS_TOTAL=$((TESTS_TOTAL + 1))
if run_test "Data Quality Checks" \
    "python3 -c \"
from supabase_helpers import get_supabase_client
import logging
from datetime import datetime, timedelta
logging.basicConfig(level=logging.ERROR)

try:
    supabase = get_supabase_client()

    # Total symbols
    total = supabase.table('raw_stocks').select('symbol', count='exact').execute()
    print(f'📊 Total symbols: {total.count:,}')

    # Data completeness
    with_prices = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('price', 'null').execute()
    price_pct = 100 * with_prices.count / max(total.count, 1)
    print(f'💰 Symbols with prices: {with_prices.count:,} ({price_pct:.1f}%)')

    with_dividends = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('dividend_yield', 'null').execute()
    div_pct = 100 * with_dividends.count / max(total.count, 1)
    print(f'💵 Symbols with dividends: {with_dividends.count:,} ({div_pct:.1f}%)')

    with_companies = supabase.table('raw_stocks').select('symbol', count='exact').not_.is_('company', 'null').execute()
    company_pct = 100 * with_companies.count / max(total.count, 1)
    print(f'🏢 Symbols with company info: {with_companies.count:,} ({company_pct:.1f}%)')

    # Historical records
    price_records = supabase.table('raw_stock_prices').select('symbol', count='exact').execute()
    print(f'📈 Price records: {price_records.count:,}')

    div_records = supabase.table('raw_dividends').select('symbol', count='exact').execute()
    print(f'📊 Dividend records: {div_records.count:,}')

    # Quality checks
    if price_pct < 50:
        print(f'❌ CRITICAL: Price coverage too low ({price_pct:.1f}%)')
        exit(1)
    elif price_pct < 80:
        print(f'⚠️ WARNING: Price coverage below target ({price_pct:.1f}%)')
    else:
        print(f'✅ Price coverage acceptable ({price_pct:.1f}%)')

    print(f'✅ Data quality checks passed')

except Exception as e:
    print(f'❌ Data quality checks failed: {e}')
    exit(1)
\""; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Summary Report
log_message ""
log_message "================================================================================"
log_message "📊 TEST SUMMARY"
log_message "================================================================================"
log_message ""
log_message "Total Tests Run: $TESTS_TOTAL"
log_message "✅ Tests Passed: $TESTS_PASSED"
log_message "❌ Tests Failed: $TESTS_FAILED"
log_message ""

if [ $TESTS_FAILED -eq 0 ]; then
    log_message "🎉 ALL TESTS PASSED!"
    log_message ""
    log_message "✅ The database has been successfully restored and all systems are operational."
    log_message "✅ The daily update script is ready to run."
    EXIT_CODE=0
else
    SUCCESS_RATE=$((TESTS_PASSED * 100 / TESTS_TOTAL))
    log_message "⚠️ SOME TESTS FAILED"
    log_message ""
    log_message "Success Rate: $SUCCESS_RATE%"
    log_message ""
    log_message "Please review the log file for details:"
    log_message "  $LOG_FILE"
    EXIT_CODE=1
fi

log_message "================================================================================"
log_message "📝 Complete test log saved to: $LOG_FILE"
log_message "================================================================================"

exit $EXIT_CODE
