# IV Discovery - Quick Reference Card

## One-Line Summary
**Implied Volatility (IV) from options chains is THE key indicator for covered call ETF distributions - higher IV = higher premiums = higher distributions.**

## Quick Start (30 seconds)

```bash
# Test your setup with a single covered call ETF
python scripts/discover_iv_for_covered_call_etfs.py --test XYLD

# Discover IV for all covered call ETFs
python scripts/discover_iv_for_covered_call_etfs.py
```

## Python API (Copy & Paste)

```python
# Single symbol
from lib.processors.iv_discovery_processor import discover_iv
result = discover_iv('XYLD')
print(f"IV: {result['iv']:.4f}, Call IV: {result['call_iv']:.4f}")

# All covered call ETFs
from lib.processors.iv_discovery_processor import discover_covered_call_etf_iv
summary = discover_covered_call_etf_iv()
print(f"Found IV for {summary['successful']} ETFs")

# Custom batch
from lib.processors.iv_discovery_processor import IVDiscoveryProcessor
processor = IVDiscoveryProcessor()
results = processor.process_batch(['XYLD', 'QYLD', 'JEPI'])
```

## SQL Queries (Copy & Paste)

```sql
-- Latest IV for covered call ETFs
SELECT s.symbol, s.name, p.iv, p.close, p.date
FROM raw_stocks s
JOIN raw_stock_prices p ON s.symbol = p.symbol
WHERE s.is_etf = true
  AND LOWER(s.investment_strategy) LIKE '%covered call%'
  AND p.iv IS NOT NULL
ORDER BY p.date DESC, p.iv DESC;

-- IV changes over time
SELECT symbol, date, iv,
       LAG(iv) OVER (PARTITION BY symbol ORDER BY date) as prev_iv
FROM raw_stock_prices
WHERE symbol = 'XYLD' AND iv IS NOT NULL
ORDER BY date DESC LIMIT 30;

-- Estimate monthly distributions
SELECT symbol,
       close as price,
       iv,
       (close * iv * SQRT(1.0/12)) as est_monthly_dist
FROM raw_stock_prices
WHERE symbol IN ('XYLD', 'QYLD', 'JEPI')
  AND iv IS NOT NULL
ORDER BY date DESC;
```

## Command-Line Options

```bash
# Test single symbol
python scripts/discover_iv_for_covered_call_etfs.py --test XYLD

# Process first 10 covered call ETFs
python scripts/discover_iv_for_covered_call_etfs.py --limit 10

# Force rediscovery (ignore cache)
python scripts/discover_iv_for_covered_call_etfs.py --force

# All liquid symbols with options
python scripts/discover_iv_for_covered_call_etfs.py --all-symbols --limit 100
```

## IV Interpretation

| IV Value | Meaning | Distributions | Action |
|----------|---------|---------------|--------|
| < 15% | Very low | Low | Look elsewhere |
| 15-20% | Normal | Normal | Standard covered call returns |
| 20-30% | Elevated | Higher | Good time for covered calls |
| > 30% | High | Very high | Excellent opportunity |

## Popular Covered Call ETFs

- **XYLD** - S&P 500 (most popular)
- **QYLD** - NASDAQ-100 (highest IV usually)
- **RYLD** - Russell 2000 (small-cap)
- **JEPI** - JPMorgan (active management)
- **JEPQ** - JPMorgan NASDAQ

## Why IV Matters

```
Higher IV → Sell options at higher premiums → Collect more income → Pay higher distributions
```

**Example**:
- XYLD at 15% IV: $0.40/month distribution
- XYLD at 30% IV: $0.60/month distribution (50% more!)

## Distribution Estimator

```python
# Quick estimate
monthly_dist = price * iv * (1/12)**0.5

# Example: XYLD at $42.50 with IV of 0.1845
monthly_dist = 42.50 * 0.1845 * 0.2887 = $0.45
```

## Daily Automation

```bash
# Add to cron (4:15 PM ET after market close)
15 16 * * 1-5 cd /path/to/project && python scripts/discover_iv_for_covered_call_etfs.py
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No IV found | Symbol may not have options; try `--test XYLD` |
| API error | Check Alpha Vantage Premium subscription |
| Rate limited | Wait a minute, Premium has 600-1200 req/min |
| No results | Verify covered call ETFs exist in `raw_stocks` table |

## Data Source

✅ **Alpha Vantage Premium** (you already have this!)
- REALTIME_OPTIONS function
- Includes IV and all Greeks
- 15+ years of historical data
- 600-1200 requests per minute

## Files Reference

- **Client**: `lib/data_sources/alpha_vantage_client.py`
- **Processor**: `lib/processors/iv_discovery_processor.py`
- **Script**: `scripts/discover_iv_for_covered_call_etfs.py`
- **Guide**: `docs/COVERED_CALL_ETF_IV_GUIDE.md`
- **Summary**: `IV_IMPLEMENTATION_SUMMARY.md`

## One-Command Setup Test

```bash
# Verify everything works
python scripts/discover_iv_for_covered_call_etfs.py --test XYLD && \
echo "✅ Success! Your IV discovery system is ready."
```

## Key Insight

**For covered call ETFs, call IV (not put IV) is what matters** because they're SELLING calls to generate income. The higher the call IV, the more premium they collect, and the more they can distribute to shareholders.

```python
result = discover_iv('XYLD')
call_iv = result['call_iv']  # ← This determines distributions!
put_iv = result['put_iv']    # ← Less relevant for covered calls
```

---

**Questions?** See full guide: `docs/COVERED_CALL_ETF_IV_GUIDE.md`
