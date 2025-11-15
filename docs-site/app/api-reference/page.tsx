'use client';

import { API_CONFIG } from '@/lib/config';

import Link from 'next/link';
import Header from '@/components/Header';

export default function APIReferencePage() {
  return (
    <div className="min-h-screen bg-white">
      <Header />

      <div className="container mx-auto px-6 py-20">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-16">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              API Reference
            </h1>
            <p className="text-xl text-gray-600">
              Complete reference for all API endpoints
            </p>
          </div>

          {/* Base URL Section */}
          <div className="mb-12 p-6 bg-gray-50 rounded-xl border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Base URL</h2>
            <code className="text-gray-700 font-mono">
              ${API_CONFIG.baseUrl}/v1
            </code>
          </div>

          {/* Endpoints List */}
          <div className="space-y-8">
            <EndpointSection
              title="Stocks"
              endpoints={[
                {
                  method: 'GET',
                  path: '/stocks',
                  description: 'List and filter stocks with dividends'
                },
                {
                  method: 'GET',
                  path: '/stocks/{symbol}',
                  description: 'Get detailed stock information'
                }
              ]}
            />

            <EndpointSection
              title="Dividends"
              endpoints={[
                {
                  method: 'GET',
                  path: '/dividends/calendar',
                  description: 'Get upcoming dividend events with flexible filtering',
                  badge: 'Enhanced'
                },
                {
                  method: 'GET',
                  path: '/dividends/history',
                  description: 'Get historical dividend payments'
                },
                {
                  method: 'GET',
                  path: '/stocks/{symbol}/dividends',
                  description: 'Get complete dividend summary for a stock'
                }
              ]}
            />

            <EndpointSection
              title="Screeners"
              endpoints={[
                {
                  method: 'GET',
                  path: '/screeners/high-yield',
                  description: 'Find high-yield dividend stocks'
                },
                {
                  method: 'GET',
                  path: '/screeners/monthly-payers',
                  description: 'Find monthly dividend payers'
                }
              ]}
            />

            <EndpointSection
              title="Prices"
              endpoints={[
                {
                  method: 'GET',
                  path: '/prices/{symbol}',
                  description: 'Get historical price data with flexible filtering',
                  badge: 'Enhanced'
                },
                {
                  method: 'GET',
                  path: '/prices/{symbol}/latest',
                  description: 'Get latest price snapshot'
                }
              ]}
            />

            <EndpointSection
              title="Search"
              endpoints={[
                {
                  method: 'GET',
                  path: '/search',
                  description: 'Search stocks by symbol, company name, or sector'
                }
              ]}
            />
          </div>

          {/* Documentation Link */}
          <div className="mt-16 p-8 bg-gray-50 rounded-xl border border-gray-200 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-3">
              Need More Details?
            </h2>
            <p className="text-gray-600 mb-6">
              Check out the full documentation for examples, parameters, and response schemas
            </p>
            <Link
              href="/api"
              className="inline-block px-8 py-3 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-all"
            >
              View Documentation
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function EndpointSection({ title, endpoints }: {
  title: string;
  endpoints: Array<{ method: string; path: string; description: string; badge?: string }>;
}) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">{title}</h2>
      <div className="space-y-3">
        {endpoints.map((endpoint, index) => (
          <div
            key={index}
            className="p-4 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-all"
          >
            <div className="flex items-start gap-4">
              <span className={`px-2 py-1 rounded text-xs font-semibold ${
                endpoint.method === 'GET'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-green-100 text-green-700'
              }`}>
                {endpoint.method}
              </span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <code className="text-sm font-mono text-gray-900">
                    {endpoint.path}
                  </code>
                  {endpoint.badge && (
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-semibold rounded">
                      {endpoint.badge}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {endpoint.description}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
