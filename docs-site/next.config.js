/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Docker optimization: standalone output for smaller image
  output: 'standalone',

  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'lh3.googleusercontent.com',
        pathname: '/**',
      },
    ],
  },

  // Webpack optimization
  webpack: (config, { dev, isServer }) => {
    if (dev) {
      // Prevent memory buildup with controlled caching
      config.cache = {
        type: 'memory',
        maxGenerations: 1, // Keep only latest generation
      };
      config.optimization = {
        ...config.optimization,
        moduleIds: 'named',
        chunkIds: 'named',
      };
    }
    return config;
  },

  // Multi-core support with memory control
  experimental: {
    workerThreads: true, // Enable parallel compilation
    cpus: 8, // Use 8 cores (good balance of speed vs memory)
  },
}

module.exports = nextConfig
