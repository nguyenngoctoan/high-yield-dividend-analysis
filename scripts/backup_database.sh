#!/bin/bash
#
# Database Backup Script
# Backs up the entire dividend tracker database
# Designed to run daily via cron
#

# Set script directory
SCRIPT_DIR="/Users/toan/dev/high-yield-dividend-analysis"
cd "$SCRIPT_DIR" || exit 1

# Configuration
BACKUP_DIR="$SCRIPT_DIR/backups"
LOG_DIR="$SCRIPT_DIR/logs"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
DATE_ONLY=$(date '+%Y%m%d')
LOG_FILE="$LOG_DIR/backup_${DATE_ONLY}.log"

# Supabase project directory
SUPABASE_PROJECT_DIR="/Users/toan/dev/ai-dividend-tracker"

# Database connection details (Supabase local instance)
DB_HOST="127.0.0.1"
DB_PORT="54322"
DB_NAME="postgres"
DB_USER="postgres"
DB_PASSWORD="postgres"

# Retention policy (days)
RETENTION_DAYS=14

# Create directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

# Logging function
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_message "================================================================================"
log_message "🗄️  DATABASE BACKUP STARTED"
log_message "================================================================================"

# Check if Supabase is running
if ! nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
    log_message "❌ Error: Database is not accessible at $DB_HOST:$DB_PORT"
    log_message "💡 Make sure Supabase is running (cd ai-dividend-tracker && npx supabase start)"
    exit 1
fi

log_message "✅ Database connection verified"

# Create backup directory for today
DAILY_BACKUP_DIR="$BACKUP_DIR/$DATE_ONLY"
mkdir -p "$DAILY_BACKUP_DIR"

# Track success
BACKUP_SUCCESS=true

# Full database backup file
FULL_BACKUP_FILE="$DAILY_BACKUP_DIR/full_backup_${TIMESTAMP}.sql.gz"
TEMP_FULL_BACKUP="$DAILY_BACKUP_DIR/full_backup_${TIMESTAMP}.sql"

log_message ""
log_message "📦 Creating full database backup..."

# Use Supabase CLI to dump the database
cd "$SUPABASE_PROJECT_DIR" || exit 1

if npx supabase db dump --local --data-only -f "$TEMP_FULL_BACKUP" >> "$LOG_FILE" 2>&1; then
    # Compress the backup
    log_message "🗜️  Compressing backup..."
    gzip "$TEMP_FULL_BACKUP"

    cd "$SCRIPT_DIR" || exit 1

    # Get file size
    FILE_SIZE=$(ls -lh "$FULL_BACKUP_FILE" | awk '{print $5}')
    FILE_SIZE_BYTES=$(stat -f%z "$FULL_BACKUP_FILE" 2>/dev/null || stat -c%s "$FULL_BACKUP_FILE" 2>/dev/null)

    # Get database statistics
    log_message ""
    log_message "📊 Database Statistics:"

    # Critical tables row counts
    TABLES=("raw_stock_prices" "raw_dividends" "raw_stocks" "raw_future_dividends" "raw_holdings_history")
    for table in "${TABLES[@]}"; do
        ROW_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            -t -c "SELECT COUNT(*) FROM public.$table;" 2>/dev/null | xargs)

        if [ -n "$ROW_COUNT" ]; then
            log_message "   📋 $table: $(printf "%'d" $ROW_COUNT 2>/dev/null || echo $ROW_COUNT) rows"
        fi
    done

    log_message ""
    log_message "✅ Full backup completed successfully"
    log_message "📁 Backup file: $(basename "$FULL_BACKUP_FILE")"
    log_message "💾 Size: $FILE_SIZE (compressed)"

else
    cd "$SCRIPT_DIR" || exit 1
    log_message "❌ Failed to create backup"
    BACKUP_SUCCESS=false
fi

# Cleanup old backups
log_message ""
log_message "🧹 Cleaning up old backups (retention: $RETENTION_DAYS days)"

DELETED_COUNT=0
while IFS= read -r old_backup; do
    if [ -d "$old_backup" ]; then
        rm -rf "$old_backup"
        DELETED_COUNT=$((DELETED_COUNT + 1))
        log_message "🗑️  Deleted old backup: $(basename "$old_backup")"
    fi
done < <(find "$BACKUP_DIR" -maxdepth 1 -type d -name "20*" -mtime +$RETENTION_DAYS)

if [ $DELETED_COUNT -gt 0 ]; then
    log_message "✅ Cleaned up $DELETED_COUNT old backup(s)"
else
    log_message "✅ No old backups to clean up"
fi

# Calculate total backup disk usage
log_message ""
TOTAL_BACKUP_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | awk '{print $1}')
BACKUP_COUNT=$(find "$BACKUP_DIR" -type d -name "20*" | wc -l | xargs)
log_message "💾 Total backup storage: $TOTAL_BACKUP_SIZE ($BACKUP_COUNT backup(s) retained)"

log_message ""
log_message "================================================================================"
if [ "$BACKUP_SUCCESS" = true ]; then
    log_message "🎉 DATABASE BACKUP COMPLETED SUCCESSFULLY"
    EXIT_CODE=0
else
    log_message "⚠️  DATABASE BACKUP COMPLETED WITH ERRORS"
    EXIT_CODE=1
fi
log_message "================================================================================"

# Cleanup old log files (keep last 14 days to match backup retention)
find "$LOG_DIR" -name "backup_*.log" -mtime +14 -delete 2>/dev/null

exit $EXIT_CODE
