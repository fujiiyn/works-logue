import { supabase } from "./supabase";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAuthHeaders(): Promise<HeadersInit> {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    return { "Content-Type": "application/json" };
  }

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${session.access_token}`,
  };
}

async function getAuthToken(): Promise<string | null> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

export async function apiFetchUpload<T>(
  path: string,
  formData: FormData,
  options?: { signal?: AbortSignal },
): Promise<T> {
  const token = await getAuthToken();
  const headers: HeadersInit = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers,
    body: formData,
    signal: options?.signal,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error: ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = await getAuthHeaders();

  // Google Frontend (Cloud Run の手前) は Content-Length 無しの
  // POST/PUT/PATCH/DELETE を 411 で蹴る。body 未指定の場合は空文字で補う。
  const method = options.method?.toUpperCase();
  const needsBody =
    method !== undefined &&
    method !== "GET" &&
    method !== "HEAD" &&
    options.body == null;

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    body: needsBody ? "" : options.body,
    headers: {
      ...headers,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail || `API error: ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ---- Public stats (right-sidebar About card) -------------------------------

export interface PublicStats {
  seeds: number;
  louges: number;
  contributors: number;
}

export const getPublicStats = () => apiFetch<PublicStats>("/api/v1/stats");

// ---- Admin API (U7) ---------------------------------------------------------

export interface AdminStats {
  total_users: number;
  total_planters: number;
  new_planters_today: number;
  pending_louge_count: number;
}

export interface AdminUserItem {
  id: string;
  display_name: string;
  avatar_url: string | null;
  role: string;
  is_banned: boolean;
  banned_at: string | null;
  ban_reason: string | null;
  planter_count: number;
  log_count: number;
  created_at: string;
  is_self: boolean;
}

export interface AdminUserList {
  items: AdminUserItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface AdminPlanterAuthor {
  id: string;
  display_name: string;
  avatar_url: string | null;
}

export interface AdminPlanterItem {
  id: string;
  title: string;
  status: string;
  seed_type_name: string;
  author: AdminPlanterAuthor;
  log_count: number;
  contributor_count: number;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface AdminPlanterList {
  items: AdminPlanterItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface AdminSeedTypeItem {
  id: string;
  slug: string;
  name: string;
  description: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
}

interface ListUsersParams {
  q?: string;
  status?: "all" | "normal" | "banned";
  page?: number;
  per_page?: number;
}

interface ListPlantersParams {
  q?: string;
  status?: "all" | "seed" | "sprout" | "louge" | "archived" | "deleted";
  page?: number;
  per_page?: number;
}

function toQuery(params: Record<string, string | number | undefined>): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    sp.set(key, String(value));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const adminApi = {
  getStats: () => apiFetch<AdminStats>("/api/v1/admin/stats"),

  listUsers: (params: ListUsersParams = {}) =>
    apiFetch<AdminUserList>(`/api/v1/admin/users${toQuery({ ...params })}`),

  banUser: (id: string, body: { reason?: string | null }) =>
    apiFetch<AdminUserItem>(`/api/v1/admin/users/${id}/ban`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  unbanUser: (id: string) =>
    apiFetch<AdminUserItem>(`/api/v1/admin/users/${id}/unban`, {
      method: "POST",
    }),

  listPlanters: (params: ListPlantersParams = {}) =>
    apiFetch<AdminPlanterList>(
      `/api/v1/admin/planters${toQuery({ ...params })}`,
    ),

  archivePlanter: (id: string) =>
    apiFetch<AdminPlanterItem>(`/api/v1/admin/planters/${id}/archive`, {
      method: "POST",
    }),

  restorePlanter: (id: string) =>
    apiFetch<AdminPlanterItem>(`/api/v1/admin/planters/${id}/restore`, {
      method: "POST",
    }),

  deletePlanter: (id: string, body: { confirm_title: string }) =>
    apiFetch<void>(`/api/v1/admin/planters/${id}`, {
      method: "DELETE",
      body: JSON.stringify(body),
    }),

  listSeedTypes: (params: { status?: "all" | "active" | "inactive" } = {}) =>
    apiFetch<AdminSeedTypeItem[]>(
      `/api/v1/admin/seed-types${toQuery({ ...params })}`,
    ),

  updateSeedTypeDescription: (id: string, body: { description: string }) =>
    apiFetch<AdminSeedTypeItem>(`/api/v1/admin/seed-types/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  toggleSeedTypeActive: (id: string) =>
    apiFetch<AdminSeedTypeItem>(
      `/api/v1/admin/seed-types/${id}/toggle-active`,
      { method: "POST" },
    ),
};
