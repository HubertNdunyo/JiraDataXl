/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone',  // For production Docker builds
  async rewrites() {
    // In Docker, use container name; otherwise use localhost
    const apiUrl = process.env.BACKEND_URL || 'http://localhost:8987'
    console.log('API rewrites configured to:', apiUrl)
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ]
  }
}

module.exports = nextConfig