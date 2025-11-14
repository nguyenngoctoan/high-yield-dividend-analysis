#!/usr/bin/env python3
"""
API Key Management Utility

Provides CLI commands for:
- Creating new API keys for users
- Listing API keys
- Revoking API keys
- Migrating data from api_keys to divv_api_keys
"""

import argparse
import sys
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
import json

# Add the parent directory to the path to import supabase_helpers
sys.path.insert(0, '/Users/toan/dev/high-yield-dividend-analysis')
from supabase_helpers import get_supabase_client


def hash_api_key(api_key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a secure random API key."""
    random_part = secrets.token_urlsafe(32)
    return f"sk_live_{random_part}"


def create_api_key(
    user_id: str,
    name: str,
    tier: str = "free",
    expires_in_days: Optional[int] = None,
    metadata: Optional[dict] = None
) -> dict:
    """
    Create a new API key for a user.

    Args:
        user_id: Unique identifier for the user
        name: Friendly name for the API key
        tier: Subscription tier (free, pro, enterprise)
        expires_in_days: Number of days until expiration (None for no expiration)
        metadata: Additional metadata (email, company, etc.)

    Returns:
        Dictionary with API key information
    """
    if tier not in ['free', 'pro', 'enterprise']:
        raise ValueError("Tier must be one of: free, pro, enterprise")

    # Generate new API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_prefix = api_key[:16]

    # Calculate expiration
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    supabase = get_supabase_client()

    # Insert the new API key
    result = supabase.table('divv_api_keys').insert({
        'user_id': user_id,
        'name': name,
        'key_hash': key_hash,
        'key_prefix': key_prefix,
        'tier': tier,
        'is_active': True,
        'expires_at': expires_at.isoformat() if expires_at else None,
        'metadata': metadata or {}
    }).execute()

    if not result.data:
        raise Exception("Failed to create API key")

    key_data = result.data[0]

    return {
        'id': key_data['id'],
        'api_key': api_key,  # Only returned on creation!
        'key_prefix': key_prefix,
        'user_id': user_id,
        'name': name,
        'tier': tier,
        'expires_at': expires_at,
        'created_at': key_data['created_at']
    }


def list_api_keys(user_id: Optional[str] = None, include_inactive: bool = False):
    """
    List API keys, optionally filtered by user.

    Args:
        user_id: Filter by user ID (None for all users)
        include_inactive: Include revoked keys
    """
    supabase = get_supabase_client()

    query = supabase.table('divv_api_keys').select('*')

    if user_id:
        query = query.eq('user_id', user_id)

    if not include_inactive:
        query = query.eq('is_active', True)

    result = query.order('created_at', desc=True).execute()

    return result.data


def revoke_api_key(key_id: str):
    """
    Revoke an API key.

    Args:
        key_id: The ID of the API key to revoke
    """
    supabase = get_supabase_client()

    result = supabase.table('divv_api_keys').update({
        'is_active': False
    }).eq('id', key_id).execute()

    if not result.data:
        raise Exception(f"API key {key_id} not found")

    return result.data[0]


def migrate_from_api_keys():
    """
    Migrate data from api_keys table to divv_api_keys table.

    This is a one-time migration for existing data.
    """
    supabase = get_supabase_client()

    # Get all keys from api_keys table
    old_keys = supabase.table('api_keys').select('*').execute()

    if not old_keys.data:
        print("No keys found in api_keys table")
        return

    print(f"Found {len(old_keys.data)} keys to migrate")

    migrated = 0
    skipped = 0

    for old_key in old_keys.data:
        try:
            # Check if key already exists in divv_api_keys
            existing = supabase.table('divv_api_keys').select('id').eq('key_hash', old_key['key_hash']).execute()

            if existing.data:
                print(f"  Skipping {old_key['key_prefix']} - already migrated")
                skipped += 1
                continue

            # Insert into divv_api_keys
            supabase.table('divv_api_keys').insert({
                'user_id': old_key['user_id'],
                'name': old_key.get('key_name', 'Migrated Key'),
                'key_hash': old_key['key_hash'],
                'key_prefix': old_key['key_prefix'],
                'tier': old_key.get('tier', 'free'),
                'is_active': old_key.get('is_active', True),
                'request_count': old_key.get('request_count', 0),
                'last_used_at': old_key.get('last_used_at'),
                'expires_at': old_key.get('expires_at'),
                'created_at': old_key.get('created_at'),
                'metadata': old_key.get('metadata', {})
            }).execute()

            print(f"  Migrated {old_key['key_prefix']} for user {old_key['user_id']}")
            migrated += 1

        except Exception as e:
            print(f"  Error migrating {old_key.get('key_prefix', 'unknown')}: {e}")

    print(f"\nMigration complete: {migrated} migrated, {skipped} skipped")


def main():
    parser = argparse.ArgumentParser(description='Manage Dividend API keys')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new API key')
    create_parser.add_argument('--user-id', required=True, help='User ID')
    create_parser.add_argument('--name', required=True, help='API key name')
    create_parser.add_argument('--tier', choices=['free', 'pro', 'enterprise'], default='free', help='Subscription tier')
    create_parser.add_argument('--expires-in-days', type=int, help='Days until expiration')
    create_parser.add_argument('--email', help='User email (stored in metadata)')
    create_parser.add_argument('--company', help='Company name (stored in metadata)')

    # List command
    list_parser = subparsers.add_parser('list', help='List API keys')
    list_parser.add_argument('--user-id', help='Filter by user ID')
    list_parser.add_argument('--include-inactive', action='store_true', help='Include revoked keys')

    # Revoke command
    revoke_parser = subparsers.add_parser('revoke', help='Revoke an API key')
    revoke_parser.add_argument('key_id', help='API key ID to revoke')

    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate from api_keys to divv_api_keys')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'create':
            metadata = {}
            if args.email:
                metadata['email'] = args.email
            if args.company:
                metadata['company'] = args.company

            result = create_api_key(
                user_id=args.user_id,
                name=args.name,
                tier=args.tier,
                expires_in_days=args.expires_in_days,
                metadata=metadata if metadata else None
            )

            print("\n✅ API Key Created Successfully!\n")
            print(f"ID:         {result['id']}")
            print(f"User ID:    {result['user_id']}")
            print(f"Name:       {result['name']}")
            print(f"Tier:       {result['tier']}")
            print(f"Key:        {result['api_key']}")
            print(f"Prefix:     {result['key_prefix']}")
            print(f"Created:    {result['created_at']}")
            if result['expires_at']:
                print(f"Expires:    {result['expires_at']}")
            print("\n⚠️  IMPORTANT: Save this API key securely - it won't be shown again!\n")

        elif args.command == 'list':
            keys = list_api_keys(
                user_id=args.user_id,
                include_inactive=args.include_inactive
            )

            if not keys:
                print("No API keys found")
                return

            print(f"\nFound {len(keys)} API key(s):\n")
            for key in keys:
                status = "✅ Active" if key['is_active'] else "❌ Revoked"
                print(f"{status} | {key['key_prefix']}... | User: {key.get('user_id', 'N/A')} | Tier: {key.get('tier', 'free')}")
                print(f"  Name: {key['name']}")
                print(f"  ID: {key['id']}")
                print(f"  Created: {key['created_at']}")
                if key.get('last_used_at'):
                    print(f"  Last Used: {key['last_used_at']}")
                if key.get('request_count'):
                    print(f"  Requests: {key['request_count']}")
                print()

        elif args.command == 'revoke':
            result = revoke_api_key(args.key_id)
            print(f"\n✅ API key {result['key_prefix']}... has been revoked\n")

        elif args.command == 'migrate':
            migrate_from_api_keys()

    except Exception as e:
        print(f"\n❌ Error: {e}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
