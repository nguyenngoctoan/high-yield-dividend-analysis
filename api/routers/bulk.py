"""
Bulk Operations Router

Endpoints for fetching data for multiple symbols in a single request.
Reduces API calls by 10-100x compared to individual requests.
"""

from fastapi import APIRouter, HTTPException, Request, Body, Query
from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
import logging

from api.models.schemas import Stock, DividendInfo, ErrorResponse
from api.middleware.tier_enforcer import TierEnforcer, get_tier_from_request
from supabase_helpers import get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/bulk/stocks",
    summary="Get multiple stocks",
    description="Fetch details for multiple stocks in a single request. "
                "Tier limits: Starter (50), Premium (200), Professional (1000), Enterprise (unlimited)"
)
async def get_stocks_bulk(
    request: Request,
    symbols: List[str] = Body(..., description="List of stock symbols", max_items=1000),
    expand: Optional[str] = Query(None, description="Comma-separated fields: company,dividends,prices")
) -> Dict[str, Any]:
    """
    Fetch details for multiple stocks in a single request.

    **Tier Limits**:
    - Starter: 50 symbols per request
    - Premium: 200 symbols per request
    - Professional: 1,000 symbols per request
    - Enterprise: Unlimited

    **Returns**:
    - `data`: Dictionary mapping symbol to stock data
    - `errors`: Dictionary mapping symbol to error message (if any)
    - `summary`: Summary statistics
    """
    try:
        # Get user's tier
        tier = await get_tier_from_request(request)

        # Check bulk limit
        max_symbols = await TierEnforcer.get_max_bulk_symbols(tier)

        if max_symbols == 0:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "bulk_requests_not_available",
                    "message": f"Bulk requests are not available on the {tier} tier. Upgrade to Starter or higher.",
                    "upgrade_url": "http://localhost:3000/pricing"
                }
            )

        if len(symbols) > max_symbols:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "bulk_limit_exceeded",
                    "message": f"Requested {len(symbols)} symbols, but {tier} tier allows maximum {max_symbols} symbols per request",
                    "max_symbols": max_symbols,
                    "requested_symbols": len(symbols),
                    "upgrade_url": "http://localhost:3000/pricing"
                }
            )

        # Filter accessible symbols
        accessible_symbols = await TierEnforcer.filter_accessible_symbols(tier, symbols)

        # Track results
        results = {}
        errors = {}
        inaccessible_symbols = set(symbols) - set(accessible_symbols)

        # Mark inaccessible symbols
        for symbol in inaccessible_symbols:
            errors[symbol] = f"Symbol not accessible on {tier} tier"

        # Fetch data for accessible symbols
        if accessible_symbols:
            supabase = get_supabase_client()

            # Normalize symbols to uppercase
            normalized_symbols = [s.upper() for s in accessible_symbols]

            # Fetch stocks
            result = supabase.table('raw_stocks').select('*').in_('symbol', normalized_symbols).execute()

            # Build results dictionary
            for row in result.data:
                symbol = row['symbol']
                results[symbol] = {
                    'symbol': symbol,
                    'exchange': row.get('exchange'),
                    'type': row.get('type'),
                    'company': row.get('company'),
                    'sector': row.get('sector'),
                    'price': row.get('price'),
                    'dividend_yield': row.get('dividend_yield'),
                    'updated_at': row.get('updated_at')
                }

                # Add expanded fields if requested
                if expand:
                    expand_fields = set(f.strip() for f in expand.split(','))

                    if 'company' in expand_fields:
                        results[symbol]['company_info'] = {
                            'name': row.get('company'),
                            'description': row.get('description'),
                            'sector': row.get('sector'),
                            'industry': row.get('industry'),
                            'market_cap': row.get('market_cap'),
                            'employees': row.get('employees'),
                            'website': row.get('website'),
                            'country': row.get('country')
                        }

                    if 'prices' in expand_fields:
                        results[symbol]['pricing_info'] = {
                            'current': row.get('price'),
                            'open': row.get('open'),
                            'high': row.get('high'),
                            'low': row.get('low'),
                            'volume': row.get('volume'),
                            'change': row.get('change'),
                            'change_percent': row.get('change_percent'),
                            'pe_ratio': row.get('pe_ratio')
                        }

            # Mark symbols not found in database
            found_symbols = set(row['symbol'] for row in result.data)
            for symbol in set(normalized_symbols) - found_symbols:
                errors[symbol] = "Symbol not found"

        return {
            "data": results,
            "errors": errors if errors else None,
            "summary": {
                "requested": len(symbols),
                "successful": len(results),
                "failed": len(errors),
                "tier": tier,
                "max_symbols": max_symbols
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk stocks request failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "api_error",
                "message": f"Failed to fetch stocks: {str(e)}",
                "code": "bulk_fetch_failed"
            }
        )


@router.post(
    "/bulk/dividends",
    summary="Get dividends for multiple stocks",
    description="Fetch dividend history for multiple stocks in a single request"
)
async def get_dividends_bulk(
    request: Request,
    symbols: List[str] = Body(..., description="List of stock symbols", max_items=1000),
    years: Optional[int] = Query(None, ge=1, le=100, description="Years of history (defaults to tier limit)")
) -> Dict[str, Any]:
    """
    Fetch dividend history for multiple stocks in a single request.

    **Historical Data Limits by Tier**:
    - Free: 1 year
    - Starter: 5 years
    - Premium: 30+ years
    - Professional/Enterprise: Full history

    **Returns**:
    - `data`: Dictionary mapping symbol to dividend data
    - `errors`: Dictionary mapping symbol to error message (if any)
    - `summary`: Summary statistics
    """
    try:
        # Get user's tier
        tier = await get_tier_from_request(request)

        # Check bulk limit
        max_symbols = await TierEnforcer.get_max_bulk_symbols(tier)

        if max_symbols == 0:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "bulk_requests_not_available",
                    "message": f"Bulk requests are not available on the {tier} tier",
                    "upgrade_url": "http://localhost:3000/pricing"
                }
            )

        if len(symbols) > max_symbols:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "bulk_limit_exceeded",
                    "message": f"Requested {len(symbols)} symbols, maximum is {max_symbols}",
                    "max_symbols": max_symbols,
                    "requested_symbols": len(symbols)
                }
            )

        # Get historical data limit
        max_years = await TierEnforcer.get_historical_data_years(tier)
        years_to_fetch = min(years or max_years, max_years)

        # Filter accessible symbols
        accessible_symbols = await TierEnforcer.filter_accessible_symbols(tier, symbols)

        # Track results
        results = {}
        errors = {}
        inaccessible_symbols = set(symbols) - set(accessible_symbols)

        for symbol in inaccessible_symbols:
            errors[symbol] = f"Symbol not accessible on {tier} tier"

        # Fetch dividend data
        if accessible_symbols:
            supabase = get_supabase_client()
            normalized_symbols = [s.upper() for s in accessible_symbols]

            # Calculate date range
            cutoff_date = (datetime.now() - timedelta(days=years_to_fetch * 365)).date()

            # Fetch dividends
            result = supabase.table('dividend_history').select('*') \
                .in_('symbol', normalized_symbols) \
                .gte('ex_date', cutoff_date.isoformat()) \
                .order('ex_date', desc=True) \
                .execute()

            # Group by symbol
            for row in result.data:
                symbol = row['symbol']
                if symbol not in results:
                    results[symbol] = []

                results[symbol].append({
                    'ex_date': row.get('ex_date'),
                    'payment_date': row.get('payment_date'),
                    'record_date': row.get('record_date'),
                    'amount': row.get('amount'),
                    'currency': row.get('currency', 'USD')
                })

            # Mark symbols with no dividends
            symbols_with_dividends = set(results.keys())
            for symbol in set(normalized_symbols) - symbols_with_dividends:
                errors[symbol] = "No dividend history found"

        return {
            "data": results,
            "errors": errors if errors else None,
            "summary": {
                "requested": len(symbols),
                "successful": len(results),
                "failed": len(errors),
                "years_fetched": years_to_fetch,
                "tier": tier,
                "max_years": max_years
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk dividends request failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "api_error",
                "message": f"Failed to fetch dividends: {str(e)}",
                "code": "bulk_fetch_failed"
            }
        )


@router.post(
    "/bulk/prices",
    summary="Get price history for multiple stocks",
    description="Fetch price history for multiple stocks in a single request"
)
async def get_prices_bulk(
    request: Request,
    symbols: List[str] = Body(..., description="List of stock symbols", max_items=1000),
    range: Optional[str] = Query('1m', description="Time range: 1d, 5d, 1m, 3m, 6m, ytd, 1y, 2y, 5y, max"),
    from_date: Optional[date] = Query(None, description="Start date (overrides range)"),
    to_date: Optional[date] = Query(None, description="End date")
) -> Dict[str, Any]:
    """
    Fetch price history for multiple stocks in a single request.

    **Price Frequency by Tier**:
    - Free: End-of-day only
    - Starter: Hourly + EOD
    - Premium: 15-minute + EOD
    - Professional: 1-minute + EOD
    - Enterprise: Real-time

    **Returns**:
    - `data`: Dictionary mapping symbol to price data
    - `errors`: Dictionary mapping symbol to error message (if any)
    - `summary`: Summary statistics
    """
    try:
        # Get user's tier
        tier = await get_tier_from_request(request)

        # Check bulk limit
        max_symbols = await TierEnforcer.get_max_bulk_symbols(tier)

        if max_symbols == 0:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "bulk_requests_not_available",
                    "message": f"Bulk requests are not available on the {tier} tier",
                    "upgrade_url": "http://localhost:3000/pricing"
                }
            )

        if len(symbols) > max_symbols:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "bulk_limit_exceeded",
                    "message": f"Requested {len(symbols)} symbols, maximum is {max_symbols}",
                    "max_symbols": max_symbols,
                    "requested_symbols": len(symbols)
                }
            )

        # Filter accessible symbols
        accessible_symbols = await TierEnforcer.filter_accessible_symbols(tier, symbols)

        # Track results
        results = {}
        errors = {}
        inaccessible_symbols = set(symbols) - set(accessible_symbols)

        for symbol in inaccessible_symbols:
            errors[symbol] = f"Symbol not accessible on {tier} tier"

        # Calculate date range
        if from_date and to_date:
            start_date = from_date
            end_date = to_date
        else:
            # Parse range parameter
            range_map = {
                '1d': 1, '5d': 5, '1m': 30, '3m': 90, '6m': 180,
                'ytd': (datetime.now() - datetime(datetime.now().year, 1, 1)).days,
                '1y': 365, '2y': 730, '5y': 1825, 'max': 10000
            }
            days = range_map.get(range, 30)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

        # Fetch price data
        if accessible_symbols:
            supabase = get_supabase_client()
            normalized_symbols = [s.upper() for s in accessible_symbols]

            # Fetch prices
            result = supabase.table('stock_prices').select('*') \
                .in_('symbol', normalized_symbols) \
                .gte('date', start_date.isoformat()) \
                .lte('date', end_date.isoformat()) \
                .order('date', desc=True) \
                .execute()

            # Group by symbol
            for row in result.data:
                symbol = row['symbol']
                if symbol not in results:
                    results[symbol] = []

                results[symbol].append({
                    'date': row.get('date'),
                    'open': row.get('open'),
                    'high': row.get('high'),
                    'low': row.get('low'),
                    'close': row.get('close'),
                    'adjusted_close': row.get('adjusted_close'),
                    'volume': row.get('volume'),
                    'vwap': row.get('vwap')
                })

            # Mark symbols with no prices
            symbols_with_prices = set(results.keys())
            for symbol in set(normalized_symbols) - symbols_with_prices:
                errors[symbol] = "No price history found"

        return {
            "data": results,
            "errors": errors if errors else None,
            "summary": {
                "requested": len(symbols),
                "successful": len(results),
                "failed": len(errors),
                "date_range": {
                    "from": start_date.isoformat(),
                    "to": end_date.isoformat()
                },
                "tier": tier
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk prices request failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "api_error",
                "message": f"Failed to fetch prices: {str(e)}",
                "code": "bulk_fetch_failed"
            }
        )


@router.post(
    "/bulk/latest",
    summary="Get latest prices for multiple stocks",
    description="Fetch the latest price snapshot for multiple stocks"
)
async def get_latest_prices_bulk(
    request: Request,
    symbols: List[str] = Body(..., description="List of stock symbols", max_items=1000)
) -> Dict[str, Any]:
    """
    Fetch latest price snapshot for multiple stocks in a single request.

    This is the most efficient endpoint for getting current prices for a watchlist.

    **Returns**:
    - `data`: Dictionary mapping symbol to latest price data
    - `errors`: Dictionary mapping symbol to error message (if any)
    - `summary`: Summary statistics
    """
    try:
        # Get user's tier
        tier = await get_tier_from_request(request)

        # Check bulk limit
        max_symbols = await TierEnforcer.get_max_bulk_symbols(tier)

        if max_symbols == 0:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "bulk_requests_not_available",
                    "message": f"Bulk requests are not available on the {tier} tier",
                    "upgrade_url": "http://localhost:3000/pricing"
                }
            )

        if len(symbols) > max_symbols:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "bulk_limit_exceeded",
                    "message": f"Requested {len(symbols)} symbols, maximum is {max_symbols}",
                    "max_symbols": max_symbols
                }
            )

        # Filter accessible symbols
        accessible_symbols = await TierEnforcer.filter_accessible_symbols(tier, symbols)

        # Track results
        results = {}
        errors = {}
        inaccessible_symbols = set(symbols) - set(accessible_symbols)

        for symbol in inaccessible_symbols:
            errors[symbol] = f"Symbol not accessible on {tier} tier"

        # Fetch latest prices from raw_stocks table
        if accessible_symbols:
            supabase = get_supabase_client()
            normalized_symbols = [s.upper() for s in accessible_symbols]

            result = supabase.table('raw_stocks').select(
                'symbol, price, open, high, low, volume, change, change_percent, '
                'dividend_yield, pe_ratio, market_cap, updated_at'
            ).in_('symbol', normalized_symbols).execute()

            for row in result.data:
                symbol = row['symbol']
                results[symbol] = {
                    'symbol': symbol,
                    'price': row.get('price'),
                    'open': row.get('open'),
                    'high': row.get('high'),
                    'low': row.get('low'),
                    'volume': row.get('volume'),
                    'change': row.get('change'),
                    'change_percent': row.get('change_percent'),
                    'dividend_yield': row.get('dividend_yield'),
                    'pe_ratio': row.get('pe_ratio'),
                    'market_cap': row.get('market_cap'),
                    'updated_at': row.get('updated_at')
                }

            # Mark symbols not found
            found_symbols = set(row['symbol'] for row in result.data)
            for symbol in set(normalized_symbols) - found_symbols:
                errors[symbol] = "Symbol not found"

        return {
            "data": results,
            "errors": errors if errors else None,
            "summary": {
                "requested": len(symbols),
                "successful": len(results),
                "failed": len(errors),
                "tier": tier,
                "max_symbols": max_symbols
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk latest prices request failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "api_error",
                "message": f"Failed to fetch latest prices: {str(e)}",
                "code": "bulk_fetch_failed"
            }
        )
