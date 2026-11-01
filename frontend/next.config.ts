import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV !== "production";
const origin = (url?: string) => { try { return url ? new URL(url).origin : ""; } catch { return ""; } };
const apiOrigin = origin(process.env.NEXT_PUBLIC_API_URL) || "http://localhost:8000";

// Content-Security-Policy. 'unsafe-inline' scripts are still needed for Next.js's inline bootstrap (nonces would make
// every page dynamic); apis.google.com and the Firebase/Google hosts are for Google sign-in. connect-src lists the API,
// Supabase and Google's auth endpoints explicitly. Dev mode also needs eval and the hot-reload websocket.
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline' https://apis.google.com${isDev ? " 'unsafe-eval'" : ""}`,
  `connect-src 'self' ${apiOrigin} https://*.supabase.co https://*.googleapis.com${isDev ? " ws: wss:" : ""}`,
  "img-src 'self' data: blob: https:",
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self' data:",
  "frame-src 'self' https://*.firebaseapp.com https://accounts.google.com",
  "frame-ancestors 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

// Browser protections on every page.
const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
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
    // Every path except the proxied Firebase sign-in pages, which keep Firebase's own headers (our CSP would block them)
    return [{ source: "/:path((?!__/auth/).*)", headers: securityHeaders }];
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
