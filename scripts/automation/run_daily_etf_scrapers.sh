#!/bin/bash
# Daily ETF Scraper Runner
# Runs all ETF scrapers to capture daily snapshots for time series analysis
# Scheduled to run daily via cron

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Set up logging
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/etf_scrapers_$(date +%Y%m%d_%H%M%S).log"

echo "========================================" >> "$LOG_FILE"
echo "Starting ETF scrapers at $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# Change to project directory
cd "$PROJECT_DIR"

# Track results
TOTAL=0
SUCCESS=0
FAILED=0

# Array of ETF scrapers to run
SCRAPERS=(
    "scripts/scrapers/etfs/yieldmax/scrape_yieldmax_all.py"
    "scripts/scrapers/etfs/roundhill/scrape_roundhill_all.py"
    "scripts/scrapers/etfs/neos/scrape_neos_all.py"
    "scripts/scrapers/etfs/kurv/scrape_kurv_all.py"
    "scripts/scrapers/etfs/graniteshares/scrape_graniteshares_all.py"
    "scripts/scrapers/etfs/defiance/scrape_defiance_all.py"
    "scripts/scrapers/etfs/globalx/scrape_globalx_all.py"
    "scripts/scrapers/etfs/purpose/scrape_purpose_all.py"
)

# Run each scraper
for scraper in "${SCRAPERS[@]}"; do
    TOTAL=$((TOTAL + 1))
    provider=$(basename "$(dirname "$scraper")")

    echo "" >> "$LOG_FILE"
    echo "========================================" >> "$LOG_FILE"
    echo "Running $provider scraper at $(date)" >> "$LOG_FILE"
    echo "========================================" >> "$LOG_FILE"

    if python3 "$scraper" >> "$LOG_FILE" 2>&1; then
        SUCCESS=$((SUCCESS + 1))
        echo "✅ $provider scraper completed successfully" >> "$LOG_FILE"
    else
        FAILED=$((FAILED + 1))
        echo "❌ $provider scraper failed" >> "$LOG_FILE"
    fi

    # Rate limiting - 2 second delay between scrapers
    sleep 2
done

# Print summary
echo "" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "ETF Scraper Run Complete at $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "Total: $TOTAL" >> "$LOG_FILE"
echo "Success: $SUCCESS" >> "$LOG_FILE"
echo "Failed: $FAILED" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

EXIT_CODE=0
if [ $FAILED -gt 0 ]; then
    EXIT_CODE=1
fi

exit $EXIT_CODE
