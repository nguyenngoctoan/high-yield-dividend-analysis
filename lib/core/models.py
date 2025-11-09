"""
Data Models Module

Defines data classes and models for stock data, dividends, company information,
and other financial entities used throughout the application.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal


@dataclass
class StockSymbol:
    """Represents a stock symbol with basic metadata."""

    symbol: str
    name: str
    exchange: str
    exchange_short_name: Optional[str] = None
    type: Optional[str] = None  # 'stock', 'etf', etc.
    is_etf: bool = False
    currency: Optional[str] = None
    country: Optional[str] = None
    ipo_date: Optional[date] = None

    def __post_init__(self):
        """Normalize symbol and determine if it's an ETF."""
        self.symbol = self.symbol.upper()
        if self.type and self.type.lower() in ['etf', 'exchange traded fund']:
            self.is_etf = True

    @property
    def is_us_exchange(self) -> bool:
        """Check if symbol is on a US exchange."""
        us_exchanges = ['NYSE', 'NASDAQ', 'AMEX', 'BATS', 'CBOE', 'OTCM', 'OTCX']
        return self.exchange_short_name in us_exchanges if self.exchange_short_name else False

    @property
    def is_canadian_exchange(self) -> bool:
        """Check if symbol is on a Canadian exchange."""
        canadian_exchanges = ['TSX', 'TSXV', 'CSE', 'TSE']
        return self.exchange_short_name in canadian_exchanges if self.exchange_short_name else False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'exchange': self.exchange,
            'exchange_short_name': self.exchange_short_name,
            'type': self.type,
            'is_etf': self.is_etf,
            'currency': self.currency,
            'country': self.country,
            'ipo_date': self.ipo_date.isoformat() if self.ipo_date else None
        }


@dataclass
class StockPrice:
    """Represents a stock price record."""

    symbol: str
    date: date
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adj_close: Optional[Decimal] = None
    volume: Optional[int] = None
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    vwap: Optional[Decimal] = None
    label: Optional[str] = None
    change_over_time: Optional[Decimal] = None
    aum: Optional[int] = None  # Assets Under Management (for ETFs)
    iv: Optional[Decimal] = None  # Implied Volatility

    def __post_init__(self):
        """Validate and normalize data."""
        self.symbol = self.symbol.upper()
        # Convert string date to date object if needed
        if isinstance(self.date, str):
            self.date = datetime.strptime(self.date, '%Y-%m-%d').date()

    @property
    def is_valid(self) -> bool:
        """Check if price data is valid."""
        return (
            self.close is not None and
            self.close > 0 and
            self.volume is not None and
            self.volume > 0
        )

    @property
    def price(self) -> Optional[Decimal]:
        """Get the primary price (close price)."""
        return self.close

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            'symbol': self.symbol,
            'date': self.date.isoformat(),
            'price': float(self.close) if self.close else None,  # price column = close price
            'open': float(self.open) if self.open else None,
            'high': float(self.high) if self.high else None,
            'low': float(self.low) if self.low else None,
            'close': float(self.close) if self.close else None,
            'adj_close': float(self.adj_close) if self.adj_close else None,
            'volume': self.volume,
            'change': float(self.change) if self.change else None,
            'change_percent': float(self.change_percent) if self.change_percent else None,
            'aum': self.aum,
            'iv': float(self.iv) if self.iv else None
        }


@dataclass
class Dividend:
    """Represents a dividend payment record."""

    symbol: str
    date: date
    amount: Decimal
    adj_dividend: Optional[Decimal] = None
    record_date: Optional[date] = None
    payment_date: Optional[date] = None
    declaration_date: Optional[date] = None
    label: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize data."""
        self.symbol = self.symbol.upper()
        # Convert string dates to date objects if needed
        if isinstance(self.date, str):
            self.date = datetime.strptime(self.date, '%Y-%m-%d').date()
        if isinstance(self.record_date, str):
            self.record_date = datetime.strptime(self.record_date, '%Y-%m-%d').date()
        if isinstance(self.payment_date, str):
            self.payment_date = datetime.strptime(self.payment_date, '%Y-%m-%d').date()
        if isinstance(self.declaration_date, str):
            self.declaration_date = datetime.strptime(self.declaration_date, '%Y-%m-%d').date()

    @property
    def is_valid(self) -> bool:
        """Check if dividend data is valid."""
        return self.amount is not None and self.amount > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            'symbol': self.symbol,
            'ex_date': self.date.isoformat(),
            'amount': float(self.amount),
            'record_date': self.record_date.isoformat() if self.record_date else None,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'declaration_date': self.declaration_date.isoformat() if self.declaration_date else None
        }


@dataclass
class CompanyInfo:
    """Represents company/ETF information."""

    symbol: str
    company_name: Optional[str] = None
    description: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    ceo: Optional[str] = None
    employees: Optional[int] = None
    market_cap: Optional[Decimal] = None
    # ETF-specific fields
    fund_family: Optional[str] = None  # For ETFs
    expense_ratio: Optional[Decimal] = None
    aum: Optional[Decimal] = None  # Assets Under Management (for ETFs)
    inception_date: Optional[date] = None
    # Additional metadata
    is_etf: bool = False
    exchange: Optional[str] = None
    currency: Optional[str] = None
    country: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize data."""
        self.symbol = self.symbol.upper()
        if isinstance(self.inception_date, str):
            self.inception_date = datetime.strptime(self.inception_date, '%Y-%m-%d').date()

    @property
    def display_name(self) -> str:
        """Get display name (company name or fund family)."""
        if self.is_etf and self.fund_family:
            return self.fund_family
        return self.company_name or self.symbol

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            'symbol': self.symbol,
            'company': self.company_name,  # Maps company_name to 'company' column
            'description': self.description,
            'sector': self.sector,
            # Note: The following fields don't exist in raw_stocks table and will be ignored:
            # industry, website, ceo, employees, market_cap, fund_family, inception_date,
            # is_etf, currency, country
            'expense_ratio': float(self.expense_ratio) if self.expense_ratio else None,
            'aum': float(self.aum) if self.aum else None,
            'exchange': self.exchange
        }


@dataclass
class StockSplit:
    """Represents a stock split record."""

    symbol: str
    date: date
    numerator: Decimal
    denominator: Decimal
    split_ratio: Optional[str] = None
    label: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize data."""
        self.symbol = self.symbol.upper()
        if isinstance(self.date, str):
            self.date = datetime.strptime(self.date, '%Y-%m-%d').date()
        # Generate split ratio if not provided
        if not self.split_ratio:
            self.split_ratio = f"{self.numerator}:{self.denominator}"

    @property
    def multiplier(self) -> Decimal:
        """Get the split multiplier."""
        return self.numerator / self.denominator

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            'symbol': self.symbol,
            'date': self.date.isoformat(),
            'numerator': float(self.numerator),
            'denominator': float(self.denominator),
            'split_ratio': self.split_ratio,
            'label': self.label
        }


@dataclass
class ValidationResult:
    """Represents the result of symbol validation."""

    symbol: str
    is_valid: bool
    has_recent_price: bool = False
    has_dividend_history: bool = False
    last_price_date: Optional[date] = None
    last_dividend_date: Optional[date] = None
    exclusion_reason: Optional[str] = None
    validation_messages: List[str] = field(default_factory=list)

    def add_message(self, message: str):
        """Add a validation message."""
        self.validation_messages.append(message)

    @property
    def should_exclude(self) -> bool:
        """Check if symbol should be excluded."""
        return not self.is_valid

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'is_valid': self.is_valid,
            'has_recent_price': self.has_recent_price,
            'has_dividend_history': self.has_dividend_history,
            'last_price_date': self.last_price_date.isoformat() if self.last_price_date else None,
            'last_dividend_date': self.last_dividend_date.isoformat() if self.last_dividend_date else None,
            'exclusion_reason': self.exclusion_reason,
            'validation_messages': self.validation_messages
        }


@dataclass
class ProcessingStats:
    """Statistics for batch processing operations."""

    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)

    def start(self):
        """Mark processing start time."""
        self.start_time = datetime.now()

    def complete(self):
        """Mark processing completion time."""
        self.end_time = datetime.now()

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get processing duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_processed == 0:
            return 0.0
        return (self.successful / self.total_processed) * 100

    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_processed': self.total_processed,
            'successful': self.successful,
            'failed': self.failed,
            'skipped': self.skipped,
            'success_rate': f"{self.success_rate:.2f}%",
            'duration_seconds': self.duration_seconds,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error_count': len(self.errors)
        }


# Export all models
__all__ = [
    'StockSymbol',
    'StockPrice',
    'Dividend',
    'CompanyInfo',
    'StockSplit',
    'ValidationResult',
    'ProcessingStats'
]
