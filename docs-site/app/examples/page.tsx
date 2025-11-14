import Link from 'next/link';
import Header from '@/components/Header';

export default function ExamplesPage() {
  return (
    <div className="min-h-screen bg-white">
      <Header />

      <div className="container mx-auto px-6 py-20">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-16">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              API Examples
            </h1>
            <p className="text-xl text-gray-600">
              Real-world examples to get you started quickly
            </p>
          </div>

          {/* New in v1.1.0 Banner */}
          <div className="mb-12 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
            <div className="flex items-center gap-3 mb-2">
              <span className="px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full">
                NEW
              </span>
              <h2 className="text-lg font-bold text-gray-900">
                Enhanced in v1.1.0
              </h2>
            </div>
            <p className="text-gray-700">
              Check out the new preset ranges, sort control, and flexible date filtering below!
            </p>
          </div>

          {/* Prices Examples */}
          <ExampleSection
            title="Price History"
            description="Get historical OHLCV data with flexible filtering"
          >
            <Example
              title="Get Last Year of Data"
              badge="Popular"
              request="GET /v1/prices/AAPL?range=1y"
              description="Uses preset range for convenience"
              code={`curl "http://localhost:8000/v1/prices/AAPL?range=1y&limit=5"`}
            />

            <Example
              title="Year-to-Date Performance"
              badge="New"
              request="GET /v1/prices/AAPL?range=ytd"
              description="Automatically calculates from Jan 1 to today"
              code={`curl "http://localhost:8000/v1/prices/AAPL?range=ytd"`}
            />

            <Example
              title="From Date to Now"
              badge="New"
              request="GET /v1/prices/AAPL?start_date=2024-01-01"
              description="Start date only - automatically goes to current date"
              code={`curl "http://localhost:8000/v1/prices/AAPL?start_date=2024-01-01&limit=5"`}
            />

            <Example
              title="Specific Date Range"
              request="GET /v1/prices/AAPL?start_date=2024-01-01&end_date=2024-12-31"
              description="Full year 2024 data"
              code={`curl "http://localhost:8000/v1/prices/AAPL?start_date=2024-01-01&end_date=2024-12-31"`}
            />

            <Example
              title="Oldest First for Charting"
              badge="New"
              request="GET /v1/prices/AAPL?range=1m&sort=asc"
              description="Sort ascending for time-series visualization"
              code={`curl "http://localhost:8000/v1/prices/AAPL?range=1m&sort=asc&limit=5"`}
            />

            <Example
              title="Raw Prices (Not Adjusted)"
              badge="New"
              request="GET /v1/prices/AAPL?range=1y&adjusted=false"
              description="Get prices without split/dividend adjustments"
              code={`curl "http://localhost:8000/v1/prices/AAPL?range=1y&adjusted=false&limit=5"`}
            />

            <Example
              title="All Historical Data"
              badge="New"
              request="GET /v1/prices/AAPL?range=max&limit=5000"
              description="Get all available data (up to 5000 results)"
              code={`curl "http://localhost:8000/v1/prices/AAPL?range=max&limit=5000"`}
            />
          </ExampleSection>

          {/* Dividends Calendar Examples */}
          <ExampleSection
            title="Dividend Calendar"
            description="Get upcoming dividend events with flexible filtering"
          >
            <Example
              title="Next Month's Dividends"
              badge="Popular"
              request="GET /v1/dividends/calendar?range=1m"
              description="Uses preset range for convenience"
              code={`curl "http://localhost:8000/v1/dividends/calendar?range=1m&limit=5"`}
            />

            <Example
              title="High-Yield Upcoming Dividends"
              badge="New"
              request="GET /v1/dividends/calendar?range=3m&min_yield=5.0"
              description="Find dividends with 5%+ yield in next 3 months"
              code={`curl "http://localhost:8000/v1/dividends/calendar?range=3m&min_yield=5.0"`}
            />

            <Example
              title="Specific Stocks Only"
              request="GET /v1/dividends/calendar?range=1m&symbols=AAPL,MSFT,T"
              description="Filter calendar for specific symbols"
              code={`curl "http://localhost:8000/v1/dividends/calendar?range=1m&symbols=AAPL,MSFT,T"`}
            />

            <Example
              title="From Date Forward"
              badge="New"
              request="GET /v1/dividends/calendar?start_date=2024-12-01"
              description="Start date only - automatically adds 90 days"
              code={`curl "http://localhost:8000/v1/dividends/calendar?start_date=2024-12-01"`}
            />

            <Example
              title="Specific Quarter"
              request="GET /v1/dividends/calendar?start_date=2024-01-01&end_date=2024-03-31"
              description="Q1 2024 dividend events"
              code={`curl "http://localhost:8000/v1/dividends/calendar?start_date=2024-01-01&end_date=2024-03-31"`}
            />
          </ExampleSection>

          {/* Stock Details Examples */}
          <ExampleSection
            title="Stock Information"
            description="Get detailed stock data and dividend summaries"
          >
            <Example
              title="Search for Stocks"
              request="GET /v1/search?q=apple&limit=3"
              description="Find stocks by name or symbol"
              code={`curl "http://localhost:8000/v1/search?q=apple&limit=3"`}
            />

            <Example
              title="Get Stock Details"
              request="GET /v1/stocks/AAPL"
              description="Complete information for a specific stock"
              code={`curl "http://localhost:8000/v1/stocks/AAPL"`}
            />

            <Example
              title="Latest Price Snapshot"
              request="GET /v1/prices/AAPL/latest"
              description="Current price with change information"
              code={`curl "http://localhost:8000/v1/prices/AAPL/latest"`}
            />

            <Example
              title="Complete Dividend Summary"
              request="GET /v1/stocks/AAPL/dividends"
              description="Full dividend history and metrics"
              code={`curl "http://localhost:8000/v1/stocks/AAPL/dividends"`}
            />
          </ExampleSection>

          {/* Screeners Examples */}
          <ExampleSection
            title="Stock Screeners"
            description="Find stocks matching specific criteria"
          >
            <Example
              title="High-Yield Dividend Stocks"
              badge="Popular"
              request="GET /v1/screeners/high-yield?min_yield=5.0&limit=10"
              description="Find stocks with 5%+ dividend yield"
              code={`curl "http://localhost:8000/v1/screeners/high-yield?min_yield=5.0&limit=10"`}
            />

            <Example
              title="Monthly Dividend Payers"
              badge="Popular"
              request="GET /v1/screeners/monthly-payers?limit=20"
              description="Stocks that pay dividends monthly"
              code={`curl "http://localhost:8000/v1/screeners/monthly-payers?limit=20"`}
            />
          </ExampleSection>

          {/* Code Examples */}
          <div className="mt-16 space-y-12">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-6">
                Code Examples
              </h2>
              <p className="text-gray-600 mb-8">
                Use the API in your favorite programming language
              </p>
            </div>

            <CodeExample
              language="JavaScript"
              title="Fetch Last Year of Prices"
              code={`// Using fetch API
const response = await fetch(
  'http://localhost:8000/v1/prices/AAPL?range=1y&sort=asc'
);
const data = await response.json();

console.log(\`Got \${data.data.length} price bars\`);
data.data.forEach(bar => {
  console.log(\`\${bar.date}: $\${bar.close}\`);
});`}
            />

            <CodeExample
              language="Python"
              title="Get High-Yield Dividends"
              code={`import requests

# Get high-yield dividends for next 3 months
response = requests.get(
    'http://localhost:8000/v1/dividends/calendar',
    params={
        'range': '3m',
        'min_yield': 5.0,
        'limit': 50
    }
)

data = response.json()
for event in data['events']:
    print(f"{event['symbol']}: {event['ex_date']} - Yield: {event.get('yield', 'N/A')}%")`}
            />

            <CodeExample
              language="curl"
              title="Complete Workflow Example"
              code={`# 1. Search for a stock
curl "http://localhost:8000/v1/search?q=tesla&limit=3"

# 2. Get stock details
curl "http://localhost:8000/v1/stocks/TSLA"

# 3. Get year-to-date price performance
curl "http://localhost:8000/v1/prices/TSLA?range=ytd&sort=asc"

# 4. Get dividend information
curl "http://localhost:8000/v1/stocks/TSLA/dividends"`}
            />
          </div>

          {/* Tips Section */}
          <div className="mt-16 p-8 bg-gray-50 rounded-xl border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Tips & Best Practices
            </h2>
            <div className="grid md:grid-cols-2 gap-6">
              <Tip
                title="Use Preset Ranges"
                description="Preset ranges like ?range=1y are shorter and less error-prone than calculating dates manually."
              />
              <Tip
                title="Sort for Charts"
                description="Use ?sort=asc when building time-series charts to get data in chronological order."
              />
              <Tip
                title="Start Date Only"
                description="Omit end_date to automatically get data from start_date to today."
              />
              <Tip
                title="Increase Limits"
                description="Use ?limit=5000 for bulk historical data downloads (max 5000 results per request)."
              />
              <Tip
                title="Adjusted Prices"
                description="Use ?adjusted=true (default) for analysis that accounts for splits and dividends."
              />
              <Tip
                title="Error Handling"
                description="Always check response status codes. 4xx errors include detailed error messages."
              />
            </div>
          </div>

          {/* Documentation Links */}
          <div className="mt-16 grid md:grid-cols-3 gap-6">
            <DocLink
              href="/api"
              title="Full Documentation"
              description="Complete API documentation with all endpoints and parameters"
            />
            <DocLink
              href="/api-reference"
              title="API Reference"
              description="Quick reference guide for all endpoints"
            />
            <DocLink
              href="/api-keys"
              title="Get API Keys"
              description="Create and manage your API keys"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function ExampleSection({ title, description, children }: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-16">
      <h2 className="text-3xl font-bold text-gray-900 mb-3">{title}</h2>
      <p className="text-gray-600 mb-8">{description}</p>
      <div className="space-y-6">
        {children}
      </div>
    </div>
  );
}

function Example({ title, request, description, code, badge }: {
  title: string;
  request: string;
  description: string;
  code: string;
  badge?: string;
}) {
  return (
    <div className="p-6 bg-white border border-gray-200 rounded-xl hover:border-gray-300 transition-all">
      <div className="flex items-center gap-3 mb-3">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {badge && (
          <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-semibold rounded">
            {badge}
          </span>
        )}
      </div>
      <code className="block text-sm font-mono text-blue-600 bg-blue-50 px-3 py-2 rounded mb-3">
        {request}
      </code>
      <p className="text-sm text-gray-600 mb-4">{description}</p>
      <div className="bg-gray-900 rounded-lg p-4">
        <code className="text-sm text-green-400 font-mono whitespace-pre-wrap break-all">
          {code}
        </code>
      </div>
    </div>
  );
}

function CodeExample({ language, title, code }: {
  language: string;
  title: string;
  code: string;
}) {
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <div className="bg-gray-50 px-6 py-3 border-b border-gray-200 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        <span className="px-3 py-1 bg-gray-200 text-gray-700 text-xs font-mono rounded">
          {language}
        </span>
      </div>
      <div className="bg-gray-900 p-6">
        <pre className="text-sm text-green-400 font-mono overflow-x-auto">
          {code}
        </pre>
      </div>
    </div>
  );
}

function Tip({ title, description }: {
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
      </svg>
      <div>
        <h4 className="font-semibold text-gray-900 mb-1">{title}</h4>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
    </div>
  );
}

function DocLink({ href, title, description }: {
  href: string;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="p-6 bg-white border border-gray-200 rounded-xl hover:border-gray-300 transition-all group"
    >
      <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
        {title} →
      </h3>
      <p className="text-sm text-gray-600">{description}</p>
    </Link>
  );
}
