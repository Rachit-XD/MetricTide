import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emit a standalone server bundle for a minimal production Docker image.
  output: "standalone",
  reactStrictMode: true,
  // The web container lives in a monorepo; trace the repo root for output tracing.
  outputFileTracingRoot: process.env.NODE_ENV === "production" ? "../../" : undefined,
};

export default nextConfig;
