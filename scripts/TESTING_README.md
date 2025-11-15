# Automated Rate Limiting Tests

This directory contains scripts for automated hourly testing of the API rate limiting system with detailed file logging.

## Files

- **`run_hourly_tests.py`** - Main test runner that executes all rate limiting tests and writes detailed logs
- **`setup_hourly_tests.sh`** - Setup script to configure the cron job for hourly execution
- **Test suites**:
  - `../tests/test_rate_limits_simple.py` - Basic rate limiting tests (7 tests)
  - `../tests/test_all_tiers.py` - Comprehensive tier-based tests (free, enterprise)

## Setup

### Run Setup Script

```bash
./scripts/setup_hourly_tests.sh
```

This will:
1. Create necessary log directories
2. Create a cron job to run tests every hour
3. Configure logging to `logs/test_runs/`
4. Optionally run a test to verify everything works

## Manual Testing

Run tests manually at any time:

```bash
# Run all tests with detailed logging
./scripts/run_hourly_tests.py

# Run individual test suites
python3 tests/test_rate_limits_simple.py
python3 tests/test_all_tiers.py
```

## Log Files

### Log Structure

Each test run creates two files:

1. **Detailed Log** (`test_run_YYYYMMDD_HHMMSS.log`)
   - Full test output with all details
   - Pass/fail status for each test
   - Complete stdout/stderr from test execution
   - Test durations

2. **JSON Summary** (`test_run_YYYYMMDD_HHMMSS.json`)
   - Machine-readable test summary
   - Run ID, timestamp, duration
   - Test results with pass/fail status
   - Perfect for monitoring dashboards

### Symlinks for Latest Results

The system maintains symlinks to the most recent test run:
- `logs/test_runs/latest.log` → Latest detailed log
- `logs/test_runs/latest.json` → Latest JSON summary

### Example Log File

```
================================================================================
DIVV API RATE LIMITING TEST RUN
================================================================================
Run ID: 20251114_191053
Timestamp: 2025-11-14 19:11:22
Total Tests: 2
Passed: 2
Failed: 0
Duration: 29.31s
Status: ✅ PASS
================================================================================

================================================================================
TEST: test_rate_limits_simple.py
================================================================================
Status: ✅ PASS
Duration: 9.05s

OUTPUT:
--------------------------------------------------------------------------------
[Full test output here...]
```

### Example JSON Summary

```json
{
  "run_id": "20251114_191053",
  "timestamp": "2025-11-14T19:11:22.574304",
  "summary": {
    "total": 2,
    "passed": 2,
    "failed": 0,
    "duration": 29.31
  },
  "results": [
    {
      "name": "test_rate_limits_simple.py",
      "success": true,
      "duration": 9.05
    },
    {
      "name": "test_all_tiers.py",
      "success": true,
      "duration": 20.26
    }
  ]
}
```

## Viewing Logs

### View Latest Results

```bash
# View latest detailed log
cat logs/test_runs/latest.log

# View latest JSON summary
cat logs/test_runs/latest.json

# Pretty-print JSON with jq
cat logs/test_runs/latest.json | jq
```

### List All Test Runs

```bash
# List all test runs (newest first)
ls -lt logs/test_runs/

# Count total test runs
ls -1 logs/test_runs/test_run_*.log | wc -l

# Show only failed runs (exit code 1)
grep -l "Status: ❌ FAIL" logs/test_runs/*.log
```

### View Specific Test Run

```bash
# View a specific run
cat logs/test_runs/test_run_20251114_191053.log

# View only the summary
head -20 logs/test_runs/test_run_20251114_191053.log

# Search for failures
grep -A 10 "❌ FAIL" logs/test_runs/*.log
```

### View Cron Execution Logs

```bash
# View cron output (script stdout/stderr)
tail -f logs/hourly_tests_cron.log

# View last 100 lines
tail -100 logs/hourly_tests_cron.log

# See when cron last ran
ls -l logs/test_runs/latest.log
```

## Cron Job Details

### Schedule

```
0 * * * *
```

- Runs at the top of every hour (00:00, 01:00, 02:00, etc.)
- Total: 24 executions per day

### Cron Job Command

```bash
cd /Users/toan/dev/high-yield-dividend-analysis && \
source .env 2>/dev/null && \
./scripts/run_hourly_tests.py >> logs/hourly_tests_cron.log 2>&1
```

### Managing Cron Jobs

```bash
# View all cron jobs
crontab -l

# Edit cron jobs manually
crontab -e

# Remove all cron jobs
crontab -r

# Remove only this cron job
crontab -l | grep -v "run_hourly_tests.py" | crontab -
```

## Log Management

### Log Rotation

To prevent log files from accumulating indefinitely, set up automatic cleanup:

#### Option 1: Logrotate (Linux)

```bash
# Create logrotate config
sudo tee /etc/logrotate.d/divv-tests > /dev/null <<EOF
/Users/toan/dev/high-yield-dividend-analysis/logs/test_runs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
}
EOF
```

#### Option 2: Cron Cleanup (macOS/Linux)

Add to crontab to keep only last 30 days:

```bash
# Clean up test logs older than 30 days (runs daily at 3am)
0 3 * * * find /Users/toan/dev/high-yield-dividend-analysis/logs/test_runs -name 'test_run_*.log' -mtime +30 -delete
0 3 * * * find /Users/toan/dev/high-yield-dividend-analysis/logs/test_runs -name 'test_run_*.json' -mtime +30 -delete
```

### Manual Cleanup

```bash
# Delete logs older than 30 days
find logs/test_runs -name 'test_run_*.log' -mtime +30 -delete
find logs/test_runs -name 'test_run_*.json' -mtime +30 -delete

# Keep only last 100 test runs
cd logs/test_runs
ls -t test_run_*.log | tail -n +101 | xargs rm
ls -t test_run_*.json | tail -n +101 | xargs rm

# Delete all test logs (keep latest symlink)
rm logs/test_runs/test_run_*.log logs/test_runs/test_run_*.json
```

## Monitoring and Alerts

### Check for Failures

```bash
# Check if latest run failed
if [ $? -ne 0 ]; then echo "Latest test failed!"; fi

# Count failures in last 24 hours
find logs/test_runs -name '*.json' -mtime -1 -exec jq -r 'select(.summary.failed > 0) | .run_id' {} \; | wc -l

# Get failure summary for last 7 days
for file in $(find logs/test_runs -name '*.json' -mtime -7); do
  jq -r '"[\(.run_id)] Failed: \(.summary.failed)/\(.summary.total)"' $file
done
```

### Integration with Monitoring Tools

#### Prometheus Metrics

Create a simple metrics exporter:

```python
#!/usr/bin/env python3
import json
import os
from datetime import datetime

log_file = "logs/test_runs/latest.json"
with open(log_file) as f:
    data = json.load(f)

print(f"# HELP divv_tests_total Total tests run")
print(f"# TYPE divv_tests_total gauge")
print(f"divv_tests_total {data['summary']['total']}")

print(f"# HELP divv_tests_passed Tests passed")
print(f"# TYPE divv_tests_passed gauge")
print(f"divv_tests_passed {data['summary']['passed']}")

print(f"# HELP divv_tests_failed Tests failed")
print(f"# TYPE divv_tests_failed gauge")
print(f"divv_tests_failed {data['summary']['failed']}")
```

#### Slack/Discord Webhook (Optional)

```bash
# Add to run_hourly_tests.py or create wrapper script
WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

if [ $failed -gt 0 ]; then
  curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"❌ DIVV API Tests Failed: $failed/$total\"}" \
    $WEBHOOK_URL
fi
```

## Troubleshooting

### No Logs Being Created

1. **Check script is executable**:
   ```bash
   chmod +x scripts/run_hourly_tests.py
   ```

2. **Check log directory exists**:
   ```bash
   mkdir -p logs/test_runs
   ```

3. **Run script manually to see errors**:
   ```bash
   ./scripts/run_hourly_tests.py
   ```

### Cron Job Not Running

1. **Check cron service is running**:
   ```bash
   # macOS
   sudo launchctl list | grep cron

   # Linux
   systemctl status cron
   ```

2. **Verify cron job exists**:
   ```bash
   crontab -l | grep run_hourly_tests
   ```

3. **Check cron execution logs** (macOS):
   ```bash
   log show --predicate 'eventMessage contains "cron"' --last 1h
   ```

4. **Test script runs correctly**:
   ```bash
   cd /Users/toan/dev/high-yield-dividend-analysis
   ./scripts/run_hourly_tests.py
   ```

### Tests Failing

1. **Ensure API is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check database connection**:
   ```bash
   python3 -c "from supabase_helpers import get_supabase_client; print('OK')"
   ```

3. **Verify test API keys exist**:
   ```bash
   python3 /tmp/create_test_key.py
   ```

4. **Check latest test output**:
   ```bash
   cat logs/test_runs/latest.log
   ```

## Test Coverage

### test_rate_limits_simple.py (7 tests)

- ✅ Valid Request - API key works correctly
- ✅ Per-Minute Limit - Rate limiting triggers after burst limit
- ✅ Rate Limit Headers - Headers present on all responses
- ✅ Health Endpoint - Health check bypasses rate limiting
- ✅ Concurrent Requests - Multiple requests handled correctly
- ✅ Invalid API Key - Returns 401 for invalid keys
- ✅ No API Key - Passes through (caught by auth middleware)

### test_all_tiers.py (2 tiers × 3 tests = 6 tests)

**Per Tier**:
- ✅ Tier Identification - Correct tier reported in headers
- ✅ Reported Limits - Monthly and per-minute limits match configuration
- ✅ Burst Limit Enforcement - Burst limits properly enforced

**Tiers Tested**:
- Free (10k/month, 10/min, burst 20)
- Enterprise (999M/month, 1000/min, burst 2000)

## Customization

### Change Schedule

Edit the cron schedule in `setup_hourly_tests.sh`:

```bash
# Every hour (current)
0 * * * *

# Every 30 minutes
*/30 * * * *

# Every 6 hours
0 */6 * * *

# Every 15 minutes
*/15 * * * *

# Daily at 2 AM
0 2 * * *
```

### Add More Tests

Add test files to the `TEST_FILES` list in `run_hourly_tests.py`:

```python
TEST_FILES = [
    "tests/test_rate_limits_simple.py",
    "tests/test_all_tiers.py",
    "tests/your_new_test.py"  # Add here
]
```

### Change Log Directory

Edit `LOG_DIR` in `run_hourly_tests.py`:

```python
LOG_DIR = os.path.join(WORK_DIR, "logs", "test_runs")
# Change to:
LOG_DIR = "/custom/path/to/logs"
```

## Production Deployment

For production environments, consider:

1. **Central Log Aggregation** - Ship logs to CloudWatch, Datadog, ELK
2. **Monitoring Alerts** - Set up PagerDuty, OpsGenie for failures
3. **Task Scheduler** - Use systemd timers or Kubernetes CronJobs
4. **Metrics Collection** - Export to Prometheus, Grafana
5. **Historical Analysis** - Store test results in database for trending

Example systemd timer (Linux):

```ini
# /etc/systemd/system/divv-tests.timer
[Unit]
Description=Hourly DIVV API Rate Limiting Tests

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```
