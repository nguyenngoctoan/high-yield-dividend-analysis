"""
API Models and Schemas

Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class StockType(str, Enum):
    """Stock type enumeration."""
    STOCK = "stock"
    ETF = "etf"
    TRUST = "trust"


class Exchange(str, Enum):
    """Exchange enumeration."""
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    AMEX = "AMEX"
    TSX = "TSX"
    CBOE = "CBOE"
    BATS = "BATS"


class DividendFrequency(str, Enum):
    """Dividend payment frequency."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    IRREGULAR = "irregular"


class DividendEventType(str, Enum):
    """Dividend event types."""
    EX_DIVIDEND = "ex_dividend"
    PAYMENT = "payment"
    DECLARATION = "declaration"


class SortOrder(str, Enum):
    """Sort order."""
    ASC = "asc"
    DESC = "desc"


# ============================================================================
# Base Response Models
# ============================================================================

class APIError(BaseModel):
    """Standard error response."""
    type: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")
    param: Optional[str] = Field(None, description="Parameter that caused the error")


class ErrorResponse(BaseModel):
    """Error response wrapper."""
    error: APIError


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    has_more: bool = Field(..., description="Whether more results exist")
    cursor: Optional[str] = Field(None, description="Cursor for next page")
    total_count: Optional[int] = Field(None, description="Total count if available")


# ============================================================================
# Stock Models
# ============================================================================

class CompanyInfo(BaseModel):
    """Company information."""
    name: str
    description: Optional[str] = None
    ceo: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[int] = None
    employees: Optional[int] = None
    website: Optional[str] = None


class PricingInfo(BaseModel):
    """Current pricing information."""
    current: float = Field(..., description="Current price")
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None


class DividendInfo(BaseModel):
    """Dividend information."""
    yield_: float = Field(..., alias="yield", description="Annual dividend yield %")
    annual_amount: Optional[float] = None
    frequency: Optional[DividendFrequency] = None
    ex_dividend_date: Optional[date] = None
    payment_date: Optional[date] = None
    payout_ratio: Optional[float] = None
    five_yr_growth_rate: Optional[float] = Field(None, alias="5yr_growth_rate")

    class Config:
        populate_by_name = True


class Stock(BaseModel):
    """Stock resource."""
    id: str = Field(..., description="Unique stock identifier")
    object: str = Field(default="stock", description="Object type")
    symbol: str = Field(..., description="Stock symbol")
    exchange: str = Field(..., description="Exchange")
    type: Optional[StockType] = Field(None, description="Stock type")
    company: Optional[str] = Field(None, description="Company name")
    sector: Optional[str] = None
    price: Optional[float] = None
    dividend_yield: Optional[float] = None
    updated_at: datetime = Field(..., description="Last update timestamp")


class StockDetail(BaseModel):
    """Detailed stock information."""
    id: str
    object: str = "stock"
    symbol: str
    exchange: str
    type: Optional[StockType] = None
    company: Optional[CompanyInfo] = None
    pricing: Optional[PricingInfo] = None
    dividends: Optional[DividendInfo] = None
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StockListResponse(BaseModel):
    """List of stocks response."""
    object: str = "list"
    data: List[Stock]
    has_more: bool
    cursor: Optional[str] = None


# ============================================================================
# Dividend Models
# ============================================================================

class DividendEvent(BaseModel):
    """Dividend calendar event."""
    id: str
    object: str = "dividend_event"
    symbol: str
    event_type: DividendEventType
    event_date: date
    amount: float
    yield_: Optional[float] = Field(None, alias="yield")
    frequency: Optional[DividendFrequency] = None
    declaration_date: Optional[date] = None
    record_date: Optional[date] = None
    payment_date: Optional[date] = None
    company: Optional[str] = None

    class Config:
        populate_by_name = True


class DividendPayment(BaseModel):
    """Historical dividend payment."""
    id: str
    object: str = "dividend_payment"
    symbol: str
    payment_date: date
    ex_dividend_date: date
    amount: float
    type: str = "cash"
    declared_date: Optional[date] = None


class DividendGrowth(BaseModel):
    """Dividend growth metrics."""
    one_yr: Optional[float] = Field(None, alias="1yr")
    three_yr: Optional[float] = Field(None, alias="3yr")
    five_yr: Optional[float] = Field(None, alias="5yr")
    ten_yr: Optional[float] = Field(None, alias="10yr")

    class Config:
        populate_by_name = True


class DividendConsistency(BaseModel):
    """Dividend consistency metrics."""
    consecutive_years: int
    increases: int
    decreases: int
    suspensions: int


class DividendSummary(BaseModel):
    """Complete dividend summary for a stock."""
    object: str = "dividend_summary"
    symbol: str
    current: DividendInfo
    next_payment: Optional[DividendEvent] = None
    history: List[DividendPayment]
    growth: Optional[DividendGrowth] = None
    consistency: Optional[DividendConsistency] = None


class DividendListResponse(BaseModel):
    """List of dividend events."""
    object: str = "list"
    data: List[DividendEvent]
    has_more: bool
    cursor: Optional[str] = None


# ============================================================================
# Screener Models
# ============================================================================

class ScreenerResult(BaseModel):
    """Screener result item."""
    symbol: str
    company: str
    yield_: float = Field(..., alias="yield")
    price: float
    market_cap: Optional[int] = None
    payout_ratio: Optional[float] = None
    consecutive_years: Optional[int] = None
    five_yr_growth: Optional[float] = Field(None, alias="5yr_growth")

    class Config:
        populate_by_name = True


class ScreenerResponse(BaseModel):
    """Screener results response."""
    object: str = "screener_results"
    screener: str = Field(..., description="Screener name")
    criteria: Dict[str, Any] = Field(..., description="Applied criteria")
    count: int
    data: List[ScreenerResult]
    has_more: bool = False
    cursor: Optional[str] = None


# ============================================================================
# ETF Models
# ============================================================================

class ETFHolding(BaseModel):
    """ETF holding."""
    symbol: str
    company: str
    weight: float = Field(..., description="Position weight %")
    shares: Optional[int] = None
    market_value: Optional[float] = None
    sector: Optional[str] = None


class ETFHoldingsResponse(BaseModel):
    """ETF holdings response."""
    object: str = "etf_holdings"
    symbol: str
    name: str
    total_holdings: int
    aum: Optional[float] = None
    expense_ratio: Optional[float] = None
    updated_at: datetime
    holdings: List[ETFHolding]
    sector_allocation: Optional[Dict[str, float]] = None


class ETFStrategyDetails(BaseModel):
    """ETF strategy details."""
    type: str = Field(..., description="Strategy type")
    mechanism: str = Field(..., description="Income mechanism")
    risk_level: str = Field(..., description="Risk level")
    leveraged: bool
    inverse: bool


class ETFClassification(BaseModel):
    """ETF classification."""
    object: str = "etf_classification"
    symbol: str
    strategy: str
    underlying_stock: Optional[str] = None
    strategy_details: ETFStrategyDetails
    related_etfs: List[str] = []


# ============================================================================
# Price Models
# ============================================================================

class PriceBar(BaseModel):
    """Price bar (OHLCV)."""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: Optional[float] = None


class PriceHistoryResponse(BaseModel):
    """Price history response."""
    object: str = "price_history"
    symbol: str
    interval: str = "daily"
    data: List[PriceBar]
    has_more: bool = False
    cursor: Optional[str] = None


class PriceSnapshot(BaseModel):
    """Current price snapshot."""
    object: str = "price_snapshot"
    symbol: str
    price: float
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    timestamp: datetime
    market_status: str


# ============================================================================
# Analytics Models
# ============================================================================

class PortfolioPosition(BaseModel):
    """Portfolio position input."""
    symbol: str = Field(..., description="Stock symbol")
    shares: float = Field(..., gt=0, description="Number of shares")


class PortfolioAnalysisRequest(BaseModel):
    """Portfolio analysis request."""
    positions: List[PortfolioPosition] = Field(..., min_items=1)
    projection_years: int = Field(default=5, ge=1, le=30)
    reinvest_dividends: bool = Field(default=False)
    annual_contribution: float = Field(default=0, ge=0)


class PortfolioProjection(BaseModel):
    """Portfolio projection for a year."""
    year: int
    dividend_income: float
    portfolio_value: float
    yield_: float = Field(..., alias="yield")

    class Config:
        populate_by_name = True


class PortfolioPositionDetail(BaseModel):
    """Detailed position in portfolio."""
    symbol: str
    shares: float
    value: float
    annual_dividends: float
    weight: float = Field(..., description="Weight in portfolio %")


class PortfolioAnalysisResponse(BaseModel):
    """Portfolio analysis response."""
    object: str = "portfolio_analysis"
    current_value: float
    annual_dividend_income: float
    portfolio_yield: float
    projections: List[PortfolioProjection]
    by_symbol: List[PortfolioPositionDetail]


# ============================================================================
# Search Models
# ============================================================================

class SearchResult(BaseModel):
    """Search result item."""
    symbol: str
    company: str
    exchange: str
    type: Optional[StockType] = None
    relevance: float = Field(..., ge=0, le=1)


class SearchResponse(BaseModel):
    """Search results response."""
    object: str = "search_results"
    query: str
    count: int
    data: List[SearchResult]


# ============================================================================
# Utility Functions
# ============================================================================

def create_stock_id(symbol: str) -> str:
    """Create unique stock identifier."""
    return f"stock_{symbol.lower()}"


def create_dividend_event_id(symbol: str, date: date) -> str:
    """Create unique dividend event identifier."""
    return f"div_event_{symbol.lower()}_{date.strftime('%Y%m%d')}"


def create_dividend_payment_id(symbol: str, date: date) -> str:
    """Create unique dividend payment identifier."""
    return f"div_hist_{symbol.lower()}_{date.strftime('%Y%m%d')}"
