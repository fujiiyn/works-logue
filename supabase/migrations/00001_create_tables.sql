-- 00001_create_tables.sql
-- Works Logue: All tables, indexes, constraints, triggers

-- =============================================================
-- Helper: updated_at trigger function
-- =============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================
-- seed_types (master)
-- =============================================================
CREATE TABLE seed_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================================
-- users
-- =============================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_id UUID UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    bio TEXT,
    avatar_url TEXT,
    insight_score FLOAT NOT NULL DEFAULT 0.0,
    role VARCHAR(10) NOT NULL DEFAULT 'user',
    is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    banned_at TIMESTAMPTZ,
    ban_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_users_auth_id ON users (auth_id);
CREATE INDEX idx_users_deleted_at ON users (deleted_at) WHERE deleted_at IS NULL;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================
-- planters
-- =============================================================
CREATE TABLE planters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    seed_type_id UUID NOT NULL REFERENCES seed_types(id),
    status VARCHAR(10) NOT NULL DEFAULT 'seed',
    louge_content TEXT,
    louge_generated_at TIMESTAMPTZ,
    structure_fulfillment FLOAT NOT NULL DEFAULT 0.0,
    maturity_score FLOAT,
    progress FLOAT NOT NULL DEFAULT 0.0,
    log_count INT NOT NULL DEFAULT 0,
    contributor_count INT NOT NULL DEFAULT 0,
    parent_planter_id UUID REFERENCES planters(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT chk_planters_status CHECK (status IN ('seed', 'sprout', 'louge', 'archived'))
);

CREATE INDEX idx_planters_seed_type_id ON planters (seed_type_id);
CREATE INDEX idx_planters_user_id ON planters (user_id);
CREATE INDEX idx_planters_status ON planters (status) WHERE deleted_at IS NULL;
CREATE INDEX idx_planters_created_at ON planters (created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_planters_deleted_at ON planters (deleted_at) WHERE deleted_at IS NULL;

CREATE TRIGGER trg_planters_updated_at
    BEFORE UPDATE ON planters
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================
-- logs
-- =============================================================
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    planter_id UUID NOT NULL REFERENCES planters(id),
    user_id UUID REFERENCES users(id),
    body TEXT NOT NULL,
    parent_log_id UUID REFERENCES logs(id),
    is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    hidden_at TIMESTAMPTZ,
    hidden_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_logs_planter_id ON logs (planter_id, created_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_logs_user_id ON logs (user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_logs_parent_log_id ON logs (parent_log_id) WHERE parent_log_id IS NOT NULL;

CREATE TRIGGER trg_logs_updated_at
    BEFORE UPDATE ON logs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================
-- tags
-- =============================================================
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(20) NOT NULL,
    parent_tag_id UUID REFERENCES tags(id),
    sort_order INT NOT NULL DEFAULT 0,
    is_leaf BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_tags_name_category UNIQUE (name, category),
    CONSTRAINT chk_tags_category CHECK (category IN ('industry', 'occupation', 'role', 'situation', 'skill', 'knowledge'))
);

CREATE INDEX idx_tags_category ON tags (category, sort_order);
CREATE INDEX idx_tags_parent ON tags (parent_tag_id);
CREATE INDEX idx_tags_name_search ON tags (name);

-- =============================================================
-- planter_tags (junction)
-- =============================================================
CREATE TABLE planter_tags (
    planter_id UUID NOT NULL REFERENCES planters(id),
    tag_id UUID NOT NULL REFERENCES tags(id),
    PRIMARY KEY (planter_id, tag_id)
);

-- =============================================================
-- user_tags (junction)
-- =============================================================
CREATE TABLE user_tags (
    user_id UUID NOT NULL REFERENCES users(id),
    tag_id UUID NOT NULL REFERENCES tags(id),
    PRIMARY KEY (user_id, tag_id)
);

-- =============================================================
-- planter_follows
-- =============================================================
CREATE TABLE planter_follows (
    user_id UUID NOT NULL REFERENCES users(id),
    planter_id UUID NOT NULL REFERENCES planters(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, planter_id)
);

-- =============================================================
-- user_follows
-- =============================================================
CREATE TABLE user_follows (
    follower_id UUID NOT NULL REFERENCES users(id),
    followee_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (follower_id, followee_id),
    CONSTRAINT chk_user_follows_no_self CHECK (follower_id != followee_id)
);

-- =============================================================
-- notifications
-- =============================================================
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    type VARCHAR(30) NOT NULL,
    planter_id UUID REFERENCES planters(id),
    actor_id UUID REFERENCES users(id),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_notifications_type CHECK (type IN ('new_log', 'status_changed', 'louge_bloomed', 'new_seed'))
);

CREATE INDEX idx_notifications_user_unread ON notifications (user_id, created_at DESC) WHERE is_read = FALSE;

-- =============================================================
-- planter_views
-- =============================================================
CREATE TABLE planter_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    planter_id UUID NOT NULL REFERENCES planters(id),
    user_id UUID REFERENCES users(id),
    viewed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_planter_views_planter ON planter_views (planter_id, viewed_at);
CREATE INDEX idx_planter_views_user ON planter_views (user_id, planter_id) WHERE user_id IS NOT NULL;
CREATE UNIQUE INDEX uq_planter_views_user ON planter_views (user_id, planter_id) WHERE user_id IS NOT NULL;

-- =============================================================
-- louge_score_snapshots
-- =============================================================
CREATE TABLE louge_score_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    planter_id UUID NOT NULL REFERENCES planters(id),
    trigger_log_id UUID REFERENCES logs(id),
    structure_fulfillment FLOAT NOT NULL,
    maturity_scores JSONB,
    maturity_total FLOAT,
    passed_structure BOOLEAN NOT NULL,
    passed_maturity BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_score_snapshots_planter ON louge_score_snapshots (planter_id, created_at DESC);

-- =============================================================
-- insight_score_events
-- =============================================================
CREATE TABLE insight_score_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    planter_id UUID NOT NULL REFERENCES planters(id),
    log_id UUID REFERENCES logs(id),
    score_delta FLOAT NOT NULL,
    reason VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_insight_events_user ON insight_score_events (user_id, created_at DESC);
CREATE INDEX idx_insight_events_planter ON insight_score_events (planter_id);

-- =============================================================
-- ai_configs (admin settings)
-- =============================================================
CREATE TABLE ai_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(50) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID REFERENCES users(id)
);
