import Link from 'next/link';
import Header from '@/components/Header';
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
          <div className="inline-block mb-6 px-4 py-1.5 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-full text-sm font-medium">
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent font-semibold">
              Production Ready
            </span>
          </div>
          <h1 className="text-7xl font-bold mb-6 tracking-tight">
            <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Divv API
            </span>
          </h1>
          <p className="text-xl text-gray-700 mb-10 leading-relaxed max-w-2xl mx-auto">
            A modern, fast API for dividend investors. Get stock data, dividend calendars,
            and analytics in milliseconds.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/api"
              className="px-8 py-3.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
            >
              Documentation
            </Link>
            <a
              href="http://localhost:8000/health"
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
          <StatCard number="24,842" label="Stocks" />
          <StatCard number="11" label="Endpoints" />
          <StatCard number="<100ms" label="Response" />
          <StatCard number="100%" label="Uptime" />
        </div>
        </div>

        {/* What's New Banner */}
        <div className="container mx-auto px-6">
        <div className="mt-24 max-w-5xl mx-auto">
          <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-2xl p-8 border border-purple-200">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center shadow-lg">
                  <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  What's New in v1.1.0
                </h3>
                <p className="text-gray-700 mb-4">
                  Enhanced API with industry-leading features: preset date ranges, flexible filtering, and more control over your queries.
                </p>
                <div className="grid md:grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">Preset date ranges</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">Sort control</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">Adjusted prices</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        </div>

        {/* Features Grid */}
        <div className="container mx-auto px-6">
        <div className="grid md:grid-cols-3 gap-6 mt-16 max-w-5xl mx-auto">
          <FeatureCard
            title="Fast & Reliable"
            description="Sub-100ms response times with 100% uptime"
            gradient="from-blue-600 to-indigo-600"
          />
          <FeatureCard
            title="Complete Data"
            description="24,000+ stocks with dividend history"
            gradient="from-indigo-600 to-purple-600"
          />
          <FeatureCard
            title="Easy to Use"
            description="RESTful API with clear documentation"
            gradient="from-purple-600 to-blue-600"
          />
        </div>
        </div>

        {/* Exchanges Supported */}
        <div className="container mx-auto px-6">
        <div className="mt-24 max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">
              <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Exchanges Supported
              </span>
            </h2>
            <p className="text-gray-600">Comprehensive coverage across major North American exchanges</p>
          </div>

          <div className="bg-white rounded-2xl p-12 border-2 border-purple-100">
            {/* Major US Exchanges */}
            <div className="mb-12">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-6 text-center">
                Major US Exchanges
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                <ExchangeLogo name="NYSE" fullName="New York Stock Exchange" />
                <ExchangeLogo name="NASDAQ" fullName="NASDAQ Stock Market" />
                <ExchangeLogo name="AMEX" fullName="NYSE American" />
                <ExchangeLogo name="CBOE" fullName="Chicago Board Options Exchange" />
              </div>
            </div>

            {/* Alternative Trading Systems */}
            <div className="mb-12 pb-12 border-b border-gray-100">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-6 text-center">
                Alternative Trading Systems
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                <ExchangeLogo name="BATS" fullName="BATS Global Markets" />
                <ExchangeLogo name="EDGX" fullName="EDGX Exchange" />
                <ExchangeLogo name="BZX" fullName="BATS BZX Exchange" />
                <ExchangeLogo name="IEX" fullName="Investors Exchange" />
              </div>
            </div>

            {/* Canadian Exchanges */}
            <div className="mb-8">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-6 text-center">
                Canadian Exchanges
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                <ExchangeLogo name="TSX" fullName="Toronto Stock Exchange" />
                <ExchangeLogo name="TSXV" fullName="TSX Venture Exchange" />
                <ExchangeLogo name="CSE" fullName="Canadian Securities Exchange" />
                <ExchangeLogo name="NEO" fullName="NEO Exchange" />
              </div>
            </div>

            {/* OTC Markets */}
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-6 text-center">
                OTC Markets
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-8 justify-items-center">
                <ExchangeLogo name="OTCM" fullName="OTC Markets Group" />
                <ExchangeLogo name="OTCX" fullName="OTC Pink" />
              </div>
            </div>
          </div>

          <div className="text-center mt-8">
            <p className="text-sm text-gray-600">
              Coverage includes <span className="font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">24,000+ symbols</span> across all supported exchanges
            </p>
          </div>
        </div>
        </div>

        {/* Code Example */}
        <div className="container mx-auto px-6">
        <div className="mt-24 max-w-3xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-3">
              <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Quick Start
              </span>
            </h2>
            <p className="text-gray-600">Get started in seconds with a simple HTTP request</p>
          </div>
          <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 rounded-2xl p-8 border-2 border-purple-200">
            <pre className="text-sm text-gray-800 font-mono overflow-x-auto">
{`curl "http://localhost:8000/v1/search?q=AAPL"

{
  "symbol": "AAPL",
  "company": "Apple Inc.",
  "exchange": "NASDAQ",
  "relevance": 1.0
}`}
            </pre>
          </div>
        </div>
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ title, description, gradient }: {
  title: string;
  description: string;
  gradient: string;
}) {
  return (
    <div className="group p-6 rounded-xl bg-white border-2 border-gray-200 hover:border-transparent hover:shadow-xl transition-all relative overflow-hidden">
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-5 transition-opacity`}></div>
      <div className="relative">
        <h3 className={`text-lg font-semibold mb-2 bg-gradient-to-r ${gradient} bg-clip-text text-transparent`}>{title}</h3>
        <p className="text-gray-600 text-sm leading-relaxed">{description}</p>
      </div>
    </div>
  );
}

function StatCard({ number, label }: { number: string; label: string }) {
  return (
    <div className="text-center">
      <div className="text-4xl font-bold text-gray-900 mb-2">{number}</div>
      <div className="text-sm text-gray-500 uppercase tracking-wider">{label}</div>
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
