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

# Database connection details (Supabase REMOTE instance)
DB_HOST="db.uykxgbrzpfswbdxtyzlv.supabase.co"
DB_PORT="6543"  # Transaction pooler port
DB_NAME="postgres"
DB_USER="postgres"
DB_PASSWORD="PngVkEu9kqrxIinO"

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

# Check if remote Supabase is accessible
if ! nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
    log_message "❌ Error: Remote database is not accessible at $DB_HOST:$DB_PORT"
    log_message "💡 Check your internet connection and Supabase service status"
    exit 1
fi

log_message "✅ Database connection verified"

# Create backup directory for today
DAILY_BACKUP_DIR="$BACKUP_DIR/$DATE_ONLY"
mkdir -p "$DAILY_BACKUP_DIR"

# Track success
BACKUP_SUCCESS=true

# Capture BEFORE state for delta calculation
log_message ""
log_message "📊 Capturing current database state..."

declare -A BEFORE_COUNTS
TABLES=("raw_stock_prices" "raw_dividends" "raw_stocks" "raw_future_dividends" "raw_excluded_symbols")
for table in "${TABLES[@]}"; do
    ROW_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -t -c "SELECT COUNT(*) FROM public.$table;" 2>/dev/null | xargs)
    BEFORE_COUNTS[$table]=${ROW_COUNT:-0}
done

# Full database backup file (schema + data)
FULL_BACKUP_FILE="$DAILY_BACKUP_DIR/full_backup_${TIMESTAMP}.sql.gz"
TEMP_FULL_BACKUP="$DAILY_BACKUP_DIR/full_backup_${TIMESTAMP}.sql"

# Schema-only backup file
SCHEMA_BACKUP_FILE="$DAILY_BACKUP_DIR/schema_backup_${TIMESTAMP}.sql"

log_message ""
log_message "📦 Creating full database backup (schema + data)..."

# Create schema-only backup (for quick schema restore)
log_message "📋 Creating schema-only backup..."
if PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --schema-only \
    --no-owner \
    --no-acl \
    -f "$SCHEMA_BACKUP_FILE" >> "$LOG_FILE" 2>&1; then
    log_message "✅ Schema backup created: $(basename $SCHEMA_BACKUP_FILE)"
else
    log_message "⚠️  Warning: Schema backup failed (continuing with full backup)"
fi

# Create full backup with BOTH schema and data using pg_dump
log_message "📦 Creating full database backup (this may take several minutes for remote database)..."
if PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    -f "$TEMP_FULL_BACKUP" >> "$LOG_FILE" 2>&1; then
    # Compress the backup
    log_message "🗜️  Compressing full backup..."
    gzip "$TEMP_FULL_BACKUP"

    # Get file size
    FILE_SIZE=$(ls -lh "$FULL_BACKUP_FILE" | awk '{print $5}')
    FILE_SIZE_BYTES=$(stat -f%z "$FULL_BACKUP_FILE" 2>/dev/null || stat -c%s "$FULL_BACKUP_FILE" 2>/dev/null)

    # Get database statistics with delta from yesterday
    log_message ""
    log_message "📊 Database Growth Statistics:"
    log_message ""

    # Try to get yesterday's counts from yesterday's log
    YESTERDAY=$(date -v-1d '+%Y%m%d' 2>/dev/null || date -d 'yesterday' '+%Y%m%d' 2>/dev/null)
    YESTERDAY_LOG="$LOG_DIR/backup_${YESTERDAY}.log"

    declare -A YESTERDAY_COUNTS
    if [ -f "$YESTERDAY_LOG" ]; then
        # Parse yesterday's counts from log
        while IFS= read -r line; do
            for table in "${TABLES[@]}"; do
                if echo "$line" | grep -q "$table:"; then
                    count=$(echo "$line" | grep -oE '[0-9,]+' | tr -d ',' | head -1)
                    YESTERDAY_COUNTS[$table]=${count:-0}
                fi
            done
        done < "$YESTERDAY_LOG"
    fi

    # Current tables row counts with delta
    for table in "${TABLES[@]}"; do
        CURRENT_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            -t -c "SELECT COUNT(*) FROM public.$table;" 2>/dev/null | xargs)

        if [ -n "$CURRENT_COUNT" ]; then
            FORMATTED_CURRENT=$(printf "%'d" $CURRENT_COUNT 2>/dev/null || echo $CURRENT_COUNT)

            # Calculate delta if we have yesterday's data
            YESTERDAY_COUNT=${YESTERDAY_COUNTS[$table]:-0}
            if [ "$YESTERDAY_COUNT" -gt 0 ]; then
                DELTA=$((CURRENT_COUNT - YESTERDAY_COUNT))
                DELTA_SIGN=""
                if [ $DELTA -gt 0 ]; then
                    DELTA_SIGN="+"
                    FORMATTED_DELTA=$(printf "%'d" $DELTA 2>/dev/null || echo $DELTA)
                    log_message "   📋 $table: $FORMATTED_CURRENT rows (${DELTA_SIGN}${FORMATTED_DELTA} since yesterday)"
                elif [ $DELTA -lt 0 ]; then
                    FORMATTED_DELTA=$(printf "%'d" ${DELTA#-} 2>/dev/null || echo ${DELTA#-})
                    log_message "   📋 $table: $FORMATTED_CURRENT rows (-${FORMATTED_DELTA} since yesterday)"
                else
                    log_message "   📋 $table: $FORMATTED_CURRENT rows (no change)"
                fi
            else
                log_message "   📋 $table: $FORMATTED_CURRENT rows"
            fi
        fi
    done

    # Additional useful metrics
    log_message ""
    log_message "📈 Additional Insights:"

    # Data quality metrics
    STOCKS_WITH_PRICES=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM public.raw_stocks WHERE price IS NOT NULL;" 2>/dev/null | xargs)
    STOCKS_WITH_DIVS=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM public.raw_stocks WHERE dividend_yield IS NOT NULL;" 2>/dev/null | xargs)
    TOTAL_STOCKS=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM public.raw_stocks;" 2>/dev/null | xargs)

    if [ "$TOTAL_STOCKS" -gt 0 ]; then
        PRICE_COVERAGE=$((100 * STOCKS_WITH_PRICES / TOTAL_STOCKS))
        DIV_COVERAGE=$((100 * STOCKS_WITH_DIVS / TOTAL_STOCKS))
        log_message "   📊 Price data coverage: ${PRICE_COVERAGE}% (${STOCKS_WITH_PRICES}/${TOTAL_STOCKS})"
        log_message "   💵 Dividend data coverage: ${DIV_COVERAGE}% (${STOCKS_WITH_DIVS}/${TOTAL_STOCKS})"
    fi

    # Average records per symbol
    if [ "$TOTAL_STOCKS" -gt 0 ]; then
        TOTAL_PRICES=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM public.raw_stock_prices;" 2>/dev/null | xargs)
        AVG_PRICES_PER_SYMBOL=$((TOTAL_PRICES / TOTAL_STOCKS))
        log_message "   📉 Avg price records per symbol: $AVG_PRICES_PER_SYMBOL"
    fi

    # Recent activity (last 24 hours)
    PRICES_24H=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM public.raw_stock_prices WHERE updated_at > NOW() - INTERVAL '24 hours';" 2>/dev/null | xargs)
    SYMBOLS_UPDATED_24H=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM public.raw_stocks WHERE updated_at > NOW() - INTERVAL '24 hours';" 2>/dev/null | xargs)

    if [ -n "$PRICES_24H" ] && [ "$PRICES_24H" -gt 0 ]; then
        FORMATTED_24H=$(printf "%'d" $PRICES_24H 2>/dev/null || echo $PRICES_24H)
        log_message "   🕐 Price updates (24h): $FORMATTED_24H"
    fi
    if [ -n "$SYMBOLS_UPDATED_24H" ] && [ "$SYMBOLS_UPDATED_24H" -gt 0 ]; then
        FORMATTED_SYMBOLS_24H=$(printf "%'d" $SYMBOLS_UPDATED_24H 2>/dev/null || echo $SYMBOLS_UPDATED_24H)
        log_message "   🕐 Symbols updated (24h): $FORMATTED_SYMBOLS_24H"
    fi

    log_message ""
    log_message "✅ Full backup completed successfully"
    log_message "📁 Full backup (schema + data): $(basename "$FULL_BACKUP_FILE")"
    log_message "📁 Schema-only backup: $(basename "$SCHEMA_BACKUP_FILE")"
    log_message "💾 Full backup size: $FILE_SIZE (compressed)"

else
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
log_message "🔍 DATA QUALITY & ERROR CHECKS"
log_message "================================================================================"

# Check for anomalies
for table in "${TABLES[@]}"; do
    CURRENT_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM public.$table;" 2>/dev/null | xargs)
    YESTERDAY_COUNT=${YESTERDAY_COUNTS[$table]:-0}

    if [ "$YESTERDAY_COUNT" -gt 0 ]; then
        DELTA=$((CURRENT_COUNT - YESTERDAY_COUNT))
        DELTA_PCT=$((100 * DELTA / YESTERDAY_COUNT))

        # Check for data loss (negative growth)
        if [ $DELTA -lt -1000 ]; then
            log_message "🔴 CRITICAL: $table lost $((DELTA * -1)) rows since yesterday"
            log_message "   ACTION REQUIRED: Investigate potential data deletion or corruption"
            BACKUP_SUCCESS=false
        fi

        # Check for unusual growth
        if [ "$table" = "raw_stocks" ] && [ $DELTA -gt 1000 ]; then
            log_message "🟡 WARNING: $table grew by $DELTA symbols (unusual daily growth)"
            log_message "   RECOMMENDED: Verify discovery process for duplicates"
        fi

        # Check for stagnant price data
        if [ "$table" = "raw_stock_prices" ] && [ $DELTA -eq 0 ]; then
            log_message "🔴 CRITICAL: No new price records added in 24 hours"
            log_message "   ACTION REQUIRED: Check if price update process is running"
            BACKUP_SUCCESS=false
        fi
    fi
done

# Check backup file size
if [ -f "$FULL_BACKUP_FILE" ]; then
    CURRENT_SIZE=$(stat -f%z "$FULL_BACKUP_FILE" 2>/dev/null || stat -c%s "$FULL_BACKUP_FILE" 2>/dev/null)

    # Find yesterday's backup for comparison
    YESTERDAY_BACKUP=$(find "$BACKUP_DIR/$YESTERDAY" -name "*.sql.gz" -type f 2>/dev/null | head -1)
    if [ -f "$YESTERDAY_BACKUP" ]; then
        YESTERDAY_SIZE=$(stat -f%z "$YESTERDAY_BACKUP" 2>/dev/null || stat -c%s "$YESTERDAY_BACKUP" 2>/dev/null)
        SIZE_DELTA=$((CURRENT_SIZE - YESTERDAY_SIZE))
        SIZE_DELTA_PCT=$((100 * SIZE_DELTA / YESTERDAY_SIZE))

        if [ $SIZE_DELTA_PCT -lt -20 ]; then
            log_message "🔴 CRITICAL: Backup file 20%+ smaller than yesterday"
            log_message "   ACTION REQUIRED: Possible data loss or incomplete backup"
            BACKUP_SUCCESS=false
        elif [ $SIZE_DELTA_PCT -gt 50 ]; then
            log_message "🟡 WARNING: Backup file 50%+ larger than yesterday"
            log_message "   RECOMMENDED: Verify data growth is expected"
        else
            log_message "✅ Backup file size normal (${SIZE_DELTA_PCT:+${SIZE_DELTA_PCT}%} vs yesterday)"
        fi
    fi
fi

# No errors detected
CRITICAL_COUNT=$(grep -c "🔴 CRITICAL" "$LOG_FILE" 2>/dev/null || echo 0)
WARNING_COUNT=$(grep -c "🟡 WARNING" "$LOG_FILE" 2>/dev/null || echo 0)

if [ "$CRITICAL_COUNT" -eq 0 ] && [ "$WARNING_COUNT" -eq 0 ]; then
    log_message "✅ No data quality issues detected"
fi

log_message ""
log_message "================================================================================"
if [ "$BACKUP_SUCCESS" = true ]; then
    log_message "🎉 DATABASE BACKUP COMPLETED SUCCESSFULLY"
    if [ "$WARNING_COUNT" -gt 0 ]; then
        log_message "⚠️  $WARNING_COUNT warning(s) detected - review recommended"
    fi
    EXIT_CODE=0
else
    log_message "⚠️  DATABASE BACKUP COMPLETED WITH ERRORS"
    log_message "🔴 $CRITICAL_COUNT critical error(s) detected - action required"
    if [ "$WARNING_COUNT" -gt 0 ]; then
        log_message "🟡 $WARNING_COUNT warning(s) detected"
    fi
    EXIT_CODE=1
fi
log_message "================================================================================"

# Cleanup old log files (keep last 14 days to match backup retention)
find "$LOG_DIR" -name "backup_*.log" -mtime +14 -delete 2>/dev/null

exit $EXIT_CODE
