import { createBrowserClient } from "@supabase/ssr";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!;

// createBrowserClient は session を Cookie に保存するため、
// Server Component (lib/auth-server.ts) からも同じ session を読める。
// @supabase/supabase-js の createClient は localStorage 保存で SSR から見えず、
// /admin の AdminLayout ガードが常に notFound() になっていた。
export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey);
