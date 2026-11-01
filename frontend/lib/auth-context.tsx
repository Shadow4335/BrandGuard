"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { User } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase";
import { Profile, UserRole } from "@/lib/types";
import { api, getDemoSession, setDemoSession, setFreshToken, getWorkspaceId, setWorkspaceId, DemoSession } from "@/lib/api";
import { signInWithGooglePopup } from "@/lib/firebase";

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
  signIn: (email: string, password: string) => Promise<boolean>;
  signInDemo: (role: UserRole) => Promise<boolean>;
  signInWithGoogle: (role?: UserRole, inviteCode?: string, rolePassword?: string) => Promise<boolean>;
  signUp: (input: { email: string; password: string; full_name: string; role: UserRole; invite_code?: string; role_password?: string }) => Promise<boolean>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  switchWorkspace: (id: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  profile: null,
  loading: true,
  error: null,
  signIn: async () => false,
  signInDemo: async () => false,
  signInWithGoogle: async () => false,
  signUp: async () => false,
  signOut: async () => {},
  refreshProfile: async () => {},
  switchWorkspace: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [supabase] = useState(() => createClient());
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = useCallback(async (userId: string) => {
    try {
      let me;
      try { me = await api.me(); }
      catch (e) { if (!getWorkspaceId()) throw e; setWorkspaceId(null); me = await api.me(); }
      setProfile({ id: userId, org_id: me.org_id, role: me.role as UserRole, email: me.email, full_name: me.full_name });
    } catch { setProfile(null); setError("Could not load your workspace. Please sign in again."); }
  }, []);

  useEffect(() => {
    let mounted = true;

    async function initAuth() {
      try {
        const demo = getDemoSession();
        if (demo) {
          const st = demoToState(demo);
          if (mounted) { setUser(st.user); setProfile(st.profile); await fetchProfile(demo.user_id); }
          return;
        }
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.user && mounted) {
          setUser(session.user);
          await fetchProfile(session.user.id);
        }
      } catch {
        setError("Could not restore your session. Please sign in again.");
      } finally {
        if (mounted) setLoading(false);
      }
    }

    initAuth();

    const { data: authListener } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (!mounted || getDemoSession()) return; // demo sessions are not Supabase sessions
        if (session?.user) {
          setUser(session.user);
          setFreshToken(session.access_token);
          void fetchProfile(session.user.id).finally(() => setFreshToken(null));
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
  }, [supabase, fetchProfile]);

  const signIn = async (email: string, password: string): Promise<boolean> => {
    setError(null);
    setWorkspaceId(null);
    setLoading(true);
    try {
      // Offline demo mode (no Supabase configured on the server): token login handled by the API
      let memoryMode = false;
      try { memoryMode = (await api.health()).store === "memory"; } catch { /* server asleep: try Supabase */ }
      if (memoryMode) {
        try {
          const role = DEMO_ROLES[email];
          const d = role ? await api.demoLogin(role) : await api.login(email, password);
          setDemoSession(d);
          const st = demoToState(d);
          setUser(st.user); setProfile(st.profile); setLoading(false);
          return true;
        } catch (e) {
          setError(e instanceof Error ? e.message : "Sign-in failed.");
          setLoading(false);
          return false;
        }
      }
      setDemoSession(null);
      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (signInError) {
        setError(/invalid login/i.test(signInError.message) ? "Wrong email or password." : signInError.message);
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

  /** One-click demo account. The server signs the demo user in, so the browser never holds a demo password. */
  const signInDemo = async (role: UserRole): Promise<boolean> => {
    setError(null);
    setWorkspaceId(null);
    setLoading(true);
    try {
      let offline = false;
      try { offline = (await api.health()).store === "memory"; } catch { /* server still waking: use the hosted path */ }
      if (offline) {
        const d = await api.demoLogin(role);
        setDemoSession(d);
        const st = demoToState(d);
        setUser(st.user); setProfile(st.profile); setLoading(false);
        return true;
      }
      setDemoSession(null);
      const tokens = await api.demoSession(role);
      const { data, error: sessionError } = await supabase.auth.setSession(tokens);
      if (sessionError || !data.user) {
        setError(sessionError?.message ?? "Demo sign-in failed. Please try again.");
        setLoading(false);
        return false;
      }
      setUser(data.user);
      await fetchProfile(data.user.id);
      setLoading(false);
      return true;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Demo sign-in failed. Please try again.");
      setLoading(false);
      return false;
    }
  };

  /** Google sign-in through Firebase. The API checks the Firebase token and returns a BrandGuard session; `role` is
   *  only used when this is the person's first sign-in. */
  const signInWithGoogle = async (role?: UserRole, inviteCode?: string, rolePassword?: string): Promise<boolean> => {
    setError(null);
    try {
      const idToken = await signInWithGooglePopup();
      if (!idToken) return false; // closed the popup
      setLoading(true);
      const res = await api.googleLogin(idToken, role, inviteCode || undefined, rolePassword || undefined);
      if (res.mode === "memory" && res.session) {
        setDemoSession(res.session);
        const st = demoToState(res.session);
        setUser(st.user); setProfile(st.profile); setLoading(false);
        return true;
      }
      setDemoSession(null);
      const tokens = { access_token: res.access_token ?? "", refresh_token: res.refresh_token ?? "" };
      if (res.profile) {
        // The API has just verified this session and sent the profile, so show the app now and let supabase-js save
        // the session in the background (its setSession re-checks the token with Supabase: about a second).
        const p = res.profile;
        setFreshToken(tokens.access_token);
        setUser({ id: p.id, email: p.email ?? undefined } as User);
        setProfile(p);
        setLoading(false);
        supabase.auth.setSession(tokens)
          .then(({ data, error: sessionError }) => {
            if (sessionError || !data.user) throw sessionError ?? new Error("no user");
            setUser(data.user);
          })
          .catch(() => {
            setUser(null); setProfile(null);
            setError("Google sign-in couldn't be completed. Please try again.");
          })
          .finally(() => setFreshToken(null));
        return true;
      }
      const { data, error: sessionError } = await supabase.auth.setSession(tokens);
      if (sessionError || !data.user) {
        setError(sessionError?.message ?? "Google sign-in failed. Please try again.");
        setLoading(false);
        return false;
      }
      setUser(data.user);
      await fetchProfile(data.user.id);
      setLoading(false);
      return true;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Google sign-in failed. Please try again.");
      setLoading(false);
      return false;
    }
  };

  const signUp = async (input: { email: string; password: string; full_name: string; role: UserRole; invite_code?: string; role_password?: string }): Promise<boolean> => {
    setError(null);
    setWorkspaceId(null);
    setLoading(true);
    try {
      const res = await api.signup(input);
      if (res.mode === "memory" && res.session) {
        setDemoSession(res.session);
        const st = demoToState(res.session);
        setUser(st.user); setProfile(st.profile); setLoading(false);
        return true;
      }
      return await signIn(res.email, input.password);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Sign-up failed. Please try again.");
      setLoading(false);
      return false;
    }
  };

  const signOut = async () => {
    setLoading(true);
    try {
      // Tell the API first, while the token is still available, so it drops it from its cache straight away
      await api.logout().catch(() => {});
      setDemoSession(null);
      setWorkspaceId(null);
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

  const switchWorkspace = async (id: string) => {
    const previous = getWorkspaceId();
    setWorkspaceId(id);
    try {
      const me = await api.me();
      setProfile({ id: me.user_id, org_id: me.org_id, role: me.role as UserRole, email: me.email, full_name: me.full_name });
    } catch (e) { setWorkspaceId(previous); throw e; }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        loading,
        error,
        signIn,
        signInDemo,
        signInWithGoogle,
        signUp,
        signOut,
        refreshProfile,
        switchWorkspace,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
