#!/bin/bash
# Setup Hourly Metrics Calculation Cron Job

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Path to the metrics calculation script
METRICS_SCRIPT="$SCRIPT_DIR/run_metrics_calculation.sh"

# Cron entry (runs every hour at minute 5)
CRON_ENTRY="5 * * * * $METRICS_SCRIPT"

echo "📅 Setting up hourly metrics calculation cron job..."
echo ""
echo "Cron schedule: Every hour at minute 5"
echo "Script: $METRICS_SCRIPT"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run_metrics_calculation.sh"; then
    echo "⚠️  Cron job already exists. Remove it first if you want to reinstall."
    echo ""
    echo "Current cron jobs:"
    crontab -l 2>/dev/null | grep "run_metrics_calculation.sh"
    echo ""
    read -p "Do you want to remove and reinstall? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove existing entry
        crontab -l 2>/dev/null | grep -v "run_metrics_calculation.sh" | crontab -
        echo "✅ Removed existing cron job"
    else
        echo "❌ Installation cancelled"
        exit 0
    fi
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Hourly metrics calculation cron job installed successfully!"
    echo ""
    echo "📊 The script will run every hour at minute 5 and calculate:"
    echo "   - Dividend payment frequency"
    echo "   - Total return TTM (trailing twelve months)"
    echo "   - Price change TTM"
    echo "   - Price change YTD (year-to-date)"
    echo "   - Current prices and dividend yields"
    echo ""
    echo "📝 Logs will be saved to: $PROJECT_DIR/logs/metrics_calculation_YYYYMMDD.log"
    echo ""
    echo "Current cron jobs:"
    crontab -l
else
    echo "❌ Failed to install cron job"
    exit 1
fi
