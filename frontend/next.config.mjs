/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Rewrite /api/* to the backend in production
  // This avoids CORS entirely — the browser talks to the same origin
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL;

    // Only apply rewrites if BACKEND_URL is set (production/preview on Vercel)
    // In local dev, the frontend calls the backend directly via NEXT_PUBLIC_API_URL
    if (!backendUrl) {
      return [];
    }

    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },

  // Security headers
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          {
            key: "Content-Security-Policy",
            value:
              "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' https://*.run.app",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
