'use client';

import { API_CONFIG } from '@/lib/config';

import Header from '@/components/Header';
import Link from 'next/link';

export default function ExcelIntegrationPage() {
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
              Microsoft Excel Integration
            </h1>
            <p className="text-xl text-gray-600">
              Use <code className="px-2 py-1 bg-gray-100 rounded text-green-600 font-mono">=DIVV()</code> in Excel with our VBA module
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
                Want more? <Link href="/pricing" className="underline font-semibold">Upgrade for full access</Link> (PE ratio, volume, market cap, etc.)
              </p>
            </div>
          </div>

          {/* Quick Example */}
          <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-2xl p-8 border-2 border-green-500 mb-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Try It Now (Free Tier)</h2>
            <div className="bg-white p-6 rounded-lg border border-green-500">
              <pre className="text-sm font-mono text-green-700">
{`=DIVV("AAPL", "price")
=DIVV("MSFT", "dividendYield")
=DIVV("JNJ", "dayHigh")

' Free tier: price, open, high/low, dividend yield`}
              </pre>
            </div>
            <p className="text-sm text-gray-600 mt-4 text-center">
              💎 Free tier includes: price, open, dayHigh, dayLow, previousClose, dividendYield, dividendAmount
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
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Download the VBA Module</h3>
                  <p className="text-gray-600 mb-3">
                    Download our ready-to-use VBA module file
                  </p>
                  <a
                    href="/DIVV.bas"
                    download
                    className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-all"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                    </svg>
                    Download DIVV.bas
                  </a>
                </div>
              </div>

              {/* Step 2 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                  2
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Open VBA Editor</h3>
                  <p className="text-gray-600 mb-3">
                    In Excel, press <kbd className="px-2 py-1 bg-gray-200 rounded font-mono text-sm">Alt+F11</kbd> (Windows) or <kbd className="px-2 py-1 bg-gray-200 rounded font-mono text-sm">Option+F11</kbd> (Mac)
                  </p>
                </div>
              </div>

              {/* Step 3 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                  3
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Import the Module</h3>
                  <p className="text-gray-600 mb-3">
                    In VBA Editor: <strong>File → Import File...</strong> and select the downloaded <code>DIVV.bas</code>
                  </p>
                </div>
              </div>

              {/* Step 4 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                  4
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Configure API Endpoint</h3>
                  <p className="text-gray-600 mb-3">
                    In the VBA code, update the <code className="px-2 py-1 bg-gray-100 rounded font-mono text-sm">API_BASE_URL</code> constant:
                  </p>
                  <pre className="bg-gray-900 p-4 rounded-lg text-white font-mono text-sm overflow-x-auto">
{`' For production (recommended)
Const API_BASE_URL As String = "https://api.divv.com"

' For local testing
Const API_BASE_URL As String = {API_CONFIG.baseUrl}`}
                  </pre>
                </div>
              </div>

              {/* Step 5 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                  5
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Save as Macro-Enabled</h3>
                  <p className="text-gray-600 mb-3">
                    Save your workbook as <strong>.xlsm</strong> (Excel Macro-Enabled Workbook) to preserve the VBA code
                  </p>
                </div>
              </div>

              {/* Step 6 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                  6
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Test the Function</h3>
                  <p className="text-gray-600 mb-3">
                    In any cell, type:
                  </p>
                  <pre className="bg-gray-900 p-4 rounded-lg text-emerald-400 font-mono text-sm">
                    =DIVV("AAPL", "price")
                  </pre>
                  <p className="text-gray-600 mt-2 text-sm">
                    Press Enter. You should see the current price of Apple stock!
                  </p>
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
                  <code className="text-green-600">=DIVV(symbol, attribute)</code>
                </h3>
                <p className="text-gray-600 mb-3">
                  Get stock data for any attribute
                </p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Examples:</p>
                  <pre className="text-sm font-mono text-gray-700">
{`=DIVV("AAPL", "price")
=DIVV("MSFT", "dividendYield")
=DIVV("JNJ", "yearHigh")
=DIVV("PG", "peRatio")`}
                  </pre>
                </div>
              </div>

              {/* Note */}
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-800">
                  <strong>📝 Note:</strong> The Excel VBA implementation includes the same core DIVV() function as Google Sheets. Advanced functions (DIVVBULK, DIVVDIVIDENDS, DIVVARISTOCRAT) can be added to the VBA module if needed.
                </p>
              </div>
            </div>
          </div>

          {/* Compatibility */}
          <div className="bg-white rounded-2xl p-8 border-2 border-gray-200 mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Compatibility</h2>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-3">✅ Supported Versions</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Excel 2010 and newer</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Excel for Windows</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Excel for Mac</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Microsoft 365</span>
                  </li>
                </ul>
              </div>

              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-3">⚠️ Limitations</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <span className="text-yellow-600">•</span>
                    <span>Requires macros to be enabled</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-yellow-600">•</span>
                    <span>Not available in Excel Online (web version)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-yellow-600">•</span>
                    <span>Mobile apps (iOS/Android) don't support VBA</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Caching */}
          <div className="bg-white rounded-2xl p-8 border-2 border-gray-200 mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Caching</h2>

            <p className="text-gray-600 mb-4">
              The VBA module includes a worksheet-based caching system to reduce API calls and improve performance.
            </p>

            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">How it works:</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>1. Data is cached in a hidden worksheet named <code className="px-2 py-1 bg-gray-200 rounded font-mono">_DivvCache</code></li>
                <li>2. Cache expires after 5 minutes by default</li>
                <li>3. Same symbol within 5 minutes = instant response (no API call)</li>
              </ul>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-800 mb-2">
                <strong>💡 Clear Cache:</strong> To force fresh data, run this in VBA:
              </p>
              <pre className="bg-gray-900 p-3 rounded text-white font-mono text-sm">
                ClearDivvCache
              </pre>
            </div>
          </div>

          {/* Troubleshooting */}
          <div className="bg-white rounded-2xl p-8 border-2 border-gray-200">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Troubleshooting</h2>

            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-red-600 mb-2">#VALUE! error</h3>
                <p className="text-gray-600">
                  Macros may be disabled. Go to <strong>File → Options → Trust Center → Trust Center Settings → Macro Settings</strong> and enable macros.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-bold text-red-600 mb-2">#NAME? error</h3>
                <p className="text-gray-600">
                  The VBA module may not be imported correctly. Check the VBA Editor (Alt+F11) to ensure the DivvAPI module is present.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-bold text-red-600 mb-2">Function returns #ERROR</h3>
                <p className="text-gray-600">
                  Check that the API endpoint URL is correct and the API is running. You can test connectivity by running <code>TestDivvConnection</code> from the VBA Editor.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-bold text-red-600 mb-2">Slow performance</h3>
                <p className="text-gray-600">
                  Make sure the cache worksheet exists. The first call to each symbol will be slower (API request), but subsequent calls should be instant.
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
