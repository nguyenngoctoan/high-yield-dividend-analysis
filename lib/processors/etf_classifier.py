"""
ETF Classifier Module

Automatically classifies ETFs by investment strategy and related stocks.
Uses pattern matching on ETF names to identify strategy types.
Based on classify_all_etfs.sql logic converted to Python.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple

from lib.core.models import ProcessingStats
from supabase_helpers import supabase_select, supabase_batch_upsert

logger = logging.getLogger(__name__)


class ETFClassifier:
    """
    Classifies ETFs into investment strategies and identifies related stocks.

    Features:
    - Pattern-based classification using ETF names
    - 80+ distinct strategy types
    - Related stock/index identification
    - Batch processing
    - Statistics tracking
    """

    # Classification rules: (pattern, investment_strategy, related_stock)
    # Order matters - more specific patterns should come first
    CLASSIFICATION_RULES = [
        # =====================================================================
        # EQUITY INDEX ETFs
        # =====================================================================
        (r's&p\s*500', 'Broad Market Index', 'SPY'),
        (r'nasdaq[\s-]?100', 'Tech-Heavy Index', 'QQQ'),
        (r'russell\s*2000', 'Small Cap Index', 'IWM'),
        (r'(dow\s*jones|dow\s*30|djia)', 'Blue Chip Index', 'DIA'),
        (r'(total\s*market|total\s*stock)', 'Total Market', 'VTI'),

        # =====================================================================
        # SECTOR & INDUSTRY ETFs
        # =====================================================================
        (r'(tech(?!.*bio)|information\s*technology|software)', 'Sector - Technology', 'XLK'),
        (r'(health|medical|pharma)', 'Sector - Healthcare', 'XLV'),
        (r'(financial|bank|insurance)', 'Sector - Financials', 'XLF'),
        (r'(energy|oil|gas|petroleum)(?!.*storage)', 'Sector - Energy', 'XLE'),
        (r'consumer\s*discretionary|consumer\s*cyclical', 'Sector - Consumer Discretionary', 'XLY'),
        (r'consumer\s*staples|consumer\s*defensive', 'Sector - Consumer Staples', 'XLP'),
        (r'consumer', 'Sector - Consumer', 'XLY'),
        (r'(real\s*estate|reit|property)', 'Sector - Real Estate', 'XLRE'),
        (r'utilit', 'Sector - Utilities', 'XLU'),
        (r'(industrial|manufacturing)', 'Sector - Industrials', 'XLI'),
        (r'(material|mining|metal)(?!.*rare\s*earth)', 'Sector - Materials', 'XLB'),
        (r'(communication|media|telecom)', 'Sector - Communication Services', 'XLC'),
        (r'(semiconductor|chip)', 'Industry - Semiconductors', 'SMH'),
        (r'(biotech|genomic)', 'Industry - Biotechnology', 'IBB'),
        (r'(aerospace|defense)', 'Industry - Aerospace & Defense', 'ITA'),

        # =====================================================================
        # COMMODITIES
        # =====================================================================
        (r'gold', 'Commodity - Precious Metals', 'GLD'),
        (r'silver', 'Commodity - Precious Metals', 'SLV'),
        (r'precious\s*metal', 'Commodity - Precious Metals', 'Multiple (Precious Metals)'),

        # =====================================================================
        # INTERNATIONAL / GEOGRAPHIC ETFs
        # =====================================================================
        (r'(eafe|developed\s*market|international\s*developed)', 'International Developed', 'EFA'),
        (r'emerging\s*market', 'Emerging Markets', 'EEM'),
        (r'(china|chinese)', 'Geographic - China', 'FXI'),
        (r'(europe|euro\s*stoxx)(?!.*emerging)', 'Geographic - Europe', 'VGK'),
        (r'(japan|nikkei)', 'Geographic - Japan', 'EWJ'),
        (r'(asia|pacific|korea|india)', 'Geographic - Asia Pacific', 'Multiple (Asia)'),
        (r'(canada|canadian|tsx)(?!.*bank)(?!.*covered\s*call)', 'Geographic - Canada', 'EWC'),
        (r'(latin\s*america|brazil|mexico|colombia)', 'Geographic - Latin America', 'Multiple (LatAm)'),
        (r'(middle\s*east|israel|saudi)', 'Geographic - Middle East', 'Multiple (Middle East)'),

        # =====================================================================
        # FIXED INCOME / BOND ETFs
        # =====================================================================
        (r'treasury.*(short[\s-]term|1[\s-]3)', 'Bonds - Short-Term Treasury', 'SHY'),
        (r'treasury.*(intermediate|7[\s-]10)', 'Bonds - Intermediate Treasury', 'IEF'),
        (r'treasury.*(long|20\+|20\s*year)', 'Bonds - Long-Term Treasury', 'TLT'),
        (r'treasury', 'Bonds - Treasury', 'IEF'),
        (r'(corporate\s*bond|investment\s*grade)', 'Bonds - Corporate', 'LQD'),
        (r'(high\s*yield|junk\s*bond)', 'Bonds - High Yield', 'HYG'),
        (r'(municipal|muni\s*bond)', 'Bonds - Municipal', 'MUB'),
        (r'(aggregate\s*bond|total\s*bond)', 'Bonds - Aggregate', 'AGG'),
        (r'(tips|inflation[\s-]linked|inflation[\s-]protected)', 'Bonds - Inflation Protected', 'TIP'),

        # =====================================================================
        # STYLE / FACTOR ETFs
        # =====================================================================
        (r'growth(?!.*dividend)', 'Factor - Growth', 'IWF'),
        (r'value', 'Factor - Value', 'IWD'),
        (r'(dividend|income)(?!.*covered\s*call)(?!.*option)', 'Factor - Dividend', 'VYM'),
        (r'momentum', 'Factor - Momentum', 'MTUM'),
        (r'quality', 'Factor - Quality', 'QUAL'),
        (r'(low\s*volatility|minimum\s*volatility)', 'Factor - Low Volatility', 'USMV'),
        (r'multi[\s-]factor', 'Factor - Multi-Factor', 'Multiple (Factors)'),

        # =====================================================================
        # ESG / THEMATIC ETFs
        # =====================================================================
        (r'(esg|sustainable|responsible)', 'Thematic - ESG', 'Multiple (ESG)'),
        (r'(clean\s*energy|renewable|solar|wind|climate)', 'Thematic - Clean Energy', 'ICLN'),
        (r'(artificial\s*intelligence|\sai\s|machine\s*learning)', 'Thematic - AI', 'Multiple (AI)'),
        (r'(robot|automation)', 'Thematic - Robotics', 'ROBO'),
        (r'(cloud|saas)', 'Thematic - Cloud Computing', 'SKYY'),
        (r'(cyber|security)', 'Thematic - Cybersecurity', 'HACK'),
        (r'(electric\s*vehicle|autonomous)', 'Thematic - Electric Vehicles', 'DRIV'),
        (r'(metaverse|gaming|esports)', 'Thematic - Metaverse/Gaming', 'Multiple (Gaming)'),

        # =====================================================================
        # CRYPTO / BLOCKCHAIN ETFs
        # =====================================================================
        (r'(bitcoin|btc)', 'Crypto - Bitcoin', 'BTC'),
        (r'(ethereum|ether)', 'Crypto - Ethereum', 'ETH'),
        (r'(blockchain|crypto)', 'Crypto - Blockchain', 'Multiple (Blockchain)'),

        # =====================================================================
        # LEVERAGED / INVERSE ETFs
        # =====================================================================
        (r'(3x|ultra\s*pro|triple)', 'Leveraged - 3x', lambda name: _get_leverage_related(name)),
        (r'(2x|ultra|double)', 'Leveraged - 2x', lambda name: _get_leverage_related(name)),
        (r'leveraged', 'Leveraged', lambda name: _get_leverage_related(name)),
        (r'(inverse|short|bear)(?!.*short[\s-]term)(?!.*short[\s-]duration)', 'Inverse/Short', lambda name: _get_leverage_related(name)),

        # =====================================================================
        # ALTERNATIVE WEIGHTING
        # =====================================================================
        (r'equal\s*weight', 'Equal Weight', lambda name: 'RSP' if 's&p 500' in name.lower() else 'Multiple'),

        # =====================================================================
        # BUFFER / DEFINED OUTCOME ETFs
        # =====================================================================
        (r'(buffer|defined\s*outcome|target\s*income)', 'Buffered/Defined Outcome', 'SPY'),
    ]

    def __init__(self):
        """Initialize ETF classifier."""
        self.stats = ProcessingStats()

    def classify_etf(self, symbol: str, name: str) -> Optional[Tuple[str, str]]:
        """
        Classify a single ETF based on its name.

        Args:
            symbol: ETF symbol
            name: ETF name

        Returns:
            Tuple of (investment_strategy, related_stock) or None if not classifiable
        """
        if not name:
            logger.debug(f"⚠️  {symbol}: No name provided")
            return None

        # Check if it's an ETF (name contains 'ETF', 'FUND', or known ETF patterns)
        name_lower = name.lower()
        if 'etf' not in name_lower and 'fund' not in name_lower:
            # Check for known ETF symbol patterns (ends with common ETF suffixes)
            if not (symbol.endswith('Y') or symbol.endswith('X') or len(symbol) == 3):
                logger.debug(f"⚠️  {symbol}: Name doesn't suggest it's an ETF")
                return None

        # Try each classification rule
        for pattern, strategy, related in self.CLASSIFICATION_RULES:
            if re.search(pattern, name_lower, re.IGNORECASE):
                # Handle callable related_stock (for complex logic)
                if callable(related):
                    related_stock = related(name_lower)
                else:
                    related_stock = related

                logger.debug(f"✅ {symbol}: Matched pattern '{pattern}' -> {strategy} ({related_stock})")
                return (strategy, related_stock)

        # Fallback: if name contains 'ETF' or 'FUND', classify as generic
        if 'etf' in name_lower or 'fund' in name_lower:
            logger.debug(f"✅ {symbol}: Generic ETF classification")
            return ('Other ETF', 'Multiple')

        logger.debug(f"❌ {symbol}: Could not classify")
        return None

    def classify_and_store(self, symbol: str, name: str) -> bool:
        """
        Classify and store ETF classification.

        Args:
            symbol: ETF symbol
            name: ETF name

        Returns:
            True if successfully classified and stored
        """
        self.stats.total_processed += 1

        try:
            classification = self.classify_etf(symbol, name)

            if not classification:
                logger.debug(f"⚠️  {symbol}: Not classifiable")
                self.stats.skipped += 1
                return False

            strategy, related_stock = classification

            # Update database
            from supabase_helpers import supabase_update
            result = supabase_update(
                'raw_stocks',
                {'symbol': symbol},
                {
                    'investment_strategy': strategy,
                    'related_stock': related_stock
                }
            )

            if result:
                logger.info(f"✅ {symbol}: {strategy} -> {related_stock}")
                self.stats.successful += 1
                return True
            else:
                logger.error(f"❌ {symbol}: Failed to update database")
                self.stats.failed += 1
                return False

        except Exception as e:
            logger.error(f"❌ {symbol}: Classification error - {e}")
            self.stats.failed += 1
            self.stats.add_error(f"{symbol}: {str(e)}")
            return False

    def classify_batch(self, etf_records: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Classify multiple ETFs in batch.

        Args:
            etf_records: List of dicts with 'symbol' and 'name' keys

        Returns:
            Dictionary mapping symbol -> success status
        """
        self.stats.start()
        logger.info(f"🏷️  Classifying {len(etf_records)} ETFs")

        results = {}

        for record in etf_records:
            symbol = record['symbol']
            name = record.get('name', '')
            success = self.classify_and_store(symbol, name)
            results[symbol] = success

        self.stats.complete()

        logger.info(
            f"🎉 Classification complete: {self.stats.successful} classified, "
            f"{self.stats.skipped} skipped, {self.stats.failed} failed, "
            f"{len(etf_records)} total in {self.stats.duration_seconds:.2f}s"
        )

        return results

    def classify_unclassified_etfs(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Classify all ETFs with NULL investment_strategy.

        Args:
            limit: Optional limit on number to process

        Returns:
            Summary dictionary with statistics
        """
        logger.info(f"🔍 Finding unclassified ETFs (limit: {limit or 'None'})")

        # Find ETFs with NULL investment_strategy
        # Consider it an ETF if name contains 'ETF' or 'FUND' or if it has holdings data
        query_conditions = {'investment_strategy': None}

        unclassified = supabase_select(
            'raw_stocks',
            'symbol,name',
            where_clause=query_conditions,
            limit=limit
        )

        if not unclassified:
            logger.info("✅ No unclassified ETFs found")
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'success_rate': 'N/A'
            }

        # Filter for likely ETFs
        etf_records = []
        for record in unclassified:
            # Check for None record or missing name
            if not record or not record.get('name'):
                continue

            name = record.get('name', '').lower()
            # Check if it looks like an ETF
            if 'etf' in name or 'fund' in name or 'trust' in name:
                etf_records.append(record)

        if not etf_records:
            logger.info("✅ No ETF-like symbols found in unclassified records")
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'success_rate': 'N/A'
            }

        logger.info(f"📊 Found {len(etf_records)} unclassified ETF-like symbols")

        # Classify them
        results = self.classify_batch(etf_records)

        # Summary
        successful = self.stats.successful
        failed = self.stats.failed
        skipped = self.stats.skipped

        summary = {
            'processed': len(results),
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'success_rate': f"{(successful / len(results) * 100):.2f}%" if results else "N/A"
        }

        logger.info(
            f"🎉 Classification summary: {successful} classified, "
            f"{skipped} skipped (not ETFs), {failed} failed"
        )

        return summary

    def get_statistics(self) -> Dict[str, Any]:
        """Get classification statistics."""
        return self.stats.to_dict()


# Helper functions for complex logic
def _get_leverage_related(name: str) -> str:
    """Determine related stock for leveraged/inverse ETFs."""
    if 's&p' in name:
        return 'SPY'
    elif 'nasdaq' in name:
        return 'QQQ'
    elif 'russell' in name:
        return 'IWM'
    else:
        return 'Multiple'


# Convenience functions
def classify_etf(symbol: str, name: str) -> Optional[Tuple[str, str]]:
    """
    Quick function to classify a single ETF.

    Args:
        symbol: ETF symbol
        name: ETF name

    Returns:
        Tuple of (investment_strategy, related_stock) or None

    Example:
        result = classify_etf('SPY', 'SPDR S&P 500 ETF Trust')
        if result:
            strategy, related = result
            print(f"Strategy: {strategy}, Related: {related}")
    """
    classifier = ETFClassifier()
    return classifier.classify_etf(symbol, name)


def classify_unclassified_etfs(limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Quick function to classify all unclassified ETFs.

    Args:
        limit: Optional limit on ETFs to process

    Returns:
        Summary dictionary

    Example:
        summary = classify_unclassified_etfs(limit=100)
        print(f"Classified {summary['successful']} ETFs")
    """
    classifier = ETFClassifier()
    return classifier.classify_unclassified_etfs(limit=limit)


# Export main classes and functions
__all__ = [
    'ETFClassifier',
    'classify_etf',
    'classify_unclassified_etfs'
]
