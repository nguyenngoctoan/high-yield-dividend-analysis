"""
Analytics Router

Portfolio analytics and dividend projections.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from api.models.schemas import (
    PortfolioAnalysisRequest, PortfolioAnalysisResponse,
    PortfolioProjection, PortfolioPositionDetail
)
from supabase_helpers import get_supabase_client

router = APIRouter()


@router.post("/analytics/portfolio", response_model=PortfolioAnalysisResponse, summary="Analyze portfolio")
async def analyze_portfolio(
    request: PortfolioAnalysisRequest
) -> PortfolioAnalysisResponse:
    """
    Calculate portfolio dividend income projections.

    Analyzes a portfolio of dividend stocks and projects future income.
    Supports dividend reinvestment and annual contributions.
    """
    try:
        supabase = get_supabase_client()

        # Fetch current data for all symbols
        symbols = [pos.symbol.upper() for pos in request.positions]
        stocks_result = supabase.table('raw_stocks').select('*')\
            .in_('symbol', symbols)\
            .execute()

        # Create symbol lookup
        stocks_by_symbol = {row['symbol']: row for row in stocks_result.data}

        # Validate all symbols found
        missing = [s for s in symbols if s not in stocks_by_symbol]
        if missing:
            raise HTTPException(
                status_code=404,
                detail={"error": {
                    "type": "invalid_request_error",
                    "message": f"Symbols not found: {', '.join(missing)}",
                    "param": "positions",
                    "code": "symbols_not_found"
                }}
            )

        # Calculate current portfolio metrics
        total_value = 0.0
        total_annual_dividends = 0.0
        positions_detail = []

        for pos in request.positions:
            stock = stocks_by_symbol[pos.symbol.upper()]
            price = stock.get('price', 0.0)
            dividend_yield = stock.get('dividend_yield', 0.0) / 100.0  # Convert % to decimal
            annual_dividend = stock.get('dividend_amount', 0.0)

            position_value = pos.shares * price
            position_annual_dividends = pos.shares * annual_dividend

            total_value += position_value
            total_annual_dividends += position_annual_dividends

            detail = PortfolioPositionDetail(
                symbol=pos.symbol.upper(),
                shares=pos.shares,
                value=position_value,
                annual_dividends=position_annual_dividends,
                weight=(position_value / total_value * 100) if total_value > 0 else 0
            )
            positions_detail.append(detail)

        # Recalculate weights after total_value is known
        for detail in positions_detail:
            detail.weight = (detail.value / total_value * 100) if total_value > 0 else 0

        portfolio_yield = (total_annual_dividends / total_value * 100) if total_value > 0 else 0

        # Simple projections (can be enhanced with growth assumptions)
        projections = []
        projected_value = total_value
        projected_annual_income = total_annual_dividends

        for year in range(1, request.projection_years + 1):
            # Simple model: assume 3% dividend growth and 7% price appreciation
            dividend_growth = 1.03
            price_growth = 1.07

            projected_annual_income *= dividend_growth

            if request.reinvest_dividends:
                # Reinvest dividends quarterly (simplified)
                quarterly_dividend = projected_annual_income / 4
                for _ in range(4):
                    shares_bought = quarterly_dividend / (projected_value / sum(p.shares for p in request.positions))
                    projected_value += quarterly_dividend

            projected_value *= price_growth
            projected_value += request.annual_contribution

            projected_yield = (projected_annual_income / projected_value * 100) if projected_value > 0 else 0

            projection = PortfolioProjection(
                year=year,
                dividend_income=projected_annual_income,
                portfolio_value=projected_value,
                yield_=projected_yield
            )
            projections.append(projection)

        return PortfolioAnalysisResponse(
            current_value=total_value,
            annual_dividend_income=total_annual_dividends,
            portfolio_yield=portfolio_yield,
            projections=projections,
            by_symbol=positions_detail
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Failed to analyze portfolio: {str(e)}",
                "code": "analysis_failed"
            }}
        )
