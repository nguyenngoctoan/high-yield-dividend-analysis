import Link from 'next/link'
import { ArrowLeft, Zap, Bug, Settings, AlertCircle, CheckCircle } from 'lucide-react'
import { STOCK_COUNT } from '@/lib/config'

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

          {/* Version 0.1.11 - GOOGLEFINANCE Parity */}
          <VersionSection
            version="0.1.11"
            date="November 14, 2025"
            isLatest={true}
          >
            <ChangeItem
              type="feature"
              title="GOOGLEFINANCE() Parity - Quote Endpoint"
              description="New /v1/stocks/{symbol}/quote endpoint with 100% feature parity with Google Sheets GOOGLEFINANCE() function. Get all price data, moving averages, 52-week ranges, fundamentals, and superior dividend data in a single API call."
            />
            <ChangeItem
              type="feature"
              title="13 New Fundamental Data Fields"
              description={`Added shares outstanding, 52-week high/low, average volume, daily change, 50-day and 200-day moving averages, and EPS. Coverage: ${STOCK_COUNT} stocks.`}
            />
            <ChangeItem
              type="improvement"
              title="Ultra-Fast Batch Updates"
              description="Optimized daily updates to process 16,000+ symbols in 1-5 minutes (16-46x faster). Batch fetches 500 symbols per API call using FMP batch quote endpoint."
            />
            <ChangeItem
              type="improvement"
              title="Enhanced Bulk Endpoints"
              description="Updated POST /v1/bulk/stocks and POST /v1/bulk/latest to include all new fundamental fields. Get comprehensive data for multiple stocks in one request."
            />
          </VersionSection>

          {/* Version 0.1.10 */}
          <VersionSection
            version="0.1.10"
            date="November 13, 2025"
          >
            <ChangeItem
              type="feature"
              title="Stock Split History"
              description="New GET /v1/stocks/{symbol}/splits endpoint to retrieve complete stock split history with ratios and dates."
            />
            <ChangeItem
              type="feature"
              title="Dividend Aristocrats & Kings"
              description="Automatic identification of Dividend Aristocrats (25+ years of increases) and Dividend Kings (50+ years) via GET /v1/stocks/{symbol}/metrics endpoint."
            />
            <ChangeItem
              type="feature"
              title="Stock Fundamentals Endpoint"
              description="New GET /v1/stocks/{symbol}/fundamentals providing market cap, P/E ratio, sector, industry, employee count, and IPO date."
            />
          </VersionSection>

          {/* Version 0.1.9 */}
          <VersionSection
            version="0.1.9"
            date="November 12, 2025"
          >
            <ChangeItem
              type="improvement"
              title="Dividend Metrics Enhancement"
              description="Enhanced GET /v1/stocks/{symbol}/metrics with consecutive payment tracking, growth streaks, and Aristocrat/King status calculation."
            />
          </VersionSection>

          {/* Version 0.1.8 */}
          <VersionSection
            version="0.1.8"
            date="November 8, 2025"
          >
            <ChangeItem
              type="feature"
              title="Google OAuth Authentication"
              description="Secure user authentication with Google OAuth 2.0. Users can sign in with their Google accounts for API key management."
            />
            <ChangeItem
              type="feature"
              title="Tier-Based Access Control"
              description="Four access tiers (Free, Starter, Premium, Professional) with progressive feature unlocking, rate limits, and bulk operation quotas."
            />
          </VersionSection>

          {/* Version 0.1.7 */}
          <VersionSection
            version="0.1.7"
            date="November 5, 2025"
          >
            <ChangeItem
              type="feature"
              title="Next.js Documentation Site"
              description="Comprehensive documentation portal with interactive examples, API reference, code samples, and changelog at localhost:3000."
            />
            <ChangeItem
              type="improvement"
              title="API Documentation Improvements"
              description="Added code examples in multiple languages (curl, Python, JavaScript) for all endpoints."
            />
          </VersionSection>

          {/* Version 0.1.6 */}
          <VersionSection
            version="0.1.6"
            date="November 1, 2025"
          >
            <ChangeItem
              type="feature"
              title="ETF Research Tools"
              description="Complete ETF endpoints including holdings composition, AUM tracking, expense ratios, and investment strategy classification (80+ strategies)."
            />
            <ChangeItem
              type="feature"
              title="Advanced Screeners"
              description="Pre-built screeners for high-yield stocks, monthly dividend payers, dividend growth, and sector-based filtering."
            />
            <ChangeItem
              type="feature"
              title="Portfolio Analytics"
              description="POST /v1/analytics/portfolio endpoint for income projections, yield analysis, and distribution tracking."
            />
          </VersionSection>

          {/* Version 0.1.5 */}
          <VersionSection
            version="0.1.5"
            date="October 28, 2025"
          >
            <ChangeItem
              type="feature"
              title="Data Source Tracking System"
              description="Intelligent system that discovers and caches which data sources (FMP, Yahoo, Alpha Vantage) have specific data for each symbol. Reduces API calls by 60-80%."
            />
            <ChangeItem
              type="feature"
              title="Implied Volatility Discovery"
              description="Alpha Vantage Premium integration for IV data on covered call ETFs. Industry-first feature for predicting ETF distributions."
            />
          </VersionSection>

          {/* Version 0.1.4 */}
          <VersionSection
            version="0.1.4"
            date="October 25, 2025"
          >
            <ChangeItem
              type="feature"
              title="Multi-Source API Integration"
              description="Hybrid data fetching with automatic fallback: FMP (primary) → Yahoo Finance → Alpha Vantage. Ensures maximum data availability."
            />
            <ChangeItem
              type="improvement"
              title="Modular Architecture Refactoring"
              description="Complete codebase refactor from 3,821-line monolithic script to 16 focused modules. 90% code reduction in main script (376 lines)."
            />
          </VersionSection>

          {/* Version 0.1.3 */}
          <VersionSection
            version="0.1.3"
            date="October 20, 2025"
          >
            <ChangeItem
              type="feature"
              title="REST API Foundation"
              description="Initial FastAPI implementation with core endpoints for stocks, dividends, and prices. OpenAPI/Swagger documentation at /docs."
            />
            <ChangeItem
              type="feature"
              title="Supabase Integration"
              description="Database layer using Supabase (local container). Tables for stocks, prices, dividends, ETF holdings, and splits."
            />
          </VersionSection>

          {/* Version 0.1.2 */}
          <VersionSection
            version="0.1.2"
            date="October 15, 2025"
          >
            <ChangeItem
              type="feature"
              title="Automated Daily Updates"
              description="Cron-based automation for daily price updates, dividend calendar refresh, and ETF holdings sync."
            />
            <ChangeItem
              type="improvement"
              title="Rate Limiting Implementation"
              description="Adaptive rate limiters for all data sources with automatic backoff on 429 errors. FMP: 144 concurrent, AV: 2 concurrent, Yahoo: 3 concurrent."
            />
          </VersionSection>

          {/* Version 0.1.1 */}
          <VersionSection
            version="0.1.1"
            date="October 10, 2025"
          >
            <ChangeItem
              type="feature"
              title="Dividend History Collection"
              description="Historical dividend payment collection with ex-dates, payment dates, and amounts. 686K+ dividend records."
            />
            <ChangeItem
              type="feature"
              title="Price History Collection"
              description="Daily OHLCV price data collection with 20+ years of history. 20M+ price bars across 24K+ symbols."
            />
            <ChangeItem
              type="improvement"
              title="Symbol Validation"
              description="Enhanced symbol validation with price activity check (7 days) and dividend history validation (1 year)."
            />
          </VersionSection>

          {/* Version 0.1.0 */}
          <VersionSection
            version="0.1.0"
            date="October 1, 2025"
          >
            <ChangeItem
              type="feature"
              title="Initial Project Setup"
              description="High-yield dividend analysis system with Python data collection scripts. Support for FMP API integration and basic stock price fetching."
            />
            <ChangeItem
              type="feature"
              title="Symbol Discovery"
              description="Multi-source symbol discovery from FMP and Alpha Vantage with deduplication and validation."
            />
            <ChangeItem
              type="feature"
              title="Portfolio Calculator"
              description="Command-line portfolio performance calculator with dividend income projections and yield-on-cost tracking."
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
