#!/usr/bin/env python3
"""
Update all code references to use new divv_ prefixed table names.
"""

import os
import re
from pathlib import Path

# Table name mappings
TABLE_MAPPINGS = {
    # Main data tables
    "raw_stocks": "divv_stocks",
    "raw_stock_prices": "divv_stock_prices",
    "raw_dividends": "divv_dividends",
    "raw_future_dividends": "divv_future_dividends",
    "raw_stock_splits": "divv_stock_splits",
    "raw_etf_holdings": "divv_etf_holdings",

    # Tracking tables
    "raw_data_source_tracking": "divv_data_source_tracking",
    "raw_stocks_excluded": "divv_stocks_excluded",
    "raw_yieldmax_dividends": "divv_yieldmax_dividends",

    # Shared tables
    "users": "divv_users",
    "tier_limits": "divv_tier_limits",
    "free_tier_stocks": "divv_free_tier_stocks",
    "mv_api_usage_daily": "divv_mv_api_usage_daily",

    # Fix inconsistencies
    "dividend_history": "divv_dividends",
    "stock_prices": "divv_stock_prices",
    "stocks": "divv_stocks",
}

def update_file(file_path: Path, dry_run: bool = False):
    """Update table references in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = []

        for old_name, new_name in TABLE_MAPPINGS.items():
            # Pattern for .table('old_name')
            pattern1 = rf"\.table\(['\"]({old_name})['\"]\)"
            replacement1 = rf".table('{new_name}')"

            # Find all matches before replacing
            matches = re.finditer(pattern1, content)
            for match in matches:
                changes.append(f"  • .table('{old_name}') → .table('{new_name}')")

            content = re.sub(pattern1, replacement1, content)

            # Pattern for FROM old_name or JOIN old_name
            pattern2 = rf"\b(FROM|JOIN)\s+({old_name})\b"
            replacement2 = rf"\1 {new_name}"

            matches = re.finditer(pattern2, content, re.IGNORECASE)
            for match in matches:
                changes.append(f"  • {match.group(1)} {old_name} → {match.group(1)} {new_name}")

            content = re.sub(pattern2, replacement2, content, flags=re.IGNORECASE)

        if content != original_content:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            return True, changes

        return False, []

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False, []

def main():
    print("=" * 80)
    print("TABLE REFERENCE UPDATE SCRIPT")
    print("=" * 80)
    print()

    # Directories to scan
    directories = [
        "api",
        "lib",
        "scripts",
        "."
    ]

    # File patterns to update
    patterns = [
        "**/*.py",
        "*.py"
    ]

    files_to_update = set()

    # Find all Python files
    for directory in directories:
        if os.path.exists(directory):
            path = Path(directory)
            for pattern in patterns:
                files_to_update.update(path.glob(pattern))

    # Remove migration files and this script
    files_to_update = [
        f for f in files_to_update
        if 'migrations' not in str(f) and
           'update_table_references.py' not in str(f) and
           '__pycache__' not in str(f)
    ]

    print(f"📁 Found {len(files_to_update)} Python files to check")
    print()

    # Dry run first
    print("🔍 Scanning files for table references...")
    print()

    files_with_changes = []
    total_changes = 0

    for file_path in sorted(files_to_update):
        changed, changes = update_file(file_path, dry_run=True)
        if changed:
            files_with_changes.append((file_path, changes))
            total_changes += len(changes)

    if not files_with_changes:
        print("✅ No files need updating!")
        return

    print(f"📊 Found {len(files_with_changes)} files with {total_changes} table references to update:")
    print()

    for file_path, changes in files_with_changes:
        print(f"📄 {file_path}")
        for change in set(changes):  # Use set to deduplicate
            print(change)
        print()

    # Ask for confirmation
    print("=" * 80)
    response = input("Apply these changes? [y/N]: ")

    if response.lower() != 'y':
        print("❌ Aborted. No changes made.")
        return

    print()
    print("✍️  Applying changes...")
    print()

    # Apply changes
    updated_count = 0
    for file_path, _ in files_with_changes:
        changed, changes = update_file(file_path, dry_run=False)
        if changed:
            updated_count += 1
            print(f"✅ Updated {file_path}")

    print()
    print("=" * 80)
    print(f"✅ Successfully updated {updated_count} files!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Review the changes: git diff")
    print("2. Run the database migration")
    print("3. Test the application")
    print("4. Update the index migration file")

if __name__ == '__main__':
    main()
