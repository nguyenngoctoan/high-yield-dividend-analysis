# Database Backup System

## Overview

The database backup system automatically creates daily compressed backups of all critical price data tables.

## Features

- **Full database backup**: Backs up all data tables in one compressed file
- **Automatic compression**: Uses gzip to compress backups (~82% compression ratio)
- **Retention policy**: Keeps backups for 14 days, automatically deletes older backups
- **Detailed logging**: Tracks backup status, file sizes, and row counts
- **Error handling**: Reports failures without breaking the daily update process
- **Integrated**: Runs automatically as part of the daily update (`daily_update_v2.sh`)

## Backup Statistics (Example Run)

- **Uncompressed size**: 15 GB
- **Compressed size**: 2.7 GB (82% compression)
- **Tables backed up**:
  - `raw_stock_prices`: 20,454,716 rows
  - `raw_dividends`: 300,641 rows
  - `raw_stocks`: 24,842 rows
  - `raw_future_dividends`: varies
  - `raw_holdings_history`: varies
- **Backup duration**: ~10-11 minutes (6 min dump + 5 min compression)
- **Storage**: With 14-day retention, expect ~38GB max

## Backup Location

```
/Users/toan/dev/high-yield-dividend-analysis/backups/
├── 20251108/
│   └── full_backup_20251108_172832.sql.gz
├── 20251109/
│   └── full_backup_20251109_220000.sql.gz
└── ... (up to 30 days)
```

## Log Files

```
/Users/toan/dev/high-yield-dividend-analysis/logs/
└── backup_20251108.log
```

## Manual Backup

To create a manual backup:

```bash
cd /Users/toan/dev/high-yield-dividend-analysis
./scripts/backup_database.sh
```

## Restoring from Backup

To restore a backup:

```bash
# 1. Decompress the backup
gunzip -k backups/20251108/full_backup_20251108_172832.sql.gz

# 2. Make sure Supabase is running
cd /Users/toan/dev/ai-dividend-tracker
npx supabase start

# 3. Restore the backup (⚠️  WARNING: This will replace existing data!)
PGPASSWORD=postgres psql \
  -h 127.0.0.1 \
  -p 54322 \
  -U postgres \
  -d postgres \
  -f /Users/toan/dev/high-yield-dividend-analysis/backups/20251108/full_backup_20251108_172832.sql
```

## Configuration

Edit `scripts/backup_database.sh` to customize:

- **Retention period**: Change `RETENTION_DAYS` (default: 14 days)
- **Backup location**: Change `BACKUP_DIR`
- **Database connection**: Update `DB_HOST`, `DB_PORT`, etc.

## Integration with Daily Update

The backup runs as **Step 6** in `daily_update_v2.sh`:

1. Discovery (weekly on Sundays)
2. Data Update (prices, dividends, companies)
3. Refresh NULL company data
4. ETF Holdings Update
5. Future Dividends Calendar
6. **Database Backup** ← New step
7. Database Status Report

## Monitoring

Check backup status:

```bash
# View today's backup log
tail -50 logs/backup_$(date '+%Y%m%d').log

# List all backups
ls -lh backups/*/

# Check total backup storage
du -sh backups/
```

## Troubleshooting

### Backup fails with "Database not accessible"

**Solution**: Make sure Supabase is running:
```bash
cd /Users/toan/dev/ai-dividend-tracker
npx supabase start
```

### Backup file is too large

**Solution**: The compressed backups are ~2.7GB. This is normal for 20M+ rows. If disk space is an issue:
- Reduce `RETENTION_DAYS` to keep fewer backups
- Consider external backup storage

### Restore fails with errors

**Solution**:
1. Check that you're using the correct Supabase instance
2. Ensure the backup file is not corrupted (test with `gunzip -t backup_file.sql.gz`)
3. Consider restoring to a fresh Supabase instance

## Notes

- Backups are **data-only** (no schema), ideal for restoring data loss
- The original 15GB SQL file is deleted after compression to save space
- Backups run automatically every day during the daily update
- Failed backups are logged but don't stop the daily update process
