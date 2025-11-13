'use client';

export default function AnalyticsPage() {
  return (
    <div className="max-w-4xl">
      <h1 className="text-3xl font-semibold mb-4 pb-3 border-b border-gray-200">
        Analytics
      </h1>

      <p className="text-sm text-gray-700 mb-8">
        Portfolio analytics and dividend projections. Calculate dividend income, analyze portfolio composition, and project future returns.
      </p>

      {/* Portfolio Analysis Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-green-100 text-green-700 text-xs font-semibold px-2 py-1 rounded">POST</span>
          Analyze portfolio
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/analytics/portfolio</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Calculate portfolio dividend income projections. Analyzes a portfolio of dividend stocks and projects future income. Supports dividend reinvestment and annual contributions.
        </p>

        <h3 className="text-base font-semibold mb-3">Request Body</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <pre className="text-sm font-mono text-gray-800">
{`{
  "positions": [
    {"symbol": "AAPL", "shares": 100},
    {"symbol": "MSFT", "shares": 50}
  ],
  "projection_years": 5,
  "reinvest_dividends": true,
  "annual_contribution": 10000
}`}
          </pre>
        </div>

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
                <td className="px-4 py-3 font-mono text-xs">positions</td>
                <td className="px-4 py-3 text-gray-600">array</td>
                <td className="px-4 py-3 text-gray-700">Array of position objects with symbol and shares</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">projection_years</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Number of years to project (default 5)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">reinvest_dividends</td>
                <td className="px-4 py-3 text-gray-600">boolean</td>
                <td className="px-4 py-3 text-gray-700">Whether to reinvest dividends (default false)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">annual_contribution</td>
                <td className="px-4 py-3 text-gray-600">number</td>
                <td className="px-4 py-3 text-gray-700">Annual contribution amount (default 0)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700">Returns current portfolio metrics and year-by-year projections including dividend income, portfolio value, and yields.</p>
        </div>
      </section>
    </div>
  );
}
