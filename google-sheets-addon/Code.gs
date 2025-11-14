/**
 * ============================================================================
 * Dividend API - Google Sheets Add-on
 * ============================================================================
 * Custom functions to fetch dividend stock data directly in Google Sheets
 * Usage: =DIVV_PRICE("AAPL"), =DIVV_DIVIDEND("AAPL"), etc.
 * ============================================================================
 */

// ============================================================================
// CONFIGURATION
// ============================================================================
const API_BASE_URL = 'https://api.yourdomain.com/v1';

/**
 * Get API key from user properties
 * Users should set this via: Tools > Script Editor > Run > setApiKey
 */
function getApiKey() {
  const userProperties = PropertiesService.getUserProperties();
  const apiKey = userProperties.getProperty('DIVV_API_KEY');

  if (!apiKey) {
    throw new Error('API Key not set. Run setApiKey() function first or use DIVV_SET_KEY()');
  }

  return apiKey;
}

/**
 * Set API key (run this function once to configure)
 * @param {string} apiKey Your Dividend API key
 */
function setApiKey(apiKey) {
  const userProperties = PropertiesService.getUserProperties();
  userProperties.setProperty('DIVV_API_KEY', apiKey);
  return 'API Key saved successfully!';
}

/**
 * Custom function to set API key from spreadsheet
 * @param {string} apiKey Your API key
 * @customfunction
 */
function DIVV_SET_KEY(apiKey) {
  return setApiKey(apiKey);
}

// ============================================================================
// CORE API FUNCTION
// ============================================================================

/**
 * Make API request
 * @param {string} endpoint API endpoint path
 * @return {object} Parsed JSON response
 */
function callAPI(endpoint) {
  const apiKey = getApiKey();
  const url = API_BASE_URL + endpoint;

  const options = {
    'method': 'get',
    'headers': {
      'X-API-Key': apiKey,
      'Content-Type': 'application/json'
    },
    'muteHttpExceptions': true
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();

    if (statusCode === 200) {
      return JSON.parse(response.getContentText());
    } else if (statusCode === 401) {
      throw new Error('Invalid API Key');
    } else if (statusCode === 429) {
      throw new Error('Rate limit exceeded');
    } else {
      throw new Error('API Error: ' + statusCode);
    }
  } catch (error) {
    throw new Error('API Request Failed: ' + error.message);
  }
}

// ============================================================================
// STOCK PRICE FUNCTIONS
// ============================================================================

/**
 * Get latest stock price
 * @param {string} symbol Stock symbol (e.g., "AAPL")
 * @return {number} Latest close price
 * @customfunction
 */
function DIVV_PRICE(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}/latest-price`);
    return data.close || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get stock price change percentage
 * @param {string} symbol Stock symbol
 * @return {number} Change percentage (as decimal)
 * @customfunction
 */
function DIVV_CHANGE(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}/latest-price`);
    return data.change_percent ? data.change_percent / 100 : 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get opening price
 * @param {string} symbol Stock symbol
 * @return {number} Opening price
 * @customfunction
 */
function DIVV_OPEN(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}/latest-price`);
    return data.open || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get high price
 * @param {string} symbol Stock symbol
 * @return {number} High price
 * @customfunction
 */
function DIVV_HIGH(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}/latest-price`);
    return data.high || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get low price
 * @param {string} symbol Stock symbol
 * @return {number} Low price
 * @customfunction
 */
function DIVV_LOW(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}/latest-price`);
    return data.low || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get trading volume
 * @param {string} symbol Stock symbol
 * @return {number} Trading volume
 * @customfunction
 */
function DIVV_VOLUME(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}/latest-price`);
    return data.volume || 'N/A';
  } catch (error) {
    return error.message;
  }
}

// ============================================================================
// DIVIDEND FUNCTIONS
// ============================================================================

/**
 * Get dividend yield
 * @param {string} symbol Stock symbol
 * @return {number} Dividend yield (as decimal)
 * @customfunction
 */
function DIVV_YIELD(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}`);
    return data.dividend_yield ? data.dividend_yield / 100 : 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get annual dividend amount (TTM)
 * @param {string} symbol Stock symbol
 * @return {number} Annual dividend amount
 * @customfunction
 */
function DIVV_ANNUAL(symbol) {
  try {
    const data = callAPI(`/dividends/${symbol}/metrics`);
    return data.ttm_dividend || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get next ex-dividend date
 * @param {string} symbol Stock symbol
 * @return {string} Next ex-dividend date
 * @customfunction
 */
function DIVV_NEXT_DATE(symbol) {
  try {
    const data = callAPI(`/dividends/${symbol}/next`);
    return data.ex_dividend_date || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get next dividend amount
 * @param {string} symbol Stock symbol
 * @return {number} Next dividend amount
 * @customfunction
 */
function DIVV_NEXT_AMOUNT(symbol) {
  try {
    const data = callAPI(`/dividends/${symbol}/next`);
    return data.dividend || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get dividend payment frequency
 * @param {string} symbol Stock symbol
 * @return {string} Payment frequency (Monthly, Quarterly, etc.)
 * @customfunction
 */
function DIVV_FREQUENCY(symbol) {
  try {
    const data = callAPI(`/dividends/${symbol}/metrics`);
    return data.frequency || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get dividend growth rate
 * @param {string} symbol Stock symbol
 * @return {number} Growth rate (as decimal)
 * @customfunction
 */
function DIVV_GROWTH(symbol) {
  try {
    const data = callAPI(`/dividends/${symbol}/metrics`);
    return data.growth_rate ? data.growth_rate / 100 : 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get dividend payout ratio
 * @param {string} symbol Stock symbol
 * @return {number} Payout ratio (as decimal)
 * @customfunction
 */
function DIVV_PAYOUT_RATIO(symbol) {
  try {
    const data = callAPI(`/dividends/${symbol}/metrics`);
    return data.payout_ratio ? data.payout_ratio / 100 : 'N/A';
  } catch (error) {
    return error.message;
  }
}

// ============================================================================
// ETF FUNCTIONS
// ============================================================================

/**
 * Get Assets Under Management (AUM) for ETFs
 * @param {string} symbol ETF symbol
 * @return {number} AUM in dollars
 * @customfunction
 */
function DIVV_AUM(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}`);
    return data.aum || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get Implied Volatility (for covered call ETFs)
 * @param {string} symbol ETF symbol
 * @return {number} IV (as decimal)
 * @customfunction
 */
function DIVV_IV(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}/latest-price`);
    return data.iv ? data.iv / 100 : 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get ETF investment strategy
 * @param {string} symbol ETF symbol
 * @return {string} Investment strategy description
 * @customfunction
 */
function DIVV_STRATEGY(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}`);
    return data.investment_strategy || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get ETF expense ratio
 * @param {string} symbol ETF symbol
 * @return {number} Expense ratio (as decimal)
 * @customfunction
 */
function DIVV_EXPENSE_RATIO(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}`);
    return data.expense_ratio ? data.expense_ratio / 100 : 'N/A';
  } catch (error) {
    return error.message;
  }
}

// ============================================================================
// COMPANY INFO FUNCTIONS
// ============================================================================

/**
 * Get company or ETF name
 * @param {string} symbol Stock symbol
 * @return {string} Company/ETF name
 * @customfunction
 */
function DIVV_NAME(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}`);
    return data.name || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get sector
 * @param {string} symbol Stock symbol
 * @return {string} Sector name
 * @customfunction
 */
function DIVV_SECTOR(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}`);
    return data.sector || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get industry
 * @param {string} symbol Stock symbol
 * @return {string} Industry name
 * @customfunction
 */
function DIVV_INDUSTRY(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}`);
    return data.industry || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get exchange
 * @param {string} symbol Stock symbol
 * @return {string} Exchange name
 * @customfunction
 */
function DIVV_EXCHANGE(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}`);
    return data.exchange || 'N/A';
  } catch (error) {
    return error.message;
  }
}

/**
 * Get market cap
 * @param {string} symbol Stock symbol
 * @return {number} Market capitalization
 * @customfunction
 */
function DIVV_MARKET_CAP(symbol) {
  try {
    const data = callAPI(`/stocks/${symbol}`);
    return data.market_cap || 'N/A';
  } catch (error) {
    return error.message;
  }
}

// ============================================================================
// PORTFOLIO FUNCTIONS
// ============================================================================

/**
 * Calculate annual dividend income for a position
 * @param {string} symbol Stock symbol
 * @param {number} shares Number of shares owned
 * @return {number} Annual dividend income
 * @customfunction
 */
function DIVV_INCOME(symbol, shares) {
  try {
    const data = callAPI(`/dividends/${symbol}/metrics`);
    const ttmDividend = data.ttm_dividend || 0;
    return ttmDividend * shares;
  } catch (error) {
    return error.message;
  }
}

/**
 * Calculate position value
 * @param {string} symbol Stock symbol
 * @param {number} shares Number of shares owned
 * @return {number} Position value
 * @customfunction
 */
function DIVV_POSITION_VALUE(symbol, shares) {
  try {
    const data = callAPI(`/stocks/${symbol}/latest-price`);
    const price = data.close || 0;
    return price * shares;
  } catch (error) {
    return error.message;
  }
}

/**
 * Calculate portfolio yield on cost
 * @param {string} symbol Stock symbol
 * @param {number} costBasis Your cost basis per share
 * @return {number} Yield on cost (as decimal)
 * @customfunction
 */
function DIVV_YIELD_ON_COST(symbol, costBasis) {
  try {
    const data = callAPI(`/dividends/${symbol}/metrics`);
    const ttmDividend = data.ttm_dividend || 0;
    if (costBasis <= 0) return 'N/A';
    return ttmDividend / costBasis;
  } catch (error) {
    return error.message;
  }
}

// ============================================================================
// SCREENER FUNCTIONS
// ============================================================================

/**
 * Search for stocks by name or symbol
 * @param {string} query Search query
 * @return {string} First matching symbol
 * @customfunction
 */
function DIVV_SEARCH(query) {
  try {
    const data = callAPI(`/search?q=${encodeURIComponent(query)}&limit=1`);
    if (data.results && data.results.length > 0) {
      return data.results[0].symbol;
    }
    return 'N/A';
  } catch (error) {
    return error.message;
  }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Check API connection status
 * @return {string} Connection status
 * @customfunction
 */
function DIVV_API_STATUS() {
  try {
    callAPI('/health');
    return 'Connected';
  } catch (error) {
    return 'Disconnected: ' + error.message;
  }
}

/**
 * Get your current API rate limit usage
 * @return {string} Rate limit info
 * @customfunction
 */
function DIVV_RATE_LIMIT() {
  try {
    const apiKey = getApiKey();
    const data = callAPI(`/api-keys/current`);
    return `${data.requests_used}/${data.rate_limit} requests used`;
  } catch (error) {
    return error.message;
  }
}

// ============================================================================
// BATCH FUNCTIONS (for better performance)
// ============================================================================

/**
 * Get multiple data points for a symbol
 * @param {string} symbol Stock symbol
 * @return {array} Array of [price, yield, annual dividend, next date]
 * @customfunction
 */
function DIVV_SUMMARY(symbol) {
  try {
    const stockData = callAPI(`/stocks/${symbol}`);
    const priceData = callAPI(`/stocks/${symbol}/latest-price`);
    const divData = callAPI(`/dividends/${symbol}/metrics`);
    const nextDiv = callAPI(`/dividends/${symbol}/next`);

    return [
      [priceData.close || 'N/A'],
      [stockData.dividend_yield ? stockData.dividend_yield / 100 : 'N/A'],
      [divData.ttm_dividend || 'N/A'],
      [nextDiv.ex_dividend_date || 'N/A'],
      [nextDiv.dividend || 'N/A']
    ];
  } catch (error) {
    return [[error.message]];
  }
}

// ============================================================================
// MENU FUNCTIONS
// ============================================================================

/**
 * Create custom menu when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Dividend API')
    .addItem('Set API Key', 'showApiKeyDialog')
    .addItem('Refresh All Data', 'refreshAllData')
    .addItem('About', 'showAbout')
    .addToUi();
}

/**
 * Show dialog to set API key
 */
function showApiKeyDialog() {
  const html = HtmlService.createHtmlOutput(
    '<p>Enter your Dividend API key:</p>' +
    '<input type="text" id="apiKey" style="width: 300px;">' +
    '<br><br>' +
    '<button onclick="saveKey()">Save</button>' +
    '<script>' +
    'function saveKey() {' +
    '  var key = document.getElementById("apiKey").value;' +
    '  google.script.run.withSuccessHandler(function() {' +
    '    alert("API Key saved successfully!");' +
    '    google.script.host.close();' +
    '  }).setApiKey(key);' +
    '}' +
    '</script>'
  ).setWidth(400).setHeight(150);

  SpreadsheetApp.getUi().showModalDialog(html, 'Set API Key');
}

/**
 * Refresh all data in the spreadsheet
 */
function refreshAllData() {
  SpreadsheetApp.getActiveSpreadsheet().getActiveSheet().getDataRange().offset(0, 0).activate();
  SpreadsheetApp.flush();
}

/**
 * Show about dialog
 */
function showAbout() {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    'Dividend API for Google Sheets',
    'Version 1.0\n\n' +
    'Custom functions to fetch dividend stock data.\n\n' +
    'Get your API key at: https://yourdomain.com/api-keys\n\n' +
    'Documentation: https://docs.yourdomain.com',
    ui.ButtonSet.OK
  );
}
