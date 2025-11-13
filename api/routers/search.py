"""
Search Router

Search stocks by symbol, company name, or sector.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.models.schemas import SearchResponse, SearchResult, StockType
from supabase_helpers import get_supabase_client

router = APIRouter()


@router.get("/search", response_model=SearchResponse, summary="Search stocks")
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query"),
    type: Optional[StockType] = Query(None, description="Filter by type"),
    limit: int = Query(20, ge=1, le=100, description="Results limit")
) -> SearchResponse:
    """
    Search stocks by symbol, company name, or sector.

    Uses fuzzy matching to find relevant results.
    """
    try:
        supabase = get_supabase_client()

        query_upper = q.upper()
        query_pattern = f"%{q.upper()}%"

        # Use database-level ILIKE search for better performance
        # Search in symbol, company, and sector
        query = supabase.table('raw_stocks').select('*')

        # Apply ILIKE search on symbol, company, or sector
        # Note: Supabase/PostgREST uses "ilike" operator
        query = query.or_(f"symbol.ilike.{query_pattern},company.ilike.{query_pattern},sector.ilike.{query_pattern}")

        # Apply type filter if specified
        if type:
            query = query.eq('type', type.value)

        # Limit results
        result = query.limit(limit * 2).execute()

        # Score and sort results
        scored_results = []
        for row in result.data:
            symbol = (row.get('symbol') or '').upper()
            company = (row.get('company') or '').upper()
            sector = (row.get('sector') or '').upper()

            # Check for exact word match in company name
            company_words = company.split()
            has_exact_word = query_upper in company_words

            score = 0.0

            # Exact matches score highest
            if symbol == query_upper:
                score = 1.0
            elif company == query_upper:
                score = 0.98
            # Exact word match in company name
            elif has_exact_word:
                score = 0.95
            # Starts with queries
            elif symbol.startswith(query_upper):
                score = 0.9
            elif company.startswith(query_upper):
                score = 0.85
            # Contains queries
            elif query_upper in symbol:
                score = 0.7
            elif query_upper in company:
                score = 0.6
            elif query_upper in sector:
                score = 0.5

            if score > 0:
                scored_results.append((row, score))

        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Take top N results
        scored_results = scored_results[:limit]

        # Convert to SearchResult models
        search_results = []
        for row, score in scored_results:
            result_item = SearchResult(
                symbol=row['symbol'],
                company=row.get('company', 'Unknown'),
                exchange=row.get('exchange', 'UNKNOWN'),
                type=row.get('type', 'stock'),
                relevance=score
            )
            search_results.append(result_item)

        return SearchResponse(
            query=q,
            count=len(search_results),
            data=search_results
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {
                "type": "api_error",
                "message": f"Search failed: {str(e)}",
                "code": "search_failed"
            }}
        )
