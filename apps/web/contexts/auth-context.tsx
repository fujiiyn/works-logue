"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import type { Session, User as SupabaseUser } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { apiFetch } from "@/lib/api-client";

interface AppUser {
  id: string;
  display_name: string;
  headline: string | null;
  bio: string | null;
  avatar_url: string | null;
  cover_url: string | null;
  location: string | null;
  x_url: string | null;
  linkedin_url: string | null;
  wantedly_url: string | null;
  website_url: string | null;
  insight_score: number;
  role: string;
  onboarded_at: string | null;
  created_at: string;
}

interface AuthContextValue {
  user: AppUser | null;
  session: Session | null;
  isLoading: boolean;
  refreshUser: () => Promise<void>;
  signIn: (
    provider: "google" | "email",
    credentials?: { email: string; password: string },
  ) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  async function fetchAppUser() {
    try {
      const appUser = await apiFetch<AppUser>("/api/v1/users/me");
      setUser(appUser);
    } catch {
      setUser(null);
    }
  }

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session: s } }) => {
      setSession(s);
      if (s) {
        fetchAppUser().finally(() => setIsLoading(false));
      } else {
        setIsLoading(false);
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, s) => {
      setSession(s);
      if (s) {
        fetchAppUser();
      } else {
        setUser(null);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  // Onboarding redirect: if logged in but not onboarded, redirect to /onboarding
  useEffect(() => {
    if (user && !user.onboarded_at) {
      const allowedPaths = ["/", "/login", "/onboarding"];
      const isViewPage = pathname.startsWith("/p/");
      if (!allowedPaths.includes(pathname) && !isViewPage) {
        router.push(`/onboarding?redirect=${encodeURIComponent(pathname)}`);
      }
    }
  }, [user, pathname, router]);

  async function signIn(
    provider: "google" | "email",
    credentials?: { email: string; password: string },
  ) {
    if (provider === "google") {
      await supabase.auth.signInWithOAuth({ provider: "google" });
    } else if (credentials) {
      const { error } = await supabase.auth.signInWithPassword(credentials);
      if (error) throw error;
    }
  }

  async function signUp(email: string, password: string) {
    const { error } = await supabase.auth.signUp({ email, password });
    if (error) throw error;
  }

  async function signOut() {
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, session, isLoading, refreshUser: fetchAppUser, signIn, signUp, signOut }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
