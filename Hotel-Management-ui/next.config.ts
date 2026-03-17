import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',   // ✅ ADD THIS LINE

  experimental: {
    serverActions: {},
  },

  env: {
    API_BASE_URL: process.env.API_BASE_URL,
  },
};

export default nextConfig;
