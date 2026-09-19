// In production (Vercel), NEXT_PUBLIC_API_URL is not set — requests go to /api
// via Next.js rewrites, which proxies to the Cloud Run backend (same origin, no CORS).
//
// In local dev, NEXT_PUBLIC_API_URL points to http://localhost:8000/api directly.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "/api";

export const POLLING_INTERVAL_MS = 2000;
