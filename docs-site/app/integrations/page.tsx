import Header from '@/components/Header';
import Link from 'next/link';

export default function IntegrationsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <div className="container mx-auto px-6 py-20">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              Integrations
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Connect Divv API to your favorite tools. Use dividend data in spreadsheets, dashboards, and applications with our ready-to-use integrations.
            </p>
          </div>

          {/* Featured Integrations */}
          <div className="grid md:grid-cols-2 gap-8 mb-16">
            {/* Google Sheets */}
            <IntegrationCard
              title="Google Sheets"
              description="Use =DIVV() function just like GOOGLEFINANCE() - same syntax, better dividend data"
              icon="📊"
              features={[
                '4 custom functions included',
                'GOOGLEFINANCE() compatible',
                'Automatic caching (5 min)',
                'Bulk fetch support',
                'Dividend Aristocrat detection'
              ]}
              status="Production Ready"
              statusColor="green"
              docsLink="/integrations/google-sheets"
              downloadLink="/DIVV.gs"
            />

            {/* Microsoft Excel */}
            <IntegrationCard
              title="Microsoft Excel"
              description="VBA module for Excel with same DIVV() function syntax as Google Sheets"
              icon="📈"
              features={[
                'VBA custom functions',
                'Worksheet-based caching',
                'Compatible with Excel 2010+',
                'No external dependencies',
                'Simple JSON parser included'
              ]}
              status="Production Ready"
              statusColor="green"
              docsLink="/integrations/excel"
              downloadLink="/DIVV.bas"
            />
          </div>

          {/* Coming Soon */}
          <div className="mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
              Coming Soon
            </h2>
            <div className="grid md:grid-cols-3 gap-6">
              <ComingSoonCard
                title="Power BI"
                description="Native connector for Power BI Desktop and Service"
                icon="📊"
              />
              <ComingSoonCard
                title="Tableau"
                description="Web data connector for Tableau Desktop and Online"
                icon="📉"
              />
              <ComingSoonCard
                title="Python SDK"
                description="Official Python library with pandas integration"
                icon="🐍"
              />
            </div>
          </div>

          {/* API Direct Access */}
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl p-12 border-2 border-blue-200">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Don't see your tool?
              </h2>
              <p className="text-xl text-gray-600">
                Use our REST API directly - it's simple, fast, and well-documented
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-8 mb-8">
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="text-lg font-bold text-gray-900 mb-3">Simple HTTP Requests</h3>
                <pre className="bg-gray-900 p-4 rounded-lg text-emerald-400 font-mono text-sm overflow-x-auto">
{`curl "http://api.divv.com/v1/stocks/AAPL/quote"

# Returns complete stock data
# No authentication required for free tier`}
                </pre>
              </div>

              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="text-lg font-bold text-gray-900 mb-3">Language Agnostic</h3>
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Python, JavaScript, Ruby, Go, PHP</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Any tool that supports HTTP</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>RESTful, JSON responses</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="text-center">
              <Link
                href="/api"
                className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-bold hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg"
              >
                <span>View API Documentation</span>
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

function IntegrationCard({
  title,
  description,
  icon,
  features,
  status,
  statusColor,
  docsLink,
  downloadLink
}: {
  title: string;
  description: string;
  icon: string;
  features: string[];
  status: string;
  statusColor: string;
  docsLink: string;
  downloadLink: string;
}) {
  const statusColors = {
    green: 'bg-green-100 text-green-700 border-green-300',
    yellow: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    blue: 'bg-blue-100 text-blue-700 border-blue-300'
  };

  return (
    <div className="bg-white rounded-2xl p-8 border-2 border-gray-200 hover:border-blue-500 hover:shadow-xl transition-all">
      <div className="flex items-start justify-between mb-4">
        <div className="text-5xl">{icon}</div>
        <div className={`px-3 py-1 rounded-full text-xs font-semibold border ${statusColors[statusColor as keyof typeof statusColors]}`}>
          {status}
        </div>
      </div>

      <h3 className="text-2xl font-bold text-gray-900 mb-3">{title}</h3>
      <p className="text-gray-600 mb-6">{description}</p>

      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Features:</h4>
        <ul className="space-y-2">
          {features.map((feature, index) => (
            <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
              <svg className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>{feature}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex gap-3">
        <Link
          href={docsLink}
          className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all text-center"
        >
          View Docs
        </Link>
        <a
          href={downloadLink}
          download
          className="flex-1 px-4 py-3 bg-white border-2 border-blue-600 text-blue-700 rounded-lg font-medium hover:bg-blue-50 transition-all text-center"
        >
          Download
        </a>
      </div>
    </div>
  );
}

function ComingSoonCard({
  title,
  description,
  icon
}: {
  title: string;
  description: string;
  icon: string;
}) {
  return (
    <div className="bg-white rounded-xl p-6 border-2 border-gray-200 opacity-75">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600 mb-4">{description}</p>
      <div className="inline-block px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-semibold">
        Coming Soon
      </div>
    </div>
  );
}
