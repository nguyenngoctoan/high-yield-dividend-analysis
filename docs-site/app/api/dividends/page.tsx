'use client';

export default function DividendsPage() {
  return (
    <div className="max-w-4xl">
      <h1 className="text-3xl font-semibold mb-4 pb-3 border-b border-gray-200">
        Dividends
      </h1>

      <p className="text-sm text-gray-700 mb-8">
        The Dividends endpoints provide access to dividend calendar events, historical dividend payments, and dividend growth metrics.
      </p>

      {/* Dividend Calendar Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Get dividend calendar
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/dividends/calendar</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Get upcoming dividend events (ex-dates, payment dates). Returns a list of future dividend events with optional filtering.
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
                <td className="px-4 py-3 font-mono text-xs">start_date</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Start date (YYYY-MM-DD)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">end_date</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">End date (YYYY-MM-DD)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">symbols</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Comma-separated symbols</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">min_yield</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">Minimum yield filter</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">limit</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Results per page (default 100, max 1000)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700">Returns a list of dividend events with ex-dates, payment dates, and amounts.</p>
        </div>
      </section>

      {/* Dividend History Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Get dividend history
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/dividends/history</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Get historical dividend payments across symbols. Returns a list of past dividend payments.
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
                <td className="px-4 py-3 font-mono text-xs">symbols</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Comma-separated symbols (required)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">start_date</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Start date</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">end_date</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">End date</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">limit</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Results per page (default 100, max 1000)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700">Returns a list of historical dividend payments.</p>
        </div>
      </section>

      {/* Stock Dividends Summary Endpoint */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Get stock dividend summary
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/stocks/{'{symbol}'}/dividends</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Get complete dividend data for a specific stock. Includes current info, next payment, history, and growth metrics.
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
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="px-4 py-3 font-mono text-xs">include_future</td>
                <td className="px-4 py-3 text-gray-600">boolean</td>
                <td className="px-4 py-3 text-gray-700">Include future scheduled dividends (default true)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">years</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Years of history (default 5)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700">Returns comprehensive dividend data including current info, next payment, historical payments, and growth metrics.</p>
        </div>
      </section>
    </div>
  );
}
