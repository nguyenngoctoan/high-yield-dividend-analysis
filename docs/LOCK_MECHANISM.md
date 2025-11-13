# Daily Update Lock Mechanism

## Overview

The daily update script now includes a lock file mechanism to **prevent concurrent runs**. This ensures only one instance runs at a time, avoiding database conflicts and resource contention.

## How It Works

### Lock Files

Two files are used:
- **`.daily_update.lock`** - Simple lock file marker
- **`.daily_update.pid`** - Contains the process ID of the running instance

### Behavior

**When script starts:**
1. Checks if lock files exist
2. If lock exists, verifies the PID is actually running
3. If running, **exits immediately** with message
4. If stale (process not running), removes lock and continues
5. Creates new lock files with current PID
6. Cleans up lock files on exit (normal or interrupted)

## Example Scenarios

### Scenario 1: Attempt Concurrent Run

```bash
# First run
./daily_update_v3_parallel.sh &

# Second run (while first is still running)
./daily_update_v3_parallel.sh

# Output:
⚠️  DAILY UPDATE ALREADY RUNNING
Another instance is already running (PID: 12345)
Exiting to prevent concurrent runs...
```

### Scenario 2: Stale Lock (Crashed Previous Run)

```bash
# Old lock exists but process died
./daily_update_v3_parallel.sh

# Output:
⚠️  Stale lock file detected (PID 99999 not running)
Removing stale lock and continuing...
🚀 DAILY STOCK DATA UPDATE V3 (PARALLEL) STARTED...
```

### Scenario 3: Normal Run

```bash
./daily_update_v3_parallel.sh

# Output:
🚀 DAILY STOCK DATA UPDATE V3 (PARALLEL) STARTED...
Process ID: 12345
Lock file created: .daily_update.lock
```

## Manual Intervention

### Check Current Lock Status

```bash
# Check if locked
if [ -f ".daily_update.lock" ]; then
    echo "Locked"
    cat .daily_update.pid
else
    echo "Not locked"
fi
```

### Force Unlock (If Needed)

```bash
# Only do this if you're SURE no script is running
rm -f .daily_update.lock .daily_update.pid
```

### Check Running Process

```bash
# View current daily update processes
ps aux | grep daily_update_v3_parallel.sh | grep -v grep
```

## Benefits

1. **Prevents Double Updates** - No duplicate processing
2. **Avoids Database Conflicts** - No concurrent writes to same tables
3. **Saves Resources** - Doesn't waste API calls/compute
4. **Smart Cleanup** - Automatically removes stale locks
5. **Cron-Safe** - Multiple cron entries won't conflict

## Cron Configuration

Safe to use aggressive cron schedules:

```cron
# Every 6 hours (only runs if previous finished)
0 */6 * * * cd /path/to/project && ./daily_update_v3_parallel.sh

# Or optimal time (10 PM daily)
0 22 * * * cd /path/to/project && ./daily_update_v3_parallel.sh
```

Even if cron triggers overlap, only one will run.

## Troubleshooting

### Issue: "Already Running" but Nothing is Running

**Cause:** Stale lock from crash or forced termination

**Solution:**
```bash
# Check if actually running
ps aux | grep daily_update

# If nothing, remove lock
rm -f .daily_update.lock .daily_update.pid
```

### Issue: Script Won't Start

**Symptom:** Immediately exits with "already running" message

**Check:**
```bash
# View the PID that's holding the lock
cat .daily_update.pid

# Check if that PID is our script
ps -p $(cat .daily_update.pid) -o command=
```

### Issue: Lock Not Cleaning Up

**Cause:** Script killed with `kill -9` (doesn't allow cleanup)

**Prevention:** Use graceful termination:
```bash
# Good (allows cleanup)
kill $(cat .daily_update.pid)

# Bad (doesn't allow cleanup)
kill -9 $(cat .daily_update.pid)
```

## Integration with Monitoring

### Check Lock in Monitoring

```bash
# monitoring script
if [ -f ".daily_update.lock" ]; then
    PID=$(cat .daily_update.pid)
    RUNTIME=$(ps -p $PID -o etime= 2>/dev/null)
    echo "Update running for: $RUNTIME (PID: $PID)"
else
    echo "No update running"
fi
```

### Alert on Long-Running Updates

```bash
# Alert if running > 2 hours
if [ -f ".daily_update.lock" ]; then
    PID=$(cat .daily_update.pid)
    START_TIME=$(ps -p $PID -o lstart= 2>/dev/null)
    # ... check if > 2 hours and alert
fi
```

## Summary

✅ **Automatic** - No configuration needed
✅ **Smart** - Detects and removes stale locks
✅ **Safe** - Prevents concurrent runs
✅ **Robust** - Handles crashes and interruptions
✅ **Cron-friendly** - Works with any schedule

The lock mechanism makes the daily update script production-ready for automated scheduling!

---

*Added: 2025-11-12*
*Part of the daily update optimization suite*
