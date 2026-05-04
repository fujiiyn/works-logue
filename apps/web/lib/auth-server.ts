/**
 * U7 Step 21: Server-side auth helpers for App Router (Server Components).
 *
 * `getCurrentUser()` resolves the calling user via Supabase SSR cookies and
 * fetches the FastAPI `/users/me` row. The returned `accessToken` is meant
 * to be threaded into `serverFetch()` so admin Server Components can call
 * the API without round-tripping through the client.
 *
 * Both helpers return null / throw rather than handling errors themselves;
 * callers (e.g. `app/admin/layout.tsx`) decide whether to `notFound()`.
 */
import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!;

export interface ServerUser {
  id: string;
  display_name: string;
  role: string;
  is_banned: boolean;
  deleted_at: string | null;
  accessToken: string;
}

interface UserMeResponse {
  id: string;
  display_name: string;
  role: string;
  is_banned: boolean;
  deleted_at: string | null;
}

async function readCookieStore() {
  const cookieStore = await cookies();
  return createServerClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      // Server Components can't set cookies; supabase-ssr requires the method
      // to exist but we deliberately no-op here.
      setAll() {
        /* no-op in Server Components */
      },
    },
  });
}

export async function getCurrentUser(): Promise<ServerUser | null> {
  const supabase = await readCookieStore();

  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();
  if (error || !session?.access_token) {
    return null;
  }

  try {
    const me = await serverFetch<UserMeResponse>(
      "/api/v1/users/me",
      session.access_token,
    );
    return {
      id: me.id,
      display_name: me.display_name,
      role: me.role,
      is_banned: me.is_banned,
      deleted_at: me.deleted_at,
      accessToken: session.access_token,
    };
  } catch {
    return null;
  }
}

export class ServerFetchError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ServerFetchError";
  }
}

export async function serverFetch<T>(
  path: string,
  accessToken: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new ServerFetchError(res.status, `serverFetch failed: ${res.status}`);
  }
  return (await res.json()) as T;
}
