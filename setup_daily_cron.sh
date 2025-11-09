#!/bin/bash

# Setup Daily Cron Job for Stock Data Updates
# This script configures a cron job to run daily_update_v2.sh

SCRIPT_DIR="/Users/toan/dev/high-yield-dividend-analysis"
CRON_SCRIPT="$SCRIPT_DIR/daily_update_v2.sh"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Daily Stock Data Update - Cron Setup${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check if script exists
if [ ! -f "$CRON_SCRIPT" ]; then
    echo -e "${RED}✗ Error: $CRON_SCRIPT not found${NC}"
    exit 1
fi

# Make sure script is executable
chmod +x "$CRON_SCRIPT"
echo -e "${GREEN}✓${NC} Script is executable"

# Get current crontab
CURRENT_CRON=$(crontab -l 2>/dev/null)

# Check if cron job already exists
if echo "$CURRENT_CRON" | grep -q "daily_update_v2.sh"; then
    echo -e "${YELLOW}⚠${NC}  Cron job already exists"
    echo ""
    echo "Current entry:"
    echo "$CURRENT_CRON" | grep "daily_update_v2.sh"
    echo ""
    read -p "Remove existing entry and reconfigure? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi

    # Remove existing entry
    CURRENT_CRON=$(echo "$CURRENT_CRON" | grep -v "daily_update_v2.sh")
fi

# Prompt for schedule
echo ""
echo "Select update schedule:"
echo "  1) Daily at 10:00 PM (recommended)"
echo "  2) Daily at 6:00 AM"
echo "  3) Daily at midnight"
echo "  4) Custom time"
echo ""
read -p "Enter choice (1-4): " CHOICE

case $CHOICE in
    1)
        CRON_TIME="0 22 * * *"
        DESC="Daily at 10:00 PM"
        ;;
    2)
        CRON_TIME="0 6 * * *"
        DESC="Daily at 6:00 AM"
        ;;
    3)
        CRON_TIME="0 0 * * *"
        DESC="Daily at midnight"
        ;;
    4)
        echo ""
        echo "Enter cron time expression (e.g., '0 22 * * *' for 10 PM daily):"
        read -p "Cron time: " CRON_TIME
        DESC="Custom schedule: $CRON_TIME"
        ;;
    *)
        echo -e "${RED}✗ Invalid choice${NC}"
        exit 1
        ;;
esac

# Create new cron entry
NEW_CRON_ENTRY="$CRON_TIME cd $SCRIPT_DIR && $CRON_SCRIPT >> $SCRIPT_DIR/logs/cron_output.log 2>&1"

# Add to crontab
if [ -z "$CURRENT_CRON" ]; then
    echo "$NEW_CRON_ENTRY" | crontab -
else
    (echo "$CURRENT_CRON"; echo "$NEW_CRON_ENTRY") | crontab -
fi

# Verify installation
if crontab -l 2>/dev/null | grep -q "daily_update_v2.sh"; then
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Cron job installed successfully!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Schedule: $DESC"
    echo "Script: $CRON_SCRIPT"
    echo "Log file: $SCRIPT_DIR/logs/daily_update_v2_YYYYMMDD.log"
    echo "Cron output: $SCRIPT_DIR/logs/cron_output.log"
    echo ""
    echo "What runs daily:"
    echo "  • Data updates (prices, dividends, companies)"
    echo "  • Future dividend calendar"
    echo "  • Company data refresh (limited)"
    echo ""
    echo "What runs weekly:"
    echo "  • Symbol discovery (Sundays)"
    echo "  • ETF holdings update (Saturdays)"
    echo ""
    echo "To view cron jobs:"
    echo "  crontab -l"
    echo ""
    echo "To remove this cron job:"
    echo "  crontab -e"
    echo "  (then delete the line with 'daily_update_v2.sh')"
    echo ""
    echo "To test the script manually:"
    echo "  cd $SCRIPT_DIR"
    echo "  ./daily_update_v2.sh"
    echo ""
else
    echo -e "${RED}✗ Failed to install cron job${NC}"
    exit 1
fi
