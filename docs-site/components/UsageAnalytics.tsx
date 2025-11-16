'use client';

import { useState, useEffect } from 'react';
import LineChart from './LineChart';

interface HourlyData {
  hour: string;
  count: number;
  timestamp: string;
}

interface EndpointData {
  endpoint: string;
  count: number;
}

interface Analytics {
  hourly: HourlyData[];
  endpoints: EndpointData[];
  stats: {
    totalRequests: number;
    avgPerHour: number;
    peakHour: string;
    peakCount: number;
  };
}

export default function UsageAnalytics() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [timeRange, setTimeRange] = useState(24);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/keys/analytics?hours=${timeRange}`);
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="mb-8 p-6 bg-gray-50 rounded-xl border border-gray-200">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!analytics) return null;

  // Format labels based on time range
  const formatLabel = (timestamp: string) => {
    const date = new Date(timestamp);

    if (timeRange <= 24) {
      // For 24 hours: show time only (e.g., "2 PM")
      return date.toLocaleTimeString('en-US', { hour: 'numeric', hour12: true });
    } else if (timeRange <= 48) {
      // For 48 hours: show day and time (e.g., "Thu 2 PM")
      return date.toLocaleDateString('en-US', { weekday: 'short', hour: 'numeric', hour12: true });
    } else {
      // For 7 days: show date (e.g., "Nov 14")
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const chartData = analytics.hourly.map(d => ({
    label: formatLabel(d.timestamp),
    value: d.count,
  }));

  return (
    <div className="mb-8 space-y-6">
      {/* Header with Time Range Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Usage Analytics</h2>
        <div className="flex gap-2">
          {[{ value: 24, label: '24h' }, { value: 48, label: '48h' }, { value: 168, label: '7d' }].map((option) => (
            <button
              key={option.value}
              onClick={() => setTimeRange(option.value)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                timeRange === option.value
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Hourly Requests Chart */}
      <div className="p-6 bg-white border border-gray-200 rounded-xl">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Requests Over Time</h3>
        <LineChart data={chartData} height={360} />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-6">
        <div className="p-6 bg-white border border-gray-200 rounded-xl">
          <p className="text-sm text-gray-500 mb-1">Peak Hour</p>
          <p className="text-2xl font-bold text-gray-900">
            {new Date(analytics.stats.peakHour + ':00:00').toLocaleTimeString('en-US', { hour: 'numeric', hour12: true })}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            {analytics.stats.peakCount} requests
          </p>
        </div>
        <div className="p-6 bg-white border border-gray-200 rounded-xl">
          <p className="text-sm text-gray-500 mb-1">Total ({timeRange}h)</p>
          <p className="text-2xl font-bold text-gray-900">
            {analytics.stats.totalRequests.toLocaleString()}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            requests
          </p>
        </div>
        <div className="p-6 bg-white border border-gray-200 rounded-xl">
          <p className="text-sm text-gray-500 mb-1">
            {timeRange >= 168 ? 'Average/Day' : 'Average/Hour'}
          </p>
          <p className="text-2xl font-bold text-gray-900">
            {analytics.stats.avgPerHour}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            requests
          </p>
        </div>
      </div>

      {/* Top Endpoints */}
      {analytics.endpoints.length > 0 && (
        <div className="p-6 bg-white border border-gray-200 rounded-xl">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Endpoints</h3>
          <div className="space-y-3">
            {analytics.endpoints.slice(0, 10).map((endpoint, index) => {
              const maxCount = analytics.endpoints[0]?.count || 1;
              const percentage = (endpoint.count / maxCount) * 100;

              return (
                <div key={index}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">
                      {endpoint.endpoint}
                    </span>
                    <span className="text-sm text-gray-500">
                      {endpoint.count.toLocaleString()}
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-gray-900 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
