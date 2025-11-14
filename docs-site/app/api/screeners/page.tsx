'use client';

export default function ScreenersPage() {
  return (
    <div className="max-w-4xl">
      <h1 className="text-3xl font-semibold mb-4 pb-3 border-b border-gray-200">
        Screeners
      </h1>

      <p className="text-sm text-gray-700 mb-8">
        Pre-built stock screeners for dividend investors. These endpoints provide curated lists of stocks matching specific dividend criteria.
      </p>

      {/* High-Yield Screener */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          High-yield screener
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/screeners/high-yield</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Pre-built screener for high-yield dividend stocks. Returns stocks with yields above the minimum threshold.
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
                <td className="px-4 py-3 font-mono text-xs">min_yield</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">Minimum yield % (default 4.0)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">min_market_cap</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Minimum market cap</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">sectors</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Comma-separated sectors</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">exchanges</td>
                <td className="px-4 py-3 text-gray-600">string</td>
                <td className="px-4 py-3 text-gray-700">Comma-separated exchanges</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">exclude_etfs</td>
                <td className="px-4 py-3 text-gray-600">boolean</td>
                <td className="px-4 py-3 text-gray-700">Exclude ETFs (default false)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">limit</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Results limit (default 100, max 1000)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700">Returns a screener response with matching stocks sorted by yield.</p>
        </div>
      </section>

      {/* Monthly Payers Screener */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Monthly dividend payers
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/screeners/monthly-payers</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Screener for stocks/ETFs that pay monthly dividends. Returns stocks with monthly dividend frequency.
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
                <td className="px-4 py-3 font-mono text-xs">min_yield</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">Minimum yield % (default 0.0)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">limit</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Results limit (default 100, max 1000)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700">Returns a list of monthly dividend paying stocks sorted by yield.</p>
        </div>
      </section>

      {/* Dividend Aristocrats Screener */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Dividend Aristocrats screener
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/screeners/dividend-aristocrats</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Find Dividend Aristocrats - stocks with 25+ years of consecutive dividend increases. These are S&P 500 companies with a proven track record of annually increasing dividends.
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
                <td className="px-4 py-3 font-mono text-xs">min_yield</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">Minimum yield % (default 0)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">limit</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Results limit (default 100, max 1000)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700 mb-3">Returns stocks with 25+ years of consecutive dividend increases, including:</p>
          <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
            <li>Symbol and company name</li>
            <li>Current dividend yield</li>
            <li>Stock price</li>
            <li>Market capitalization</li>
            <li>Payout ratio</li>
            <li><strong>Consecutive years of increases</strong> - Number of years with dividend growth</li>
          </ul>
        </div>
      </section>

      {/* Dividend Kings Screener */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          Dividend Kings screener
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/screeners/dividend-kings</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Find Dividend Kings - elite stocks with 50+ years of consecutive dividend increases. These are the most reliable dividend payers with half a century of consistent dividend growth.
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
                <td className="px-4 py-3 font-mono text-xs">min_yield</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">Minimum yield % (default 0)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">limit</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Results limit (default 50, max 500)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700">Returns stocks with 50+ years of consecutive dividend increases, with the same data fields as the Dividend Aristocrats screener.</p>
        </div>
      </section>

      {/* High Dividend Growth Screener */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">GET</span>
          High dividend growth screener
        </h2>

        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <code className="text-sm font-mono text-gray-800">/v1/screeners/high-growth-dividends</code>
        </div>

        <p className="text-sm text-gray-700 mb-6">
          Find dividend growth stocks with strong 5-year dividend growth rates. Focuses on companies that are consistently growing their dividends at an above-average pace.
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
                <td className="px-4 py-3 font-mono text-xs">min_growth</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">Minimum 5-year growth rate % (default 10.0)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">min_yield</td>
                <td className="px-4 py-3 text-gray-600">float</td>
                <td className="px-4 py-3 text-gray-700">Minimum current yield % (default 2.0)</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">limit</td>
                <td className="px-4 py-3 text-gray-600">integer</td>
                <td className="px-4 py-3 text-gray-700">Results limit (default 100, max 1000)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className="text-base font-semibold mb-3">Returns</h3>
        <div className="bg-gray-50 rounded-md p-4 mb-6">
          <p className="text-sm text-gray-700 mb-3">Returns stocks with strong dividend growth, including:</p>
          <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
            <li>Symbol and company name</li>
            <li>Current dividend yield</li>
            <li>Stock price</li>
            <li>Market capitalization</li>
            <li>Payout ratio</li>
            <li><strong>5-year dividend growth rate</strong> - Annualized growth percentage</li>
          </ul>
        </div>
      </section>
    </div>
  );
}
