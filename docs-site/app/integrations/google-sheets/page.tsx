'use client';

import { API_CONFIG } from '@/lib/config';

import Header from '@/components/Header';
import Link from 'next/link';

export default function GoogleSheetsIntegrationPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <div className="container mx-auto px-6 py-20">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-12">
            <Link href="/integrations" className="text-blue-600 hover:text-blue-700 mb-4 inline-flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Integrations
            </Link>
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              Google Sheets Integration
            </h1>
            <p className="text-xl text-gray-600">
              Use <code className="px-2 py-1 bg-gray-100 rounded text-green-600 font-mono">=DIVV()</code> just like GOOGLEFINANCE() - same syntax, better dividend data
            </p>
          </div>

          {/* Free Forever Banner */}
          <div className="bg-gradient-to-br from-green-600 to-blue-600 rounded-2xl p-8 border-2 border-green-700 mb-8 text-white text-center">
            <div className="text-5xl mb-4">🎉</div>
            <h2 className="text-3xl font-bold mb-3">
              Track Prices & Dividends for Free. Forever.
            </h2>
            <p className="text-xl text-green-100 mb-4">
              Most dividend investors never need to pay
            </p>
            <div className="bg-white/10 backdrop-blur rounded-lg p-6 max-w-2xl mx-auto mb-4">
              <div className="grid md:grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-3xl font-bold">20</div>
                  <div className="text-sm text-green-100">stocks tracked</div>
                </div>
                <div>
                  <div className="text-3xl font-bold">5x/day</div>
                  <div className="text-sm text-green-100">price checks</div>
                </div>
                <div>
                  <div className="text-3xl font-bold">$0</div>
                  <div className="text-sm text-green-100">forever</div>
                </div>
              </div>
              <p className="text-sm text-green-100 mt-4">
                Free tier: 10,000 API calls/month • Your 20-stock portfolio uses ~3,000/month
              </p>
            </div>
            <div className="bg-white/10 backdrop-blur rounded-lg p-4 max-w-2xl mx-auto">
              <p className="text-sm font-semibold mb-2">Free tier includes:</p>
              <div className="flex flex-wrap gap-2 justify-center">
                <span className="px-3 py-1 bg-white/20 rounded-full text-sm">Price</span>
                <span className="px-3 py-1 bg-white/20 rounded-full text-sm">Open</span>
                <span className="px-3 py-1 bg-white/20 rounded-full text-sm">High/Low</span>
                <span className="px-3 py-1 bg-white/20 rounded-full text-sm">Dividend Yield</span>
                <span className="px-3 py-1 bg-white/20 rounded-full text-sm">Dividend Amount</span>
              </div>
              <p className="text-xs text-green-100 mt-3">
                Want more? <Link href="/pricing" className="underline font-semibold">Upgrade for full access</Link> (PE ratio, volume, market cap, dividend history, etc.)
              </p>
            </div>
          </div>

          {/* Quick Example */}
          <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-2xl p-8 border-2 border-green-500 mb-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Try It Now</h2>

            {/* Current Data Examples */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Current Data (Free Tier)</h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Instead of this:</h4>
                  <pre className="bg-white p-4 rounded-lg border border-gray-300 text-sm font-mono text-gray-700">
{`=GOOGLEFINANCE("AAPL", "price")
=GOOGLEFINANCE("AAPL", "high")
=GOOGLEFINANCE("AAPL", "low")`}
                  </pre>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-green-700 mb-2">Use this:</h4>
                  <pre className="bg-white p-4 rounded-lg border border-green-500 text-sm font-mono text-green-700">
{`=DIVV("AAPL", "price")
=DIVV("AAPL", "dayHigh")
=DIVV("AAPL", "dividendYield")`}
                  </pre>
                </div>
              </div>
            </div>

            {/* Historical Data Examples */}
            <div className="border-t border-gray-300 pt-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Historical Data (Paid Tier)</h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">GOOGLEFINANCE syntax:</h4>
                  <pre className="bg-white p-4 rounded-lg border border-gray-300 text-sm font-mono text-gray-700">
{`=GOOGLEFINANCE("AAPL", "price",
  DATE(2024,1,15))`}
                  </pre>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-green-700 mb-2">DIVV syntax:</h4>
                  <pre className="bg-white p-4 rounded-lg border border-green-500 text-sm font-mono text-green-700">
{`=DIVV("AAPL", "close",
  "2024-01-15")`}
                  </pre>
                </div>
              </div>
            </div>

            <p className="text-sm text-gray-600 mt-6 text-center">
              💎 Free tier includes: price, open, dayHigh, dayLow, previousClose, dividendYield, dividendAmount<br/>
              📅 Historical data requires <Link href="/pricing" className="text-blue-600 underline">Starter tier ($9/mo)</Link> or higher
            </p>
          </div>

          {/* Installation Steps */}
          <div className="bg-white rounded-2xl p-8 border-2 border-gray-200 mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Installation (5 minutes)</h2>

            <div className="space-y-8">
              {/* Step 1 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                  1
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Open Google Sheets Apps Script</h3>
                  <p className="text-gray-600 mb-3">
                    In your Google Sheet, go to <strong>Extensions → Apps Script</strong>
                  </p>
                  <img src="/screenshots/sheets-step1.png" alt="Step 1" className="rounded-lg border border-gray-300 w-full" />
                </div>
              </div>

              {/* Step 2 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                  2
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Download the DIVV Script</h3>
                  <p className="text-gray-600 mb-3">
                    Download our ready-to-use Google Apps Script file
                  </p>
                  <a
                    href="/DIVV.gs"
                    download
                    className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-all"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                    </svg>
                    Download DIVV.gs
                  </a>
                </div>
              </div>

              {/* Step 3 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                  3
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Copy the Script Code</h3>
                  <p className="text-gray-600 mb-3">
                    Open the downloaded file, select all (Cmd+A / Ctrl+A), and copy the code
                  </p>
                </div>
              </div>

              {/* Step 4 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                  4
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Paste into Apps Script</h3>
                  <p className="text-gray-600 mb-3">
                    Delete any existing code in the Apps Script editor and paste the DIVV code
                  </p>
                </div>
              </div>

              {/* Step 5 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                  5
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Configure API Endpoint</h3>
                  <p className="text-gray-600 mb-3">
                    Update the <code className="px-2 py-1 bg-gray-100 rounded font-mono text-sm">API_BASE_URL</code> at the top of the script:
                  </p>
                  <pre className="bg-gray-900 p-4 rounded-lg text-white font-mono text-sm overflow-x-auto">
{`// For production (recommended)
const API_BASE_URL = 'https://api.divv.com';

// For local testing
const API_BASE_URL = {API_CONFIG.baseUrl};`}
                  </pre>
                </div>
              </div>

              {/* Step 6 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                  6
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Save and Test</h3>
                  <p className="text-gray-600 mb-3">
                    Click <strong>Save</strong> (💾 icon), then go back to your sheet and try:
                  </p>
                  <pre className="bg-gray-900 p-4 rounded-lg text-emerald-400 font-mono text-sm">
                    =DIVV("AAPL", "price")
                  </pre>
                </div>
              </div>
            </div>
          </div>

          {/* Available Functions */}
          <div className="bg-white rounded-2xl p-8 border-2 border-gray-200 mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Available Functions</h2>

            <div className="space-y-6">
              {/* DIVV() */}
              <div className="border-l-4 border-green-500 pl-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  <code className="text-green-600">=DIVV(symbol, attribute, [startDate], [endDate])</code>
                </h3>
                <p className="text-gray-600 mb-3">
                  Get current or historical stock data with GOOGLEFINANCE() compatible syntax
                </p>

                {/* Current Data Examples */}
                <div className="bg-gray-50 p-4 rounded-lg mb-4">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Current Data (Free Tier):</p>
                  <pre className="text-sm font-mono text-gray-700">
{`=DIVV("AAPL", "price")           → 175.43
=DIVV("MSFT", "dividendYield")   → 0.89%
=DIVV("JNJ", "dividendAmount")   → 4.76
=DIVV("PG", "dayHigh")           → 168.85`}
                  </pre>
                </div>

                {/* Historical Data Examples */}
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <p className="text-sm font-semibold text-blue-800 mb-2">
                    📅 Historical Data (Paid Tier - $9/mo):
                  </p>
                  <pre className="text-sm font-mono text-gray-700">
{`// Single date
=DIVV("AAPL", "close", "2024-01-15")         → 185.59
=DIVV("AAPL", "close", DATE(2024,1,15))     → 185.59

// Date range (returns 2D array)
=DIVV("AAPL", "close", "2024-01-01", "2024-01-31")
// Returns: [Date, Close] array for charting

// Cell reference
=DIVV("AAPL", "close", A1)  // A1 = 2024-01-15`}
                  </pre>
                  <p className="text-xs text-blue-700 mt-2">
                    <Link href="/pricing" className="underline font-semibold">Upgrade to unlock</Link> historical data
                  </p>
                </div>
              </div>

              {/* DIVVBULK() */}
              <div className="border-l-4 border-blue-500 pl-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  <code className="text-blue-600">=DIVVBULK(symbols, attribute)</code>
                </h3>
                <p className="text-gray-600 mb-3">
                  Get data for multiple stocks at once (more efficient)
                </p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Example:</p>
                  <pre className="text-sm font-mono text-gray-700">
{`=DIVVBULK(A2:A10, "price")
// Where A2:A10 contains: AAPL, MSFT, GOOGL, etc.`}
                  </pre>
                </div>
              </div>

              {/* DIVVDIVIDENDS() */}
              <div className="border-l-4 border-purple-500 pl-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  <code className="text-purple-600">=DIVVDIVIDENDS(symbol, limit)</code>
                </h3>
                <p className="text-gray-600 mb-3">
                  Get dividend history for a stock
                </p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Example:</p>
                  <pre className="text-sm font-mono text-gray-700">
{`=DIVVDIVIDENDS("AAPL", 12)
// Returns last 12 dividends with dates and amounts`}
                  </pre>
                </div>
              </div>

              {/* DIVVARISTOCRAT() */}
              <div className="border-l-4 border-yellow-500 pl-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  <code className="text-yellow-600">=DIVVARISTOCRAT(symbol, returnYears)</code>
                </h3>
                <p className="text-gray-600 mb-3">
                  Check if stock is a Dividend Aristocrat (25+ years of increases)
                </p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Examples:</p>
                  <pre className="text-sm font-mono text-gray-700">
{`=DIVVARISTOCRAT("JNJ")        → TRUE (is Aristocrat)
=DIVVARISTOCRAT("JNJ", TRUE)  → 61 (years of increases)
=DIVVARISTOCRAT("TSLA")       → FALSE`}
                  </pre>
                </div>
              </div>
            </div>
          </div>

          {/* Supported Attributes */}
          <div className="bg-white rounded-2xl p-8 border-2 border-gray-200 mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Supported Attributes</h2>
            <p className="text-gray-600 mb-6">
              All GOOGLEFINANCE() attributes are supported, plus additional dividend-specific fields:
            </p>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-3">GOOGLEFINANCE() Compatible</h3>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-gray-100 rounded text-gray-700 font-mono text-xs">price</code>
                    <span className="text-gray-600">Current price</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-gray-100 rounded text-gray-700 font-mono text-xs">high52</code>
                    <span className="text-gray-600">52-week high</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-gray-100 rounded text-gray-700 font-mono text-xs">low52</code>
                    <span className="text-gray-600">52-week low</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-gray-100 rounded text-gray-700 font-mono text-xs">pe</code>
                    <span className="text-gray-600">P/E ratio</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-gray-100 rounded text-gray-700 font-mono text-xs">eps</code>
                    <span className="text-gray-600">Earnings per share</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-gray-100 rounded text-gray-700 font-mono text-xs">marketcap</code>
                    <span className="text-gray-600">Market capitalization</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-gray-100 rounded text-gray-700 font-mono text-xs">volume</code>
                    <span className="text-gray-600">Trading volume</span>
                  </li>
                </ul>
              </div>

              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-3">Dividend-Specific</h3>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-green-100 rounded text-green-700 font-mono text-xs">dividendYield</code>
                    <span className="text-gray-600">Current yield %</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-green-100 rounded text-green-700 font-mono text-xs">dividendAmount</code>
                    <span className="text-gray-600">Annual dividend</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-green-100 rounded text-green-700 font-mono text-xs">priceAvg50</code>
                    <span className="text-gray-600">50-day MA</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-green-100 rounded text-green-700 font-mono text-xs">priceAvg200</code>
                    <span className="text-gray-600">200-day MA</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-green-100 rounded text-green-700 font-mono text-xs">yearHigh</code>
                    <span className="text-gray-600">52-week high</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <code className="px-2 py-1 bg-green-100 rounded text-green-700 font-mono text-xs">yearLow</code>
                    <span className="text-gray-600">52-week low</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-800">
                <strong>💡 Tip:</strong> You can use either GOOGLEFINANCE() style names (e.g., <code>high52</code>) or Divv style names (e.g., <code>yearHigh</code>) - both work!
              </p>
            </div>
          </div>

          {/* Advanced Features */}
          <div className="bg-white rounded-2xl p-8 border-2 border-gray-200 mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Advanced Features</h2>

            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">🚀 Automatic Caching</h3>
                <p className="text-gray-600">
                  Data is cached for 5 minutes to improve performance and reduce API calls. You can adjust this in the script configuration.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">🔄 Retry Logic</h3>
                <p className="text-gray-600">
                  Automatically retries failed requests up to 3 times with exponential backoff. Handles rate limiting gracefully.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">🔑 API Key Support</h3>
                <p className="text-gray-600 mb-2">
                  Add your API key to unlock higher rate limits and premium features:
                </p>
                <pre className="bg-gray-900 p-4 rounded-lg text-white font-mono text-sm">
                  const API_KEY = 'your-api-key-here';
                </pre>
              </div>

              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">🧹 Clear Cache</h3>
                <p className="text-gray-600 mb-2">
                  Need fresh data? Run this in the Apps Script editor:
                </p>
                <pre className="bg-gray-900 p-4 rounded-lg text-white font-mono text-sm">
                  clearDivvCache()
                </pre>
              </div>
            </div>
          </div>

          {/* Example Dashboard */}
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-8 border-2 border-purple-200 mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Example: Dividend Dashboard</h2>
            <p className="text-gray-600 mb-6">
              Here's how to build a simple dividend tracking dashboard in Google Sheets:
            </p>

            <div className="bg-white rounded-lg p-6 border border-gray-300">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-300">
                    <th className="text-left p-2 font-bold">Symbol</th>
                    <th className="text-left p-2 font-bold">Price</th>
                    <th className="text-left p-2 font-bold">Yield</th>
                    <th className="text-left p-2 font-bold">Aristocrat?</th>
                  </tr>
                </thead>
                <tbody className="font-mono text-xs">
                  <tr className="border-b border-gray-200">
                    <td className="p-2">AAPL</td>
                    <td className="p-2 text-green-600">=DIVV(A2,"price")</td>
                    <td className="p-2 text-green-600">=DIVV(A2,"dividendYield")</td>
                    <td className="p-2 text-green-600">=DIVVARISTOCRAT(A2)</td>
                  </tr>
                  <tr className="border-b border-gray-200">
                    <td className="p-2">JNJ</td>
                    <td className="p-2 text-green-600">=DIVV(A3,"price")</td>
                    <td className="p-2 text-green-600">=DIVV(A3,"dividendYield")</td>
                    <td className="p-2 text-green-600">=DIVVARISTOCRAT(A3)</td>
                  </tr>
                  <tr>
                    <td className="p-2">PG</td>
                    <td className="p-2 text-green-600">=DIVV(A4,"price")</td>
                    <td className="p-2 text-green-600">=DIVV(A4,"dividendYield")</td>
                    <td className="p-2 text-green-600">=DIVVARISTOCRAT(A4)</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Troubleshooting */}
          <div className="bg-white rounded-2xl p-8 border-2 border-gray-200">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Troubleshooting</h2>

            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-red-600 mb-2">#ERROR: Invalid symbol</h3>
                <p className="text-gray-600">
                  Check that the symbol is correct and exists in our database. Symbols must be in UPPERCASE.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-bold text-red-600 mb-2">#ERROR: API error: 429</h3>
                <p className="text-gray-600">
                  You've hit the rate limit. The function will automatically retry. Consider upgrading your plan or using DIVVBULK() for better efficiency.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-bold text-red-600 mb-2">Function not recognized</h3>
                <p className="text-gray-600">
                  Make sure you saved the script and refreshed your Google Sheet. Try closing and reopening the sheet.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-bold text-red-600 mb-2">Authorization required</h3>
                <p className="text-gray-600">
                  The first time you use the function, Google will ask for authorization. Click "Review Permissions" and grant access.
                </p>
              </div>
            </div>
          </div>

          {/* CTA */}
          <div className="mt-12 text-center">
            <Link
              href="/api"
              className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg font-bold hover:from-green-700 hover:to-blue-700 transition-all shadow-lg text-lg"
            >
              <span>View Full API Documentation</span>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
