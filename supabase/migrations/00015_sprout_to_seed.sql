-- 00015_sprout_to_seed.sql
-- Reverse direction of 00014's state merge: unify Planter status under 'seed'
-- (instead of 'sprout'). Planters are 'seed' from creation.

BEGIN;

ALTER TABLE planters DROP CONSTRAINT IF EXISTS chk_planters_status;

UPDATE planters SET status = 'seed' WHERE status = 'sprout';

ALTER TABLE planters ADD CONSTRAINT chk_planters_status
    CHECK (status IN ('seed', 'logue', 'archived'));

ALTER TABLE planters ALTER COLUMN status SET DEFAULT 'seed';

COMMIT;
