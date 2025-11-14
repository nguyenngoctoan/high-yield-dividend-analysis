# API Throughput Analysis and Optimization

## Current Status

### Aggressive Mode Performance (50 workers)
- **Throughput**: 309 API calls/minute (41% of 750/min limit)
- **Improvement**: +54% over baseline (200 calls/min)
- **Processing Rate**: ~3 symbols/second
- **Database Batching**: 2000 records every 1.5-2 seconds ✅

### Key Findings

#### What Works Well
1. **Batch Database Writes**: Background thread with Queue pattern successfully decoupled API fetching from database I/O
2. **Worker Optimization**: 50 workers provides good balance without overwhelming API (200 workers caused timeouts)
3. **Error Handling**: Automatic retry logic working correctly

#### Identified Bottlenecks

1. **FMP API Response Time** (PRIMARY BOTTLENECK)
   - Each historical fetch takes ~0.5-1 second per symbol
   - This is API server-side latency, not rate limiting
   - 19,205 symbols × 0.5s = ~160 minutes minimum (serial)
   - With 50 workers: 160 min ÷ 50 = 3.2 minutes minimum
   - Actual: ~5-6 minutes due to network overhead

2. **Historical Data Volume**
   - Fetching FULL historical data for every symbol on every run
   - This is unnecessary after initial backfill

3. **Sequential Symbol Processing**
   - Processing one symbol at a time (fetch prices + fetch dividends)
   - Even with concurrency, this limits throughput

## Why We Can't Hit 750 Calls/Minute with Current Approach

The **750 requests/minute limit** is a RATE limit, not a latency limit. Our bottleneck is API response latency:

- **Rate limit**: We can make 750 requests/minute = 12.5 req/sec
- **Latency limit**: Each request takes ~0.5-1 second to respond
- **Maximum theoretical throughput**: 50 workers × 1 req/sec = 50 symbols × 2 calls = 100 calls/sec = 6000 calls/min

BUT: FMP's server can't respond fast enough to sustain this.

### Actual Throughput Math
- 309 calls/min ÷ 60 = 5.15 calls/sec
- With 50 workers: 5.15 ÷ 50 = 0.103 calls/sec/worker
- Inverse: 1 ÷ 0.103 = 9.7 seconds per call per worker

This means each API call (on average) takes **~10 seconds** due to:
- FMP server processing time
- Network latency
- Queue waiting time

## Path to 700+ Calls/Minute

To achieve 700+ calls/minute, we need to **change the strategy**, not just tune concurrency.

### Strategy 1: Batch EOD for Daily Updates (RECOMMENDED)

**Use FMP's Batch EOD Endpoint** for daily updates:

```python
# Single API call gets ALL symbols' latest prices
batch_data = fmp_client.fetch_batch_eod_prices(today)
# Returns 19,205 symbols in ONE call
```

**Benefits**:
- 1 API call instead of 19,205 calls
- Perfect for daily updates (just need today's data)
- Would take <1 minute instead of hours

**Implementation**:
1. Create "incremental update" mode
2. Use batch EOD for today's prices (1 call)
3. Use batch for dividends if available
4. Only fetch historical data for NEW symbols

### Strategy 2: Smart Backfill

**Only fetch historical data when needed**:
- On first run: Fetch ALL historical data (current behavior)
- On daily runs: Use batch EOD for recent prices
- On symbol additions: Fetch historical for new symbols only

### Strategy 3: Parallel Batch Processing

**Fetch multiple date ranges in parallel**:
- Instead of fetching full history per symbol
- Fetch one date at a time for all symbols (batch EOD)
- Process 30 days in parallel using batch endpoints

## Implementation Priority

### Phase 1: Incremental Mode (HIGHEST IMPACT)
```bash
python3 update_stock_v2.py --mode incremental
```
- Use batch EOD for today only
- Expected: 1-2 minutes total (vs 60+ minutes)
- Expected throughput: 700+ calls/min (using batch endpoints)

### Phase 2: Smart Historical Backfill
- Track which symbols have complete historical data
- Only backfill gaps or new symbols
- Use checkpoint system to resume interrupted backfills

### Phase 3: Hybrid Approach
- Daily cron job: Incremental mode (fast, batch EOD)
- Weekly cron job: Historical backfill for new symbols
- Monthly cron job: Full verification and gap fill

## Current Aggressive Mode Results

### Performance Metrics (50 workers, batch writes)
```
Workers: 50
Batch Size: 2000 records
Current Throughput: 309 API calls/min
Improvement over baseline: +54%
Database write speed: 1000 records/sec ✅
```

### Conclusion
Aggressive mode with 50 workers and batched writes provides a **54% improvement** over baseline, but we've hit the **fundamental limit of per-symbol API latency**.

To achieve 700+ calls/minute, we must:
1. ✅ Implement batch EOD endpoint usage (1 call instead of 19K)
2. ✅ Create incremental update mode
3. ✅ Reserve full historical fetches for initial load and new symbols

**Next Step**: Implement incremental mode using batch EOD endpoint.
