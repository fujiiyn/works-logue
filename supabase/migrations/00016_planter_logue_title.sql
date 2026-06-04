-- 00016_planter_logue_title.sql
-- Add a dedicated `logue_title` column for the AI-generated pattern name.
-- Until now the pattern name only lived inside the Markdown body
-- (`logue_content` h1), so every list view fell back to the original Seed
-- title. Promoting it to a first-class column lets the UI show "ノウハウ
-- 名" instead of the raw Seed title in Logue state.

BEGIN;

ALTER TABLE planters
    ADD COLUMN IF NOT EXISTS logue_title TEXT;

-- Backfill existing logues from the first line of `logue_content` (always
-- `# <pattern_name>` per LogueGenerator._build_markdown prior to 00016).
UPDATE planters
SET logue_title = NULLIF(
        ltrim(split_part(logue_content, E'\n', 1), '# '),
        ''
    )
WHERE status = 'logue'
  AND logue_content IS NOT NULL
  AND logue_title IS NULL;

CREATE INDEX IF NOT EXISTS idx_planters_logue_title
    ON planters (logue_title)
    WHERE status = 'logue' AND deleted_at IS NULL;

COMMIT;
