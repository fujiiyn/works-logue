-- 00014_seed_sprout_merge_logue_rename.sql
-- 1) Merge Planter status 'seed' into 'sprout' (Planters are 'sprout' from creation)
-- 2) Rename domain term 'Louge' -> 'Logue' (typo fix; brand "Works Logue" unaffected)
--
-- Idempotent and transactional so this can be re-run safely.

BEGIN;

-- =============================================================
-- 1. Drop old constraints first so UPDATE can introduce new values
-- =============================================================
ALTER TABLE planters DROP CONSTRAINT IF EXISTS chk_planters_status;
ALTER TABLE notifications DROP CONSTRAINT IF EXISTS chk_notifications_type;

-- =============================================================
-- 2. Migrate data: status 'seed' -> 'sprout', 'louge' -> 'logue'
-- =============================================================
UPDATE planters SET status = 'sprout' WHERE status = 'seed';
UPDATE planters SET status = 'logue' WHERE status = 'louge';

-- =============================================================
-- 3. Add new CHECK constraints
-- =============================================================
ALTER TABLE planters ADD CONSTRAINT chk_planters_status
    CHECK (status IN ('sprout', 'logue', 'archived'));

-- =============================================================
-- 4. New default for status is 'sprout'
-- =============================================================
ALTER TABLE planters ALTER COLUMN status SET DEFAULT 'sprout';

-- =============================================================
-- 5. Rename planters columns louge_* -> logue_* (idempotent)
-- =============================================================
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'planters'
          AND column_name = 'louge_content'
    ) THEN
        ALTER TABLE planters RENAME COLUMN louge_content TO logue_content;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'planters'
          AND column_name = 'louge_generated_at'
    ) THEN
        ALTER TABLE planters RENAME COLUMN louge_generated_at TO logue_generated_at;
    END IF;
END $$;

-- =============================================================
-- 6. Rename louge_score_snapshots table -> logue_score_snapshots (idempotent)
-- =============================================================
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'louge_score_snapshots'
    ) THEN
        ALTER TABLE louge_score_snapshots RENAME TO logue_score_snapshots;
    END IF;
END $$;

-- =============================================================
-- 7. Replace the bloomed-feed index with the new column name and status value
-- =============================================================
DROP INDEX IF EXISTS idx_planters_louge_generated_at;
CREATE INDEX IF NOT EXISTS idx_planters_logue_generated_at
    ON planters (logue_generated_at DESC)
    WHERE status = 'logue' AND deleted_at IS NULL;

-- =============================================================
-- 8. Migrate notifications.type values and add new CHECK constraint
-- =============================================================
UPDATE notifications SET type = 'logue_bloomed' WHERE type = 'louge_bloomed';
ALTER TABLE notifications ADD CONSTRAINT chk_notifications_type
    CHECK (type IN ('new_log', 'status_changed', 'logue_bloomed', 'new_seed'));

-- =============================================================
-- 9. Rename ai_configs keys
-- =============================================================
UPDATE ai_configs SET key = 'logue_model'
    WHERE key = 'louge_model';
UPDATE ai_configs SET key = 'logue_generation_prompt'
    WHERE key = 'louge_generation_prompt';

COMMIT;
