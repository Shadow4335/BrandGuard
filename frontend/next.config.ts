import type { NextConfig } from "next";

// Basic browser protections on every page. There's deliberately no Content-Security-Policy: Next.js inline scripts
// need nonces, so a CSP should be added on purpose and tested, not as a blanket header.
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  // SAMEORIGIN, not DENY: our own pages frame Firebase's sign-in iframe, which is served from this domain (below)
  { key: "X-Frame-Options", value: "SAMEORIGIN" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" },
];

// Serve Firebase's sign-in pages (/__/auth/*: the popup handler and the iframe) from this domain. Safari, and other
// browsers that block third-party storage, restrict the iframe when it comes from <project>.firebaseapp.com, which
// breaks or delays Google sign-in. With NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN set to this site's domain, Firebase loads them
// from here instead (Firebase's recommended setup). Locally the auth domain stays <project>.firebaseapp.com.
const firebaseProject = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;

const nextConfig: NextConfig = {
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  async rewrites() {
    if (!firebaseProject) return [];
    const firebaseHost = `https://${firebaseProject}.firebaseapp.com`;
    return [{ source: "/__/auth/:path*", destination: `${firebaseHost}/__/auth/:path*` }];
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
