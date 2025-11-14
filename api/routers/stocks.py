"""
Stocks Router

Endpoints for stock and ETF information.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
import base64
import json

from api.models.schemas import (
    Stock, StockDetail, StockListResponse, StockType,
    CompanyInfo, PricingInfo, DividendInfo, DividendFrequency,
    create_stock_id, ErrorResponse, Fundamentals, DividendMetrics,
    HourlyPriceResponse, HourlyPriceBar, StockSplit, SplitHistoryResponse
)
from supabase_helpers import get_supabase_client

router = APIRouter()


def encode_cursor(data: dict) -> str:
    """Encode pagination cursor."""
    return base64.b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor: str) -> dict:
    """Decode pagination cursor."""
    try:
        return json.loads(base64.b64decode(cursor).decode())
    except:
        raise HTTPException(status_code=400, detail="Invalid cursor")


@router.get("/stocks", response_model=StockListResponse, summary="List stocks")
async def list_stocks(
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    type: Optional[StockType] = Query(None, description="Filter by type"),
    has_dividends: Optional[bool] = Query(None, description="Filter for dividend-paying stocks"),
    min_yield: Optional[float] = Query(None, ge=0, description="Minimum dividend yield %"),
    max_yield: Optional[float] = Query(None, ge=0, description="Maximum dividend yield %"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page"),
    cursor: Optional[str] = Query(None, description="Pagination cursor")
) -> StockListResponse:
    """
    List all available stocks with optional filtering.

    Returns a paginated list of stocks matching the specified criteria.
    """
    try:
        supabase = get_supabase_client()

        # Build query
        query = supabase.table('raw_stocks').select('*')

        # Apply filters
        if exchange:
            query = query.eq('exchange', exchange.upper())

        if type:
            query = query.eq('type', type.value)

        if has_dividends is not None:
            if has_dividends:
                query = query.not_.is_('dividend_yield', 'null').gt('dividend_yield', 0)
            else:
                query = query.or_('dividend_yield.is.null,dividend_yield.eq.0')

        if min_yield is not None:
            query = query.gte('dividend_yield', min_yield)

        if max_yield is not None:
            query = query.lte('dividend_yield', max_yield)

        if sector:
            query = query.eq('sector', sector)

        # Handle cursor pagination
        if cursor:
            cursor_data = decode_cursor(cursor)
            query = query.gt('symbol', cursor_data.get('last_symbol'))

        # Order and limit
        query = query.order('symbol', desc=False).limit(limit + 1)

        # Execute query
        result = query.execute()

        # Check if there are more results
        has_more = len(result.data) > limit
        data = result.data[:limit] if has_more else result.data

        # Generate next cursor
        next_cursor = None
        if has_more and data:
            next_cursor = encode_cursor({'last_symbol': data[-1]['symbol']})

        # Convert to Stock models
        stocks = []
        for row in data:
            stock = Stock(
                id=create_stock_id(row['symbol']),
                symbol=row['symbol'],
                exchange=row.get('exchange', 'UNKNOWN'),
                type=row.get('type', 'stock'),
                company=row.get('company'),
                sector=row.get('sector'),
                price=row.get('price'),
                dividend_yield=row.get('dividend_yield'),
                updated_at=row.get('updated_at', row.get('created_at'))
            )
            stocks.append(stock)

        return StockListResponse(
            data=stocks,
            has_more=has_more,
            cursor=next_cursor
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to fetch stocks: {str(e)}",
                "code": "fetch_failed"
            }}
        )


@router.get("/stocks/{symbol}", response_model=StockDetail, summary="Get stock details")
async def get_stock(
    symbol: str = Path(..., description="Stock symbol"),
    expand: Optional[str] = Query(None, description="Comma-separated fields to expand: company,dividends,prices")
) -> StockDetail:
    """
    Retrieve detailed information for a specific stock.

    Supports expansion of related data via the expand parameter.
    """
    try:
        supabase = get_supabase_client()

        # Fetch stock
        result = supabase.table('raw_stocks').select('*').eq('symbol', symbol.upper()).execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail={"error": {
                    "type": "resource_not_found_error",
                    "message": f"Symbol '{symbol}' not found",
                    "param": "symbol",
                    "code": "symbol_not_found"
                }}
            )

        row = result.data[0]

        # Parse expand parameter
        expand_fields = set()
        if expand:
            expand_fields = set(f.strip() for f in expand.split(','))

        # Build company info
        company_info = None
        if 'company' in expand_fields or not expand:
            company_info = CompanyInfo(
                name=row.get('company', 'Unknown'),
                description=row.get('description'),
                ceo=row.get('ceo'),
                sector=row.get('sector'),
                industry=row.get('industry'),
                market_cap=row.get('market_cap'),
                employees=row.get('employees'),
                website=row.get('website'),
                country=row.get('country'),
                ipo_date=row.get('ipo_date'),
                currency=row.get('currency')
            )

        # Build pricing info
        pricing_info = None
        if 'prices' in expand_fields or not expand:
            pricing_info = PricingInfo(
                current=row.get('price', 0.0),
                open=row.get('open'),
                high=row.get('high'),
                low=row.get('low'),
                volume=row.get('volume'),
                change=row.get('change'),
                change_percent=row.get('change_percent'),
                pe_ratio=row.get('pe_ratio'),
                vwap=row.get('vwap')
            )

        # Build dividend info
        dividend_info = None
        if row.get('dividend_yield') and ('dividends' in expand_fields or not expand):
            # Determine frequency from dividend data
            frequency = None
            if row.get('dividend_frequency'):
                try:
                    frequency = DividendFrequency(row['dividend_frequency'].lower())
                except:
                    pass

            dividend_info = DividendInfo(
                yield_=row.get('dividend_yield', 0.0),
                annual_amount=row.get('dividend_amount'),
                frequency=frequency,
                ex_dividend_date=row.get('ex_dividend_date'),
                payment_date=row.get('dividend_date'),
                payout_ratio=row.get('payout_ratio'),
                five_yr_growth_rate=row.get('dividend_growth_5yr')
            )

        return StockDetail(
            id=create_stock_id(row['symbol']),
            symbol=row['symbol'],
            exchange=row.get('exchange', 'UNKNOWN'),
            type=row.get('type', 'stock'),
            company=company_info,
            pricing=pricing_info,
            dividends=dividend_info,
            updated_at=row.get('updated_at', row.get('created_at'))
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to fetch stock details: {str(e)}",
                "code": "fetch_failed"
            }}
        )


@router.get("/stocks/{symbol}/fundamentals", response_model=Fundamentals, summary="Get stock fundamentals")
async def get_stock_fundamentals(
    symbol: str = Path(..., description="Stock symbol")
) -> Fundamentals:
    """
    Get detailed fundamental metrics for a stock.

    Returns company fundamentals including market cap, P/E ratio, sector info, etc.
    """
    try:
        supabase = get_supabase_client()

        # Fetch stock
        result = supabase.table('raw_stocks').select('*').eq('symbol', symbol.upper()).execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail={"error": {
                    "type": "resource_not_found_error",
                    "message": f"Symbol '{symbol}' not found",
                    "param": "symbol",
                    "code": "symbol_not_found"
                }}
            )

        row = result.data[0]

        return Fundamentals(
            symbol=row['symbol'],
            market_cap=row.get('market_cap'),
            pe_ratio=row.get('pe_ratio'),
            payout_ratio=row.get('payout_ratio'),
            employees=row.get('employees'),
            ipo_date=row.get('ipo_date'),
            sector=row.get('sector'),
            industry=row.get('industry'),
            website=row.get('website'),
            country=row.get('country')
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to fetch fundamentals: {str(e)}",
                "code": "fetch_failed"
            }}
        )


@router.get("/stocks/{symbol}/metrics", response_model=DividendMetrics, summary="Get dividend metrics")
async def get_dividend_metrics(
    symbol: str = Path(..., description="Stock symbol")
) -> DividendMetrics:
    """
    Get detailed dividend metrics and consistency data.

    Returns dividend yield, growth rates, payout ratio, and consistency metrics
    including Dividend Aristocrat/King status.
    """
    try:
        supabase = get_supabase_client()

        # Fetch stock
        result = supabase.table('raw_stocks').select('*').eq('symbol', symbol.upper()).execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail={"error": {
                    "type": "resource_not_found_error",
                    "message": f"Symbol '{symbol}' not found",
                    "param": "symbol",
                    "code": "symbol_not_found"
                }}
            )

        row = result.data[0]

        # Calculate consecutive increases from dividend history
        div_result = supabase.table('raw_dividends')\
            .select('ex_date, amount')\
            .eq('symbol', symbol.upper())\
            .order('ex_date', desc=True)\
            .limit(200)\
            .execute()

        consecutive_increases = 0
        consecutive_payments = len(div_result.data) if div_result.data else 0

        # Simple consecutive increase calculation
        if div_result.data and len(div_result.data) >= 2:
            prev_amount = None
            for div in reversed(div_result.data):
                if prev_amount is not None:
                    if div['amount'] >= prev_amount:
                        consecutive_increases += 1
                    else:
                        break
                prev_amount = div['amount']

        # Determine aristocrat/king status (simplified)
        is_aristocrat = consecutive_increases >= 25
        is_king = consecutive_increases >= 50

        # Parse frequency
        frequency = None
        if row.get('dividend_frequency'):
            try:
                frequency = DividendFrequency(row['dividend_frequency'].lower())
            except:
                pass

        return DividendMetrics(
            symbol=row['symbol'],
            current_yield=row.get('dividend_yield'),
            annual_amount=row.get('dividend_amount'),
            frequency=frequency,
            payout_ratio=row.get('payout_ratio'),
            five_yr_growth_rate=row.get('dividend_growth_5yr'),
            consecutive_increases=consecutive_increases if consecutive_increases > 0 else None,
            consecutive_payments=consecutive_payments if consecutive_payments > 0 else None,
            is_dividend_aristocrat=is_aristocrat,
            is_dividend_king=is_king
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to fetch dividend metrics: {str(e)}",
                "code": "fetch_failed"
            }}
        )


@router.get("/stocks/{symbol}/splits", response_model=SplitHistoryResponse, summary="Get stock split history")
async def get_stock_splits(
    symbol: str = Path(..., description="Stock symbol"),
    limit: int = Query(50, ge=1, le=200, description="Max results")
) -> SplitHistoryResponse:
    """
    Get historical stock split events for a symbol.

    Returns all stock splits with split ratios and dates.
    """
    try:
        supabase = get_supabase_client()

        # Fetch splits
        result = supabase.table('raw_stock_splits').select('*')\
            .eq('symbol', symbol.upper())\
            .order('date', desc=True)\
            .limit(limit)\
            .execute()

        # Convert to StockSplit models
        splits = []
        for row in result.data:
            split = StockSplit(
                id=f"split_{symbol.lower()}_{row['date']}",
                symbol=row['symbol'],
                date=row['date'],
                ratio=row.get('ratio', row.get('split_ratio', 1.0)),
                from_factor=row.get('from_factor'),
                to_factor=row.get('to_factor')
            )
            splits.append(split)

        return SplitHistoryResponse(
            symbol=symbol.upper(),
            data=splits
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to fetch stock splits: {str(e)}",
                "code": "fetch_failed"
            }}
        )
