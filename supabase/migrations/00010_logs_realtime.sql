-- 00010_logs_realtime.sql
-- Enable Supabase Realtime for the logs table so the LogThread can subscribe
-- to INSERT events and reflect other users' / AI facilitator posts immediately.
--
-- Writes still go through FastAPI (direct Postgres connection); the browser
-- client only reads via the Realtime channel.

-- Add logs to the supabase_realtime publication (idempotent guard).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_publication_tables
        WHERE pubname = 'supabase_realtime' AND tablename = 'logs'
    ) THEN
        EXECUTE 'ALTER PUBLICATION supabase_realtime ADD TABLE logs';
    END IF;
END
$$;

-- Enable RLS so Realtime authorization gates row visibility.
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;

-- Public SELECT policy: anyone (anon, authenticated) can read non-deleted logs.
-- Writes are not permitted from PostgREST/Realtime — FastAPI uses a direct
-- Postgres connection and is not subject to these policies.
DROP POLICY IF EXISTS "logs_public_read" ON logs;
CREATE POLICY "logs_public_read"
    ON logs
    FOR SELECT
    TO anon, authenticated
    USING (deleted_at IS NULL);

-- Schema-level USAGE grant. Without this, anon/authenticated cannot resolve
-- objects in the public schema at all and Realtime fails to deliver any
-- postgres_changes event to the browser (it tries to evaluate visibility as
-- the subscribing role and gets "permission denied for schema public"
-- before reaching the row policy).
GRANT USAGE ON SCHEMA public TO anon, authenticated;

-- Table-level SELECT grant. Required in addition to RLS: Realtime evaluates
-- privileges using the subscribing role, and tables created via raw SQL
-- migrations (vs. Studio) do NOT get the default anon/authenticated grants
-- that Supabase Studio adds automatically. Without these, Realtime silently
-- skips events for those roles even when the RLS policy would have allowed
-- the row.
GRANT SELECT ON public.logs TO anon, authenticated;

-- Defense in depth: explicitly revoke writes from anon/authenticated. RLS
-- without policy already denies, but explicit REVOKE makes intent durable
-- if a future policy is added by mistake.
REVOKE INSERT, UPDATE, DELETE ON public.logs FROM anon, authenticated;
