#!/bin/bash
#
# Public & Auth Schema Backup Script
# Backs up public and auth schemas from Supabase database
#

# Set script directory
SCRIPT_DIR="/Users/toan/dev/high-yield-dividend-analysis"
cd "$SCRIPT_DIR" || exit 1

# Use PostgreSQL 17
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"

# Load environment variables
set -a
source .env
set +a

# Configuration
BACKUP_DIR="$SCRIPT_DIR/backups"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Database connection details
DB_HOST="db.uykxgbrzpfswbdxtyzlv.supabase.co"
DB_PORT="6543"
DB_NAME="postgres"
DB_USER="postgres"

# Create backups directory
mkdir -p "$BACKUP_DIR"

echo "================================================================================"
echo "🗄️  BACKING UP PUBLIC & AUTH SCHEMAS"
echo "================================================================================"
echo ""

# Public schema backup
PUBLIC_BACKUP_FILE="$BACKUP_DIR/public_schema_${TIMESTAMP}.sql"
echo "📦 Backing up PUBLIC schema..."

if PGPASSWORD="$SUPABASE_DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --schema=public \
    --no-owner \
    --no-privileges \
    --clean \
    --if-exists \
    -f "$PUBLIC_BACKUP_FILE" 2>&1; then

    # Compress the backup
    gzip "$PUBLIC_BACKUP_FILE"
    PUBLIC_SIZE=$(ls -lh "${PUBLIC_BACKUP_FILE}.gz" | awk '{print $5}')
    echo "✅ Public schema backed up: $(basename ${PUBLIC_BACKUP_FILE}.gz) ($PUBLIC_SIZE)"
else
    echo "❌ Failed to backup public schema"
    exit 1
fi

# Auth schema backup
AUTH_BACKUP_FILE="$BACKUP_DIR/auth_schema_${TIMESTAMP}.sql"
echo ""
echo "🔐 Backing up AUTH schema..."

if PGPASSWORD="$SUPABASE_DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --schema=auth \
    --no-owner \
    --no-privileges \
    --clean \
    --if-exists \
    -f "$AUTH_BACKUP_FILE" 2>&1; then

    # Compress the backup
    gzip "$AUTH_BACKUP_FILE"
    AUTH_SIZE=$(ls -lh "${AUTH_BACKUP_FILE}.gz" | awk '{print $5}')
    echo "✅ Auth schema backed up: $(basename ${AUTH_BACKUP_FILE}.gz) ($AUTH_SIZE)"
else
    echo "❌ Failed to backup auth schema"
    exit 1
fi

# Combined backup (both schemas)
COMBINED_BACKUP_FILE="$BACKUP_DIR/public_auth_combined_${TIMESTAMP}.sql"
echo ""
echo "🔗 Creating combined backup (public + auth)..."

if PGPASSWORD="$SUPABASE_DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --schema=public \
    --schema=auth \
    --no-owner \
    --no-privileges \
    --clean \
    --if-exists \
    -f "$COMBINED_BACKUP_FILE" 2>&1; then

    # Compress the backup
    gzip "$COMBINED_BACKUP_FILE"
    COMBINED_SIZE=$(ls -lh "${COMBINED_BACKUP_FILE}.gz" | awk '{print $5}')
    echo "✅ Combined backup created: $(basename ${COMBINED_BACKUP_FILE}.gz) ($COMBINED_SIZE)"
else
    echo "❌ Failed to create combined backup"
    exit 1
fi

# Summary
echo ""
echo "================================================================================"
echo "🎉 BACKUP COMPLETED SUCCESSFULLY"
echo "================================================================================"
echo ""
echo "📁 Backup files created in: $BACKUP_DIR"
echo ""
echo "   1. Public schema only:  $(basename ${PUBLIC_BACKUP_FILE}.gz)"
echo "   2. Auth schema only:    $(basename ${AUTH_BACKUP_FILE}.gz)"
echo "   3. Combined (both):     $(basename ${COMBINED_BACKUP_FILE}.gz)"
echo ""
echo "Total size: $(du -sh $BACKUP_DIR | awk '{print $1}')"
echo ""

# Get some table counts
echo "📊 Database Statistics:"
echo ""

TABLE_COUNT=$(PGPASSWORD="$SUPABASE_DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | xargs)

echo "   Tables in public schema: $TABLE_COUNT"

STOCKS_COUNT=$(PGPASSWORD="$SUPABASE_DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM public.raw_stocks;" 2>/dev/null | xargs)

if [ -n "$STOCKS_COUNT" ]; then
    echo "   Total stocks: $(printf "%'d" $STOCKS_COUNT)"
fi

PRICES_COUNT=$(PGPASSWORD="$SUPABASE_DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM public.raw_stock_prices;" 2>/dev/null | xargs)

if [ -n "$PRICES_COUNT" ]; then
    echo "   Total price records: $(printf "%'d" $PRICES_COUNT)"
fi

echo ""
echo "================================================================================"

exit 0
