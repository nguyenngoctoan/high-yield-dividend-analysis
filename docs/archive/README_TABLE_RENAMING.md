# Database Table Renaming Analysis

## Welcome!

This directory now contains comprehensive documentation for the database table renaming project to add a `raw_` prefix to core data tables.

### What's This About?

You're planning to rename 8 database tables to distinguish the raw data ingestion layer from processed application data:

- `stocks` → `raw_stocks`
- `stock_prices` → `raw_stock_prices`
- `dividend_history` → `raw_dividend_history`
- And 5 more...

This analysis covers **104+ files** with **200+ references** that need to be updated.

### Start Here

1. **First Time Reading?** → `TABLE_RENAMING_START_HERE.md`
2. **Want Quick Overview?** → `ANALYSIS_SUMMARY.txt`
3. **Need File List?** → `FILES_TO_UPDATE_CHECKLIST.md`
4. **Want All Details?** → `TABLE_RENAMING_ANALYSIS.md`
5. **Quick Reference?** → `TABLE_RENAMING_QUICK_REFERENCE.md`

### Key Numbers

- **8 tables** to rename
- **104+ files** affected
- **200+ code references** found
- **10-15 hours** estimated effort

### Critical Files to Update First

1. `supabase_helpers.py` (40+ references)
2. `lib/processors/incremental_processor.py` (direct references)
3. All 9 migration files
4. 5 core processor files

### Quick Links

| Document | Purpose | Size |
|----------|---------|------|
| TABLE_RENAMING_START_HERE.md | Navigation & quick start | 8.9K |
| ANALYSIS_SUMMARY.txt | High-level overview | 8.5K |
| TABLE_RENAMING_QUICK_REFERENCE.md | Lookup reference | 5.3K |
| FILES_TO_UPDATE_CHECKLIST.md | Complete task list | 8.6K |
| TABLE_RENAMING_ANALYSIS.md | Full technical docs | 25K |

**Total:** 56.3K of comprehensive documentation

---

Read `TABLE_RENAMING_START_HERE.md` to begin!
