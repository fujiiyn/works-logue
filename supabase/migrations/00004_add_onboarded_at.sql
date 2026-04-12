-- U2 Seed: Add onboarded_at column to users table
ALTER TABLE users ADD COLUMN onboarded_at TIMESTAMPTZ;
