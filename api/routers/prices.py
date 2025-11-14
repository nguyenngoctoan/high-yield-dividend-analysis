"""
Prices Router

Price history and snapshot endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
from datetime import date, datetime, timedelta

from api.models.schemas import (
    PriceHistoryResponse, PriceBar, PriceSnapshot,
    HourlyPriceResponse, HourlyPriceBar
)
from supabase_helpers import get_supabase_client

router = APIRouter()


@router.get("/prices/{symbol}", response_model=PriceHistoryResponse, summary="Get price history")
async def get_price_history(
    symbol: str = Path(..., description="Stock symbol"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    range: Optional[str] = Query(None, description="Preset range: 1d, 5d, 1m, 3m, 6m, ytd, 1y, 2y, 5y, max"),
    interval: str = Query("daily", description="Interval: daily, weekly, monthly"),
    limit: int = Query(100, ge=1, le=5000, description="Max results (default 100, max 5000)"),
    sort: str = Query("desc", description="Sort order: asc (oldest first), desc (newest first)"),
    adjusted: bool = Query(True, description="Use adjusted prices (split/dividend adjusted)")
) -> PriceHistoryResponse:
    """
    Get price history for a symbol with flexible date filtering.

    Examples:
    - /prices/AAPL → Last 30 days
    - /prices/AAPL?range=1y → Last year
    - /prices/AAPL?range=ytd → Year to date
    - /prices/AAPL?start_date=2023-01-01 → From Jan 1, 2023 to today
    - /prices/AAPL?start_date=2023-01-01&end_date=2023-12-31 → Full year 2023
    - /prices/AAPL?range=1m&sort=asc → Last month, oldest first
    """
    try:
        supabase = get_supabase_client()

        # Handle preset ranges (overrides dates if provided)
        if range:
            today = date.today()
            range_map = {
                '1d': 1,
                '5d': 5,
                '1m': 30,
                '3m': 90,
                '6m': 180,
                '1y': 365,
                '2y': 730,
                '5y': 1825,
                'ytd': (today - date(today.year, 1, 1)).days,
                'max': None
            }

            if range in range_map:
                end_date = today
                if range == 'max':
                    # Get all available data - set start_date very far back
                    start_date = date(1990, 1, 1)
                else:
                    start_date = today - timedelta(days=range_map[range])
            else:
                raise HTTPException(
                    status_code=400,
                    detail={"error": {
                        "type": "invalid_request_error",
                        "message": f"Invalid range '{range}'. Valid options: 1d, 5d, 1m, 3m, 6m, ytd, 1y, 2y, 5y, max",
                        "param": "range",
                        "code": "invalid_range"
                    }}
                )

        # Handle start_date only case (from start_date to today)
        elif start_date and not end_date:
            end_date = date.today()

        # Handle end_date only case (30 days before end_date to end_date)
        elif end_date and not start_date:
            start_date = end_date - timedelta(days=30)

        # Default: last 30 days
        elif not start_date and not end_date:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

        # Validate sort parameter
        if sort not in ['asc', 'desc']:
            raise HTTPException(
                status_code=400,
                detail={"error": {
                    "type": "invalid_request_error",
                    "message": f"Invalid sort '{sort}'. Must be 'asc' or 'desc'",
                    "param": "sort",
                    "code": "invalid_sort"
                }}
            )

        # Build query
        query = supabase.table('raw_stock_prices').select('*')\
            .eq('symbol', symbol.upper())\
            .gte('date', start_date.isoformat())\
            .lte('date', end_date.isoformat())\
            .order('date', desc=(sort == 'desc'))\
            .limit(limit)

        # Execute
        result = query.execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail={"error": {
                    "type": "resource_not_found_error",
                    "message": f"No price data found for '{symbol}'",
                    "param": "symbol",
                    "code": "no_price_data"
                }}
            )

        # Convert to PriceBar models
        price_bars = []
        for row in result.data:
            # Use adjusted close if requested and available, otherwise use regular close
            if adjusted and row.get('adj_close') is not None:
                close_price = row.get('adj_close')
            else:
                close_price = row.get('close', 0.0)

            bar = PriceBar(
                date=row['date'],
                open=row.get('open', 0.0),
                high=row.get('high', 0.0),
                low=row.get('low', 0.0),
                close=close_price,
                volume=row.get('volume', 0),
                adj_close=row.get('adj_close')
            )
            price_bars.append(bar)

        return PriceHistoryResponse(
            symbol=symbol.upper(),
            interval=interval,
            data=price_bars,
            has_more=len(result.data) == limit
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to fetch price history: {str(e)}",
                "code": "fetch_failed"
            }}
        )


@router.get("/prices/{symbol}/latest", response_model=PriceSnapshot, summary="Get latest price")
async def get_latest_price(
    symbol: str = Path(..., description="Stock symbol")
) -> PriceSnapshot:
    """
    Get latest price snapshot for a symbol.

    Returns current price with change information.
    """
    try:
        supabase = get_supabase_client()

        # Fetch stock for latest price
        stock_result = supabase.table('raw_stocks').select('*')\
            .eq('symbol', symbol.upper())\
            .execute()

        if not stock_result.data:
            raise HTTPException(
                status_code=404,
                detail={"error": {
                    "type": "resource_not_found_error",
                    "message": f"Symbol '{symbol}' not found",
                    "param": "symbol",
                    "code": "symbol_not_found"
                }}
            )

        stock = stock_result.data[0]

        # Determine market status (simple approximation)
        now = datetime.now()
        market_hours = (9, 30) <= (now.hour, now.minute) < (16, 0)
        is_weekday = now.weekday() < 5
        market_status = "open" if (market_hours and is_weekday) else "closed"

        return PriceSnapshot(
            symbol=symbol.upper(),
            price=stock.get('price', 0.0),
            change=stock.get('change', 0.0),
            change_percent=stock.get('change_percent', 0.0),
            volume=stock.get('volume', 0),
            timestamp=stock.get('updated_at', datetime.now()),
            market_status=market_status
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to fetch latest price: {str(e)}",
                "code": "fetch_failed"
            }}
        )


@router.get("/prices/{symbol}/hourly", response_model=HourlyPriceResponse, summary="Get hourly price data")
async def get_hourly_prices(
    symbol: str = Path(..., description="Stock symbol"),
    date: Optional[date] = Query(None, description="Specific date (YYYY-MM-DD), defaults to today"),
    limit: int = Query(24, ge=1, le=100, description="Max results (default 24 hours)")
) -> HourlyPriceResponse:
    """
    Get intraday hourly price data for a symbol.

    Returns hour-by-hour OHLCV data for market hours.

    Examples:
    - /prices/AAPL/hourly → Today's hourly prices
    - /prices/AAPL/hourly?date=2025-11-12 → Specific date
    """
    try:
        supabase = get_supabase_client()

        # Default to today if no date specified
        target_date = date if date else datetime.now().date()

        # Fetch hourly prices
        query = supabase.table('raw_stock_prices_hourly').select('*')\
            .eq('symbol', symbol.upper())\
            .eq('date', target_date.isoformat())\
            .order('timestamp', desc=False)\
            .limit(limit)

        result = query.execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail={"error": {
                    "type": "resource_not_found_error",
                    "message": f"No hourly data found for '{symbol}' on {target_date}",
                    "param": "symbol",
                    "code": "data_not_found"
                }}
            )

        # Convert to HourlyPriceBar models
        bars = []
        for row in result.data:
            bar = HourlyPriceBar(
                timestamp=row['timestamp'],
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                vwap=row.get('vwap')
            )
            bars.append(bar)

        return HourlyPriceResponse(
            symbol=symbol.upper(),
            date=target_date,
            data=bars
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to fetch hourly prices: {str(e)}",
                "code": "fetch_failed"
            }}
        )
