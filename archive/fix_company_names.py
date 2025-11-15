#!/usr/bin/env python3
"""
Fix company_name field in stocks table to extract actual company/issuer names
"""

import re
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase = create_client(supabase_url, supabase_key)

def extract_company_name(full_name):
    """Extract company name from full ETF name."""
    if not full_name:
        return None
    
    # Common ETF company patterns
    company_patterns = {
        # Major issuers - exact matches first
        'YieldMax': ['YieldMax'],
        'Roundhill': ['Roundhill'],
        'Vanguard': ['Vanguard'],
        'iShares': ['iShares'],
        'SPDR': ['SPDR'],
        'Invesco': ['Invesco'],
        'Schwab': ['Schwab'],
        'BlackRock': ['BlackRock'],
        'State Street': ['State Street'],
        
        # ARK variations
        'ARK': ['ARK Innovation', 'ARK Autonomous', 'ARK Next Generation', 'ARK Genomics', 'ARK Fintech'],
        
        # Global X variations  
        'Global X': ['Global X'],
        
        # ProShares variations
        'ProShares': ['ProShares'],
        
        # First Trust variations
        'First Trust': ['First Trust', 'FT ', 'FT Vest'],
        
        # VanEck variations
        'VanEck': ['VanEck'],
        
        # Direxion variations
        'Direxion': ['Direxion'],
        
        # JPMorgan variations
        'JPMorgan': ['JPMorgan', 'J.P. Morgan'],
        
        # Pacer variations
        'Pacer': ['Pacer'],
        
        # Defiance variations
        'Defiance': ['Defiance'],
        
        # Amplify variations
        'Amplify': ['Amplify'],
        
        # Reality Shares variations
        'Reality Shares': ['Reality Shares'],
        
        # T-Rex variations
        'T-Rex': ['T-Rex'],
        
        # Harbor variations
        'Harbor': ['Harbor'],
        
        # Virtus variations
        'Virtus': ['Virtus'],
        
        # Gabelli variations
        'Gabelli': ['Gabelli'],
        
        # WisdomTree variations
        'WisdomTree': ['WisdomTree'],
        
        # ETFMG variations
        'ETFMG': ['ETFMG'],
        
        # Krane Shares variations
        'Krane Shares': ['Krane Shares', 'KraneShares'],
    }
    
    full_name_upper = full_name.upper()
    
    # Check for company patterns
    for company_name, patterns in company_patterns.items():
        for pattern in patterns:
            if pattern.upper() in full_name_upper:
                return company_name
    
    # For funds with "Trust" - often SPDR or similar
    if 'TRUST' in full_name_upper:
        if 'SPDR' in full_name_upper:
            return 'SPDR'
        elif 'SELECT SECTOR' in full_name_upper:
            return 'SPDR'
    
    # Extract first word if it looks like a company name (capitalized, not common words)
    words = full_name.split()
    if words:
        first_word = words[0]
        # Skip common ETF words
        skip_words = ['THE', 'AN', 'A', 'OF', 'AND', 'OR', 'FOR', 'TO', 'IN', 'ON', 'AT', 'BY']
        if first_word.upper() not in skip_words and first_word.isalpha() and len(first_word) > 2:
            return first_word
    
    return None

def test_extraction():
    """Test the company name extraction."""
    test_cases = [
        "YieldMax PLTR Option Income Strategy ETF",
        "Roundhill PLTR WeeklyPay ETF", 
        "SPDR S&P 500 ETF Trust",
        "iShares Core Canadian Short Term Bond Index ETF",
        "Vanguard Ultra-Short Bond ETF",
        "ARK Innovation ETF",
        "Global X Robotics & Artificial Intelligence ETF",
        "T-Rex 2X Inverse Tesla Daily Target ETF",
        "Invesco Next Gen Media and Gaming ETF"
    ]
    
    print("Testing company name extraction:")
    for name in test_cases:
        extracted = extract_company_name(name)
        print(f"'{name}' -> '{extracted}'")
    print()

def fix_company_names_batch(limit=100):
    """Fix company names in batches."""
    print(f"Fixing company names (batch size: {limit})...")
    
    # Get stocks where company_name equals name (the bug)
    result = supabase.table('raw_stocks').select('symbol, name, company_name').limit(limit).execute()
    
    if not result.data:
        print("No data found to fix")
        return 0
    
    updates = []
    fixed_count = 0
    
    for stock in result.data:
        symbol = stock['symbol']
        name = stock.get('name', '')
        current_company_name = stock.get('company_name', '')
        
        # Skip if company_name is already different from name (already fixed)
        if current_company_name != name and current_company_name:
            continue
            
        # Extract proper company name
        extracted_company = extract_company_name(name)
        
        if extracted_company and extracted_company != current_company_name:
            updates.append({
                'symbol': symbol,
                'company_name': extracted_company
            })
            fixed_count += 1
            print(f"  {symbol}: '{name}' -> Company: '{extracted_company}'")
    
    # Apply updates if any
    if updates:
        try:
            result = supabase.table('raw_stocks').upsert(updates).execute()
            print(f"✅ Successfully updated {len(updates)} company names")
        except Exception as e:
            print(f"❌ Error updating company names: {e}")
            return 0
    else:
        print("No company names needed fixing in this batch")
    
    return fixed_count

if __name__ == "__main__":
    # Test the extraction first
    test_extraction()
    
    # Ask for confirmation before making changes
    response = input("Proceed with fixing company names in database? (y/N): ")
    if response.lower() == 'y':
        fixed = fix_company_names_batch(1000)  # Fix up to 1000 at once
        print(f"\n🎉 Fixed {fixed} company names total")
    else:
        print("Cancelled - no changes made")