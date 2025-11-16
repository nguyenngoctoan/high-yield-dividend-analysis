import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function GET(request: NextRequest) {
  try {
    // Get query parameters
    const { searchParams } = new URL(request.url);
    const hours = parseInt(searchParams.get('hours') || '24');

    // Get all API keys
    const { data: keys, error: keysError } = await supabase
      .from('divv_api_keys')
      .select('*')
      .order('created_at', { ascending: false });

    if (keysError) {
      console.error('Error fetching keys:', keysError);
      return NextResponse.json(
        { error: 'Failed to fetch analytics', detail: keysError.message },
        { status: 500 }
      );
    }

    // Generate mock data based on total request counts
    // In production, this would come from actual logs
    const hourlyData: any[] = [];
    const totalRequests = keys?.reduce((sum, key) => sum + (key.request_count || 0), 0) || 0;

    // For 7 days, show daily aggregates. Otherwise show hourly.
    const isWeeklyView = hours >= 168; // 7 days = 168 hours

    if (isWeeklyView) {
      // Create daily buckets for 7-day view
      const days = 7;
      const avgPerDay = totalRequests / days;

      for (let i = 0; i < days; i++) {
        const dayTime = new Date();
        dayTime.setDate(dayTime.getDate() - (days - i - 1));
        dayTime.setHours(12, 0, 0, 0); // Set to noon for consistency

        // Simulate realistic daily distribution
        const variance = Math.random() * 0.6 + 0.7; // 0.7 to 1.3x average
        const dayCount = Math.max(0, Math.round(avgPerDay * variance));

        hourlyData.push({
          hour: dayTime.toISOString().slice(0, 10), // YYYY-MM-DD
          count: dayCount,
          timestamp: dayTime.toISOString(),
        });
      }
    } else {
      // Create hourly buckets for 24h and 48h views
      const avgPerHour = totalRequests / hours;

      for (let i = 0; i < hours; i++) {
        const hourTime = new Date();
        hourTime.setHours(hourTime.getHours() - (hours - i - 1));
        hourTime.setMinutes(0, 0, 0);

        // Simulate realistic hourly distribution
        const variance = Math.random() * 0.6 + 0.7; // 0.7 to 1.3x average
        const hourCount = Math.max(0, Math.round(avgPerHour * variance));

        hourlyData.push({
          hour: hourTime.toISOString().slice(0, 13),
          count: hourCount,
          timestamp: hourTime.toISOString(),
        });
      }
    }

    // Mock endpoint data (top endpoints)
    const endpointData = [
      { endpoint: '/v1/stocks/{symbol}/quote', count: Math.floor(totalRequests * 0.35) },
      { endpoint: '/v1/stocks/{symbol}/dividends', count: Math.floor(totalRequests * 0.25) },
      { endpoint: '/v1/stocks/{symbol}/fundamentals', count: Math.floor(totalRequests * 0.15) },
      { endpoint: '/v1/stocks/search', count: Math.floor(totalRequests * 0.12) },
      { endpoint: '/v1/etfs/{symbol}', count: Math.floor(totalRequests * 0.08) },
      { endpoint: '/v1/screener', count: Math.floor(totalRequests * 0.05) },
    ].filter(e => e.count > 0);

    // Calculate stats
    const peakHour = hourlyData.reduce((max, curr) =>
      curr.count > max.count ? curr : max, hourlyData[0] || { hour: '', count: 0, timestamp: '' });

    const avgPerPeriod = isWeeklyView
      ? Math.round((totalRequests / 7) * 10) / 10  // Average per day for weekly view
      : Math.round((totalRequests / hours) * 10) / 10; // Average per hour for other views

    return NextResponse.json({
      hourly: hourlyData,
      endpoints: endpointData,
      stats: {
        totalRequests,
        avgPerHour: avgPerPeriod,
        peakHour: peakHour.hour,
        peakCount: peakHour.count,
        timeRange: {
          start: hourlyData[0]?.timestamp || new Date().toISOString(),
          end: hourlyData[hourlyData.length - 1]?.timestamp || new Date().toISOString(),
          hours,
        },
      },
    });
  } catch (error) {
    console.error('Error fetching analytics:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
