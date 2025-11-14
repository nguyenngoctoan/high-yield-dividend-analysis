'use client';

export default function StocksPage() {
  return (
    <div className="max-w-4xl">
      <h1 className="text-3xl font-semibold mb-4 pb-3 border-b border-gray-200">
        Stocks
      </h1>

      <p className="text-sm text-gray-700 mb-8">
        The Stocks endpoints provide access to stock and ETF data, including dividend information, company profiles, and pricing data.
      </p>

      {/* List Stocks Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          List stocks
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/stocks</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          List all available stocks with optional filtering. Returns a paginated list of stocks matching the specified criteria.
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
                <td className="px-4 py-3 font-mono text-xs">has_dividends</td>
                <td className="px-4 py-3 text-gray-600">boolean</td>
                <td className="px-4 py-3 text-gray-700">Only show dividend-paying stocks</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">min_yield</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">Minimum dividend yield %</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">max_yield</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">Maximum dividend yield %</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">sector</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Filter by sector</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">exchange</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Filter by exchange (NASDAQ, NYSE, etc.)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">type</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">"stock", "etf", or "trust"</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">limit</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Results per page (max 1000)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">cursor</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Pagination cursor</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700">Returns a list object containing stock data.</p>
        </div>
      </section>

      {/* Get Stock Details Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Get stock details
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/stocks/{'{symbol}'}</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Retrieve detailed information for a specific stock. Supports expansion of related data via the expand parameter.
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
            <tbody>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">symbol</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Stock symbol (e.g., "AAPL")</td>
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
            <tbody>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">expand</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Comma-separated fields to expand: company,dividends,prices</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700">Returns a stock detail object with company info, pricing data, and dividend information.</p>
        </div>
      </section>

      {/* Get Stock Fundamentals Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Get stock fundamentals
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/stocks/{'{symbol}'}/fundamentals</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Get detailed fundamental metrics for a stock. Returns company fundamentals including market cap, P/E ratio, sector info, and more.
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
            <tbody>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">symbol</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Stock symbol (e.g., "AAPL")</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700 mb-3">Returns a fundamentals object with the following fields:</p>
          <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
            <li>Market capitalization</li>
            <li>P/E ratio</li>
            <li>Payout ratio</li>
            <li>Employee count</li>
            <li>IPO date</li>
            <li>Sector & industry</li>
            <li>Website URL</li>
            <li>Country</li>
          </ul>
        </div>
      </section>

      {/* Get Dividend Metrics Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Get dividend metrics
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/stocks/{'{symbol}'}/metrics</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Get detailed dividend metrics and consistency data. Returns dividend yield, growth rates, payout ratio, and consistency metrics including Dividend Aristocrat/King status.
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
            <tbody>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">symbol</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Stock symbol (e.g., "JNJ", "T")</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700 mb-3">Returns dividend metrics including:</p>
          <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
            <li>Current dividend yield</li>
            <li>Annual dividend amount</li>
            <li>Payment frequency</li>
            <li>Payout ratio</li>
            <li>5-year growth rate</li>
            <li><strong>Consecutive years of increases</strong> - Track dividend growth streaks</li>
            <li><strong>Consecutive payment count</strong> - Total dividend payments</li>
            <li><strong>is_dividend_aristocrat</strong> - 25+ years of consecutive increases</li>
            <li><strong>is_dividend_king</strong> - 50+ years of consecutive increases</li>
          </ul>
        </div>
      </section>

      {/* Get Stock Splits Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Get stock split history
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/stocks/{'{symbol}'}/splits</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Get historical stock split events for a symbol. Returns all stock splits with split ratios and dates.
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
            <tbody>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">symbol</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Stock symbol</td>
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
            <tbody>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">limit</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Max results (default 50, max 200)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700">Returns a list of stock splits with date, ratio, and split factors.</p>
        </div>
      </section>
    </div>
  );
}
