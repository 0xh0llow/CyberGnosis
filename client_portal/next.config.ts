import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',

  async rewrites() {
    // In produzione (dentro Docker) usa il service name interno.
    // In sviluppo locale usa localhost:38000 (porta pubblica del compose).
    const apiBase =
      process.env.CENTRAL_SERVER_URL ?? 'http://localhost:38000'

    return [
      {
        source: '/api/:path*',
        destination: `${apiBase}/api/:path*`,
      },
      {
        source: '/health',
        destination: `${apiBase}/health`,
      },
    ]
  },
}

export default nextConfig
