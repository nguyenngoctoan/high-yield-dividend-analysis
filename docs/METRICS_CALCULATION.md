# Stock Metrics Calculation

## Overview

The `calculate_stock_metrics.py` script calculates derived metrics for all stocks in the database based on historical price and dividend data.

## Metrics Calculated

### 1. Dividend Frequency
Determines how often dividends are paid based on historical dividend patterns:
- **Weekly**: ~7 days between payments (4-13 days tolerance)
- **Bi-Weekly**: ~14 days between payments (11-20 days tolerance)
- **Monthly**: ~30 days between payments (21-45 days tolerance)
- **Quarterly**: ~90 days between payments (70-115 days tolerance)
- **Semi-Annual**: ~180 days between payments (140-220 days tolerance)
- **Annual**: ~365 days between payments (320-410 days tolerance)

### 2. Total Return TTM (Trailing Twelve Months)
Measures total return including both price appreciation and dividends:
```
Total Return TTM = (Current Price - Price 12mo ago + Dividends TTM) / Price 12mo ago
```

### 3. Price Change TTM (Trailing Twelve Months)
Measures price appreciation only:
```
Price Change TTM = (Current Price - Price 12mo ago) / Price 12mo ago
```

### 4. Price Change YTD (Year-to-Date)
Measures price appreciation since start of current year:
```
Price Change YTD = (Current Price - Price at Year Start) / Price at Year Start
```

### 5. Additional Metrics
- **Last Dividend Date**: Most recent ex-dividend date
- **Last Dividend Amount**: Most recent dividend payment
- **Dividend Yield**: Annual dividends / Current price
- **Current Price**: Latest closing price

## Usage

### Calculate for All Stocks
```bash
source venv/bin/activate
python scripts/calculate_stock_metrics.py
```

### Calculate for Single Symbol
```bash
python scripts/calculate_stock_metrics.py --symbol AAPL
```

### Process with Limit (Testing)
```bash
python scripts/calculate_stock_metrics.py --limit 100
```

### Custom Batch Size
```bash
python scripts/calculate_stock_metrics.py --batch-size 200
```

## Automated Execution

### Hourly Cron Job

The script is designed to run hourly via cron. To set up:

```bash
# Navigate to project directory
cd /Users/toan/dev/high-yield-dividend-analysis

# Run setup script
./scripts/setup_hourly_metrics_cron.sh
```

This will install a cron job that runs every hour at minute 5.

### Manual Execution

You can also run the wrapper script manually:

```bash
./scripts/run_metrics_calculation.sh
```

### Viewing Logs

Logs are saved to `logs/metrics_calculation_YYYYMMDD.log`:

```bash
# View today's log
tail -f logs/metrics_calculation_$(date +%Y%m%d).log

# View all logs
ls -lh logs/metrics_calculation_*.log
```

## Database Updates

The script updates the following columns in the `stocks` table:

| Column | Type | Description |
|--------|------|-------------|
| `frequency` | text | Dividend payment frequency |
| `total_return_ttm` | numeric | Total return (trailing 12 months) |
| `price_change_ttm` | numeric | Price change (trailing 12 months) |
| `price_change_ytd` | numeric | Price change (year-to-date) |
| `price` | numeric | Current stock price |
| `last_dividend_date` | date | Most recent dividend date |
| `last_dividend_amount` | numeric | Most recent dividend amount |
| `dividend_yield` | numeric | Annual dividend yield |

## Performance

### Processing Time
- **Single stock**: ~0.5 seconds
- **100 stocks**: ~50 seconds
- **All stocks (23,519)**: ~3-4 hours

### Database Impact
- Uses batch updates (100 stocks per batch)
- Minimal database load
- Safe to run hourly

## Requirements

### Data Dependencies
The script requires:
1. **Price data** in `stock_prices` table
   - Current price
   - Historical prices (12+ months)

2. **Dividend data** in `dividend_history` table
   - Historical dividends
   - Ex-dividend dates

### Missing Data Handling
- Stocks without sufficient data are skipped
- Partial metrics are calculated when possible
- Errors are logged but don't stop processing

## Example Output

```
🚀 Starting stock metrics calculation
📊 Processing 23519 stocks
📈 Progress: 100/23519 (0.4%)
📈 Progress: 200/23519 (0.9%)
...
✅ Updated 100 stocks with calculated metrics
================================================================================
📊 METRICS CALCULATION SUMMARY
================================================================================
Total stocks processed: 23519
✅ Successful: 14926
❌ Failed: 8593

📈 Metrics Calculated:
   - Dividend frequency: 14016
   - Total return TTM: 16687
   - Price change YTD: 16687
================================================================================
```

## Troubleshooting

### No Metrics Calculated
**Problem**: Script runs but no metrics are calculated

**Solutions**:
1. Check if price data exists: `SELECT COUNT(*) FROM stock_prices;`
2. Check if dividend data exists: `SELECT COUNT(*) FROM dividend_history;`
3. Ensure Supabase is running: `docker ps | grep supabase`

### High TTM Values
**Problem**: Total return or price change values seem unusually high

**Cause**: May indicate:
- Stock splits not accounted for
- Data quality issues
- Very volatile stocks

**Solution**: Review individual stock data manually

### Cron Job Not Running
**Problem**: Hourly updates aren't happening

**Solutions**:
1. Check if cron job is installed: `crontab -l | grep metrics`
2. Check logs: `tail -f logs/metrics_calculation_*.log`
3. Verify script is executable: `ls -l scripts/run_metrics_calculation.sh`
4. Test manual run: `./scripts/run_metrics_calculation.sh`

## Integration with Data Pipeline

This script should be run:

1. **After major data updates**:
   - After repopulating dividend data
   - After bulk price updates
   - After adding new symbols

2. **On a regular schedule**:
   - Hourly via cron (recommended)
   - Daily minimum for production

3. **Before using calculated metrics**:
   - Portfolio performance calculations
   - Stock screening and ranking
   - Dividend yield analysis

## Related Scripts

- `update_stock_v2.py` - Main data update pipeline
- `scripts/repopulate_all_dividends.py` - Bulk dividend updates
- `scripts/run_all_scripts.py` - Master orchestration script

## Technical Details

### Frequency Algorithm

The frequency calculator:
1. Sorts dividends by ex-date
2. Calculates days between consecutive dividends
3. Finds average interval
4. Matches to frequency categories with tolerance ranges
5. Falls back to most common interval if no match

### TTM Calculation Strategy

For trailing twelve months:
1. Gets current price (most recent)
2. Finds price closest to 12 months ago
3. Sums dividends paid in last 12 months
4. Calculates return percentage

### YTD Calculation Strategy

For year-to-date:
1. Gets current price (most recent)
2. Finds price at start of current year (Jan 1)
3. Calculates percentage change

## Future Enhancements

Potential improvements:
- [ ] Add dividend growth rate calculation
- [ ] Calculate Sharpe ratio and volatility
- [ ] Add price target estimates
- [ ] Calculate forward dividend yield
- [ ] Add sector/industry percentile rankings
- [ ] Implement ML-based predictions
