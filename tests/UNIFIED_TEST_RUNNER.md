# Unified Test Runner

The unified test runner combines all test suites into a single automated testing system that runs hourly via cron.

## 🚀 NEW: API Auto-Start Wrapper

The test runner now includes an intelligent wrapper script (`run_tests_with_api.sh`) that:
- ✅ Checks if API server is running
- ✅ Automatically starts API if not running
- ✅ Waits for API to be healthy before running tests
- ✅ Keeps API running for subsequent test cycles
- ✅ Logs API server output separately

**Cron Command**:
```bash
0 * * * * /Users/toan/dev/high-yield-dividend-analysis/scripts/run_tests_with_api.sh >> \
  /Users/toan/dev/high-yield-dividend-analysis/logs/hourly_tests_cron.log 2>&1
```

**Additional Logs**:
- API server log: `logs/api_server.log`
- API PID file: `logs/api_server.pid`

## Quick Reference

### Test Schedule
- **Frequency**: Every hour at minute 0 (`0 * * * *`)
- **Next run**: Top of the next hour (e.g., 00:00, 01:00, 02:00, etc.)
- **Total runs**: 24 per day

### Test Suites Included

| Test Suite | File | Purpose | Duration |
|------------|------|---------|----------|
| Rate Limiting | `test_rate_limits_simple.py` | Basic rate limit enforcement (7 tests) | ~10s |
| Tier Tests | `test_all_tiers.py` | Free & Enterprise tier validation | ~22s |
| Data Quality | `test_data_quality.py` | Data validation checks | ~2s |
| API Endpoints | `test_api_endpoints.py` | API endpoint tests with seed data (pytest) | ~5s |

**Total**: ~40s per run

## Results Location

### Detailed Logs
```
/Users/toan/dev/high-yield-dividend-analysis/logs/test_runs/
```

Each run creates two files:
- `test_run_YYYYMMDD_HHMMSS.log` - Full detailed log
- `test_run_YYYYMMDD_HHMMSS.json` - Machine-readable JSON summary

### Latest Results (Symlinks)
```bash
# View latest detailed log
cat /Users/toan/dev/high-yield-dividend-analysis/logs/test_runs/latest.log

# View latest JSON summary
cat /Users/toan/dev/high-yield-dividend-analysis/logs/test_runs/latest.json | jq

# Quick status check
jq -r '"[\(.run_id)] \(.summary.passed)/\(.summary.total) passed"' \
  /Users/toan/dev/high-yield-dividend-analysis/logs/test_runs/latest.json
```

### Cron Output
```bash
# View cron execution log
tail -f /Users/toan/dev/high-yield-dividend-analysis/logs/hourly_tests_cron.log

# Check last 100 lines
tail -100 /Users/toan/dev/high-yield-dividend-analysis/logs/hourly_tests_cron.log
```

## Manual Execution

### Run All Tests Manually
```bash
cd /Users/toan/dev/high-yield-dividend-analysis
./scripts/run_hourly_tests.py
```

### Run Individual Test Suite
```bash
# Rate limiting tests
python3 tests/test_rate_limits_simple.py

# Tier tests
python3 tests/test_all_tiers.py

# Data quality tests
python3 tests/test_data_quality.py

# API endpoint tests
pytest tests/test_api_endpoints.py -v
```

### Run New Integration Tests (Separate)
```bash
# API endpoint tests only
cd /Users/toan/dev/high-yield-dividend-analysis/tests
pytest test_api_endpoints.py -v

# Run all via bash script
./run_tests.sh

# Google Sheets tests (manual - requires Apps Script)
# See: tests/test_divv_integration.js
```

## Monitoring

### Check Latest Run Status
```bash
# JSON summary
cat logs/test_runs/latest.json | jq .summary

# Example output:
# {
#   "total": 4,
#   "passed": 4,
#   "failed": 0,
#   "duration": 39.8
# }
```

### List All Test Runs
```bash
# Show all runs (newest first)
ls -lt logs/test_runs/test_run_*.log

# Count total runs
ls -1 logs/test_runs/test_run_*.log | wc -l

# Show last 10 runs
ls -t logs/test_runs/test_run_*.json | head -10
```

### Find Failed Runs
```bash
# Find all failed runs
grep -l "\"failed\": [1-9]" logs/test_runs/*.json

# Show failure details
for file in logs/test_runs/*.json; do
  FAILED=$(jq -r .summary.failed $file)
  if [ "$FAILED" -gt 0 ]; then
    RUN_ID=$(jq -r .run_id $file)
    echo "❌ $RUN_ID - $FAILED test(s) failed"
  fi
done
```

### Check Test Trends (Last 24 Hours)
```bash
# Show pass/fail for last 24 hours
find logs/test_runs -name '*.json' -mtime -1 -exec \
  jq -r '"[\(.timestamp)] \(.summary.passed)/\(.summary.total) passed"' {} \; | \
  sort -r
```

## Cron Management

### View Cron Job
```bash
crontab -l | grep run_hourly_tests
```

### Edit Cron Schedule
```bash
# Open crontab editor
crontab -e

# Current schedule: 0 * * * * (every hour)
# Change to every 30 minutes: */30 * * * *
# Change to every 6 hours: 0 */6 * * *
```

### Disable Hourly Tests
```bash
# Remove the cron job
crontab -l | grep -v "run_hourly_tests" | crontab -
```

### Re-enable Hourly Tests
```bash
# Run setup script again
./scripts/setup_hourly_tests.sh
```

## Log Management

### Automatic Cleanup
The logs will accumulate over time. Set up automatic cleanup to keep only recent logs:

```bash
# Add to crontab (keeps last 30 days, runs daily at 3am)
0 3 * * * find /Users/toan/dev/high-yield-dividend-analysis/logs/test_runs -name 'test_run_*.log' -mtime +30 -delete
0 3 * * * find /Users/toan/dev/high-yield-dividend-analysis/logs/test_runs -name 'test_run_*.json' -mtime +30 -delete
```

### Manual Cleanup
```bash
# Delete logs older than 30 days
find logs/test_runs -name 'test_run_*.*' -mtime +30 -delete

# Keep only last 100 runs
cd logs/test_runs
ls -t test_run_*.log | tail -n +101 | xargs rm -f
ls -t test_run_*.json | tail -n +101 | xargs rm -f

# View disk usage
du -sh logs/test_runs
```

## Test Results Format

### JSON Summary Structure
```json
{
  "run_id": "20251114_231548",
  "timestamp": "2025-11-14T23:15:48.123456",
  "summary": {
    "total": 4,
    "passed": 4,
    "failed": 0,
    "duration": 39.84
  },
  "results": [
    {
      "name": "test_rate_limits_simple.py",
      "success": true,
      "duration": 10.25
    },
    {
      "name": "test_all_tiers.py",
      "success": true,
      "duration": 21.98
    },
    {
      "name": "test_data_quality.py",
      "success": true,
      "duration": 1.57
    },
    {
      "name": "test_api_endpoints.py",
      "success": true,
      "duration": 6.04
    }
  ]
}
```

### Log File Structure
```
================================================================================
DIVV API UNIFIED TEST RUN
================================================================================
Run ID: 20251114_231548
Timestamp: 2025-11-14 23:15:48
Total Tests: 4
Passed: 4
Failed: 0
Duration: 39.84s
Status: ✅ PASS
================================================================================

================================================================================
TEST: test_rate_limits_simple.py
================================================================================
Status: ✅ PASS
Duration: 10.25s

OUTPUT:
--------------------------------------------------------------------------------
[Full test output here...]
================================================================================

[Repeat for each test suite...]
```

## Troubleshooting

### Tests Always Failing
**Problem**: All tests fail with connection errors

**Solution**: Ensure API is running
```bash
# Check if API is running
curl http://localhost:8000/health

# If not running, check if it should be started automatically
# or add API startup to cron before tests
```

### No Logs Being Created
**Problem**: No log files in `logs/test_runs/`

**Solution**:
```bash
# 1. Check script is executable
chmod +x scripts/run_hourly_tests.py

# 2. Check log directory exists
mkdir -p logs/test_runs

# 3. Run manually to see errors
./scripts/run_hourly_tests.py
```

### Cron Not Running
**Problem**: No new logs at the top of each hour

**Solution**:
```bash
# 1. Verify cron job exists
crontab -l | grep run_hourly_tests

# 2. Check macOS allows cron
# System Preferences > Security & Privacy > Full Disk Access
# Add Terminal or cron to allowed apps

# 3. Check cron service (Linux)
systemctl status cron

# 4. Test the exact cron command manually
cd /Users/toan/dev/high-yield-dividend-analysis && \
source .env 2>/dev/null && \
./scripts/run_hourly_tests.py
```

### High Disk Usage
**Problem**: Test logs taking up too much space

**Solution**:
```bash
# Check current usage
du -sh logs/test_runs

# Set up automatic cleanup (see Log Management above)

# Or clean up old logs manually
find logs/test_runs -name 'test_run_*.*' -mtime +7 -delete
```

## Integration with Monitoring Tools

### Prometheus Metrics Exporter
Create a simple metrics file for Prometheus:

```python
#!/usr/bin/env python3
# Export latest test results as Prometheus metrics
import json

with open('logs/test_runs/latest.json') as f:
    data = json.load(f)

print(f"# HELP divv_tests_total Total test suites run")
print(f"# TYPE divv_tests_total gauge")
print(f"divv_tests_total {data['summary']['total']}")

print(f"# HELP divv_tests_passed Test suites passed")
print(f"# TYPE divv_tests_passed gauge")
print(f"divv_tests_passed {data['summary']['passed']}")

print(f"# HELP divv_tests_failed Test suites failed")
print(f"# TYPE divv_tests_failed gauge")
print(f"divv_tests_failed {data['summary']['failed']}")

print(f"# HELP divv_tests_duration_seconds Test run duration")
print(f"# TYPE divv_tests_duration_seconds gauge")
print(f"divv_tests_duration_seconds {data['summary']['duration']}")
```

### Slack/Discord Alerts
Add webhook notification for failures:

```bash
# Add to scripts/run_hourly_tests.py or create wrapper
WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

if [ $FAILED -gt 0 ]; then
  curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"❌ DIVV Tests Failed: $FAILED/$TOTAL at $(date)\"}" \
    $WEBHOOK_URL
fi
```

## Related Documentation

- [Rate Limiting Tests](./README.md) - Original rate limiting test documentation
- [API Endpoint Tests](./TESTING_README.md) - New API endpoint test documentation
- [Test Data](./seed_data.json) - Seed data for API tests
- [Setup Script](../scripts/setup_hourly_tests.sh) - Cron setup script
- [Test Runner](../scripts/run_hourly_tests.py) - Main test runner script
