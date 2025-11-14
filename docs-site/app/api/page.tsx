export default function APIIntroduction() {
  return (
    <div className="prose max-w-none">
      <h1 className="text-3xl font-semibold mb-4 pb-3 border-b border-gray-200">Dividend API Documentation</h1>
      <p className="text-base text-gray-700 mb-8">
        Welcome to the Dividend API documentation. Build powerful dividend investing applications with our production-grade REST API.
      </p>

      <div className="bg-blue-50 border border-blue-200 rounded-md p-5 mb-8">
        <h3 className="text-base font-semibold text-gray-900 mb-2">Getting Started</h3>
        <p className="text-sm text-gray-700 mb-4">
          The API is currently running at <code className="bg-gray-100 px-2 py-0.5 rounded text-sm">http://localhost:8000</code>
        </p>
        <a
          href="http://localhost:8000/v1/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md font-medium hover:bg-blue-700 no-underline"
        >
          View Interactive API Reference
        </a>
      </div>

      <h2 className="text-xl font-semibold mt-12 mb-4 pb-2 border-b border-gray-200">Base URL</h2>
      <pre className="bg-gray-50 border border-gray-200 p-4 rounded-md"><code>http://localhost:8000/v1</code></pre>

      <h2 className="text-xl font-semibold mt-12 mb-4 pb-2 border-b border-gray-200">Key Features</h2>

      <div className="grid grid-cols-2 gap-4 my-6 not-prose">
        <FeatureBox
          title="Comprehensive Data"
          description="Access 24,842+ stocks with real-time prices, dividend history, and future payment schedules"
        />
        <FeatureBox
          title="Dividend Aristocrats & Kings"
          description="Instantly identify stocks with 25+ or 50+ years of consecutive dividend increases - no manual calculation needed"
          isNew
        />
        <FeatureBox
          title="Complete Fundamentals"
          description="Market cap, P/E ratios, payout ratios, sector/industry classifications, and company profiles"
          isNew
        />
        <FeatureBox
          title="ETF Research Tools"
          description="AUM tracking, expense ratio comparison, strategy classification (80+ types), and holdings composition"
          isNew
        />
        <FeatureBox
          title="Intraday Data"
          description="Hour-by-hour OHLCV data with VWAP for better entry timing and volume analysis"
          isNew
        />
        <FeatureBox
          title="High Performance"
          description="Sub-100ms response times with intelligent caching and materialized database views"
        />
        <FeatureBox
          title="Advanced Screeners"
          description="Pre-built screeners for high-yield, monthly payers, aristocrats, kings, and high dividend growth stocks"
        />
        <FeatureBox
          title="Portfolio Analytics"
          description="Calculate dividend projections, reinvestment scenarios, and portfolio performance metrics"
        />
      </div>

      <h2 className="text-xl font-semibold mt-12 mb-4 pb-2 border-b border-gray-200">Quick Example</h2>
      <p className="text-sm text-gray-700">Get high-yield dividend stocks with a simple GET request:</p>

      <h2 className="text-xl font-semibold mt-12 mb-4 pb-2 border-b border-gray-200">Available Endpoints</h2>

      <div className="space-y-6 not-prose">
        {/* Stocks & Fundamentals */}
        <div>
          <h3 className="text-base font-semibold text-gray-900 mb-3">Stocks & Fundamentals</h3>
          <div className="space-y-3">
            <EndpointCard
              method="GET"
              path="/v1/stocks"
              description="List all stocks with optional filtering"
            />
            <EndpointCard
              method="GET"
              path="/v1/stocks/{symbol}"
              description="Get detailed information for a specific stock"
            />
            <EndpointCard
              method="GET"
              path="/v1/stocks/{symbol}/fundamentals"
              description="📊 NEW: Get stock fundamentals (market cap, P/E ratio, sector, industry)"
              isNew
            />
            <EndpointCard
              method="GET"
              path="/v1/stocks/{symbol}/metrics"
              description="📊 NEW: Get dividend metrics with Aristocrat/King status"
              isNew
            />
            <EndpointCard
              method="GET"
              path="/v1/stocks/{symbol}/splits"
              description="📊 NEW: Get historical stock split events"
              isNew
            />
          </div>
        </div>

        {/* Dividend Data */}
        <div>
          <h3 className="text-base font-semibold text-gray-900 mb-3">Dividend Data</h3>
          <div className="space-y-3">
            <EndpointCard
              method="GET"
              path="/v1/dividends/{symbol}"
              description="Get dividend history for a stock"
            />
            <EndpointCard
              method="GET"
              path="/v1/dividends/{symbol}/upcoming"
              description="Get upcoming dividends for a stock"
            />
            <EndpointCard
              method="GET"
              path="/v1/dividends/calendar"
              description="Get upcoming dividend events and payment dates"
            />
          </div>
        </div>

        {/* Price Data */}
        <div>
          <h3 className="text-base font-semibold text-gray-900 mb-3">Price Data</h3>
          <div className="space-y-3">
            <EndpointCard
              method="GET"
              path="/v1/prices/{symbol}"
              description="Get price history with preset ranges (1d, 1m, ytd, max)"
            />
            <EndpointCard
              method="GET"
              path="/v1/prices/{symbol}/latest"
              description="Get latest price snapshot"
            />
            <EndpointCard
              method="GET"
              path="/v1/prices/{symbol}/hourly"
              description="📊 NEW: Get intraday hourly OHLCV data with VWAP"
              isNew
            />
          </div>
        </div>

        {/* Pre-built Screeners */}
        <div>
          <h3 className="text-base font-semibold text-gray-900 mb-3">Pre-built Screeners</h3>
          <div className="space-y-3">
            <EndpointCard
              method="GET"
              path="/v1/screeners/high-yield"
              description="Pre-built screener for high-yield dividend stocks"
            />
            <EndpointCard
              method="GET"
              path="/v1/screeners/monthly-payers"
              description="Find stocks that pay monthly dividends"
            />
            <EndpointCard
              method="GET"
              path="/v1/screeners/dividend-aristocrats"
              description="📊 NEW: Find stocks with 25+ years of consecutive increases"
              isNew
            />
            <EndpointCard
              method="GET"
              path="/v1/screeners/dividend-kings"
              description="📊 NEW: Find elite stocks with 50+ years of consecutive increases"
              isNew
            />
            <EndpointCard
              method="GET"
              path="/v1/screeners/high-growth-dividends"
              description="📊 NEW: Find stocks with strong 5-year dividend growth"
              isNew
            />
          </div>
        </div>

        {/* ETF Research */}
        <div>
          <h3 className="text-base font-semibold text-gray-900 mb-3">ETF Research</h3>
          <div className="space-y-3">
            <EndpointCard
              method="GET"
              path="/v1/etfs"
              description="List all ETFs with filtering"
            />
            <EndpointCard
              method="GET"
              path="/v1/etfs/{symbol}"
              description="Get ETF details with AUM and expense ratio"
            />
            <EndpointCard
              method="GET"
              path="/v1/etfs/{symbol}/holdings"
              description="Get ETF holdings composition"
            />
            <EndpointCard
              method="GET"
              path="/v1/etfs/strategies"
              description="Get ETF strategy classifications (80+ types)"
            />
          </div>
        </div>

        {/* Portfolio Analytics */}
        <div>
          <h3 className="text-base font-semibold text-gray-900 mb-3">Portfolio Analytics</h3>
          <div className="space-y-3">
            <EndpointCard
              method="POST"
              path="/v1/analytics/portfolio/income"
              description="Calculate dividend income projections"
            />
            <EndpointCard
              method="POST"
              path="/v1/analytics/portfolio/yield"
              description="Analyze portfolio yield metrics"
            />
          </div>
        </div>

        {/* Utility */}
        <div>
          <h3 className="text-base font-semibold text-gray-900 mb-3">Utility</h3>
          <div className="space-y-3">
            <EndpointCard
              method="GET"
              path="/v1/search"
              description="Search stocks by symbol, company name, or sector"
            />
          </div>
        </div>
      </div>

      <h2 className="text-xl font-semibold mt-12 mb-4 pb-2 border-b border-gray-200">Response Format</h2>
      <p className="text-sm text-gray-700 mb-4">All responses follow a consistent JSON structure:</p>

      <pre className="bg-gray-50 border border-gray-200 p-4 rounded-md overflow-x-auto"><code>{`{
  "object": "list",
  "has_more": false,
  "cursor": null,
  "data": [
    {
      "id": "stock_aapl",
      "symbol": "AAPL",
      "company": "Apple Inc.",
      "exchange": "NASDAQ",
      "price": 185.50,
      "dividend_yield": 0.52
    }
  ]
}`}</code></pre>

      <h2 className="text-xl font-semibold mt-12 mb-4 pb-2 border-b border-gray-200">Error Handling</h2>
      <p className="text-sm text-gray-700 mb-4">Errors are returned with appropriate HTTP status codes and structured error objects:</p>

      <pre className="bg-gray-50 border border-gray-200 p-4 rounded-md overflow-x-auto"><code>{`{
  "error": {
    "type": "invalid_request_error",
    "message": "Symbol 'INVALID' not found",
    "param": "symbol",
    "code": "symbol_not_found"
  }
}`}</code></pre>

      <h2 className="text-xl font-semibold mt-12 mb-4 pb-2 border-b border-gray-200">Next Steps</h2>
      <ul className="text-sm text-gray-700 space-y-2">
        <li>Browse the <strong>Core Resources</strong> section for detailed endpoint documentation</li>
        <li>Check out <strong>Screeners</strong> for pre-built dividend stock filters</li>
        <li>Explore <strong>Analytics</strong> for portfolio analysis features</li>
        <li>Visit the <a href="http://localhost:8000/v1/docs" target="_blank" rel="noopener noreferrer">Interactive API Reference</a> to test endpoints</li>
      </ul>
    </div>
  );
}

function FeatureBox({ title, description, isNew }: { title: string; description: string; isNew?: boolean }) {
  return (
    <div className={`border rounded-md p-5 hover:border-blue-300 ${isNew ? 'border-green-300 bg-green-50/30' : 'border-gray-200'}`}>
      <div className="flex items-center gap-2 mb-2">
        <h3 className="font-semibold text-base text-gray-900">{title}</h3>
        {isNew && (
          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800">
            NEW
          </span>
        )}
      </div>
      <p className="text-gray-700 text-sm">{description}</p>
    </div>
  );
}

function EndpointCard({ method, path, description, isNew }: { method: string; path: string; description: string; isNew?: boolean }) {
  const methodColors: Record<string, string> = {
    GET: 'bg-blue-100 text-blue-800',
    POST: 'bg-green-100 text-green-800',
    PUT: 'bg-yellow-100 text-yellow-800',
    DELETE: 'bg-red-100 text-red-800',
  };

  return (
    <div className={`border rounded-md p-4 hover:border-blue-300 ${isNew ? 'border-blue-300 bg-blue-50/30' : 'border-gray-200'}`}>
      <div className="flex items-center gap-3 mb-2">
        <span className={`px-2 py-1 rounded text-xs font-mono font-semibold ${methodColors[method]}`}>
          {method}
        </span>
        <code className="text-sm text-gray-900 font-mono">{path}</code>
        {isNew && (
          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800">
            v1.2.0
          </span>
        )}
      </div>
      <p className="text-sm text-gray-700">{description}</p>
    </div>
  );
}
