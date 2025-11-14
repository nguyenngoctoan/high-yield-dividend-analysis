import Link from 'next/link'
import { ArrowLeft, Zap, Bug, Settings, AlertCircle, CheckCircle } from 'lucide-react'

export default function ChangelogPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
          <h1 className="text-4xl font-bold text-slate-900 mb-3">Changelog</h1>
          <p className="text-lg text-slate-600">
            Stay up to date with Divv API new features, improvements, and bug fixes
          </p>
        </div>
      </div>

      {/* Changelog Timeline */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="space-y-12">

          {/* Version 1.1.0 */}
          <VersionSection
            version="1.1.0"
            date="November 13, 2025"
            isLatest={true}
          >
            <ChangeItem
              type="feature"
              title="Preset Date Ranges"
              description="Added convenient preset date ranges for price and dividend queries: 1M, 3M, 6M, YTD, 1Y, 2Y, 5Y, MAX. No more manual date calculations!"
            />
            <ChangeItem
              type="feature"
              title="Sort Control"
              description="New sort parameter for historical data endpoints. Sort by date ascending or descending to get data in your preferred order."
            />
            <ChangeItem
              type="feature"
              title="Adjusted Price Support"
              description="Added adjusted=true parameter to get split and dividend-adjusted historical prices. Essential for accurate backtesting and performance analysis."
            />
            <ChangeItem
              type="improvement"
              title="Enhanced Dividend Metrics"
              description="Improved dividend metrics calculation with more accurate TTM (trailing twelve months) dividend totals and growth rate calculations."
            />
            <ChangeItem
              type="improvement"
              title="Better Error Messages"
              description="More descriptive error messages with actionable suggestions when queries fail or return no data."
            />
            <ChangeItem
              type="fix"
              title="Fixed Date Range Edge Cases"
              description="Resolved issues with date range queries at month and year boundaries. All date ranges now return consistent results."
            />
          </VersionSection>

          {/* Version 1.0.2 */}
          <VersionSection
            version="1.0.2"
            date="November 10, 2025"
          >
            <ChangeItem
              type="improvement"
              title="Performance Optimization"
              description="Reduced average response time from 120ms to <100ms through database query optimization and intelligent caching."
            />
            <ChangeItem
              type="improvement"
              title="Expanded Exchange Coverage"
              description="Added support for Canadian exchanges (TSX, TSXV, CSE) and OTC markets (OTCM, OTCX). Now covering 24,000+ symbols."
            />
            <ChangeItem
              type="fix"
              title="Fixed Dividend Calendar Timezone Issues"
              description="Corrected timezone handling for ex-dividend dates. All dates now correctly displayed in market timezone (ET)."
            />
            <ChangeItem
              type="fix"
              title="ETF Holdings Data Accuracy"
              description="Fixed data sync issues with ETF holdings. Holdings now update daily and reflect accurate positions."
            />
          </VersionSection>

          {/* Version 1.0.1 */}
          <VersionSection
            version="1.0.1"
            date="November 5, 2025"
          >
            <ChangeItem
              type="feature"
              title="Dividend Screeners"
              description="Added new screener endpoints for high-yield stocks and dividend growth stocks with customizable filters."
            />
            <ChangeItem
              type="feature"
              title="Sector Performance Analytics"
              description="New endpoint to analyze dividend yield and performance by sector. Ideal for sector rotation strategies."
            />
            <ChangeItem
              type="improvement"
              title="Rate Limiting Headers"
              description="Added X-RateLimit-* headers to all responses so you can track your usage and avoid hitting limits."
            />
            <ChangeItem
              type="fix"
              title="Fixed Special Character Handling"
              description="Corrected handling of stock symbols with special characters (e.g., BRK.B, BF.A) in search queries."
            />
          </VersionSection>

          {/* Version 1.0.0 */}
          <VersionSection
            version="1.0.0"
            date="November 1, 2025"
          >
            <ChangeItem
              type="feature"
              title="Initial Public Release"
              description="First public release of the Dividend API with comprehensive stock data, dividend history, and ETF metrics."
            />
            <ChangeItem
              type="feature"
              title="23+ REST API Endpoints"
              description="Complete REST API covering stocks, prices, dividends, ETFs, analytics, and search functionality."
            />
            <ChangeItem
              type="feature"
              title="API Key Authentication"
              description="Secure API key authentication with three tiers: Free (1,000 req/month), Pro (100,000 req/month), and Enterprise (unlimited)."
            />
            <ChangeItem
              type="feature"
              title="Token Bucket Rate Limiting"
              description="Fair and predictable rate limiting using token bucket algorithm. Never get surprised by rate limit errors."
            />
            <ChangeItem
              type="feature"
              title="Covered Call ETF IV Data"
              description="Industry-first: Implied Volatility (IV) data for covered call ETFs to help predict future distributions."
            />
            <ChangeItem
              type="feature"
              title="Multi-Exchange Support"
              description="Coverage of major US exchanges (NYSE, NASDAQ, AMEX, CBOE) and alternative trading systems."
            />
          </VersionSection>

          {/* Beta Releases */}
          <VersionSection
            version="0.9.0 Beta"
            date="October 20, 2025"
            isBeta={true}
          >
            <ChangeItem
              type="feature"
              title="Beta Launch"
              description="Limited beta release to 100 selected testers. Gathered feedback on API design, performance, and feature requests."
            />
            <ChangeItem
              type="improvement"
              title="Documentation Portal"
              description="Launched comprehensive documentation with code examples in multiple languages (curl, Python, JavaScript, etc.)"
            />
          </VersionSection>

        </div>

        {/* Subscribe to Updates */}
        <div className="mt-16 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-200">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-slate-900 mb-3">
              Stay Updated
            </h3>
            <p className="text-slate-600 mb-6 max-w-2xl mx-auto">
              Get notified about new features, improvements, and important updates via email or RSS feed.
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <Link
                href="/subscribe"
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Subscribe to Updates
              </Link>
              <Link
                href="/changelog/rss"
                className="px-6 py-3 bg-white text-blue-600 rounded-lg font-semibold border-2 border-blue-600 hover:bg-blue-50 transition-colors"
              >
                RSS Feed
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function VersionSection({
  version,
  date,
  isLatest = false,
  isBeta = false,
  children
}: {
  version: string
  date: string
  isLatest?: boolean
  isBeta?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-slate-200" />

      {/* Version header */}
      <div className="relative pl-12">
        {/* Timeline dot */}
        <div className={`absolute left-0 top-1 -translate-x-[7px] w-4 h-4 rounded-full border-4 ${
          isLatest ? 'bg-blue-600 border-blue-200' : 'bg-white border-slate-300'
        }`} />

        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-2xl font-bold text-slate-900">
              v{version}
            </h2>
            {isLatest && (
              <span className="px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full">
                LATEST
              </span>
            )}
            {isBeta && (
              <span className="px-3 py-1 bg-amber-100 text-amber-800 text-xs font-bold rounded-full">
                BETA
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500">{date}</p>
        </div>

        {/* Changes */}
        <div className="space-y-4">
          {children}
        </div>
      </div>
    </div>
  )
}

function ChangeItem({
  type,
  title,
  description
}: {
  type: 'feature' | 'improvement' | 'fix' | 'breaking'
  title: string
  description: string
}) {
  const config = {
    feature: {
      icon: Zap,
      iconColor: 'text-green-600',
      iconBg: 'bg-green-100',
      label: 'New',
      labelColor: 'bg-green-100 text-green-800'
    },
    improvement: {
      icon: Settings,
      iconColor: 'text-blue-600',
      iconBg: 'bg-blue-100',
      label: 'Improved',
      labelColor: 'bg-blue-100 text-blue-800'
    },
    fix: {
      icon: Bug,
      iconColor: 'text-purple-600',
      iconBg: 'bg-purple-100',
      label: 'Fixed',
      labelColor: 'bg-purple-100 text-purple-800'
    },
    breaking: {
      icon: AlertCircle,
      iconColor: 'text-red-600',
      iconBg: 'bg-red-100',
      label: 'Breaking',
      labelColor: 'bg-red-100 text-red-800'
    }
  }

  const { icon: Icon, iconColor, iconBg, label, labelColor } = config[type]

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 hover:border-slate-300 transition-colors">
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-lg ${iconBg} flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${iconColor}`} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${labelColor}`}>
              {label}
            </span>
            <h3 className="font-semibold text-slate-900">{title}</h3>
          </div>
          <p className="text-slate-600 text-sm leading-relaxed">
            {description}
          </p>
        </div>
      </div>
    </div>
  )
}
