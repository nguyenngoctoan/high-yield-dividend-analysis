#!/bin/bash
# Quick script to open Supabase SQL Editor with migration ready to paste

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}         Supabase SQL Migration Helper                          ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Get project ID from .env
if [ -f .env ]; then
    source .env
    if [ -n "$SUPABASE_URL" ]; then
        # Extract project ref from URL (format: https://xxx.supabase.co)
        PROJECT_REF=$(echo "$SUPABASE_URL" | sed 's/https:\/\///' | cut -d'.' -f1)
        echo -e "${GREEN}✅ Found Supabase project: ${PROJECT_REF}${NC}"
    fi
fi

# If we couldn't get it from .env, ask for it
if [ -z "$PROJECT_REF" ]; then
    echo -e "${YELLOW}⚠️  Could not detect project ID from .env${NC}"
    echo ""
    echo "Please enter your Supabase project reference ID:"
    echo "(Found in your Supabase dashboard URL)"
    read -p "Project Ref: " PROJECT_REF

    if [ -z "$PROJECT_REF" ]; then
        echo "❌ Project reference required"
        exit 1
    fi
fi

# Copy migration to clipboard
echo ""
echo -e "${BLUE}📋 Copying migration SQL to clipboard...${NC}"
cat migrations/update_pricing_tiers_v2.sql | pbcopy
echo -e "${GREEN}✅ Migration SQL copied to clipboard!${NC}"

# Build Supabase SQL Editor URL
SQL_EDITOR_URL="https://supabase.com/dashboard/project/${PROJECT_REF}/sql/new"

echo ""
echo -e "${BLUE}🌐 Opening Supabase SQL Editor...${NC}"
echo ""
echo "URL: ${SQL_EDITOR_URL}"
echo ""

# Open the URL in browser
open "$SQL_EDITOR_URL"

echo -e "${GREEN}✅ Browser opened!${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "NEXT STEPS:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. ✅ SQL Editor should open in your browser"
echo "2. ✅ Migration SQL is already in your clipboard"
echo "3. ✅ Paste into the editor (Cmd+V)"
echo "4. ✅ Click 'Run' or press Cmd+Enter"
echo ""
echo "The migration will:"
echo "  • Create tier_limits table with 5 pricing tiers"
echo "  • Add usage tracking to divv_api_keys"
echo "  • Create free_tier_stocks with 40 sample stocks"
echo "  • Add helper functions for rate limiting"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "AFTER MIGRATION:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Run these commands to verify and test:"
echo ""
echo "  # Verify migration"
echo "  ./scripts/verify_migration.sh"
echo ""
echo "  # Test rate limiting"
echo "  python3 tests/test_rate_limits_simple.py"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
