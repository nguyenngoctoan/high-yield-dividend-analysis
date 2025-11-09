#!/bin/bash
#
# Fast SQL-based cleanup of international symbols
# Removes all stocks with international exchange suffixes from all tables
# Keeps US and Canadian stocks only
#

set -e

PGHOST="localhost"
PGPORT="5434"
PGUSER="postgres"
PGDATABASE="postgres"
export PGPASSWORD="postgres"

echo "========================================================================"
echo "International Symbols Cleanup (SQL)"
echo "========================================================================"
echo ""
echo "This will DELETE all stocks with international exchange suffixes"
echo "from ALL database tables."
echo ""
echo "Stocks that will be KEPT:"
echo "  - US: NASDAQ, NYSE, AMEX, BATS, OTC (no suffix)"
echo "  - Canadian: .TO (TSX), .V (TSXV)"
echo ""
echo "Stocks that will be DELETED:"
echo "  - All other international exchanges (.L, .DE, .KS, .T, .HK, etc.)"
echo ""

# Count current international symbols
echo "Counting international symbols..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
SELECT 'raw_stocks' as table_name, COUNT(*) as count
FROM raw_stocks
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$'

UNION ALL

SELECT 'raw_stock_prices', COUNT(DISTINCT symbol)
FROM raw_stock_prices
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$'

UNION ALL

SELECT 'raw_stock_prices_hourly', COUNT(DISTINCT symbol)
FROM raw_stock_prices_hourly
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$'

UNION ALL

SELECT 'raw_dividends', COUNT(DISTINCT symbol)
FROM raw_dividends
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$'

UNION ALL

SELECT 'raw_stock_splits', COUNT(DISTINCT symbol)
FROM raw_stock_splits
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$'

UNION ALL

SELECT 'holdings', COUNT(DISTINCT symbol)
FROM holdings
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$'

ORDER BY table_name;
EOF

echo ""
read -p "Do you want to DELETE all these international symbols? (yes/no): " response

if [ "$response" != "yes" ] && [ "$response" != "y" ]; then
    echo "Operation cancelled"
    exit 0
fi

echo ""
echo "Starting deletion..."
echo ""

# Delete from raw_stock_splits first (has foreign key to raw_stocks)
echo "Cleaning raw_stock_splits..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
DELETE FROM raw_stock_splits
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$';

SELECT COUNT(*) as deleted_count FROM raw_stock_splits WHERE FALSE;
EOF

# Delete from raw_stock_prices_hourly
echo "Cleaning raw_stock_prices_hourly..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
DELETE FROM raw_stock_prices_hourly
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$';
EOF

# Delete from raw_stock_prices
echo "Cleaning raw_stock_prices..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
DELETE FROM raw_stock_prices
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$';
EOF

# Delete from raw_dividends
echo "Cleaning raw_dividends..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
DELETE FROM raw_dividends
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$';
EOF

# Delete from raw_holdings_history
echo "Cleaning raw_holdings_history..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
DELETE FROM raw_holdings_history
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$';
EOF

# Delete from holdings
echo "Cleaning holdings..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
DELETE FROM holdings
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$';
EOF

# Delete from dim_stocks
echo "Cleaning dim_stocks..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
DELETE FROM dim_stocks
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$';
EOF

# Delete from raw_stocks (last, since others may have foreign keys)
echo "Cleaning raw_stocks..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
DELETE FROM raw_stocks
WHERE symbol ~ '\.(L|AX|DE|AS|MI|PA|SW|HK|BR|LS|MC|CO|ST|OL|HE|IC|VI|AT|WA|PR|BD|SA|MX|JK|KL|SI|BK|TW|KS|KQ|T|F|NZ|JO|SG|BO|NS|NE|ME)$';
EOF

echo ""
echo "========================================================================"
echo "✅ CLEANUP COMPLETE"
echo "========================================================================"
echo ""
echo "Verifying - remaining symbols:"
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
SELECT 'raw_stocks' as table_name, COUNT(*) as remaining
FROM raw_stocks

UNION ALL

SELECT 'raw_stock_prices', COUNT(DISTINCT symbol)
FROM raw_stock_prices

UNION ALL

SELECT 'raw_dividends', COUNT(DISTINCT symbol)
FROM raw_dividends

ORDER BY table_name;
EOF

echo ""
echo "✅ Done!"
