#!/usr/bin/env python3
"""
Analyze usage of stocks table columns across the entire codebase.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# All columns in the stocks table
COLUMNS = [
    'aum',
    'company',
    'description',
    'dividend_yield',
    'exchange',
    'expense_ratio',
    'frequency',
    'last_dividend_amount',
    'last_dividend_date',
    'last_updated',
    'name',
    'nav_stability_score',
    'overall_rating',
    'overall_score',
    'price',
    'price_appreciation_score',
    'price_change_ttm',
    'price_change_ytd',
    'rating_last_updated',
    'sector',
    'symbol',
    'total_return_score',
    'total_return_ttm',
    'yield_percentile',
]

def search_files(directory, extensions, column):
    """Search for column references in files with given extensions."""
    matches = []

    for ext in extensions:
        for filepath in Path(directory).rglob(f'*{ext}'):
            # Skip virtual environment, node_modules, .git
            if any(skip in str(filepath) for skip in ['venv', 'node_modules', '.git', '__pycache__', 'archive']):
                continue

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                    # Search for the column name
                    # Look for patterns like: 'column', "column", column=, ['column'], column:, etc.
                    patterns = [
                        rf"['\"]!{column}['\"]",  # 'column' or "column"
                        rf"\b{column}\s*[:=]",    # column: or column=
                        rf"\['{column}'\]",       # ['column']
                        rf'"{column}"',           # "column"
                        rf"'{column}'",           # 'column'
                        rf"\b{column}\b",         # word boundary match
                    ]

                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            # Find the line number
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if re.search(pattern, line, re.IGNORECASE):
                                    matches.append({
                                        'file': str(filepath),
                                        'line': i,
                                        'content': line.strip()[:100]
                                    })
                            break  # Found in this file, move to next file
            except Exception as e:
                pass

    return matches

def analyze_column_usage(base_dir='.'):
    """Analyze usage of each column in the codebase."""
    print("=" * 80)
    print("STOCKS TABLE COLUMN USAGE ANALYSIS")
    print("=" * 80)

    usage_stats = {}

    # File extensions to search
    python_extensions = ['.py']
    sql_extensions = ['.sql']
    js_extensions = ['.js', '.ts', '.tsx', '.jsx']

    for column in COLUMNS:
        print(f"\n🔍 Analyzing column: {column}")

        # Search Python files
        py_matches = search_files(base_dir, python_extensions, column)

        # Search SQL files
        sql_matches = search_files(base_dir, sql_extensions, column)

        # Search JS/TS files
        js_matches = search_files(base_dir, js_extensions, column)

        total_matches = len(py_matches) + len(sql_matches) + len(js_matches)

        usage_stats[column] = {
            'python': py_matches,
            'sql': sql_matches,
            'js': js_matches,
            'total': total_matches
        }

        if total_matches == 0:
            print(f"   ⚠️  NO USAGE FOUND")
        else:
            print(f"   ✅ Used in {total_matches} locations ({len(py_matches)} Python, {len(sql_matches)} SQL, {len(js_matches)} JS/TS)")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY: COLUMN USAGE")
    print("=" * 80)

    unused_columns = []
    rarely_used = []
    heavily_used = []

    for column, stats in sorted(usage_stats.items(), key=lambda x: x[1]['total']):
        total = stats['total']

        if total == 0:
            unused_columns.append(column)
            print(f"❌ {column:30} UNUSED")
        elif total <= 2:
            rarely_used.append(column)
            print(f"⚠️  {column:30} RARELY USED ({total} locations)")
        else:
            heavily_used.append(column)
            print(f"✅ {column:30} Used ({total} locations)")

    # Detailed report for unused/rarely used
    print("\n" + "=" * 80)
    print("DETAILED REPORT: UNUSED & RARELY USED COLUMNS")
    print("=" * 80)

    if unused_columns:
        print("\n🗑️  COLUMNS WITH NO USAGE (safe to drop):")
        for col in unused_columns:
            print(f"   - {col}")

    if rarely_used:
        print("\n⚠️  RARELY USED COLUMNS (review before dropping):")
        for col in rarely_used:
            stats = usage_stats[col]
            print(f"\n   - {col} ({stats['total']} locations):")

            # Show where it's used
            for match in stats['python'][:3]:  # Show first 3 matches
                print(f"      Python: {os.path.basename(match['file'])}:{match['line']}")
            for match in stats['sql'][:3]:
                print(f"      SQL: {os.path.basename(match['file'])}:{match['line']}")
            for match in stats['js'][:3]:
                print(f"      JS/TS: {os.path.basename(match['file'])}:{match['line']}")

    # Recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)

    if unused_columns:
        print(f"\n✅ SAFE TO DROP: {len(unused_columns)} columns")
        print("   These columns are not referenced anywhere in the codebase:")
        for col in unused_columns:
            print(f"   - {col}")
        print("\n   SQL to drop these columns:")
        print("   ALTER TABLE stocks")
        for i, col in enumerate(unused_columns):
            comma = "," if i < len(unused_columns) - 1 else ";"
            print(f"     DROP COLUMN IF EXISTS {col}{comma}")

    if rarely_used:
        print(f"\n⚠️  REVIEW NEEDED: {len(rarely_used)} columns")
        print("   These columns have minimal usage. Review if they're still needed:")
        for col in rarely_used:
            print(f"   - {col}")

    print(f"\n✅ KEEP: {len(heavily_used)} columns")
    print("   These columns are actively used and should be kept.")

    return usage_stats, unused_columns, rarely_used

if __name__ == "__main__":
    stats, unused, rarely_used = analyze_column_usage()
