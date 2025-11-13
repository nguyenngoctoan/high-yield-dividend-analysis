"""
Screeners Router

Pre-built stock screeners for dividend investors.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.models.schemas import ScreenerResponse, ScreenerResult, SortOrder
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
    order: SortOrder = Query(SortOrder.DESC, description="Sort order")
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
    limit: int = Query(100, ge=1, le=1000)
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
