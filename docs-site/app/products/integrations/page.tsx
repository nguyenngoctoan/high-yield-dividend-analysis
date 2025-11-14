import Link from 'next/link'
import { Table, Download, Zap, TrendingUp, CheckCircle, ArrowRight, FileSpreadsheet } from 'lucide-react'

export default function IntegrationsProductPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Hero Section */}
      <section className="px-6 py-20 bg-gradient-to-r from-green-600 to-green-700 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-green-500/30 px-4 py-2 rounded-full text-sm mb-6">
            <Table className="w-4 h-4" />
            <span>Spreadsheet Integrations</span>
          </div>
          <h1 className="text-5xl font-bold mb-6">
            Divv Data in Your Spreadsheets
          </h1>
          <p className="text-xl text-green-100 mb-8">
            Access comprehensive dividend data directly in Excel or Google Sheets with custom DIVV functions.
            Like YAHOOFINANCE() or GOOGLEFINANCE(), but built specifically for dividend investors.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link
              href="#download"
              className="px-8 py-3 bg-white text-green-600 rounded-lg font-semibold hover:bg-green-50 transition-colors inline-flex items-center gap-2"
            >
              <Download className="w-5 h-5" />
              Download Add-ons
            </Link>
            <Link
              href="#examples"
              className="px-8 py-3 bg-green-500 text-white rounded-lg font-semibold hover:bg-green-400 transition-colors"
            >
              See Examples
            </Link>
          </div>
        </div>
      </section>

      {/* Quick Demo */}
      <section className="px-6 py-16 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-900 mb-4">
            Simple Functions, Powerful Results
          </h2>
          <p className="text-lg text-slate-600">
            Just type a formula and get instant access to dividend data
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden">
          {/* Spreadsheet Header */}
          <div className="bg-slate-50 px-6 py-3 border-b border-slate-200 flex items-center gap-4">
            <FileSpreadsheet className="w-5 h-5 text-slate-600" />
            <span className="font-semibold text-slate-700">Portfolio Tracker.xlsx</span>
          </div>

          {/* Spreadsheet Grid */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-slate-100 border-b border-slate-200">
                  <th className="px-4 py-3 text-left text-sm font-semibold text-slate-600 w-12"></th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">A</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">B</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">C</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">D</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">E</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">F</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                <tr className="bg-slate-50">
                  <td className="px-4 py-3 text-sm font-semibold text-slate-600">1</td>
                  <td className="px-4 py-3 text-sm font-semibold text-slate-900">Symbol</td>
                  <td className="px-4 py-3 text-sm font-semibold text-slate-900">Name</td>
                  <td className="px-4 py-3 text-sm font-semibold text-slate-900">Price</td>
                  <td className="px-4 py-3 text-sm font-semibold text-slate-900">Yield</td>
                  <td className="px-4 py-3 text-sm font-semibold text-slate-900">Annual Div</td>
                  <td className="px-4 py-3 text-sm font-semibold text-slate-900">Next Date</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm font-semibold text-slate-600">2</td>
                  <td className="px-4 py-3 text-sm text-slate-900">AAPL</td>
                  <td className="px-4 py-3 text-sm text-blue-600 font-mono">=DIVV_NAME(A2)</td>
                  <td className="px-4 py-3 text-sm text-blue-600 font-mono">=DIVV_PRICE(A2)</td>
                  <td className="px-4 py-3 text-sm text-blue-600 font-mono">=DIVV_YIELD(A2)</td>
                  <td className="px-4 py-3 text-sm text-blue-600 font-mono">=DIVV_ANNUAL(A2)</td>
                  <td className="px-4 py-3 text-sm text-blue-600 font-mono">=DIVV_NEXT_DATE(A2)</td>
                </tr>
                <tr className="bg-slate-50">
                  <td className="px-4 py-3 text-sm font-semibold text-slate-600">3</td>
                  <td className="px-4 py-3 text-sm text-slate-900">AAPL</td>
                  <td className="px-4 py-3 text-sm text-slate-700">Apple Inc.</td>
                  <td className="px-4 py-3 text-sm text-slate-700">$150.25</td>
                  <td className="px-4 py-3 text-sm text-green-700">0.52%</td>
                  <td className="px-4 py-3 text-sm text-slate-700">$0.96</td>
                  <td className="px-4 py-3 text-sm text-slate-700">2025-02-08</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm font-semibold text-slate-600">4</td>
                  <td className="px-4 py-3 text-sm text-slate-900">XYLD</td>
                  <td className="px-4 py-3 text-sm text-slate-700">Global X S&P 500...</td>
                  <td className="px-4 py-3 text-sm text-slate-700">$42.15</td>
                  <td className="px-4 py-3 text-sm text-green-700">11.8%</td>
                  <td className="px-4 py-3 text-sm text-slate-700">$4.97</td>
                  <td className="px-4 py-3 text-sm text-slate-700">2025-11-20</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-6 text-center">
          <p className="text-slate-600">
            That's it! Type a formula, get the data. Updates automatically.
          </p>
        </div>
      </section>

      {/* Platform Support */}
      <section className="px-6 py-16 bg-slate-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-slate-900 mb-12 text-center">
            Works in Your Favorite Spreadsheet App
          </h2>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Excel */}
            <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-200">
              <div className="flex items-center gap-4 mb-6">
                <div className="p-3 bg-green-100 rounded-lg">
                  <FileSpreadsheet className="w-8 h-8 text-green-600" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-slate-900">Microsoft Excel</h3>
                  <p className="text-sm text-slate-600">Windows & Mac</p>
                </div>
              </div>

              <p className="text-slate-600 mb-6">
                VBA-based add-in that works with Excel 2010 and later. Simple .bas file import, no external dependencies.
              </p>

              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Works offline once data is cached</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>20+ custom DIVV_ functions</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Easy installation (3 steps)</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Manual or auto-refresh</span>
                </li>
              </ul>

              <Link
                href="#excel-download"
                className="block w-full text-center px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors"
              >
                Download for Excel
              </Link>
            </div>

            {/* Google Sheets */}
            <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-200">
              <div className="flex items-center gap-4 mb-6">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Table className="w-8 h-8 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-slate-900">Google Sheets</h3>
                  <p className="text-sm text-slate-600">Cloud-based</p>
                </div>
              </div>

              <p className="text-slate-600 mb-6">
                Apps Script add-on with custom menu integration. Auto-refresh, cloud-based, perfect for collaboration.
              </p>

              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Works anywhere, cloud-based</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>30+ custom DIVV_ functions</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Custom menu integration</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Auto-refresh capabilities</span>
                </li>
              </ul>

              <Link
                href="#sheets-install"
                className="block w-full text-center px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Install for Sheets
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Available Functions */}
      <section className="px-6 py-16 max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-slate-900 mb-4 text-center">
          30+ Functions for Dividend Investors
        </h2>
        <p className="text-lg text-slate-600 mb-12 text-center">
          Everything you need to track dividends, analyze yields, and manage your portfolio
        </p>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Price Functions */}
          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">💰 Price Data</h3>
            <div className="space-y-2 font-mono text-sm">
              <div className="text-blue-600">=DIVV_PRICE("AAPL")</div>
              <div className="text-blue-600">=DIVV_CHANGE("AAPL")</div>
              <div className="text-blue-600">=DIVV_VOLUME("AAPL")</div>
              <div className="text-slate-400">+ 3 more...</div>
            </div>
          </div>

          {/* Dividend Functions */}
          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">📊 Dividends</h3>
            <div className="space-y-2 font-mono text-sm">
              <div className="text-blue-600">=DIVV_YIELD("AAPL")</div>
              <div className="text-blue-600">=DIVV_ANNUAL("AAPL")</div>
              <div className="text-blue-600">=DIVV_NEXT_DATE("AAPL")</div>
              <div className="text-blue-600">=DIVV_FREQUENCY("AAPL")</div>
              <div className="text-slate-400">+ 3 more...</div>
            </div>
          </div>

          {/* ETF Functions */}
          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">📈 ETF Metrics</h3>
            <div className="space-y-2 font-mono text-sm">
              <div className="text-blue-600">=DIVV_AUM("SPY")</div>
              <div className="text-blue-600">=DIVV_IV("XYLD")</div>
              <div className="text-blue-600">=DIVV_STRATEGY("XYLD")</div>
              <div className="text-slate-400">+ 1 more...</div>
            </div>
          </div>

          {/* Company Info */}
          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">🏢 Company Info</h3>
            <div className="space-y-2 font-mono text-sm">
              <div className="text-blue-600">=DIVV_NAME("AAPL")</div>
              <div className="text-blue-600">=DIVV_SECTOR("AAPL")</div>
              <div className="text-blue-600">=DIVV_INDUSTRY("AAPL")</div>
              <div className="text-slate-400">+ 2 more...</div>
            </div>
          </div>

          {/* Portfolio Functions */}
          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">💼 Portfolio</h3>
            <div className="space-y-2 font-mono text-sm">
              <div className="text-blue-600">=DIVV_INCOME("AAPL", 100)</div>
              <div className="text-blue-600">=DIVV_POSITION_VALUE(...)</div>
              <div className="text-blue-600">=DIVV_YIELD_ON_COST(...)</div>
            </div>
          </div>

          {/* Utilities */}
          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">🔧 Utilities</h3>
            <div className="space-y-2 font-mono text-sm">
              <div className="text-blue-600">=DIVV_SEARCH("Apple")</div>
              <div className="text-blue-600">=DIVV_API_STATUS()</div>
              <div className="text-blue-600">=DIVV_SUMMARY("AAPL")</div>
            </div>
          </div>
        </div>

        <div className="mt-8 text-center">
          <Link
            href="/docs/functions"
            className="inline-flex items-center gap-2 text-green-600 font-semibold hover:text-green-700"
          >
            View Complete Function Reference
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Use Cases / Examples */}
      <section id="examples" className="px-6 py-16 bg-slate-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-slate-900 mb-12 text-center">
            Pre-Built Templates for Every Use Case
          </h2>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Portfolio Tracker */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-3">📊 Portfolio Tracker</h3>
              <p className="text-slate-600 mb-4">
                Track your dividend positions with real-time prices, yields, and income projections.
              </p>
              <div className="bg-slate-50 rounded p-4 mb-4 font-mono text-xs overflow-x-auto">
                <div className="text-slate-600">Symbol | Price | Yield | Annual Income</div>
                <div className="text-blue-600">AAPL | =DIVV_PRICE(A2) | =DIVV_YIELD(A2) | ...</div>
              </div>
              <Link href="/templates/portfolio-tracker" className="text-green-600 text-sm font-semibold hover:text-green-700">
                Download Template →
              </Link>
            </div>

            {/* Dividend Calendar */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-3">📅 Dividend Calendar</h3>
              <p className="text-slate-600 mb-4">
                Never miss a dividend payment. Track upcoming ex-dates and amounts.
              </p>
              <div className="bg-slate-50 rounded p-4 mb-4 font-mono text-xs overflow-x-auto">
                <div className="text-slate-600">Symbol | Next Date | Next Amount</div>
                <div className="text-blue-600">AAPL | =DIVV_NEXT_DATE(A2) | =DIVV_NEXT_AMOUNT(A2)</div>
              </div>
              <Link href="/templates/dividend-calendar" className="text-green-600 text-sm font-semibold hover:text-green-700">
                Download Template →
              </Link>
            </div>

            {/* Covered Call ETF Dashboard */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-3">🎯 Covered Call ETF Dashboard</h3>
              <p className="text-slate-600 mb-4">
                Track IV for covered call ETFs to predict future distributions.
              </p>
              <div className="bg-slate-50 rounded p-4 mb-4 font-mono text-xs overflow-x-auto">
                <div className="text-slate-600">Symbol | IV | Monthly Est.</div>
                <div className="text-blue-600">XYLD | =DIVV_IV(A2) | =PRICE*IV*SQRT(1/12)</div>
              </div>
              <Link href="/templates/covered-call-dashboard" className="text-green-600 text-sm font-semibold hover:text-green-700">
                Download Template →
              </Link>
            </div>

            {/* High-Yield Screener */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-3">🔍 High-Yield Screener</h3>
              <p className="text-slate-600 mb-4">
                Find high-yield dividend opportunities sorted by yield, sector, and safety metrics.
              </p>
              <div className="bg-slate-50 rounded p-4 mb-4 font-mono text-xs overflow-x-auto">
                <div className="text-slate-600">Symbol | Yield | Sector | Payout Ratio</div>
                <div className="text-blue-600">T | =DIVV_YIELD(A2) | =DIVV_SECTOR(A2) | ...</div>
              </div>
              <Link href="/templates/high-yield-screener" className="text-green-600 text-sm font-semibold hover:text-green-700">
                Download Template →
              </Link>
            </div>

            {/* Income Projection */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-3">📈 Income Projection</h3>
              <p className="text-slate-600 mb-4">
                Project future dividend income based on growth rates and reinvestment.
              </p>
              <div className="bg-slate-50 rounded p-4 mb-4 font-mono text-xs overflow-x-auto">
                <div className="text-slate-600">Symbol | Growth | Year 5 | Year 10</div>
                <div className="text-blue-600">AAPL | =DIVV_GROWTH(A2) | =ANNUAL*(1+GROWTH)^5</div>
              </div>
              <Link href="/templates/income-projection" className="text-green-600 text-sm font-semibold hover:text-green-700">
                Download Template →
              </Link>
            </div>

            {/* Sector Allocation */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-3">🥧 Sector Allocation</h3>
              <p className="text-slate-600 mb-4">
                Analyze portfolio diversification across sectors with automatic categorization.
              </p>
              <div className="bg-slate-50 rounded p-4 mb-4 font-mono text-xs overflow-x-auto">
                <div className="text-slate-600">Symbol | Sector | Value | % Portfolio</div>
                <div className="text-blue-600">AAPL | =DIVV_SECTOR(A2) | =VALUE | =VALUE/TOTAL</div>
              </div>
              <Link href="/templates/sector-allocation" className="text-green-600 text-sm font-semibold hover:text-green-700">
                Download Template →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Download/Installation Section */}
      <section id="download" className="px-6 py-16 max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-slate-900 mb-12 text-center">
          Get Started in 3 Minutes
        </h2>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Excel Installation */}
          <div id="excel-download" className="bg-gradient-to-br from-green-50 to-white rounded-xl p-8 border-2 border-green-200">
            <div className="flex items-center gap-3 mb-6">
              <FileSpreadsheet className="w-8 h-8 text-green-600" />
              <h3 className="text-2xl font-bold text-slate-900">Excel Add-in</h3>
            </div>

            <ol className="space-y-4 mb-8">
              <li className="flex gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-green-600 text-white text-sm font-bold flex-shrink-0">1</span>
                <div>
                  <div className="font-semibold text-slate-900">Download DividendAPI.bas</div>
                  <div className="text-sm text-slate-600">VBA module file</div>
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-green-600 text-white text-sm font-bold flex-shrink-0">2</span>
                <div>
                  <div className="font-semibold text-slate-900">Import to Excel</div>
                  <div className="text-sm text-slate-600">Alt+F11 → File → Import</div>
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-green-600 text-white text-sm font-bold flex-shrink-0">3</span>
                <div>
                  <div className="font-semibold text-slate-900">Add API Key</div>
                  <div className="text-sm text-slate-600">Settings!A2 cell</div>
                </div>
              </li>
            </ol>

            <div className="flex gap-3">
              <Link
                href="/downloads/excel-addon.zip"
                className="flex-1 text-center px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors inline-flex items-center justify-center gap-2"
              >
                <Download className="w-5 h-5" />
                Download
              </Link>
              <Link
                href="/docs/excel-installation"
                className="px-6 py-3 bg-white text-green-600 rounded-lg font-semibold border-2 border-green-600 hover:bg-green-50 transition-colors"
              >
                Guide
              </Link>
            </div>
          </div>

          {/* Google Sheets Installation */}
          <div id="sheets-install" className="bg-gradient-to-br from-blue-50 to-white rounded-xl p-8 border-2 border-blue-200">
            <div className="flex items-center gap-3 mb-6">
              <Table className="w-8 h-8 text-blue-600" />
              <h3 className="text-2xl font-bold text-slate-900">Google Sheets Add-on</h3>
            </div>

            <ol className="space-y-4 mb-8">
              <li className="flex gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-600 text-white text-sm font-bold flex-shrink-0">1</span>
                <div>
                  <div className="font-semibold text-slate-900">Open Apps Script</div>
                  <div className="text-sm text-slate-600">Extensions → Apps Script</div>
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-600 text-white text-sm font-bold flex-shrink-0">2</span>
                <div>
                  <div className="font-semibold text-slate-900">Paste Code</div>
                  <div className="text-sm text-slate-600">Copy Code.gs and save</div>
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-600 text-white text-sm font-bold flex-shrink-0">3</span>
                <div>
                  <div className="font-semibold text-slate-900">Set API Key</div>
                  <div className="text-sm text-slate-600">Menu → Set API Key</div>
                </div>
              </li>
            </ol>

            <div className="flex gap-3">
              <Link
                href="/docs/sheets-code"
                className="flex-1 text-center px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Get Code
              </Link>
              <Link
                href="/docs/sheets-installation"
                className="px-6 py-3 bg-white text-blue-600 rounded-lg font-semibold border-2 border-blue-600 hover:bg-blue-50 transition-colors"
              >
                Guide
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-8 text-center">
          <p className="text-slate-600">
            Need an API key?{' '}
            <Link href="/signup" className="text-green-600 font-semibold hover:text-green-700">
              Sign up for free →
            </Link>
          </p>
        </div>
      </section>

      {/* Pricing Note */}
      <section className="px-6 py-16 bg-gradient-to-r from-green-600 to-green-700 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">
            Free to Install, Flexible Pricing
          </h2>
          <p className="text-lg text-green-100 mb-8">
            The Divv add-ons are completely free to install. You only need a Divv API key (free tier includes 1,000 requests/month).
            Upgrade to Pro for unlimited symbols and advanced features.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link
              href="/signup"
              className="px-8 py-3 bg-white text-green-600 rounded-lg font-semibold hover:bg-green-50 transition-colors"
            >
              Get Free API Key
            </Link>
            <Link
              href="/pricing"
              className="px-8 py-3 bg-green-500 text-white rounded-lg font-semibold hover:bg-green-400 transition-colors"
            >
              View Pricing
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
