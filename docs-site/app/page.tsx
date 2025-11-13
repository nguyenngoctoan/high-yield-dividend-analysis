import Link from 'next/link';
import Header from '@/components/Header';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      <Header />
      {/* Hero Section */}
      <div className="container mx-auto px-6 pt-32 pb-20">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-block mb-6 px-4 py-1.5 bg-blue-50 text-blue-600 rounded-full text-sm font-medium">
            Production Ready
          </div>
          <h1 className="text-7xl font-bold text-gray-900 mb-6 tracking-tight">
            Dividend API
          </h1>
          <p className="text-xl text-gray-600 mb-10 leading-relaxed max-w-2xl mx-auto">
            A modern, fast API for dividend investors. Get stock data, dividend calendars,
            and analytics in milliseconds.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/api"
              className="px-8 py-3.5 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-all shadow-sm hover:shadow-md"
            >
              Documentation
            </Link>
            <a
              href="http://localhost:8000/health"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-3.5 bg-white border-2 border-gray-200 text-gray-700 rounded-lg font-medium hover:border-gray-300 transition-all"
            >
              API Status
            </a>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-24 max-w-4xl mx-auto">
          <StatCard number="24,842" label="Stocks" />
          <StatCard number="11" label="Endpoints" />
          <StatCard number="<100ms" label="Response" />
          <StatCard number="100%" label="Uptime" />
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-6 mt-24 max-w-5xl mx-auto">
          <FeatureCard
            title="Fast & Reliable"
            description="Sub-100ms response times with 100% uptime"
          />
          <FeatureCard
            title="Complete Data"
            description="24,000+ stocks with dividend history"
          />
          <FeatureCard
            title="Easy to Use"
            description="RESTful API with clear documentation"
          />
        </div>

        {/* Code Example */}
        <div className="mt-24 max-w-3xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Quick Start</h2>
            <p className="text-gray-600">Get started in seconds with a simple HTTP request</p>
          </div>
          <div className="bg-gray-50 rounded-2xl p-8 border border-gray-200">
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
  );
}

function FeatureCard({ title, description }: {
  title: string;
  description: string;
}) {
  return (
    <div className="p-6 rounded-xl bg-white border border-gray-200 hover:border-gray-300 transition-all">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-sm leading-relaxed">{description}</p>
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
