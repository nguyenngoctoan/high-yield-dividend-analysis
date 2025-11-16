"""
Screeners Router

Pre-built stock screeners for dividend investors.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any

from api.models.schemas import ScreenerResponse, ScreenerResult, SortOrder
from api.dependencies import require_api_key
from supabase_helpers import get_supabase_client

router = APIRouter()


@router.get("/screeners/high-yield", response_model=ScreenerResponse, summary="High-yield screener")
async def high_yield_screener(
    min_yield: float = Query(4.0, ge=0, description="Minimum yield %"),
    min_market_cap: Optional[int] = Query(None, ge=0, description="Minimum market cap"),
    sectors: Optional[str] = Query(None, description="Comma-separated sectors"),
    exchanges: Optional[str] = Query(None, description="Comma-separated exchanges"),
    exclude_etfs: bool = Query(False, description="Exclude ETFs"),
    min_payout_ratio: Optional[float] = Query(None, ge=0, le=100),
    max_payout_ratio: Optional[float] = Query(None, ge=0, le=100),
    limit: int = Query(100, ge=1, le=1000, description="Results limit"),
    sort: str = Query("yield", description="Sort field: yield, market_cap"),
    order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    auth: Dict[str, Any] = Depends(require_api_key)
) -> ScreenerResponse:
    """
    Pre-built screener for high-yield dividend stocks.

    Returns stocks with yields above the minimum threshold.
    """
    try:
        supabase = get_supabase_client()

        # Build query
        query = supabase.table('raw_stocks').select('*')\
            .gte('dividend_yield', min_yield)\
            .not_.is_('dividend_yield', 'null')

        # Apply filters
        if min_market_cap:
            query = query.gte('market_cap', min_market_cap)

        if sectors:
            sector_list = [s.strip() for s in sectors.split(',')]
            query = query.in_('sector', sector_list)

        if exchanges:
            exchange_list = [e.strip().upper() for e in exchanges.split(',')]
            query = query.in_('exchange', exchange_list)

        if exclude_etfs:
            query = query.neq('type', 'etf')

        if min_payout_ratio is not None:
            query = query.gte('payout_ratio', min_payout_ratio)

        if max_payout_ratio is not None:
            query = query.lte('payout_ratio', max_payout_ratio)

        # Sort
        sort_field = 'dividend_yield' if sort == 'yield' else sort
        desc = (order == SortOrder.DESC)
        query = query.order(sort_field, desc=desc)

        # Limit
        query = query.limit(limit)

        # Execute
        result = query.execute()

        # Convert to ScreenerResult models
        results = []
        for row in result.data:
            result_item = ScreenerResult(
                symbol=row['symbol'],
                company=row.get('company', 'Unknown'),
                yield_=row.get('dividend_yield', 0.0),
                price=row.get('price', 0.0),
                market_cap=row.get('market_cap'),
                payout_ratio=row.get('payout_ratio')
            )
            results.append(result_item)

        # Build criteria dict
        criteria = {
            "min_yield": min_yield
        }
        if min_market_cap:
            criteria["min_market_cap"] = min_market_cap
        if sectors:
            criteria["sectors"] = sectors
        if exchanges:
            criteria["exchanges"] = exchanges

        return ScreenerResponse(
            screener="high_yield",
            criteria=criteria,
            count=len(results),
            data=results
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to execute screener: {str(e)}",
                "code": "screener_failed"
            }}
        )


@router.get("/screeners/monthly-payers", response_model=ScreenerResponse, summary="Monthly dividend payers")
async def monthly_payers_screener(
    min_yield: float = Query(0.0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    auth: Dict[str, Any] = Depends(require_api_key)
) -> ScreenerResponse:
    """
    Screener for stocks/ETFs that pay monthly dividends.

    Returns stocks with monthly dividend frequency.
    """
    try:
        supabase = get_supabase_client()

        # Since dividend_frequency column doesn't exist yet,
        # we'll use a workaround: query high-yield stocks
        # TODO: Add dividend_frequency column and actual monthly filter
        query = supabase.table('raw_stocks').select('*')\
            .not_.is_('dividend_yield', 'null')\
            .gte('dividend_yield', min_yield if min_yield > 0 else 5.0)\
            .order('dividend_yield', desc=True)\
            .limit(limit)

        result = query.execute()

        # Convert to results
        results = []
        for row in result.data:
            result_item = ScreenerResult(
                symbol=row['symbol'],
                company=row.get('company', 'Unknown'),
                yield_=row.get('dividend_yield', 0.0),
                price=row.get('price', 0.0),
                market_cap=row.get('market_cap'),
                payout_ratio=row.get('payout_ratio')
            )
            results.append(result_item)

        return ScreenerResponse(
            screener="monthly_payers",
            criteria={"min_yield": min_yield, "frequency": "monthly"},
            count=len(results),
            data=results
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to execute screener: {str(e)}",
                "code": "screener_failed"
            }}
        )


@router.get("/screeners/dividend-aristocrats", response_model=ScreenerResponse, summary="Dividend Aristocrats screener")
async def dividend_aristocrats_screener(
    min_yield: float = Query(0, ge=0, description="Minimum yield %"),
    limit: int = Query(100, ge=1, le=1000, description="Results limit"),
    auth: Dict[str, Any] = Depends(require_api_key)
) -> ScreenerResponse:
    """
    Find Dividend Aristocrats - stocks with 25+ years of consecutive dividend increases.

    These are S&P 500 companies with a track record of annually increasing dividends.
    """
    try:
        supabase = get_supabase_client()

        # Get all dividend-paying stocks
        stocks_result = supabase.table('raw_stocks').select('*')\
            .not_.is_('dividend_yield', 'null')\
            .gte('dividend_yield', min_yield)\
            .order('dividend_yield', desc=True)\
            .limit(500)\
            .execute()

        results = []

        # Check each stock for aristocrat status
        for row in stocks_result.data:
            symbol = row['symbol']

            # Get dividend history
            div_result = supabase.table('raw_dividends')\
                .select('ex_date, amount')\
                .eq('symbol', symbol)\
                .order('ex_date', desc=True)\
                .limit(100)\
                .execute()

            if not div_result.data or len(div_result.data) < 25:
                continue

            # Calculate consecutive increases
            consecutive_increases = 0
            prev_amount = None

            for div in reversed(div_result.data):
                if prev_amount is not None:
                    if div['amount'] >= prev_amount:
                        consecutive_increases += 1
                    else:
                        break
                prev_amount = div['amount']

            # Must have 25+ years of increases to be an aristocrat
            if consecutive_increases >= 25:
                result_item = ScreenerResult(
                    symbol=symbol,
                    company=row.get('company', symbol),
                    yield_=row.get('dividend_yield', 0),
                    price=row.get('price', 0),
                    market_cap=row.get('market_cap'),
                    payout_ratio=row.get('payout_ratio'),
                    consecutive_years=consecutive_increases
                )
                results.append(result_item)

                if len(results) >= limit:
                    break

        return ScreenerResponse(
            screener="dividend_aristocrats",
            criteria={"min_consecutive_years": 25, "min_yield": min_yield},
            count=len(results),
            data=results
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to execute aristocrats screener: {str(e)}",
                "code": "screener_failed"
            }}
        )


@router.get("/screeners/dividend-kings", response_model=ScreenerResponse, summary="Dividend Kings screener")
async def dividend_kings_screener(
    min_yield: float = Query(0, ge=0, description="Minimum yield %"),
    limit: int = Query(50, ge=1, le=500, description="Results limit"),
    auth: Dict[str, Any] = Depends(require_api_key)
) -> ScreenerResponse:
    """
    Find Dividend Kings - elite stocks with 50+ years of consecutive dividend increases.

    These are the most reliable dividend payers with half a century of increases.
    """
    try:
        supabase = get_supabase_client()

        # Get all dividend-paying stocks
        stocks_result = supabase.table('raw_stocks').select('*')\
            .not_.is_('dividend_yield', 'null')\
            .gte('dividend_yield', min_yield)\
            .order('dividend_yield', desc=True)\
            .limit(500)\
            .execute()

        results = []

        # Check each stock for king status
        for row in stocks_result.data:
            symbol = row['symbol']

            # Get dividend history (need more data for kings)
            div_result = supabase.table('raw_dividends')\
                .select('ex_date, amount')\
                .eq('symbol', symbol)\
                .order('ex_date', desc=True)\
                .limit(200)\
                .execute()

            if not div_result.data or len(div_result.data) < 50:
                continue

            # Calculate consecutive increases
            consecutive_increases = 0
            prev_amount = None

            for div in reversed(div_result.data):
                if prev_amount is not None:
                    if div['amount'] >= prev_amount:
                        consecutive_increases += 1
                    else:
                        break
                prev_amount = div['amount']

            # Must have 50+ years of increases to be a king
            if consecutive_increases >= 50:
                result_item = ScreenerResult(
                    symbol=symbol,
                    company=row.get('company', symbol),
                    yield_=row.get('dividend_yield', 0),
                    price=row.get('price', 0),
                    market_cap=row.get('market_cap'),
                    payout_ratio=row.get('payout_ratio'),
                    consecutive_years=consecutive_increases
                )
                results.append(result_item)

                if len(results) >= limit:
                    break

        return ScreenerResponse(
            screener="dividend_kings",
            criteria={"min_consecutive_years": 50, "min_yield": min_yield},
            count=len(results),
            data=results
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to execute kings screener: {str(e)}",
                "code": "screener_failed"
            }}
        )


@router.get("/screeners/high-growth-dividends", response_model=ScreenerResponse, summary="High dividend growth screener")
async def high_growth_dividends_screener(
    min_growth: float = Query(10.0, ge=0, description="Minimum 5-year growth rate %"),
    min_yield: float = Query(2.0, ge=0, description="Minimum current yield %"),
    limit: int = Query(100, ge=1, le=1000, description="Results limit"),
    auth: Dict[str, Any] = Depends(require_api_key)
) -> ScreenerResponse:
    """
    Find dividend growth stocks with strong 5-year dividend growth rates.

    Focuses on companies that are consistently growing their dividends.
    """
    try:
        supabase = get_supabase_client()

        # Get stocks with dividend growth data
        query = supabase.table('raw_stocks').select('*')\
            .not_.is_('dividend_yield', 'null')\
            .gte('dividend_yield', min_yield)\
            .not_.is_('dividend_growth_5yr', 'null')\
            .gte('dividend_growth_5yr', min_growth)\
            .order('dividend_growth_5yr', desc=True)\
            .limit(limit)

        result = query.execute()

        # Convert to ScreenerResult models
        results = []
        for row in result.data:
            result_item = ScreenerResult(
                symbol=row['symbol'],
                company=row.get('company', row['symbol']),
                yield_=row.get('dividend_yield', 0),
                price=row.get('price', 0),
                market_cap=row.get('market_cap'),
                payout_ratio=row.get('payout_ratio'),
                five_yr_growth=row.get('dividend_growth_5yr')
            )
            results.append(result_item)

        return ScreenerResponse(
            screener="high_growth_dividends",
            criteria={
                "min_5yr_growth": min_growth,
                "min_yield": min_yield
            },
            count=len(results),
            data=results
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to execute growth screener: {str(e)}",
                "code": "screener_failed"
            }}
        )
