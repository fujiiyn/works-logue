-- 00006_feed_search_indexes.sql
-- U5 Feed & Search: pg_trgm extension + search/feed indexes

-- Enable trigram extension for ILIKE performance
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Title trigram index for keyword search (ILIKE)
CREATE INDEX idx_planters_title_trgm
    ON planters USING gin (title gin_trgm_ops)
    WHERE deleted_at IS NULL;

-- Louge generated_at index for "bloomed" tab sorting
CREATE INDEX idx_planters_louge_generated_at
    ON planters (louge_generated_at DESC)
    WHERE status = 'louge' AND deleted_at IS NULL;
