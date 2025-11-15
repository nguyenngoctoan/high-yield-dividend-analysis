#!/bin/bash
# Full Batch Update - Populate GOOGLEFINANCE Parity Data
# This will fetch and save fundamental data for ALL stocks

echo "=================================================="
echo "  GOOGLEFINANCE Parity Data - Full Batch Update"
echo "=================================================="
echo ""
echo "This will:"
echo "  • Fetch quotes for 16,000+ stocks"
echo "  • Save all GOOGLEFINANCE parity fields"
echo "  • Take approximately 1-2 minutes"
echo ""
echo "Starting update..."
echo ""

python3 update.py --mode batch

echo ""
echo "=================================================="
echo "  ✅ Update Complete!"
echo "=================================================="
echo ""
echo "Test the quote endpoint:"
echo "  curl http://localhost:8000/v1/stocks/AAPL/quote | jq"
echo ""
