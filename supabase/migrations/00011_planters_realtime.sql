-- 00011_planters_realtime.sql
-- Enable Supabase Realtime for the planters table so other browsers see
-- score animations / status transitions / Louge bloom in real time without
-- having to poll. Score and Louge content updates flow:
--
--   FastAPI write → planters UPDATE → WAL → supabase_realtime publication →
--   browser .channel("planter:{id}").on("postgres_changes", "UPDATE", ...)
--
-- REPLICA IDENTITY FULL is required so the UPDATE payload contains every
-- column (default DEFAULT only ships changed columns + PK, which would miss
-- structure_parts / progress / louge_content depending on the write).

-- Add planters to the publication (idempotent guard).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_publication_tables
        WHERE pubname = 'supabase_realtime' AND tablename = 'planters'
    ) THEN
        EXECUTE 'ALTER PUBLICATION supabase_realtime ADD TABLE planters';
    END IF;
END
$$;

-- Ship the full row on UPDATE. Note: planters carries louge_content (a
-- multi-KB AI-generated article) so every UPDATE roughly doubles WAL
-- volume for that row. Acceptable at current scale; revisit if planters
-- writes become hot.
ALTER TABLE planters REPLICA IDENTITY FULL;

-- Required for Realtime authorization to evaluate row visibility.
ALTER TABLE planters ENABLE ROW LEVEL SECURITY;

-- Public SELECT policy: anyone (anon, authenticated) can read non-deleted
-- planters. Writes go via FastAPI (postgres role, BYPASSRLS) so this does
-- not affect the API.
DROP POLICY IF EXISTS "planters_public_read" ON planters;
CREATE POLICY "planters_public_read"
    ON planters
    FOR SELECT
    TO anon, authenticated
    USING (deleted_at IS NULL);

-- Schema USAGE was granted in 00010 but assert it again here to keep the
-- migration self-contained for fresh environments.
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON public.planters TO anon, authenticated;

-- Defense in depth: see 00010 for rationale.
REVOKE INSERT, UPDATE, DELETE ON public.planters FROM anon, authenticated;
