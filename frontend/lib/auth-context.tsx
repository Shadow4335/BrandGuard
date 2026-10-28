"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { User } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase";
import { Profile, UserRole } from "@/lib/types";
import { api, getDemoSession, setDemoSession, DemoSession } from "@/lib/api";

const DEMO_ROLES: Record<string, UserRole> = {
  "admin@demo.test": "admin",
  "creator@demo.test": "creator",
  "manager@demo.test": "manager",
  "reviewer@demo.test": "reviewer",
};

function demoToState(d: DemoSession): { user: User; profile: Profile } {
  return {
    user: { id: d.user_id, email: d.email } as User,
    profile: { id: d.user_id, org_id: d.org_id, role: d.role as UserRole, email: d.email, full_name: d.full_name },
  };
}

interface AuthContextType {
  user: User | null;
  profile: Profile | null;
  loading: boolean;
  error: string | null;
  signIn: (email: string, password?: string) => Promise<boolean>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  profile: null,
  loading: true,
  error: null,
  signIn: async () => false,
  signOut: async () => {},
  refreshProfile: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [supabase] = useState(() => createClient());
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = async (userId: string) => {
    try {
      const { data, error: profError } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", userId)
        .single();

      if (profError) {
        // Fallback: check user metadata for role if profile query fails or table empty
        const authUser = (await supabase.auth.getUser()).data.user;
        const role = (authUser?.user_metadata?.role as UserRole) || "creator";
        setProfile({
          id: userId,
          org_id: "demo-org-id",
          role: role,
          email: authUser?.email,
          full_name: authUser?.user_metadata?.full_name || authUser?.email?.split("@")[0],
        });
      } else if (data) {
        setProfile(data as Profile);
      }
    } catch (e: unknown) {
      console.warn("Could not fetch database profile:", e);
    }
  };

  useEffect(() => {
    let mounted = true;

    async function initAuth() {
      try {
        const demo = getDemoSession();
        if (demo) {
          const st = demoToState(demo);
          if (mounted) { setUser(st.user); setProfile(st.profile); }
          return;
        }
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.user && mounted) {
          setUser(session.user);
          await fetchProfile(session.user.id);
        }
      } catch (err: unknown) {
        console.warn("Auth initialization note:", err);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    initAuth();

    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (!mounted) return;
        if (session?.user) {
          setUser(session.user);
          await fetchProfile(session.user.id);
        } else {
          setUser(null);
          setProfile(null);
        }
        setLoading(false);
      }
    );

    return () => {
      mounted = false;
      authListener?.subscription.unsubscribe();
    };
  }, [supabase]);

  const signIn = async (email: string, password = "BrandGuard2026!"): Promise<boolean> => {
    setError(null);
    setLoading(true);
    try {
      // Offline demo mode (no Supabase configured on the server): one-click token login
      const role = DEMO_ROLES[email];
      if (role) {
        try {
          const health = await api.health();
          if (health.store === "memory") {
            const d = await api.demoLogin(role);
            setDemoSession(d);
            const st = demoToState(d);
            setUser(st.user); setProfile(st.profile); setLoading(false);
            return true;
          }
        } catch { /* fall through to Supabase sign-in */ }
      }
      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (signInError) {
        setError(signInError.message);
        setLoading(false);
        return false;
      }

      if (data.user) {
        setUser(data.user);
        await fetchProfile(data.user.id);
      }
      setLoading(false);
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Authentication failed";
      setError(msg);
      setLoading(false);
      return false;
    }
  };

  const signOut = async () => {
    setLoading(true);
    try {
      setDemoSession(null);
      await supabase.auth.signOut();
      setUser(null);
      setProfile(null);
    } finally {
      setLoading(false);
    }
  };

  const refreshProfile = async () => {
    if (user) {
      await fetchProfile(user.id);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        loading,
        error,
        signIn,
        signOut,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
