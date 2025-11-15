'use client';

export default function SearchPage() {
  return (
    <div className="max-w-4xl">
      <h1 className="text-3xl font-semibold mb-4 pb-3 border-b border-gray-200">
        Search
      </h1>

      <p className="text-sm text-gray-700 mb-8">
        The Search endpoint provides powerful fuzzy search across stocks, ETFs, and trusts. Search by symbol, company name, or sector with intelligent ranking.
      </p>

      {/* Search Stocks Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Search stocks
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/search</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Search for stocks by symbol, company name, or sector using fuzzy matching. Results are intelligently ranked with exact matches prioritized.
        </p>

        <h3 className="text-base font-semibold mb-3">Parameters</h3>
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
                <td className="px-4 py-3 font-mono text-xs">q</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">
                  <span className="bg-red-100 text-red-700 text-xs px-1.5 py-0.5 rounded mr-2">required</span>
                  Search query (minimum 1 character)
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">type</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Filter by type: "stock", "etf", or "trust"</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">limit</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Maximum results (1-100, default: 20)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Example Request</h3>
        <div className="bg-gray-900 rounded-md p-4 mb-6 overflow-x-auto">
          <code className="text-sm font-mono text-green-400">
            curl "https://api.divv.com/v1/search?q=apple&limit=5" \<br />
            &nbsp;&nbsp;-H "Authorization: Bearer YOUR_API_KEY"
          </code>
        </div>

        <h3 className="text-base font-semibold mb-3">Response</h3>
        <div className="bg-gray-900 rounded-md p-4 mb-6 overflow-x-auto">
          <pre className="text-sm font-mono text-gray-300">{`{
  "results": [
    {
      "symbol": "AAPL",
      "company": "Apple Inc.",
      "exchange": "NASDAQ",
      "type": "stock",
      "sector": "Technology",
      "dividend_yield": 0.0052,
      "market_cap": 2850000000000,
      "score": 100
    },
    {
      "symbol": "APLE",
      "company": "Apple Hospitality REIT Inc",
      "exchange": "NYSE",
      "type": "trust",
      "sector": "Real Estate",
      "dividend_yield": 0.0675,
      "market_cap": 3200000000,
      "score": 85
    }
  ],
  "count": 2,
  "query": "apple"
}`}</pre>
        </div>

        <h3 className="text-base font-semibold mb-3">Search Features</h3>
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-2">
            <li><strong>Symbol Matching:</strong> Search by ticker symbol (e.g., "AAPL", "MSFT")</li>
            <li><strong>Company Name:</strong> Search by full or partial company name (e.g., "Apple", "Microsoft")</li>
            <li><strong>Sector Search:</strong> Find stocks by sector (e.g., "Technology", "Healthcare")</li>
            <li><strong>Fuzzy Matching:</strong> Tolerant of typos and partial matches</li>
            <li><strong>Smart Ranking:</strong> Exact symbol matches ranked highest, followed by company name matches</li>
          </ul>
        </div>

        <h3 className="text-base font-semibold mb-3">Use Cases</h3>
        <div className="space-y-3 text-sm text-gray-700">
          <div className="bg-gray-50 rounded-md p-3">
            <p className="font-semibold mb-1">Autocomplete Search Box</p>
            <p className="text-gray-600">Provide instant search suggestions as users type stock symbols or company names</p>
          </div>
          <div className="bg-gray-50 rounded-md p-3">
            <p className="font-semibold mb-1">Symbol Lookup</p>
            <p className="text-gray-600">Find the correct ticker symbol when you only know the company name</p>
          </div>
          <div className="bg-gray-50 rounded-md p-3">
            <p className="font-semibold mb-1">Sector Discovery</p>
            <p className="text-gray-600">Explore all stocks in a specific sector or industry</p>
          </div>
        </div>
      </section>
    </div>
  );
}
