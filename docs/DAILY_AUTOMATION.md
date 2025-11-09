# Daily Automation Setup

**Date**: October 12, 2025
**Status**: ✅ Ready for production

## Overview

Automated daily stock data updates using `daily_update_v2.sh` with cron scheduling. Includes prices, dividends, company info, ETF holdings, and future dividend calendar.

---

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
cd /Users/toan/dev/high-yield-dividend-analysis
./setup_daily_cron.sh
```

Follow the prompts to:
1. Choose update schedule (10 PM daily recommended)
2. Confirm installation
3. Done!

### Option 2: Manual Cron Setup

```bash
# Edit crontab
crontab -e

# Add this line (runs at 10 PM daily):
0 22 * * * cd /Users/toan/dev/high-yield-dividend-analysis && ./daily_update_v2.sh >> logs/cron_output.log 2>&1
```

### Option 3: Test Run (No Cron)

```bash
cd /Users/toan/dev/high-yield-dividend-analysis
./daily_update_v2.sh
```

---

## What Gets Updated

### Daily Operations

**Every Day**:
- ✅ Price updates for all symbols
- ✅ Dividend history updates
- ✅ Company info updates (name, sector, AUM, expense ratio)
- ✅ ETF holdings update (portfolio compositions)
- ✅ Future dividend calendar (90 days ahead)
- ✅ Company data refresh (fixes NULL values, limited to 100/day)

### Weekly Operations

**Sunday** (weekly):
- 🔍 Symbol discovery (find new stocks/ETFs)
- ✅ Symbol validation
- 📊 Add valid symbols to database
- 🏷️  ETF classification (investment_strategy, related_stock)


---

## Schedule Options

### Recommended: 10 PM Daily
```bash
# Cron: 0 22 * * *
```
**Why?**: Markets are closed, data is finalized, low system load

### Alternative: 6 AM Daily
```bash
# Cron: 0 6 * * *
```
**Why?**: Fresh data ready before market open

### Alternative: Midnight
```bash
# Cron: 0 0 * * *
```
**Why?**: Traditional batch processing time

---

## Log Files

### Daily Logs
```bash
logs/daily_update_v2_YYYYMMDD.log
```
- Detailed execution logs
- One file per day
- Auto-rotated (kept for 30 days)

### Cron Output
```bash
logs/cron_output.log
```
- Cron execution summary
- Errors and warnings
- Manual rotation recommended

### View Recent Logs
```bash
# Today's log
tail -f logs/daily_update_v2_$(date +%Y%m%d).log

# Yesterday's log
tail -100 logs/daily_update_v2_$(date -v-1d +%Y%m%d).log

# All logs from this week
ls -lht logs/daily_update_v2_*.log | head -7
```

---

## Monitoring

### Check Cron Status
```bash
# View installed cron jobs
crontab -l

# Check cron service (macOS)
launchctl list | grep cron
```

### Check Last Run
```bash
# View last log file
ls -t logs/daily_update_v2_*.log | head -1 | xargs tail -50

# Check for errors
grep "❌" logs/daily_update_v2_$(date +%Y%m%d).log

# Check completion status
grep "COMPLETED" logs/daily_update_v2_$(date +%Y%m%d).log
```

### Database Status
```bash
# Run status report
python3 -c "
from supabase_helpers import get_supabase_client
supabase = get_supabase_client()

result = supabase.table('stocks').select('symbol', count='exact').execute()
print(f'Total symbols: {result.count:,}')

with_prices = supabase.table('stocks').select('symbol', count='exact').not_.is_('price', 'null').execute()
print(f'With prices: {with_prices.count:,}')

with_holdings = supabase.table('stocks').select('symbol', count='exact').not_.is_('holdings', 'null').execute()
print(f'ETFs with holdings: {with_holdings.count:,}')
"
```

---

## Troubleshooting

### Cron Not Running

**Check if cron has Full Disk Access** (macOS):
1. System Preferences → Security & Privacy → Privacy
2. Select "Full Disk Access"
3. Add `/usr/sbin/cron` if not present

**Test manually**:
```bash
cd /Users/toan/dev/high-yield-dividend-analysis
./daily_update_v2.sh
```

### Docker Not Starting

**Check Docker installation**:
```bash
/Applications/Docker.app/Contents/Resources/bin/docker --version
```

**Start Docker manually**:
```bash
open -a Docker
```

### Supabase Connection Errors

**Check containers**:
```bash
/Applications/Docker.app/Contents/Resources/bin/docker ps --filter "name=dividend-tracker"
```

**Restart Supabase**:
```bash
cd /Users/toan/dev/ai-dividend-tracker
/Applications/Docker.app/Contents/Resources/bin/docker compose restart
```

### Virtual Environment Issues

**Recreate venv**:
```bash
cd /Users/toan/dev/high-yield-dividend-analysis
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Customization

### Change Update Frequency

**Edit cron schedule**:
```bash
crontab -e
```

**Common patterns**:
```bash
# Every 6 hours
0 */6 * * *

# Twice daily (6 AM and 6 PM)
0 6,18 * * *

# Weekdays only at 10 PM
0 22 * * 1-5
```

### Modify What Gets Updated

Edit `daily_update_v2.sh`:

```bash
# Disable discovery (runs weekly by default)
# Comment out lines 95-107

# Run holdings update daily instead of weekly
# Change line 128 condition from 'eq 6' to remove the if block

# Skip future dividends
# Comment out lines 158-167
```

### Add Email Notifications

Add to end of `daily_update_v2.sh`:

```bash
# Send email on completion
if [ "$OVERALL_SUCCESS" = true ]; then
    echo "Daily update completed successfully" | mail -s "Stock Update: Success" your@email.com
else
    echo "Daily update had errors. Check logs." | mail -s "Stock Update: ERRORS" your@email.com
fi
```

---

## Performance Notes

### Execution Time

**Typical durations**:
- Discovery (weekly): 10-20 minutes
- Price updates: 30-60 minutes (depends on symbol count)
- Dividend updates: 15-30 minutes
- Company updates: 5-10 minutes
- Holdings (weekly): 20-40 minutes (depends on ETF count)

**Total time**: ~1-2 hours for daily run, ~2-3 hours on weekends (with discovery/holdings)

### Resource Usage

- **CPU**: Moderate (parallel API requests)
- **Memory**: ~500MB-1GB
- **Network**: ~100-500MB data transfer
- **Disk**: ~100MB logs per month

### Rate Limits

FMP API limits are respected:
- 144 concurrent requests (configurable)
- Automatic backoff on 429 errors
- Exponential retry logic

---

## Maintenance

### Weekly Tasks

✅ **Automated** (no action needed):
- Symbol discovery (Sundays)
- ETF holdings update (Saturdays)

### Monthly Tasks

📋 **Manual**:
- Review error logs for patterns
- Check database size and performance
- Update excluded symbols list if needed

### Quarterly Tasks

📋 **Manual**:
- Review and update API keys
- Check for library updates (`pip list --outdated`)
- Verify cron is still running

---

## Backup Strategy

### Before Automation

**Backup database**:
```bash
/Applications/Docker.app/Contents/Resources/bin/docker exec dividend-tracker-supabase-db \
  pg_dump -U postgres postgres > backup_$(date +%Y%m%d).sql
```

### Restore from Backup
```bash
cat backup_YYYYMMDD.sql | \
/Applications/Docker.app/Contents/Resources/bin/docker exec -i dividend-tracker-supabase-db \
  psql -U postgres postgres
```

---

## Uninstall

### Remove Cron Job
```bash
crontab -e
# Delete the line containing 'daily_update_v2.sh'
# Save and exit
```

### Remove Scripts
```bash
cd /Users/toan/dev/high-yield-dividend-analysis
rm daily_update_v2.sh setup_daily_cron.sh
```

### Keep Logs (Optional)
```bash
# Logs are in logs/ directory
# Remove manually if desired:
rm -rf logs/daily_update_v2_*.log
```

---

## Summary

✅ **Daily automation ready**
✅ **Cron setup script provided** (`setup_daily_cron.sh`)
✅ **Comprehensive logging**
✅ **Error handling and retry logic**
✅ **Docker + Supabase health checks**
✅ **Weekly discovery and holdings updates**
✅ **30-day log retention**

**Run setup**: `./setup_daily_cron.sh`
**Test manually**: `./daily_update_v2.sh`
**View logs**: `tail -f logs/daily_update_v2_$(date +%Y%m%d).log`
