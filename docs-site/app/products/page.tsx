import Link from 'next/link'
import { Code, Table, Plug, Zap, Shield, TrendingUp } from 'lucide-react'

export default function ProductsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Hero Section */}
      <section className="px-6 py-20 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold text-slate-900 mb-6">
            Divv Products
          </h1>
          <p className="text-xl text-slate-600 mb-8">
            Powerful tools for dividend investors. Access comprehensive dividend data through Divv API or directly in your spreadsheets.
          </p>
        </div>
      </section>

      {/* Main Products Grid */}
      <section className="px-6 py-12 max-w-6xl mx-auto">
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          {/* REST API Card */}
          <Link href="/products/api" className="group">
            <div className="bg-white rounded-xl shadow-lg p-8 border border-slate-200 hover:border-blue-500 hover:shadow-xl transition-all h-full">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Code className="w-8 h-8 text-blue-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900">REST API</h2>
              </div>

              <p className="text-slate-600 mb-6">
                Production-grade REST API with 23+ endpoints for dividend stock data, ETF metrics, and portfolio analytics.
              </p>

              <div className="space-y-3 mb-6">
                <div className="flex items-start gap-3">
                  <Zap className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-slate-700">Sub-100ms response times</span>
                </div>
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-slate-700">API key authentication with rate limiting</span>
                </div>
                <div className="flex items-start gap-3">
                  <TrendingUp className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-slate-700">24,000+ stocks and ETFs covered</span>
                </div>
              </div>

              <div className="bg-slate-900 text-slate-100 rounded-lg p-4 mb-6 font-mono text-sm overflow-x-auto">
                <div className="text-slate-400 mb-2"># Get stock price</div>
                <div>curl https://api.yourdomain.com/v1/stocks/AAPL/latest-price \</div>
                <div className="ml-4">-H "X-API-Key: your_key"</div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">Starting at Free</span>
                <span className="text-blue-600 font-semibold group-hover:translate-x-1 transition-transform">
                  Learn more →
                </span>
              </div>
            </div>
          </Link>

          {/* Spreadsheet Integrations Card */}
          <Link href="/products/integrations" className="group">
            <div className="bg-white rounded-xl shadow-lg p-8 border border-slate-200 hover:border-green-500 hover:shadow-xl transition-all h-full">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <Table className="w-8 h-8 text-green-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900">Spreadsheet Integrations</h2>
              </div>

              <p className="text-slate-600 mb-6">
                Access dividend data directly in Excel or Google Sheets with custom functions like YAHOOFINANCE() or GOOGLEFINANCE().
              </p>

              <div className="space-y-3 mb-6">
                <div className="flex items-start gap-3">
                  <Zap className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-slate-700">30+ custom functions for dividends & ETFs</span>
                </div>
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-slate-700">Works in Excel (Windows/Mac) & Google Sheets</span>
                </div>
                <div className="flex items-start gap-3">
                  <TrendingUp className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-slate-700">Ready-made portfolio tracker templates</span>
                </div>
              </div>

              <div className="bg-slate-900 text-slate-100 rounded-lg p-4 mb-6 font-mono text-sm overflow-x-auto">
                <div className="text-slate-400 mb-2">// In your spreadsheet</div>
                <div>=DIVV_PRICE("AAPL")</div>
                <div>=DIVV_YIELD("AAPL")</div>
                <div>=DIVV_NEXT_DATE("AAPL")</div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">Free to install</span>
                <span className="text-green-600 font-semibold group-hover:translate-x-1 transition-transform">
                  Learn more →
                </span>
              </div>
            </div>
          </Link>
        </div>

        {/* Feature Comparison */}
        <div className="bg-white rounded-xl shadow-lg p-8 border border-slate-200">
          <h3 className="text-2xl font-bold text-slate-900 mb-6 text-center">
            Choose the Right Tool for Your Needs
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-4 px-4 text-slate-900 font-semibold">Feature</th>
                  <th className="text-center py-4 px-4 text-slate-900 font-semibold">REST API</th>
                  <th className="text-center py-4 px-4 text-slate-900 font-semibold">Spreadsheets</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="py-4 px-4 text-slate-700">Best for</td>
                  <td className="py-4 px-4 text-center text-slate-600">Developers, Apps, Automation</td>
                  <td className="py-4 px-4 text-center text-slate-600">Investors, Analysts, Portfolios</td>
                </tr>
                <tr>
                  <td className="py-4 px-4 text-slate-700">Setup time</td>
                  <td className="py-4 px-4 text-center text-slate-600">~10 minutes</td>
                  <td className="py-4 px-4 text-center text-slate-600">~3 minutes</td>
                </tr>
                <tr>
                  <td className="py-4 px-4 text-slate-700">Technical skill required</td>
                  <td className="py-4 px-4 text-center text-slate-600">Moderate (API knowledge)</td>
                  <td className="py-4 px-4 text-center text-slate-600">Low (basic formulas)</td>
                </tr>
                <tr>
                  <td className="py-4 px-4 text-slate-700">Data access</td>
                  <td className="py-4 px-4 text-center text-slate-600">Full programmatic control</td>
                  <td className="py-4 px-4 text-center text-slate-600">Function-based</td>
                </tr>
                <tr>
                  <td className="py-4 px-4 text-slate-700">Real-time updates</td>
                  <td className="py-4 px-4 text-center">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800">
                      ✓ Yes
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800">
                      ✓ Yes
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="py-4 px-4 text-slate-700">Historical data</td>
                  <td className="py-4 px-4 text-center">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800">
                      ✓ Full access
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-yellow-100 text-yellow-800">
                      Limited
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="py-4 px-4 text-slate-700">Custom analytics</td>
                  <td className="py-4 px-4 text-center">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800">
                      ✓ Unlimited
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800">
                      ✓ Formula-based
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="py-4 px-4 text-slate-700">Starting price</td>
                  <td className="py-4 px-4 text-center text-slate-900 font-semibold">Free</td>
                  <td className="py-4 px-4 text-center text-slate-900 font-semibold">Free</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Use Both Section */}
        <div className="mt-12 bg-gradient-to-r from-blue-50 to-green-50 rounded-xl p-8 border border-blue-200">
          <div className="flex items-start gap-4">
            <Plug className="w-8 h-8 text-blue-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">
                Use Both Together
              </h3>
              <p className="text-slate-700 mb-4">
                Many users combine both products: Use spreadsheets for portfolio tracking and quick analysis,
                and the API for custom applications, automation, and advanced analytics.
              </p>
              <p className="text-slate-600 text-sm">
                Both products use the same API key and share the same rate limits, making it easy to switch between them.
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-16 text-center">
          <h3 className="text-3xl font-bold text-slate-900 mb-4">
            Ready to Get Started?
          </h3>
          <p className="text-lg text-slate-600 mb-8">
            Sign up for a free account and start accessing dividend data today.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link
              href="/signup"
              className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Get Your Free API Key
            </Link>
            <Link
              href="/products/api"
              className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold border-2 border-blue-600 hover:bg-blue-50 transition-colors"
            >
              View Documentation
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
