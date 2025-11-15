'use client';

export default function ETFsPage() {
  return (
    <div className="max-w-4xl">
      <h1 className="text-3xl font-semibold mb-4 pb-3 border-b border-gray-200">
        ETFs
      </h1>

      <p className="text-sm text-gray-700 mb-8">
        The ETFs endpoints provide comprehensive data on exchange-traded funds, including AUM, expense ratios, investment strategies, and detailed holdings information.
      </p>

      {/* Get ETF Details Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Get ETF details
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/etfs/{'{symbol}'}</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Retrieve comprehensive information about an ETF including assets under management, expense ratio, investment strategy, and holdings count.
        </p>

        <h3 className="text-base font-semibold mb-3">Path Parameters</h3>
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
                <td className="px-4 py-3 font-mono text-xs">symbol</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">
                  <span className="bg-red-100 text-red-700 text-xs px-1.5 py-0.5 rounded mr-2">required</span>
                  ETF ticker symbol (e.g., "SPY", "JEPI", "SCHD")
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Example Request</h3>
        <div className="bg-gray-900 rounded-md p-4 mb-6 overflow-x-auto">
          <code className="text-sm font-mono text-green-400">
            curl "https://api.divv.com/v1/etfs/JEPI" \<br />
            &nbsp;&nbsp;-H "Authorization: Bearer YOUR_API_KEY"
          </code>
        </div>

        <h3 className="text-base font-semibold mb-3">Response</h3>
        <div className="bg-gray-900 rounded-md p-4 mb-6 overflow-x-auto">
          <pre className="text-sm font-mono text-gray-300">{`{
  "symbol": "JEPI",
  "name": "JPMorgan Equity Premium Income ETF",
  "expense_ratio": 0.0035,
  "aum": 28500000000,
  "aum_millions": 28500.0,
  "investment_strategy": "covered_call",
  "related_stock": "SPX",
  "dividend_yield": 0.0812,
  "holdings_count": 127,
  "holdings_updated_at": "2025-11-15T00:00:00Z"
}`}</pre>
        </div>

        <h3 className="text-base font-semibold mb-3">Response Fields</h3>
        <div className="border border-gray-200 rounded-md mb-6">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Field</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Type</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="px-4 py-3 font-mono text-xs">symbol</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">ETF ticker symbol</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">name</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Full ETF name</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">expense_ratio</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">Annual expense ratio (0.0035 = 0.35%)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">aum</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Assets under management in USD</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">aum_millions</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">AUM in millions (for easier reading)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">investment_strategy</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Strategy type: "covered_call", "dividend_growth", "high_yield", etc.</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">related_stock</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Underlying index or stock (for covered call ETFs)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">dividend_yield</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">Current dividend yield</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">holdings_count</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Number of holdings in the ETF</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">holdings_updated_at</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Last update timestamp for holdings data</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Get ETF Holdings Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Get ETF holdings
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/etfs/{'{symbol}'}/holdings</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Retrieve the complete list of holdings for an ETF, including weights and share counts.
        </p>

        <h3 className="text-base font-semibold mb-3">Path Parameters</h3>
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
                <td className="px-4 py-3 font-mono text-xs">symbol</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">
                  <span className="bg-red-100 text-red-700 text-xs px-1.5 py-0.5 rounded mr-2">required</span>
                  ETF ticker symbol
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Query Parameters</h3>
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
                <td className="px-4 py-3 font-mono text-xs">limit</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Maximum holdings to return (default: 100)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">min_weight</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">Minimum position weight (e.g., 0.01 for 1%)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Example Request</h3>
        <div className="bg-gray-900 rounded-md p-4 mb-6 overflow-x-auto">
          <code className="text-sm font-mono text-green-400">
            curl "https://api.divv.com/v1/etfs/SCHD/holdings?limit=10" \<br />
            &nbsp;&nbsp;-H "Authorization: Bearer YOUR_API_KEY"
          </code>
        </div>

        <h3 className="text-base font-semibold mb-3">Response</h3>
        <div className="bg-gray-900 rounded-md p-4 mb-6 overflow-x-auto">
          <pre className="text-sm font-mono text-gray-300">{`{
  "etf_symbol": "SCHD",
  "holdings": [
    {
      "symbol": "CSCO",
      "company": "Cisco Systems Inc",
      "weight": 0.0425,
      "shares": 12500000,
      "market_value": 625000000
    },
    {
      "symbol": "PEP",
      "company": "PepsiCo Inc",
      "weight": 0.0412,
      "shares": 3800000,
      "market_value": 618000000
    }
  ],
  "count": 2,
  "total_holdings": 104,
  "updated_at": "2025-11-15T00:00:00Z"
}`}</pre>
        </div>
      </section>

      {/* Use Cases */}
      <section className="mb-12">
        <h3 className="text-base font-semibold mb-3">Common Use Cases</h3>
        <div className="space-y-3 text-sm text-gray-700">
          <div className="bg-gray-50 rounded-md p-3">
            <p className="font-semibold mb-1">Income ETF Analysis</p>
            <p className="text-gray-600">Compare covered call ETFs (JEPI, JEPQ, QYLD) by yield, expense ratio, and AUM</p>
          </div>
          <div className="bg-gray-50 rounded-md p-3">
            <p className="font-semibold mb-1">Portfolio Overlap Analysis</p>
            <p className="text-gray-600">Check holdings to identify overlap between ETFs in your portfolio</p>
          </div>
          <div className="bg-gray-50 rounded-md p-3">
            <p className="font-semibold mb-1">Strategy Comparison</p>
            <p className="text-gray-600">Filter ETFs by investment strategy to find dividend growth vs. high yield funds</p>
          </div>
        </div>
      </section>

      {/* Supported Investment Strategies */}
      <section className="mb-12">
        <h3 className="text-base font-semibold mb-3">Investment Strategies</h3>
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <ul className="grid grid-cols-2 gap-2 text-sm text-gray-700">
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              <code className="text-xs">covered_call</code>
            </li>
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              <code className="text-xs">dividend_growth</code>
            </li>
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              <code className="text-xs">high_yield</code>
            </li>
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              <code className="text-xs">dividend_aristocrats</code>
            </li>
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              <code className="text-xs">index</code>
            </li>
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              <code className="text-xs">sector</code>
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
}
