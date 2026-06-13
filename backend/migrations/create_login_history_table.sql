-- ============================================================
-- LexGuard AI — User Login Activity Migration
-- Creates the login_history table and index.
-- ============================================================

CREATE TABLE IF NOT EXISTS login_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    login_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    device_info VARCHAR(255),
    ip_address VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON login_history (user_id);
