"""
Dividends Router

Endpoints for dividend calendar and history.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
from datetime import date, datetime

from api.models.schemas import (
    DividendEvent, DividendListResponse, DividendSummary,
    DividendPayment, DividendInfo, DividendGrowth, DividendConsistency,
    DividendEventType, DividendFrequency,
    create_dividend_event_id, create_dividend_payment_id
)
from supabase_helpers import get_supabase_client

router = APIRouter()


@router.get("/dividends/calendar", response_model=DividendListResponse, summary="Get dividend calendar")
async def get_dividend_calendar(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    range: Optional[str] = Query(None, description="Preset range: 1w, 1m, 3m, 6m, 1y"),
    symbols: Optional[str] = Query(None, description="Comma-separated symbols"),
    min_yield: Optional[float] = Query(None, ge=0, description="Minimum yield %"),
    event_type: Optional[DividendEventType] = Query(None, description="Event type filter"),
    limit: int = Query(100, ge=1, le=5000, description="Max results (default 100, max 5000)"),
    sort: str = Query("asc", description="Sort order: asc (earliest first), desc (latest first)")
) -> DividendListResponse:
    """
    Get upcoming dividend events (ex-dates, payment dates) with flexible date filtering.

    Examples:
    - /dividends/calendar → Next 90 days
    - /dividends/calendar?range=1m → Next month
    - /dividends/calendar?start_date=2024-01-01 → From Jan 1 to 90 days later
    - /dividends/calendar?start_date=2024-01-01&end_date=2024-12-31 → Full year 2024
    - /dividends/calendar?range=3m&symbols=AAPL,MSFT → AAPL/MSFT next 3 months
    """
    try:
        from datetime import timedelta
        supabase = get_supabase_client()

        # Handle preset ranges (overrides dates if provided)
        if range:
            today = date.today()
            range_map = {
                '1w': 7,
                '1m': 30,
                '3m': 90,
                '6m': 180,
                '1y': 365
            }

            if range in range_map:
                start_date = today
                end_date = today + timedelta(days=range_map[range])
            else:
                raise HTTPException(
                    status_code=400,
                    detail={"error": {
                        "type": "invalid_request_error",
                        "message": f"Invalid range '{range}'. Valid options: 1w, 1m, 3m, 6m, 1y",
                        "param": "range",
                        "code": "invalid_range"
                    }}
                )

        # Handle start_date only case (from start_date + 90 days)
        elif start_date and not end_date:
            end_date = start_date + timedelta(days=90)

        # Handle end_date only case (90 days before end_date to end_date)
        elif end_date and not start_date:
            start_date = end_date - timedelta(days=90)

        # Default: next 90 days from today
        elif not start_date and not end_date:
            start_date = date.today()
            end_date = start_date + timedelta(days=90)

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
        query = supabase.table('raw_future_dividends').select('*')

        # Apply filters
        query = query.gte('ex_date', start_date.isoformat())
        query = query.lte('ex_date', end_date.isoformat())

        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
            query = query.in_('symbol', symbol_list)

        if min_yield is not None:
            # Join with raw_stocks to filter by yield
            pass  # TODO: Implement yield filter with join

        # Order and limit
        query = query.order('ex_date', desc=(sort == 'desc')).limit(limit)

        # Execute query
        result = query.execute()

        # Convert to DividendEvent models
        events = []
        for row in result.data:
            # Determine frequency
            frequency = None
            if row.get('frequency'):
                try:
                    frequency = DividendFrequency(row['frequency'].lower())
                except:
                    pass

            # Convert ex_date string to date object
            ex_date = row['ex_date']
            if isinstance(ex_date, str):
                from datetime import datetime as dt
                ex_date = dt.fromisoformat(ex_date).date()

            event = DividendEvent(
                id=create_dividend_event_id(row['symbol'], ex_date),
                symbol=row['symbol'],
                event_type=DividendEventType.EX_DIVIDEND,
                event_date=ex_date,
                amount=row.get('amount', 0.0),
                frequency=frequency,
                payment_date=row.get('payment_date'),
                company=row.get('company')
            )
            events.append(event)

        return DividendListResponse(
            data=events,
            has_more=len(result.data) == limit
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to fetch dividend calendar: {str(e)}",
                "code": "fetch_failed"
            }}
        )


@router.get("/dividends/history", response_model=DividendListResponse, summary="Get dividend history")
async def get_dividend_history(
    symbols: str = Query(..., description="Comma-separated symbols (required)"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page")
) -> DividendListResponse:
    """
    Get historical dividend payments across symbols.

    Returns a list of past dividend payments.
    """
    try:
        supabase = get_supabase_client()

        # Parse symbols
        symbol_list = [s.strip().upper() for s in symbols.split(',')]

        # Build query
        query = supabase.table('raw_dividends').select('*').in_('symbol', symbol_list)

        # Apply date filters
        if start_date:
            query = query.gte('ex_date', start_date.isoformat())
        if end_date:
            query = query.lte('ex_date', end_date.isoformat())

        # Order and limit
        query = query.order('ex_date', desc=True).limit(limit)

        # Execute query
        result = query.execute()

        # Convert to DividendPayment models (reusing DividendEvent)
        events = []
        for row in result.data:
            # Convert ex_date string to date object
            ex_date = row['ex_date']
            if isinstance(ex_date, str):
                from datetime import datetime as dt
                ex_date = dt.fromisoformat(ex_date).date()

            event = DividendEvent(
                id=create_dividend_payment_id(row['symbol'], ex_date),
                symbol=row['symbol'],
                event_type=DividendEventType.PAYMENT,
                event_date=ex_date,
                amount=row.get('amount', 0.0),
                payment_date=row.get('payment_date')
            )
            events.append(event)

        return DividendListResponse(
            data=events,
            has_more=len(result.data) == limit
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to fetch dividend history: {str(e)}",
                "code": "fetch_failed"
            }}
        )


@router.get("/stocks/{symbol}/dividends", response_model=DividendSummary, summary="Get stock dividend summary")
async def get_stock_dividends(
    symbol: str = Path(..., description="Stock symbol"),
    include_future: bool = Query(True, description="Include future scheduled dividends"),
    years: int = Query(5, ge=1, le=30, description="Years of history")
) -> DividendSummary:
    """
    Get complete dividend data for a specific stock.

    Includes current info, next payment, history, and growth metrics.
    """
    try:
        supabase = get_supabase_client()

        # Fetch stock for current dividend info
        stock_result = supabase.table('raw_stocks').select('*').eq('symbol', symbol.upper()).execute()

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

        # Current dividend info
        frequency = None
        if stock.get('dividend_frequency'):
            try:
                frequency = DividendFrequency(stock['dividend_frequency'].lower())
            except:
                pass

        current_info = DividendInfo(
            yield_=stock.get('dividend_yield', 0.0),
            annual_amount=stock.get('dividend_amount'),
            frequency=frequency,
            payout_ratio=stock.get('payout_ratio')
        )

        # Next payment (if include_future)
        next_payment = None
        if include_future:
            future_result = supabase.table('raw_future_dividends').select('*')\
                .eq('symbol', symbol.upper())\
                .gte('ex_date', date.today().isoformat())\
                .order('ex_date', desc=False)\
                .limit(1)\
                .execute()

            if future_result.data:
                row = future_result.data[0]
                # Convert ex_date string to date object
                ex_date = row['ex_date']
                if isinstance(ex_date, str):
                    from datetime import datetime as dt
                    ex_date = dt.fromisoformat(ex_date).date()

                next_payment = DividendEvent(
                    id=create_dividend_event_id(row['symbol'], ex_date),
                    symbol=row['symbol'],
                    event_type=DividendEventType.EX_DIVIDEND,
                    event_date=ex_date,
                    amount=row.get('amount', 0.0),
                    payment_date=row.get('payment_date')
                )

        # Historical dividends
        from datetime import timedelta
        cutoff_date = date.today() - timedelta(days=years * 365)
        history_result = supabase.table('raw_dividends').select('*')\
            .eq('symbol', symbol.upper())\
            .gte('ex_date', cutoff_date.isoformat())\
            .order('ex_date', desc=True)\
            .execute()

        history = []
        for row in history_result.data:
            # Convert ex_date string to date object
            ex_date = row['ex_date']
            if isinstance(ex_date, str):
                from datetime import datetime as dt
                ex_date = dt.fromisoformat(ex_date).date()

            payment = DividendPayment(
                id=create_dividend_payment_id(row['symbol'], ex_date),
                symbol=row['symbol'],
                payment_date=row.get('payment_date'),
                ex_dividend_date=ex_date,
                amount=row.get('amount', 0.0)
            )
            history.append(payment)

        # TODO: Calculate growth and consistency metrics from history
        growth = None
        consistency = None

        return DividendSummary(
            symbol=symbol.upper(),
            current=current_info,
            next_payment=next_payment,
            history=history,
            growth=growth,
            consistency=consistency
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to fetch dividend summary: {str(e)}",
                "code": "fetch_failed"
            }}
        )
