-- 00012_bloom_threshold_to_0_85.sql
-- Revert bloom_threshold from 0.9 → 0.85.
--
-- Rationale: 0.9 was set in 00009 to make the bar feel meaningful, but the
-- maturity rubric has a structural ceiling for single-contributor planters
-- (diversity caps around 0.7–0.8 when only one person posts), so the
-- aspect-wise maximum tops out at ~0.85. 0.9 is unreachable in that mode
-- and the early test scenarios (one tester walking through a sample
-- conversation) never bloom. 0.85 is high enough to demand structure +
-- specificity + counterarguments while still being reachable.
UPDATE app_settings
SET value = '0.85', updated_at = NOW()
WHERE key = 'score.bloom_threshold';
