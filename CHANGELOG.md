# Changelog

All notable changes to the Divv API project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-11-13

### Added
- **Preset Date Ranges**: Convenient preset date ranges for price and dividend queries
  - Supported ranges: `1M`, `3M`, `6M`, `YTD`, `1Y`, `2Y`, `5Y`, `MAX`
  - No more manual date calculations required
  - Example: `GET /v1/prices/historical?symbol=AAPL&range=YTD`

- **Sort Control**: New `sort` parameter for historical data endpoints
  - Sort by date ascending (`asc`) or descending (`desc`)
  - Default behavior: most recent first
  - Example: `GET /v1/dividends/AAPL?sort=asc`

- **Adjusted Price Support**: Split and dividend-adjusted historical prices
  - New `adjusted=true` parameter
  - Essential for accurate backtesting and performance analysis
  - Accounts for stock splits and dividend payments
  - Example: `GET /v1/prices/historical?symbol=AAPL&adjusted=true`

### Improved
- Enhanced dividend metrics calculation with more accurate TTM (trailing twelve months) totals
- Better dividend growth rate calculations accounting for irregular payment schedules
- More descriptive error messages with actionable suggestions
- Improved API documentation with more code examples

### Fixed
- Date range edge cases at month and year boundaries
- Inconsistent results with certain date range combinations
- YTD calculation now correctly handles fiscal vs calendar year

---

## [1.0.2] - 2025-11-10

### Improved
- **Performance Optimization**: Reduced average response time from 120ms to <100ms
  - Database query optimization with better indexing
  - Intelligent caching layer for frequently requested data
  - CDN integration for static responses

- **Expanded Exchange Coverage**: Added 6,000+ new symbols
  - Canadian exchanges: TSX, TSXV, CSE
  - OTC markets: OTCM, OTCX
  - Total coverage now 24,000+ symbols

### Fixed
- Timezone handling for ex-dividend dates (now correctly in ET)
- ETF holdings data sync issues (now updates daily)
- Special handling for symbols with multiple share classes
- Memory leak in long-running API processes

---

## [1.0.1] - 2025-11-05

### Added
- **Dividend Screeners**: New screener endpoints with customizable filters
  - `GET /v1/screeners/high-yield?min_yield=5&limit=50`
  - `GET /v1/screeners/dividend-growth?min_growth=10`
  - Filter by sector, market cap, payout ratio, and more

- **Sector Performance Analytics**: New analytics endpoint
  - `GET /v1/analytics/sector-performance`
  - Analyze dividend yield and performance by sector
  - Ideal for sector rotation strategies

- **Rate Limiting Headers**: Track your usage in real-time
  - `X-RateLimit-Limit`: Your tier's request limit
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

### Fixed
- Special character handling in stock symbols (e.g., BRK.B, BF.A)
- Search query parsing for symbols with dots and dashes
- Case sensitivity issues in symbol lookup

---

## [1.0.0] - 2025-11-01

### Added
- 🎉 **Initial Public Release of Divv API**
- **23+ REST API Endpoints** covering:
  - Stock data and company information
  - Historical and real-time prices
  - Dividend history and calendar
  - ETF metrics and holdings
  - Analytics and screeners
  - Search functionality

- **API Key Authentication**: Secure access control
  - Free tier: 1,000 requests/month, 10 req/min
  - Pro tier: 100,000 requests/month, 100 req/min
  - Enterprise tier: Unlimited requests, 1,000 req/min

- **Token Bucket Rate Limiting**: Fair and predictable
  - Smooth request distribution
  - Burst allowance for occasional spikes
  - Clear rate limit headers

- **Covered Call ETF IV Data**: Industry-first feature
  - Implied Volatility (IV) for covered call ETFs
  - Helps predict future distribution levels
  - Updated daily with options market data

- **Multi-Exchange Support**: Comprehensive coverage
  - NYSE, NASDAQ, AMEX, CBOE
  - BATS, EDGX, BZX, IEX
  - 18,000+ symbols at launch

- **Production-Grade Infrastructure**:
  - Sub-100ms response times
  - 99.9% uptime SLA
  - Global CDN distribution
  - Automatic failover and redundancy

### Documentation
- Complete API reference with OpenAPI/Swagger spec
- Interactive API explorer
- Code examples in multiple languages
- Comprehensive guides and tutorials

---

## [0.9.0 Beta] - 2025-10-20

### Added
- Beta release to 100 selected testers
- Documentation portal with code examples
- Feedback collection system
- Basic monitoring and analytics

### Changed
- API endpoint structure based on beta feedback
- Improved error response format
- Enhanced data validation

### Fixed
- Various bugs reported during beta testing
- Performance issues with large date ranges
- Inconsistent response formats

---

## [0.8.0 Alpha] - 2025-10-01

### Added
- Internal alpha release
- Core API functionality
- Database schema and migrations
- Basic authentication

---

## Release Notes

### Upgrading

#### From 1.0.x to 1.1.0
No breaking changes. All new features are additive and backward compatible.

**New features to try**:
```bash
# Use preset date ranges
GET /v1/prices/historical?symbol=AAPL&range=YTD

# Get adjusted prices
GET /v1/prices/historical?symbol=AAPL&adjusted=true

# Control sort order
GET /v1/dividends/AAPL?sort=asc
```

#### From 0.9.0 Beta to 1.0.0
**Breaking changes**:
- Authentication now required for all endpoints (was optional in beta)
- `/stocks` endpoint pagination changed from `page`/`per_page` to `offset`/`limit`
- Error response format standardized to JSON API spec

**Migration guide**:
1. Obtain API key from dashboard
2. Add `X-API-Key` header to all requests
3. Update pagination parameters if using `/stocks` endpoint
4. Update error handling to expect JSON API error format

### Deprecations

**Deprecated in 1.1.0** (will be removed in 2.0.0):
- None

**Removed in 1.1.0**:
- None

### Security

#### 1.1.0
- No security updates

#### 1.0.2
- Updated dependencies to patch security vulnerabilities
- Enhanced API key hashing algorithm

#### 1.0.0
- Initial security implementation
- API key authentication
- Rate limiting
- HTTPS enforcement

---

## Planned Features

### Version 1.2.0 (Q1 2026)
- [ ] Historical dividend arrays in single request
- [ ] Webhook support for real-time updates
- [ ] Bulk symbol lookup (up to 100 symbols)
- [ ] Options chain data (Premium tier)

### Version 1.3.0 (Q2 2026)
- [ ] Technical indicators (RSI, MACD, etc.)
- [ ] Analyst ratings and price targets
- [ ] News sentiment analysis
- [ ] Portfolio tracking endpoints

### Version 2.0.0 (Q3 2026)
- [ ] GraphQL API (alongside REST)
- [ ] WebSocket streaming for real-time data
- [ ] Advanced analytics and backtesting
- [ ] Machine learning price predictions

---

## Support

- **Documentation**: https://docs.yourdomain.com
- **API Status**: https://status.yourdomain.com
- **GitHub Issues**: https://github.com/yourusername/dividend-api/issues
- **Email**: support@yourdomain.com

---

## Contributing

We welcome feedback and contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

**Legend**:
- 🎉 Major release
- ⚡ Performance improvement
- 🐛 Bug fix
- 📝 Documentation
- 🔒 Security
- ⚠️ Breaking change
- 🗑️ Deprecated

---

*Stay updated*: Subscribe to our [changelog RSS feed](/changelog/rss) or follow us on [Twitter](https://twitter.com/dividendapi)
