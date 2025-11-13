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

      <div className="grid md:grid-cols-2 gap-4 my-6 not-prose">
        <FeatureBox
          title="Comprehensive Data"
          description="Access 24,842+ stocks with real-time prices, dividend history, and future payment schedules"
        />
        <FeatureBox
          title="High Performance"
          description="Sub-100ms response times with intelligent caching and materialized database views"
        />
        <FeatureBox
          title="Flexible Filtering"
          description="Filter stocks by yield, market cap, sector, exchange, and more with powerful query parameters"
        />
        <FeatureBox
          title="Portfolio Analytics"
          description="Calculate dividend projections, reinvestment scenarios, and portfolio performance metrics"
        />
      </div>

      <h2 className="text-xl font-semibold mt-12 mb-4 pb-2 border-b border-gray-200">Quick Example</h2>
      <p className="text-sm text-gray-700">Get high-yield dividend stocks with a simple GET request:</p>

      <h2 className="text-xl font-semibold mt-12 mb-4 pb-2 border-b border-gray-200">Available Endpoints</h2>

      <div className="space-y-4 not-prose">
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
          path="/v1/dividends/calendar"
          description="Get upcoming dividend events and payment dates"
        />
        <EndpointCard
          method="GET"
          path="/v1/screeners/high-yield"
          description="Pre-built screener for high-yield dividend stocks"
        />
        <EndpointCard
          method="POST"
          path="/v1/analytics/portfolio"
          description="Analyze portfolio and calculate dividend projections"
        />
        <EndpointCard
          method="GET"
          path="/v1/search"
          description="Search stocks by symbol, company name, or sector"
        />
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

function FeatureBox({ title, description }: { title: string; description: string }) {
  return (
    <div className="border border-gray-200 rounded-md p-5 hover:border-blue-300">
      <h3 className="font-semibold text-base text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-700 text-sm">{description}</p>
    </div>
  );
}

function EndpointCard({ method, path, description }: { method: string; path: string; description: string }) {
  const methodColors: Record<string, string> = {
    GET: 'bg-blue-100 text-blue-800',
    POST: 'bg-green-100 text-green-800',
    PUT: 'bg-yellow-100 text-yellow-800',
    DELETE: 'bg-red-100 text-red-800',
  };

  return (
    <div className="border border-gray-200 rounded-md p-4 hover:border-blue-300">
      <div className="flex items-center gap-3 mb-2">
        <span className={`px-2 py-1 rounded text-xs font-mono font-semibold ${methodColors[method]}`}>
          {method}
        </span>
        <code className="text-sm text-gray-900 font-mono">{path}</code>
      </div>
      <p className="text-sm text-gray-700">{description}</p>
    </div>
  );
}
