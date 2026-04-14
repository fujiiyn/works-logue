-- 00005_u3_log_score.sql
-- U3 Log & Score: app_settings table, structure_parts column

-- =============================================================
-- app_settings (key-value store for application configuration)
-- =============================================================
CREATE TABLE app_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================================
-- louge_score_snapshots: add structure_parts column
-- =============================================================
ALTER TABLE louge_score_snapshots
    ADD COLUMN structure_parts JSONB;

-- =============================================================
-- Initial score settings
-- =============================================================
INSERT INTO app_settings (key, value) VALUES
    ('score.min_contributors', '3'),
    ('score.min_logs', '5'),
    ('score.bloom_threshold', '0.7'),
    ('score.bud_threshold', '0.8');
