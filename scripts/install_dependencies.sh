#!/bin/bash

echo "=========================================="
echo "📦 Installing Dependencies"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment found"
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "📌 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

echo ""
echo "📥 Upgrading pip..."
pip install --upgrade pip

echo ""
echo "📥 Installing required packages..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Testing imports..."
python3 -c "
import yfinance
import supabase
import pandas
import requests
print('✅ yfinance imported successfully')
print('✅ supabase imported successfully')
print('✅ pandas imported successfully')
print('✅ requests imported successfully')
"

echo ""
echo "You can now run:"
echo "  ./run_nasdaq_full_update.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  python3 update_stock.py --nasdaq-only --discover-symbols --validate-discovered"