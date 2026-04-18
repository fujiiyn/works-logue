-- 00007_planter_views_ip.sql
-- Add ip_address column to planter_views for anonymous view deduplication

ALTER TABLE planter_views ADD COLUMN ip_address VARCHAR(45);

-- Allow user_id to be null (anonymous views)
-- Already nullable in 00001

-- Replace unique index: deduplicate by user_id OR ip_address
DROP INDEX IF EXISTS uq_planter_views_user;

-- Logged-in user deduplication
CREATE UNIQUE INDEX uq_planter_views_user
    ON planter_views (user_id, planter_id)
    WHERE user_id IS NOT NULL;

-- Anonymous (IP-based) deduplication is handled at application level
-- (check viewed_at within 10-minute window)
CREATE INDEX idx_planter_views_ip
    ON planter_views (ip_address, planter_id, viewed_at DESC)
    WHERE ip_address IS NOT NULL;
