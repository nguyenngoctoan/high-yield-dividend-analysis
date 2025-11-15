/**
 * Application Configuration
 * Centralized configuration for URLs, API endpoints, and environment-specific settings
 */

// API Configuration
export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  version: 'v1',
} as const;

// Get full API URL
export const getApiUrl = (path: string = '') => {
  const base = API_CONFIG.baseUrl;
  const version = API_CONFIG.version;
  return path ? `${base}/${version}${path}` : `${base}/${version}`;
};

// Frontend Configuration
export const FRONTEND_CONFIG = {
  url: process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:3000',
} as const;

// Stock Count (single source of truth)
export const STOCK_COUNT = '19,600+' as const;

// Feature Flags
export const FEATURES = {
  authentication: true,
  oauth: true,
  apiKeys: true,
} as const;

// Supabase Configuration (for client-side auth)
export const SUPABASE_CONFIG = {
  url: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
} as const;

// Validate required environment variables
if (typeof window === 'undefined') {
  // Server-side validation
  const required = {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  };

  const missing = Object.entries(required)
    .filter(([_, value]) => !value)
    .map(([key]) => key);

  if (missing.length > 0) {
    console.warn(
      `⚠️  Missing environment variables: ${missing.join(', ')}\n` +
      `   Some features may not work correctly.`
    );
  }
}
