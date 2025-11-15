/**
 * DIVV() - Custom Google Sheets function for dividend data
 *
 * A drop-in replacement for GOOGLEFINANCE() with superior dividend data.
 *
 * @param {string} symbol - Stock symbol (e.g., "AAPL", "MSFT")
 * @param {string} attribute - Data attribute to retrieve
 * @param {Date|string} startDate - (Optional) Start date for historical data
 * @param {Date|string} endDate - (Optional) End date for historical data range
 * @return {number|string|array} The requested data
 *
 * @customfunction
 *
 * Examples:
 *   =DIVV("AAPL", "price")                          → Current price
 *   =DIVV("AAPL", "close", "2024-01-15")           → Historical close on specific date
 *   =DIVV("AAPL", "close", DATE(2024,1,1))         → Using DATE() function
 *   =DIVV("AAPL", "close", "2024-01-01", "2024-12-31") → Price history for date range
 *   =DIVV("AAPL", "dividendYield")                  → Current dividend yield
 *
 * Installation:
 *   1. Open your Google Sheet
 *   2. Go to Extensions > Apps Script
 *   3. Delete any existing code
 *   4. Paste this entire file
 *   5. Update API_BASE_URL with your Divv API endpoint
 *   6. Save (Ctrl+S or Cmd+S)
 *   7. Start using =DIVV() in your sheet!
 *
 * Version: 2.0.0
 * Last Updated: 2025-11-14
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

/**
 * Base URL for Divv API
 * Update this to your production API endpoint or use localhost for testing
 */
const API_BASE_URL = 'http://localhost:8000';

/**
 * API Key (optional for now, required for production)
 * Get your free API key at: https://divv.com/api-keys
 */
const API_KEY = ''; // Leave empty for local development

/**
 * Enable caching to reduce API calls and improve performance
 * Cached data expires after CACHE_DURATION_SECONDS
 */
const ENABLE_CACHE = true;
const CACHE_DURATION_SECONDS = 300; // 5 minutes

/**
 * Retry configuration for failed requests
 */
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

/**
 * Tier restrictions
 * Free tier: only price and dividendYield
 * Paid tiers: all attributes
 * Set to 'free' or 'paid' based on your subscription
 */
const ACCOUNT_TIER = 'free'; // Change to 'paid' after upgrading

// ============================================================================
// MAIN FUNCTION
// ============================================================================

/**
 * Main DIVV function - entry point for Google Sheets
 */
function DIVV(symbol, attribute, startDate, endDate) {
  // Input validation
  if (!symbol || typeof symbol !== 'string') {
    return '#ERROR: Invalid symbol';
  }

  symbol = symbol.toString().trim().toUpperCase();

  // If dates are provided, fetch historical data
  if (startDate || endDate) {
    return fetchHistoricalData(symbol, attribute, startDate, endDate);
  }

  // Otherwise, fetch current/latest data
  const cacheKey = `DIVV_${symbol}`;
  let data = null;

  if (ENABLE_CACHE) {
    data = getFromCache(cacheKey);
    if (data) {
      return extractAttribute(data, attribute);
    }
  }

  // Fetch from API
  try {
    data = fetchStockData(symbol);

    // Store in cache
    if (ENABLE_CACHE && data) {
      saveToCache(cacheKey, data);
    }

    return extractAttribute(data, attribute);

  } catch (error) {
    return `#ERROR: ${error.message}`;
  }
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

/**
 * Fetch stock data from Divv API with retry logic
 */
function fetchStockData(symbol, retryCount = 0) {
  const url = `${API_BASE_URL}/v1/stocks/${symbol}/quote`;

  const options = {
    method: 'get',
    headers: {
      'Accept': 'application/json'
    },
    muteHttpExceptions: true
  };

  // Add API key if configured
  if (API_KEY) {
    options.headers['X-API-Key'] = API_KEY;
  }

  try {
    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();

    // Success
    if (statusCode === 200) {
      const data = JSON.parse(response.getContentText());
      return data;
    }

    // Not found
    if (statusCode === 404) {
      throw new Error(`Symbol ${symbol} not found`);
    }

    // Rate limited - retry with backoff
    if (statusCode === 429 && retryCount < MAX_RETRIES) {
      const delay = RETRY_DELAY_MS * Math.pow(2, retryCount);
      Utilities.sleep(delay);
      return fetchStockData(symbol, retryCount + 1);
    }

    // Other errors
    throw new Error(`API error: ${statusCode}`);

  } catch (error) {
    if (retryCount < MAX_RETRIES) {
      Utilities.sleep(RETRY_DELAY_MS);
      return fetchStockData(symbol, retryCount + 1);
    }
    throw error;
  }
}

/**
 * Fetch historical price data from Divv API
 */
function fetchHistoricalData(symbol, attribute, startDate, endDate) {
  // Check tier restriction (historical data requires paid tier)
  if (ACCOUNT_TIER === 'free') {
    return '#UPGRADE: Historical data requires a paid plan. Visit divv.com/pricing';
  }

  // Convert dates to ISO format (YYYY-MM-DD)
  const formatDate = (date) => {
    if (!date) return null;

    // Handle Date objects
    if (date instanceof Date) {
      return Utilities.formatDate(date, Session.getScriptTimeZone(), 'yyyy-MM-dd');
    }

    // Handle string dates (assume YYYY-MM-DD format)
    if (typeof date === 'string') {
      return date;
    }

    // Handle numeric dates (Google Sheets serial number)
    if (typeof date === 'number') {
      const d = new Date((date - 25569) * 86400 * 1000);
      return Utilities.formatDate(d, Session.getScriptTimeZone(), 'yyyy-MM-dd');
    }

    return null;
  };

  const start = formatDate(startDate);
  const end = formatDate(endDate);

  // Build URL with query parameters
  let url = `${API_BASE_URL}/v1/prices/${symbol}?`;

  if (start && end) {
    // Date range
    url += `start_date=${start}&end_date=${end}`;
  } else if (start) {
    // Single date - get just that day
    url += `start_date=${start}&end_date=${start}`;
  } else if (end) {
    // End date only - get just that day
    url += `start_date=${end}&end_date=${end}`;
  }

  const options = {
    method: 'get',
    headers: {
      'Accept': 'application/json'
    },
    muteHttpExceptions: true
  };

  if (API_KEY) {
    options.headers['X-API-Key'] = API_KEY;
  }

  try {
    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();

    if (statusCode === 200) {
      const result = JSON.parse(response.getContentText());

      // Extract price history data
      if (!result.data || result.data.length === 0) {
        return '#N/A';
      }

      // If single date, return single value
      if (result.data.length === 1) {
        return extractHistoricalAttribute(result.data[0], attribute);
      }

      // If date range, return array of [date, value]
      const output = [['Date', attribute || 'Close']];
      result.data.forEach(bar => {
        output.push([
          bar.date,
          extractHistoricalAttribute(bar, attribute)
        ]);
      });

      return output;
    }

    if (statusCode === 404) {
      return '#N/A';
    }

    throw new Error(`API error: ${statusCode}`);

  } catch (error) {
    return `#ERROR: ${error.message}`;
  }
}

/**
 * Extract attribute from historical price bar
 */
function extractHistoricalAttribute(bar, attribute) {
  if (!attribute) {
    attribute = 'close';  // Default to close price
  }

  const attr = attribute.toLowerCase();

  // Map common attributes
  const attrMap = {
    'price': 'close',
    'close': 'close',
    'open': 'open',
    'high': 'high',
    'low': 'low',
    'volume': 'volume'
  };

  const mappedAttr = attrMap[attr] || attr;

  return bar[mappedAttr] || '#N/A';
}

// ============================================================================
// DATA EXTRACTION
// ============================================================================

/**
 * Extract specific attribute from stock data
 */
function extractAttribute(data, attribute) {
  if (!data) {
    return '#N/A';
  }

  // If no attribute specified, return all data as 2D array for sheets
  if (!attribute) {
    return formatDataForSheets(data);
  }

  // Normalize attribute name (handle both camelCase and snake_case)
  const normalizedAttr = normalizeAttributeName(attribute);

  // Check tier restrictions (free tier only gets price and dividend data)
  if (ACCOUNT_TIER === 'free') {
    const allowedAttributes = ['price', 'open', 'dayHigh', 'dayLow', 'previousClose', 'dividendYield', 'dividendAmount'];
    if (!allowedAttributes.includes(normalizedAttr)) {
      return '#UPGRADE: This attribute requires a paid plan. Visit divv.com/pricing';
    }
  }

  // Try to get the value
  const value = data[normalizedAttr] || data[attribute];

  if (value === null || value === undefined) {
    return '#N/A';
  }

  return value;
}

/**
 * Normalize attribute names to match API response
 * Handles GOOGLEFINANCE() compatibility
 */
function normalizeAttributeName(attr) {
  const attrMap = {
    // GOOGLEFINANCE() compatible names
    'price': 'price',
    'priceopen': 'open',
    'high': 'dayHigh',
    'low': 'dayLow',
    'volume': 'volume',
    'marketcap': 'marketCap',
    'pe': 'peRatio',
    'eps': 'eps',
    'high52': 'yearHigh',
    'low52': 'yearLow',
    'change': 'change',
    'changepct': 'changePercent',
    'shares': 'sharesOutstanding',
    'avgvol': 'avgVolume',
    'sma50': 'priceAvg50',
    'sma200': 'priceAvg200',
    'dividendyield': 'dividendYield',

    // Divv-specific (camelCase)
    'dividendamount': 'dividendAmount',
    'previousclose': 'previousClose',
    'dayhigh': 'dayHigh',
    'daylow': 'dayLow',
    'yearhigh': 'yearHigh',
    'yearlow': 'yearLow',
    'peratio': 'peRatio',
    'sharesoutstanding': 'sharesOutstanding',
    'avgvolume': 'avgVolume',
    'priceavg50': 'priceAvg50',
    'priceavg200': 'priceAvg200',
    'changepercent': 'changePercent',
    'marketcap': 'marketCap',
  };

  const normalized = attr.toLowerCase().replace(/[_\s]/g, '');
  return attrMap[normalized] || attr;
}

/**
 * Format data object as 2D array for Google Sheets
 */
function formatDataForSheets(data) {
  const fields = [
    ['Symbol', data.symbol || '#N/A'],
    ['Price', data.price || '#N/A'],
    ['Open', data.open || '#N/A'],
    ['Day High', data.dayHigh || '#N/A'],
    ['Day Low', data.dayLow || '#N/A'],
    ['Previous Close', data.previousClose || '#N/A'],
    ['Change', data.change || '#N/A'],
    ['Change %', data.changePercent || '#N/A'],
    ['Volume', data.volume || '#N/A'],
    ['Avg Volume', data.avgVolume || '#N/A'],
    ['52-Week High', data.yearHigh || '#N/A'],
    ['52-Week Low', data.yearLow || '#N/A'],
    ['50-Day MA', data.priceAvg50 || '#N/A'],
    ['200-Day MA', data.priceAvg200 || '#N/A'],
    ['Market Cap', data.marketCap || '#N/A'],
    ['P/E Ratio', data.peRatio || '#N/A'],
    ['EPS', data.eps || '#N/A'],
    ['Shares Outstanding', data.sharesOutstanding || '#N/A'],
    ['Dividend Yield', data.dividendYield || '#N/A'],
    ['Dividend Amount', data.dividendAmount || '#N/A'],
    ['Company', data.company || '#N/A'],
    ['Exchange', data.exchange || '#N/A'],
    ['Sector', data.sector || '#N/A']
  ];

  return fields;
}

// ============================================================================
// CACHE MANAGEMENT
// ============================================================================

/**
 * Get data from cache
 */
function getFromCache(key) {
  try {
    const cache = CacheService.getScriptCache();
    const cached = cache.get(key);

    if (cached) {
      return JSON.parse(cached);
    }
  } catch (error) {
    // Cache errors are non-fatal
    console.log('Cache read error:', error);
  }

  return null;
}

/**
 * Save data to cache
 */
function saveToCache(key, data) {
  try {
    const cache = CacheService.getScriptCache();
    cache.put(key, JSON.stringify(data), CACHE_DURATION_SECONDS);
  } catch (error) {
    // Cache errors are non-fatal
    console.log('Cache write error:', error);
  }
}

/**
 * Clear all cached data (utility function)
 */
function clearDivvCache() {
  try {
    const cache = CacheService.getScriptCache();
    cache.removeAll(cache.getKeys());
    return 'Cache cleared successfully';
  } catch (error) {
    return 'Error clearing cache: ' + error.message;
  }
}

// ============================================================================
// BULK FUNCTIONS (Advanced)
// ============================================================================

/**
 * Fetch multiple stocks at once (more efficient)
 *
 * Usage: =DIVVBULK(A1:A10, "price")
 * Where A1:A10 contains stock symbols
 */
function DIVVBULK(symbols, attribute) {
  if (!symbols || !Array.isArray(symbols)) {
    return '#ERROR: Invalid symbols range';
  }

  const results = [];

  for (let i = 0; i < symbols.length; i++) {
    const row = symbols[i];
    const symbol = Array.isArray(row) ? row[0] : row;

    if (symbol && typeof symbol === 'string') {
      results.push([DIVV(symbol, attribute)]);
    } else {
      results.push(['#N/A']);
    }
  }

  return results;
}

// ============================================================================
// HELPER FUNCTIONS FOR SHEETS
// ============================================================================

/**
 * Get dividend history for a symbol
 * Returns array of [date, amount] pairs
 *
 * Usage: =DIVVDIVIDENDS("AAPL")
 */
function DIVVDIVIDENDS(symbol, limit) {
  // Check tier restriction
  if (ACCOUNT_TIER === 'free') {
    return '#UPGRADE: Dividend history requires a paid plan. Visit divv.com/pricing';
  }

  if (!symbol || typeof symbol !== 'string') {
    return '#ERROR: Invalid symbol';
  }

  symbol = symbol.toString().trim().toUpperCase();
  limit = limit || 12; // Default to last 12 dividends

  const url = `${API_BASE_URL}/v1/dividends/${symbol}?limit=${limit}`;

  const options = {
    method: 'get',
    headers: { 'Accept': 'application/json' },
    muteHttpExceptions: true
  };

  if (API_KEY) {
    options.headers['X-API-Key'] = API_KEY;
  }

  try {
    const response = UrlFetchApp.fetch(url, options);

    if (response.getResponseCode() === 200) {
      const data = JSON.parse(response.getContentText());

      // Return as 2D array for sheets
      const results = [['Date', 'Amount', 'Frequency']];

      if (data.dividends && Array.isArray(data.dividends)) {
        data.dividends.forEach(div => {
          results.push([
            div.ex_date || div.exDate,
            div.amount,
            div.frequency || 'N/A'
          ]);
        });
      }

      return results;
    }

    return '#ERROR: Failed to fetch dividends';

  } catch (error) {
    return `#ERROR: ${error.message}`;
  }
}

/**
 * Check if stock is a Dividend Aristocrat (25+ years)
 *
 * Usage: =DIVVARISTOCRAT("JNJ")
 * Returns: TRUE/FALSE or years of increases
 */
function DIVVARISTOCRAT(symbol, returnYears) {
  // Check tier restriction
  if (ACCOUNT_TIER === 'free') {
    return '#UPGRADE: Aristocrat detection requires a paid plan. Visit divv.com/pricing';
  }

  if (!symbol || typeof symbol !== 'string') {
    return '#ERROR: Invalid symbol';
  }

  symbol = symbol.toString().trim().toUpperCase();

  const url = `${API_BASE_URL}/v1/stocks/${symbol}/metrics`;

  const options = {
    method: 'get',
    headers: { 'Accept': 'application/json' },
    muteHttpExceptions: true
  };

  if (API_KEY) {
    options.headers['X-API-Key'] = API_KEY;
  }

  try {
    const response = UrlFetchApp.fetch(url, options);

    if (response.getResponseCode() === 200) {
      const data = JSON.parse(response.getContentText());
      const years = data.consecutive_years_of_increases || 0;

      if (returnYears) {
        return years;
      }

      return years >= 25;
    }

    return returnYears ? 0 : false;

  } catch (error) {
    return `#ERROR: ${error.message}`;
  }
}

// ============================================================================
// UTILITIES
// ============================================================================

/**
 * Test function to verify API connectivity
 * Run this from Script Editor to test your setup
 */
function testDivvConnection() {
  const testSymbol = 'AAPL';

  Logger.log('Testing Divv API connection...');
  Logger.log('API Base URL: ' + API_BASE_URL);
  Logger.log('Testing with symbol: ' + testSymbol);

  try {
    const result = DIVV(testSymbol, 'price');
    Logger.log('Success! Current price of ' + testSymbol + ': $' + result);
    return 'Connection successful!';
  } catch (error) {
    Logger.log('Error: ' + error.message);
    return 'Connection failed: ' + error.message;
  }
}

/**
 * Get API usage stats (if API key is configured)
 */
function getDivvApiStats() {
  if (!API_KEY) {
    return 'API key not configured';
  }

  // TODO: Implement when API stats endpoint is available
  return 'API stats endpoint coming soon';
}
