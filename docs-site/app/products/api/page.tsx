import Link from 'next/link'
import { Code, Zap, Shield, BarChart3, CheckCircle, ArrowRight } from 'lucide-react'
import { STOCK_COUNT } from '@/lib/config'

export default function APIProductPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Hero Section */}
      <section className="px-6 py-20 bg-gradient-to-r from-blue-600 to-blue-700 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/30 px-4 py-2 rounded-full text-sm mb-6">
            <Code className="w-4 h-4" />
            <span>REST API</span>
          </div>
          <h1 className="text-5xl font-bold mb-6">
            Divv Data API
          </h1>
          <p className="text-xl text-blue-100 mb-8">
            Production-grade REST API for dividend stocks, ETF metrics, and portfolio analytics.
            Built for developers who need reliable, fast, and comprehensive dividend data.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link
              href="/api-keys"
              className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
            >
              Get API Key
            </Link>
            <Link
              href="/api"
              className="px-8 py-3 bg-blue-500 text-white rounded-lg font-semibold hover:bg-blue-400 transition-colors"
            >
              View Documentation
            </Link>
          </div>
        </div>
      </section>

      {/* Quick Example */}
      <section className="px-6 py-16 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-900 mb-4">
            Get Started in Minutes
          </h2>
          <p className="text-lg text-slate-600">
            Simple, intuitive REST API with comprehensive documentation
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Request */}
          <div>
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-600 text-sm font-bold">1</span>
              Make a Request
            </h3>
            <div className="bg-slate-900 rounded-lg p-6 text-slate-100 font-mono text-sm overflow-x-auto">
              <div className="text-slate-400 mb-2"># Get latest stock price</div>
              <div className="text-green-400">curl</div> https://api.yourdomain.com/v1/stocks/AAPL/latest-price \<br/>
              <div className="ml-4">-H <span className="text-yellow-300">"X-API-Key: your_api_key"</span></div>
            </div>
          </div>

          {/* Response */}
          <div>
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-600 text-sm font-bold">2</span>
              Get Clean JSON
            </h3>
            <div className="bg-slate-900 rounded-lg p-6 text-slate-100 font-mono text-sm overflow-x-auto">
              {'{'}<br/>
              <div className="ml-4">
                <span className="text-blue-400">"symbol"</span>: <span className="text-yellow-300">"AAPL"</span>,<br/>
                <span className="text-blue-400">"close"</span>: <span className="text-green-400">150.25</span>,<br/>
                <span className="text-blue-400">"change_percent"</span>: <span className="text-green-400">2.5</span>,<br/>
                <span className="text-blue-400">"volume"</span>: <span className="text-green-400">50000000</span>,<br/>
                <span className="text-blue-400">"date"</span>: <span className="text-yellow-300">"2025-11-13"</span>
              </div>
              {'}'}
            </div>
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section className="px-6 py-16 bg-slate-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-slate-900 mb-12 text-center">
            Everything You Need for Dividend Investing Apps
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <div className="p-3 bg-blue-100 rounded-lg w-fit mb-4">
                <Zap className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">
                Blazing Fast
              </h3>
              <p className="text-slate-600 mb-4">
                Sub-100ms response times with intelligent caching and CDN distribution. Built for production workloads.
              </p>
              <ul className="space-y-2">
                <li className="flex items-start gap-2 text-sm text-slate-600">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Response time &lt; 100ms</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-600">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>99.9% uptime SLA</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-600">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Global CDN</span>
                </li>
              </ul>
            </div>

            {/* Feature 2 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <div className="p-3 bg-green-100 rounded-lg w-fit mb-4">
                <Shield className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">
                Secure & Reliable
              </h3>
              <p className="text-slate-600 mb-4">
                Enterprise-grade security with API key authentication, rate limiting, and comprehensive monitoring.
              </p>
              <ul className="space-y-2">
                <li className="flex items-start gap-2 text-sm text-slate-600">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>API key authentication</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-600">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Token bucket rate limiting</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-600">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>HTTPS encryption</span>
                </li>
              </ul>
            </div>

            {/* Feature 3 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <div className="p-3 bg-purple-100 rounded-lg w-fit mb-4">
                <BarChart3 className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">
                Comprehensive Data
              </h3>
              <p className="text-slate-600 mb-4">
                {STOCK_COUNT} stocks and ETFs with real-time prices, dividend history, ETF metrics, and portfolio analytics.
              </p>
              <ul className="space-y-2">
                <li className="flex items-start gap-2 text-sm text-slate-600">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>{STOCK_COUNT} symbols</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-600">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Daily data updates</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-slate-600">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Historical data access</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* API Endpoints */}
      <section className="px-6 py-16 max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-slate-900 mb-12 text-center">
          23+ Endpoints for Every Use Case
        </h2>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Stock & Price Endpoints */}
          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Stock & Price Data</h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-blue-100 text-blue-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/stocks</div>
                  <div className="text-xs text-slate-500">List all stocks & ETFs</div>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-blue-100 text-blue-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/stocks/:symbol</div>
                  <div className="text-xs text-slate-500">Get stock details</div>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-blue-100 text-blue-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/stocks/:symbol/latest-price</div>
                  <div className="text-xs text-slate-500">Latest price & volume</div>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-blue-100 text-blue-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/prices/historical</div>
                  <div className="text-xs text-slate-500">Historical price data</div>
                </div>
              </li>
            </ul>
          </div>

          {/* Dividend Endpoints */}
          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Dividend Data</h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-green-100 text-green-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/dividends/:symbol</div>
                  <div className="text-xs text-slate-500">Dividend history</div>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-green-100 text-green-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/dividends/:symbol/next</div>
                  <div className="text-xs text-slate-500">Next dividend payment</div>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-green-100 text-green-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/dividends/:symbol/metrics</div>
                  <div className="text-xs text-slate-500">Yield, growth, frequency</div>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-green-100 text-green-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/dividends/calendar</div>
                  <div className="text-xs text-slate-500">Upcoming dividends</div>
                </div>
              </li>
            </ul>
          </div>

          {/* ETF Endpoints */}
          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">ETF Data</h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-purple-100 text-purple-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/etfs</div>
                  <div className="text-xs text-slate-500">All ETFs with metrics</div>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-purple-100 text-purple-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/etfs/:symbol</div>
                  <div className="text-xs text-slate-500">ETF details & holdings</div>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-purple-100 text-purple-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/etfs/covered-call</div>
                  <div className="text-xs text-slate-500">Covered call ETFs with IV</div>
                </div>
              </li>
            </ul>
          </div>

          {/* Analytics Endpoints */}
          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Analytics & Screeners</h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-orange-100 text-orange-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/screeners/high-yield</div>
                  <div className="text-xs text-slate-500">High dividend yield stocks</div>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-orange-100 text-orange-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/screeners/dividend-growth</div>
                  <div className="text-xs text-slate-500">Growing dividend stocks</div>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-orange-100 text-orange-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/analytics/sector-performance</div>
                  <div className="text-xs text-slate-500">Sector yield analysis</div>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <code className="px-2 py-1 bg-orange-100 text-orange-600 rounded text-xs font-mono flex-shrink-0">GET</code>
                <div>
                  <div className="font-mono text-sm text-slate-700">/search?q=:query</div>
                  <div className="text-xs text-slate-500">Search stocks by name</div>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 text-center">
          <Link
            href="/api"
            className="inline-flex items-center gap-2 text-blue-600 font-semibold hover:text-blue-700"
          >
            View Full API Documentation
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Pricing */}
      <section className="px-6 py-16 bg-slate-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-slate-900 mb-4 text-center">
            Simple, Transparent Pricing
          </h2>
          <p className="text-lg text-slate-600 mb-12 text-center">
            Start free, upgrade as you grow
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Free Tier */}
            <div className="bg-white rounded-xl p-8 border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-2">Free</h3>
              <div className="mb-6">
                <span className="text-4xl font-bold text-slate-900">$0</span>
                <span className="text-slate-600">/month</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>1,000 requests/month</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>10 requests/minute</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>All endpoints</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Community support</span>
                </li>
              </ul>
              <Link
                href="/signup"
                className="block w-full text-center px-6 py-3 bg-slate-900 text-white rounded-lg font-semibold hover:bg-slate-800 transition-colors"
              >
                Get Started
              </Link>
            </div>

            {/* Pro Tier */}
            <div className="bg-blue-600 rounded-xl p-8 border-2 border-blue-700 relative">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-yellow-400 text-yellow-900 px-4 py-1 rounded-full text-sm font-bold">
                POPULAR
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Pro</h3>
              <div className="mb-6">
                <span className="text-4xl font-bold text-white">$29</span>
                <span className="text-blue-100">/month</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2 text-white">
                  <CheckCircle className="w-5 h-5 text-blue-200 mt-0.5 flex-shrink-0" />
                  <span>100,000 requests/month</span>
                </li>
                <li className="flex items-start gap-2 text-white">
                  <CheckCircle className="w-5 h-5 text-blue-200 mt-0.5 flex-shrink-0" />
                  <span>100 requests/minute</span>
                </li>
                <li className="flex items-start gap-2 text-white">
                  <CheckCircle className="w-5 h-5 text-blue-200 mt-0.5 flex-shrink-0" />
                  <span>All endpoints</span>
                </li>
                <li className="flex items-start gap-2 text-white">
                  <CheckCircle className="w-5 h-5 text-blue-200 mt-0.5 flex-shrink-0" />
                  <span>Priority email support</span>
                </li>
                <li className="flex items-start gap-2 text-white">
                  <CheckCircle className="w-5 h-5 text-blue-200 mt-0.5 flex-shrink-0" />
                  <span>Hourly data updates</span>
                </li>
              </ul>
              <Link
                href="/signup?plan=pro"
                className="block w-full text-center px-6 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
              >
                Start Pro Trial
              </Link>
            </div>

            {/* Enterprise Tier */}
            <div className="bg-white rounded-xl p-8 border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-2">Enterprise</h3>
              <div className="mb-6">
                <span className="text-4xl font-bold text-slate-900">Custom</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Unlimited requests</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>1,000 requests/minute</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Real-time updates</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Dedicated support</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>SLA guarantee</span>
                </li>
                <li className="flex items-start gap-2 text-slate-700">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Custom features</span>
                </li>
              </ul>
              <Link
                href="/contact"
                className="block w-full text-center px-6 py-3 bg-slate-900 text-white rounded-lg font-semibold hover:bg-slate-800 transition-colors"
              >
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-20 bg-gradient-to-r from-blue-600 to-blue-700 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-6">
            Ready to Build Something Great?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join hundreds of developers using Divv API to power their dividend investing applications.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link
              href="/signup"
              className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
            >
              Get Your Free API Key
            </Link>
            <Link
              href="/api"
              className="px-8 py-3 bg-blue-500 text-white rounded-lg font-semibold hover:bg-blue-400 transition-colors"
            >
              Read the Docs
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
