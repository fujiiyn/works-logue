-- 00017_bloom_threshold_to_0_9.sql
-- Raise bloom_threshold from 0.85 → 0.9.
--
-- Rationale: Logues bloomed with few logs are thin, and the AI fills the gaps
-- with generic advice. 0.9 requires more logs before blooming.
-- Trade-off (see 00012): a planter where only one person posts caps diversity
-- around 0.7–0.8, so it will not bloom at 0.9. That is now intended — bloom
-- should require multiple contributors. The value stays tunable from Admin.
UPDATE app_settings
SET value = '0.9', updated_at = NOW()
WHERE key = 'score.bloom_threshold';
