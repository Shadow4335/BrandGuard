import { createBrowserClient } from "@supabase/ssr";

// Supabase is reached through this site's own domain (/supabase/*, proxied in next.config.ts). Some networks block
// supabase.co outright (several Indian ISPs, for example), which would make sign-in fail with "Failed to fetch".
export const SUPABASE_PROXY_PATH = "/supabase";

export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

  if (!supabaseUrl || !supabaseAnonKey) {
    // Return dummy client if env not set yet to avoid build/runtime crash
    return createBrowserClient(
      supabaseUrl || "https://placeholder-brandguard.supabase.co",
      supabaseAnonKey || "placeholder-anon-key"
    );
  }

  const inBrowser = typeof window !== "undefined";
  const url = inBrowser ? `${window.location.origin}${SUPABASE_PROXY_PATH}` : supabaseUrl;
  // The session is stored under a key derived from the URL's first label. Keep the name the real project URL gives
  // (sb-<project ref>-auth-token), so switching to the proxy doesn't sign anyone out.
  const projectRef = new URL(supabaseUrl).hostname.split(".")[0];
  return createBrowserClient(url, supabaseAnonKey, { cookieOptions: { name: `sb-${projectRef}-auth-token` } });
}
