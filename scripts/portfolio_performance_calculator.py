#!/usr/bin/env python3
"""
Portfolio Performance Calculator
This script provides corrected portfolio performance calculations to verify and fix
the logic issues in the Dividend Tracker application.
"""

import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class PortfolioPerformance:
    """Portfolio performance metrics."""
    total_equity: float
    total_contributions: float
    cash_balance: float
    total_return: float
    total_return_percentage: float
    dividends_received: float = 0.0
    withdrawals: float = 0.0
    fees_paid: float = 0.0

class PortfolioPerformanceCalculator:
    """Calculator for portfolio performance metrics with corrected logic."""
    
    def __init__(self):
        """Initialize the calculator with Supabase connection."""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            if supabase_url and supabase_key:
                self.supabase = create_client(supabase_url, supabase_key)
                print(f"Connected to Supabase: {supabase_url}")
            else:
                self.supabase = None
                print("Warning: Supabase credentials not found")
        except Exception as e:
            self.supabase = None
            print(f"Error connecting to Supabase: {e}")
    
    def calculate_portfolio_performance(
        self,
        total_equity: float,
        total_contributions: float,
        cash_balance: float,
        dividends_received: float = 0.0,
        withdrawals: float = 0.0,
        fees_paid: float = 0.0
    ) -> PortfolioPerformance:
        """
        Calculate portfolio performance with corrected logic.
        
        Args:
            total_equity: Current value of all invested assets
            total_contributions: Total money invested (excluding dividends)
            cash_balance: Uninvested cash in the account
            dividends_received: Total dividends received (optional)
            withdrawals: Total money withdrawn (optional)
            fees_paid: Total fees paid (optional)
        
        Returns:
            PortfolioPerformance object with calculated metrics
        """
        
        # CORRECTED CALCULATION LOGIC:
        # Total Return = (Total Equity + Cash Balance) - (Total Contributions - Withdrawals) + Dividends - Fees
        
        # Net contributions (money actually invested, accounting for withdrawals)
        net_contributions = total_contributions - withdrawals
        
        # Total portfolio value (invested + cash)
        total_portfolio_value = total_equity + cash_balance
        
        # Total return calculation
        total_return = total_portfolio_value - net_contributions + dividends_received - fees_paid
        
        # Total return percentage
        if net_contributions > 0:
            total_return_percentage = (total_return / net_contributions) * 100
        else:
            total_return_percentage = 0.0
        
        return PortfolioPerformance(
            total_equity=total_equity,
            total_contributions=total_contributions,
            cash_balance=cash_balance,
            total_return=total_return,
            total_return_percentage=total_return_percentage,
            dividends_received=dividends_received,
            withdrawals=withdrawals,
            fees_paid=fees_paid
        )
    
    def analyze_ui_calculation_issue(
        self,
        total_equity: float = 170540.50,
        total_contributions: float = 257597.34,
        cash_balance: float = 16362.70,
        ui_total_return: float = -70694.14,
        ui_percentage: float = 27.44
    ) -> Dict:
        """
        Analyze the calculation issue from the UI.
        
        Args:
            total_equity: Total equity from UI
            total_contributions: Total contributions from UI
            cash_balance: Cash balance from UI
            ui_total_return: Total return shown in UI
            ui_percentage: Percentage shown in UI
        
        Returns:
            Dictionary with analysis results
        """
        
        print("=== PORTFOLIO PERFORMANCE ANALYSIS ===")
        print(f"UI Values:")
        print(f"  Total Equity: ${total_equity:,.2f}")
        print(f"  Total Contributions: ${total_contributions:,.2f}")
        print(f"  Cash Balance: ${cash_balance:,.2f}")
        print(f"  UI Total Return: ${ui_total_return:,.2f}")
        print(f"  UI Percentage: {ui_percentage:.2f}%")
        print()
        
        # Calculate using corrected logic
        corrected_performance = self.calculate_portfolio_performance(
            total_equity=total_equity,
            total_contributions=total_contributions,
            cash_balance=cash_balance
        )
        
        print("=== CORRECTED CALCULATION ===")
        print(f"Total Portfolio Value: ${corrected_performance.total_equity + corrected_performance.cash_balance:,.2f}")
        print(f"Net Contributions: ${corrected_performance.total_contributions:,.2f}")
        print(f"Corrected Total Return: ${corrected_performance.total_return:,.2f}")
        print(f"Corrected Percentage: {corrected_performance.total_return_percentage:.2f}%")
        print()
        
        # Analyze the difference
        return_difference = corrected_performance.total_return - ui_total_return
        percentage_difference = corrected_performance.total_return_percentage - ui_percentage
        
        print("=== ANALYSIS ===")
        print(f"Return Difference: ${return_difference:,.2f}")
        print(f"Percentage Difference: {percentage_difference:.2f}%")
        print()
        
        # Identify the likely issue
        print("=== LIKELY ISSUE IDENTIFICATION ===")
        
        # Check if the UI is using the wrong formula
        ui_likely_formula = total_equity - total_contributions + cash_balance
        print(f"UI likely using: Total Equity - Total Contributions + Cash Balance")
        print(f"  = ${total_equity:,.2f} - ${total_contributions:,.2f} + ${cash_balance:,.2f}")
        print(f"  = ${ui_likely_formula:,.2f}")
        print()
        
        if abs(ui_likely_formula - ui_total_return) < 0.01:
            print("✅ CONFIRMED: UI is using the incorrect formula!")
            print("   The UI is adding cash balance to the return calculation.")
            print("   This is incorrect because cash balance is already part of total portfolio value.")
        else:
            print("❓ UI formula doesn't match the expected incorrect formula.")
            print("   There may be additional factors not visible in the UI.")
        
        print()
        print("=== RECOMMENDED CORRECTIONS ===")
        print("1. Use the corrected formula:")
        print("   Total Return = (Total Equity + Cash Balance) - Total Contributions")
        print("2. Consider adding:")
        print("   - Dividends received")
        print("   - Withdrawals made")
        print("   - Fees paid")
        print("3. Update the UI to show:")
        print(f"   Total Return: ${corrected_performance.total_return:,.2f}")
        print(f"   Percentage: {corrected_performance.total_return_percentage:.2f}%")
        
        return {
            'ui_values': {
                'total_equity': total_equity,
                'total_contributions': total_contributions,
                'cash_balance': cash_balance,
                'total_return': ui_total_return,
                'percentage': ui_percentage
            },
            'corrected_values': {
                'total_return': corrected_performance.total_return,
                'percentage': corrected_performance.total_return_percentage
            },
            'differences': {
                'return_difference': return_difference,
                'percentage_difference': percentage_difference
            },
            'likely_issue': 'UI adding cash balance to return calculation'
        }
    
    def create_portfolio_performance_function(self) -> str:
        """
        Create a SQL function for portfolio performance calculation.
        
        Returns:
            SQL function definition
        """
        
        sql_function = """
-- Portfolio Performance Calculation Function
CREATE OR REPLACE FUNCTION calculate_portfolio_performance(
    p_total_equity DECIMAL,
    p_total_contributions DECIMAL,
    p_cash_balance DECIMAL DEFAULT 0,
    p_dividends_received DECIMAL DEFAULT 0,
    p_withdrawals DECIMAL DEFAULT 0,
    p_fees_paid DECIMAL DEFAULT 0
)
RETURNS TABLE(
    total_equity DECIMAL,
    total_contributions DECIMAL,
    cash_balance DECIMAL,
    total_portfolio_value DECIMAL,
    net_contributions DECIMAL,
    total_return DECIMAL,
    total_return_percentage DECIMAL,
    dividends_received DECIMAL,
    withdrawals DECIMAL,
    fees_paid DECIMAL
) AS $$
BEGIN
    RETURN QUERY SELECT
        p_total_equity,
        p_total_contributions,
        p_cash_balance,
        p_total_equity + p_cash_balance as total_portfolio_value,
        p_total_contributions - p_withdrawals as net_contributions,
        (p_total_equity + p_cash_balance) - (p_total_contributions - p_withdrawals) + p_dividends_received - p_fees_paid as total_return,
        CASE 
            WHEN (p_total_contributions - p_withdrawals) > 0 
            THEN ((p_total_equity + p_cash_balance) - (p_total_contributions - p_withdrawals) + p_dividends_received - p_fees_paid) / (p_total_contributions - p_withdrawals) * 100
            ELSE 0
        END as total_return_percentage,
        p_dividends_received,
        p_withdrawals,
        p_fees_paid;
END;
$$ LANGUAGE plpgsql;
"""
        
        return sql_function
    
    def test_calculation_with_sample_data(self):
        """Test the calculation with various sample scenarios."""
        
        print("=== TESTING WITH SAMPLE DATA ===")
        
        test_cases = [
            {
                'name': 'UI Example (Incorrect)',
                'total_equity': 170540.50,
                'total_contributions': 257597.34,
                'cash_balance': 16362.70,
                'expected_ui_return': -70694.14
            },
            {
                'name': 'Profitable Portfolio',
                'total_equity': 120000.00,
                'total_contributions': 100000.00,
                'cash_balance': 5000.00,
                'dividends_received': 2000.00
            },
            {
                'name': 'Losing Portfolio',
                'total_equity': 80000.00,
                'total_contributions': 100000.00,
                'cash_balance': 2000.00
            },
            {
                'name': 'With Withdrawals',
                'total_equity': 150000.00,
                'total_contributions': 120000.00,
                'cash_balance': 10000.00,
                'withdrawals': 20000.00,
                'dividends_received': 5000.00
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\\nTest Case {i}: {case['name']}")
            print("-" * 40)
            
            performance = self.calculate_portfolio_performance(
                total_equity=case['total_equity'],
                total_contributions=case['total_contributions'],
                cash_balance=case.get('cash_balance', 0),
                dividends_received=case.get('dividends_received', 0),
                withdrawals=case.get('withdrawals', 0),
                fees_paid=case.get('fees_paid', 0)
            )
            
            print(f"Total Equity: ${performance.total_equity:,.2f}")
            print(f"Total Contributions: ${performance.total_contributions:,.2f}")
            print(f"Cash Balance: ${performance.cash_balance:,.2f}")
            print(f"Total Portfolio Value: ${performance.total_equity + performance.cash_balance:,.2f}")
            print(f"Total Return: ${performance.total_return:,.2f}")
            print(f"Total Return %: {performance.total_return_percentage:.2f}%")
            
            if 'expected_ui_return' in case:
                print(f"UI Expected Return: ${case['expected_ui_return']:,.2f}")
                print(f"Difference: ${performance.total_return - case['expected_ui_return']:,.2f}")

def main():
    """Main function to run the portfolio performance analysis."""
    
    calculator = PortfolioPerformanceCalculator()
    
    # Analyze the UI calculation issue
    analysis = calculator.analyze_ui_calculation_issue()
    
    # Test with sample data
    calculator.test_calculation_with_sample_data()
    
    # Show the SQL function
    print("\\n=== SQL FUNCTION FOR DATABASE ===")
    print(calculator.create_portfolio_performance_function())
    
    print("\\n=== SUMMARY ===")
    print("The main issue is that the UI is incorrectly adding cash balance")
    print("to the total return calculation. Cash balance should be included")
    print("in the total portfolio value, not added separately to the return.")
    print("\\nUse the corrected formula:")
    print("Total Return = (Total Equity + Cash Balance) - Total Contributions")

if __name__ == "__main__":
    main()

