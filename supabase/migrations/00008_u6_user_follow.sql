-- 00008_u6_user_follow.sql
-- U6 User & Follow: users テーブル拡張 + planter_follows 拡張

-- =============================================================
-- users: プロフィール拡張フィールド
-- =============================================================
ALTER TABLE users
    ADD COLUMN headline VARCHAR(60),
    ADD COLUMN cover_url TEXT,
    ADD COLUMN location VARCHAR(100),
    ADD COLUMN x_url TEXT,
    ADD COLUMN linkedin_url TEXT,
    ADD COLUMN wantedly_url TEXT,
    ADD COLUMN website_url TEXT,
    ADD COLUMN pending_avatar_path TEXT,
    ADD COLUMN pending_cover_path TEXT;

-- =============================================================
-- planter_follows: 手動アンフォローフラグ
-- =============================================================
ALTER TABLE planter_follows
    ADD COLUMN is_manually_unfollowed BOOLEAN NOT NULL DEFAULT FALSE;
