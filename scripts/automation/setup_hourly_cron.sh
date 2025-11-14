#!/bin/bash
# Setup cron job for hourly price tracking (no auto-cleanup)

SCRIPT_DIR="/Users/toan/dev/high-yield-dividend-analysis"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"
FETCH_SCRIPT="$SCRIPT_DIR/fetch_hourly_prices.py"
LOG_DIR="$SCRIPT_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Cron entry to fetch hourly prices at the top of every hour during market hours (4 AM - 8 PM ET)
# Runs Monday-Friday only (includes pre-market from 4 AM, regular hours, and after-hours until 8 PM)
FETCH_CRON="0 4-20 * * 1-5 cd $SCRIPT_DIR && $PYTHON_PATH $FETCH_SCRIPT >> $LOG_DIR/hourly_cron.log 2>&1"

echo "=================================================="
echo "HOURLY PRICE TRACKING - CRON SETUP"
echo "=================================================="
echo ""
echo "This will add a cron job to fetch hourly prices:"
echo ""
echo "HOURLY FETCH: Every hour from 4 AM to 8 PM ET (Mon-Fri)"
echo "   Covers pre-market (4-9:30 AM) + regular hours (9:30 AM - 4 PM) + post-market (4-8 PM)"
echo "   $FETCH_CRON"
echo ""
echo "⚠️  NOTE: Auto-cleanup is DISABLED - all hourly data will be retained"
echo "   You can manually cleanup old data by running cleanup_old_hourly_data.py"
echo ""
read -p "Add this cron job? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    # Remove old entries if they exist
    if crontab -l 2>/dev/null | grep -F "fetch_hourly_prices.py" > /dev/null; then
        echo "⚠️  Removing old fetch_hourly_prices.py cron entry..."
        crontab -l 2>/dev/null | grep -v "fetch_hourly_prices.py" | crontab -
    fi

    if crontab -l 2>/dev/null | grep -F "cleanup_old_hourly_data.py" > /dev/null; then
        echo "⚠️  Removing old cleanup_old_hourly_data.py cron entry..."
        crontab -l 2>/dev/null | grep -v "cleanup_old_hourly_data.py" | crontab -
    fi

    # Add new cron entry (fetch only, no cleanup)
    (crontab -l 2>/dev/null; echo "$FETCH_CRON") | crontab -

    echo "✅ Cron job added successfully!"
    echo ""
    echo "Current crontab:"
    echo "=================================================="
    crontab -l
    echo "=================================================="
    echo ""
    echo "Log files:"
    echo "  Hourly fetch: $LOG_DIR/hourly_cron.log"
    echo ""
    echo "Script logs:"
    echo "  Fetch: $SCRIPT_DIR/hourly_prices.log"
else
    echo "❌ Cron job not added."
    echo ""
    echo "To add manually, run:"
    echo "  crontab -e"
    echo ""
    echo "And add this line:"
    echo "  $FETCH_CRON"
fi

echo ""
echo "To test the script manually:"
echo "  cd $SCRIPT_DIR"
echo "  source venv/bin/activate"
echo "  python fetch_hourly_prices.py      # Fetch hourly prices"
echo ""
echo "To manually cleanup old data (optional):"
echo "  python cleanup_old_hourly_data.py  # Delete data older than 1 day"
echo ""
echo "To remove the cron job later:"
echo "  crontab -l | grep -v 'fetch_hourly_prices.py' | crontab -"
