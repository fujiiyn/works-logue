-- 00009_bloom_threshold_to_0_9.sql
-- Raise bloom_threshold from 0.7 to 0.9 for stricter maturity gating.

UPDATE app_settings
SET value = '0.9', updated_at = NOW()
WHERE key = 'score.bloom_threshold';
