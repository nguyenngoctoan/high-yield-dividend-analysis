#!/usr/bin/env python3
"""
Unified Test Runner with Detailed Logging
Runs all test suites (rate limiting, API endpoints, integration) and creates detailed log files
"""

import sys
import subprocess
from datetime import datetime
import os
import json

# Test files to run
TEST_FILES = [
    # Rate limiting and tier tests
    "tests/test_rate_limits_simple.py",
    "tests/test_all_tiers.py",
    "tests/test_tier_restrictions.py",
    "tests/test_data_quality.py",
    # API endpoint tests (pytest)
    "python3 -m pytest tests/test_api_endpoints.py -v --tb=short",
]

# Working directory
WORK_DIR = "/Users/toan/dev/high-yield-dividend-analysis"

# Log directory
LOG_DIR = os.path.join(WORK_DIR, "logs", "test_runs")


def ensure_log_dir():
    """Ensure log directory exists"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        print(f"✅ Created log directory: {LOG_DIR}")


def run_test(test_command: str) -> tuple[bool, str, float]:
    """
    Run a test file or command and return (success, output, duration)
    """
    import time
    import shlex
    start_time = time.time()

    try:
        # If it's a command with arguments (pytest, etc), run as shell command
        if " " in test_command or "pytest" in test_command:
            result = subprocess.run(
                test_command,
                cwd=WORK_DIR,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                shell=True
            )
        else:
            # Run as Python script
            result = subprocess.run(
                ["python3", test_command],
                cwd=WORK_DIR,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

        duration = time.time() - start_time
        output = result.stdout + result.stderr
        success = result.returncode == 0

        return success, output, duration
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return False, f"Test timed out after 5 minutes", duration
    except Exception as e:
        duration = time.time() - start_time
        return False, f"Error running test: {str(e)}", duration


def write_test_log(run_id: str, test_results: list, summary: dict):
    """
    Write detailed test log to file
    """
    timestamp = datetime.now()

    # Create log file name with timestamp
    log_filename = f"test_run_{run_id}.log"
    log_filepath = os.path.join(LOG_DIR, log_filename)

    # Also create a JSON summary file
    json_filename = f"test_run_{run_id}.json"
    json_filepath = os.path.join(LOG_DIR, json_filename)

    # Write detailed log
    with open(log_filepath, 'w') as f:
        f.write("="*80 + "\n")
        f.write("DIVV API UNIFIED TEST RUN\n")
        f.write("="*80 + "\n")
        f.write(f"Run ID: {run_id}\n")
        f.write(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Tests: {summary['total']}\n")
        f.write(f"Passed: {summary['passed']}\n")
        f.write(f"Failed: {summary['failed']}\n")
        f.write(f"Duration: {summary['duration']:.2f}s\n")
        f.write(f"Status: {'✅ PASS' if summary['failed'] == 0 else '❌ FAIL'}\n")
        f.write("="*80 + "\n\n")

        for result in test_results:
            f.write("="*80 + "\n")
            f.write(f"TEST: {result['name']}\n")
            f.write("="*80 + "\n")
            f.write(f"Status: {'✅ PASS' if result['success'] else '❌ FAIL'}\n")
            f.write(f"Duration: {result['duration']:.2f}s\n")
            f.write("\n")
            f.write("OUTPUT:\n")
            f.write("-"*80 + "\n")
            f.write(result['output'])
            f.write("\n" + "="*80 + "\n\n")

    # Write JSON summary
    json_data = {
        "run_id": run_id,
        "timestamp": timestamp.isoformat(),
        "summary": summary,
        "results": [
            {
                "name": r['name'],
                "success": r['success'],
                "duration": r['duration']
            }
            for r in test_results
        ]
    }

    with open(json_filepath, 'w') as f:
        json.dump(json_data, f, indent=2)

    print(f"\n📝 Detailed log written to: {log_filepath}")
    print(f"📊 JSON summary written to: {json_filepath}")

    # Also update the latest symlink
    latest_log = os.path.join(LOG_DIR, "latest.log")
    latest_json = os.path.join(LOG_DIR, "latest.json")

    # Remove old symlinks if they exist
    if os.path.islink(latest_log):
        os.unlink(latest_log)
    if os.path.islink(latest_json):
        os.unlink(latest_json)

    # Create new symlinks
    os.symlink(log_filename, latest_log)
    os.symlink(json_filename, latest_json)

    print(f"🔗 Latest logs symlinked to: {latest_log} and {latest_json}")

    return log_filepath


def main():
    """
    Run all tests and write detailed logs
    """
    import time
    start_time = time.time()

    # Generate run ID from timestamp
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\n" + "="*80)
    print("DIVV API UNIFIED TEST SUITE")
    print("="*80)
    print(f"Run ID: {run_id}")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Tests to run: {len(TEST_FILES)}")
    print("="*80 + "\n")

    # Ensure log directory exists
    ensure_log_dir()

    test_results = []

    for test_command in TEST_FILES:
        # Extract test name from command or file path
        if "pytest" in test_command:
            # Extract filename from pytest command (e.g., "python3 -m pytest tests/test_api_endpoints.py -v")
            parts = test_command.split()
            for part in parts:
                if part.endswith('.py'):
                    test_name = os.path.basename(part)
                    break
            else:
                test_name = "pytest_tests"
        else:
            test_name = os.path.basename(test_command)

        print(f"\n{'='*80}")
        print(f"Running: {test_name}")
        print("="*80)

        success, output, duration = run_test(test_command)

        test_results.append({
            'name': test_name,
            'success': success,
            'output': output,
            'duration': duration
        })

        if success:
            print(f"✅ {test_name} PASSED ({duration:.2f}s)")
        else:
            print(f"❌ {test_name} FAILED ({duration:.2f}s)")

        # Print output (truncated)
        lines = output.split('\n')
        if len(lines) > 50:
            print('\n'.join(lines[:25]))
            print(f"\n... ({len(lines) - 50} lines omitted) ...\n")
            print('\n'.join(lines[-25:]))
        else:
            print(output)

    total_duration = time.time() - start_time

    # Summary
    passed = sum(1 for r in test_results if r['success'])
    failed = len(test_results) - passed

    summary = {
        'total': len(test_results),
        'passed': passed,
        'failed': failed,
        'duration': total_duration
    }

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Total Duration: {summary['duration']:.2f}s")
    print("="*80)

    # Write detailed logs
    log_file = write_test_log(run_id, test_results, summary)

    if failed > 0:
        print(f"\n❌ {failed} test(s) failed - detailed logs written")
        print(f"📄 View logs: cat {log_file}")
        sys.exit(1)
    else:
        print("\n✅ All tests passed - logs written")
        print(f"📄 View logs: cat {log_file}")
        sys.exit(0)


if __name__ == "__main__":
    main()
