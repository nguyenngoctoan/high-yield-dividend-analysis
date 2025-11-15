import Link from 'next/link';
import Header from '@/components/Header';
import { API_CONFIG, STOCK_COUNT } from '@/lib/config';
import './hero-animation.css';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-slate-100 via-blue-50 to-indigo-50" style={{ minHeight: '600px' }}>
        {/* Animated Circuit Background */}
        <div className="absolute inset-0 opacity-10 -z-10">
          {/* SVG Circuit traces with corners */}
          <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <linearGradient id="pulse-blue" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="transparent" />
                <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.8" />
                <stop offset="100%" stopColor="transparent" />
              </linearGradient>
              <linearGradient id="pulse-purple" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="transparent" />
                <stop offset="50%" stopColor="#8b5cf6" stopOpacity="0.8" />
                <stop offset="100%" stopColor="transparent" />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>

            {/* Circuit trace paths with 90 degree turns */}
            <path d="M 0 8 L 25 8 L 25 20 L 50 20" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 0 15 L 20 15 L 20 35 L 45 35 L 45 55" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 0 22 L 35 22 L 35 45" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 0 30 L 28 30 L 28 60 L 55 60" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 0 42 L 18 42 L 18 72 L 38 72" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 0 52 L 32 52 L 32 80 L 60 80" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 0 65 L 22 65 L 22 88 L 48 88" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 0 75 L 40 75 L 40 95" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 0 85 L 30 85 L 30 98" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>

            {/* Vertical starting paths */}
            <path d="M 15 0 L 15 25 L 42 25 L 42 50" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 25 0 L 25 18 L 52 18 L 52 40 L 72 40" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 38 0 L 38 28 L 65 28 L 65 55" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 48 0 L 48 35 L 75 35 L 75 68" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 58 0 L 58 42 L 82 42 L 82 75 L 95 75" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 68 0 L 68 50 L 88 50 L 88 82" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 78 0 L 78 32 L 98 32" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 85 0 L 85 62 L 100 62" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 92 0 L 92 45 L 100 45" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>

            {/* Right to left paths */}
            <path d="M 100 12 L 78 12 L 78 38 L 55 38" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 100 25 L 65 25 L 65 48 L 42 48" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 100 58 L 70 58 L 70 85 L 45 85" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 100 70 L 80 70 L 80 92" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>
            <path d="M 100 82 L 62 82 L 62 95" stroke="#94a3b8" strokeWidth="0.08" fill="none" opacity="0.8"/>

            {/* Animated light pulses following the paths */}
            <circle r="0.2" fill="#3b82f6" filter="url(#glow)">
              <animateMotion dur="4s" repeatCount="indefinite" path="M 0 8 L 25 8 L 25 20 L 50 20" />
            </circle>
            <circle r="0.2" fill="#8b5cf6" filter="url(#glow)">
              <animateMotion dur="5s" repeatCount="indefinite" path="M 0 15 L 20 15 L 20 35 L 45 35 L 45 55" />
            </circle>
            <circle r="0.15" fill="#6366f1" filter="url(#glow)">
              <animateMotion dur="3.5s" repeatCount="indefinite" path="M 0 22 L 35 22 L 35 45" />
            </circle>
            <circle r="0.2" fill="#3b82f6" filter="url(#glow)">
              <animateMotion dur="4.5s" repeatCount="indefinite" path="M 0 30 L 28 30 L 28 60 L 55 60" />
            </circle>
            <circle r="0.15" fill="#06b6d4" filter="url(#glow)">
              <animateMotion dur="4.2s" repeatCount="indefinite" path="M 0 42 L 18 42 L 18 72 L 38 72" />
            </circle>
            <circle r="0.2" fill="#8b5cf6" filter="url(#glow)">
              <animateMotion dur="3.8s" repeatCount="indefinite" path="M 0 52 L 32 52 L 32 80 L 60 80" />
            </circle>
            <circle r="0.15" fill="#3b82f6" filter="url(#glow)">
              <animateMotion dur="5.2s" repeatCount="indefinite" path="M 0 65 L 22 65 L 22 88 L 48 88" />
            </circle>
            <circle r="0.2" fill="#8b5cf6" filter="url(#glow)">
              <animateMotion dur="4.8s" repeatCount="indefinite" path="M 0 75 L 40 75 L 40 95" />
            </circle>
            <circle r="0.15" fill="#6366f1" filter="url(#glow)">
              <animateMotion dur="4.3s" repeatCount="indefinite" path="M 0 85 L 30 85 L 30 98" />
            </circle>

            {/* Vertical pulses */}
            <circle r="0.2" fill="#3b82f6" filter="url(#glow)">
              <animateMotion dur="5s" repeatCount="indefinite" path="M 15 0 L 15 25 L 42 25 L 42 50" />
            </circle>
            <circle r="0.15" fill="#8b5cf6" filter="url(#glow)">
              <animateMotion dur="5.5s" repeatCount="indefinite" path="M 25 0 L 25 18 L 52 18 L 52 40 L 72 40" />
            </circle>
            <circle r="0.2" fill="#6366f1" filter="url(#glow)">
              <animateMotion dur="4.7s" repeatCount="indefinite" path="M 38 0 L 38 28 L 65 28 L 65 55" />
            </circle>
            <circle r="0.15" fill="#06b6d4" filter="url(#glow)">
              <animateMotion dur="5.3s" repeatCount="indefinite" path="M 48 0 L 48 35 L 75 35 L 75 68" />
            </circle>
            <circle r="0.2" fill="#3b82f6" filter="url(#glow)">
              <animateMotion dur="6s" repeatCount="indefinite" path="M 58 0 L 58 42 L 82 42 L 82 75 L 95 75" />
            </circle>
            <circle r="0.15" fill="#8b5cf6" filter="url(#glow)">
              <animateMotion dur="5.8s" repeatCount="indefinite" path="M 68 0 L 68 50 L 88 50 L 88 82" />
            </circle>
            <circle r="0.2" fill="#6366f1" filter="url(#glow)">
              <animateMotion dur="4.4s" repeatCount="indefinite" path="M 78 0 L 78 32 L 98 32" />
            </circle>
            <circle r="0.15" fill="#3b82f6" filter="url(#glow)">
              <animateMotion dur="5.6s" repeatCount="indefinite" path="M 85 0 L 85 62 L 100 62" />
            </circle>
            <circle r="0.2" fill="#8b5cf6" filter="url(#glow)">
              <animateMotion dur="5.1s" repeatCount="indefinite" path="M 92 0 L 92 45 L 100 45" />
            </circle>

            {/* Right to left pulses */}
            <circle r="0.2" fill="#8b5cf6" filter="url(#glow)">
              <animateMotion dur="4.6s" repeatCount="indefinite" path="M 100 12 L 78 12 L 78 38 L 55 38" />
            </circle>
            <circle r="0.15" fill="#6366f1" filter="url(#glow)">
              <animateMotion dur="5.4s" repeatCount="indefinite" path="M 100 25 L 65 25 L 65 48 L 42 48" />
            </circle>
            <circle r="0.2" fill="#06b6d4" filter="url(#glow)">
              <animateMotion dur="5.1s" repeatCount="indefinite" path="M 100 58 L 70 58 L 70 85 L 45 85" />
            </circle>

            {/* Circuit nodes at intersections */}
            <circle cx="25" cy="8" r="0.12" fill="#3b82f6" opacity="0.8"/>
            <circle cx="25" cy="20" r="0.12" fill="#3b82f6" opacity="0.8"/>
            <circle cx="20" cy="15" r="0.12" fill="#8b5cf6" opacity="0.8"/>
            <circle cx="20" cy="35" r="0.12" fill="#8b5cf6" opacity="0.8"/>
            <circle cx="45" cy="35" r="0.12" fill="#8b5cf6" opacity="0.8"/>
            <circle cx="28" cy="30" r="0.12" fill="#6366f1" opacity="0.8"/>
            <circle cx="28" cy="60" r="0.12" fill="#6366f1" opacity="0.8"/>
            <circle cx="32" cy="52" r="0.12" fill="#3b82f6" opacity="0.8"/>
            <circle cx="32" cy="80" r="0.12" fill="#3b82f6" opacity="0.8"/>
            <circle cx="15" cy="25" r="0.12" fill="#8b5cf6" opacity="0.8"/>
            <circle cx="42" cy="25" r="0.12" fill="#8b5cf6" opacity="0.8"/>
            <circle cx="52" cy="18" r="0.12" fill="#06b6d4" opacity="0.8"/>
            <circle cx="52" cy="40" r="0.12" fill="#06b6d4" opacity="0.8"/>
            <circle cx="72" cy="40" r="0.12" fill="#06b6d4" opacity="0.8"/>
            <circle cx="65" cy="28" r="0.12" fill="#3b82f6" opacity="0.8"/>
            <circle cx="75" cy="35" r="0.12" fill="#3b82f6" opacity="0.8"/>
            <circle cx="82" cy="42" r="0.12" fill="#8b5cf6" opacity="0.8"/>
            <circle cx="78" cy="12" r="0.12" fill="#8b5cf6" opacity="0.8"/>
            <circle cx="78" cy="38" r="0.12" fill="#8b5cf6" opacity="0.8"/>
          </svg>
        </div>

        <div className="container mx-auto px-6 pt-32 pb-20 relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-block mb-6 px-4 py-1.5 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-full text-sm font-medium">
            <span className="bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent font-semibold">
              The Dividend Data Specialist
            </span>
          </div>
          <h1 className="text-7xl font-bold mb-6 tracking-tight">
            <span className="bg-gradient-to-r from-green-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">
              Divv API
            </span>
          </h1>
          <p className="text-2xl text-gray-800 mb-4 leading-relaxed max-w-3xl mx-auto font-semibold">
            The only API built exclusively for dividend investors
          </p>
          <p className="text-lg text-gray-600 mb-10 leading-relaxed max-w-2xl mx-auto">
            Google Sheets + Excel compatible. Dividend Aristocrats. 50+ years of history.
            Sub-100ms responses. Built by income investors, for income investors.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/api"
              className="px-8 py-3.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
            >
              Documentation
            </Link>
            <a
              href={`${API_CONFIG.baseUrl}/health`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-3.5 bg-white border-2 border-purple-200 text-gray-700 rounded-lg font-medium hover:border-purple-400 hover:text-purple-700 transition-all"
            >
              API Status
            </a>
          </div>
        </div>
      </div>

        {/* Stats */}
        <div className="container mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-24 max-w-4xl mx-auto">
          <StatCard number={STOCK_COUNT} label="Dividend Stocks" />
          <StatCard number="50+ yrs" label="History" />
          <StatCard number="<100ms" label="Response" />
          <StatCard number="FREE" label="For Most Users" highlight={true} />
        </div>
        </div>

        {/* Free Forever Banner */}
        <div className="container mx-auto px-6">
        <div className="mt-24 max-w-5xl mx-auto">
          <div className="bg-gradient-to-br from-green-600 to-blue-600 rounded-2xl p-12 text-white relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32"></div>
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full -ml-24 -mb-24"></div>

            <div className="relative z-10 text-center">
              <div className="text-6xl mb-6">💰</div>
              <h2 className="text-4xl font-bold mb-4">
                Track Prices & Dividends for Free
              </h2>
              <p className="text-2xl text-green-100 mb-8">
                Free tier gives you the essentials. Upgrade for advanced metrics.
              </p>

              <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto mb-8">
                <div className="bg-white/10 backdrop-blur rounded-xl p-6">
                  <div className="text-4xl font-bold mb-2">20</div>
                  <div className="text-green-100">Stocks Tracked</div>
                </div>
                <div className="bg-white/10 backdrop-blur rounded-xl p-6">
                  <div className="text-4xl font-bold mb-2">5x/day</div>
                  <div className="text-green-100">Price Checks</div>
                </div>
                <div className="bg-white/10 backdrop-blur rounded-xl p-6">
                  <div className="text-4xl font-bold mb-2">$0</div>
                  <div className="text-green-100">Forever</div>
                </div>
              </div>

              <div className="bg-white/20 backdrop-blur rounded-lg p-6 max-w-2xl mx-auto mb-6">
                <p className="text-lg font-semibold mb-2">Free Tier Includes:</p>
                <div className="grid md:grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-300" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>5,000 API calls/month</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-300" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Price & dividend data</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-300" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Google Sheets integration</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-300" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Excel VBA module</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-300" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>No credit card required</span>
                  </div>
                </div>
                <p className="text-xs text-green-200 mt-4 border-t border-white/20 pt-4">
                  <Link href="/pricing" className="underline font-semibold">Upgrade to Starter ($9/mo)</Link> for full attribute access: PE ratio, volume, market cap, dividend history, Aristocrat detection, and more
                </p>
              </div>

              <p className="text-sm text-green-200 mb-6">
                Your 20-stock portfolio checking prices 5x/day = ~3,000 calls/month (30% of free tier)
              </p>

              <Link
                href="/integrations/google-sheets"
                className="inline-flex items-center gap-2 px-8 py-4 bg-white text-green-700 rounded-lg font-bold hover:bg-green-50 transition-all shadow-xl text-lg"
              >
                <span>Get Started Free</span>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
        </div>

        {/* Google Sheets & Excel Integration */}
        <div className="container mx-auto px-6">
        <div className="mt-24 max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-green-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">
                Drop-in Replacement for GOOGLEFINANCE()
              </span>
            </h2>
            <p className="text-xl text-gray-600">
              100% parity with Google Sheets, but with superior dividend data
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Before: GOOGLEFINANCE */}
            <div className="bg-white rounded-2xl p-8 border-2 border-gray-300 relative">
              <div className="absolute -top-4 left-8 px-4 py-1 bg-gray-500 text-white text-xs font-medium rounded-full">
                BEFORE
              </div>
              <h3 className="text-lg font-bold text-gray-700 mb-4">Google Sheets GOOGLEFINANCE()</h3>
              <pre className="text-sm font-mono text-gray-600 overflow-x-auto bg-gray-50 p-4 rounded-lg">
{`=GOOGLEFINANCE("AAPL", "price")
=GOOGLEFINANCE("AAPL", "high52")
=GOOGLEFINANCE("AAPL", "low52")
=GOOGLEFINANCE("AAPL", "pe")

❌ Multiple formulas needed
❌ Limited dividend data
❌ Stale data
❌ No Aristocrats/Kings`}
              </pre>
            </div>

            {/* After: Divv API */}
            <div className="bg-gradient-to-br from-green-50 via-blue-50 to-purple-50 rounded-2xl p-8 border-2 border-green-500 relative shadow-lg">
              <div className="absolute -top-4 left-8 px-4 py-1 bg-green-600 text-white text-xs font-medium rounded-full">
                AFTER: DIVV()
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-4">Same Syntax. Better Data.</h3>
              <pre className="text-sm font-mono text-gray-800 overflow-x-auto bg-white p-4 rounded-lg border border-green-200">
{`=DIVV("AAPL", "price")
=DIVV("AAPL", "yearHigh")
=DIVV("AAPL", "dividendYield")
=DIVV("AAPL", "peRatio")

✅ Familiar GOOGLEFINANCE() syntax
✅ Complete dividend history
✅ Aristocrats/Kings included
✅ 50+ years of history
✅ Free tier: 5,000 calls/mo`}
              </pre>
            </div>
          </div>

          <div className="mt-8 text-center flex gap-4 justify-center">
            <Link
              href="/integrations/google-sheets"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg font-medium hover:from-green-700 hover:to-blue-700 transition-all shadow-lg"
            >
              <span>Google Sheets Setup →</span>
            </Link>
            <a
              href="/DIVV.gs"
              download
              className="inline-flex items-center gap-2 px-6 py-3 bg-white border-2 border-green-600 text-green-700 rounded-lg font-medium hover:bg-green-50 transition-all"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
              </svg>
              <span>Download Script</span>
            </a>
          </div>
        </div>
        </div>

        {/* Dividend-Specific Features */}
        <div className="container mx-auto px-6">
        <div className="mt-24 max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-green-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">
                Why Dividend Investors Choose Divv
              </span>
            </h2>
            <p className="text-xl text-gray-600">
              Features you won't find in generic financial APIs
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <DividendFeatureCard
              icon="👑"
              title="Aristocrats & Kings"
              description="Instantly identify stocks with 25+ or 50+ years of consecutive dividend increases. No manual calculation needed."
              highlight="25+ years tracked automatically"
            />
            <DividendFeatureCard
              icon="📅"
              title="Complete Dividend Calendar"
              description="Historical dividends + future ex-dates. Track monthly, quarterly, and special dividends with precise payment schedules."
              highlight="50+ years of history"
            />
            <DividendFeatureCard
              icon="📊"
              title="Dividend Metrics"
              description="Yield, payout ratio, growth rates, sustainability scores. Everything an income investor needs in one endpoint."
              highlight="All metrics, one API call"
            />
            <DividendFeatureCard
              icon="🎯"
              title="Pre-Built Screeners"
              description="High-yield, monthly payers, Aristocrats, Kings, high-growth dividends. Start analyzing immediately."
              highlight="5+ curated screeners"
            />
            <DividendFeatureCard
              icon="📈"
              title="ETF Income Analysis"
              description="Track covered call ETFs, REITs, BDCs, and income funds. AUM, expense ratios, holdings composition."
              highlight="8,000+ ETFs covered"
            />
            <DividendFeatureCard
              icon="⚡"
              title="Spreadsheet Ready"
              description="Google Sheets + Excel compatible. GOOGLEFINANCE() parity means drop-in replacement for your existing models."
              highlight="Zero migration friction"
            />
          </div>
        </div>
        </div>

        {/* Competitive Advantage */}
        <div className="container mx-auto px-6">
        <div className="mt-24 max-w-6xl mx-auto">
          <div className="bg-gradient-to-br from-green-900 to-blue-900 rounded-2xl p-12 text-white">
            <div className="text-center mb-10">
              <h2 className="text-4xl font-bold mb-4">
                Why Not Just Use a Generic API?
              </h2>
              <p className="text-xl text-green-100">
                Because dividend data has unique requirements that generic APIs ignore
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-8 mb-8">
              <div className="bg-white/10 rounded-xl p-6 backdrop-blur">
                <div className="text-red-300 font-bold mb-3 text-sm">❌ GENERIC APIs (Polygon, Alpha Vantage, FMP)</div>
                <ul className="space-y-2 text-white/90">
                  <li className="flex items-start gap-2">
                    <span className="text-red-400">•</span>
                    <span>No Aristocrat/King identification</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-400">•</span>
                    <span>Missing historical dividends (&gt;10 years)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-400">•</span>
                    <span>No dividend growth metrics</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-400">•</span>
                    <span>Expensive real-time data you don't need</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-400">•</span>
                    <span>$50-200/month entry pricing</span>
                  </li>
                </ul>
              </div>

              <div className="bg-white/10 rounded-xl p-6 backdrop-blur border-2 border-green-400">
                <div className="text-green-300 font-bold mb-3 text-sm">✅ DIVV API (Dividend Specialist)</div>
                <ul className="space-y-2 text-white">
                  <li className="flex items-start gap-2">
                    <span className="text-green-400">✓</span>
                    <span className="font-medium">Automatic Aristocrat/King detection</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-400">✓</span>
                    <span className="font-medium">50+ years of dividend history</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-400">✓</span>
                    <span className="font-medium">Complete growth & sustainability metrics</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-400">✓</span>
                    <span className="font-medium">EOD data optimized for income investing</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-400">✓</span>
                    <span className="font-medium">$9/month (5-20x cheaper)</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="text-center">
              <p className="text-2xl font-bold text-green-300 mb-4">
                Save 80-95% vs. generic APIs. Get better dividend data.
              </p>
              <Link
                href="/pricing"
                className="inline-flex items-center gap-2 px-8 py-4 bg-white text-gray-900 rounded-lg font-bold hover:bg-green-50 transition-all shadow-xl"
              >
                <span>See Pricing Comparison</span>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
        </div>

        {/* Exchanges Supported */}
        <div className="container mx-auto px-6">
        <div className="mt-24 max-w-6xl mx-auto">
          <div className="bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 rounded-3xl p-12 text-white relative overflow-hidden">
            {/* Decorative elements */}
            <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl -mr-48 -mt-48"></div>
            <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl -ml-48 -mb-48"></div>

            <div className="relative z-10">
              <div className="text-center mb-12">
                <div className="inline-block mb-4 px-4 py-2 bg-white/10 backdrop-blur rounded-full">
                  <span className="text-blue-200 text-sm font-semibold">🌎 GLOBAL COVERAGE</span>
                </div>
                <h2 className="text-4xl font-bold mb-4">
                  {STOCK_COUNT} Dividend Stocks
                </h2>
                <p className="text-xl text-blue-100">
                  Comprehensive coverage across North American exchanges
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-6 mb-8">
                {/* US Exchanges Card */}
                <div className="bg-white/10 backdrop-blur rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center text-2xl">
                      🇺🇸
                    </div>
                    <div>
                      <h3 className="font-bold text-lg">US Exchanges</h3>
                      <p className="text-blue-200 text-sm">Major Markets</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                      <span>NYSE • NASDAQ • AMEX</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                      <span>CBOE • BATS • IEX</span>
                    </div>
                  </div>
                </div>

                {/* Canadian Exchanges Card */}
                <div className="bg-white/10 backdrop-blur rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-orange-500 rounded-lg flex items-center justify-center text-2xl">
                      🇨🇦
                    </div>
                    <div>
                      <h3 className="font-bold text-lg">Canadian</h3>
                      <p className="text-blue-200 text-sm">TSX & More</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                      <span>TSX • TSX Venture</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <div className="w-2 h-2 bg-orange-400 rounded-full"></div>
                      <span>CSE • NEO Exchange</span>
                    </div>
                  </div>
                </div>

                {/* OTC Markets Card */}
                <div className="bg-white/10 backdrop-blur rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-teal-500 rounded-lg flex items-center justify-center text-2xl">
                      📊
                    </div>
                    <div>
                      <h3 className="font-bold text-lg">OTC Markets</h3>
                      <p className="text-blue-200 text-sm">Alternative Trading</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      <span>OTCQX • OTCQB</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <div className="w-2 h-2 bg-teal-400 rounded-full"></div>
                      <span>Pink Sheets • Grey Market</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white/5 backdrop-blur rounded-xl p-4 text-center border border-white/10">
                  <div className="text-3xl font-bold text-blue-300 mb-1">14</div>
                  <div className="text-xs text-blue-200 uppercase tracking-wide">Exchanges</div>
                </div>
                <div className="bg-white/5 backdrop-blur rounded-xl p-4 text-center border border-white/10">
                  <div className="text-3xl font-bold text-purple-300 mb-1">24K+</div>
                  <div className="text-xs text-blue-200 uppercase tracking-wide">Symbols</div>
                </div>
                <div className="bg-white/5 backdrop-blur rounded-xl p-4 text-center border border-white/10">
                  <div className="text-3xl font-bold text-green-300 mb-1">Real-time</div>
                  <div className="text-xs text-blue-200 uppercase tracking-wide">Updates</div>
                </div>
                <div className="bg-white/5 backdrop-blur rounded-xl p-4 text-center border border-white/10">
                  <div className="text-3xl font-bold text-orange-300 mb-1">50+ yrs</div>
                  <div className="text-xs text-blue-200 uppercase tracking-wide">History</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        </div>

        {/* Use Case Examples */}
        <div className="container mx-auto px-6">
        <div className="mt-24 max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-green-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">
                Built for Income Investors
              </span>
            </h2>
            <p className="text-xl text-gray-600">
              See how dividend investors are using Divv API
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <UseCaseCard
              title="Find Dividend Aristocrats"
              description="Identify stable, reliable dividend growers with 25+ years of consecutive increases"
              code={`curl "api.divv.com/v1/screeners/dividend-aristocrats?limit=10"

# Returns stocks like:
# JNJ - 61 years of increases
# PG - 67 years of increases
# KO - 61 years of increases`}
            />

            <UseCaseCard
              title="Track Monthly Income"
              description="Build a portfolio with monthly dividend payments for consistent cash flow"
              code={`curl "api.divv.com/v1/screeners/monthly-payers?min_yield=5"

# Find monthly payers like:
# JEPI, JEPQ, O, STAG, MAIN
# Perfect for retirement income`}
            />

            <UseCaseCard
              title="Analyze Dividend Growth"
              description="Find stocks with strong dividend growth rates for compounding income"
              code={`curl "api.divv.com/v1/stocks/MSFT/metrics"

# Get complete metrics:
# - Current yield: 0.8%
# - 5yr growth rate: 10.2%
# - Payout ratio: 25%
# - Years of increases: 19`}
            />

            <UseCaseCard
              title="Google Sheets Integration"
              description="Use =DIVV() just like GOOGLEFINANCE() - familiar syntax, better data"
              code={`// Add to Google Sheets (Tools > Script Editor)
function DIVV(symbol, attribute) {
  const url = \`api.divv.com/v1/stocks/\${symbol}/quote\`;
  const response = UrlFetchApp.fetch(url);
  const data = JSON.parse(response.getContentText());
  return data[attribute] || data;
}

// Then use like GOOGLEFINANCE:
=DIVV("AAPL", "price")
=DIVV("JNJ", "dividendYield")
=DIVV("PG", "yearHigh")`}
            />
          </div>

          <div className="text-center">
            <Link
              href="/api"
              className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg font-bold hover:from-green-700 hover:to-blue-700 transition-all shadow-lg text-lg"
            >
              <span>Explore All Endpoints</span>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
        </div>
      </div>
    </div>
  );
}

function DividendFeatureCard({ icon, title, description, highlight }: {
  icon: string;
  title: string;
  description: string;
  highlight: string;
}) {
  return (
    <div className="group p-6 rounded-xl bg-white border-2 border-gray-200 hover:border-green-500 hover:shadow-xl transition-all relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-green-50 to-blue-50 opacity-0 group-hover:opacity-100 transition-opacity"></div>
      <div className="relative">
        <div className="text-4xl mb-3">{icon}</div>
        <h3 className="text-xl font-bold mb-2 text-gray-900">{title}</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-3">{description}</p>
        <div className="inline-block px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full">
          {highlight}
        </div>
      </div>
    </div>
  );
}

function UseCaseCard({ title, description, code }: {
  title: string;
  description: string;
  code: string;
}) {
  return (
    <div className="bg-white rounded-xl border-2 border-gray-200 overflow-hidden hover:border-blue-500 transition-all shadow-sm">
      <div className="p-6 bg-gradient-to-r from-green-50 to-blue-50">
        <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-600 text-sm">{description}</p>
      </div>
      <div className="bg-slate-800 p-6">
        <pre className="text-base text-white font-mono overflow-x-auto leading-relaxed bg-slate-800">
          <code className="text-white">{code}</code>
        </pre>
      </div>
    </div>
  );
}

function StatCard({ number, label, highlight }: { number: string; label: string; highlight?: boolean }) {
  return (
    <div className="text-center">
      <div className={`text-4xl font-bold mb-2 ${highlight ? 'text-blue-600' : 'text-gray-900'}`}>{number}</div>
      <div className={`text-sm uppercase tracking-wider ${highlight ? 'text-blue-500 font-semibold' : 'text-gray-500'}`}>{label}</div>
    </div>
  );
}

function ExchangeLogo({ name, fullName }: { name: string; fullName: string }) {
  return (
    <div className="flex flex-col items-center justify-center group cursor-default">
      <div className="w-24 h-24 rounded-lg bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-purple-200 flex items-center justify-center mb-3 group-hover:border-purple-400 group-hover:shadow-lg transition-all">
        <div className="text-2xl font-bold bg-gradient-to-br from-blue-600 to-purple-600 bg-clip-text text-transparent group-hover:from-blue-700 group-hover:to-purple-700 transition-all tracking-tight">
          {name}
        </div>
      </div>
      <div className="text-xs text-gray-600 text-center font-medium max-w-[120px]">
        {fullName}
      </div>
    </div>
  );
}
