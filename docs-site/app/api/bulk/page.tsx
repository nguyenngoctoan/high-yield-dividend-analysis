'use client';

export default function BulkPage() {
  return (
    <div className="max-w-4xl">
      <div className="flex items-center gap-3 mb-4 pb-3 border-b border-gray-200">
        <h1 className="text-3xl font-semibold">
          Bulk Operations
        </h1>
        <span className="bg-gradient-to-r from-purple-600 to-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
          PROFESSIONAL+
        </span>
      </div>

      <p className="text-sm text-gray-700 mb-4">
        Bulk endpoints allow you to fetch data for multiple symbols in a single request, dramatically reducing API calls and improving performance.
      </p>

      <div className="bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200 rounded-lg p-4 mb-8">
        <div className="flex items-start gap-3">
          <div className="text-2xl">⚡</div>
          <div>
            <p className="font-semibold text-purple-900 mb-2">10-100x Fewer API Calls</p>
            <p className="text-sm text-gray-700">
              Instead of making 100 individual requests, make 1 bulk request. Perfect for portfolio tracking, screeners, and data analysis.
            </p>
          </div>
        </div>
      </div>

      {/* Bulk Stocks Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-green-100 text-green-700 text-xs font-semibold px-2 py-1 rounded">POST</span>
          Get multiple stocks
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/bulk/stocks</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Fetch detailed information for multiple stocks in a single request. Returns data for all symbols with error handling for invalid symbols.
        </p>

        <h3 className="text-base font-semibold mb-3">Request Body</h3>
        <div className="border border-gray-200 rounded-md mb-6">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Type</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="px-4 py-3 font-mono text-xs">symbols</td>
                <td className="px-4 py-3 text-gray-600">array</td>
                <td className="px-4 py-3 text-gray-700">
                  <span className="bg-red-100 text-red-700 text-xs px-1.5 py-0.5 rounded mr-2">required</span>
                  List of stock symbols (max 1,000)
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">expand</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Comma-separated fields: "company", "dividends", "prices"</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Tier Limits</h3>
        <div className="border border-gray-200 rounded-md mb-6">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Tier</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Max Symbols</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Use Case</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr className="bg-gray-100">
                <td className="px-4 py-3 text-gray-500">Free</td>
                <td className="px-4 py-3 text-gray-500">Not available</td>
                <td className="px-4 py-3 text-gray-500">Use individual endpoints</td>
              </tr>
              <tr className="bg-gray-100">
                <td className="px-4 py-3 text-gray-500">Starter</td>
                <td className="px-4 py-3 text-gray-500">Not available</td>
                <td className="px-4 py-3 text-gray-500">Use individual endpoints</td>
              </tr>
              <tr className="bg-gray-100">
                <td className="px-4 py-3 text-gray-500">Premium</td>
                <td className="px-4 py-3 text-gray-500">Not available</td>
                <td className="px-4 py-3 text-gray-500">Use individual endpoints</td>
              </tr>
              <tr className="bg-purple-50">
                <td className="px-4 py-3 font-semibold">Professional</td>
                <td className="px-4 py-3 font-semibold">1,000 symbols</td>
                <td className="px-4 py-3 text-gray-700">Large portfolios, screeners</td>
              </tr>
              <tr className="bg-purple-50">
                <td className="px-4 py-3 font-semibold">Enterprise</td>
                <td className="px-4 py-3 font-semibold">Unlimited</td>
                <td className="px-4 py-3 text-gray-700">Full market analysis</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Example Request</h3>
        <div className="bg-gray-900 rounded-md p-4 mb-6 overflow-x-auto">
          <code className="text-sm font-mono text-green-400">
            curl -X POST "https://api.divv.com/v1/bulk/stocks" \<br />
            &nbsp;&nbsp;-H "Authorization: Bearer YOUR_API_KEY" \<br />
            &nbsp;&nbsp;-H "Content-Type: application/json" \<br />
            &nbsp;&nbsp;-d '{`'{`}<br />
            &nbsp;&nbsp;&nbsp;&nbsp;"symbols": ["AAPL", "MSFT", "JNJ", "PG", "KO"],<br />
            &nbsp;&nbsp;&nbsp;&nbsp;"expand": "dividends"<br />
            &nbsp;&nbsp;{`}'`}'
          </code>
        </div>

        <h3 className="text-base font-semibold mb-3">Response</h3>
        <div className="bg-gray-900 rounded-md p-4 mb-6 overflow-x-auto">
          <pre className="text-sm font-mono text-gray-300">{`{
  "data": {
    "AAPL": {
      "symbol": "AAPL",
      "company": "Apple Inc.",
      "price": 175.43,
      "dividend_yield": 0.0052,
      "dividends": {
        "annual_amount": 0.92,
        "frequency": "quarterly",
        "ex_date": "2025-11-08"
      }
    },
    "MSFT": {
      "symbol": "MSFT",
      "company": "Microsoft Corporation",
      "price": 378.91,
      "dividend_yield": 0.0078,
      "dividends": {
        "annual_amount": 2.96,
        "frequency": "quarterly",
        "ex_date": "2025-11-20"
      }
    }
  },
  "errors": {
    "INVALID": "Symbol not found"
  },
  "summary": {
    "total_requested": 5,
    "successful": 4,
    "failed": 1
  }
}`}</pre>
        </div>
      </section>

      {/* Performance Benefits */}
      <section className="mb-12">
        <h3 className="text-base font-semibold mb-3">Performance Benefits</h3>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-sm font-semibold text-red-900 mb-2">❌ Without Bulk (100 stocks)</div>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• 100 API requests</li>
              <li>• 100 calls against rate limit</li>
              <li>• ~10-30 seconds total time</li>
              <li>• Complex error handling</li>
            </ul>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-md p-4">
            <div className="text-sm font-semibold text-green-900 mb-2">✅ With Bulk (100 stocks)</div>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• 1 API request</li>
              <li>• 1 call against rate limit</li>
              <li>• ~1-2 seconds total time</li>
              <li>• Built-in error handling</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="mb-12">
        <h3 className="text-base font-semibold mb-3">Common Use Cases</h3>
        <div className="space-y-3 text-sm text-gray-700">
          <div className="bg-gray-50 rounded-md p-3">
            <p className="font-semibold mb-1">Portfolio Tracking</p>
            <p className="text-gray-600">Fetch current prices and dividend data for your entire portfolio in one request</p>
          </div>
          <div className="bg-gray-50 rounded-md p-3">
            <p className="font-semibold mb-1">Screener Results</p>
            <p className="text-gray-600">Get detailed data for all stocks matching your screening criteria</p>
          </div>
          <div className="bg-gray-50 rounded-md p-3">
            <p className="font-semibold mb-1">Watchlist Updates</p>
            <p className="text-gray-600">Monitor multiple symbols simultaneously with minimal API usage</p>
          </div>
          <div className="bg-gray-50 rounded-md p-3">
            <p className="font-semibold mb-1">Data Analysis</p>
            <p className="text-gray-600">Download large datasets for backtesting or research</p>
          </div>
        </div>
      </section>

      {/* Upgrade CTA */}
      <section className="mb-12">
        <div className="bg-gradient-to-br from-purple-900 to-blue-900 rounded-2xl p-8 text-white text-center">
          <div className="text-3xl mb-3">🚀</div>
          <h3 className="text-2xl font-bold mb-3">Ready to Scale?</h3>
          <p className="text-blue-100 mb-6">
            Upgrade to Professional to access bulk endpoints and handle 1,000+ symbols per request
          </p>
          <a
            href="/pricing"
            className="inline-block px-8 py-3 bg-white text-purple-900 rounded-lg font-semibold hover:bg-blue-50 transition-all"
          >
            View Professional Pricing
          </a>
        </div>
      </section>
    </div>
  );
}
