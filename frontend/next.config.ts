import type { NextConfig } from "next";

// A separate API is optional. Without it, Next.js serves its own /api/v1 routes.
const BACKEND_URL = process.env.BACKEND_URL;

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return BACKEND_URL
      ? [{ source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` }]
      : [];
  },
};

export default nextConfig;
