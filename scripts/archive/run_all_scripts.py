#!/usr/bin/env python3
import subprocess
import sys

def run_script(script_path):
    print(f"Running {script_path}...")
    result = subprocess.run(["python3", script_path], stdout=sys.stdout, stderr=sys.stderr, text=True)
    if result.returncode != 0:
        print(f"❌ Error running {script_path} (exit code {result.returncode})")
        sys.exit(result.returncode)
    else:
        print(f"✅ Success running {script_path}!")

if __name__ == "__main__":
    scripts = [
        # Main Supabase scripts
        "update_stock_supabase.py",  # Primary data pipeline
        "fetch_prices_dividends_supabase.py",  # Historical data fetcher
        "run_all_projections.py",  # Portfolio projections
    ]
    for script in scripts:
        run_script(script)
    print("🎉 All scripts ran successfully!")
