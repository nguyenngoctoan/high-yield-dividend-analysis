#!/usr/bin/env python3
"""
Backup public and auth schemas using Python
Works around pg_dump version mismatch issues
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def main():
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    if not db_password:
        print("❌ SUPABASE_DB_PASSWORD not found in .env")
        return 1

    # Configuration
    db_host = "db.uykxgbrzpfswbdxtyzlv.supabase.co"
    db_port = "6543"
    db_user = "postgres"
    db_name = "postgres"

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(__file__).parent.parent.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    print("=" * 80)
    print("🗄️  DATABASE SCHEMA BACKUP")
    print("=" * 80)
    print()

    # Try to use Docker's pg_dump (comes with supabase CLI)
    print("📦 Attempting backup using Supabase CLI's pg_dump...")

    schemas = ["public", "auth"]

    for schema in schemas:
        backup_file = backup_dir / f"{schema}_schema_{timestamp}.sql"

        print(f"\n📋 Backing up {schema} schema...")

        # Use docker to run pg_dump with correct version
        cmd = [
            "docker", "run", "--rm",
            "-e", f"PGPASSWORD={db_password}",
            "supabase/postgres:17.6.0.98",
            "pg_dump",
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "--schema", schema,
            "--no-owner",
            "--no-privileges",
            "--clean",
            "--if-exists"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                # Write to file
                with open(backup_file, 'w') as f:
                    f.write(result.stdout)

                # Compress
                subprocess.run(['gzip', str(backup_file)], check=True)
                compressed_file = f"{backup_file}.gz"

                # Get size
                size_bytes = os.path.getsize(compressed_file)
                size_mb = size_bytes / (1024 * 1024)

                print(f"✅ {schema} schema backed up: {os.path.basename(compressed_file)} ({size_mb:.2f} MB)")
            else:
                print(f"❌ Failed to backup {schema} schema")
                print(f"Error: {result.stderr}")
                return 1

        except subprocess.TimeoutExpired:
            print(f"❌ Backup timed out for {schema} schema")
            return 1
        except Exception as e:
            print(f"❌ Error backing up {schema} schema: {e}")
            return 1

    # Create combined backup
    print(f"\n🔗 Creating combined backup...")
    combined_file = backup_dir / f"public_auth_combined_{timestamp}.sql"

    cmd = [
        "docker", "run", "--rm",
        "-e", f"PGPASSWORD={db_password}",
        "supabase/postgres:17.6.0.98",
        "pg_dump",
        "-h", db_host,
        "-p", db_port,
        "-U", db_user,
        "-d", db_name,
        "--schema", "public",
        "--schema", "auth",
        "--no-owner",
        "--no-privileges",
        "--clean",
        "--if-exists"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            with open(combined_file, 'w') as f:
                f.write(result.stdout)

            subprocess.run(['gzip', str(combined_file)], check=True)
            compressed_file = f"{combined_file}.gz"

            size_bytes = os.path.getsize(compressed_file)
            size_mb = size_bytes / (1024 * 1024)

            print(f"✅ Combined backup created: {os.path.basename(compressed_file)} ({size_mb:.2f} MB)")
        else:
            print(f"❌ Failed to create combined backup")
            print(f"Error: {result.stderr}")
            return 1

    except Exception as e:
        print(f"❌ Error creating combined backup: {e}")
        return 1

    print()
    print("=" * 80)
    print("🎉 BACKUP COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"\n📁 Backups saved to: {backup_dir}")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
