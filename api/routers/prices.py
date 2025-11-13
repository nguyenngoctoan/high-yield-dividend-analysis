"""
Prices Router

Price history and snapshot endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
from datetime import date, datetime, timedelta

from api.models.schemas import (
    PriceHistoryResponse, PriceBar, PriceSnapshot
)
from supabase_helpers import get_supabase_client

router = APIRouter()


@router.get("/prices/{symbol}", response_model=PriceHistoryResponse, summary="Get price history")
async def get_price_history(
    symbol: str = Path(..., description="Stock symbol"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    interval: str = Query("daily", description="Interval: daily, weekly, monthly"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page")
) -> PriceHistoryResponse:
    """
    Get price history for a symbol.

    Returns OHLCV data for the specified date range.
    """
    try:
        supabase = get_supabase_client()

        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Build query
        query = supabase.table('raw_stock_prices').select('*')\
            .eq('symbol', symbol.upper())\
            .gte('date', start_date.isoformat())\
            .lte('date', end_date.isoformat())\
            .order('date', desc=True)\
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
            bar = PriceBar(
                date=row['date'],
                open=row.get('open', 0.0),
                high=row.get('high', 0.0),
                low=row.get('low', 0.0),
                close=row.get('close', 0.0),
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
