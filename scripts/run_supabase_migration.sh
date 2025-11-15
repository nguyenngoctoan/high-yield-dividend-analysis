#!/bin/bash
# Run Supabase Migration Script
# This script automates the process of running migrations via Supabase CLI

set -e  # Exit on error

echo "=================================="
echo "Supabase Migration Runner"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo -e "${RED}❌ Supabase CLI is not installed${NC}"
    echo ""
    echo "Install it with:"
    echo "  brew install supabase/tap/supabase"
    echo ""
    echo "Or see: https://supabase.com/docs/guides/cli"
    exit 1
fi

echo -e "${GREEN}✅ Supabase CLI is installed${NC}"

# Check if already logged in
echo ""
echo -e "${BLUE}Checking Supabase authentication...${NC}"

if supabase projects list &> /dev/null; then
    echo -e "${GREEN}✅ Already logged in to Supabase${NC}"
else
    echo -e "${YELLOW}⚠️  Not logged in to Supabase${NC}"
    echo ""
    echo "Opening browser for Supabase login..."
    echo ""

    supabase login

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Login failed${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Successfully logged in${NC}"
fi

# List available projects
echo ""
echo -e "${BLUE}Available Supabase projects:${NC}"
supabase projects list

# Check if project is already linked
echo ""
echo -e "${BLUE}Checking if project is linked...${NC}"

if [ -f .supabase/config.toml ] && grep -q "project_id" .supabase/config.toml; then
    PROJECT_ID=$(grep "project_id" .supabase/config.toml | cut -d'"' -f2)
    echo -e "${GREEN}✅ Project already linked: ${PROJECT_ID}${NC}"
else
    echo -e "${YELLOW}⚠️  Project not linked${NC}"
    echo ""
    echo "Please enter your Supabase project reference ID:"
    echo "(You can find this in your Supabase dashboard URL or project settings)"
    read -p "Project Ref: " PROJECT_REF

    if [ -z "$PROJECT_REF" ]; then
        echo -e "${RED}❌ Project reference cannot be empty${NC}"
        exit 1
    fi

    echo ""
    echo -e "${BLUE}Linking to project: ${PROJECT_REF}${NC}"
    supabase link --project-ref "$PROJECT_REF"

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to link project${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Project linked successfully${NC}"
fi

# Check if migration file exists
MIGRATION_FILE="supabase/migrations/20251114_update_pricing_tiers_v2.sql"

echo ""
echo -e "${BLUE}Checking migration file...${NC}"

if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${YELLOW}⚠️  Migration not found in supabase/migrations/${NC}"
    echo "Copying from migrations/ directory..."

    mkdir -p supabase/migrations
    cp migrations/update_pricing_tiers_v2.sql "$MIGRATION_FILE"

    echo -e "${GREEN}✅ Migration file copied${NC}"
fi

# Show migration details
echo ""
echo -e "${BLUE}Migration file: ${MIGRATION_FILE}${NC}"
FILE_SIZE=$(wc -c < "$MIGRATION_FILE" | xargs)
echo "Size: ${FILE_SIZE} bytes"
echo ""

# Confirm before running
echo -e "${YELLOW}This will apply the following migration:${NC}"
echo "  - Update divv_api_keys table (add tier, usage tracking columns)"
echo "  - Create tier_limits table with 5 tiers"
echo "  - Create free_tier_stocks table with ~150 stocks"
echo "  - Create increment_key_usage() function"
echo "  - Populate initial tier data"
echo ""

read -p "Continue with migration? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Migration cancelled${NC}"
    exit 0
fi

# Run the migration
echo ""
echo -e "${BLUE}Running migration...${NC}"
echo ""

supabase db push

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Migration completed successfully!${NC}"
    echo ""

    # Verify migration
    echo -e "${BLUE}Verifying migration...${NC}"
    echo ""
    echo "Checking tier_limits table..."

    # Note: We can't easily query via CLI, so provide manual verification steps
    echo ""
    echo -e "${YELLOW}To verify the migration, run these queries in Supabase SQL Editor:${NC}"
    echo ""
    echo "-- Check tier limits"
    echo "SELECT tier, monthly_call_limit, calls_per_minute FROM tier_limits ORDER BY monthly_call_limit;"
    echo ""
    echo "-- Check new columns in divv_api_keys"
    echo "SELECT column_name, data_type FROM information_schema.columns"
    echo "WHERE table_name = 'divv_api_keys' AND column_name IN ('tier', 'monthly_usage', 'minute_usage');"
    echo ""
    echo "-- Count free tier stocks"
    echo "SELECT COUNT(*) FROM free_tier_stocks;"
    echo ""

    # Suggest next steps
    echo -e "${GREEN}Next Steps:${NC}"
    echo "1. Verify the migration in Supabase SQL Editor (queries above)"
    echo "2. Restart your API server to load rate limiting middleware"
    echo "3. Run the test suite: python3 tests/test_rate_limits_simple.py"
    echo ""

else
    echo ""
    echo -e "${RED}❌ Migration failed${NC}"
    echo ""
    echo "Common issues:"
    echo "  - Tables already exist (migration is idempotent, should be safe to re-run)"
    echo "  - Permission denied (check database permissions)"
    echo "  - Connection timeout (check network/VPN)"
    echo ""
    echo "Check the error message above for details."
    echo ""
    exit 1
fi
