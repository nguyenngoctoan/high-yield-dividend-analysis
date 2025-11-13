"""
ETFs Router

ETF holdings and classification endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
from datetime import datetime

from api.models.schemas import (
    ETFHoldingsResponse, ETFHolding, ETFClassification,
    ETFStrategyDetails
)
from supabase_helpers import get_supabase_client

router = APIRouter()


@router.get("/etfs/{symbol}/holdings", response_model=ETFHoldingsResponse, summary="Get ETF holdings")
async def get_etf_holdings(
    symbol: str = Path(..., description="ETF symbol"),
    limit: int = Query(50, ge=1, le=500, description="Number of holdings"),
    include_weights: bool = Query(True, description="Include position weights")
) -> ETFHoldingsResponse:
    """
    Get ETF portfolio holdings breakdown.

    Returns top holdings with weights and sector allocation.
    """
    try:
        supabase = get_supabase_client()

        # Fetch ETF info
        etf_result = supabase.table('raw_stocks').select('*')\
            .eq('symbol', symbol.upper())\
            .eq('type', 'etf')\
            .execute()

        if not etf_result.data:
            raise HTTPException(
                status_code=404,
                detail={"error": {
                    "type": "resource_not_found_error",
                    "message": f"ETF '{symbol}' not found",
                    "param": "symbol",
                    "code": "etf_not_found"
                }}
            )

        etf = etf_result.data[0]

        # Fetch holdings
        holdings_result = supabase.table('raw_etf_holdings').select('*')\
            .eq('etf_symbol', symbol.upper())\
            .order('weight', desc=True)\
            .limit(limit)\
            .execute()

        # Convert to ETFHolding models
        holdings = []
        sector_allocation = {}

        for row in holdings_result.data:
            holding = ETFHolding(
                symbol=row['holding_symbol'],
                company=row.get('company', 'Unknown'),
                weight=row.get('weight', 0.0),
                shares=row.get('shares'),
                market_value=row.get('market_value'),
                sector=row.get('sector')
            )
            holdings.append(holding)

            # Aggregate sector allocation
            if row.get('sector') and row.get('weight'):
                sector_allocation[row['sector']] = \
                    sector_allocation.get(row['sector'], 0) + row['weight']

        # Get total holdings count
        total_count_result = supabase.table('raw_etf_holdings').select('*', count='exact')\
            .eq('etf_symbol', symbol.upper())\
            .execute()

        return ETFHoldingsResponse(
            symbol=symbol.upper(),
            name=etf.get('company', symbol.upper()),
            total_holdings=total_count_result.count or len(holdings),
            aum=etf.get('aum'),
            expense_ratio=etf.get('expense_ratio'),
            updated_at=etf.get('updated_at', datetime.now()),
            holdings=holdings,
            sector_allocation=sector_allocation if sector_allocation else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to fetch ETF holdings: {str(e)}",
                "code": "fetch_failed"
            }}
        )


@router.get("/etfs/classify/{symbol}", response_model=ETFClassification, summary="Classify ETF strategy")
async def classify_etf(
    symbol: str = Path(..., description="ETF symbol")
) -> ETFClassification:
    """
    Identify ETF investment strategy and related stocks.

    Analyzes ETF to determine strategy type and underlying assets.
    """
    try:
        from lib.processors.etf_classifier import ETFClassifier

        classifier = ETFClassifier()

        # Fetch ETF data
        supabase = get_supabase_client()
        etf_result = supabase.table('raw_stocks').select('*')\
            .eq('symbol', symbol.upper())\
            .eq('type', 'etf')\
            .execute()

        if not etf_result.data:
            raise HTTPException(
                status_code=404,
                detail={"error": {
                    "type": "resource_not_found_error",
                    "message": f"ETF '{symbol}' not found",
                    "param": "symbol",
                    "code": "etf_not_found"
                }}
            )

        etf = etf_result.data[0]

        # Classify strategy
        classification = classifier.classify_etf(
            symbol=symbol.upper(),
            name=etf.get('company', ''),
            description=etf.get('description', '')
        )

        # Build strategy details
        strategy_details = ETFStrategyDetails(
            type="income" if "yield" in classification.get('strategy', '').lower() else "growth",
            mechanism=classification.get('mechanism', 'unknown'),
            risk_level=classification.get('risk_level', 'unknown'),
            leveraged=classification.get('leveraged', False),
            inverse=classification.get('inverse', False)
        )

        return ETFClassification(
            symbol=symbol.upper(),
            strategy=classification.get('strategy', 'Unknown'),
            underlying_stock=classification.get('related_stock'),
            strategy_details=strategy_details,
            related_etfs=classification.get('related_etfs', [])
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to classify ETF: {str(e)}",
                "code": "classification_failed"
            }}
        )
